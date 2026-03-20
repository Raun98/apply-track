from typing import Dict, List, Optional

from fastapi import WebSocket


class WebSocketManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self):
        # user_id -> list of WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            # Clean up empty lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected sockets
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    async def notify_application_update(
        self,
        user_id: int,
        application_id: int,
        update_type: str,
        data: dict,
    ):
        """Notify a user about an application update."""
        await self.send_personal_message(
            {
                "type": "application_update",
                "update_type": update_type,
                "application_id": application_id,
                "data": data,
            },
            user_id,
        )

    async def notify_new_email(
        self,
        user_id: int,
        email_id: int,
        application_id: Optional[int] = None,
    ):
        """Notify a user about a new processed email."""
        await self.send_personal_message(
            {
                "type": "new_email",
                "email_id": email_id,
                "application_id": application_id,
            },
            user_id,
        )


# Singleton instance
websocket_manager = WebSocketManager()
