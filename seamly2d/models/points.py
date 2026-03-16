from dataclasses import dataclass, field
from typing import Union


@dataclass
class BaseGeom:
    id: int = 0
    mx: float = 0.1
    my: float = 0.15
    show_name: bool = True


@dataclass
class SinglePoint(BaseGeom):
    """type="single" — absolute origin point."""
    name: str = "A"
    x: float = 0.0
    y: float = 0.0


@dataclass
class EndLinePoint(BaseGeom):
    """type="endLine" — point at distance/angle from base."""
    name: str = ""
    base_point: int = 0
    length: str = "1.0"
    angle: str = "0"
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class AlongLinePoint(BaseGeom):
    """type="alongLine" — point along a line segment at a distance."""
    name: str = ""
    first_point: int = 0
    second_point: int = 0
    length: str = "1.0"
    type_line: str = "none"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class NormalPoint(BaseGeom):
    """type="normal" — point perpendicular to a line."""
    name: str = ""
    first_point: int = 0
    second_point: int = 0
    length: str = "1.0"
    angle: str = "0"
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class BisectorPoint(BaseGeom):
    """type="bisector"."""
    name: str = ""
    first_point: int = 0
    second_point: int = 0
    third_point: int = 0
    length: str = "1.0"
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class LineIntersectPoint(BaseGeom):
    """type="lineIntersect"."""
    name: str = ""
    p1_line1: int = 0
    p2_line1: int = 0
    p1_line2: int = 0
    p2_line2: int = 0


@dataclass
class ShoulderPoint(BaseGeom):
    """type="shoulder"."""
    name: str = ""
    p1_line: int = 0
    p2_line: int = 0
    p_shoulder: int = 0
    length: str = "1.0"
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class PointOfIntersection(BaseGeom):
    """type="pointOfIntersection" — intersection from x/y of two points."""
    name: str = ""
    first_point: int = 0
    second_point: int = 0


@dataclass
class PointFromXY(BaseGeom):
    """type="pointFromXandYOfTwoPoints"."""
    name: str = ""
    first_point: int = 0
    second_point: int = 0


# Union alias for all point types
AnyPoint = Union[
    SinglePoint, EndLinePoint, AlongLinePoint, NormalPoint,
    BisectorPoint, LineIntersectPoint, ShoulderPoint,
    PointOfIntersection, PointFromXY
]
