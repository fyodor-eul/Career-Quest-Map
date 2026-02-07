from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class QuestionSpec:
    qid: str
    type: Literal["mcq", "slider", "rating", "text"]
    prompt: str
    options: list[str] | None = None
    slider: dict[str, Any] | None = None
    placeholder: str | None = None
