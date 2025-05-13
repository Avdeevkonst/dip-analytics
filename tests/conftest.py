import random
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.commons.enums import Jam, Weather
from src.commons.models import Base, Car, Road, RoadCapacity, RoadCondition, TrafficMeasurement
from src.commons.schemas import CarCreate, RoadConditionCreate

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:avdeev97@172.18.0.2:5432/dip_analytics"

# Create async engine for tests
engine = create_async_engine(TEST_DATABASE_URL, echo=True, poolclass=NullPool)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def test_db_setup() -> AsyncGenerator:
    """Set up test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for a test."""
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator:
    """Create a new async client."""
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def create_road() -> Road:
    """Create a test road."""
    stmt = Road(
        name=f"ROAD-{uuid4().hex[:8]}",
        length=random.randint(1000, 10000),
        start="Test Start",
        end="Test End",
        city="Test City",
        description="Test Description",
        street="Test Street",
    )
    async with async_session() as session:
        session.add(stmt)
        await session.commit()
    return stmt


@pytest_asyncio.fixture(autouse=True)
async def create_car(create_road: Road) -> Car:
    """Create a test car."""
    stmt = Car(
        plate_number=f"TEST{random.randint(1000, 9999)}",
        model="Toyota",
        average_speed=60,
        road_id=create_road.id,
    )
    async with async_session() as session:
        session.add(stmt)
        await session.commit()
    return stmt


@pytest_asyncio.fixture(autouse=True)
async def create_road_condition(create_road: Road) -> RoadCondition:
    """Create a test road condition."""
    stmt = RoadCondition(
        road_id=create_road.id,
        weather_status=Weather.SNOWY,
        jam_status=Jam.LOW,
        name=f"Test Road Condition {random.randint(1000, 9999)}",
        description="Test Description",
    )
    async with async_session() as session:
        session.add(stmt)
        await session.commit()
    return stmt


@pytest_asyncio.fixture(autouse=True)
async def create_traffic_measurement(create_road: Road) -> TrafficMeasurement:
    """Create a test traffic measurement."""
    stmt = TrafficMeasurement(
        road_id=create_road.id,
        timestamp=datetime.now(UTC),
        average_speed=60,
        flow_rate=1000,
        density=1000,
    )
    async with async_session() as session:
        session.add(stmt)
        await session.commit()
    return stmt


@pytest_asyncio.fixture(autouse=True)
async def create_road_capacity(create_road: Road) -> RoadCapacity:
    """Create a test road capacity."""
    stmt = RoadCapacity(
        road_id=create_road.id,
        lanes=random.randint(1, 4),
        speed_limit=random.randint(10, 120),
        max_capacity=random.randint(1000, 10000),
        name=f"Test Road Capacity {random.randint(1000, 9999)}",
        description="Test Description",
    )
    async with async_session() as session:
        session.add(stmt)
        await session.commit()
    return stmt


@pytest.fixture(autouse=True)
def car_sensor_data(create_road: Road) -> CarCreate:
    """Create a test car sensor data."""
    return CarCreate(
        plate_number=f"TEST {random.randint(1000, 9999)}",
        model=random.choice(
            ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes", "Audi", "Volkswagen", "Hyundai"]
        ),
        average_speed=random.randint(10, 120),
        road_id=create_road.id,
    )


@pytest.fixture
def road_id(create_road: Road) -> UUID:
    """Get road ID from created road."""
    return create_road.id


@pytest.fixture
def road_condition_data(create_road: Road) -> RoadConditionCreate:
    """Create test road condition data."""
    return RoadConditionCreate(
        road_id=create_road.id,
        weather_status=Weather.SNOWY,
        jam_status=Jam.LOW,
        name=f"Test Road Condition {random.randint(1000, 9999)}",
        description="Test Description",
    )
