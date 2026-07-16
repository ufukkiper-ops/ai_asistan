"""Yahoo Mail OAuth2 (IMAP/SMTP XOAUTH2)."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent

YAHOO_SCOPES = [
    "openid",
    "email",
    "mail-r",
    "mail-w",
]

AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
USERINFO_URL = "https://api.login.yahoo.com/openid/v1/userinfo"


def get_redirect_uri():
    return os.getenv(
        "YAHOO_REDIRECT_URI",
        "http://127.0.0.1:5001/mail/oauth/yahoo/callback",
    )


def get_client_id():
    return (os.getenv("YAHOO_CLIENT_ID") or "").strip()


def get_client_secret():
    return (os.getenv("YAHOO_CLIENT_SECRET") or "").strip()


def is_yahoo_configured():
    return bool(get_client_id() and get_client_secret())


def _basic_auth_header():
    raw = f"{get_client_id()}:{get_client_secret()}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .decode("ascii")
        .rstrip("=")
    )
    return verifier, challenge


def build_authorization_url(redirect_uri=None):
    if not is_yahoo_configured():
        raise RuntimeError("Yahoo OAuth yapılandırılmadı (YAHOO_CLIENT_ID/SECRET).")

    state = secrets.token_urlsafe(24)
    verifier, challenge = _pkce_pair()
    params = {
        "client_id": get_client_id(),
        "redirect_uri": redirect_uri or get_redirect_uri(),
        "response_type": "code",
        "scope": " ".join(YAHOO_SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "language": "tr-tr",
    }
    return f"{AUTH_URL}?{urlencode(params)}", state, verifier


def exchange_code_for_tokens(code: str, code_verifier: str = "", redirect_uri=None):
    data = {
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri or get_redirect_uri(),
        "code": code,
    }
    if code_verifier:
        data["code_verifier"] = code_verifier

    response = httpx.post(
        TOKEN_URL,
        data=data,
        headers={
            "Authorization": _basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Yahoo token hatası: {response.text[:240]}")
    payload = response.json()
    expires_in = int(payload.get("expires_in") or 3600)
    expiry = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() + expires_in))
    return {
        "access_token": payload.get("access_token") or "",
        "refresh_token": payload.get("refresh_token") or "",
        "token_expiry": expiry,
        "scopes": (payload.get("scope") or " ".join(YAHOO_SCOPES)).split(),
    }


def refresh_access_token(refresh_token: str):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = httpx.post(
        TOKEN_URL,
        data=data,
        headers={
            "Authorization": _basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=30,
    )
    if response.status_code >= 400:
        return None
    payload = response.json()
    expires_in = int(payload.get("expires_in") or 3600)
    expiry = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() + expires_in))
    return {
        "access_token": payload.get("access_token") or "",
        "refresh_token": payload.get("refresh_token") or refresh_token,
        "token_expiry": expiry,
        "scopes": (payload.get("scope") or " ".join(YAHOO_SCOPES)).split(),
    }


def fetch_yahoo_email(access_token: str) -> str:
    response = httpx.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if response.status_code >= 400:
        raise RuntimeError("Yahoo hesabından e-posta alınamadı.")
    data = response.json()
    email = (data.get("email") or "").strip().lower()
    if not email:
        raise RuntimeError("Yahoo hesabından e-posta alınamadı.")
    return email


def get_fresh_access_token(mail_data):
    if not mail_data or mail_data.get("provider") != "yahoo_oauth":
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

    if not refresh_token or not is_yahoo_configured():
        return access_token or None, None

    updated = refresh_access_token(refresh_token)
    if not updated or not updated.get("access_token"):
        return None, None
    return updated["access_token"], updated
