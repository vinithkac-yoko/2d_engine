"""Serialize Pattern dataclass trees back to Seamly2D .val XML."""

import xml.etree.ElementTree as ET
from xml.dom import minidom

from .models.measurements import MeasurementSet
from .models.pattern import DrawBlock, Line, Pattern
from .models.pieces import Piece
from .models.points import (
    AlongLinePoint, BisectorPoint, EndLinePoint, LineIntersectPoint,
    NormalPoint, PointFromXY, PointOfIntersection, ShoulderPoint, SinglePoint,
)
from .models.curves import (
    ArcWithLength, EllipticalArc, SimpleArc, SimpleSpline, SplinePath,
)


def _set(el: ET.Element, attr: str, value) -> None:
    if value is not None:
        el.set(attr, str(value))


def _bool_attr(value: bool) -> str:
    return "true" if value else "false"


class ValSerializer:
    """Serialize a Pattern back to a pretty-printed .val XML string."""

    def serialize(self, pattern: Pattern) -> str:
        root = ET.Element("pattern")
        meta = pattern.metadata
        root.set("version", meta.version)
        root.set("fullName", meta.full_name)
        root.set("email", "")
        root.set("description", meta.description)
        root.set("notes", meta.notes)
        root.set("patternNumber", meta.pattern_number)
        root.set("company", meta.company)
        root.set("customer", meta.customer)
        root.set("measurementFile", meta.measurement_file)
        root.set("unit", meta.unit.value)
        root.set("labelDateFormat", meta.label_date_format)
        root.set("labelPathFormat", meta.label_path_format)

        ET.SubElement(root, "patternName").text = meta.full_name
        ET.SubElement(root, "patternMaterials")

        for draw in pattern.draws:
            root.append(self._serialize_draw(draw))

        pieces_el = ET.SubElement(root, "pieces")
        for piece in pattern.pieces:
            pieces_el.append(self._serialize_piece(piece))

        ET.SubElement(root, "groups")

        return self._prettify(root)

    def _prettify(self, root: ET.Element) -> str:
        raw = ET.tostring(root, encoding="unicode", xml_declaration=False)
        reparsed = minidom.parseString(f'<?xml version="1.0" encoding="UTF-8"?>{raw}')
        return reparsed.toprettyxml(indent="  ", encoding=None)

    def _serialize_draw(self, draw: DrawBlock) -> ET.Element:
        draw_el = ET.Element("draw")
        draw_el.set("name", draw.name)

        calc_el = ET.SubElement(draw_el, "calculation")
        for pt in draw.points:
            calc_el.append(self._serialize_point(pt))
        for line in draw.lines:
            calc_el.append(self._serialize_line(line))
        for sp in draw.splines:
            calc_el.append(self._serialize_spline(sp))
        for arc in draw.arcs:
            calc_el.append(self._serialize_arc(arc))
        for el_arc in draw.el_arcs:
            calc_el.append(self._serialize_el_arc(el_arc))

        ET.SubElement(draw_el, "modeling")
        return draw_el

    def _base_attrs(self, el: ET.Element, obj) -> None:
        el.set("id", str(obj.id))
        el.set("mx", str(obj.mx))
        el.set("my", str(obj.my))
        el.set("showPointName", _bool_attr(obj.show_name))

    def _serialize_point(self, pt) -> ET.Element:
        el = ET.Element("point")
        self._base_attrs(el, pt)

        if isinstance(pt, SinglePoint):
            el.set("type", "single")
            el.set("name", pt.name)
            el.set("x", str(pt.x))
            el.set("y", str(pt.y))

        elif isinstance(pt, EndLinePoint):
            el.set("type", "endLine")
            el.set("name", pt.name)
            el.set("basePoint", str(pt.base_point))
            el.set("length", pt.length)
            el.set("angle", pt.angle)
            el.set("typeLine", pt.type_line)
            el.set("lineWeight", pt.line_weight)
            el.set("lineColor", pt.line_color)

        elif isinstance(pt, AlongLinePoint):
            el.set("type", "alongLine")
            el.set("name", pt.name)
            el.set("firstPoint", str(pt.first_point))
            el.set("secondPoint", str(pt.second_point))
            el.set("length", pt.length)
            el.set("typeLine", pt.type_line)
            el.set("lineWeight", pt.line_weight)
            el.set("lineColor", pt.line_color)

        elif isinstance(pt, NormalPoint):
            el.set("type", "normal")
            el.set("name", pt.name)
            el.set("firstPoint", str(pt.first_point))
            el.set("secondPoint", str(pt.second_point))
            el.set("length", pt.length)
            el.set("angle", pt.angle)
            el.set("typeLine", pt.type_line)
            el.set("lineWeight", pt.line_weight)
            el.set("lineColor", pt.line_color)

        elif isinstance(pt, BisectorPoint):
            el.set("type", "bisector")
            el.set("name", pt.name)
            el.set("firstPoint", str(pt.first_point))
            el.set("secondPoint", str(pt.second_point))
            el.set("thirdPoint", str(pt.third_point))
            el.set("length", pt.length)
            el.set("typeLine", pt.type_line)
            el.set("lineWeight", pt.line_weight)
            el.set("lineColor", pt.line_color)

        elif isinstance(pt, LineIntersectPoint):
            el.set("type", "lineIntersect")
            el.set("name", pt.name)
            el.set("p1Line1", str(pt.p1_line1))
            el.set("p2Line1", str(pt.p2_line1))
            el.set("p1Line2", str(pt.p1_line2))
            el.set("p2Line2", str(pt.p2_line2))

        elif isinstance(pt, ShoulderPoint):
            el.set("type", "shoulder")
            el.set("name", pt.name)
            el.set("p1Line", str(pt.p1_line))
            el.set("p2Line", str(pt.p2_line))
            el.set("pShoulder", str(pt.p_shoulder))
            el.set("length", pt.length)
            el.set("typeLine", pt.type_line)
            el.set("lineWeight", pt.line_weight)
            el.set("lineColor", pt.line_color)

        elif isinstance(pt, PointOfIntersection):
            el.set("type", "pointOfIntersection")
            el.set("name", pt.name)
            el.set("firstPoint", str(pt.first_point))
            el.set("secondPoint", str(pt.second_point))

        elif isinstance(pt, PointFromXY):
            el.set("type", "pointFromXandYOfTwoPoints")
            el.set("name", pt.name)
            el.set("firstPoint", str(pt.first_point))
            el.set("secondPoint", str(pt.second_point))

        return el

    def _serialize_line(self, line: Line) -> ET.Element:
        el = ET.Element("line")
        el.set("firstPoint", str(line.first_point))
        el.set("secondPoint", str(line.second_point))
        el.set("typeLine", line.type_line)
        el.set("lineWeight", line.line_weight)
        el.set("lineColor", line.line_color)
        return el

    def _serialize_spline(self, sp) -> ET.Element:
        el = ET.Element("spline")
        self._base_attrs(el, sp)

        if isinstance(sp, SimpleSpline):
            el.set("type", "simpleInteractive")
            el.set("point1", str(sp.point1))
            el.set("point4", str(sp.point4))
            el.set("angle1", sp.angle1)
            el.set("angle2", sp.angle2)
            el.set("length1", sp.length1)
            el.set("length2", sp.length2)
            el.set("typeLine", sp.type_line)
            el.set("lineWeight", sp.line_weight)
            el.set("lineColor", sp.line_color)

        elif isinstance(sp, SplinePath):
            el.set("type", "pathInteractive")
            el.set("typeLine", sp.type_line)
            el.set("lineWeight", sp.line_weight)
            el.set("lineColor", sp.line_color)
            for pp in sp.path_points:
                pp_el = ET.SubElement(el, "pathPoint")
                pp_el.set("pSpline", str(pp.p_spline))
                pp_el.set("angle1", pp.angle1)
                pp_el.set("angle2", pp.angle2)
                pp_el.set("length1", pp.length1)
                pp_el.set("length2", pp.length2)

        return el

    def _serialize_arc(self, arc) -> ET.Element:
        el = ET.Element("arc")
        self._base_attrs(el, arc)

        if isinstance(arc, SimpleArc):
            el.set("type", "simple")
            el.set("center", str(arc.center))
            el.set("radius", arc.radius)
            el.set("angle1", arc.angle1)
            el.set("angle2", arc.angle2)
            el.set("typeLine", arc.type_line)
            el.set("lineWeight", arc.line_weight)
            el.set("lineColor", arc.line_color)

        elif isinstance(arc, ArcWithLength):
            el.set("type", "arcWithLength")
            el.set("center", str(arc.center))
            el.set("radius", arc.radius)
            el.set("angle1", arc.angle1)
            el.set("length", arc.length)
            el.set("typeLine", arc.type_line)
            el.set("lineWeight", arc.line_weight)
            el.set("lineColor", arc.line_color)

        return el

    def _serialize_el_arc(self, arc: EllipticalArc) -> ET.Element:
        el = ET.Element("elArc")
        self._base_attrs(el, arc)
        el.set("center", str(arc.center))
        el.set("radius1", arc.radius1)
        el.set("radius2", arc.radius2)
        el.set("angle1", arc.angle1)
        el.set("angle2", arc.angle2)
        el.set("rotationAngle", arc.rotation_angle)
        el.set("typeLine", arc.type_line)
        el.set("lineWeight", arc.line_weight)
        el.set("lineColor", arc.line_color)
        return el

    def _serialize_piece(self, piece: Piece) -> ET.Element:
        el = ET.Element("piece")
        el.set("id", str(piece.id))
        el.set("name", piece.name)
        el.set("inLayout", "1" if piece.in_layout else "0")
        el.set("seamAllowance", "1" if piece.seam_allowance else "0")
        el.set("width", str(piece.seam_allowance_width))
        el.set("united", "1" if piece.united else "0")
        el.set("version", "2")

        nodes_el = ET.SubElement(el, "nodes")
        for node in piece.nodes:
            node_el = ET.SubElement(nodes_el, "node")
            node_el.set("idObject", str(node.id_object))
            node_el.set("type", node.node_type)
            if node.reverse:
                node_el.set("reverse", "1")
        return el


class VitSerializer:
    """Serialize a MeasurementSet back to .vit XML."""

    def serialize(self, ms: MeasurementSet) -> str:
        root = ET.Element("measurements")
        root.set("version", ms.version)
        root.set("units", ms.units)
        root.set("fullName", ms.full_name)
        root.set("email", "")
        root.set("birthDate", "")
        root.set("gender", ms.gender)
        root.set("pmSystem", ms.pm_system)

        for m in ms.measurements.values():
            m_el = ET.SubElement(root, "m")
            m_el.set("name", m.name)
            m_el.set("value", str(m.value))
            if m.full_name:
                m_el.set("fullName", m.full_name)

        raw = ET.tostring(root, encoding="unicode")
        reparsed = minidom.parseString(f'<?xml version="1.0" encoding="UTF-8"?>{raw}')
        return reparsed.toprettyxml(indent="  ", encoding=None)
