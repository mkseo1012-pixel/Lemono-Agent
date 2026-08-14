from __future__ import annotations

import re

from .memory import MemoryStore


class PreferenceLearner:
    """Learns only explicit user preferences; never rewrites code or permissions."""

    PATTERNS = (
        re.compile(r"(?:나는|제가|난)\s+(.{2,80}?)(?:을|를)?\s*(?:좋아해|선호해|원해)(?:요)?[.!]?"),
        re.compile(r"(?:답변은|응답은)\s+(.{2,80}?)(?:로|하게)\s*(?:해줘|해주세요|원해요?)[.!]?"),
        re.compile(r"I (?:prefer|like|want)\s+(.{2,80}?)[.!]?$", re.IGNORECASE),
    )

    def __init__(self, memory: MemoryStore):
        self.memory = memory

    def learn(self, user_id: str, message: str) -> list[str]:
        learned: list[str] = []
        for pattern in self.PATTERNS:
            match = pattern.search(message.strip())
            if not match:
                continue
            preference = match.group(1).strip(" ,.")
            if preference and preference not in learned:
                self.memory.add(user_id, "preference", preference, "explicit-user-statement", 0.95)
                learned.append(preference)
        return learned

