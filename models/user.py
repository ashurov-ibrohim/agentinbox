from sqlalchemy import String, UUID as uid, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from datetime import datetime, timezone
from database import Base


class Users(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(uid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    picture: Mapped[str] = mapped_column(Text, nullable=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    sessions: Mapped[list["ChatSession"]] = relationship(back_populates="users")