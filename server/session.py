"""In-memory session store."""

import time
import asyncio
from dataclasses import dataclass, field

from ai.context import ConversationContext, PatternContext
from seamly2d.models.pattern import Pattern
from seamly2d.models.pattern import PatternMetadata


@dataclass
class Session:
    session_id: str
    conversation: ConversationContext
    pattern_ctx: PatternContext
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.last_active = time.time()


class SessionStore:
    SESSION_TTL = 3600  # 1 hour

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, session_id: str) -> Session:
        async with self._lock:
            if session_id in self._sessions:
                s = self._sessions[session_id]
                s.touch()
                return s
            # Create empty session with blank pattern
            pattern = Pattern(metadata=PatternMetadata())
            pat_ctx = PatternContext(pattern=pattern, session_id=session_id)
            conv_ctx = ConversationContext(session_id=session_id)
            session = Session(
                session_id=session_id,
                conversation=conv_ctx,
                pattern_ctx=pat_ctx,
            )
            self._sessions[session_id] = session
            return session

    async def get(self, session_id: str) -> Session | None:
        async with self._lock:
            s = self._sessions.get(session_id)
            if s:
                s.touch()
            return s

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def cleanup_expired(self) -> None:
        now = time.time()
        async with self._lock:
            expired = [sid for sid, s in self._sessions.items()
                       if now - s.last_active > self.SESSION_TTL]
            for sid in expired:
                del self._sessions[sid]
