from pydantic import BaseModel
from typing import Optional


class PatternUploadResponse(BaseModel):
    session_id: str
    svg: str
    draw_names: list[str]
    piece_names: list[str]
    measurement_count: int
    message: str = "Pattern loaded successfully"
