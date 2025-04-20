from faststream import FastStream
from faststream.kafka import KafkaBroker
from loguru import logger

from src.analitycs.services import CarService
from src.config import settings
from src.schemas import CarCreate
from src.services.kafka import serializer
from src.utils import Topics

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
