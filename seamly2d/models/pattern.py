from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .measurements import MeasurementSet


class Unit(Enum):
    CM = "cm"
    MM = "mm"
    INCH = "inch"


@dataclass
class PatternMetadata:
    version: str = "0.8.9"
    full_name: str = ""
    description: str = ""
    notes: str = ""
    pattern_number: str = ""
    company: str = ""
    customer: str = ""
    measurement_file: str = ""
    unit: Unit = Unit.CM
    label_date_format: str = ""
    label_path_format: str = ""


@dataclass
class Line:
    """A visible line between two existing points."""
    first_point: int = 0
    second_point: int = 0
    type_line: str = "hair"
    line_weight: str = "0.35"
    line_color: str = "black"


@dataclass
class DrawBlock:
    name: str = ""
    points: list = field(default_factory=list)    # list[AnyPoint]
    lines: list = field(default_factory=list)     # list[Line]
    splines: list = field(default_factory=list)   # list[AnySpline]
    arcs: list = field(default_factory=list)      # list[AnyArc]
    el_arcs: list = field(default_factory=list)   # list[EllipticalArc]


@dataclass
class Pattern:
    metadata: PatternMetadata = field(default_factory=PatternMetadata)
    draws: list = field(default_factory=list)     # list[DrawBlock]
    pieces: list = field(default_factory=list)    # list[Piece]
    measurements: Optional["MeasurementSet"] = None

    def _build_id_map(self) -> dict:
        """Build a mapping from id -> geometry object across all draws."""
        id_map = {}
        for draw in self.draws:
            for obj in draw.points + draw.lines + draw.splines + draw.arcs + draw.el_arcs:
                if hasattr(obj, "id"):
                    id_map[obj.id] = obj
        return id_map

    def next_id(self) -> int:
        """Return the next available integer ID."""
        all_ids = []
        for draw in self.draws:
            for obj in draw.points + draw.splines + draw.arcs + draw.el_arcs:
                if hasattr(obj, "id"):
                    all_ids.append(obj.id)
        for piece in self.pieces:
            all_ids.append(piece.id)
        return max(all_ids, default=0) + 1

    def find_point_by_name(self, name: str):
        """Find the first point with the given label across all draws."""
        for draw in self.draws:
            for pt in draw.points:
                if hasattr(pt, "name") and pt.name == name:
                    return pt
        return None

    def find_draw_by_name(self, name: str):
        """Find a draw block by name."""
        for draw in self.draws:
            if draw.name == name:
                return draw
        return None
