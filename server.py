import asyncio
import os
import uuid
import concurrent.futures

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="HiveMind Pipeline Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/pipeline")
async def pipeline_ws(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())[:8]
    await websocket.send_json({"type": "connected", "session_id": session_id})

    try:
        data = await websocket.receive_json()
        task = data.get("task", "").strip()

        if not task:
            await websocket.send_json({"type": "error", "message": "No task provided"})
            await websocket.close()
            return

        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def emitter(event: dict):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        from clawforge.pipeline import run_pipeline

        def run_in_thread():
            try:
                result = run_pipeline(task, emitter=emitter)
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {"type": "done", "result": result}
                )
            except Exception as exc:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {"type": "error", "message": str(exc)}
                )

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = loop.run_in_executor(executor, run_in_thread)

        while True:
            event = await queue.get()
            await websocket.send_json(event)
            if event.get("type") in ("done", "error"):
                break

        await future

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


# Serve production build if it exists
dist_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
