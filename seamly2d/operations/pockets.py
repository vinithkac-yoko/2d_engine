from ..models.pattern import Pattern
from ..models.points import AlongLinePoint
from ..exceptions import OperationError
from .base import PatternOperation, OperationResult


class AddPocketOpening(PatternOperation):
    """Mark a pocket opening on a seam line by inserting two AlongLinePoint elements.

    Creates:
    - PktTop: start of pocket opening
    - PktBot: end of pocket opening (PktTop + opening_width)
    """

    def __init__(self, draw_name: str, seam_start_name: str, seam_end_name: str,
                 opening_width: str = "15",
                 distance_from_start: str = "5"):
        self.draw_name = draw_name
        self.seam_start_name = seam_start_name
        self.seam_end_name = seam_end_name
        self.opening_width = opening_width
        self.distance_from_start = distance_from_start

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

        nid = p.next_id()
        pkt_top = AlongLinePoint(
            id=nid, name="PktTop",
            first_point=p1.id, second_point=p2.id,
            length=self.distance_from_start, type_line="hair",
            line_weight="0.35", line_color="blue",
        )
        draw.points.append(pkt_top)
        nid += 1

        pkt_bot = AlongLinePoint(
            id=nid, name="PktBot",
            first_point=p1.id, second_point=p2.id,
            length=f"{self.distance_from_start}+{self.opening_width}",
            type_line="hair", line_weight="0.35", line_color="blue",
        )
        draw.points.append(pkt_bot)

        changed = [pkt_top.id, pkt_bot.id]
        return OperationResult(
            success=True,
            pattern=p,
            message=(
                f"Added pocket opening on seam '{self.seam_start_name}'→"
                f"'{self.seam_end_name}': width={self.opening_width}cm "
                f"starting {self.distance_from_start}cm from start"
            ),
            changed_ids=changed,
        )
