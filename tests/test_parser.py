from pathlib import Path
from seamly2d.parser import ValParser, VitParser
from seamly2d.models.points import SinglePoint, EndLinePoint, AlongLinePoint, NormalPoint

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_val():
    pattern = ValParser().parse(FIXTURES / "simple_bodice.val")
    assert len(pattern.draws) == 1
    draw = pattern.draws[0]
    assert draw.name == "Bodice Front"
    assert len(draw.points) == 10
    assert len(pattern.pieces) == 1
    assert pattern.pieces[0].name == "Front Bodice"


def test_point_types():
    pattern = ValParser().parse(FIXTURES / "simple_bodice.val")
    draw = pattern.draws[0]
    types = {type(p).__name__ for p in draw.points}
    assert "SinglePoint" in types
    assert "EndLinePoint" in types
    assert "AlongLinePoint" in types
    assert "NormalPoint" in types


def test_parse_vit():
    ms = VitParser().parse(FIXTURES / "measurements.vit")
    assert ms.get("bust") == 88.0
    assert ms.get("waist") == 68.0
    assert ms.get("hip") == 96.0


def test_round_trip():
    from seamly2d.serializer import ValSerializer
    original = ValParser().parse(FIXTURES / "simple_bodice.val")
    xml = ValSerializer().serialize(original)
    reparsed = ValParser().parse_string(xml)
    assert len(reparsed.draws) == len(original.draws)
    assert len(reparsed.draws[0].points) == len(original.draws[0].points)
    assert len(reparsed.pieces) == len(original.pieces)
