from __future__ import annotations

import shutil

from .config import Settings
from .memory import MemoryStore
from .models import DiagnosticCheck, DiagnosticReport
from .providers import ModelProvider


class Diagnostics:
    def __init__(self, settings: Settings, memory: MemoryStore, providers: dict[str, ModelProvider]):
        self.settings, self.memory, self.providers = settings, memory, providers

    def run(self) -> DiagnosticReport:
        checks: list[DiagnosticCheck] = []
        try:
            db_ok = self.memory.ping()
        except Exception as exc:
            checks.append(DiagnosticCheck(name="memory", status="error", detail=type(exc).__name__, remediation="Check LEMONO_DATA_DIR permissions."))
        else:
            checks.append(DiagnosticCheck(name="memory", status="ok" if db_ok else "error", detail=str(self.settings.database_path)))

        configured = [name for name, provider in self.providers.items() if provider.configured]
        checks.append(DiagnosticCheck(
            name="providers",
            status="ok" if configured else "warning",
            detail=f"configured: {', '.join(configured) if configured else 'none'}",
            remediation=None if configured else "Set one of OPENAI_API_KEY, XAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY.",
        ))
        free = shutil.disk_usage(self.settings.data_dir).free
        checks.append(DiagnosticCheck(name="disk", status="ok" if free > 100 * 1024 * 1024 else "warning", detail=f"{free // (1024 * 1024)} MiB free"))
        if any(check.status == "error" for check in checks):
            status = "unhealthy"
        elif any(check.status == "warning" for check in checks):
            status = "degraded"
        else:
            status = "healthy"
        return DiagnosticReport(status=status, checks=checks)

