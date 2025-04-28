import typing
from datetime import UTC, datetime, timedelta
from functools import total_ordering
from typing import Literal

from loguru import logger

S = Literal["LOW", "MEDIUM", "HIGH", "UNSTAGED"]
D = typing.TypeVar("D", bound=dict[str, str | float | int])


@total_ordering
class State:
    def __init__(self, state: S) -> None:
        self.state = state
        self.compare_value = {
            "UNSTAGED": -1,
            "LOW": 0,
            "MEDIUM": 1,
            "HIGH": 2,
        }

    def __eq__(self, value: object) -> bool:
        return self.state == value

    def __gt__(self, value: object) -> bool:
        if not isinstance(value, str):
            return NotImplemented

        return self.compare_value[self.state] > self.compare_value[value]

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, str):
            return NotImplemented

        return self.compare_value[self.state] < self.compare_value[value]


class TrafficStateManager:
    def __init__(self):
        self.last_state_change: datetime | None = None
        self.current_state: S = "LOW"
        self.cooldown_minutes: int = 10
        self._response_data: dict[str, str | float | int] = {}

    def can_change_state(self) -> bool:
        """
        Check if enough time has passed since the last state change.
        Returns True if cooldown period has passed or if no state change has occurred yet.
        """
        if self.last_state_change is None:
            return True

        time_since_last_change = datetime.now(UTC) - self.last_state_change
        return time_since_last_change >= timedelta(minutes=self.cooldown_minutes)

    def update_state(self, new_state: S) -> bool:
        """
        Update the state if cooldown period has passed.
        Returns True if state was updated, False if cooldown period hasn't passed.
        """
        if not self.can_change_state():
            return False

        if self.current_state != new_state:
            self.current_state = new_state
            self.last_state_change = datetime.now(UTC)
            logger.info(f"Traffic state changed to: {new_state}")
            return True

        return False

    @property
    def get_state(self) -> S:
        """Get the current traffic state."""
        return self.current_state

    def get_time_since_last_change(self) -> timedelta | None:
        """Get the time elapsed since the last state change."""
        if self.last_state_change is None:
            return None
        return datetime.now(UTC) - self.last_state_change

    @property
    def response_data(self) -> dict[str, str | float | int]:
        return self._response_data

    @response_data.setter
    def response_data(self, value: dict[str, str | float | int]) -> None:
        self._response_data = value


# Create a singleton instance
traffic_state_manager = TrafficStateManager()
