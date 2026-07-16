import json
import os
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
CLIENT_SECRETS_FILE = ROOT_DIR / "google_client_secret.json"

_CLIENT_ID_RE = re.compile(r"^[\w.-]+\.apps\.googleusercontent\.com$")


def validate_google_oauth_credentials(client_id, client_secret):
    """Google Cloud OAuth Client ID/Secret formatini dogrula (e-posta vs. reddet)."""
    client_id = (client_id or "").strip()
    client_secret = (client_secret or "").strip()
    if not client_id or not client_secret:
        raise ValueError("Client ID ve Client Secret gerekli.")
    if "@" in client_id or not _CLIENT_ID_RE.match(client_id):
        raise ValueError(
            "Geçersiz Client ID. Gmail adresi değil; Google Cloud Console → "
            "APIs & Services → Credentials → OAuth 2.0 Client ID içinden "
            "....apps.googleusercontent.com ile biten değeri yapıştırın."
        )
    if client_secret.startswith("AIza"):
        raise ValueError(
            "Bu bir API Key gibi görünüyor. OAuth Client Secret "
            "(genelde GOCSPX- ile başlar) gerekli."
        )
    return client_id, client_secret


def save_google_credentials(client_id, client_secret, redirect_uri=None):
    client_id, client_secret = validate_google_oauth_credentials(client_id, client_secret)

    redirect_uri = redirect_uri or "http://127.0.0.1:5001/auth/google/callback"
    if redirect_uri.endswith("/auth/google/callback"):
        mail_redirect_uri = (
            redirect_uri[: -len("/auth/google/callback")] + "/mail/oauth/google/callback"
        )
    else:
        mail_redirect_uri = "http://127.0.0.1:5001/mail/oauth/google/callback"

    lines = []
    found = {
        "GOOGLE_CLIENT_ID": False,
        "GOOGLE_CLIENT_SECRET": False,
        "GOOGLE_REDIRECT_URI": False,
        "GOOGLE_MAIL_REDIRECT_URI": False,
    }

    if ENV_FILE.exists():
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                key = line.split("=", 1)[0].strip()
                if key == "GOOGLE_CLIENT_ID":
                    lines.append(f"GOOGLE_CLIENT_ID={client_id}\n")
                    found["GOOGLE_CLIENT_ID"] = True
                elif key == "GOOGLE_CLIENT_SECRET":
                    lines.append(f"GOOGLE_CLIENT_SECRET={client_secret}\n")
                    found["GOOGLE_CLIENT_SECRET"] = True
                elif key == "GOOGLE_REDIRECT_URI":
                    lines.append(f"GOOGLE_REDIRECT_URI={redirect_uri}\n")
                    found["GOOGLE_REDIRECT_URI"] = True
                elif key == "GOOGLE_MAIL_REDIRECT_URI":
                    lines.append(f"GOOGLE_MAIL_REDIRECT_URI={mail_redirect_uri}\n")
                    found["GOOGLE_MAIL_REDIRECT_URI"] = True
                else:
                    lines.append(line)

    if not found["GOOGLE_CLIENT_ID"]:
        lines.append(f"GOOGLE_CLIENT_ID={client_id}\n")
    if not found["GOOGLE_CLIENT_SECRET"]:
        lines.append(f"GOOGLE_CLIENT_SECRET={client_secret}\n")
    if not found["GOOGLE_REDIRECT_URI"]:
        lines.append(f"GOOGLE_REDIRECT_URI={redirect_uri}\n")
    if not found["GOOGLE_MAIL_REDIRECT_URI"]:
        lines.append(f"GOOGLE_MAIL_REDIRECT_URI={mail_redirect_uri}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    os.environ["GOOGLE_CLIENT_ID"] = client_id
    os.environ["GOOGLE_CLIENT_SECRET"] = client_secret
    os.environ["GOOGLE_REDIRECT_URI"] = redirect_uri
    os.environ["GOOGLE_MAIL_REDIRECT_URI"] = mail_redirect_uri


def _extract_web_credentials(config):
    web = config.get("web") or config.get("installed") or {}
    client_id = (web.get("client_id") or "").strip()
    client_secret = (web.get("client_secret") or "").strip()
    if not client_id or not client_secret:
        raise ValueError("JSON dosyasında client_id ve client_secret bulunamadı.")
    return client_id, client_secret


def save_google_credentials_from_json(raw_json, redirect_uri=None):
    try:
        config = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Geçersiz JSON dosyası.") from exc

    client_id, client_secret = _extract_web_credentials(config)
    redirect_uri = redirect_uri or "http://127.0.0.1:5001/auth/google/callback"

    with open(CLIENT_SECRETS_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    save_google_credentials(client_id, client_secret, redirect_uri)
    return client_id


def bootstrap_google_credentials():
    if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"):
        return

    if not CLIENT_SECRETS_FILE.exists():
        return

    try:
        raw = CLIENT_SECRETS_FILE.read_text(encoding="utf-8")
        if "BURAYA_CLIENT_ID" in raw:
            return
        save_google_credentials_from_json(raw)
    except Exception:
        pass
