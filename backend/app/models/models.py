import enum
from datetime import datetime

from aiogram import enums
from sqlalchemy import func, String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class IntPkMixin:
    id: Mapped[int] = mapped_column(primary_key=True)


class NoteStatus(str, enum.Enum):
    active = "active"
    done = "done"
    cancelled = "cancelled"


class User(IntPkMixin, TimestampMixin, Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    nickname: Mapped[str | None] = mapped_column(default=None)


class Note(IntPkMixin, TimestampMixin, Base):
    __tablename__ = "notes"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)
    deadline_date: Mapped[datetime | None] = mapped_column(default=None)
    status: Mapped[NoteStatus] = mapped_column(Enum(NoteStatus), default=NoteStatus.active)


class Reminder(IntPkMixin, TimestampMixin, Base):
    pass
    # name: Mapped[str | None] = mapped_column(String(50), default=None)
    # surname: Mapped[str | None] = mapped_column(String(50), default=None)
    # age: Mapped[int | None] = mapped_column(default=None)
    # username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    # email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user)
