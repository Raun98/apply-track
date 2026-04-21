import asyncio
import json
import logging
from typing import Dict, List, Optional
from fastapi import WebSocket
import redis.asyncio as aioredis
import redis as syncredis
from ..config import get_settings

logger = logging.getLogger(__name__)

CHANNEL = "ws:broadcast"

# Module-level sync Redis pool shared across all Celery task invocations in a worker process.
_sync_redis_pool: Optional[syncredis.Redis] = None


def _get_sync_redis() -> syncredis.Redis:
    global _sync_redis_pool
    if _sync_redis_pool is None:
        settings = get_settings()
        _sync_redis_pool = syncredis.from_url(settings.REDIS_URL)
    return _sync_redis_pool


class WebSocketManager:
    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}
        self._redis_sub: Optional[aioredis.Redis] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._sync_redis_pool: Optional[syncredis.Redis] = None

    async def startup(self):
        settings = get_settings()
        self._redis_sub = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        self._listener_task = asyncio.create_task(self._listen())
        self._sync_redis_pool = syncredis.from_url(settings.REDIS_URL)

    async def shutdown(self):
        if self._listener_task:
            self._listener_task.cancel()
        if self._redis_sub:
            await self._redis_sub.aclose()
        if self._sync_redis_pool:
            self._sync_redis_pool.close()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(websocket)
        logger.info(f"WS connected: user {user_id} ({len(self.connections[user_id])} connections)")

    def disconnect(self, user_id: int, websocket: Optional[WebSocket] = None):
        if user_id not in self.connections:
            return
        if websocket is None:
            self.connections.pop(user_id, None)
        else:
            self.connections[user_id] = [
                ws for ws in self.connections[user_id] if ws != websocket
            ]
            if not self.connections[user_id]:
                del self.connections[user_id]
        logger.info(f"WS disconnected: user {user_id}")

    async def send_to_user(self, user_id: int, data: dict):
        sockets = self.connections.get(user_id, [])
        dead = []
        for ws in sockets:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"WS send failed for user {user_id}: {e}")
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def _listen(self):
        while True:
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
                break
            except Exception as e:
                logger.error(f"WS Redis listener crashed, restarting in 5s: {e}")
                await asyncio.sleep(5)

    @staticmethod
    def publish_sync(user_id: int, event: str, data: dict):
        """Publish an event to the Redis pub/sub channel (called from Celery workers).

        Uses a module-level connection pool so we don't open a new TCP connection
        on every Celery task invocation.
        """
        try:
            r = _get_sync_redis()
            payload = json.dumps({"user_id": user_id, "event": event, "data": data})
            r.publish(CHANNEL, payload)
        except Exception as e:
            logger.error(f"WS publish_sync error: {e}")


manager = WebSocketManager()
