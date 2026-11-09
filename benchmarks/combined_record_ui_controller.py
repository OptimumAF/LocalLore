"""Run and replay the fixed Story Record cohort on an already owned guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import re
import time

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import android_process_client_v4 as wire
from benchmarks import combined_record_ui_binding as binding
from benchmarks import owned_combined_record_ui_client as client
from benchmarks import owned_combined_record_ui_contract as contract
from benchmarks import receipt_avd_environment as env

SECONDS = 1200
MAX_BOOT_POLLS = 61
COMMANDS_AFTER_BOOT = 24 + len(binding.INSTRUMENTATIONS)
SCOPE = "combined-record-ui-controller-v1"
RESULT_FILE = "controller-result-v1.json"
TARGETS = (
    ("product_apk", binding.APP, "/data/local/tmp/locallore-product-v1.apk"),
    ("test_apk", binding.TEST, "/data/local/tmp/locallore-test-v1.apk"),
)
RESULT_KEYS = frozenset(("version", "scope", "admission", "running", "session", "caller",
                         "client_count", "clients", "journey", "outcome", "reason",
                         "observer_handles_closed", "feature_acceptance", "elapsed_ms"))
_need = env.require
_same = contract._same


def _line(raw):
    lines = raw.decode("ascii").splitlines()
    _need(len(lines) == 1, "checks_failed")
    return lines[0]


def _package_query(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def _uid(raw, package):
    values = {}
    lines = raw.decode("ascii").splitlines()
    _need(len(lines) <= len(TARGETS), "checks_failed")
    for line in lines:
        match = re.fullmatch(r"package:([^\s]+) uid:([1-9][0-9]{0,9})", line)
        _need(match is not None and match[1] in (binding.APP, binding.TEST)
              and match[1] not in values, "checks_failed")
        values[match[1]] = int(match[2])
    _need(package in values and all(10000 <= uid <= 2147483647 for uid in values.values()),
          "checks_failed")
    return values[package]


def _installed(command, artifacts):
    installed = {}
    for role, package, _ in TARGETS:
        uid = _uid(command(_package_query(package), "package"), package)
        line = _line(command(["cmd", "package", "path", "--user", "0", package], "package-path"))
        pattern = r"package:/data/app/(?:~~[A-Za-z0-9_=-]+/)?" + re.escape(package) + r"-[A-Za-z0-9_~=-]+/base\.apk"
        _need(re.fullmatch(pattern, line) is not None, "checks_failed")
        path = line[len("package:"):]
        digest = artifacts[role]["sha256"]
        _need(_line(command(["sha256sum", path], "package-hash")) == digest + "  " + path,
              "checks_failed")
        installed[role] = dict(package=package, uid=uid, path=path, sha256=digest)
    _need(len({row["uid"] for row in installed.values()}) == len(TARGETS), "checks_failed")
    return installed


def _journey(command, pause, artifacts):
    for index in range(MAX_BOOT_POLLS):
        raw = command(["getprop", "sys.boot_completed"], "boot")
        state = "" if raw == b"" else _line(raw)
        _need(state in ("", "0", "1"), "checks_failed")
        if state == "1":
            break
        _need(index + 1 < MAX_BOOT_POLLS, "deadline")
        pause()
    for prop, expected in (("ro.build.version.sdk", "35"), ("ro.product.cpu.abi", "x86_64"),
                           ("ro.kernel.qemu", "1")):
        _need(_line(command(["getprop", prop], "property")) == expected, "checks_failed")
    _need(_line(command(["am", "get-current-user"], "user")) == "0", "checks_failed")
    for _, package, _ in TARGETS:
        _need(command(_package_query(package), "package-absent") == b"", "packages_present")
    for role, _, path in TARGETS:
        source = artifacts[role]
        _need(command(["dd", "of=" + path, "bs=65536"], "apk-stage", source=source, seconds=120) == b"",
              "checks_failed")
        _need(_line(command(["sha256sum", path], "staged-hash")) == source["sha256"] + "  " + path,
              "checks_failed")
        _need(_line(command(["pm", "install", "-r", "-t", "--user", "0", path], "install", seconds=120))
              == "Success", "checks_failed")
    before = _installed(command, artifacts)
    results = []
    for kind, _, _ in binding.INSTRUMENTATIONS:
        raw = command(binding.instrumentation_argv(kind), kind, seconds=90, limit=evidence.MAX_BYTES)
        results.append(dict(kind=kind, **binding.validate_result(kind, raw)))
    _need(_same(before, _installed(command, artifacts)), "checks_failed")
    return {"installed": before, "tests": results}


def _check_command(row, index, argv, label, source, seconds):
    contract._int(row["index"], index, index, "binding")
    contract._int(row["effective_deadline_ms"], 1, seconds * 1000, "budget")
    _need(row["label"] == label and _same(row["operation"], {"argv": argv, "stdin": source})
          and row["client_qualified"] is True and row["status"] == "completed"
          and _same(row["returncode"], 0), "checks_failed")


def _replay(output, count, trace, session_binding, admission):
    contract._int(count, 1 + COMMANDS_AFTER_BOOT, MAX_BOOT_POLLS + COMMANDS_AFTER_BOOT, "binding")
    _need(type(trace) is list and len(trace) == count, "binding")
    reader = client.REPLAY
    rows = reader.require_current_clients(output, count, session_binding, admission)
    _need(type(rows) is list and len(rows) == count, "binding")
    index = 0

    def command(argv, label, *, source=None, seconds=15, limit=131072):
        nonlocal index
        _need(index < count, "binding")
        row = rows[index]
        expected = reader._pin(output / "clients" / f"command-{index + 1:04d}.json")
        _need(_same(trace[index], expected), "binding")
        index += 1
        _check_command(row, index, argv, label, source, seconds)
        if source is None:
            _need(reader._raw(row["stderr"], cap=limit) == b"", "checks_failed")
        return reader._raw(row["stdout"], cap=limit)

    result = _journey(command, lambda: None, admission["artifacts"])
    _need(index == count, "binding")
    return result


def _admission(admission_binding, running_binding):
    reader = client.REPLAY
    admission = contract.validate_admission(reader._json(admission_binding))
    running = reader._at(running_binding, Path(admission["root"]) / "running-v1.json")
    contract.validate_running(running, admission, admission_binding)
    return admission


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    _need(remaining > 0, "deadline")
    return remaining


def run(admission_binding, running_binding):
    """Consume an independently owned target under an outer process supervisor."""
    started = time.monotonic()
    until = started + SECONDS
    admission_binding, running_binding = copy.deepcopy(admission_binding), copy.deepcopy(running_binding)
    admission = _admission(admission_binding, running_binding)
    output = env.safe_path(Path(admission["root"]) / "controller-v1", exists=False)
    output.mkdir(exist_ok=False)
    identity = wire._identity(output)
    live = cap = None
    result = dict(version=1, scope=SCOPE, admission=admission_binding, running=running_binding,
                  session=None, caller=None, client_count=0, clients=[], journey=None,
                  outcome="refused", reason="checks_failed", observer_handles_closed=None,
                  feature_acceptance=False, elapsed_ms=None)
    reader = client.REPLAY
    try:
        live = client.LiveOwnedCombinedRecordUiTarget(admission_binding, running_binding)
        cap = client.OwnedCombinedRecordUiSdkCapture(output / "clients", SECONDS, live)
        result["caller"], result["session"] = live.caller, cap.session_binding
        until = min(until, cap.until)
        cap.until = until
        boot_until = min(until, time.monotonic() + 120)

        def command(argv, label, *, source=None, seconds=15, limit=131072):
            deadline = boot_until if label == "boot" else until
            budget = min(seconds, _remaining(deadline))
            previous = cap.count
            # Include pre-command proof work in the controller's absolute deadline.
            cap.until = deadline
            try:
                if source is None:
                    raw = cap.shell(argv, label, seconds=budget, cap=limit)
                else:
                    raw = cap.stream(argv, source, label, seconds=budget, cap=limit)
            finally:
                cap.until = until
                if cap.count == previous + 1:
                    path = cap.directory / f"command-{cap.count:04d}.json"
                    if os.path.lexists(path):
                        result["clients"].append(reader._pin(path))
            _remaining(deadline)
            _need(cap.count == previous + 1 == len(result["clients"]), "binding")
            row = reader._json(result["clients"][-1])
            _check_command(row, cap.count, argv, label, source, seconds)
            _need(reader._raw(row["stdout"], cap=limit) == raw, "binding")
            if source is None:
                _need(reader._raw(row["stderr"], cap=limit) == b"", "checks_failed")
            return raw

        def pause():
            live.guard(min_seconds=2)
            _need(_remaining(boot_until) > 2, "deadline")
            time.sleep(2)

        journey = _journey(command, pause, admission["artifacts"])
        _need(cap.clean and _same(journey, _replay(output, cap.count, result["clients"],
                                                  result["session"], admission)), "binding")
        binding.verify_artifacts(admission["artifacts"])
        contract.revalidate_inputs(admission)
        _remaining(until)
        result.update(journey=journey, outcome="completed", reason=None)
    except Exception as error:
        if isinstance(error, TimeoutError) or str(error) == "deadline":
            result["reason"] = "deadline"
    finally:
        if cap is not None:
            result["client_count"] = cap.count
            try:
                cap.close()
            except Exception:
                result.update(outcome="refused", reason="resource_uncertain")
        if live is not None:
            try:
                result["observer_handles_closed"] = live.close() is True
            except Exception:
                result["observer_handles_closed"] = False
            if result["observer_handles_closed"] is not True:
                result.update(outcome="refused", reason="resource_uncertain")
        result["elapsed_ms"] = int((time.monotonic() - started) * 1000)
        if result["outcome"] == "completed" and not 0 <= result["elapsed_ms"] < SECONDS * 1000:
            result.update(outcome="refused", reason="deadline")
        _need(wire._identity(output) == identity, "binding")
        env.create_json(output / RESULT_FILE, result)
        _need(wire._identity(output) == identity, "binding")
    return result


def verify_controller_result(result_binding, admission_binding, running_binding, expected_caller):
    """Replay a complete controller record with an independently observed caller."""
    reader = client.REPLAY
    admission = _admission(admission_binding, running_binding)
    contract.revalidate_inputs(admission)
    binding.verify_artifacts(admission["artifacts"])
    output = Path(admission["root"]) / "controller-v1"
    result = reader._at(result_binding, output / RESULT_FILE)
    contract._obj(result, RESULT_KEYS, "binding")
    contract._int(result["version"], 1, 1, "binding")
    contract._int(result["elapsed_ms"], 0, SECONDS * 1000 - 1, "budget")
    _need(result["scope"] == SCOPE and result["outcome"] == "completed" and result["reason"] is None
          and result["observer_handles_closed"] is True and result["feature_acceptance"] is False,
          "binding")
    _need(_same(result["admission"], admission_binding) and _same(result["running"], running_binding)
          and _same(result["caller"], expected_caller), "binding")
    session_pin = reader._pin(output / contract.SESSION_FILE)
    _need(_same(result["session"], session_pin), "binding")
    session = contract.validate_session(reader._json(session_pin), admission)
    _need(_same(session["caller"], expected_caller) and _same(session["admission"], admission_binding)
          and _same(session["running"], running_binding) and _same(session["seconds"], SECONDS),
          "binding")
    journey = _replay(output, result["client_count"], result["clients"], session_pin, admission)
    _need(_same(result["journey"], journey), "binding")
    return result
