"""Prove Android boot before the fixed SDK24 story-deletion capture.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import time

from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env

DIRECTORY = "boot-readiness-v1"
SECONDS = 120
MAX_POLLS = 24
POLL_INTERVAL_SECONDS = 5
COMMAND_SECONDS = 15
REPLY_BYTES = 16
LABEL = "boot-ready"
ARGV = ("getprop", "sys.boot_completed")
_KEYS = ("session", "client_count", "completed_epoch")


class ReadinessCleanupError(RuntimeError):
    """A readiness capture could not be closed."""


def _remaining(until):
    seconds = until - time.monotonic()
    if not seconds > 0:
        raise TimeoutError("deadline")
    return seconds


def _is_ready(raw):
    if raw in (b"1", b"1\n", b"1\r\n"):
        return True
    core._need(raw in (b"", b"\n", b"\r\n", b"0", b"0\n", b"0\r\n"), "observation")
    return False


def _read_probe(row, index):
    core._int(row["index"], index, index, "binding")
    core._int(row["effective_deadline_ms"], 1, COMMAND_SECONDS * 1000, "budget")
    core._need(row["label"] == LABEL and row["client_qualified"] is True
               and row["status"] == "completed" and core._same(row["returncode"], 0)
               and core._same(row["operation"], {"argv": list(ARGV), "stdin": None}), "observation")
    core._need(owned.REPLAY._raw(row["stderr"], cap=REPLY_BYTES) == b"", "observation")
    return owned.REPLAY._raw(row["stdout"], cap=REPLY_BYTES)


def verify_readiness(output, readiness, admission_binding, running_binding, expected_caller):
    """Recheck every poll under the same admission, transport and observed caller."""
    core._obj(readiness, _KEYS, "binding")
    count = readiness["client_count"]
    core._int(count, 1, MAX_POLLS, "binding")
    admission = owned.validate_admission(owned.REPLAY._json(admission_binding))
    root = Path(admission["root"])
    core._need(output == root / "controller-v1", "binding")
    directory = output / DIRECTORY
    running = owned.validate_running(owned.REPLAY._at(running_binding, root / "running-v1.json"),
                                     admission, admission_binding)
    session_pin = readiness["session"]
    session = owned.validate_session(owned.REPLAY._at(session_pin, directory / owned.SESSION_FILE), admission)
    for field, expected in (("admission", admission_binding), ("running", running_binding),
                            ("caller", expected_caller), ("descriptor", running), ("seconds", SECONDS)):
        core._need(core._same(session[field], expected), "binding")
    completed = readiness["completed_epoch"]
    core._need(type(completed) in (int, float)
               and session["started_epoch"] <= completed < session["deadline_epoch"], "clock")
    rows = owned.REPLAY.require_current_clients(directory, count, session_pin, admission)
    core._need(type(rows) is list and len(rows) == count, "binding")
    for index, row in enumerate(rows, 1):
        core._need(_is_ready(_read_probe(row, index)) is (index == count), "observation")
    return readiness


def wait_for_android(output, live, admission_binding, running_binding, deadline):
    """Use only owned getprop calls, with a finite poll count and shared deadline."""
    until = min(deadline, time.monotonic() + SECONDS)
    _remaining(until)
    directory = env.safe_path(output / DIRECTORY, exists=False)
    directory.mkdir(exist_ok=False)
    cap = owned.OwnedCrossOwnerDeletionSdkCapture(directory / "clients", SECONDS, live)
    try:
        until = cap.until = min(until, cap.until)
        for index in range(1, MAX_POLLS + 1):
            budget = min(COMMAND_SECONDS, _remaining(until))
            raw = cap.shell(list(ARGV), LABEL, seconds=budget, cap=REPLY_BYTES)
            _remaining(until)
            core._need(cap.clean and cap.count == index, "binding")
            pin = owned.REPLAY._pin(cap.directory / f"command-{index:04d}.json")
            saved = _read_probe(owned.REPLAY._json(pin), index)
            core._need(saved == raw, "binding")
            if _is_ready(raw):
                readiness = dict(session=cap.session_binding, client_count=index, completed_epoch=time.time())
                verify_readiness(output, readiness, admission_binding, running_binding, live.caller)
                _remaining(until)
                return readiness
            if index < MAX_POLLS:
                time.sleep(min(POLL_INTERVAL_SECONDS, _remaining(until)))
        raise TimeoutError("deadline")
    finally:
        try:
            cap.close()
        except Exception:
            raise ReadinessCleanupError("resource_uncertain") from None
