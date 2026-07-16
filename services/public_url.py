"""İstemcinin gördüğü genel taban URL (LAN IP / Render / localhost)."""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse, urlunparse

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "::1"}


def get_public_base_url(request=None) -> str:
    """PUBLIC_BASE_URL > istek Host > varsayılan localhost."""
    explicit = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit

    if request is not None:
        # Proxy arkasında (Render)
        proto = (request.headers.get("X-Forwarded-Proto") or request.scheme or "http").split(",")[0].strip()
        host = (request.headers.get("X-Forwarded-Host") or request.host or "").split(",")[0].strip()
        if host:
            return f"{proto}://{host}".rstrip("/")

    port = os.getenv("PORT", "5001")
    return f"http://127.0.0.1:{port}"


def is_loopback_host(host: str) -> bool:
    hostname = (host or "").split(":")[0].strip().lower()
    return hostname in _LOCAL_HOSTS


def external_request_url(request) -> str:
    """OAuth token exchange icin proxy-arkasi https URL."""
    url = request.url
    proto = (request.headers.get("X-Forwarded-Proto") or request.scheme or "http").split(",")[0].strip()
    if proto == "https" and url.startswith("http://"):
        url = "https://" + url[len("http://") :]
    return url


def mail_oauth_redirect_uri(provider: str, request=None) -> str:
    """
    Google Console'da kayitli callback ile birebir eslesmeli.
    Render'da localhost env varsa canli host'a cevir.
    """
    provider = (provider or "").strip().lower()
    env_keys = {
        "google": "GOOGLE_MAIL_REDIRECT_URI",
        "microsoft": "MICROSOFT_REDIRECT_URI",
        "yahoo": "YAHOO_REDIRECT_URI",
    }
    env_val = (os.getenv(env_keys.get(provider, "")) or "").strip()
    base = get_public_base_url(request)
    live_callback = f"{base}/mail/oauth/{provider}/callback"

    if not env_val:
        # Google login redirect'inden turetmeyi dene
        if provider == "google":
            login_redirect = (os.getenv("GOOGLE_REDIRECT_URI") or "").strip()
            if login_redirect.endswith("/auth/google/callback"):
                derived = login_redirect[: -len("/auth/google/callback")] + "/mail/oauth/google/callback"
                parsed = urlparse(derived)
                if parsed.hostname and not is_loopback_host(parsed.hostname):
                    return derived
                if request is not None and not is_loopback_host(urlparse(base).hostname or ""):
                    return live_callback
                return derived
        return live_callback

    parsed = urlparse(env_val)
    # Env localhost / yanlis host ise canli request host'unu kullan
    if request is not None:
        req_host = (request.headers.get("X-Forwarded-Host") or request.host or "").split(",")[0].strip()
        if req_host and not is_loopback_host(req_host.split(":")[0]):
            if is_loopback_host(parsed.hostname or "") or (
                parsed.hostname
                and parsed.hostname.lower() not in req_host.lower()
                and "onrender.com" in req_host.lower()
            ):
                return live_callback

    return env_val


def looks_like_lan_ip(value: str) -> bool:
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", (value or "").strip()))
