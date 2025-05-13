from datetime import datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from src.commons.enums import Jam, Sort, Weather
from src.commons.state import State

T = TypeVar("T", bound=BaseModel)


class ReturnPagination[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class FromAttr(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ReturnBase(FromAttr):
    id: UUID
    created_at: datetime
    updated_at: datetime


class CarCreate(BaseModel):
    """Raw car data from traffic sensors."""

    plate_number: str = Field(..., description="Car plate number")
    road_id: UUID
    model: str = Field(..., description="Car model")
    average_speed: float = Field(..., ge=0, description="Current speed from sensor")


class GetCar(BaseModel):
    id: UUID | None = None
    plate_number: str | None = None
    model: str | None = None
    road_id: UUID | None = None


class GetCarByTimeRange(BaseModel):
    range_time: PositiveInt
    road_id: UUID | None


class Pagination(BaseModel):
    sort: Sort
    page: int | None = Field(None, ge=1)
    limit: int | None = Field(None, ge=1)


class RoadConditionBase(FromAttr):
    road_id: UUID
    weather_status: Weather
    jam_status: Jam
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=400)


class RoadConditionCreate(RoadConditionBase): ...


class GetRoadCondition(BaseModel):
    id: UUID | None = None
    road_id: UUID | None = None
    weather_status: Weather | None = None
    jam_status: Jam | None = None
    name: str | None = None


class RoadBase(FromAttr):
    start: str = Field(..., min_length=1, max_length=255)
    end: str = Field(..., min_length=1, max_length=255)
    length: float
    city: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    street: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=400)


class RoadCreate(RoadBase): ...


class GetRoad(BaseModel):
    id: UUID | None = None
    city: str | None = None
    name: str | None = None
    length: float | None = None


class TrafficState(BaseModel):
    """Traffic state response model."""

    state: str = Field(..., description="Current traffic state (HIGH/LOW)")
    congestion_level: float = Field(..., description="Detailed congestion information")
    last_change: datetime | None = Field(None, description="Last state change timestamp")
    cooldown_until: datetime | None = Field(None, description="State cannot be changed until this time")


class TrafficMeasurementCreate(BaseModel):
    """Traffic measurement creation schema."""

    road_id: UUID
    timestamp: datetime
    average_speed: float = Field(..., ge=0)
    flow_rate: int = Field(..., ge=0)
    density: float = Field(..., ge=0)


class RoadCapacityCreate(BaseModel):
    """Road capacity creation schema."""

    road_id: UUID
    lanes: int = Field(..., gt=0)
    speed_limit: int = Field(..., gt=0)
    max_capacity: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=400)


class TrafficAnalysis(BaseModel):
    """Traffic analysis response model."""

    current_speed: float = Field(..., description="Current average speed (km/h)")
    flow_rate: int = Field(..., description="Current flow rate (vehicles/hour)")
    density: float = Field(..., description="Current density (vehicles/km)")
    congestion_level: float = Field(..., description="Current congestion level (0-1)")
    state: State = Field(State("UNSTAGED"), description="Traffic status (UNSTAGED/LOW/MEDIUM/HIGH)")
    trend: str = Field(..., description="Speed trend (STABLE/INCREASING/DECREASING)")


class GetTrafficMeasurement(BaseModel):
    """Schema for querying traffic measurements."""

    id: UUID | None = None
    road_id: UUID | None = None
    timestamp: datetime | None = None


class GetRoadCapacity(BaseModel):
    """Schema for querying road capacity."""

    id: UUID | None = None
    road_id: UUID | None = None
    lanes: int | None = None
    speed_limit: int | None = None
    max_capacity: int | None = None
