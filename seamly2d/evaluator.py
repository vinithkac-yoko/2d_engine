"""Safe formula evaluator for Seamly2D formula strings.

Uses simpleeval for sandboxed expression evaluation.
Never uses Python's built-in eval() on raw formula strings.
"""

import math
from typing import Optional

from simpleeval import SimpleEval, InvalidExpression

from .exceptions import FormulaEvalError


def _deg_to_rad(deg: float) -> float:
    return deg * math.pi / 180.0


# Functions available inside formulas
_SAFE_FUNCTIONS = {
    "sin": lambda x: math.sin(_deg_to_rad(x)),
    "cos": lambda x: math.cos(_deg_to_rad(x)),
    "tan": lambda x: math.tan(_deg_to_rad(x)),
    "asin": lambda x: math.degrees(math.asin(x)),
    "acos": lambda x: math.degrees(math.acos(x)),
    "atan": lambda x: math.degrees(math.atan(x)),
    "atan2": lambda y, x: math.degrees(math.atan2(y, x)),
    "sqrt": math.sqrt,
    "abs": abs,
    "ceil": math.ceil,
    "floor": math.floor,
    "round": round,
    "pow": math.pow,
    "pi": math.pi,
    # Seamly2D geometry helpers — resolved from variable table
    # These are registered as stubs that look up pre-computed values
}


class FormulaEvaluator:
    """Evaluate Seamly2D formula strings against a set of variables.

    Variables include:
    - Measurement values (e.g. bust=88, waist=68)
    - Geometry-derived variables (e.g. Line_A_A1=2.0, Arc_1=5.2)
    - Custom increments defined in the pattern
    """

    def __init__(self, measurements: Optional[dict] = None,
                 geometry_vars: Optional[dict] = None):
        self._vars: dict[str, float] = {}
        if measurements:
            self._vars.update(measurements)
        if geometry_vars:
            self._vars.update(geometry_vars)

        self._evaluator = SimpleEval(functions=dict(_SAFE_FUNCTIONS))
        self._evaluator.names = self._vars

    def update_variable(self, name: str, value: float) -> None:
        self._vars[name] = value
        self._evaluator.names = self._vars

    def update_variables(self, variables: dict[str, float]) -> None:
        self._vars.update(variables)
        self._evaluator.names = self._vars

    def evaluate(self, formula: str) -> float:
        """Evaluate a formula string and return a float result."""
        if not formula or formula.strip() == "":
            return 0.0
        # Try direct float parse first (common case)
        try:
            return float(formula)
        except ValueError:
            pass
        try:
            result = self._evaluator.eval(formula)
            return float(result)
        except (InvalidExpression, ZeroDivisionError, ValueError, TypeError, KeyError) as e:
            raise FormulaEvalError(
                f"Cannot evaluate formula {formula!r}: {e}"
            ) from e

    def evaluate_angle(self, formula: str) -> float:
        """Evaluate an angle formula, returning degrees."""
        return self.evaluate(formula)

    def safe_evaluate(self, formula: str, default: float = 0.0) -> float:
        """Like evaluate but returns default on error instead of raising."""
        try:
            return self.evaluate(formula)
        except FormulaEvalError:
            return default

    @classmethod
    def from_measurement_set(cls, mset) -> "FormulaEvaluator":
        """Build an evaluator from a MeasurementSet object."""
        return cls(measurements=mset.to_dict() if mset else {})
