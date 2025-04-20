from fastapi import HTTPException

from src.models import Car, RoadCondition
from src.schemas import CarCreate, GetCar, GetRoadCondition, RoadConditionCreate
from src.services.db import CrudEntity


class CarCrud(CrudEntity):
    def __init__(self):
        super().__init__(model=Car)

    async def create_car(self, car: CarCreate) -> Car:
        return await self.create_entity(car)

    async def get_car(self, conditions: GetCar) -> list[Car]:
        return await self.get_many(conditions)

    async def delete_car(self, conditions: GetCar) -> None:
        if conditions.model is not None or conditions.plate_number is not None:
            raise HTTPException(status_code=400, detail="Cannot delete car by model or plate number")
        await self.delete_entity(conditions)


class RoadConditionCrud(CrudEntity):
    def __init__(self):
        super().__init__(model=RoadCondition)

    async def create_road_condition(self, payload: RoadConditionCreate) -> RoadCondition:
        return await self.create_entity(payload)

    async def get_road_condition(self, conditions: GetRoadCondition) -> list[RoadCondition]:
        return await self.get_many(conditions)

    async def delete_road_condition(self, conditions: GetRoadCondition) -> None:
        if conditions.road_id is not None:
            raise HTTPException(status_code=400, detail="Cannot delete road condition by road id")
        await self.delete_entity(conditions)
