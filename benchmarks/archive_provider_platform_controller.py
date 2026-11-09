"""Run and replay two archive provider tests on one already owned guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import re
import time

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import android_process_client_v4 as wire
from benchmarks import archive_provider_platform_binding as binding
from benchmarks import owned_archive_provider_platform as owned
from benchmarks import receipt_avd_environment as env

SECONDS = 1200
MAX_BOOT_POLLS = 61
COMMANDS_AFTER_BOOT = 32
SCOPE = "archive-provider-platform-controller-v1"
RESULT_FILE = "controller-result-v1.json"
TARGETS = (
    ("product_apk", binding.APP, "/data/local/tmp/locallore-product-v1.apk"),
    ("test_apk", binding.TEST, "/data/local/tmp/locallore-test-v1.apk"),
)
RESULT_KEYS = frozenset((
    "version", "scope", "admission", "running", "session", "caller", "client_count",
    "clients", "journey", "outcome", "reason", "observer_handles_closed",
    "feature_acceptance", "elapsed_ms",
))


def _line(raw):
    lines = raw.decode("ascii").splitlines()
    env.require(len(lines) == 1, "checks_failed")
    return lines[0]


def _package_query(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def _installed(command, artifacts):
    installed = {}
    observed_uids = {}
    for role, package, _ in TARGETS:
        uids = {}
        for line in command(_package_query(package), "package").decode("ascii").splitlines():
            match = re.fullmatch(r"package:([^\s]+) uid:([1-9][0-9]{0,9})", line)
            env.require(match is not None and match[1] in (binding.APP, binding.TEST)
                        and match[1] not in uids, "checks_failed")
            name, uid = match[1], int(match[2])
            env.require(10000 <= uid <= 2147483647
                        and observed_uids.setdefault(name, uid) == uid, "checks_failed")
            uids[name] = uid
        env.require(package in uids, "checks_failed")
        line = _line(command(["cmd", "package", "path", "--user", "0", package], "package-path"))
        pattern = (r"package:/data/app/(?:~~[A-Za-z0-9_=-]+/)?" + re.escape(package)
                   + r"-[A-Za-z0-9_~=-]+/base\.apk")
        env.require(re.fullmatch(pattern, line) is not None, "checks_failed")
        path = line[len("package:"):]
        digest = artifacts[role]["sha256"]
        env.require(_line(command(["sha256sum", path], "package-hash")) == digest + "  " + path,
                    "checks_failed")
        installed[role] = dict(package=package, uid=uids[package], path=path, sha256=digest)
    env.require(len({row["uid"] for row in installed.values()}) == len(TARGETS), "checks_failed")
    return installed


def _journey(command, pause, artifacts):
    for index in range(MAX_BOOT_POLLS):
        raw = command(["getprop", "sys.boot_completed"], "boot")
        state = "" if raw == b"" else _line(raw)
        env.require(state in ("", "0", "1"), "checks_failed")
        if state == "1":
            break
        env.require(index + 1 < MAX_BOOT_POLLS, "deadline")
        pause()
    for prop, expected in (("ro.build.version.sdk", "35"), ("ro.product.cpu.abi", "x86_64"),
                           ("ro.kernel.qemu", "1")):
        env.require(_line(command(["getprop", prop], "property")) == expected, "checks_failed")
    env.require(_line(command(["am", "get-current-user"], "user")) == "0", "checks_failed")
    for _, package, _ in TARGETS:
        env.require(command(_package_query(package), "package-absent") == b"", "packages_present")
    for role, _, path in TARGETS:
        source = artifacts[role]
        env.require(command(["dd", "of=" + path, "bs=65536"], "apk-stage",
                            source=source, seconds=120) == b"", "checks_failed")
        env.require(_line(command(["sha256sum", path], "staged-hash")) ==
                    source["sha256"] + "  " + path, "checks_failed")
        env.require(_line(command(["pm", "install", "-R", "-t", "--user", "0", path],
                                  "install", seconds=120)) == "Success", "checks_failed")
    before = _installed(command, artifacts)
    results = []
    for kind, _, _ in binding.INSTRUMENTATIONS:
        raw = command(binding.instrumentation_argv(kind), kind, seconds=90, limit=evidence.MAX_BYTES)
        result = binding.validate_result(kind, raw)
        env.require(owned._same(before, _installed(command, artifacts)), "checks_failed")
        results.append(dict(kind=kind, **result))
    return {"installed": before, "tests": results}


def _read_command(row, index, argv, label, source, seconds, limit):
    owned._int(row["index"], index, index, "binding")
    owned._int(row["effective_deadline_ms"], 1, seconds * 1000, "budget")
    env.require(row["label"] == label and owned._same(row["operation"], {"argv": argv, "stdin": source})
                and row["client_qualified"] is True and row["status"] == "completed"
                and owned._same(row["returncode"], 0), "checks_failed")
    if source is None:
        env.require(owned.REPLAY._raw(row["stderr"], cap=limit) == b"", "checks_failed")
    return owned.REPLAY._raw(row["stdout"], cap=limit)


def _replay(output, count, trace, session_binding, admission):
    owned._int(count, 1 + COMMANDS_AFTER_BOOT, MAX_BOOT_POLLS + COMMANDS_AFTER_BOOT, "binding")
    env.require(type(trace) is list and len(trace) == count, "binding")
    rows = owned.REPLAY.require_current_clients(output, count, session_binding, admission)
    env.require(type(rows) is list and len(rows) == count, "binding")
    index = 0

    def command(argv, label, *, source=None, seconds=15, limit=131072):
        nonlocal index
        env.require(index < count, "binding")
        expected = owned.REPLAY._pin(output / "clients" / f"command-{index + 1:04d}.json")
        env.require(owned._same(trace[index], expected), "binding")
        index += 1
        return _read_command(rows[index - 1], index, argv, label, source, seconds, limit)

    result = _journey(command, lambda: None, admission["artifacts"])
    env.require(index == count, "binding")
    return result


def _admission(admission_binding, running_binding):
    admission = owned.validate_admission(owned.REPLAY._json(admission_binding))
    running = owned.REPLAY._at(running_binding, Path(admission["root"]) / "running-v1.json")
    owned.validate_running(running, admission, admission_binding)
    return admission


def _remaining(deadline):
    seconds = deadline - time.monotonic()
    env.require(seconds > 0, "deadline")
    return seconds


def run(admission_binding, running_binding):
    """Capture one bounded journey on an independently owned target."""
    started = time.monotonic()
    until = started + SECONDS
    admission_binding, running_binding = copy.deepcopy(admission_binding), copy.deepcopy(running_binding)
    admission = _admission(admission_binding, running_binding)
    output = env.safe_path(Path(admission["root"]) / "controller-v1", exists=False)
    output.mkdir(exist_ok=False)
    identity = wire._identity(output)
    live = capture = None
    result = dict(version=1, scope=SCOPE, admission=admission_binding, running=running_binding,
                  session=None, caller=None, client_count=0, clients=[], journey=None,
                  outcome="refused", reason="checks_failed", observer_handles_closed=None,
                  feature_acceptance=False, elapsed_ms=None)
    try:
        live = owned.LiveOwnedArchiveProviderPlatformTarget(admission_binding, running_binding)
        capture = owned.OwnedArchiveProviderPlatformSdkCapture(output / "clients", SECONDS, live)
        result.update(session=capture.session_binding, caller=live.caller)
        until = min(until, capture.until)
        capture.until = until
        boot_until = min(until, time.monotonic() + 120)

        def command(argv, label, *, source=None, seconds=15, limit=131072):
            deadline = boot_until if label == "boot" else until
            budget = min(seconds, _remaining(deadline))
            previous = capture.count
            capture.until = deadline
            try:
                if source is None:
                    raw = capture.shell(argv, label, seconds=budget, cap=limit)
                else:
                    raw = capture.stream(argv, source, label, seconds=budget, cap=limit)
            finally:
                capture.until = until
                if capture.count == previous + 1:
                    path = capture.directory / f"command-{capture.count:04d}.json"
                    if os.path.lexists(path):
                        result["clients"].append(owned.REPLAY._pin(path))
            _remaining(deadline)
            env.require(capture.count == previous + 1 == len(result["clients"]), "binding")
            row = owned.REPLAY._json(result["clients"][-1])
            env.require(_read_command(row, capture.count, argv, label, source, seconds, limit) == raw, "binding")
            return raw

        def pause():
            live.guard(min_seconds=2)
            env.require(_remaining(boot_until) > 2, "deadline")
            time.sleep(2)

        journey = _journey(command, pause, admission["artifacts"])
        replayed = _replay(output, capture.count, result["clients"], result["session"], admission)
        env.require(capture.clean and owned._same(journey, replayed), "binding")
        binding.verify_artifacts(admission["artifacts"])
        owned.revalidate_inputs(admission)
        _remaining(until)
        result.update(journey=journey, outcome="completed", reason=None)
    except Exception as error:
        if isinstance(error, TimeoutError) or str(error) == "deadline":
            result["reason"] = "deadline"
    finally:
        if capture is not None:
            result["client_count"] = capture.count
            try:
                capture.close()
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
        env.require(wire._identity(output) == identity, "binding")
        env.create_json(output / RESULT_FILE, result)
        env.require(wire._identity(output) == identity, "binding")
    return result


def verify_controller_result(result_binding, admission_binding, running_binding, expected_caller):
    """Replay command evidence against the independently observed caller."""
    admission = _admission(admission_binding, running_binding)
    owned.revalidate_inputs(admission)
    binding.verify_artifacts(admission["artifacts"])
    output = Path(admission["root"]) / "controller-v1"
    result = owned.REPLAY._at(result_binding, output / RESULT_FILE)
    owned._obj(result, RESULT_KEYS, "binding")
    owned._int(result["version"], 1, 1, "binding")
    owned._int(result["elapsed_ms"], 0, SECONDS * 1000 - 1, "budget")
    env.require(result["scope"] == SCOPE and result["outcome"] == "completed" and result["reason"] is None
                and result["observer_handles_closed"] is True and result["feature_acceptance"] is False,
                "binding")
    env.require(owned._same(result["admission"], admission_binding)
                and owned._same(result["running"], running_binding)
                and owned._same(result["caller"], expected_caller), "binding")
    session_pin = owned.REPLAY._pin(output / owned.SESSION_FILE)
    env.require(owned._same(result["session"], session_pin), "binding")
    session = owned.validate_session(owned.REPLAY._json(session_pin), admission)
    env.require(owned._same(session["caller"], expected_caller)
                and owned._same(session["admission"], admission_binding)
                and owned._same(session["running"], running_binding)
                and owned._same(session["seconds"], SECONDS), "binding")
    journey = _replay(output, result["client_count"], result["clients"], session_pin, admission)
    env.require(owned._same(result["journey"], journey), "binding")
    return result
