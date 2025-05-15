from datetime import datetime

from fastapi import FastAPI
from loguru import logger
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.commons.models import Car, Road, RoadCondition
from src.config import settings
from src.services.db import DatabaseConfig


class AdminAuth(AuthenticationBackend):
    """Authentication backend for admin panel."""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # In production, use proper authentication
        # TODO: change logic to validate username and password with user from user service
        valid = username == "admin" and password == "admin"  # noqa: S105
        if valid:
            request.session.update({"token": "..."})
        return valid

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("token", False))


class CarAdmin(ModelView, model=Car):
    """Admin interface for Car model."""

    name = "Car"
    name_plural = "Cars"
    icon = "fa-solid fa-car"

    column_list = [Car.id, Car.plate_number, Car.model, Car.average_speed, Car.created_at]
    column_searchable_list = [Car.plate_number, Car.model]
    column_sortable_list = [Car.average_speed, Car.created_at]
    column_default_sort = ("created_at", True)

    can_create = False  # Cars are created only through sensors
    can_edit = True
    can_delete = True
    can_view_details = True

    def on_model_change(self, data: dict, model: Car, is_created: bool) -> None:
        """Log changes to car records."""
        model.updated_at = datetime.now()
        action = "Created" if is_created else "Updated"
        logger.info(f"{action} car: {model.plate_number}")


class RoadAdmin(ModelView, model=Road):
    """Admin interface for Road model."""

    name = "Road"
    name_plural = "Roads"
    icon = "fa-solid fa-road"

    column_list = [Road.id, Road.name, Road.start, Road.end, Road.length, Road.city]
    column_searchable_list = [Road.name, Road.city]
    column_sortable_list = [Road.name, Road.city, Road.length]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    async def on_model_change(self, data: dict, model: Road, is_created: bool, request: Request) -> None:
        """Log changes to road records."""
        model.updated_at = datetime.now()
        action = "Created" if is_created else "Updated"
        logger.info(f"{action} road: {model.name}")
        await super().on_model_change(data, model, is_created, request)


class RoadConditionAdmin(ModelView, model=RoadCondition):
    """Admin interface for RoadCondition model."""

    name = "Road Condition"
    name_plural = "Road Conditions"
    icon = "fa-solid fa-traffic-light"

    column_list = [
        RoadCondition.id,
        RoadCondition.name,
        RoadCondition.road_id,
        RoadCondition.weather_status,
        RoadCondition.jam_status,
        RoadCondition.created_at,
    ]
    column_searchable_list = [RoadCondition.name]
    column_sortable_list = [RoadCondition.created_at]
    column_default_sort = ("created_at", True)

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    async def on_model_change(self, data: dict, model: RoadCondition, is_created: bool, request: Request) -> None:
        """Log changes to road condition records."""
        model.updated_at = datetime.now()
        action = "Created" if is_created else "Updated"
        logger.info(f"{action} road condition: {model.name}")
        await super().on_model_change(data, model, is_created, request)


def setup_admin(app: FastAPI) -> None:
    """Setup admin interface for the application."""
    engine = DatabaseConfig(settings.db_url_postgresql).engine

    authentication_backend = AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="Traffic Analytics Admin",
        base_url="/admin",
    )

    # Register admin views
    admin.add_view(CarAdmin)
    admin.add_view(RoadAdmin)
    admin.add_view(RoadConditionAdmin)
