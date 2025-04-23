import json
from typing import Any

from faststream.kafka import KafkaBroker

from src.config import settings


def serializer(value: Any) -> bytes:
    return json.dumps(value).encode()


def deserializer(serialized: bytes) -> Any:
    return json.loads(serialized)


kafka_broker = KafkaBroker(settings.KAFKA_BOOTSTRAP_SERVERS)
