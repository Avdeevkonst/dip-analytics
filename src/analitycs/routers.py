import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.analitycs.handlers import traffic_state_manager

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.websocket("/ws/congestion")
async def websocket_traffic_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for real-time traffic congestion monitoring.
    Sends state updates (true/false) based on congestion level with 10-minute cooldown.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    sleep_time = 60
    try:
        while True:
            state = traffic_state_manager.get_state
            time_since_change = traffic_state_manager.get_time_since_last_change()

            sleep_time = (
                traffic_state_manager.cooldown_minutes - (time_since_change.total_seconds() / 60)
                if time_since_change
                else 0
            )

            sleep_time = 60 * 10 - sleep_time
            if state != "UNSTAGED":
                await websocket.send_json(
                    {
                        "state": state,
                        "congestion_level": traffic_state_manager.response_data["congestion_level"],
                    },
                    mode="text",
                )

            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
        with contextlib.suppress(Exception):
            await websocket.close()

    except Exception as exc:  # noqa: BLE001
        logger.error(f"Error in WebSocket connection: {exc!s}")
        with contextlib.suppress(Exception):
            await websocket.close()
