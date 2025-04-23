import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.analitycs.services import TrafficAnalysisService, traffic_state_manager

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.websocket("/ws/congestion")
async def websocket_traffic_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for real-time traffic congestion monitoring.
    Sends state updates (true/false) based on congestion level with 10-minute cooldown.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    service = TrafficAnalysisService()
    sleep_time = 60
    try:
        while True:
            # Get current congestion data
            # TODO: change direcly using to taskiq
            congestion_data = await service.analyze_traffic_congestion()

            # Determine new state based on congestion level
            new_state = congestion_data["congestion_level"] == "HIGH"

            # Try to update state (will only update if cooldown period has passed)
            state_changed = traffic_state_manager.update_state(new_state)

            # Get current state (either newly updated or existing)
            current_state = traffic_state_manager.get_state()

            # Calculate time until next possible state change
            time_since_change = traffic_state_manager.get_time_since_last_change()
            minutes_until_next_change = traffic_state_manager.cooldown_minutes - (
                time_since_change.total_seconds() / 60 if time_since_change else 0
            )

            # Send state update
            await websocket.send_json(
                {
                    "state": current_state,
                    "congestion_level": congestion_data["congestion_level"],
                    "average_speed": congestion_data["average_speed"],
                    "timestamp": congestion_data["timestamp"],
                    "state_changed": state_changed,
                    "minutes_until_next_change": max(0, minutes_until_next_change),
                },
                mode="text",
            )

            # Wait before next update
            await asyncio.sleep(sleep_time)  # Update every minute

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")

    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in WebSocket connection: {e!s}")
        with contextlib.suppress(Exception):
            await websocket.close()
