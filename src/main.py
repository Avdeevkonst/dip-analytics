import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from loguru import logger

from src.admin import setup_admin
from src.analytics.kafka_handler import broker
from src.analytics.routers import router as traffic_router
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan for the FastAPI application.
    1. Connects to the Kafka broker.
    2. Closes the Kafka broker when the application is stopped.
    """
    await broker.connect()
    # Setup admin panel
    setup_admin(app)

    yield

    await broker.close()


app = FastAPI(
    title="Traffic Analytics API",
    version="0.1.0",
    lifespan=lifespan,
    description="Real-time traffic analytics with admin interface",
)

# Store settings in app state for admin panel
app.state.settings = settings


# Setup API routes
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(traffic_router)
app.include_router(v1_router)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Any):
    """
    Middleware for logging request information.
    Logs the start time of the request and the time it took to process.
    """
    logger.info(f"Start processing request {request.url}")
    logger.info(f"Client ip_address:{request.headers.get('x-forwarded-for', None)}")
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Request processed time was {process_time}")
    return response
