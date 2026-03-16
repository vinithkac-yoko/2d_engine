class SeamlyError(Exception):
    """Base exception for seamly2d library."""

class SeamlyParseError(SeamlyError):
    """Raised when a .val or .vit file cannot be parsed."""

class FormulaEvalError(SeamlyError):
    """Raised when a formula string cannot be evaluated."""

class OperationError(SeamlyError):
    """Raised when a pattern operation cannot be applied."""

class IDNotFoundError(OperationError):
    """Raised when a referenced point/arc/spline ID does not exist."""
