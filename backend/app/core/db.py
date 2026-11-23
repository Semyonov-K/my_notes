from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.config import get_settings


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей (SQLAlchemy 2.0)."""


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    _engine = create_async_engine(settings.database_url, echo=settings.debug)
    return _engine


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    _session_factory = async_sessionmaker(
        get_engine(), expire_on_commit=False, class_=AsyncSession
    )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        yield session
