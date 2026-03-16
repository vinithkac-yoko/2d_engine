from ..models.pattern import Pattern
from ..models.points import EndLinePoint, NormalPoint, AlongLinePoint
from ..exceptions import OperationError
from .base import PatternOperation, OperationResult


class ModifyDart(PatternOperation):
    """Modify an existing dart by changing the length formula of dart intake points.

    Identifies dart intake points as EndLinePoint or NormalPoint elements
    whose names match a pattern (e.g. 'D2', 'D3') or whose base/first_point
    matches the given dart_base_point_name.
    """

    def __init__(self, draw_name: str, dart_base_point_name: str,
                 new_intake_formula: str):
        self.draw_name = draw_name
        self.dart_base_point_name = dart_base_point_name
        self.new_intake_formula = new_intake_formula

    def apply(self, pattern: Pattern) -> OperationResult:
        p = self._clone(pattern)
        draw = p.find_draw_by_name(self.draw_name)
        if draw is None:
            raise OperationError(f"Draw block '{self.draw_name}' not found.")

        base_pt = p.find_point_by_name(self.dart_base_point_name)
        if base_pt is None:
            raise OperationError(
                f"Point '{self.dart_base_point_name}' not found in pattern."
            )

        changed = []
        for pt in draw.points:
            if isinstance(pt, EndLinePoint) and pt.base_point == base_pt.id:
                pt.length = self.new_intake_formula
                changed.append(pt.id)
            elif isinstance(pt, NormalPoint) and pt.first_point == base_pt.id:
                pt.length = self.new_intake_formula
                changed.append(pt.id)

        if not changed:
            raise OperationError(
                f"No dart intake points found based on '{self.dart_base_point_name}'."
            )

        return OperationResult(
            success=True,
            pattern=p,
            message=f"Modified dart at '{self.dart_base_point_name}': intake = {self.new_intake_formula}",
            changed_ids=changed,
        )


class AddDart(PatternOperation):
    """Add a new waist dart to a draw block.

    Creates three new points:
    - D_mid: AlongLinePoint on the seam between seam_start and seam_end
    - D_left: EndLinePoint offset left of D_mid
    - D_right: EndLinePoint offset right of D_mid
    - D_apex: NormalPoint above D_mid (dart tip)
    """

    def __init__(self, draw_name: str, seam_start_name: str, seam_end_name: str,
                 intake_formula: str = "(bust-waist)/6",
                 length_formula: str = "12",
                 position_formula: str = "0.5"):
        self.draw_name = draw_name
        self.seam_start_name = seam_start_name
        self.seam_end_name = seam_end_name
        self.intake_formula = intake_formula
        self.length_formula = length_formula
        self.position_formula = position_formula  # fraction along seam

    def apply(self, pattern: Pattern) -> OperationResult:
        p = self._clone(pattern)
        draw = p.find_draw_by_name(self.draw_name)
        if draw is None:
            raise OperationError(f"Draw block '{self.draw_name}' not found.")

        p1 = p.find_point_by_name(self.seam_start_name)
        p2 = p.find_point_by_name(self.seam_end_name)
        if p1 is None:
            raise OperationError(f"Point '{self.seam_start_name}' not found.")
        if p2 is None:
            raise OperationError(f"Point '{self.seam_end_name}' not found.")

        # Use the seam length auto-variable for position
        seg_var = f"Line_{self.seam_start_name}_{self.seam_end_name}"
        pos_formula = f"{seg_var}*{self.position_formula}"

        nid = p.next_id()
        # Dart midpoint on seam
        d_mid = AlongLinePoint(
            id=nid, name="DartMid",
            first_point=p1.id, second_point=p2.id,
            length=pos_formula, type_line="none",
        )
        draw.points.append(d_mid)
        nid += 1

        # Dart left (intake/2 in direction of seam)
        d_left = AlongLinePoint(
            id=nid, name="DartL",
            first_point=p1.id, second_point=p2.id,
            length=f"{pos_formula}-{self.intake_formula}/2",
            type_line="none",
        )
        draw.points.append(d_left)
        nid += 1

        # Dart right
        d_right = AlongLinePoint(
            id=nid, name="DartR",
            first_point=p1.id, second_point=p2.id,
            length=f"{pos_formula}+{self.intake_formula}/2",
            type_line="none",
        )
        draw.points.append(d_right)
        nid += 1

        # Dart apex (perpendicular from seam)
        d_apex = NormalPoint(
            id=nid, name="DartApex",
            first_point=d_left.id, second_point=d_right.id,
            length=self.length_formula, angle="0",
            type_line="none",
        )
        draw.points.append(d_apex)

        changed = [d_mid.id, d_left.id, d_right.id, d_apex.id]
        return OperationResult(
            success=True,
            pattern=p,
            message=f"Added dart between '{self.seam_start_name}' and '{self.seam_end_name}'",
            changed_ids=changed,
        )
