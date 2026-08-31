from sqlalchemy import UUID as uid, ForeignKey, DateTime, Text, Enum, String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from uuid import UUID, uuid4
from database import Base
from enums.role import Role
from datetime import datetime, timezone
from typing import Optional


class ChatSession(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(uid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # Gemini Interactions API'da suhbatni davom ettirish uchun kerak
    # (previous_interaction_id sifatida uzatiladi)
    last_interaction_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    users: Mapped["Users"] = relationship(back_populates="sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session")


class ChatMessage(Base):
    __tablename__ = "messages"
    id: Mapped[UUID] = mapped_column(uid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    content: Mapped[str] = (mapped_column(Text, nullable=False))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

