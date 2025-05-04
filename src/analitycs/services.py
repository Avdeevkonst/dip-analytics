import math
from datetime import UTC, datetime

from src.analitycs.cruds import CarCrud, RoadConditionCrud, RoadCrud
from src.decorators import monitor_traffic_congestion
from src.models import Car, Road, RoadCondition
from src.schemas import CarCreate, GetCar, GetCarByTimeRange, GetRoad, GetRoadCondition, RoadConditionCreate, RoadCreate
from src.services.db import PgUnitOfWork

HIGH = 5
MEDIUM = 20
LOW = 40
RADIUS = 6371
SECONDS_IN_HOUR = 3600


class CarService:
    """
    Service for creating, deleting, and getting cars.
    """

    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: CarCrud = CarCrud()

    async def create_car(self, payload: CarCreate) -> Car:
        """
        Create a car.
        """
        self.uow.activate()
        car = await self.crud.create_car(payload)
        await self.uow.commit()
        return car

    async def delete_car(self, conditions: GetCar) -> None:
        """
        Delete a car.
        """
        self.uow.activate()
        await self.crud.delete_car(conditions)
        await self.uow.commit()

    async def get_car(self, conditions: GetCar) -> list[Car]:
        """
        Get a car.
        """
        self.uow.activate()
        return await self.crud.get_car(conditions)


class RoadConditionService:
    """
    Service for creating, deleting, and getting road conditions.
    """

    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: RoadConditionCrud = RoadConditionCrud()

    async def create_road_condition(self, payload: RoadConditionCreate) -> RoadCondition:
        """
        Create a road condition.
        """
        self.uow.activate()
        road_condition = await self.crud.create_road_condition(payload)
        await self.uow.commit()
        return road_condition

    async def delete_road_condition(self, conditions: GetRoadCondition) -> None:
        """
        Delete a road condition.
        """
        self.uow.activate()
        await self.crud.delete_road_condition(conditions)
        await self.uow.commit()

    async def get_road_condition(self, conditions: GetRoadCondition) -> list[RoadCondition]:
        """
        Get a road condition.
        """
        self.uow.activate()
        return await self.crud.get_road_condition(conditions)


class RoadService:
    """
    Service for creating, deleting, and getting roads.
    """

    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: RoadCrud = RoadCrud()

    async def create_road(self, payload: RoadCreate) -> Road:
        """
        Create a road.
        """
        self.uow.activate()
        road = await self.crud.create_road(payload)
        await self.uow.commit()
        return road

    async def delete_road(self, conditions: GetRoad) -> None:
        """
        Delete a road.
        """
        self.uow.activate()
        await self.crud.delete_road(conditions)
        await self.uow.commit()

    async def get_road(self, conditions: GetRoad) -> list[Road]:
        """
        Get a road.
        """
        self.uow.activate()
        return await self.crud.get_road(conditions)


class TrafficAnalysisService:
    """
    Service for analyzing traffic congestion.
    """

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
        average_speed = calculate_average_speed(recent_cars)
        # Analyze location changes
        location_changes = calculate_distance(recent_cars)
        avg_location_speed = sum(location_changes) / len(location_changes)
        congestion_level = calculate_congestion_level(average_speed)

        return {
            "congestion_level": congestion_level,
            "average_speed": round(average_speed, 2),
            "car_count": len(recent_cars),
            "location_based_speed": round(avg_location_speed, 2),
            "timestamp": datetime.now(UTC).isoformat(),
        }


def calculate_distance(recent_cars: list[Car]) -> list[float]:
    location_changes = []
    # find the same car and put list of it in the loc list
    # TODO: rework algorithm to find the same car

    for car in range(len(recent_cars) - 1):
        car1 = recent_cars[car]
        car2 = recent_cars[car + 1]
        if car1.plate_number == car2.plate_number:
            time_diff = calculate_time_diff(car1, car2)

            if time_diff > 0:
                distance = calculate_distance_between_two_cars(car1, car2)
                speed = distance / time_diff
                location_changes.append(speed)

    return location_changes


def calculate_average_speed(recent_cars: list[Car]) -> float:
    """
    Calculate the average speed of the cars.
    """
    total_speed = sum(car.avarage_speed for car in recent_cars)
    return total_speed / len(recent_cars)


def calculate_congestion_level(average_speed: float) -> str:
    """
    Calculate the congestion level based on the average speed.
    """
    if average_speed < HIGH:
        return "HIGH"
    elif average_speed < MEDIUM:
        return "MEDIUM"
    else:
        return "LOW"


def calculate_distance_between_two_cars(car1: Car, car2: Car) -> float:
    """
    Calculate the distance between two cars.
    """
    lat1 = math.radians(car1.latitude)
    lon1 = math.radians(car1.longitude)
    lat2 = math.radians(car2.latitude)
    lon2 = math.radians(car2.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return RADIUS * c


def calculate_time_diff(car1: Car, car2: Car) -> float:
    """
    Calculate the time difference between two cars.
    """
    return (car2.created_at - car1.created_at).total_seconds() / SECONDS_IN_HOUR
