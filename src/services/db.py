from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import Enum
from types import TracebackType
from typing import Any, Generic, TypeVar
from typing import cast as type_cast
from uuid import UUID

from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import (
    ColumnExpressionArgument,
    Delete,
    Executable,
    Insert,
    Select,
    String,
    Update,
    cast,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from project_utils import handle_error
from src.config import settings
from src.model_base import Base, PrimaryKeyUUID

ModelType = TypeVar("ModelType", bound=Base)


class NotCreatedSessionError(NotImplementedError): ...


class DatabaseConfig:
    def __init__(
        self,
        db_url_postgresql: str,
    ):
        self.db_url_postgresql = db_url_postgresql

    @property
    def engine(self):
        return create_async_engine(self.db_url_postgresql, echo=settings.ECHO, poolclass=NullPool)

    @property
    def async_session_maker(self):
        return async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


class IUnitOfWorkBase(ABC):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):  # noqa: ANN001
        await self.rollback()

    @abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abstractmethod
    async def close(self):
        raise NotImplementedError

    @abstractmethod
    async def rollback(self):
        raise NotImplementedError


class PgUnitOfWork(IUnitOfWorkBase):
    def __init__(self) -> None:
        self._session_factory = DatabaseConfig(settings.db_url_postgresql).async_session_maker
        self._async_session: AsyncSession

    def activate(self):
        if not isinstance(self._async_session, AsyncSession):
            self._async_session = self._session_factory()

    async def __aenter__(self):
        self.activate()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if exc_type is not None:
            await self.rollback()

        await self.close()
        if isinstance(exc_val, HTTPException):
            raise exc_val
        else:
            handle_error(exc_type, exc_val, exc_tb)

    async def rollback(self):
        if self._async_session is None:
            raise NotCreatedSessionError

        await self._async_session.rollback()

    async def close(self):
        if self._async_session is None:
            raise NotCreatedSessionError
        await self._async_session.close()

    async def commit(self):
        if self._async_session is None:
            raise NotCreatedSessionError
        await self._async_session.commit()

    async def flush(self):
        if self._async_session is None:
            raise NotCreatedSessionError
        await self._async_session.flush()

    async def refresh(self, instance: type[ModelType]):
        if self._async_session is None:
            raise NotCreatedSessionError
        await self._async_session.refresh(instance)

    async def execute(self, statement: Executable, *args: Any):
        if self._async_session is None:
            raise NotCreatedSessionError
        return await self._async_session.execute(statement, *args)

    def add(self, instance: object):
        if self._async_session is None:
            raise NotCreatedSessionError
        self._async_session.add(instance)


class Query(Generic[ModelType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model
        self.conditions = []

    def insert(self, body: dict | BaseModel) -> Insert:
        if isinstance(body, BaseModel):
            body = body.model_dump()
        return insert(self.model).values(**body).returning(self.model)

    def update(self, *condition: ColumnExpressionArgument, body: dict | BaseModel) -> Update:
        if isinstance(body, BaseModel):
            body = body.model_dump()
        return update(self.model).values(**body).where(*condition).returning(self.model)

    def delete(self, *condition: ColumnExpressionArgument) -> Delete:
        return delete(self.model).where(*condition)

    def select(self, *condition: ColumnExpressionArgument) -> Select:
        return select(self.model).where(*condition)

    def make_conditions(self, conditions: BaseModel):
        """
        Make conditions for the query by pydantic model fields.
        If the field is not None and the model has the field, add the condition to the query.
        """
        logger.info(f"Making conditions {self.model!r} {conditions=}")
        for key, value in conditions.model_dump().items():
            if value is not None and hasattr(self.model, key):
                column = getattr(self.model, key, None)
                if column is None:
                    continue
                if isinstance(value, Enum):
                    self.conditions.append(cast(column, String) == value.value)
                else:
                    self.conditions.append(column == value)


class Crud(Generic[ModelType], Query[ModelType]):
    def __init__(self, model: type[ModelType]):
        super().__init__(model=model)
        self.uow = PgUnitOfWork()

    async def create_entity(self, payload: dict | BaseModel) -> ModelType:
        """
        Create an entity.
        """
        if isinstance(payload, BaseModel):
            body = payload.model_dump()
        else:
            body = payload
        body["created_at"] = datetime.now(UTC)

        stmt = self.model(**body)

        self.uow.add(stmt)
        await self.uow.flush()

        return stmt

    async def update_entity(self, payload: dict | BaseModel, conditions: BaseModel) -> ModelType:
        """
        Update an entity.
        """
        if isinstance(payload, BaseModel):
            body = payload.model_dump()
        else:
            body = payload
        body["updated_at"] = datetime.now(UTC)
        self.make_conditions(conditions)

        query = self.update(*self.conditions, body=body)
        result_query = await self.uow.execute(query)
        await self.uow.flush()
        response = result_query.scalar_one()
        return type_cast("ModelType", response)

    async def delete_entity(self, conditions: BaseModel) -> None:
        """
        Delete an entity.
        """
        self.make_conditions(conditions)
        query = self.delete(*self.conditions)
        await self.uow.execute(query)
        await self.uow.flush()


class CrudEntity(Crud[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.uow = PgUnitOfWork()
        super().__init__(model=model)

    async def get_entity(self, r_id: UUID) -> ModelType:
        model = type_cast("type[PrimaryKeyUUID]", self.model)
        conditions = model.id == r_id
        query = self.select(conditions)

        result_query = await self.uow.execute(query)
        response = result_query.scalar_one()
        return type_cast("ModelType", response)

    async def get_entity_by_conditions(self, conditions: BaseModel) -> ModelType:
        """Get one row by conditions
        :param conditions:
        :return: self.model
        """
        self.make_conditions(conditions)
        query = self.select(*self.conditions)

        result_query = await self.uow.execute(query)
        response = result_query.scalar_one()
        return type_cast("ModelType", response)

    async def one_or_none(self, conditions: BaseModel) -> ModelType | None:
        """Get one row by conditions if exists else return None
        :param conditions:
        :return: self.model
        """
        self.make_conditions(conditions)
        query = self.select(*self.conditions)

        result_query = await self.uow.execute(query)
        response = result_query.scalar_one_or_none()
        return type_cast("ModelType | None", response)

    async def get_many(self, conditions: BaseModel) -> list[ModelType]:
        """Get all rows by conditions
        :param conditions:
        :return: list[self.model]
        """
        self.make_conditions(conditions)
        query = self.select(*self.conditions)

        result_query = await self.uow.execute(query)
        response = result_query.scalars().fetchall()
        return type_cast("list[ModelType]", response)

    async def get_all(self) -> list[ModelType]:
        query = self.select()
        result_query = await self.uow.execute(query)
        response = result_query.scalars().fetchall()
        return type_cast("list[ModelType]", response)

    async def get_by_query(self, query: Executable) -> list[ModelType]:
        result_query = await self.uow.execute(query)
        response = result_query.scalars().fetchall()
        return type_cast("list[ModelType]", response)
