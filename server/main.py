import asyncio
from typing import Dict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from connection.manager import Manager
from game.dispatcher import Command, Dispatcher, Result, ResultType
from game.models import Player
from game.schemas import ErrorData

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = Manager()
dispatcher = Dispatcher(manager)
sessions: Dict[WebSocket, str] = {}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        game = dispatcher.state.game
        await websocket.send_text(
            Result(type=ResultType.CONNECT_SUCCESS, data=game).model_dump_json()
        )
        while True:
            raw = await websocket.receive_json()
            player_id = sessions.get(websocket)
            if player_id is not None and not dispatcher.state.is_seated(player_id):
                sessions.pop(websocket, None)
                player_id = None
            try:
                command = Command(**raw)
                result = await dispatcher.dispatch_command(player_id, command)
            except ValidationError:
                result = Result(
                    type=ResultType.ERROR, data=ErrorData(message="that command made no sense")
                )
            if result is None:
                continue
            await websocket.send_text(result.model_dump_json())
            if isinstance(result.data, Player):
                sessions[websocket] = result.data.id
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        player_id = sessions.pop(websocket, None)
        if player_id is not None:
            asyncio.create_task(dispatcher.player_left(player_id))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
