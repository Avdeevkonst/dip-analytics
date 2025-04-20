from src.analitycs.cruds import CarCrud, RoadConditionCrud, RoadCrud
from src.models import Car, Road, RoadCondition
from src.schemas import CarCreate, GetCar, GetRoad, GetRoadCondition, RoadConditionCreate, RoadCreate
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


class RoadConditionService:
    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: RoadConditionCrud = RoadConditionCrud()

    async def create_road_condition(self, payload: RoadConditionCreate) -> RoadCondition:
        self.uow.activate()
        road_condition = await self.crud.create_road_condition(payload)
        await self.uow.commit()
        return road_condition

    async def delete_road_condition(self, params: GetRoadCondition) -> None:
        self.uow.activate()
        await self.crud.delete_road_condition(params)
        await self.uow.commit()

    async def get_road_condition(self, params: GetRoadCondition) -> list[RoadCondition]:
        self.uow.activate()
        return await self.crud.get_road_condition(params)


class RoadService:
    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: RoadCrud = RoadCrud()

    async def create_road(self, payload: RoadCreate) -> Road:
        self.uow.activate()
        road = await self.crud.create_road(payload)
        await self.uow.commit()
        return road

    async def delete_road(self, params: GetRoad) -> None:
        self.uow.activate()
        await self.crud.delete_road(params)
        await self.uow.commit()

    async def get_road(self, params: GetRoad) -> list[Road]:
        self.uow.activate()
        return await self.crud.get_road(params)
