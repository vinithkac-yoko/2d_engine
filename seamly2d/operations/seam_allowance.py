from ..models.pattern import Pattern
from ..exceptions import OperationError
from .base import PatternOperation, OperationResult


class SetSeamAllowance(PatternOperation):
    """Enable and set seam allowance width on a pattern piece."""

    def __init__(self, piece_name: str, width: float, enabled: bool = True):
        self.piece_name = piece_name
        self.width = width
        self.enabled = enabled

    def apply(self, pattern: Pattern) -> OperationResult:
        p = self._clone(pattern)
        for piece in p.pieces:
            if piece.name == self.piece_name:
                piece.seam_allowance = self.enabled
                piece.seam_allowance_width = str(self.width)
                return OperationResult(
                    success=True,
                    pattern=p,
                    message=f"Set seam allowance on '{self.piece_name}' to {self.width}cm",
                    changed_ids=[piece.id],
                )
        raise OperationError(f"Piece '{self.piece_name}' not found.")
