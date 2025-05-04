import json
from typing import Any


def serializer(to_serialize: Any) -> bytes:
    """
    Serialize the data to bytes.
    """
    return json.dumps(to_serialize).encode()


def deserializer(serialized: bytes) -> Any:
    """
    Deserialize the data from bytes.
    """
    return json.loads(serialized)
