from dataclasses import dataclass, field
from typing import Union
from .points import BaseGeom


@dataclass
class SimpleArc(BaseGeom):
    """type="simple" — circular arc."""
    center: int = 0
    radius: str = "1.0"
    angle1: str = "0"
    angle2: str = "90"
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class ArcWithLength(BaseGeom):
    """type="arcWithLength"."""
    center: int = 0
    radius: str = "1.0"
    angle1: str = "0"
    length: str = "10.0"
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class EllipticalArc(BaseGeom):
    """type="ellipticalArc"."""
    center: int = 0
    radius1: str = "1.0"
    radius2: str = "0.5"
    angle1: str = "0"
    angle2: str = "90"
    rotation_angle: str = "0"
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class SimpleSpline(BaseGeom):
    """type="simpleInteractive" — cubic bezier via angles+lengths."""
    point1: int = 0
    point4: int = 0
    angle1: str = "0"
    angle2: str = "180"
    length1: str = "1.0"
    length2: str = "1.0"
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class SplinePathPoint:
    p_spline: int = 0
    angle1: str = "0"
    angle2: str = "180"
    length1: str = "1.0"
    length2: str = "1.0"


@dataclass
class SplinePath(BaseGeom):
    """type="pathInteractive" — multi-segment spline."""
    path_points: list = field(default_factory=list)  # list[SplinePathPoint]
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


AnyArc = Union[SimpleArc, ArcWithLength, EllipticalArc]
AnySpline = Union[SimpleSpline, SplinePath]
