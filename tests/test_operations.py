from pathlib import Path
from seamly2d.parser import ValParser, VitParser
from seamly2d.operations import (
    AddPocketOpening, ModifyDart, AddDart, UpdateMeasurement, SetSeamAllowance
)
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load():
    p = ValParser().parse(FIXTURES / "simple_bodice.val")
    p.measurements = VitParser().parse(FIXTURES / "measurements.vit")
    return p


def test_add_pocket():
    pattern = load()
    orig_count = sum(len(d.points) for d in pattern.draws)
    result = AddPocketOpening("Bodice Front", "A4", "A5").apply(pattern)
    assert result.success
    assert len(result.changed_ids) == 2
    new_count = sum(len(d.points) for d in result.pattern.draws)
    assert new_count == orig_count + 2


def test_modify_dart():
    pattern = load()
    result = ModifyDart("Bodice Front", "D1", "(bust-waist)/6").apply(pattern)
    assert result.success
    # D2 and D3 should have updated length
    for draw in result.pattern.draws:
        for pt in draw.points:
            if pt.id in result.changed_ids:
                assert pt.length == "(bust-waist)/6"


def test_update_measurement():
    pattern = load()
    result = UpdateMeasurement("bust", 96.0).apply(pattern)
    assert result.success
    assert result.pattern.measurements.get("bust") == 96.0
    # Original unchanged
    assert pattern.measurements.get("bust") == 88.0


def test_set_seam_allowance():
    pattern = load()
    result = SetSeamAllowance("Front Bodice", 1.5).apply(pattern)
    assert result.success
    piece = result.pattern.pieces[0]
    assert piece.seam_allowance is True
    assert piece.seam_allowance_width == "1.5"


def test_add_dart():
    pattern = load()
    orig_count = sum(len(d.points) for d in pattern.draws)
    result = AddDart("Bodice Front", "A4", "A5").apply(pattern)
    assert result.success
    assert len(result.changed_ids) == 4
    new_count = sum(len(d.points) for d in result.pattern.draws)
    assert new_count == orig_count + 4


def test_operation_errors():
    from seamly2d.exceptions import OperationError
    pattern = load()
    with pytest.raises(OperationError):
        ModifyDart("Bodice Front", "NONEXISTENT", "1").apply(pattern)
    with pytest.raises(OperationError):
        ModifyDart("NODRAW", "A", "1").apply(pattern)
