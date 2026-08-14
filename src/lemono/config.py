from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def read_dotenv(path: Path) -> dict[str, str]:
    """Read a minimal KEY=VALUE file. Invalid names and comments are ignored."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.replace("_", "").isalnum():
            values[key] = value.strip().strip("'\"")
    return values


def _load_dotenv(path: Path) -> None:
    """Load a minimal KEY=VALUE file without overriding the process environment."""
    for key, value in read_dotenv(path).items():
        os.environ.setdefault(key, value)


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
        _load_dotenv(Path(".env"))
        configured_dir = Path(
            data.get("data_dir", os.environ.get("LEMONO_DATA_DIR", "~/.lemono"))
        ).expanduser()
        _load_dotenv(configured_dir / ".env")
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
