import asyncio
import json
import logging
from typing import Dict, Optional
from fastapi import WebSocket
import redis.asyncio as aioredis
import redis as syncredis
from ..config import get_settings

logger = logging.getLogger(__name__)

CHANNEL = "ws:broadcast"


class WebSocketManager:
    def __init__(self):
        self.connections: Dict[int, WebSocket] = {}
        self._redis_sub: Optional[aioredis.Redis] = None
        self._listener_task: Optional[asyncio.Task] = None

    async def startup(self):
        """Call from FastAPI lifespan/startup."""
        settings = get_settings()
        self._redis_sub = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        self._listener_task = asyncio.create_task(self._listen())

    async def shutdown(self):
        if self._listener_task:
            self._listener_task.cancel()
        if self._redis_sub:
            await self._redis_sub.aclose()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket
        logger.info(f"WS connected: user {user_id}")

    def disconnect(self, user_id: int):
        self.connections.pop(user_id, None)
        logger.info(f"WS disconnected: user {user_id}")

    async def send_to_user(self, user_id: int, data: dict):
        ws = self.connections.get(user_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"WS send failed for user {user_id}: {e}")
                self.disconnect(user_id)

    async def _listen(self):
        """Background task: subscribe to Redis and forward messages."""
        try:
            pubsub = self._redis_sub.pubsub()
            await pubsub.subscribe(CHANNEL)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        payload = json.loads(message["data"])
                        user_id = payload.get("user_id")
                        if user_id:
                            await self.send_to_user(user_id, payload)
                    except Exception as e:
                        logger.error(f"WS listener error: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WS Redis listener crashed: {e}")

    @staticmethod
    def publish_sync(user_id: int, event: str, data: dict):
        """Called from Celery workers (sync context) to push WS events."""
        try:
            settings = get_settings()
            r = syncredis.from_url(settings.REDIS_URL)
            payload = json.dumps({"user_id": user_id, "event": event, "data": data})
            r.publish(CHANNEL, payload)
            r.close()
        except Exception as e:
            logger.error(f"WS publish_sync error: {e}")


manager = WebSocketManager()
