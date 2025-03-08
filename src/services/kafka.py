import asyncio
import json
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, ConsumerRecord
from loguru import logger
from pydantic import BaseModel, ValidationError

from src.analitycs.services import CarService
from src.schemas import CarCreate
from src.services.db import Singleton
from src.utils import Topics


class KafkaManager(Singleton):
    def __init__(
        self,
        *,
        bootstrap_servers: str,
        topics_consume: list[str],
    ):
        self.loop = asyncio.get_event_loop()
        self.topics = topics_consume
        self.producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=self.serializer,
            loop=self.loop,
        )
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=bootstrap_servers,
            loop=self.loop,
            value_deserializer=self.deserializer,
        )

    async def send_one(self, topic: str, payload: dict, **kw: Any):
        await self.producer.send(topic=topic, value=payload, **kw)

    def serializer(self, value: Any) -> bytes:
        return json.dumps(value).encode()

    def deserializer(self, serialized: bytes) -> Any:
        return json.loads(serialized)

    async def distribute_responsibilities(self) -> None:
        async for msg in self.consumer:
            match msg.topic:
                case Topics.CAR.value:
                    payload = self.validate(msg, CarCreate)
                    if payload:
                        await CarService().create_car(payload=payload)  # pyright:ignore[reportArgumentType]
                case _:
                    continue
            if self.consumer._closed:
                return

    async def close(self):
        await self.consumer.stop()
        await self.producer.stop()

    def validate(self, msg: ConsumerRecord, base_model: type[BaseModel]):
        try:
            return base_model.model_validate(msg.value)
        except ValidationError as e:
            logger.info(f"Error validating message: {e}")
