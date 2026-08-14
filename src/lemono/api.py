from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .agent import LemonoAgent
from .config import Settings
from .diagnostics import Diagnostics
from .memory import MemoryStore
from .models import ChatRequest, ChatResponse, DiagnosticReport, MemoryRecord
from .providers import ProviderError, build_providers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    memory = MemoryStore(settings.database_path)
    providers = build_providers(settings.request_timeout_seconds)
    agent = LemonoAgent(settings, memory, providers)
    diagnostics = Diagnostics(settings, memory, providers)
    app = FastAPI(title="Lemono Agent", version=__version__)
    app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type"])

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"name": "Lemono Agent", "version": __version__, "docs": "/docs"}

    @app.post("/v1/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        try:
            return await agent.chat(request)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/v1/diagnostics", response_model=DiagnosticReport)
    async def diagnose() -> DiagnosticReport:
        return diagnostics.run()

    @app.get("/v1/memories/{user_id}", response_model=list[MemoryRecord])
    async def memories(user_id: str, query: str = "", limit: int = 20) -> list[MemoryRecord]:
        return memory.search(user_id, query, min(max(limit, 1), 100)) if query else memory.recent(user_id, min(max(limit, 1), 100))

    @app.delete("/v1/memories/{user_id}")
    async def forget(user_id: str) -> dict[str, int]:
        return {"deleted": memory.delete_user(user_id)}

    return app


app = create_app()

