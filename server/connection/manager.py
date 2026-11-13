from typing import List

from fastapi import WebSocket
from pydantic import BaseModel


class Manager:
    def __init__(self):
        self._active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)

    async def broadcast(self, data: BaseModel) -> None:
        message = data.model_dump_json()
        for connection in list(self._active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)
