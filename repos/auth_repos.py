from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from models.user import Users


def get_user_by_email(db: Session, email: str) -> Optional[Users]:
    """Email bo'yicha userni DB'dan qidiradi. Topilmasa None qaytaradi."""
    return db.query(Users).filter(Users.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> Optional[Users]:
    """ID bo'yicha userni DB'dan qidiradi. JWT ichidagi 'sub' shu ID bo'ladi."""
    return db.query(Users).filter(Users.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    name: Optional[str],
    picture: Optional[str],
    access_token: Optional[str],
    refresh_token: Optional[str],
    token_expiry: Optional[datetime],
) -> Users:
    """Yangi user yozuvini yaratadi (birinchi marta Google orqali kirganda)."""
    user = Users(
        email=email,
        name=name,
        picture=picture,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=token_expiry,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_tokens(
    db: Session,
    user: Users,
    name: Optional[str],
    picture: Optional[str],
    access_token: Optional[str],
    refresh_token: Optional[str],
    token_expiry: Optional[datetime],
) -> Users:
    """Mavjud user qayta login qilganda ma'lumot va tokenlarini yangilaydi."""
    user.name = name or user.name
    user.picture = picture or user.picture
    user.access_token = access_token
    # Google refresh_token'ni faqat birinchi consent'da beradi - shuning uchun
    # yangisi kelmasa eskisini o'chirib yubormaymiz
    if refresh_token:
        user.refresh_token = refresh_token
    user.token_expiry = token_expiry

    db.commit()
    db.refresh(user)
    return user
