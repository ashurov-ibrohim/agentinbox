from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dependencies import get_current_user
from models.user import Users
from services.gmail_services import (
    list_messages,
    get_message_detail,
    mark_as_read,
    send_reply,
)

router = APIRouter(prefix="/mcp", tags=["webmcp"])


class ReplyRequest(BaseModel):
    text: str


@router.get("/messages")
def get_messages(
    unread: bool = False,
    max_results: int = 10,
    current_user: Users = Depends(get_current_user),
):
    return list_messages(current_user, max_results=max_results, unread_only=unread)


@router.get("/messages/{message_id}")
def get_message(message_id: str, current_user: Users = Depends(get_current_user)):
    return get_message_detail(current_user, message_id)


@router.post("/messages/{message_id}/read")
def read_message(message_id: str, current_user: Users = Depends(get_current_user)):
    mark_as_read(current_user, message_id)
    return {"message": "Xat o'qilgan deb belgilandi"}


@router.post("/messages/{message_id}/reply")
def reply_message(
    message_id: str,
    payload: ReplyRequest,
    current_user: Users = Depends(get_current_user),
):
    result = send_reply(current_user, message_id, payload.text)
    return {"message": "Javob yuborildi", "sent_id": result.get("id")}
