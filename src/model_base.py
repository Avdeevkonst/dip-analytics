import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(AsyncAttrs, DeclarativeBase): ...


class TimestampMixin:
    """
    Mixin for timestamp fields.
    """

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class PrimaryKeyUUID:
    """
    Mixin for primary key UUID field.
    """

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class Data:
    """
    Mixin for name and description fields.
    """

    name: Mapped[str] = mapped_column(String(length=100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(length=400), nullable=True)


class Point:
    """
    Mixin for latitude and longitude fields.
    """

    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()


class General(Base, PrimaryKeyUUID, TimestampMixin):
    """
    Abstract base class for all models.
    """

    __abstract__ = True

    @declared_attr  # pyright: ignore[reportArgumentType]
    @classmethod
    def __tablename__(cls):
        return cls.__name__.lower()
