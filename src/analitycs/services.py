import math
from datetime import UTC, datetime

from src.analitycs.cruds import CarCrud, RoadConditionCrud, RoadCrud
from src.decorators import monitor_traffic_congestion
from src.models import Car, Road, RoadCondition
from src.schemas import CarCreate, GetCar, GetCarByTimeRange, GetRoad, GetRoadCondition, RoadConditionCreate, RoadCreate
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


class TrafficAnalysisService:
    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: CarCrud = CarCrud()

    @monitor_traffic_congestion
    async def analyze_traffic_congestion(self, minutes: int = 5) -> dict:
        """
        Analyze traffic congestion based on car data from the last N minutes.
        Returns a dictionary with congestion level and details.
        """
        self.uow.activate()

        # Get all cars from the last N minutes
        recent_cars = await self.crud.get_car_by_time_range(GetCarByTimeRange(range_time=minutes))

        if not recent_cars:
            return {
                "congestion_level": "LOW",
                "message": "No recent car data available",
                "average_speed": 0,
                "car_count": 0,
            }

        # Calculate average speed
        total_speed = sum(car.avarage_speed for car in recent_cars)
        average_speed = total_speed / len(recent_cars)

        # Analyze location changes
        location_changes = []
        for i in range(len(recent_cars) - 1):
            car1 = recent_cars[i]
            car2 = recent_cars[i + 1]
            if car1.plate_number == car2.plate_number:
                R = 6371

                lat1, lon1 = math.radians(car1.latitude), math.radians(car1.longitude)
                lat2, lon2 = math.radians(car2.latitude), math.radians(car2.longitude)

                dlat = lat2 - lat1
                dlon = lon2 - lon1

                a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                distance = R * c

                time_diff = (car2.created_at - car1.created_at).total_seconds() / 3600

                if time_diff > 0:
                    speed = distance / time_diff
                    location_changes.append(speed)

        if not location_changes:
            congestion_level = "LOW"
        else:
            avg_location_speed = sum(location_changes) / len(location_changes)
            match avg_location_speed:
                case avg_location_speed if avg_location_speed < 5:
                    congestion_level = "HIGH"
                case avg_location_speed if avg_location_speed < 20:
                    congestion_level = "MEDIUM"
                case _:
                    congestion_level = "LOW"

        return {
            "congestion_level": congestion_level,
            "average_speed": round(average_speed, 2),
            "car_count": len(recent_cars),
            "location_based_speed": round(avg_location_speed, 2) if location_changes else 0,
            "timestamp": datetime.now(UTC).isoformat(),
        }
