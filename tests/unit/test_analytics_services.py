"""Unit tests for analytics services."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from commons.state import State
from src.analytics.services import (
    CarService,
    RoadConditionService,
    RoadService,
    TrafficAnalysisService,
)
from src.commons.models import Car, Road, RoadCondition
from src.commons.schemas import (
    CarCreate,
    GetCar,
    GetRoad,
    GetRoadCondition,
    RoadConditionCreate,
    RoadCreate,
)


class TestCarService:
    """Test cases for CarService."""

    @pytest.fixture
    def service(self) -> CarService:
        """Create CarService instance."""
        return CarService()

    @pytest.mark.asyncio
    async def test_process_sensor_data_new_car(
        self,
        service: CarService,
        car_sensor_data: CarCreate,
    ) -> None:
        """Test processing sensor data for a new car."""
        # Ensure unique plate number
        car_sensor_data.plate_number = f"TEST-{uuid4().hex[:8]}"
        result = await service.process_sensor_data(car_sensor_data)
        assert result.plate_number == car_sensor_data.plate_number
        assert result.model == car_sensor_data.model
        assert result.average_speed == car_sensor_data.average_speed
        assert result.road_id == car_sensor_data.road_id

    @pytest.mark.asyncio
    async def test_get_cars_by_road(
        self,
        service: CarService,
        create_car: Car,
        road_id: UUID,
    ) -> None:
        """Test getting cars by road ID."""
        cars = await service.get_cars_by_road(road_id)
        assert len(cars) > 0
        assert all(car.road_id == road_id for car in cars)

    @pytest.mark.asyncio
    async def test_get_recent_cars(
        self,
        service: CarService,
        create_car: Car,
    ) -> None:
        """Test getting recent cars."""
        # Update car's updated_at to ensure it's within the time range
        cars = await service.get_car(GetCar(id=create_car.id))
        assert len(cars) == 1
        car = cars[0]
        car.updated_at = datetime.now(UTC)

        cars = await service.get_recent_cars(minutes=5)
        assert len(cars) > 0
        assert all(
            car.updated_at >= datetime.now(UTC) - timedelta(minutes=5) for car in cars if car.updated_at is not None
        )

    @pytest.mark.asyncio
    async def test_delete_car(
        self,
        service: CarService,
        create_car: Car,
    ) -> None:
        """Test deleting a car."""
        await service.delete_car(GetCar(id=create_car.id))
        result = await service.get_car(GetCar(id=create_car.id))
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_car(
        self,
        service: CarService,
        create_car: Car,
    ) -> None:
        """Test getting a car by conditions."""
        result = await service.get_car(GetCar(id=create_car.id))
        assert len(result) == 1
        assert result[0].id == create_car.id


class TestRoadConditionService:
    """Test cases for RoadConditionService."""

    @pytest.fixture
    def service(self) -> RoadConditionService:
        """Create RoadConditionService instance."""
        return RoadConditionService()

    @pytest.mark.asyncio
    async def test_create_road_condition(
        self,
        service: RoadConditionService,
        road_condition_data: RoadConditionCreate,
    ) -> None:
        """Test creating a road condition."""
        result = await service.create_road_condition(road_condition_data)
        assert result.road_id == road_condition_data.road_id
        assert result.weather_status == road_condition_data.weather_status
        assert result.jam_status == road_condition_data.jam_status

    @pytest.mark.asyncio
    async def test_delete_road_condition(
        self,
        service: RoadConditionService,
        create_road_condition: RoadCondition,
    ) -> None:
        """Test deleting a road condition."""
        await service.delete_road_condition(
            GetRoadCondition(id=create_road_condition.id),
        )
        result = await service.get_road_condition(
            GetRoadCondition(id=create_road_condition.id),
        )
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_road_condition(
        self,
        service: RoadConditionService,
        create_road_condition: RoadCondition,
    ) -> None:
        """Test getting a road condition by conditions."""
        result = await service.get_road_condition(
            GetRoadCondition(id=create_road_condition.id),
        )
        assert len(result) == 1
        assert result[0].id == create_road_condition.id


class TestRoadService:
    """Test cases for RoadService."""

    @pytest.fixture
    def service(self) -> RoadService:
        """Create RoadService instance."""
        return RoadService()

    @pytest.mark.asyncio
    async def test_create_road(
        self,
        service: RoadService,
        create_road: Road,
    ) -> None:
        """Test creating a road."""
        payload = RoadCreate(
            name=f"ROAD-{uuid4().hex[:8]}",  # Generate unique name
            length=create_road.length,
            start=create_road.start,
            end=create_road.end,
            city=create_road.city,
            description=create_road.description,
            street=create_road.street,
        )
        result = await service.create_road(payload)
        assert result.name == payload.name
        assert result.length == payload.length
        assert result.start == payload.start
        assert result.end == payload.end
        assert result.city == payload.city
        assert result.description == payload.description
        assert result.street == payload.street

    @pytest.mark.asyncio
    async def test_delete_road(
        self,
        service: RoadService,
        create_road: Road,
    ) -> None:
        """Test deleting a road."""
        # Delete in correct order to avoid foreign key constraints
        traffic_service = TrafficAnalysisService()
        car_service = CarService()
        road_condition_service = RoadConditionService()

        # Delete traffic measurements first
        async with traffic_service.traffic_crud.uow:
            await traffic_service.traffic_crud.delete_traffic_measurement(road_id=create_road.id)

        # Delete cars
        async with car_service.crud.uow:
            await car_service.delete_car(GetCar(road_id=create_road.id))

        # Delete road conditions
        async with road_condition_service.crud.uow:
            await road_condition_service.delete_road_condition(GetRoadCondition(road_id=create_road.id))

        # Delete road capacity
        async with traffic_service.capacity_crud.uow:
            await traffic_service.capacity_crud.delete_road_capacity(road_id=create_road.id)

        # Finally delete the road
        async with service.crud.uow:
            await service.delete_road(GetRoad(id=create_road.id))

        # Verify road is deleted
        async with service.crud.uow:
            roads = await service.get_road(GetRoad(id=create_road.id))
            assert not roads

    @pytest.mark.asyncio
    async def test_get_road(
        self,
        service: RoadService,
        create_road: Road,
    ) -> None:
        """Test getting a road by conditions."""
        result = await service.get_road(GetRoad(id=create_road.id))
        assert len(result) == 1
        assert result[0].id == create_road.id


class TestTrafficAnalysisService:
    """Test cases for TrafficAnalysisService."""

    @pytest.fixture
    def service(self) -> TrafficAnalysisService:
        """Create TrafficAnalysisService instance."""
        return TrafficAnalysisService()

    @pytest.mark.asyncio
    async def test_analyze_traffic_no_cars(
        self,
        service: TrafficAnalysisService,
        create_road: Road,
    ) -> None:
        """Test analyzing traffic with no cars on the road."""
        # Delete all cars and traffic measurements from the road first
        car_service = CarService()
        async with car_service.crud.uow:
            await car_service.delete_car(GetCar(road_id=create_road.id))

        async with service.traffic_crud.uow:
            await service.traffic_crud.delete_traffic_measurement(road_id=create_road.id)

        # Analyze traffic
        result = await service.analyze_traffic(road_id=create_road.id)

        # Verify no traffic data
        assert result.flow_rate == 0
        assert result.density == 0
        assert result.current_speed == 0

    @pytest.mark.asyncio
    async def test_analyze_traffic_with_cars(
        self,
        service: TrafficAnalysisService,
        create_car: Car,
        create_road: Road,
    ) -> None:
        """Test analyzing traffic with cars on the road."""
        result = await service.analyze_traffic(create_road.id)
        assert result.current_speed > 0
        assert result.flow_rate > 0
        assert result.density > 0
        assert result.congestion_level >= 0
        assert result.state in [State("LOW"), State("MEDIUM"), State("HIGH")]
        assert result.trend in ["INCREASING", "DECREASING", "STABLE"]
