from datetime import UTC, datetime
from uuid import UUID

from loguru import logger

from src.analytics.cruds import (
    CarCrud,
    RoadCapacityCrud,
    RoadConditionCrud,
    RoadCrud,
    TrafficMeasurementCrud,
)
from src.commons.enums import State
from src.commons.models import Car, Road, RoadCondition
from src.commons.schemas import (
    CarCreate,
    GetCar,
    GetCarByTimeRange,
    GetRoad,
    GetRoadCondition,
    RoadConditionCreate,
    RoadCreate,
    TrafficAnalysis,
    TrafficMeasurementCreate,
)
from src.decorators import monitor_traffic_congestion
from src.services.db import PgUnitOfWork


class CarService:
    """Service for processing and managing car data from sensors."""

    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: CarCrud = CarCrud(uow=self.uow)
        self.traffic_analyzer = TrafficAnalysisService()

    async def process_sensor_data(self, payload: CarCreate) -> Car:
        """Process incoming sensor data and update car information.

        Args:
            payload: Raw sensor data

        Returns:
            Updated car record
        """
        async with self.uow:
            # Try to find existing car record
            cars = await self.crud.get_car(GetCar(plate_number=payload.plate_number))

            if cars:
                # Calculate new average speed
                existing_car = cars[0]
                new_speed = (existing_car.average_speed + payload.average_speed) // 2
                payload.average_speed = new_speed

                # Update car data
                updated_car = await self.crud.update_car(
                    GetCar(id=existing_car.id),
                    payload,
                )
                logger.info(f"Updated car data: {updated_car}")

                # Update traffic measurements if car has road_id
                if updated_car.road_id:
                    road_cars = await self.get_cars_by_road(updated_car.road_id)
                    await self.traffic_analyzer.update_traffic_measurement(road_id=updated_car.road_id, cars=road_cars)

                return updated_car

            # Create new car record
            new_car = await self.crud.create_car(
                payload,
            )
            logger.info(f"Created new car record: {new_car}")

            # Update traffic measurements if new car has road_id
            if new_car.road_id:
                road_cars = await self.get_cars_by_road(new_car.road_id)
                await self.traffic_analyzer.update_traffic_measurement(road_id=new_car.road_id, cars=road_cars)

            return new_car

    async def get_cars_by_road(self, road_id: UUID) -> list[Car]:
        """Get all cars currently on a specific road."""
        async with self.uow:
            return await self.crud.get_many(GetCar(road_id=road_id))

    async def get_recent_cars(self, minutes: int = 5) -> list[Car]:
        """Get cars updated within the last N minutes."""
        async with self.uow:
            return await self.crud.get_car_by_time_range(GetCarByTimeRange(range_time=minutes))

    async def delete_car(self, conditions: GetCar) -> None:
        """Delete a car record."""
        async with self.uow:
            await self.crud.delete_car(conditions)

    async def get_car(self, conditions: GetCar) -> list[Car]:
        """Get car records by conditions."""
        async with self.uow:
            return await self.crud.get_car(conditions)


class RoadConditionService:
    """
    Service for creating, deleting, and getting road conditions.
    """

    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: RoadConditionCrud = RoadConditionCrud(uow=self.uow)

    async def create_road_condition(self, payload: RoadConditionCreate) -> RoadCondition:
        """
        Create a road condition.
        """
        async with self.uow:
            return await self.crud.create_road_condition(payload)

    async def delete_road_condition(self, conditions: GetRoadCondition) -> None:
        """
        Delete a road condition.
        """
        async with self.uow:
            await self.crud.delete_road_condition(conditions)

    async def get_road_condition(self, conditions: GetRoadCondition) -> list[RoadCondition]:
        """
        Get a road condition.
        """
        async with self.uow:
            return await self.crud.get_road_condition(conditions)


class RoadService:
    """
    Service for creating, deleting, and getting roads.
    """

    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.crud: RoadCrud = RoadCrud(uow=self.uow)

    async def create_road(self, payload: RoadCreate) -> Road:
        """
        Create a road.
        """
        async with self.uow:
            return await self.crud.create_road(payload)

    async def delete_road(self, conditions: GetRoad) -> None:
        """
        Delete a road.
        """
        async with self.uow:
            await self.crud.delete_road(conditions)

    async def get_road(self, conditions: GetRoad) -> list[Road]:
        """
        Get a road.
        """
        async with self.uow:
            return await self.crud.get_road(conditions)


class TrafficAnalysisService:
    """Service for analyzing traffic conditions."""

    def __init__(self) -> None:
        self.uow: PgUnitOfWork = PgUnitOfWork()
        self.car_crud = CarCrud(uow=self.uow)
        self.traffic_crud = TrafficMeasurementCrud(uow=self.uow)
        self.capacity_crud = RoadCapacityCrud(uow=self.uow)
        self.road_crud = RoadCrud(uow=self.uow)
        self.window_size = 5  # minutes

    @monitor_traffic_congestion
    async def analyze_traffic(self, road_id: UUID) -> TrafficAnalysis:
        """
        Analyze current traffic state for a road segment.

        Args:
            road_id: Road segment ID

        Returns:
            Traffic analysis results
        """
        async with self.uow:
            # Get road capacity data
            capacity = await self.capacity_crud.get_road_capacity(road_id)

            # Get recent measurements
            measurements = await self.traffic_crud.get_recent_measurements(road_id=road_id, minutes=self.window_size)

            if not measurements:
                # Get cars on the road to determine initial state
                cars = await self.car_crud.get_many(GetCar(road_id=road_id))
                if not cars:
                    return TrafficAnalysis(
                        current_speed=0,
                        flow_rate=0,
                        density=0,
                        congestion_level=0,
                        state=State("UNSTAGED"),
                        trend="STABLE",
                    )

                # Calculate initial state from current cars
                avg_speed = sum(car.average_speed for car in cars) / len(cars)
                flow_rate = len(cars) * 3600  # cars per hour
                density = len(cars) / capacity.lanes  # cars per lane
                congestion_level = density / capacity.max_capacity

                return TrafficAnalysis(
                    current_speed=avg_speed,
                    flow_rate=flow_rate,
                    density=density,
                    congestion_level=congestion_level,
                    state=self._determine_state(congestion_level),
                    trend="STABLE",
                )

            # Calculate metrics from measurements
            latest = measurements[0]
            trend = self._determine_trend(measurements)

            congestion_level = latest.density / capacity.max_capacity
            return TrafficAnalysis(
                current_speed=latest.average_speed,
                flow_rate=latest.flow_rate,
                density=latest.density,
                congestion_level=congestion_level,
                state=self._determine_state(congestion_level),
                trend=trend,
            )

    def _determine_state(self, congestion_level: float) -> State:
        """
        Determine traffic state based on congestion level.

        Args:
            congestion_level: Current congestion level

        Returns:
            Traffic state
        """
        if congestion_level >= 0.8:
            return State("HIGH")
        elif congestion_level >= 0.4:
            return State("MEDIUM")
        else:
            return State("LOW")

    def _determine_trend(self, measurements: list) -> str:
        """Determine traffic trend based on recent measurements."""
        if len(measurements) < 2:
            return "STABLE"

        latest = measurements[0].density
        previous = measurements[1].density

        if latest > previous * 1.1:
            return "INCREASING"
        elif latest < previous * 0.9:
            return "DECREASING"
        return "STABLE"

    async def update_traffic_measurement(self, road_id: UUID, cars: list[Car]) -> None:
        """
        Update traffic measurements for a road segment.

        Args:
            road_id: Road segment ID
            cars: List of cars currently on the road segment
        """
        if not cars:
            return

        async with self.uow:
            # Calculate metrics
            average_speed = sum(car.average_speed for car in cars) / len(cars)

            # Get road length
            road = await self.road_crud.get_road_by_id(road_id=road_id)

            if not road:
                raise ValueError(f"Road {road_id} not found")

            # Calculate flow rate and density
            flow_rate = len(cars) * 3600  # Assuming measurement period is 1 second
            density = len(cars) / road.length if road.length > 0 else 0

            # Create new measurement
            measurement = TrafficMeasurementCreate(
                road_id=road_id,
                timestamp=datetime.now(UTC),
                average_speed=average_speed,
                flow_rate=flow_rate,
                density=density,
            )

            await self.traffic_crud.create_measurement(measurement)
