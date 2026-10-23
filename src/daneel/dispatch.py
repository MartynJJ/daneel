"""Printer dispatch — send a sliced 3MF to the P1S over LAN and log the result.

Wraps ``bambulabs-api`` (MQTT for status/control, FTPS for upload). The
``[printer]`` section of the config supplies IP, serial and LAN access code.
:func:`watch` polls until the job reaches a terminal state and then appends a
record to the print log from the 3MF's slicer estimates and the observed
wall-clock time.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from daneel.config import PrinterConfig
from daneel.printlog import PrintLog, PrintRecord
from daneel.slice import read_3mf_estimates

# GcodeState names -> print-log status. Anything else is still in flight.
_TERMINAL = {"FINISH": "success", "FAILED": "failed"}
_IDLE = {"IDLE", "FINISH", "FAILED"}


class DispatchError(RuntimeError):
    """Connection, upload or start failure."""


@dataclass
class PrinterStatus:
    state: str  # GcodeState name: IDLE/PREPARE/RUNNING/PAUSE/FINISH/FAILED/UNKNOWN
    percent: int | None
    remaining_min: int | None
    bed_temp: float | None
    nozzle_temp: float | None
    file: str | None

    @property
    def busy(self) -> bool:
        return self.state not in _IDLE and self.state != "UNKNOWN"


class P1S:
    """Thin session wrapper over :class:`bambulabs_api.Printer`."""

    def __init__(self, config: PrinterConfig, *, connect_timeout: float = 15.0) -> None:
        try:
            from bambulabs_api import Printer
        except ImportError as exc:
            raise DispatchError('bambulabs-api missing: pip install -e ".[printer]"') from exc
        self._printer = Printer(config.ip, config.access_code, config.serial)
        self._timeout = connect_timeout

    def __enter__(self) -> P1S:
        self._printer.mqtt_start()
        time.sleep(2)
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            if self._printer.get_state().name != "UNKNOWN":
                return self
            time.sleep(0.5)
        self._printer.mqtt_stop()
        raise DispatchError(
            "no status from printer — check IP, serial, access code and that it is online"
        )

    def __exit__(self, *exc: object) -> None:
        self._printer.mqtt_stop()

    def status(self) -> PrinterStatus:
        p = self._printer

        def _int(v: object) -> int | None:
            return v if isinstance(v, int) else None

        return PrinterStatus(
            state=p.get_state().name,
            percent=_int(p.get_percentage()),
            remaining_min=_int(p.get_time()),
            bed_temp=p.get_bed_temperature(),
            nozzle_temp=p.get_nozzle_temperature(),
            file=p.get_file_name() or None,
        )

    def upload(self, path: Path) -> str:
        """FTPS-upload a 3MF; returns the filename on the printer."""
        with path.open("rb") as fh:
            reply = self._printer.upload_file(fh, path.name)
        if not reply or "226" not in reply:
            raise DispatchError(f"upload failed: {reply!r}")
        return path.name

    def start(self, remote_name: str, *, use_ams: bool = False, plate: int = 1) -> None:
        if not self._printer.start_print(remote_name, plate, use_ams=use_ams):
            raise DispatchError("printer rejected start_print")

    def stop(self) -> bool:
        return self._printer.stop_print()


def watch(
    session: P1S,
    path: Path,
    *,
    part: str | None = None,
    filament: str | None = None,
    log: PrintLog | None = None,
    poll_s: float = 10.0,
    start_timeout_s: float = 300.0,
    on_status: Callable[[PrinterStatus], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> PrintRecord:
    """Poll until the job finishes or fails, then append to the print log.

    The printer reports the previous job's FINISH until the new one starts, so
    we wait to see a non-terminal state first (bounded by ``start_timeout_s``).
    """
    t_wait = clock()
    seen_active = False
    t_start = clock()
    while True:
        st = session.status()
        if on_status:
            on_status(st)
        if st.state in ("PREPARE", "RUNNING", "PAUSE"):
            if not seen_active:
                seen_active, t_start = True, clock()
        elif seen_active and st.state in _TERMINAL:
            status = _TERMINAL[st.state]
            break
        elif not seen_active and clock() - t_wait > start_timeout_s:
            status = "failed"
            break
        sleep(poll_s)

    minutes, grams = read_3mf_estimates(path)
    elapsed = (clock() - t_start) / 60 if seen_active else None
    return (log or PrintLog()).add(
        label=path.stem,
        part=part,
        file=str(path),
        filament=filament,
        grams=grams if status == "success" else None,
        duration_min=round(elapsed, 1) if elapsed is not None else minutes,
        status=status,
        notes=None if seen_active else "print never started",
    )
