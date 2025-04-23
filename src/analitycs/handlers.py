from datetime import UTC, datetime, timedelta

from loguru import logger


class TrafficStateManager:
    def __init__(self):
        self.last_state_change: datetime | None = None
        self.current_state: bool = False
        self.cooldown_minutes: int = 10
        self._response_data: dict = {}

    def can_change_state(self) -> bool:
        """
        Check if enough time has passed since the last state change.
        Returns True if cooldown period has passed or if no state change has occurred yet.
        """
        if self.last_state_change is None:
            return True

        time_since_last_change = datetime.now(UTC) - self.last_state_change
        return time_since_last_change >= timedelta(minutes=self.cooldown_minutes)

    def update_state(self, new_state: bool) -> bool:
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

    def get_state(self) -> bool:
        """Get the current traffic state."""
        return self.current_state

    def get_time_since_last_change(self) -> timedelta | None:
        """Get the time elapsed since the last state change."""
        if self.last_state_change is None:
            return None
        return datetime.now(UTC) - self.last_state_change

    @property
    def response_data(self) -> dict:
        return self._response_data

    @response_data.setter
    def response_data(self, value: dict) -> None:
        self._response_data = value


# Create a singleton instance
traffic_state_manager = TrafficStateManager()
