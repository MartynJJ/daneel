"""Tests for the print log."""

import pytest

from daneel.printlog import PrintLog


def test_add_assigns_id_and_persists(tmp_path):
    log = PrintLog(tmp_path / "prints.jsonl")
    r1 = log.add(label="desk hook", grams=12.5, duration_min=45)
    r2 = log.add(label="bracket", status="failed")
    assert r1.id == "P0001" and r2.id == "P0002"
    assert r1.timestamp  # auto-stamped
    # Reloading from disk returns the same records.
    assert [r.id for r in PrintLog(tmp_path / "prints.jsonl").records()] == ["P0001", "P0002"]


def test_rejects_bad_status(tmp_path):
    with pytest.raises(ValueError):
        PrintLog(tmp_path / "prints.jsonl").add(label="x", status="done")


def test_summary(tmp_path):
    log = PrintLog(tmp_path / "prints.jsonl")
    log.add(label="a", status="success", grams=10, duration_min=30)
    log.add(label="b", status="failed", grams=5, duration_min=60)
    log.add(label="c", status="success", grams=20)
    s = log.summary()
    assert s["total"] == 3
    assert s["success_rate"] == pytest.approx(2 / 3)  # 2 of 3 completed succeeded
    assert s["total_grams"] == 35
    assert s["total_hours"] == pytest.approx(1.5)
    assert s["by_status"] == {"success": 2, "failed": 1}
