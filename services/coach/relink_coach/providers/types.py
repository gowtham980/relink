from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ChatResult:
    text: str
    provider_used: str
    fallback: bool = False
    fallback_reason: str | None = None
    model: str | None = None

    def meta(self) -> dict[str, Any]:
        return asdict(self)
