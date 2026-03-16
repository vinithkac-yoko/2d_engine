"""OpenAI provider implementation."""

import base64
from typing import Optional, AsyncIterator

import openai as oai

from ..base import AIProvider, AIResponse, ContentPart, ContentType, Message


class OpenAIProvider(AIProvider):
    """OpenAI API — supports text and images. PDFs require text extraction."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = oai.AsyncOpenAI(api_key=api_key)
        self._model = model

    def _build_messages(self, messages: list, system_prompt: str = "") -> list:
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
                continue
            content = []
            for part in msg.content:
                content.append(self._part_to_block(part))
            result.append({"role": msg.role, "content": content})
        return result

    def _part_to_block(self, part: ContentPart) -> dict:
        if part.type == ContentType.TEXT:
            return {"type": "text", "text": part.text or ""}
        elif part.type == ContentType.IMAGE:
            encoded = base64.standard_b64encode(part.data).decode()
            url = f"data:{part.mime_type or 'image/png'};base64,{encoded}"
            return {"type": "image_url", "image_url": {"url": url}}
        # PDF not natively supported — caller should extract text first
        return {"type": "text", "text": "[PDF content not supported directly]"}

    def _convert_tools(self, tools: list) -> list:
        """Convert Anthropic-style tool definitions to OpenAI format."""
        result = []
        for t in tools:
            result.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {}),
                }
            })
        return result

    async def complete(self, messages: list, system_prompt: str = "",
                       tools: Optional[list] = None,
                       max_tokens: int = 4096,
                       temperature: float = 0.3) -> AIResponse:
        oai_messages = self._build_messages(messages, system_prompt)
        kwargs = dict(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=oai_messages,
        )
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        text = choice.message.content or ""
        tool_calls = choice.message.tool_calls or []

        return AIResponse(
            text=text,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            stop_reason=choice.finish_reason or "stop",
            tool_calls=tool_calls,
            raw=response,
        )

    async def stream(self, messages: list, system_prompt: str = "",
                     tools: Optional[list] = None,
                     max_tokens: int = 4096) -> AsyncIterator[str]:
        oai_messages = self._build_messages(messages, system_prompt)
        kwargs = dict(
            model=self._model,
            max_tokens=max_tokens,
            messages=oai_messages,
            stream=True,
        )
        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    @property
    def supports_images(self) -> bool:
        return True

    @property
    def supports_pdfs(self) -> bool:
        return False

    @property
    def model_name(self) -> str:
        return self._model
