import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..models.pattern import Pattern


@dataclass
class OperationResult:
    success: bool
    pattern: Pattern
    message: str = ""
    changed_ids: list = field(default_factory=list)


class PatternOperation(ABC):
    @abstractmethod
    def apply(self, pattern: Pattern) -> OperationResult:
        ...

    def _clone(self, pattern: Pattern) -> Pattern:
        """Deep copy pattern before mutation."""
        return copy.deepcopy(pattern)
