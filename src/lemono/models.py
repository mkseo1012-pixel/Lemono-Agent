from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str = Field(default="local", min_length=1, max_length=128, pattern=r"^[\w.-]+$")
    session_id: str = Field(default="default", min_length=1, max_length=128, pattern=r"^[\w.-]+$")
    provider: str | None = None
    model: str | None = None


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    memories_used: int
    learned_preferences: list[str] = []


class MemoryRecord(BaseModel):
    id: int
    user_id: str
    kind: Literal["conversation", "fact", "preference", "summary"]
    content: str
    source: str
    confidence: float
    created_at: datetime


class DiagnosticCheck(BaseModel):
    name: str
    status: Literal["ok", "warning", "error"]
    detail: str
    remediation: str | None = None


class DiagnosticReport(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    checks: list[DiagnosticCheck]

