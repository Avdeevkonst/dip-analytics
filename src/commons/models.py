from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.commons.enums import Jam, Weather
from src.commons.model_base import Base, Data, General

association_table = Table(
    "association_table",
    Base.metadata,
    Column("road_id", ForeignKey("road.id")),
    Column("car_id", ForeignKey("car.id")),
)


class Road(General, Data):
    """
    Road model.
    """

    start: Mapped[str] = mapped_column(String(255))
    end: Mapped[str] = mapped_column(String(255))
    length: Mapped[float] = mapped_column()
    city: Mapped[str] = mapped_column(String(255))
    street: Mapped[str] = mapped_column(String(255))
    cars: Mapped[list["Car"]] = relationship(secondary=association_table)

    __table_args__ = (
        Index("idx_road_city", "city"),
        Index("idx_road_name", "name", unique=True),
    )


class RoadCondition(General, Data):
    """
    Road condition model.
    """

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


class Car(General):
    """Car model with aggregated data from sensors."""

    plate_number: Mapped[str] = mapped_column(String(255), unique=True)
    model: Mapped[str] = mapped_column(String(255))
    average_speed: Mapped[float] = mapped_column()

    road_id: Mapped[UUID] = mapped_column(ForeignKey("road.id"))
    road: Mapped["Road"] = relationship(back_populates="cars")

    __table_args__ = (
        Index(
            "idx_car_created_at",
            "created_at",
            postgresql_using="btree",
            postgresql_ops={"created_at": "DESC"},
        ),
        Index("idx_car_plate_number", "plate_number", unique=True),
    )


class TrafficMeasurement(General):
    """Traffic measurement data for a specific road segment."""

    road_id: Mapped[UUID] = mapped_column(ForeignKey("road.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    average_speed: Mapped[float] = mapped_column()
    flow_rate: Mapped[int] = mapped_column()  # vehicles per hour
    density: Mapped[float] = mapped_column()  # vehicles per kilometer

    __table_args__ = (Index("idx_traffic_road_id_timestamp", "road_id", "timestamp"),)


class RoadCapacity(General, Data):
    """Road capacity and speed limits."""

    road_id: Mapped[UUID] = mapped_column(ForeignKey("road.id"), unique=True)
    lanes: Mapped[int] = mapped_column(Integer())
    speed_limit: Mapped[int] = mapped_column(Integer())
    max_capacity: Mapped[int] = mapped_column(Integer())  # vehicles per hour

    __table_args__ = (Index("idx_road_capacity_road_id", "road_id"),)
