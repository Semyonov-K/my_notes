import enum
from datetime import datetime, time


from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
    Time,
    Index,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.db import Base


class IntPkMixin:
    id: Mapped[int] = mapped_column(primary_key=True)


class NoteStatus(str, enum.Enum):
    active = "active"
    done = "done"
    cancelled = "cancelled"


class User(IntPkMixin, Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    nickname: Mapped[str | None] = mapped_column(default=None)
    timezone: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Note(IntPkMixin, Base):
    __tablename__ = "notes"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)
    deadline_date: Mapped[datetime | None] = mapped_column(default=None)
    status: Mapped[NoteStatus] = mapped_column(Enum(NoteStatus), default=NoteStatus.active)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class DeadlineAlert(IntPkMixin, Base):
    __tablename__ = "deadline_alerts"

    __table_args__ = (
        UniqueConstraint("note_id", "offset_minutes", name="uq_note_offset"),
    )

    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    offset_minutes: Mapped[int] = mapped_column(default=0)


class ScheduleMode(str, enum.Enum):
    at_times = "at_times"
    interval = "interval"


class Schedule(IntPkMixin, Base):
    __tablename__ = "schedules"

    __table_args__ = (
        UniqueConstraint("note_id", name="uq_schedule_note"),
        CheckConstraint(
            "weekdays BETWEEN 1 AND 127",
            name="ck_schedule_weekdays",
        ),
        CheckConstraint(
            """
            (
                mode = 'at_times'
                AND times IS NOT NULL
                AND cardinality(times) > 0
                AND interval_minutes IS NULL
                AND window_start IS NULL
                AND window_end IS NULL
            )
            OR
            (
                mode = 'interval'
                AND interval_minutes IS NOT NULL
                AND interval_minutes >= 15
                AND window_start IS NOT NULL
                AND window_end IS NOT NULL
                AND times IS NULL
            )
            """,
            name="ck_schedule_mode_fields",
        ),
    )

    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    mode: Mapped[ScheduleMode] = mapped_column(
        Enum(ScheduleMode),
        nullable=False,
    )
    weekdays: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    times: Mapped[list[time] | None] = mapped_column(ARRAY(Time), default=None)
    interval_minutes: Mapped[int | None] = mapped_column(default=None)
    window_start: Mapped[time | None] = mapped_column(Time, default=None)
    window_end: Mapped[time | None] = mapped_column(Time, default=None)


class ReminderSource(str, enum.Enum):
    deadline = "deadline"
    schedule = "schedule"


class ReminderStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    sent = "sent"
    cancelled = "cancelled"


class Reminder(IntPkMixin, Base):
    __tablename__ = "reminders"

    __table_args__ = (
        CheckConstraint(
            """
            (
                source = 'deadline'
                AND deadline_alert_id IS NOT NULL
                AND schedule_id IS NULL
            )
            OR
            (
                source = 'schedule'
                AND schedule_id IS NOT NULL
                AND deadline_alert_id IS NULL
            )
            """,
            name="ck_reminder_source_fk",
        ),

        Index("ix_reminders_pending_due", "status", "remind_at"),
        Index(
            "uq_reminder_live_deadline_alert",
            "deadline_alert_id",
            unique=True,
            postgresql_where=text(
                "status IN ('pending', 'processing') AND deadline_alert_id IS NOT NULL"
            ),
        ),
        Index(
            "uq_reminder_live_schedule",
            "schedule_id",
            unique=True,
            postgresql_where=text(
                "status IN ('pending', 'processing') AND schedule_id IS NOT NULL"
            ),
        ),
    )
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source: Mapped[ReminderSource] = mapped_column(
        Enum(ReminderSource),
        nullable=False,
    )
    deadline_alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("deadline_alerts.id", ondelete="CASCADE"),
        default=None,
    )
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id", ondelete="CASCADE"),
        default=None,
    )
    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus),
        default=ReminderStatus.pending,
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
