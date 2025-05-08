from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select

from src.commons.models import Car, Road, RoadCapacity, RoadCondition, TrafficMeasurement
from src.commons.schemas import (
    CarCreate,
    GetCar,
    GetCarByTimeRange,
    GetRoad,
    GetRoadCapacity,
    GetRoadCondition,
    GetTrafficMeasurement,
    RoadCapacityCreate,
    RoadConditionCreate,
    RoadCreate,
    TrafficMeasurementCreate,
)
from src.services.db import CrudEntity, PgUnitOfWork


class CarCrud(CrudEntity[Car]):
    """
    CRUD operations for Car model.
    """

    def __init__(self, uow: PgUnitOfWork):
        super().__init__(model=Car, uow=uow)

    async def create_car(self, car: CarCreate) -> Car:
        """
        Create a car.
        """
        return await self.create_entity(car)

    async def update_car(self, conditions: GetCar, car: CarCreate) -> Car:
        """
        Update a car.

        Args:
            conditions: Conditions to find the car
            car: New car data

        Returns:
            Updated car
        """
        # Get existing car first
        existing_cars = await self.get_car(conditions)
        if not existing_cars:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Car with plate number {conditions.plate_number} not found",
            )
        existing_car = existing_cars[0]

        # Calculate new average speed
        new_avg_speed = (existing_car.average_speed + car.average_speed) // 2

        # Update car data
        return await self.update_entity(
            conditions,
            car.model_copy(update={"average_speed": new_avg_speed}),
        )

    async def get_car(self, conditions: GetCar) -> list[Car]:
        """
        Get a car.
        """
        return await self.get_many(conditions)

    async def get_car_by_time_range(self, conditions: GetCarByTimeRange) -> list[Car]:
        """
        Get a car by time range.
        """
        time_to_select = datetime.now(UTC) - timedelta(minutes=conditions.range_time)
        query = select(Car).where(Car.created_at >= time_to_select)
        return await self.get_by_query(query)

    async def delete_car(self, conditions: GetCar) -> None:
        """
        Delete a car.
        """
        await self.delete_entity(conditions)


class RoadConditionCrud(CrudEntity[RoadCondition]):
    """
    CRUD operations for RoadCondition model.
    """

    def __init__(self, uow: PgUnitOfWork):
        super().__init__(model=RoadCondition, uow=uow)

    async def create_road_condition(self, payload: RoadConditionCreate) -> RoadCondition:
        """
        Create a road condition.
        """
        return await self.create_entity(payload)

    async def get_road_condition(self, conditions: GetRoadCondition) -> list[RoadCondition]:
        """
        Get a road condition.
        """
        return await self.get_many(conditions)

    async def delete_road_condition(self, conditions: GetRoadCondition) -> None:
        """
        Delete a road condition.
        """
        await self.delete_entity(conditions)


class RoadCrud(CrudEntity[Road]):
    """
    CRUD operations for Road model.
    """

    def __init__(self, uow: PgUnitOfWork):
        super().__init__(model=Road, uow=uow)

    async def create_road(self, road: RoadCreate) -> Road:
        """
        Create a road.
        """
        return await self.create_entity(road)

    async def get_road(self, conditions: GetRoad) -> list[Road]:
        """
        Get a road.
        """
        return await self.get_many(conditions)

    async def get_road_by_id(self, road_id: UUID) -> Road:
        """
        Get a road by id.
        """
        return await self.get_entity_by_conditions(GetRoad(id=road_id))

    async def delete_road(self, conditions: GetRoad) -> None:
        """
        Delete a road.
        """
        await self.delete_entity(conditions)


class TrafficMeasurementCrud(CrudEntity[TrafficMeasurement]):
    """CRUD operations for TrafficMeasurement model."""

    def __init__(self, uow: PgUnitOfWork):
        super().__init__(model=TrafficMeasurement, uow=uow)

    async def create_measurement(self, measurement: TrafficMeasurementCreate) -> TrafficMeasurement:
        """Create a traffic measurement."""
        return await self.create_entity(measurement)

    async def get_recent_measurements(self, road_id: UUID, minutes: int = 5) -> list[TrafficMeasurement]:
        """Get recent measurements for a road."""
        time_to_select = datetime.now(UTC) - timedelta(minutes=minutes)
        query = (
            select(TrafficMeasurement)
            .where(TrafficMeasurement.road_id == road_id, TrafficMeasurement.timestamp >= time_to_select)
            .order_by(TrafficMeasurement.timestamp.desc())
        )
        return await self.get_by_query(query)

    async def delete_traffic_measurement(self, road_id: UUID) -> None:
        """Delete all traffic measurements for a road."""
        query = select(TrafficMeasurement).where(TrafficMeasurement.road_id == road_id)
        measurements = await self.get_by_query(query)
        for measurement in measurements:
            await self.delete_entity(GetTrafficMeasurement(id=measurement.id))


class RoadCapacityCrud(CrudEntity[RoadCapacity]):
    """CRUD operations for RoadCapacity model."""

    def __init__(self, uow: PgUnitOfWork):
        super().__init__(model=RoadCapacity, uow=uow)

    async def create_capacity(self, capacity: RoadCapacityCreate) -> RoadCapacity:
        """Create road capacity information."""
        return await self.create_entity(capacity)

    async def get_road_capacity(self, road_id: UUID) -> RoadCapacity:
        """Get road capacity information."""
        result = await self.one_or_none(GetRoadCapacity(road_id=road_id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Road capacity information not found for road {road_id}"
            )
        return result

    async def delete_road_capacity(self, road_id: UUID) -> None:
        """Delete road capacity information."""
        query = select(RoadCapacity).where(RoadCapacity.road_id == road_id)
        capacities = await self.get_by_query(query)
        for capacity in capacities:
            await self.delete_entity(GetRoadCapacity(id=capacity.id))
