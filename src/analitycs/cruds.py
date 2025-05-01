from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select

from src.models import Car, Road, RoadCondition
from src.schemas import CarCreate, GetCar, GetCarByTimeRange, GetRoad, GetRoadCondition, RoadConditionCreate, RoadCreate
from src.services.db import CrudEntity


class CarCrud(CrudEntity[Car]):
    def __init__(self):
        super().__init__(model=Car)

    async def create_car(self, car: CarCreate) -> Car:
        return await self.create_entity(car)

    async def get_car(self, conditions: GetCar) -> list[Car]:
        return await self.get_many(conditions)

    async def get_car_by_time_range(self, conditions: GetCarByTimeRange) -> list[Car]:
        time_to_select = datetime.now(UTC) - timedelta(minutes=conditions.range_time)
        query = select(Car).where(Car.created_at >= time_to_select)
        return await self.get_by_query(query)

    async def delete_car(self, conditions: GetCar) -> None:
        if conditions.model is not None or conditions.plate_number is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete car by model or plate number"
            )
        await self.delete_entity(conditions)


class RoadConditionCrud(CrudEntity[RoadCondition]):
    def __init__(self):
        super().__init__(model=RoadCondition)

    async def create_road_condition(self, payload: RoadConditionCreate) -> RoadCondition:
        return await self.create_entity(payload)

    async def get_road_condition(self, conditions: GetRoadCondition) -> list[RoadCondition]:
        return await self.get_many(conditions)

    async def delete_road_condition(self, conditions: GetRoadCondition) -> None:
        if conditions.road_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete road condition by road id"
            )
        await self.delete_entity(conditions)


class RoadCrud(CrudEntity[Road]):
    def __init__(self):
        super().__init__(model=Road)

    async def create_road(self, road: RoadCreate) -> Road:
        return await self.create_entity(road)

    async def get_road(self, conditions: GetRoad) -> list[Road]:
        return await self.get_many(conditions)

    async def delete_road(self, conditions: GetRoad) -> None:
        await self.delete_entity(conditions)
