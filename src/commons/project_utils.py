from types import TracebackType
from typing import NoReturn

from fastapi import HTTPException, status
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

import src.commons.models as models

HIGH = 5
MEDIUM = 20
LOW = 40
RADIUS = 6371
SECONDS_IN_HOUR = 3600


def handle_error(
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: TracebackType | None,
):
    if exc_type is not None and exc_val is not None:
        status_code = status.HTTP_404_NOT_FOUND if exc_type is NoResultFound else status.HTTP_400_BAD_REQUEST
        handle_error_message(str(exc_val), status_code)


def handle_error_message(
    error: SQLAlchemyError | str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> NoReturn:  # pragma: no cover
    msg = convert_sqlachemy_exception(error)
    raise HTTPException(
        status_code=status_code,
        detail=msg,
    )


def convert_sqlachemy_exception(error: SQLAlchemyError | str) -> str:
    """Convert SQLAlchemy exception to string."""
    if isinstance(error, str):
        return error
    return str(error)


def calculate_average_speed(recent_cars: list[models.Car]) -> float:
    """
    Calculate the average speed of the cars.
    """
    total_speed = sum(car.average_speed for car in recent_cars)
    return total_speed / len(recent_cars)


def calculate_congestion_level(average_speed: float) -> str:
    """
    Calculate the congestion level based on the average speed.
    """
    if average_speed < HIGH:
        return "HIGH"
    elif average_speed < MEDIUM:
        return "MEDIUM"
    else:
        return "LOW"
