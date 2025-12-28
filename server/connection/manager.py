from fastapi import WebSocket
from typing import List

from pydantic import BaseModel


class Manager:
    def __init__(self):
        self._active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self._active_connections.remove(websocket)

    async def broadcast(self, data: BaseModel):
        for connection in self._active_connections:
            await connection.send_text(data.model_dump_json())
