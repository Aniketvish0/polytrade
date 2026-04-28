import json
from dataclasses import asdict

from fastapi import WebSocket

from app.ws.events import WSEvent


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws is not websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: str, event: WSEvent):
        payload = json.dumps(event.to_dict(), default=str)
        if user_id in self._connections:
            dead = []
            for ws in self._connections[user_id]:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws, user_id)

    async def broadcast(self, event: WSEvent):
        payload = json.dumps(event.to_dict(), default=str)
        for user_id, connections in list(self._connections.items()):
            dead = []
            for ws in connections:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws, user_id)


ws_manager = ConnectionManager()
