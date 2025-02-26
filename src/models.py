from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.model_base import Data, General
from src.utils import Jam, Weather


class Base(DeclarativeBase): ...


class Road(General, Data):
    start: Mapped[str] = mapped_column(String(255))
    end: Mapped[str] = mapped_column(String(255))
    length: Mapped[float] = mapped_column()
    city: Mapped[str] = mapped_column(String(255))


class RoadCondition(General, Data):
    weather_status: Mapped[str] = mapped_column(Enum(Weather))
    jam_status: Mapped[str] = mapped_column(Enum(Jam))


class RoadConditionHistory(General):
    road_cond: Mapped[UUID] = mapped_column(ForeignKey("roadcondition.id"))
    road: Mapped[UUID] = mapped_column(ForeignKey("road.id"))
