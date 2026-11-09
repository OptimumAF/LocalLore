"""Run the fixed story-deletion test on an already owned emulator.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
import time

from benchmarks import android_process_client_v4 as wire
from benchmarks import cross_owner_deletion_ui_capture as capture
from benchmarks import cross_owner_deletion_ui_replay as journey
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env

SCOPE = "cross-owner-deletion-ui-controller-v1"
RESULT_FILE = "controller-result-v1.json"
RESULT_KEYS = (
    "version", "scope", "admission", "running", "session", "caller", "client_count",
    "journey", "outcome", "reason", "observer_handles_closed", "elapsed_ms",
)


def _remaining(until):
    seconds = until - time.monotonic()
    core._need(seconds > 0, "deadline")
    return seconds


def run(admission_binding, running_binding):
    """Run one finite capture. The enclosing owner remains responsible for shutdown."""
    started = time.monotonic()
    until = started + capture.SESSION_SECONDS
    admission_binding, running_binding = copy.deepcopy((admission_binding, running_binding))
    live = owned.LiveOwnedCrossOwnerDeletionTarget(admission_binding, running_binding)
    output = identity = cap = None
    result = dict(version=1, scope=SCOPE, admission=admission_binding, running=running_binding,
                  session=None, caller=None, client_count=0, journey=None, outcome="refused",
                  reason="checks_failed", observer_handles_closed=False, elapsed_ms=None)
    try:
        admission = live.admission
        candidate = env.safe_path(Path(admission["root"]) / "controller-v1", exists=False)
        candidate.mkdir(exist_ok=False)
        identity = wire._identity(candidate)
        output = candidate
        cap = owned.OwnedCrossOwnerDeletionSdkCapture(output / "clients", capture.SESSION_SECONDS, live)
        result.update(session=cap.session_binding, caller=live.caller)
        until = min(until, cap.until)

        def command(argv, label, *, source=None, limit=journey._MAX_REPLY):
            index = cap.count + 1
            core._int(index, 1, journey.COMMAND_COUNT, "binding")
            core._need(capture._LABELS[index - 1] == label, "capability")
            budget = min(capture._DEADLINES_MS.get(label, 15_000) / 1000, _remaining(until))
            if source is None:
                raw = cap.shell(argv, label, seconds=budget, cap=limit)
            else:
                raw = cap.stream(argv, source, label, seconds=budget, cap=limit)
            _remaining(until)
            core._need(cap.count == index, "binding")
            pin = owned.REPLAY._pin(cap.directory / f"command-{index:04d}.json")
            row = capture.read_command(owned.REPLAY, owned.REPLAY._json(pin), index, label)
            core._need(core._same(row["argv"], argv) and core._same(row["stdin"], source)
                       and row["stdout"] == raw and (source is not None or row["stderr"] == b""), "binding")
            return raw

        live_result = journey._journey(command, admission["artifacts"])
        core._need(cap.clean and cap.count == journey.COMMAND_COUNT, "binding")
        verified = owned.verify_capture(admission_binding, running_binding, result["session"], result["caller"])
        core._need(core._same(live_result, verified), "binding")
        _remaining(until)
        result.update(journey=verified, outcome="completed", reason=None)
    except Exception as error:
        if output is None:
            raise
        if isinstance(error, TimeoutError) or str(error) == "deadline":
            result["reason"] = "deadline"
    finally:
        if cap is not None:
            result["client_count"] = cap.count
            try:
                cap.close()
            except Exception:
                result.update(outcome="refused", reason="resource_uncertain")
        try:
            result["observer_handles_closed"] = live.close() is True
        except Exception:
            pass
        if not result["observer_handles_closed"]:
            result.update(outcome="refused", reason="resource_uncertain")
        result["elapsed_ms"] = int((time.monotonic() - started) * 1000)
        if result["outcome"] == "completed" and not 0 <= result["elapsed_ms"] < capture.SESSION_SECONDS * 1000:
            result.update(outcome="refused", reason="deadline")
        if output is not None:
            if result["outcome"] != "completed":
                result["journey"] = None
            core._need(wire._identity(output) == identity, "binding")
            env.create_json(output / RESULT_FILE, result)
            core._need(wire._identity(output) == identity, "binding")
    return result


def verify_controller_result(result_binding, admission_binding, running_binding, expected_caller):
    """Recheck the exact result and complete capture against an observed caller."""
    admission = owned.validate_admission(owned.REPLAY._json(admission_binding))
    output = Path(admission["root"]) / "controller-v1"
    result = owned.REPLAY._at(result_binding, output / RESULT_FILE)
    core._obj(result, RESULT_KEYS, "binding")
    core._int(result["version"], 1, 1, "binding")
    core._int(result["elapsed_ms"], 0, capture.SESSION_SECONDS * 1000 - 1, "budget")
    core._int(result["client_count"], journey.COMMAND_COUNT, journey.COMMAND_COUNT, "binding")
    core._need(result["scope"] == SCOPE and result["outcome"] == "completed"
               and result["reason"] is None and result["observer_handles_closed"] is True, "binding")
    session = owned.REPLAY._pin(output / owned.SESSION_FILE)
    for field, expected in (("admission", admission_binding), ("running", running_binding),
                            ("caller", expected_caller), ("session", session)):
        core._need(core._same(result[field], expected), "binding")
    replayed = owned.verify_capture(admission_binding, running_binding, session, expected_caller)
    core._need(core._same(result["journey"], replayed), "binding")
    env.check_binding(result_binding)
    return result
