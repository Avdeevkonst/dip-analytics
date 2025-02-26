import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(AsyncAttrs, DeclarativeBase): ...


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class PrimaryKeyUUID:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class Data:
    name: Mapped[str] = mapped_column(String(length=100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(length=400), nullable=True)


class General(Base, PrimaryKeyUUID, TimestampMixin):
    __abstract__ = True

    @declared_attr  # pyright: ignore[reportArgumentType]
    @classmethod
    def __tablename__(cls):
        return cls.__name__.lower()
