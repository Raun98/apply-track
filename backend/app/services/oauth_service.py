import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.config import get_settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MICROSOFT_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"

GOOGLE_SCOPES = "https://mail.google.com/ email openid"
MICROSOFT_SCOPES = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access email openid profile"


def _callback_url(provider: str) -> str:
    settings = get_settings()
    return f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/email-accounts/oauth/{provider}/callback"


def get_google_auth_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": _callback_url("google"),
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def get_microsoft_auth_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "redirect_uri": _callback_url("microsoft"),
        "response_type": "code",
        "scope": MICROSOFT_SCOPES,
        "state": state,
    }
    return f"{MICROSOFT_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_google_code(code: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": _callback_url("google"),
            "grant_type": "authorization_code",
        })
        resp.raise_for_status()
        token_data = resp.json()

        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo_resp.raise_for_status()
        email = userinfo_resp.json().get("email", "")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "expires_at": expires_at,
        "email": email,
    }


async def exchange_microsoft_code(code: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(MICROSOFT_TOKEN_URL, data={
            "code": code,
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "redirect_uri": _callback_url("microsoft"),
            "grant_type": "authorization_code",
            "scope": MICROSOFT_SCOPES,
        })
        resp.raise_for_status()
        token_data = resp.json()

        userinfo_resp = await client.get(
            MICROSOFT_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo_resp.raise_for_status()
        me = userinfo_resp.json()
        email = me.get("mail") or me.get("userPrincipalName", "")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "expires_at": expires_at,
        "email": email,
    }


async def refresh_google_token(refresh_token: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "refresh_token": refresh_token,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        token_data = resp.json()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    return {
        "access_token": token_data["access_token"],
        "expires_at": expires_at,
    }


async def refresh_microsoft_token(refresh_token: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(MICROSOFT_TOKEN_URL, data={
            "refresh_token": refresh_token,
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "scope": MICROSOFT_SCOPES,
        })
        resp.raise_for_status()
        token_data = resp.json()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    return {
        "access_token": token_data["access_token"],
        "expires_at": expires_at,
    }


def generate_state() -> str:
    return secrets.token_hex(32)


def _redis_state_key(state: str) -> str:
    return f"oauth_state:{state}"


async def store_oauth_state(state: str, user_id: int) -> None:
    import redis.asyncio as aioredis
    settings = get_settings()
    r = aioredis.from_url(settings.REDIS_URL)
    try:
        await r.set(_redis_state_key(state), str(user_id), ex=600)
    finally:
        await r.aclose()


async def consume_oauth_state(state: str) -> Optional[int]:
    """Return the user_id for the given state and delete it (one-time use)."""
    import redis.asyncio as aioredis
    settings = get_settings()
    r = aioredis.from_url(settings.REDIS_URL)
    try:
        key = _redis_state_key(state)
        value = await r.getdel(key)
        if value is None:
            return None
        return int(value)
    finally:
        await r.aclose()
