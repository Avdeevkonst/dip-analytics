from enum import Enum


class Weather(str, Enum):
    """Weather status enum."""

    DRY = "DRY"
    WET = "WET"
    SNOWY = "SNOWY"
    CLOUDY = "CLOUDY"
    ICY = "ICY"
    MUDDY = "MUDDY"


class Jam(str, Enum):
    """Traffic jam status enum."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Sort(str, Enum):
    """Sort direction enum."""

    ASC = "asc"
    DESC = "desc"


class Topics(str, Enum):
    """Kafka topics enum."""

    CAR = "car"
    ROAD = "road"
    ROAD_CONDITION = "road_condition"
