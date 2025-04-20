from datetime import datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.utils import Jam, Sort, Weather

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


class CarBase(FromAttr):
    plate_number: str
    model: str
    avarage_speed: int
    latitude: float
    longitude: float


class CarCreate(CarBase): ...


class GetCar(BaseModel):
    id: UUID | None = None
    plate_number: str | None = None
    model: str | None = None


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
    description: str = Field(..., min_length=1, max_length=400)


class RoadCreate(RoadBase): ...


class GetRoad(BaseModel):
    id: UUID | None = None
    city: str | None = None
    name: str | None = None
    length: float | None = None
