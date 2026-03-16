"""Abstract AI provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, AsyncIterator


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


class AIProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list, system_prompt: str = "",
                       tools: Optional[list] = None,
                       max_tokens: int = 4096,
                       temperature: float = 0.3) -> AIResponse:
        ...

    @abstractmethod
    async def stream(self, messages: list, system_prompt: str = "",
                     tools: Optional[list] = None,
                     max_tokens: int = 4096) -> AsyncIterator[str]:
        ...

    @property
    @abstractmethod
    def supports_images(self) -> bool: ...

    @property
    @abstractmethod
    def supports_pdfs(self) -> bool: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...
