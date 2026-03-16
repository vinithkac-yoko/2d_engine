from dataclasses import dataclass, field


@dataclass
class PieceNode:
    id_object: int = 0
    node_type: str = "NodePoint"  # NodePoint, NodeArc, NodeSpline, NodeSplinePath
    reverse: bool = False


@dataclass
class CustomSeamAllowance:
    enabled: bool = False
    nodes: list = field(default_factory=list)


@dataclass
class Piece:
    id: int = 0
    name: str = ""
    in_layout: bool = True
    seam_allowance: bool = False
    seam_allowance_width: str = "1.0"
    united: bool = False
    nodes: list = field(default_factory=list)  # list[PieceNode]
    custom_sa: CustomSeamAllowance = field(default_factory=CustomSeamAllowance)
