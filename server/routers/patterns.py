"""Pattern upload and download endpoints."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..dependencies import get_session_store
from ..models.pattern import PatternUploadResponse
from ..session import SessionStore
from seamly2d.parser import ValParser, VitParser
from seamly2d.exceptions import SeamlyParseError
from ai.context import PatternContext

router = APIRouter(prefix="/api/patterns", tags=["patterns"])


@router.post("/upload", response_model=PatternUploadResponse)
async def upload_pattern(
    session_id: str = Form(...),
    val_file: UploadFile = File(...),
    vit_file: UploadFile = File(None),
    sessions: SessionStore = Depends(get_session_store),
):
    val_bytes = await val_file.read()
    if len(val_bytes) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 20MB)")

    try:
        parser = ValParser()
        pattern = parser.parse_string(val_bytes.decode("utf-8"))
    except (SeamlyParseError, UnicodeDecodeError) as e:
        raise HTTPException(400, f"Cannot parse pattern file: {e}")

    if vit_file:
        vit_bytes = await vit_file.read()
        try:
            vit_parser = VitParser()
            pattern.measurements = vit_parser.parse_string(
                vit_bytes.decode("utf-8")
            )
        except Exception:
            pass  # Measurements are optional

    session = await sessions.get_or_create(session_id)
    session.pattern_ctx.pattern = pattern
    session.conversation.clear()

    svg = session.pattern_ctx.render_svg()

    return PatternUploadResponse(
        session_id=session_id,
        svg=svg,
        draw_names=[d.name for d in pattern.draws],
        piece_names=[p.name for p in pattern.pieces],
        measurement_count=len(pattern.measurements.measurements)
        if pattern.measurements else 0,
    )


@router.get("/download/{session_id}")
async def download_pattern(
    session_id: str,
    sessions: SessionStore = Depends(get_session_store),
):
    session = await sessions.get(session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    from seamly2d.serializer import ValSerializer
    serializer = ValSerializer()
    xml_str = serializer.serialize(session.pattern_ctx.pattern)

    return Response(
        content=xml_str.encode("utf-8"),
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=pattern.val"},
    )
