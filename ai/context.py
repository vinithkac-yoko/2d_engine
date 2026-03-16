"""Conversation and pattern context for a chat session."""

import copy
from dataclasses import dataclass, field
from typing import Optional

from .base import Message
from seamly2d.models.pattern import Pattern
from seamly2d.renderer import SVGRenderer


@dataclass
class PatternContext:
    """Holds the live mutable pattern state with undo support."""
    pattern: Pattern
    session_id: str
    _undo_stack: list = field(default_factory=list, repr=False)
    _renderer: SVGRenderer = field(default_factory=SVGRenderer, repr=False)
    MAX_UNDO = 20

    def push_undo(self) -> None:
        self._undo_stack.append(copy.deepcopy(self.pattern))
        if len(self._undo_stack) > self.MAX_UNDO:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self.pattern = self._undo_stack.pop()
        return True

    def render_svg(self, highlight_ids: Optional[list] = None) -> str:
        return self._renderer.render(self.pattern, highlight_ids)


@dataclass
class ConversationContext:
    """Message history for one chat session."""
    session_id: str
    messages: list = field(default_factory=list)  # list[Message | dict]
    max_history: int = 40

    def add(self, message) -> None:
        self.messages.append(message)
        # Trim to max_history, always keeping pairs
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def get_recent(self) -> list:
        return list(self.messages)

    def clear(self) -> None:
        self.messages.clear()
