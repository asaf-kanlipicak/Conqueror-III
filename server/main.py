from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from connection import ConnectionManager
from state import game_state

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({"type": "init", "data": game_state.get_state()}))
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            x = message["x"]
            y = message["y"]
            
            new_val = game_state.toggle(x, y)
            
            await manager.broadcast(json.dumps({
                "type": "update",
                "x": x,
                "y": y,
                "val": new_val
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)