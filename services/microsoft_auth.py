"""Microsoft / Outlook OAuth2 (IMAP/SMTP XOAUTH2)."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent

MICROSOFT_SCOPES = [
    "offline_access",
    "openid",
    "email",
    "profile",
    "User.Read",
    "https://outlook.office.com/IMAP.AccessAsUser.All",
    "https://outlook.office.com/SMTP.Send",
]

AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"


def get_redirect_uri():
    return os.getenv(
        "MICROSOFT_REDIRECT_URI",
        "http://127.0.0.1:5001/mail/oauth/microsoft/callback",
    )


def get_client_id():
    return (os.getenv("MICROSOFT_CLIENT_ID") or "").strip()


def get_client_secret():
    return (os.getenv("MICROSOFT_CLIENT_SECRET") or "").strip()


def is_microsoft_configured():
    return bool(get_client_id() and get_client_secret())


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .decode("ascii")
        .rstrip("=")
    )
    return verifier, challenge


def build_authorization_url(redirect_uri=None):
    if not is_microsoft_configured():
        raise RuntimeError("Microsoft OAuth yapılandırılmadı (MICROSOFT_CLIENT_ID/SECRET).")

    state = secrets.token_urlsafe(24)
    verifier, challenge = _pkce_pair()
    params = {
        "client_id": get_client_id(),
        "response_type": "code",
        "redirect_uri": redirect_uri or get_redirect_uri(),
        "response_mode": "query",
        "scope": " ".join(MICROSOFT_SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    return f"{AUTH_URL}?{urlencode(params)}", state, verifier


def exchange_code_for_tokens(code: str, code_verifier: str, redirect_uri=None):
    data = {
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri or get_redirect_uri(),
        "code_verifier": code_verifier,
        "scope": " ".join(MICROSOFT_SCOPES),
    }
    response = httpx.post(TOKEN_URL, data=data, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Microsoft token hatası: {response.text[:240]}")
    payload = response.json()
    expires_in = int(payload.get("expires_in") or 3600)
    expiry = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() + expires_in))
    return {
        "access_token": payload.get("access_token") or "",
        "refresh_token": payload.get("refresh_token") or "",
        "token_expiry": expiry,
        "scopes": (payload.get("scope") or "").split(),
        "id_token": payload.get("id_token") or "",
    }


def refresh_access_token(refresh_token: str):
    data = {
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": " ".join(MICROSOFT_SCOPES),
    }
    response = httpx.post(TOKEN_URL, data=data, timeout=30)
    if response.status_code >= 400:
        return None
    payload = response.json()
    expires_in = int(payload.get("expires_in") or 3600)
    expiry = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() + expires_in))
    return {
        "access_token": payload.get("access_token") or "",
        "refresh_token": payload.get("refresh_token") or refresh_token,
        "token_expiry": expiry,
        "scopes": (payload.get("scope") or "").split() or MICROSOFT_SCOPES,
    }


def _email_from_id_token(id_token: str) -> str:
    try:
        parts = id_token.split(".")
        if len(parts) < 2:
            return ""
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        return (data.get("preferred_username") or data.get("email") or "").strip().lower()
    except Exception:
        return ""


def fetch_microsoft_email(access_token: str, id_token: str = "") -> str:
    email = _email_from_id_token(id_token)
    if email:
        return email

    # Graph için ayrı scope gerekebilir; id_token yoksa access token claim dene
    try:
        response = httpx.get(
            GRAPH_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        if response.status_code < 400:
            data = response.json()
            email = (data.get("mail") or data.get("userPrincipalName") or "").strip().lower()
            if email:
                return email
    except Exception:
        pass

    raise RuntimeError("Microsoft hesabından e-posta alınamadı.")


def get_fresh_access_token(mail_data):
    if not mail_data or mail_data.get("provider") != "microsoft_oauth":
        return None, None

    refresh_token = mail_data.get("refresh_token")
    access_token = mail_data.get("access_token")
    expiry = mail_data.get("token_expiry")

    needs_refresh = True
    if access_token and expiry:
        try:
            from datetime import datetime, timezone

            dt = datetime.fromisoformat(expiry)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            needs_refresh = dt.timestamp() <= time.time() + 60
        except ValueError:
            needs_refresh = True

    if not needs_refresh and access_token:
        return access_token, None

    if not refresh_token or not is_microsoft_configured():
        return access_token or None, None

    updated = refresh_access_token(refresh_token)
    if not updated or not updated.get("access_token"):
        return None, None
    return updated["access_token"], updated
