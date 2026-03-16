"""Parse Seamly2D .val and .vit XML files into Python dataclass trees."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .exceptions import SeamlyParseError
from .models.measurements import Measurement, MeasurementSet
from .models.pattern import DrawBlock, Line, Pattern, PatternMetadata, Unit
from .models.pieces import CustomSeamAllowance, Piece, PieceNode
from .models.points import (
    AlongLinePoint,
    BisectorPoint,
    EndLinePoint,
    LineIntersectPoint,
    NormalPoint,
    PointFromXY,
    PointOfIntersection,
    ShoulderPoint,
    SinglePoint,
)
from .models.curves import (
    ArcWithLength,
    EllipticalArc,
    SimpleArc,
    SimpleSpline,
    SplinePath,
    SplinePathPoint,
)


def _int(el: ET.Element, attr: str, default: int = 0) -> int:
    v = el.get(attr)
    return int(v) if v is not None else default


def _float(el: ET.Element, attr: str, default: float = 0.0) -> float:
    v = el.get(attr)
    return float(v) if v is not None else default


def _str(el: ET.Element, attr: str, default: str = "") -> str:
    return el.get(attr, default)


def _bool_str(el: ET.Element, attr: str, default: bool = True) -> bool:
    v = el.get(attr, "").lower()
    if v in ("true", "1"):
        return True
    if v in ("false", "0"):
        return False
    return default


class ValParser:
    """Parse a Seamly2D .val pattern file into a Pattern object."""

    def parse(self, path: Path) -> Pattern:
        try:
            tree = ET.parse(str(path))
        except ET.ParseError as e:
            raise SeamlyParseError(f"XML parse error in {path}: {e}") from e
        return self._parse_root(tree.getroot())

    def parse_string(self, xml: str) -> Pattern:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as e:
            raise SeamlyParseError(f"XML parse error: {e}") from e
        return self._parse_root(root)

    # ------------------------------------------------------------------
    def _parse_root(self, root: ET.Element) -> Pattern:
        if root.tag != "pattern":
            raise SeamlyParseError(f"Expected <pattern> root, got <{root.tag}>")

        metadata = self._parse_metadata(root)
        pattern = Pattern(metadata=metadata)

        for draw_el in root.findall("draw"):
            pattern.draws.append(self._parse_draw(draw_el))

        pieces_el = root.find("pieces")
        if pieces_el is not None:
            for piece_el in pieces_el.findall("piece"):
                pattern.pieces.append(self._parse_piece(piece_el))

        return pattern

    def _parse_metadata(self, root: ET.Element) -> PatternMetadata:
        unit_str = root.get("unit", "cm")
        try:
            unit = Unit(unit_str)
        except ValueError:
            unit = Unit.CM

        return PatternMetadata(
            version=root.get("version", "0.8.9"),
            full_name=root.get("fullName", ""),
            description=root.get("description", ""),
            notes=root.get("notes", ""),
            pattern_number=root.get("patternNumber", ""),
            company=root.get("company", ""),
            customer=root.get("customer", ""),
            measurement_file=root.get("measurementFile", ""),
            unit=unit,
            label_date_format=root.get("labelDateFormat", ""),
            label_path_format=root.get("labelPathFormat", ""),
        )

    def _parse_draw(self, draw_el: ET.Element) -> DrawBlock:
        block = DrawBlock(name=draw_el.get("name", ""))

        calc_el = draw_el.find("calculation")
        if calc_el is not None:
            self._parse_calculation(calc_el, block)

        return block

    def _parse_calculation(self, calc_el: ET.Element, block: DrawBlock) -> None:
        for child in calc_el:
            tag = child.tag
            if tag == "point":
                pt = self._parse_point(child)
                if pt is not None:
                    block.points.append(pt)
            elif tag == "line":
                block.lines.append(self._parse_line(child))
            elif tag == "spline":
                sp = self._parse_spline(child)
                if sp is not None:
                    block.splines.append(sp)
            elif tag == "arc":
                arc = self._parse_arc(child)
                if arc is not None:
                    block.arcs.append(arc)
            elif tag == "elArc":
                arc = self._parse_el_arc(child)
                if arc is not None:
                    block.el_arcs.append(arc)

    def _base_attrs(self, el: ET.Element) -> dict:
        return dict(
            id=_int(el, "id"),
            mx=_float(el, "mx", 0.1),
            my=_float(el, "my", 0.15),
            show_name=_bool_str(el, "showPointName", True),
        )

    def _parse_point(self, el: ET.Element):
        ptype = el.get("type", "")
        base = self._base_attrs(el)
        name = _str(el, "name")

        if ptype == "single":
            return SinglePoint(**base, name=name,
                               x=_float(el, "x"), y=_float(el, "y"))

        elif ptype == "endLine":
            return EndLinePoint(**base, name=name,
                                base_point=_int(el, "basePoint"),
                                length=_str(el, "length", "1.0"),
                                angle=_str(el, "angle", "0"),
                                type_line=_str(el, "typeLine", "hair"),
                                line_weight=_str(el, "lineWeight", "0.35"),
                                line_color=_str(el, "lineColor", "black"))

        elif ptype == "alongLine":
            return AlongLinePoint(**base, name=name,
                                  first_point=_int(el, "firstPoint"),
                                  second_point=_int(el, "secondPoint"),
                                  length=_str(el, "length", "1.0"),
                                  type_line=_str(el, "typeLine", "none"),
                                  line_weight=_str(el, "lineWeight", "0.35"),
                                  line_color=_str(el, "lineColor", "black"))

        elif ptype == "normal":
            return NormalPoint(**base, name=name,
                               first_point=_int(el, "firstPoint"),
                               second_point=_int(el, "secondPoint"),
                               length=_str(el, "length", "1.0"),
                               angle=_str(el, "angle", "0"),
                               type_line=_str(el, "typeLine", "hair"),
                               line_weight=_str(el, "lineWeight", "0.35"),
                               line_color=_str(el, "lineColor", "black"))

        elif ptype == "bisector":
            return BisectorPoint(**base, name=name,
                                 first_point=_int(el, "firstPoint"),
                                 second_point=_int(el, "secondPoint"),
                                 third_point=_int(el, "thirdPoint"),
                                 length=_str(el, "length", "1.0"),
                                 type_line=_str(el, "typeLine", "hair"),
                                 line_weight=_str(el, "lineWeight", "0.35"),
                                 line_color=_str(el, "lineColor", "black"))

        elif ptype == "lineIntersect":
            return LineIntersectPoint(**base, name=name,
                                      p1_line1=_int(el, "p1Line1"),
                                      p2_line1=_int(el, "p2Line1"),
                                      p1_line2=_int(el, "p1Line2"),
                                      p2_line2=_int(el, "p2Line2"))

        elif ptype == "shoulder":
            return ShoulderPoint(**base, name=name,
                                 p1_line=_int(el, "p1Line"),
                                 p2_line=_int(el, "p2Line"),
                                 p_shoulder=_int(el, "pShoulder"),
                                 length=_str(el, "length", "1.0"),
                                 type_line=_str(el, "typeLine", "hair"),
                                 line_weight=_str(el, "lineWeight", "0.35"),
                                 line_color=_str(el, "lineColor", "black"))

        elif ptype == "pointOfIntersection":
            return PointOfIntersection(**base, name=name,
                                       first_point=_int(el, "firstPoint"),
                                       second_point=_int(el, "secondPoint"))

        elif ptype in ("pointFromXandYOfTwoPoints",):
            return PointFromXY(**base, name=name,
                               first_point=_int(el, "firstPoint"),
                               second_point=_int(el, "secondPoint"))

        # Unknown type — skip silently
        return None

    def _parse_line(self, el: ET.Element) -> Line:
        return Line(
            first_point=_int(el, "firstPoint"),
            second_point=_int(el, "secondPoint"),
            type_line=_str(el, "typeLine", "hair"),
            line_weight=_str(el, "lineWeight", "0.35"),
            line_color=_str(el, "lineColor", "black"),
        )

    def _parse_spline(self, el: ET.Element):
        stype = el.get("type", "")
        base = self._base_attrs(el)

        if stype == "simpleInteractive":
            return SimpleSpline(**base,
                                point1=_int(el, "point1"),
                                point4=_int(el, "point4"),
                                angle1=_str(el, "angle1", "0"),
                                angle2=_str(el, "angle2", "180"),
                                length1=_str(el, "length1", "1.0"),
                                length2=_str(el, "length2", "1.0"),
                                type_line=_str(el, "typeLine", "hair"),
                                line_weight=_str(el, "lineWeight", "0.35"),
                                line_color=_str(el, "lineColor", "black"))

        elif stype in ("pathInteractive", "cubicBezierPath"):
            path_points = []
            for pp in el.findall("pathPoint"):
                path_points.append(SplinePathPoint(
                    p_spline=_int(pp, "pSpline"),
                    angle1=_str(pp, "angle1", "0"),
                    angle2=_str(pp, "angle2", "180"),
                    length1=_str(pp, "length1", "1.0"),
                    length2=_str(pp, "length2", "1.0"),
                ))
            return SplinePath(**base, path_points=path_points,
                              type_line=_str(el, "typeLine", "hair"),
                              line_weight=_str(el, "lineWeight", "0.35"),
                              line_color=_str(el, "lineColor", "black"))
        return None

    def _parse_arc(self, el: ET.Element):
        atype = el.get("type", "simple")
        base = self._base_attrs(el)

        if atype == "simple":
            return SimpleArc(**base,
                             center=_int(el, "center"),
                             radius=_str(el, "radius", "1.0"),
                             angle1=_str(el, "angle1", "0"),
                             angle2=_str(el, "angle2", "90"),
                             type_line=_str(el, "typeLine", "hair"),
                             line_weight=_str(el, "lineWeight", "0.35"),
                             line_color=_str(el, "lineColor", "black"))

        elif atype == "arcWithLength":
            return ArcWithLength(**base,
                                 center=_int(el, "center"),
                                 radius=_str(el, "radius", "1.0"),
                                 angle1=_str(el, "angle1", "0"),
                                 length=_str(el, "length", "10.0"),
                                 type_line=_str(el, "typeLine", "hair"),
                                 line_weight=_str(el, "lineWeight", "0.35"),
                                 line_color=_str(el, "lineColor", "black"))
        return None

    def _parse_el_arc(self, el: ET.Element):
        base = self._base_attrs(el)
        return EllipticalArc(**base,
                             center=_int(el, "center"),
                             radius1=_str(el, "radius1", "1.0"),
                             radius2=_str(el, "radius2", "0.5"),
                             angle1=_str(el, "angle1", "0"),
                             angle2=_str(el, "angle2", "90"),
                             rotation_angle=_str(el, "rotationAngle", "0"),
                             type_line=_str(el, "typeLine", "hair"),
                             line_weight=_str(el, "lineWeight", "0.35"),
                             line_color=_str(el, "lineColor", "black"))

    def _parse_piece(self, el: ET.Element) -> Piece:
        nodes = []
        nodes_el = el.find("nodes")
        if nodes_el is not None:
            for node_el in nodes_el.findall("node"):
                reverse_val = node_el.get("reverse", "0")
                nodes.append(PieceNode(
                    id_object=_int(node_el, "idObject"),
                    node_type=_str(node_el, "type", "NodePoint"),
                    reverse=reverse_val in ("1", "true"),
                ))

        sa_width = el.get("width", "1.0")
        return Piece(
            id=_int(el, "id"),
            name=_str(el, "name"),
            in_layout=_bool_str(el, "inLayout", True),
            seam_allowance=_bool_str(el, "seamAllowance", False),
            seam_allowance_width=sa_width,
            united=_bool_str(el, "united", False),
            nodes=nodes,
        )


class VitParser:
    """Parse a Seamly2D .vit individual measurement file."""

    def parse(self, path: Path) -> MeasurementSet:
        try:
            tree = ET.parse(str(path))
        except ET.ParseError as e:
            raise SeamlyParseError(f"XML parse error in {path}: {e}") from e
        return self._parse_root(tree.getroot())

    def parse_string(self, xml: str) -> MeasurementSet:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as e:
            raise SeamlyParseError(f"XML parse error: {e}") from e
        return self._parse_root(root)

    def _parse_root(self, root: ET.Element) -> MeasurementSet:
        ms = MeasurementSet(
            version=root.get("version", "0.5.1"),
            units=root.get("units", "cm"),
            full_name=root.get("fullName", ""),
            gender=root.get("gender", "female"),
            pm_system=root.get("pmSystem", ""),
        )
        for m_el in root.findall("m"):
            name = m_el.get("name", "")
            if not name:
                continue
            try:
                value = float(m_el.get("value", "0"))
            except ValueError:
                value = 0.0
            ms.measurements[name] = Measurement(
                name=name,
                value=value,
                full_name=m_el.get("fullName", ""),
                description=m_el.get("description", ""),
            )
        return ms
