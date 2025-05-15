from typing import Protocol

from sqlalchemy.orm import Mapped, mapped_column


class HasAverageSpeed(Protocol):
    average_speed: Mapped[float] = mapped_column()
