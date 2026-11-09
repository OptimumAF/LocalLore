"""Fixed installation and test on an already owned cold-navigation target.

An outer operation owns guest preparation, launch and teardown.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import re
import time

from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_cold_navigation_ui_client as client
from benchmarks import owned_cold_navigation_ui_contract as contract
from benchmarks import receipt_avd_environment as env

SECONDS = 1200
MAX_BOOT_POLLS = 61
MAX_CLIENTS = MAX_BOOT_POLLS + 25
SCOPE = "cold-navigation-controller-v1"
RESULT_FILE = "controller-result-v1.json"
TARGETS = (
    ("product_apk", contract.APP, "/data/local/tmp/locallore-product-v1.apk"),
    ("test_apk", contract.TEST, "/data/local/tmp/locallore-test-v1.apk"),
)
RESULT_KEYS = frozenset(("version", "scope", "admission", "running", "session", "caller",
                         "client_count", "clients", "journey", "outcome", "reason",
                         "observer_handles_closed", "feature_acceptance"))
_need = contract._need
_same = contract._same


def _line(raw):
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError:
        raise contract.TargetRefused("checks_failed") from None
    _need(len(lines) == 1, "checks_failed")
    return lines[0]


def _package_query(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def _uid(raw, package):
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError:
        raise contract.TargetRefused("checks_failed") from None
    values = {}
    _need(len(lines) <= 2, "checks_failed")
    for line in lines:
        match = re.fullmatch(r"package:([^\s]+) uid:([1-9][0-9]{0,9})", line)
        _need(match is not None and match[1] in (contract.APP, contract.TEST)
              and match[1] not in values, "checks_failed")
        values[match[1]] = int(match[2])
    uid = values.get(package)
    _need(uid is not None and all(10000 <= value <= 2147483647 for value in values.values()), "checks_failed")
    return uid


def _installed(command, artifacts):
    installed = {}
    for role, package, _ in TARGETS:
        uid = _uid(command(_package_query(package), "package"), package)
        line = _line(command(["cmd", "package", "path", "--user", "0", package], "package-path"))
        pattern = r"package:/data/app/(?:~~[A-Za-z0-9_=-]+/)?" + re.escape(package) + r"-[A-Za-z0-9_~=-]+/base\.apk"
        _need(re.fullmatch(pattern, line) is not None, "checks_failed")
        path = line[len("package:"):]
        digest = artifacts[role]["sha256"]
        _need(_line(command(["sha256sum", path], "package-hash")) == digest + "  " + path, "checks_failed")
        installed[role] = dict(package=package, uid=uid, path=path, sha256=digest)
    _need(len({row["uid"] for row in installed.values()}) == len(TARGETS), "checks_failed")
    return installed


def _journey(command, instrument, pause, artifacts):
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
        _need(_line(command(contract.PROFILE._install_argv(path), "install", seconds=120)) == "Success",
              "checks_failed")
    before = _installed(command, artifacts)
    result = instrument()
    _need(_same(before, _installed(command, artifacts)), "checks_failed")
    return {"installed": before, "test": result}


def _replay(output, count, trace, session_binding, admission):
    contract._int(count, 1, MAX_CLIENTS, "binding")
    _need(type(trace) is list and len(trace) == count, "binding")
    reader = client._REPLAY
    session = contract.validate_session(reader._json(session_binding), admission)
    rows = reader.require_current_clients(output, count, session_binding, admission)
    index = 0

    def consume(argv, label, source):
        nonlocal index
        _need(index < count, "binding")
        row, pin = rows[index], trace[index]
        expected = reader._pin(output / "clients" / f"command-{index + 1:04d}.json")
        _need(_same(pin, expected) and row["label"] == label
              and _same(row["operation"], {"argv": argv, "stdin": source}), "binding")
        index += 1
        return row, pin

    def command(argv, label, *, source=None, seconds=15):
        row, _ = consume(argv, label, source)
        if source is None:
            _need(reader._raw(row["stderr"], cap=131072) == b"", "checks_failed")
        return reader._raw(row["stdout"], cap=131072)

    def instrument():
        _, pin = consume(contract.instrumentation_argv(), contract.KIND, None)
        return {"client": pin, "instrumentation": client.replay_client_record(pin, session, admission)}

    result = _journey(command, instrument, lambda: None, admission["artifacts"])
    _need(index == count, "binding")
    return result


def _admission(admission_binding, running_binding):
    reader = client._REPLAY
    admission = contract.validate_admission(reader._json(admission_binding))
    contract.binding(running_binding)
    _need(running_binding["path"] == str(Path(admission["root"]) / "running-v1.json"), "binding")
    contract.validate_running(reader._json(running_binding), admission, admission_binding)
    return admission


def run(admission_binding, running_binding):
    """Consume an already running owned target and retain the attempt, even on refusal."""
    admission_binding, running_binding = copy.deepcopy(admission_binding), copy.deepcopy(running_binding)
    admission = _admission(admission_binding, running_binding)
    output = env.safe_path(Path(admission["root"]) / "controller-v1", exists=False)
    output.mkdir(exist_ok=False)
    identity = wire._identity(output)
    live = cap = None
    result = dict(version=1, scope=SCOPE, admission=admission_binding, running=running_binding,
                  session=None, caller=None, client_count=0, clients=[], journey=None,
                  outcome="refused", reason="checks_failed", observer_handles_closed=None,
                  feature_acceptance=False)
    try:
        live = client.LiveOwnedColdNavigationUiTarget(admission_binding, running_binding)
        cap = client.OwnedColdNavigationUiSdkCapture(output / "clients", SECONDS, live)
        result["caller"], result["session"] = live.caller, cap.session_binding

        def retain(action):
            previous = cap.count
            try:
                return action()
            finally:
                if cap.count == previous + 1:
                    path = cap.directory / f"command-{cap.count:04d}.json"
                    if os.path.lexists(path):
                        result["clients"].append(client._REPLAY._pin(path))

        def command(argv, label, *, source=None, seconds=15):
            if label == "boot":
                _need(time.monotonic() < boot_until, "deadline")
            if source is None:
                raw = retain(lambda: cap.shell(argv, label, seconds=seconds, full_budget=label == "install"))
            else:
                raw = retain(lambda: cap.stream(argv, source, label, seconds=seconds))
            _need(cap.count == len(result["clients"]) and cap.count > 0, "binding")
            row = client._REPLAY._json(result["clients"][-1])
            _need(row["client_qualified"] is True and row["label"] == label
                  and _same(row["operation"], {"argv": argv, "stdin": source})
                  and client._REPLAY._raw(row["stdout"], cap=131072) == raw, "binding")
            if source is None:
                _need(client._REPLAY._raw(row["stderr"], cap=131072) == b"", "checks_failed")
            if label == "boot":
                _need(time.monotonic() < boot_until, "deadline")
            return raw

        boot_until = time.monotonic() + 120

        def pause():
            _need(time.monotonic() + 2 < boot_until, "deadline")
            live.guard(min_seconds=2)
            time.sleep(2)

        journey = _journey(command, lambda: retain(cap.run_cold_navigation), pause, admission["artifacts"])
        _need(cap.clean and _same(journey, _replay(output, cap.count, result["clients"],
                                                  result["session"], admission)), "binding")
        result.update(journey=journey, outcome="completed", reason=None)
    except BaseException:
        # The create-only result retains the captured prefix for diagnosis.
        pass
    finally:
        if cap is not None:
            result["client_count"] = cap.count
            try:
                cap.close()
            except BaseException:
                result.update(outcome="refused", reason="resource_uncertain")
        if live is not None:
            try:
                closed = live.close()
                result["observer_handles_closed"] = closed if type(closed) is bool else None
            except BaseException:
                pass
            if result["observer_handles_closed"] is not True:
                result.update(outcome="refused", reason="resource_uncertain")
        _need(wire._identity(output) == identity, "binding")
        env.create_json(output / RESULT_FILE, result)
        _need(wire._identity(output) == identity, "binding")
    return result


def verify_controller_result(binding, admission_binding, running_binding, expected_caller):
    """Recheck a completed result against the outer operation's expected caller."""
    reader = client._REPLAY
    admission = _admission(admission_binding, running_binding)
    contract.verify_artifacts(admission["artifacts"])
    output = Path(admission["root"]) / "controller-v1"
    result = reader._at(binding, output / RESULT_FILE)
    contract._obj(result, RESULT_KEYS, "binding")
    contract._int(result["version"], 1, 1, "binding")
    _need(result["scope"] == SCOPE and result["outcome"] == "completed" and result["reason"] is None
          and result["observer_handles_closed"] is True and result["feature_acceptance"] is False,
          "binding")
    _need(_same(result["admission"], admission_binding) and _same(result["running"], running_binding)
          and _same(result["caller"], expected_caller), "binding")
    session_pin = reader._pin(output / contract.SESSION_FILE)
    _need(_same(result["session"], session_pin), "binding")
    session = contract.validate_session(reader._json(session_pin), admission)
    _need(_same(session["caller"], expected_caller) and _same(session["admission"], admission_binding)
          and _same(session["running"], running_binding), "binding")
    journey = _replay(output, result["client_count"], result["clients"], session_pin, admission)
    _need(_same(result["journey"], journey), "binding")
    return result
