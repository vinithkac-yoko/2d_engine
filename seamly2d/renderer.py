"""Render a Pattern to an SVG string for browser preview."""

import math
from typing import Optional

from .evaluator import FormulaEvaluator
from .models.pattern import Pattern, DrawBlock
from .models.points import (
    SinglePoint, EndLinePoint, AlongLinePoint, NormalPoint,
    BisectorPoint, LineIntersectPoint, ShoulderPoint,
    PointOfIntersection, PointFromXY,
)
from .models.curves import SimpleArc, ArcWithLength, EllipticalArc, SimpleSpline, SplinePath


POINT_RADIUS = 3
LABEL_OFFSET = 5
HIGHLIGHT_COLOR = "#e63946"
DEFAULT_STROKE = "#333333"
PIECE_FILL = "rgba(173,216,230,0.15)"
PIECE_STROKE = "#1a6496"


def _rad(deg: float) -> float:
    return deg * math.pi / 180.0


class SVGRenderer:
    """Render a Pattern to SVG string.

    Coordinate system: pattern uses Y-down (same as SVG), origin top-left.
    All coordinates in pattern units (cm), scaled to pixels by scale factor.
    """

    def __init__(self, width: int = 900, height: int = 700, padding: int = 40):
        self.width = width
        self.height = height
        self.padding = padding

    def render(self, pattern: Pattern,
               highlight_ids: Optional[list] = None) -> str:
        highlight = set(highlight_ids or [])
        evaluator = FormulaEvaluator.from_measurement_set(pattern.measurements)

        # First pass: resolve all point coordinates
        coords = self._resolve_coords(pattern, evaluator)

        if not coords:
            return self._empty_svg()

        # Compute bounding box and scale
        xs = [c[0] for c in coords.values()]
        ys = [c[1] for c in coords.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        span_x = max_x - min_x or 1
        span_y = max_y - min_y or 1

        scale_x = (self.width - 2 * self.padding) / span_x
        scale_y = (self.height - 2 * self.padding) / span_y
        scale = min(scale_x, scale_y)

        def tx(x: float) -> float:
            return (x - min_x) * scale + self.padding

        def ty(y: float) -> float:
            return (y - min_y) * scale + self.padding

        elements = []

        # Draw lines
        for draw in pattern.draws:
            id_map = pattern._build_id_map()
            for line in draw.lines:
                c1 = coords.get(line.first_point)
                c2 = coords.get(line.second_point)
                if c1 and c2:
                    elements.append(
                        f'<line x1="{tx(c1[0]):.1f}" y1="{ty(c1[1]):.1f}" '
                        f'x2="{tx(c2[0]):.1f}" y2="{ty(c2[1]):.1f}" '
                        f'stroke="{DEFAULT_STROKE}" stroke-width="1.2" stroke-opacity="0.7"/>'
                    )

            # Draw implicit lines for endLine, normal, alongLine points
            for pt in draw.points:
                stroke = HIGHLIGHT_COLOR if pt.id in highlight else DEFAULT_STROKE
                if isinstance(pt, (EndLinePoint,)) and pt.type_line != "none":
                    c1 = coords.get(pt.base_point)
                    c2 = coords.get(pt.id)
                    if c1 and c2:
                        elements.append(
                            f'<line x1="{tx(c1[0]):.1f}" y1="{ty(c1[1]):.1f}" '
                            f'x2="{tx(c2[0]):.1f}" y2="{ty(c2[1]):.1f}" '
                            f'stroke="{stroke}" stroke-width="1" opacity="0.5"/>'
                        )
                elif isinstance(pt, NormalPoint) and pt.type_line != "none":
                    c1 = coords.get(pt.first_point)
                    c2 = coords.get(pt.id)
                    if c1 and c2:
                        elements.append(
                            f'<line x1="{tx(c1[0]):.1f}" y1="{ty(c1[1]):.1f}" '
                            f'x2="{tx(c2[0]):.1f}" y2="{ty(c2[1]):.1f}" '
                            f'stroke="{stroke}" stroke-width="1" opacity="0.5"/>'
                        )

            # Draw arcs
            for arc in draw.arcs:
                svg_arc = self._arc_to_path(arc, evaluator, coords, tx, ty, scale)
                if svg_arc:
                    color = HIGHLIGHT_COLOR if arc.id in highlight else DEFAULT_STROKE
                    elements.append(
                        f'<path d="{svg_arc}" fill="none" stroke="{color}" stroke-width="1.5"/>'
                    )

            # Draw splines
            for sp in draw.splines:
                svg_sp = self._spline_to_path(sp, evaluator, coords, tx, ty, scale)
                if svg_sp:
                    color = HIGHLIGHT_COLOR if sp.id in highlight else DEFAULT_STROKE
                    elements.append(
                        f'<path d="{svg_sp}" fill="none" stroke="{color}" stroke-width="1.5"/>'
                    )

        # Draw piece outlines
        for piece in pattern.pieces:
            path_d = self._piece_to_path(piece, coords, tx, ty)
            if path_d:
                elements.append(
                    f'<path d="{path_d}" fill="{PIECE_FILL}" '
                    f'stroke="{PIECE_STROKE}" stroke-width="2"/>'
                )

        # Draw points (on top)
        for draw in pattern.draws:
            for pt in draw.points:
                c = coords.get(pt.id)
                if c is None:
                    continue
                cx, cy = tx(c[0]), ty(c[1])
                color = HIGHLIGHT_COLOR if pt.id in highlight else "#1a6496"
                name = getattr(pt, "name", "")
                elements.append(
                    f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{POINT_RADIUS}" '
                    f'fill="{color}" stroke="white" stroke-width="1" data-id="{pt.id}"/>'
                )
                if name and getattr(pt, "show_name", True):
                    elements.append(
                        f'<text x="{cx + LABEL_OFFSET:.1f}" y="{cy - LABEL_OFFSET:.1f}" '
                        f'font-size="10" fill="{color}" font-family="monospace">{name}</text>'
                    )

        body = "\n  ".join(elements)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">\n'
            f'  <rect width="100%" height="100%" fill="#fafafa"/>\n'
            f'  {body}\n'
            f'</svg>'
        )

    def _empty_svg(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}">'
            f'<rect width="100%" height="100%" fill="#fafafa"/>'
            f'<text x="50%" y="50%" text-anchor="middle" fill="#999" font-size="16">'
            f'No pattern loaded</text></svg>'
        )

    def _resolve_coords(self, pattern: Pattern,
                        evaluator: FormulaEvaluator) -> dict:
        """Resolve all point IDs to (x, y) float tuples."""
        coords: dict[int, tuple] = {}

        for draw in pattern.draws:
            for pt in draw.points:
                try:
                    xy = self._evaluate_point(pt, evaluator, coords)
                    if xy is not None:
                        coords[pt.id] = xy
                        # Register auto line-length variable for downstream formulas
                        name = getattr(pt, "name", "")
                        if name:
                            evaluator.update_variable(f"pt_{name}_x", xy[0])
                            evaluator.update_variable(f"pt_{name}_y", xy[1])
                except Exception:
                    pass  # Skip points with unresolvable formulas

        return coords

    def _evaluate_point(self, pt, evaluator: FormulaEvaluator,
                        coords: dict) -> Optional[tuple]:
        if isinstance(pt, SinglePoint):
            return (pt.x, pt.y)

        elif isinstance(pt, EndLinePoint):
            base = coords.get(pt.base_point)
            if base is None:
                return None
            length = evaluator.safe_evaluate(pt.length)
            angle = evaluator.safe_evaluate(pt.angle)
            rad = _rad(angle)
            return (base[0] + math.cos(rad) * length,
                    base[1] + math.sin(rad) * length)

        elif isinstance(pt, AlongLinePoint):
            p1 = coords.get(pt.first_point)
            p2 = coords.get(pt.second_point)
            if p1 is None or p2 is None:
                return None
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            total = math.sqrt(dx*dx + dy*dy)
            if total == 0:
                return p1
            length = evaluator.safe_evaluate(pt.length)
            t = length / total
            return (p1[0] + dx * t, p1[1] + dy * t)

        elif isinstance(pt, NormalPoint):
            p1 = coords.get(pt.first_point)
            p2 = coords.get(pt.second_point)
            if p1 is None or p2 is None:
                return None
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            total = math.sqrt(dx*dx + dy*dy)
            if total == 0:
                return p1
            # Perpendicular direction
            nx, ny = -dy / total, dx / total
            extra_angle = evaluator.safe_evaluate(pt.angle)
            if extra_angle != 0:
                rad = _rad(extra_angle)
                c, s = math.cos(rad), math.sin(rad)
                nx, ny = nx * c - ny * s, nx * s + ny * c
            length = evaluator.safe_evaluate(pt.length)
            return (p1[0] + nx * length, p1[1] + ny * length)

        elif isinstance(pt, LineIntersectPoint):
            c1 = coords.get(pt.p1_line1)
            c2 = coords.get(pt.p2_line1)
            c3 = coords.get(pt.p1_line2)
            c4 = coords.get(pt.p2_line2)
            if not all([c1, c2, c3, c4]):
                return None
            return self._line_intersect(c1, c2, c3, c4)

        elif isinstance(pt, PointOfIntersection):
            c1 = coords.get(pt.first_point)
            c2 = coords.get(pt.second_point)
            if c1 is None or c2 is None:
                return None
            return (c1[0], c2[1])  # x from first, y from second

        elif isinstance(pt, PointFromXY):
            c1 = coords.get(pt.first_point)
            c2 = coords.get(pt.second_point)
            if c1 is None or c2 is None:
                return None
            return (c1[0], c2[1])

        elif isinstance(pt, BisectorPoint):
            c1 = coords.get(pt.first_point)
            vertex = coords.get(pt.second_point)
            c3 = coords.get(pt.third_point)
            if not all([c1, vertex, c3]):
                return None
            # Direction from vertex to c1 and c3, average angle
            a1 = math.atan2(c1[1] - vertex[1], c1[0] - vertex[0])
            a3 = math.atan2(c3[1] - vertex[1], c3[0] - vertex[0])
            bis_angle = (a1 + a3) / 2.0
            length = evaluator.safe_evaluate(pt.length)
            return (vertex[0] + math.cos(bis_angle) * length,
                    vertex[1] + math.sin(bis_angle) * length)

        elif isinstance(pt, ShoulderPoint):
            p1 = coords.get(pt.p1_line)
            p2 = coords.get(pt.p2_line)
            ps = coords.get(pt.p_shoulder)
            if not all([p1, p2, ps]):
                return None
            # Place on line p1-p2 at given distance from ps
            length = evaluator.safe_evaluate(pt.length)
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            total = math.sqrt(dx*dx + dy*dy)
            if total == 0:
                return p1
            # Parameter t along p1-p2 such that dist(result, ps) = length
            # Simple approximation: midpoint of p1-p2
            return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

        return None

    @staticmethod
    def _line_intersect(p1, p2, p3, p4) -> Optional[tuple]:
        """Compute intersection of line (p1,p2) and (p3,p4)."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    def _arc_to_path(self, arc, evaluator, coords, tx, ty, scale) -> Optional[str]:
        if isinstance(arc, SimpleArc):
            center = coords.get(arc.center)
            if center is None:
                return None
            try:
                r = evaluator.safe_evaluate(arc.radius) * scale
                a1 = evaluator.safe_evaluate(arc.angle1)
                a2 = evaluator.safe_evaluate(arc.angle2)
            except Exception:
                return None
            cx, cy = tx(center[0]), ty(center[1])
            start_x = cx + r * math.cos(_rad(a1))
            start_y = cy + r * math.sin(_rad(a1))
            end_x = cx + r * math.cos(_rad(a2))
            end_y = cy + r * math.sin(_rad(a2))
            large_arc = 1 if abs(a2 - a1) > 180 else 0
            sweep = 1 if a2 > a1 else 0
            return (f"M {start_x:.1f} {start_y:.1f} "
                    f"A {r:.1f} {r:.1f} 0 {large_arc} {sweep} "
                    f"{end_x:.1f} {end_y:.1f}")
        return None

    def _spline_to_path(self, sp, evaluator, coords, tx, ty, scale) -> Optional[str]:
        if isinstance(sp, SimpleSpline):
            p1 = coords.get(sp.point1)
            p4 = coords.get(sp.point4)
            if p1 is None or p4 is None:
                return None
            try:
                a1 = evaluator.safe_evaluate(sp.angle1)
                a2 = evaluator.safe_evaluate(sp.angle2)
                l1 = evaluator.safe_evaluate(sp.length1) * scale
                l2 = evaluator.safe_evaluate(sp.length2) * scale
            except Exception:
                return None
            sx, sy = tx(p1[0]), ty(p1[1])
            ex, ey = tx(p4[0]), ty(p4[1])
            cp1x = sx + math.cos(_rad(a1)) * l1
            cp1y = sy + math.sin(_rad(a1)) * l1
            cp2x = ex + math.cos(_rad(a2 + 180)) * l2
            cp2y = ey + math.sin(_rad(a2 + 180)) * l2
            return (f"M {sx:.1f} {sy:.1f} "
                    f"C {cp1x:.1f} {cp1y:.1f} {cp2x:.1f} {cp2y:.1f} "
                    f"{ex:.1f} {ey:.1f}")

        elif isinstance(sp, SplinePath):
            if len(sp.path_points) < 2:
                return None
            parts = []
            for i, pp in enumerate(sp.path_points[:-1]):
                p1 = coords.get(pp.p_spline)
                p2 = coords.get(sp.path_points[i + 1].p_spline)
                if p1 is None or p2 is None:
                    continue
                try:
                    a1 = evaluator.safe_evaluate(pp.angle2)
                    a2 = evaluator.safe_evaluate(sp.path_points[i + 1].angle1)
                    l1 = evaluator.safe_evaluate(pp.length2) * scale
                    l2 = evaluator.safe_evaluate(sp.path_points[i + 1].length1) * scale
                except Exception:
                    continue
                sx, sy = tx(p1[0]), ty(p1[1])
                ex, ey = tx(p2[0]), ty(p2[1])
                cp1x = sx + math.cos(_rad(a1)) * l1
                cp1y = sy + math.sin(_rad(a1)) * l1
                cp2x = ex + math.cos(_rad(a2 + 180)) * l2
                cp2y = ey + math.sin(_rad(a2 + 180)) * l2
                if not parts:
                    parts.append(f"M {sx:.1f} {sy:.1f}")
                parts.append(
                    f"C {cp1x:.1f} {cp1y:.1f} {cp2x:.1f} {cp2y:.1f} {ex:.1f} {ey:.1f}"
                )
            return " ".join(parts) if parts else None

        return None

    def _piece_to_path(self, piece, coords, tx, ty) -> Optional[str]:
        points = []
        for node in piece.nodes:
            c = coords.get(node.id_object)
            if c:
                points.append((tx(c[0]), ty(c[1])))
        if len(points) < 3:
            return None
        d = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
        for px, py in points[1:]:
            d += f" L {px:.1f} {py:.1f}"
        d += " Z"
        return d
