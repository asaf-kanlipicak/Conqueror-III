from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from connection.manager import Manager
from game.dispatcher import Dispatcher, ResultType, Result, Command
from game.models import Player

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
websocket_player_map: Dict[WebSocket, Player] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        result = Result(type=ResultType.CONNECT_SUCCESS, data=dispatcher.state.game)
        await websocket.send_text(result.model_dump_json())
        while True:
            data = await websocket.receive_json()
            command = Command(**data)
            player = websocket_player_map.get(websocket)
            result = await dispatcher.dispatch_command(player, command)
            if result:
                await websocket.send_text(result.model_dump_json())
                if result.type == ResultType.JOIN_SUCCESS:
                    websocket_player_map[websocket] = result.data
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        websocket_player_map.pop(websocket, None)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)