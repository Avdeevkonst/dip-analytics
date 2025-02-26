import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Analytics API", version="0.1.0", lifespan=lifespan)


v1_router = APIRouter(prefix="/api/v1")


app.include_router(v1_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Any):
    logger.info(f"Start processing request {request.url}")
    logger.info(f"Client ip_address:{request.headers.get('x-forwarded-for', None)}")
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Request processed time was {process_time}")
    return response
