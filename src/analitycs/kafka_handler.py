from faststream import FastStream
from faststream.kafka import KafkaBroker
from loguru import logger

from project_utils import Topics
from src.analitycs.services import CarService, RoadConditionService, RoadService
from src.config import settings
from src.schemas import CarCreate, RoadConditionCreate, RoadCreate
from src.services.kafka import serializer

broker = KafkaBroker(
    settings.KAFKA_BOOTSTRAP_SERVERS,
    key_serializer=serializer,
    value_serializer=serializer,
)
app = FastStream(broker)


@broker.subscriber(Topics.CAR.value)
async def create_car(msg: CarCreate):
    await CarService().create_car(payload=msg)
    logger.info(f"Car created: {msg}")


@broker.subscriber(Topics.ROAD_CONDITION.value)
async def create_road_condition(msg: RoadConditionCreate):
    await RoadConditionService().create_road_condition(payload=msg)
    logger.info(f"Road condition created: {msg}")


@broker.subscriber(Topics.ROAD.value)
async def create_road(msg: RoadCreate):
    await RoadService().create_road(payload=msg)
    logger.info(f"Road created: {msg}")
