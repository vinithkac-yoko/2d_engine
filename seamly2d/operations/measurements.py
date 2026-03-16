from ..models.pattern import Pattern
from ..models.measurements import Measurement
from ..exceptions import OperationError
from .base import PatternOperation, OperationResult


class UpdateMeasurement(PatternOperation):
    """Update the value of a body measurement variable."""

    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value

    def apply(self, pattern: Pattern) -> OperationResult:
        p = self._clone(pattern)
        if p.measurements is None:
            raise OperationError("Pattern has no measurement set loaded.")
        p.measurements.set(self.name, self.value)
        return OperationResult(
            success=True,
            pattern=p,
            message=f"Updated measurement '{self.name}' to {self.value}",
            changed_ids=[],
        )
