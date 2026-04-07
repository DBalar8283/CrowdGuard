from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.database import init_db
from app.db.schemas import StreamPayload
from app.services.event_service import persist_payload
from app.services.perception_stream import RealPerceptionStream
from app.services.simulation import StreamSimulator


class RuntimeState:
    def __init__(self) -> None:
        self.simulator = StreamSimulator()
        self.perception = RealPerceptionStream()
        self.latest_payload: StreamPayload | None = None
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        init_db()
        self._running = True
        if settings.source_mode.lower() != "simulation":
            self.perception.start()
        self._task = asyncio.create_task(self._loop(), name="crowdguard-stream-loop")

    async def stop(self) -> None:
        self._running = False
        self.perception.stop()
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _loop(self) -> None:
        hz = max(settings.stream_hz, 1)
        dt = 1.0 / hz
        mode = settings.source_mode.lower().strip()

        while self._running:
            if mode == "simulation":
                payload = self.simulator.next_payload(dt)
            else:
                payload = self.perception.next_payload(dt)

            if payload is not None:
                self.latest_payload = payload
                persist_payload(payload)

            await asyncio.sleep(dt)


runtime = RuntimeState()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            payload = runtime.latest_payload
            if payload:
                await ws.send_json(payload.model_dump(mode="json"))
            await asyncio.sleep(1.0 / max(settings.stream_hz, 1))
    except WebSocketDisconnect:
        return
