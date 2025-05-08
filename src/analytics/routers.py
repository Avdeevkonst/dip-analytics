import asyncio
import contextlib
from datetime import timedelta
from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger

from src.analytics.handlers import traffic_state_manager
from src.analytics.services import TrafficAnalysisService
from src.commons.schemas import TrafficAnalysis, TrafficState

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("/{road_id}/analysis", response_model=TrafficAnalysis)
async def get_traffic_analysis(road_id: UUID) -> TrafficAnalysis:
    """
    Get current traffic analysis for a road segment.

    Args:
        road_id: Road segment ID

    Returns:
        Current traffic analysis
    """
    try:
        return await TrafficAnalysisService().analyze_traffic(road_id)
    except ValueError as e:
        logger.error(f"Error analyzing traffic for road {road_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error analyzing traffic for road {road_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.websocket("/ws/congestion")
async def websocket_traffic_monitor(websocket: WebSocket) -> NoReturn:
    """
    WebSocket endpoint for real-time traffic congestion monitoring.

    Sends state updates based on congestion level with 10-minute cooldown.
    Continuously monitors traffic state and sends updates to connected clients.

    Args:
        websocket: The WebSocket connection instance.

    Raises:
        WebSocketDisconnect: When client disconnects.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            state = traffic_state_manager.get_state
            time_since_change = traffic_state_manager.get_time_since_last_change()

            cooldown_remaining: float = (
                traffic_state_manager.cooldown_minutes - (time_since_change.total_seconds() / 60)
                if time_since_change
                else 0
            )

            sleep_time: float = max(0, 60 * 10 - cooldown_remaining)
            cooldown_until = (
                traffic_state_manager.last_state_change + timedelta(minutes=traffic_state_manager.cooldown_minutes)
                if traffic_state_manager.last_state_change
                else None
            )

            if state != "UNSTAGED":
                response = TrafficState(
                    state=state.value,
                    congestion_level=traffic_state_manager.response_data.congestion_level
                    if traffic_state_manager.response_data
                    else 0,
                    last_change=traffic_state_manager.last_state_change,
                    cooldown_until=cooldown_until,
                )
                await websocket.send_json(response.model_dump_json(), mode="text")

            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
        with contextlib.suppress(Exception):
            await websocket.close()

    except (ConnectionError, TimeoutError) as exc:
        logger.error(f"Connection error in WebSocket: {exc!s}")
        with contextlib.suppress(Exception):
            await websocket.close()

    except Exception as exc:
        logger.critical(f"Unexpected error in WebSocket connection: {exc!s}")
        with contextlib.suppress(Exception):
            await websocket.close()
        raise
