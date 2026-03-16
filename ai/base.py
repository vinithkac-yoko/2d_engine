"""Shared data classes for AI messaging."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    AUDIO_TRANSCRIPT = "audio_transcript"


@dataclass
class ContentPart:
    type: ContentType
    text: Optional[str] = None
    data: Optional[bytes] = None
    mime_type: Optional[str] = None

    @classmethod
    def text(cls, content: str) -> "ContentPart":
        return cls(type=ContentType.TEXT, text=content)

    @classmethod
    def image(cls, data: bytes, mime_type: str = "image/png") -> "ContentPart":
        return cls(type=ContentType.IMAGE, data=data, mime_type=mime_type)

    @classmethod
    def pdf(cls, data: bytes) -> "ContentPart":
        return cls(type=ContentType.PDF, data=data, mime_type="application/pdf")


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: list = field(default_factory=list)  # list[ContentPart]

    @classmethod
    def from_text(cls, role: str, text: str) -> "Message":
        return cls(role=role, content=[ContentPart.text(text)])


@dataclass
class AIResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = "end_turn"
    tool_calls: list = field(default_factory=list)  # raw tool call blocks
    raw: Optional[object] = None


