"""Chat endpoints — HTTP POST and WebSocket."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from ..dependencies import get_agent, get_session_store
from ..models.chat import ChatRequest, ChatResponse
from ..session import SessionStore
from ai.base import ContentPart, ContentType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_http(
    request: ChatRequest,
    sessions: SessionStore = Depends(get_session_store),
    agent=Depends(get_agent),
):
    session = await sessions.get_or_create(request.session_id)
    try:
        reply, pattern, changed_ids = await agent.process_turn(
            user_text=request.text,
            attachments=[],
            conv_ctx=session.conversation,
            pat_ctx=session.pattern_ctx,
        )
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(500, str(e))

    svg = session.pattern_ctx.render_svg(highlight_ids=changed_ids)
    return ChatResponse(reply=reply, svg=svg, changed_ids=changed_ids)


@router.websocket("/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    sessions: SessionStore = Depends(get_session_store),
    agent=Depends(get_agent),
):
    """
    WebSocket protocol (JSON messages):
    Client → Server: {"type": "message", "text": "...", "attachments": []}
    Server → Client: {"type": "chunk", "text": "..."}   # streamed reply (future)
    Server → Client: {"type": "svg_update", "svg": "...", "changed_ids": [...]}
    Server → Client: {"type": "done", "reply": "...", "changed_ids": [...]}
    Server → Client: {"type": "error", "message": "..."}
    """
    await websocket.accept()
    session = await sessions.get_or_create(session_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "message")
            if msg_type != "message":
                continue

            user_text = data.get("text", "").strip()
            if not user_text:
                continue

            # Parse any attachments (base64 encoded files)
            attachments = []
            for att in data.get("attachments", []):
                att_type = att.get("type", "")
                att_data = att.get("data", "")
                if att_type.startswith("image/") and att_data:
                    import base64
                    raw_bytes = base64.b64decode(att_data)
                    attachments.append(ContentPart.image(raw_bytes, att_type))
                elif att_type == "application/pdf" and att_data:
                    import base64
                    raw_bytes = base64.b64decode(att_data)
                    if agent.provider.supports_pdfs:
                        attachments.append(ContentPart.pdf(raw_bytes))
                    else:
                        # Extract text from PDF
                        text = _extract_pdf_text(raw_bytes)
                        if text:
                            attachments.append(ContentPart.text(f"[PDF content]\n{text}"))

            try:
                reply, pattern, changed_ids = await agent.process_turn(
                    user_text=user_text,
                    attachments=attachments,
                    conv_ctx=session.conversation,
                    pat_ctx=session.pattern_ctx,
                )
                svg = session.pattern_ctx.render_svg(highlight_ids=changed_ids)
                await websocket.send_json({
                    "type": "svg_update",
                    "svg": svg,
                    "changed_ids": changed_ids,
                })
                await websocket.send_json({
                    "type": "done",
                    "reply": reply,
                    "changed_ids": changed_ids,
                })
            except Exception as e:
                logger.exception("Agent error in WebSocket")
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        pass


def _extract_pdf_text(data: bytes) -> str:
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""
