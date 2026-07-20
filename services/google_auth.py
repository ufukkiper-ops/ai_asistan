import json
import os
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

ROOT_DIR = Path(__file__).resolve().parent.parent
CLIENT_SECRETS_FILE = ROOT_DIR / "google_client_secret.json"

# Sadece Google ile giris/kayit
AUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
# Gmail senkronu (istege bagli)
GMAIL_SCOPES = AUTH_SCOPES + [
    "https://mail.google.com/",
]


def _ensure_insecure_transport():
    if os.getenv("OAUTHLIB_INSECURE_TRANSPORT") is None:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    # Google bazen daraltılmis scope dondurur; oauthlib hata atmasin
    os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")


def _has_gmail_scope(scopes) -> bool:
    for scope in scopes or []:
        s = (scope or "").lower()
        if "mail.google.com" in s or "googleapis.com/auth/gmail" in s:
            return True
    return False


def _naive_utc_expiry(value):
    """google-auth Credentials.expiry icin timezone'siz UTC datetime."""
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def get_redirect_uri():
    return os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:5001/auth/google/callback",
    )


def _client_config_from_env():
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [get_redirect_uri()],
        }
    }


def _client_config_from_file():
    if not CLIENT_SECRETS_FILE.exists():
        return None

    with open(CLIENT_SECRETS_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_client_config():
    # .env veya google_client_secret.json sonradan eklenebilir
    load_dotenv = None
    try:
        from dotenv import load_dotenv as _load_dotenv
        load_dotenv = _load_dotenv
    except ImportError:
        pass

    if load_dotenv:
        load_dotenv(ROOT_DIR / ".env", override=True)

    return _client_config_from_env() or _client_config_from_file()


def is_google_configured():
    return get_client_config() is not None


def get_google_setup_hint():
    return "Google henüz bağlı değil. Önce Google ayarlarını yapın."


def get_mail_link_redirect_uri():
    explicit = (os.getenv("GOOGLE_MAIL_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit
    base = get_redirect_uri()
    if base.endswith("/auth/google/callback"):
        return base[: -len("/auth/google/callback")] + "/mail/oauth/google/callback"
    return "http://127.0.0.1:5001/mail/oauth/google/callback"


def build_authorization_url(
    action="register",
    force_account_picker=False,
    redirect_uri=None,
    with_mail=False,
):
    # Mail OAuth start (link_mail) her zaman Gmail scope ister
    with_mail = bool(with_mail) or action in {"link_mail", "consent", "register_mail", "login_mail"}
    scopes = GMAIL_SCOPES if with_mail else AUTH_SCOPES
    flow = create_oauth_flow(redirect_uri=redirect_uri, scopes=scopes)
    # Gmail baglama veya hesap secici: consent + select_account
    want_consent = with_mail or force_account_picker
    prompt = "consent select_account" if want_consent else "select_account"
    auth_kwargs = {
        "access_type": "offline",
        "prompt": prompt,
    }
    if not with_mail:
        auth_kwargs["include_granted_scopes"] = "true"
    authorization_url, state = flow.authorization_url(**auth_kwargs)
    return authorization_url, state, flow.code_verifier


def create_oauth_flow(redirect_uri=None, scopes=None):
    _ensure_insecure_transport()

    config = get_client_config()
    if not config:
        raise RuntimeError(get_google_setup_hint())

    return Flow.from_client_config(
        config,
        scopes=scopes or GMAIL_SCOPES,
        redirect_uri=redirect_uri or get_redirect_uri(),
    )


def exchange_code_for_credentials(flow, authorization_response, require_mail_scope=False):
    _ensure_insecure_transport()
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    scopes = list(credentials.scopes or [])
    if require_mail_scope and not _has_gmail_scope(scopes):
        raise RuntimeError(
            "Gmail izni verilmedi. Google Cloud Console → OAuth consent screen → "
            "Data Access / Scopes bölümüne https://mail.google.com/ ekleyin. "
            "Sonra https://myaccount.google.com/permissions adresinden "
            "Uygulama erişimini kaldırıp Mail → Hesap Ekle ile "
            "e-posta ve uygulama şifresi kullanarak tekrar bağlayın."
        )
    expiry = _naive_utc_expiry(credentials.expiry)
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_expiry": expiry.isoformat() if expiry else None,
        "scopes": scopes,
    }


def credentials_from_user_mail(mail_data):
    if not mail_data or mail_data.get("provider") != "google_oauth":
        return None

    refresh_token = mail_data.get("refresh_token")
    if not refresh_token:
        return None

    config = get_client_config()
    if not config:
        return None

    web = config.get("web", config.get("installed", {}))
    creds = Credentials(
        token=mail_data.get("access_token"),
        refresh_token=refresh_token,
        token_uri=web.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=web.get("client_id"),
        client_secret=web.get("client_secret"),
        scopes=mail_data.get("scopes") or GMAIL_SCOPES,
    )

    if mail_data.get("token_expiry"):
        try:
            creds.expiry = _naive_utc_expiry(mail_data["token_expiry"])
        except ValueError:
            pass

    try:
        needs_refresh = bool(creds.expired)
    except TypeError:
        # naive/aware karisikligi: guvenli tarafta yenile
        needs_refresh = True
    if needs_refresh and creds.refresh_token:
        creds.refresh(Request())
        creds.expiry = _naive_utc_expiry(creds.expiry)

    return creds


def get_fresh_access_token(mail_data):
    creds = credentials_from_user_mail(mail_data)
    if not creds or not creds.token:
        return None, None

    expiry = _naive_utc_expiry(creds.expiry)
    updated = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token or mail_data.get("refresh_token"),
        "token_expiry": expiry.isoformat() if expiry else None,
        "scopes": list(creds.scopes or mail_data.get("scopes") or GMAIL_SCOPES),
    }
    return creds.token, updated


def fetch_google_email(access_token):
    import httpx

    response = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    email = (data.get("email") or "").strip().lower()
    if not email:
        raise RuntimeError("Google hesabından e-posta alınamadı.")
    return email


def flow_for_callback(state, code_verifier, redirect_uri=None, with_mail=False):
    _ensure_insecure_transport()

    config = get_client_config()
    if not config:
        raise RuntimeError(get_google_setup_hint())

    flow = Flow.from_client_config(
        config,
        scopes=GMAIL_SCOPES if with_mail else AUTH_SCOPES,
        state=state,
        redirect_uri=redirect_uri or get_redirect_uri(),
    )
    flow.code_verifier = code_verifier
    return flow
