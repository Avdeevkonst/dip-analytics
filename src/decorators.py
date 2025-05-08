from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, TypeVar

from loguru import logger

from src.analytics.handlers import traffic_state_manager
from src.commons.schemas import TrafficAnalysis

RT = TypeVar("RT", bound=TrafficAnalysis)


def monitor_traffic_congestion(func: Callable[..., Coroutine[Any, Any, RT]]) -> Callable[..., Coroutine[Any, Any, RT]]:
    """
    Decorator that monitors traffic congestion and calls the decorated function
    with the current state (True for HIGH congestion, False for LOW).
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> RT:
        try:
            result: RT = await func(*args, **kwargs)

            traffic_state_manager.response_data = result
            traffic_state_manager.update_state(result.state)

            return result

        except Exception as e:
            logger.error(f"Error in traffic monitoring: {e!s}")
            raise

    return wrapper
