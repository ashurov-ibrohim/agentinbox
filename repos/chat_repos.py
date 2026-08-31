from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from enums.role import Role
from models.chat import ChatMessage, ChatSession


def create_session(db: Session, user_id: UUID) -> ChatSession:
    """Foydalanuvchi uchun yangi chat sessiyasi (suhbat) yaratadi."""
    session = ChatSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: UUID) -> Optional[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def update_last_interaction_id(
    db: Session, session: ChatSession, interaction_id: str
) -> ChatSession:
    """Gemini bilan suhbatni keyingi safar davom ettirish uchun oxirgi interaction ID'ni saqlaydi."""
    session.last_interaction_id = interaction_id
    db.commit()
    db.refresh(session)
    return session


def add_message(db: Session, session_id: UUID, role: Role, content: str) -> ChatMessage:
    """Sessiyaga bitta xabar (foydalanuvchidan yoki modeldan) qo'shadi."""
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages(db: Session, session_id: UUID) -> List[ChatMessage]:
    """Sessiyadagi barcha xabarlarni yozilish tartibida qaytaradi."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
