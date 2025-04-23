import typing
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import Enum
from types import TracebackType
from typing import Any, Generic, TypeVar
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

from src.config import settings
from src.model_base import Base
from src.utils import handle_error

M = TypeVar("M", bound=Base)


class NotCreatedSessionError(NotImplementedError): ...


class Singleton:  # pragma: no cover
    def __new__(cls, *args: typing.Any, **kwds: typing.Any):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args: typing.Any, **kwds: typing.Any):
        pass


class DatabaseConfig(Singleton):
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

    async def refresh(self, instance: type[M]):
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


class Query:
    def __init__(self, model: type[M]) -> None:
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

    def make_conditions(self, params: BaseModel):
        logger.info(f"Making conditions {self.model!r} {params=}")
        for k, v in params:
            if v is not None and hasattr(self.model, k):
                column = getattr(self.model, k, None)
                if column is None:
                    continue
                if isinstance(v, Enum):
                    self.conditions.append(cast(column, String) == v.value)
                else:
                    self.conditions.append(column == v)


class CrudEntity(Generic[M], Query):
    def __init__(self, model: type[M]):
        self.uow = PgUnitOfWork()
        super().__init__(model=model)

    async def create_entity(self, payload: dict | BaseModel) -> M:
        if isinstance(payload, BaseModel):
            body = payload.model_dump()
        else:
            body = payload
        body["created_at"] = datetime.now(UTC)

        stmt = self.model(**body)

        self.uow.add(stmt)
        await self.uow.flush()

        return stmt  # pyright: ignore[reportReturnType]

    async def update_entity(self, payload: dict | BaseModel, conditions: BaseModel) -> M:
        if isinstance(payload, BaseModel):
            body = payload.model_dump()
        else:
            body = payload
        body["updated_at"] = datetime.now(UTC)
        self.make_conditions(conditions)

        query = self.update(*self.conditions, body=body)
        result = await self.uow.execute(query)
        await self.uow.flush()
        return result.scalar_one()

    async def delete_entity(self, conditions: BaseModel) -> None:
        self.make_conditions(conditions)
        query = self.delete(*self.conditions)
        await self.uow.execute(query)
        await self.uow.flush()

    async def get_entity(self, r_id: UUID) -> M:
        conditions = self.model.id == r_id  # pyright: ignore[reportAttributeAccessIssue]
        query = self.select(conditions)

        result = await self.uow.execute(query)

        return result.scalar_one()

    async def get_entity_by_conditions(self, conditions: BaseModel) -> M:
        """Get one row by conditions
        :param conditions:
        :return: self.model
        """

        self.make_conditions(conditions)
        query = self.select(*self.conditions)

        result = await self.uow.execute(query)

        return result.scalar_one()

    async def one_or_none(self, conditions: BaseModel) -> M | None:
        """Get one row by conditions if exists else return None
        :param conditions:
        :return: self.model
        """
        self.make_conditions(conditions)
        query = self.select(*self.conditions)

        result = await self.uow.execute(query)

        return result.scalar_one_or_none()

    async def get_many(self, conditions: BaseModel) -> list[M]:
        """Get all rows by conditions
        :param conditions:
        :return: list[self.model]
        """
        self.make_conditions(conditions)
        query = self.select(*self.conditions)

        result = await self.uow.execute(query)
        return result.scalars().fetchall()  # pyright:ignore[reportReturnType]

    async def get_all(self) -> list[M]:
        query = self.select()
        result = await self.uow.execute(query)
        return result.scalars().fetchall()  # pyright:ignore[reportReturnType]

    async def get_by_query(self, query: Executable) -> list[M]:
        result = await self.uow.execute(query)
        return result.scalars().fetchall()  # pyright:ignore[reportReturnType]
