"""Tests for printer dispatch (no hardware: fake session, fake clock)."""

from daneel import dispatch
from daneel.dispatch import PrinterStatus, watch
from daneel.printlog import PrintLog


def _st(state, pct=0):
    return PrinterStatus(state, pct, None, 25.0, 25.0, None)


class FakeSession:
    def __init__(self, states):
        self.states = list(states)

    def status(self):
        return self.states.pop(0) if len(self.states) > 1 else self.states[0]


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def _run(states, tmp_path, monkeypatch, **kw):
    monkeypatch.setattr(dispatch, "read_3mf_estimates", lambda p: (45.0, 12.5))
    clk = Clock()
    return watch(
        FakeSession(states),
        tmp_path / "cube.3mf",
        log=PrintLog(tmp_path / "log.jsonl"),
        poll_s=60,
        sleep=clk.sleep,
        clock=clk,
        **kw,
    )


def test_success_ignores_stale_finish(tmp_path, monkeypatch):
    states = [_st("FINISH"), _st("PREPARE"), _st("RUNNING", 50), _st("FINISH", 100)]
    rec = _run(states, tmp_path, monkeypatch, part="calib_cube")
    assert rec.status == "success" and rec.grams == 12.5 and rec.part == "calib_cube"
    assert rec.duration_min == 2.0


def test_failed_print_has_no_grams(tmp_path, monkeypatch):
    rec = _run([_st("RUNNING"), _st("FAILED")], tmp_path, monkeypatch)
    assert rec.status == "failed" and rec.grams is None


def test_never_started(tmp_path, monkeypatch):
    rec = _run([_st("FINISH")], tmp_path, monkeypatch, start_timeout_s=120)
    assert rec.status == "failed" and rec.notes == "print never started"


def test_busy_flag():
    assert _st("RUNNING").busy and not _st("FINISH").busy and not _st("UNKNOWN").busy
