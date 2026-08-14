from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data_dir: Path = Field(default=Path("~/.lemono").expanduser())
    default_provider: str = "openai"
    default_model: str = "gpt-5"
    fallback_providers: str = ""
    max_context_memories: int = Field(default=6, ge=0, le=20)
    request_timeout_seconds: float = Field(default=60, ge=1, le=300)
    max_input_chars: int = Field(default=32_000, ge=100, le=200_000)
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    def __init__(self, **data: Any):
        fields = type(self).model_fields
        for name, field in fields.items():
            env_name = f"LEMONO_{name.upper()}"
            if name in data or env_name not in os.environ:
                continue
            value: Any = os.environ[env_name]
            annotation = field.annotation
            if annotation is int:
                value = int(value)
            elif annotation is float:
                value = float(value)
            data[name] = value
        super().__init__(**data)
        self.data_dir = self.data_dir.expanduser()

    @property
    def database_path(self) -> Path:
        return self.data_dir / "lemono.db"

    @property
    def fallback_list(self) -> list[str]:
        return [item.strip() for item in self.fallback_providers.split(",") if item.strip()]

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]
