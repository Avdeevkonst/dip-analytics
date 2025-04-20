from src.analitycs.cruds import CarCrud
from src.models import Car
from src.schemas import CarCreate, GetCar
from src.services.db import PgUnitOfWork


class CarService:
    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: CarCrud = CarCrud()

    async def create_car(self, payload: CarCreate) -> Car:
        self.uow.activate()
        car = await self.crud.create_car(payload)
        await self.uow.commit()
        return car

    async def delete_car(self, params: GetCar) -> None:
        self.uow.activate()
        await self.crud.delete_car(params)
        await self.uow.commit()

    async def get_car(self, params: GetCar) -> list[Car]:
        self.uow.activate()
        return await self.crud.get_car(params)
