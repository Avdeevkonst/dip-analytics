from fastapi import HTTPException

from src.models import Car
from src.schemas import CarCreate, GetCar
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
