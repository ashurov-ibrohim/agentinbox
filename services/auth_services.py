from datetime import timezone
from typing import Tuple

import httpx
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session
from constants import get_scopes
from config import settings
from models.user import Users
from repos import auth_repos
from utils.security import create_access_token


def _build_google_flow() -> Flow:
    """Google OAuth uchun Flow obyektini quradi (client_id/secret config'dan olinadi)."""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URL],
        }
    }
    return Flow.from_client_config(
        client_config, scopes=get_scopes(), redirect_uri=settings.GOOGLE_REDIRECT_URL
    )


def get_google_auth_url() -> str:
    """Foydalanuvchini yo'naltirish uchun Google consent ekrani URL'ini qaytaradi."""
    flow = _build_google_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def _fetch_google_userinfo(credentials: Credentials) -> dict:
    """Access token orqali Google'dan foydalanuvchi profilini (email, ism, rasm) oladi."""
    resp = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"},
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=400, detail="Failed to retrieve Google user information"
        )
    return resp.json()


def handle_google_callback(db: Session, code: str) -> Tuple[Users, str]:
    """
    Google'dan qaytgan 'code'ni to'liq login jarayoniga aylantiradi:
    1. code -> access/refresh token
    2. token -> foydalanuvchi profili
    3. profil -> DB'da user yaratish/yangilash (repos orqali)
    4. user -> ilovamizning JWT tokeni

    Router bu funksiyani chaqiradi, natijada (user, jwt_token) oladi.
    """
    flow = _build_google_flow()
    try:
        flow.fetch_token(code=code)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Google token exchange failed"
        )

    credentials: Credentials = flow.credentials
    userinfo = _fetch_google_userinfo(credentials)

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not received from Google")

    token_expiry = None
    if credentials.expiry:
        token_expiry = (
            credentials.expiry
            if credentials.expiry.tzinfo
            else credentials.expiry.replace(tzinfo=timezone.utc)
        )

    user = auth_repos.get_user_by_email(db, email)
    if not user:
        user = auth_repos.create_user(
            db,
            email=email,
            name=userinfo.get("name"),
            picture=userinfo.get("picture"),
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=token_expiry,
        )
    else:
        user = auth_repos.update_user_tokens(
            db,
            user,
            name=userinfo.get("name"),
            picture=userinfo.get("picture"),
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=token_expiry,
        )

    jwt_token = create_access_token({"sub": str(user.id)})
    return user, jwt_token
