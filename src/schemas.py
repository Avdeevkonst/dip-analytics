from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.utils import Sort

T = TypeVar("T", bound=BaseModel)


class ReturnPagination(BaseModel, Generic[T]):
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
