from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    text: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str
    svg: Optional[str] = None
    changed_ids: list[int] = []
