from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.model_base import Data, General, Point
from src.utils import Jam, Weather


class Base(DeclarativeBase): ...


class Road(General, Data):
    start: Mapped[str] = mapped_column(String(255))
    end: Mapped[str] = mapped_column(String(255))
    length: Mapped[float] = mapped_column()
    city: Mapped[str] = mapped_column(String(255))

    __table_args__ = (
        Index("idx_road_city", "city"),
        Index("idx_road_name", "name", unique=True),
    )


class RoadCondition(General, Data):
    road_id: Mapped[UUID] = mapped_column(
        ForeignKey("road.id"),
    )
    weather_status: Mapped[str] = mapped_column(Enum(Weather))
    jam_status: Mapped[str] = mapped_column(Enum(Jam))

    __table_args__ = (
        Index("idx_road_condition_road_id", "road_id"),
        Index(
            "idx_road_condition_created_at",
            "created_at",
            postgresql_using="btree",
            postgresql_ops={"created_at": "DESC"},
        ),
    )


class Car(General, Point):
    plate_number: Mapped[str] = mapped_column(String(255))
    model: Mapped[str] = mapped_column(String(255))
    avarage_speed: Mapped[int] = mapped_column(Integer())

    __table_args__ = (
        Index(
            "idx_pages_created_at",
            "created_at",
            postgresql_using="btree",
            postgresql_ops={"created_at": "DESC"},
        ),
        Index("idx_car_plate_number", "plate_number"),
    )
