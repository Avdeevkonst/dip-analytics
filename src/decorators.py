from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, TypeVar

from loguru import logger

RT = TypeVar("RT")


def monitor_traffic_congestion(func: Callable[..., Coroutine[Any, Any, RT]]) -> Callable[..., Coroutine[Any, Any, RT]]:
    """
    Decorator that monitors traffic congestion and calls the decorated function
    with the current state (True for HIGH congestion, False for LOW).
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> RT:
        try:
            # Get current congestion data

            # Determine state based on congestion level
            result = await func(*args, **kwargs)

            # TODO: put state and result in class that will be handle by traffic state manager

            # Call the decorated function with the state
            return result  # noqa: RET504

        except Exception as e:
            logger.error(f"Error in traffic monitoring: {e!s}")
            raise

    return wrapper
