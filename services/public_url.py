"""İstemcinin gördüğü genel taban URL (LAN IP / Render / localhost)."""

from __future__ import annotations

import os
import re

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


def mail_oauth_redirect_uri(provider: str, request=None) -> str:
    provider = (provider or "").strip().lower()
    env_keys = {
        "google": "GOOGLE_MAIL_REDIRECT_URI",
        "microsoft": "MICROSOFT_REDIRECT_URI",
        "yahoo": "YAHOO_REDIRECT_URI",
    }
    env_val = (os.getenv(env_keys.get(provider, "")) or "").strip()
    base = get_public_base_url(request)

    # Env localhost ise ama istek LAN/IP üzerinden geliyorsa istek host'unu kullan
    if env_val:
        from urllib.parse import urlparse

        parsed = urlparse(env_val)
        if request is not None and is_loopback_host(parsed.hostname or ""):
            req_host = (request.headers.get("X-Forwarded-Host") or request.host or "").split(",")[0].strip()
            if req_host and not is_loopback_host(req_host.split(":")[0]):
                return f"{base}/mail/oauth/{provider}/callback"
        return env_val

    return f"{base}/mail/oauth/{provider}/callback"


def looks_like_lan_ip(value: str) -> bool:
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", (value or "").strip()))
