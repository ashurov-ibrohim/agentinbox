from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from dependencies import get_current_user
from models.user import Users
from services import auth_services

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login():
    auth_url = auth_services.get_google_auth_url()
    return RedirectResponse(auth_url)


@router.get("/callback")
def callback(code: str, db: Session = Depends(get_db)):
    user, jwt_token = auth_services.handle_google_callback(db, code)

    response = RedirectResponse(url=settings.FRONTEND_URL)
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # Render'da HTTPS -> True
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/me")
def me(current_user: Users = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Muvaffaqiyatli chiqildi"}
