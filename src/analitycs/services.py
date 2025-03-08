from typing import Final

from src.analitycs.cruds import CarCrud
from src.config import settings
from src.models import Car
from src.schemas import CarCreate, GetCar
from src.services.db import PgUnitOfWork

UOW: Final = settings.db_url_postgresql


class CarService:
    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork(UOW)
        self.crud: CarCrud = CarCrud(self.uow)

    async def create_car(self, payload: CarCreate) -> Car:
        car = await self.crud.create_car(payload)
        await self.uow.commit()
        return car

    async def delete_car(self, params: GetCar) -> None:
        await self.crud.delete_car(params)
        await self.uow.commit()

    async def get_car(self, params: GetCar) -> list[Car]:
        return await self.crud.get_car(params)
