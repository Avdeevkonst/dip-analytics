from loguru import logger
from pydantic_settings import BaseSettings

from src.commons.enums import Topics

logger.add("logs/{time:YYYY-MM-DD}.log", format="{time} {level} {message}", rotation="1 week")


class Settings(BaseSettings):
    """Application settings.

    This class manages all configuration settings for the application,
    including database connections, Kafka settings, and application behavior flags.
    All sensitive data should be provided via environment variables.
    """

    PG_HOST: str = "172.18.0.2"
    PG_PORT: str = "5432"
    PG_NAME: str = "dip_analytics"
    PG_USER: str = "postgres"
    PG_PASS: str = "avdeev97"  # noqa: S105

    KAFKA_BOOTSTRAP_SERVERS: str = "172.18.0.4:9092"
    KAFKA_CONSUME_TOPICS: list[str] = [Topics.ROAD_CONDITION.value, Topics.CAR.value]
    SEND_TOPICS: list[str] = [Topics.ROAD_CONDITION.value, Topics.CAR.value]
    GROUP_ID: str = "as"

    REDIS_HOST: str = "redis"
    REDIS_PORT: str = "6379"

    ADMIN_SECRET_KEY: str = "admin"  # noqa: S105

    ECHO: bool = False
    DEBUG: bool = True

    @property
    def db_url_postgresql(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASS}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_NAME}"

    @property
    def db_url_redis(self) -> str:
        """Generate Redis connection URL."""
        return f"redis://@{self.REDIS_HOST}:{self.REDIS_PORT}/"


settings = Settings()  # pyright: ignore[reportCallIssue]
