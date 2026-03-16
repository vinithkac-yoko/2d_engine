"""Anthropic Claude provider implementation."""

import base64
from typing import Optional, AsyncIterator

import anthropic

from ..base import AIProvider, AIResponse, ContentPart, ContentType, Message


class ClaudeProvider(AIProvider):
    """Anthropic Claude API — supports text, images, and PDFs natively."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    def _build_messages(self, messages: list) -> list:
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
                continue
            blocks = []
            for part in msg.content:
                blocks.append(self._part_to_block(part))
            result.append({"role": msg.role, "content": blocks})
        return result

    def _part_to_block(self, part: ContentPart) -> dict:
        if part.type == ContentType.TEXT:
            return {"type": "text", "text": part.text or ""}
        elif part.type == ContentType.IMAGE:
            encoded = base64.standard_b64encode(part.data).decode()
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": part.mime_type or "image/png",
                    "data": encoded,
                },
            }
        elif part.type == ContentType.PDF:
            encoded = base64.standard_b64encode(part.data).decode()
            return {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": encoded,
                },
            }
        return {"type": "text", "text": str(part.text or "")}

    async def complete(self, messages: list, system_prompt: str = "",
                       tools: Optional[list] = None,
                       max_tokens: int = 4096,
                       temperature: float = 0.3) -> AIResponse:
        kwargs = dict(
            model=self._model,
            max_tokens=max_tokens,
            messages=self._build_messages(messages),
        )
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = tools

        response = await self.client.messages.create(**kwargs)

        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        return AIResponse(
            text="\n".join(text_parts),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason or "end_turn",
            tool_calls=tool_calls,
            raw=response,
        )

    async def stream(self, messages: list, system_prompt: str = "",
                     tools: Optional[list] = None,
                     max_tokens: int = 4096) -> AsyncIterator[str]:
        kwargs = dict(
            model=self._model,
            max_tokens=max_tokens,
            messages=self._build_messages(messages),
        )
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = tools

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    @property
    def supports_images(self) -> bool:
        return True

    @property
    def supports_pdfs(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return self._model
