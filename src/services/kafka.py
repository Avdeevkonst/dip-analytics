import json
from typing import Any

from faststream.kafka.fastapi import KafkaRouter

from src.config import settings


def serializer(value: Any) -> bytes:
    return json.dumps(value).encode()


def deserializer(serialized: bytes) -> Any:
    return json.loads(serialized)


kafka_router = KafkaRouter(
    settings.KAFKA_BOOTSTRAP_SERVERS,
    key_serializer=serializer,
    value_serializer=serializer,
)
