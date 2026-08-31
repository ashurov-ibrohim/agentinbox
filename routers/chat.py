from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from enums.role import Role
from models.user import Users
from repos import chat_repos
from services.gemini_services import chat_with_agent

router = APIRouter(prefix="/chat", tags=["chat"])


class MessageRequest(BaseModel):
    message: str


@router.post("/sessions")
def create_session(
    db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)
):
    """Yangi suhbat (chat sessiyasi) boshlaydi."""
    session = chat_repos.create_session(db, current_user.id)
    return {"session_id": str(session.id)}


@router.post("/sessions/{session_id}/messages")
def send_message(
    session_id: UUID,
    payload: MessageRequest,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """
    Foydalanuvchi xabarini qabul qiladi, shu sessiyaning oldingi xabarlarini
    (history) DB'dan o'qib, Gemini agent'ga yuboradi (kerak bo'lsa u Gmail
    tool'larini chaqiradi) va javobni qaytaradi. Ikkala tomon xabari ham
    DB'ga saqlanadi.
    """
    session = chat_repos.get_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1. Shu sessiyada avval yozilgan xabarlarni olamiz - Gemini'ga suhbat
    #    kontekstini berish uchun
    previous_messages = chat_repos.get_messages(db, session_id)
    history = [
        {"role": m.role.value, "content": m.content} for m in previous_messages
    ]

    # 2. Foydalanuvchi xabarini DB'ga saqlaymiz
    chat_repos.add_message(db, session_id, Role.user, payload.message)

    # 3. Gemini'ga yuboramiz
    result = chat_with_agent(current_user, payload.message, history=history)

    # 4. Gemini javobini ham DB'ga saqlaymiz
    chat_repos.add_message(db, session_id, Role.model, result["reply"])

    return {"reply": result["reply"]}


@router.get("/sessions/{session_id}/messages")
def get_history(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Sessiyaning to'liq xabar tarixini qaytaradi."""
    session = chat_repos.get_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = chat_repos.get_messages(db, session_id)
    return [
        {"role": m.role.value, "content": m.content, "created_at": m.created_at}
        for m in messages
    ]
