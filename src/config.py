from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PG_HOST: str = "172.18.0.5"
    PG_PORT: str = "5432"
    PG_NAME: str = "dip_analytics"
    PG_USER: str = "postgres"
    PG_PASS: str = "avdeev97"

    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_CONSUME_TOPICS: list[str] = ["RoadCondition"]
    SEND_TOPICS: list[str] = ["RoadCondition"]
    GROUP_ID: str = "as"

    REDIS_HOST: str = "redis"
    REDIS_PORT: str = "6379"

    ECHO: bool = False
    DEBUG: bool = True

    @property
    def db_url_postgresql(self) -> str:
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASS}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_NAME}"

    @property
    def db_url_redis(self) -> str:
        return f"redis://@{self.REDIS_HOST}:{self.REDIS_PORT}/"


settings = Settings()  # pyright: ignore[reportCallIssue]
