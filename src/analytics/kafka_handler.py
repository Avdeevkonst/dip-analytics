from faststream import FastStream
from faststream.kafka import KafkaBroker
from loguru import logger

from src.analytics.services import CarService, RoadConditionService, RoadService
from src.commons.schemas import CarCreate, RoadConditionCreate, RoadCreate
from src.config import settings
from src.enums import Topics
from src.services.kafka import serializer

broker = KafkaBroker(
    settings.KAFKA_BOOTSTRAP_SERVERS,
    key_serializer=serializer,
    value_serializer=serializer,
)
app = FastStream(broker)


@broker.subscriber(Topics.CAR.value)
async def process_car_data(msg: CarCreate):
    """
    Process car data from traffic sensors.
    Aggregates data if car was seen by multiple sensors.
    """
    car_service = CarService()
    await car_service.process_sensor_data(msg)
    logger.info(f"Processed car data from sensor: {msg.plate_number}")


@broker.subscriber(Topics.ROAD_CONDITION.value)
async def create_road_condition(msg: RoadConditionCreate):
    """
    Subscriber for creating a road condition.
    """
    await RoadConditionService().create_road_condition(payload=msg)
    logger.info(f"Road condition created: {msg}")


@broker.subscriber(Topics.ROAD.value)
async def create_road(msg: RoadCreate):
    """
    Subscriber for creating a road.
    """
    await RoadService().create_road(payload=msg)
    logger.info(f"Road created: {msg}")
