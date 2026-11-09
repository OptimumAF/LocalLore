"""Install the fixed Story Record APK pair and verify one guarded UI journey.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import copy
from pathlib import Path
import re
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).parents[1]))

from benchmarks import adb_held_socket_probe as file_guard
from benchmarks import android_process_record_large_text_ui_verification as verification
from benchmarks import archive_ui_build as files
from benchmarks import owned_record_large_text_ui_contract as contract
from benchmarks import receipt_avd_environment as env
from benchmarks.android_instrumentation_evidence import MAX_BYTES, validate_instrumentation
from benchmarks.android_process_client_v4 import _identity
from benchmarks.android_process_record_large_text_ui_client import OwnedRecordLargeTextUiSdkCapture
from benchmarks.owned_record_large_text_ui_owner import LiveOwnedRecordLargeTextUiTarget

SECONDS = 1200
SCOPE = "record-large-text-ui-controller-v1"
REQUEST_SCOPE = "record-large-text-ui-controller-request-v1"
ROLES = ("product_apk", "test_apk")
PACKAGES = (contract.APP, contract.TEST)
STAGED = ("/data/local/tmp/locallore-product-v1.apk", "/data/local/tmp/locallore-test-v1.apk")
PROPERTIES = (("ro.build.version.sdk", "35"), ("ro.product.cpu.abi", "x86_64"), ("ro.kernel.qemu", "1"))
MAX_BOOT_POLLS = 61
COMMANDS_AFTER_BOOT = 25
RESULT_KEYS = frozenset(("version", "scope", "request", "session", "client_count", "outcome",
                         "reason", "trace", "observer_handles_closed", "feature_acceptance", "elapsed_ms"))
_need = env.require
_same = contract._same


def _raw(pin, limit):
    contract.binding(pin, max_bytes=limit)
    return files._bound(pin, cap=limit)


def _json(pin):
    return env.decode_json(_raw(pin, 2 * 1024 * 1024))


def _at(pin, path):
    _need(type(pin) is dict and pin.get("path") == str(path), "binding")
    return _json(pin)


def _inputs(admission_binding, running_binding):
    admission = contract.validate_admission(_json(admission_binding))
    contract.validate_running(_json(running_binding), admission, admission_binding)
    contract.revalidate_inputs(admission)
    contract.verify_current(admission)
    return admission


def _request(output, admission, admission_binding, running_binding, caller):
    return dict(version=1, scope=REQUEST_SCOPE, admission=admission_binding, running=running_binding,
                build=admission["artifacts"]["build"], root=str(output),
                controller=env.binding(Path(__file__).resolve()),
                sources=admission["sources"], python=admission["python"], caller=caller, seconds=SECONDS)


def _session(output, pin, admission, admission_binding, running_binding, caller):
    session = contract.validate_session(_at(pin, output / contract.SESSION_FILE), admission)
    _need(_same(session["admission"], admission_binding)
          and _same(session["running"], running_binding)
          and _same(session["descriptor"], _json(running_binding))
          and _same(session["caller"], caller)
          and session["root"] == str(output) and session["seconds"] == SECONDS, "binding")


def _write(output, identity, name, value):
    _need(_identity(output) == identity, "binding")
    env.create_json(output / name, value)
    pin = env.binding(output / name)
    _need(_identity(output) == identity, "binding")
    return pin


def _lines(raw):
    text = raw.decode("ascii").replace("\r\n", "\n")
    _need(all(char == "\n" or 32 <= ord(char) <= 126 for char in text), "output")
    return text.splitlines()


def _line(raw):
    lines = _lines(raw)
    _need(len(lines) == 1, "output")
    return lines[0]


def _package_query(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def _uid(raw, package):
    values = {}
    lines = _lines(raw)
    _need(len(lines) <= 2, "package")
    for line in lines:
        match = re.fullmatch(r"package:([^\s]+) uid:([1-9][0-9]{0,9})", line)
        _need(match is not None and match[1] in PACKAGES and package in match[1]
              and match[1] not in values, "package")
        value = int(match[2])
        _need(10000 <= value <= 2147483647, "package")
        values[match[1]] = value
    return values.get(package)


def _apk_path(raw):
    line = _line(raw)
    _need(re.fullmatch(r"package:/data/app/[A-Za-z0-9_~=/.-]+/base\.apk", line) is not None, "package")
    path = line[len("package:"):]
    _need(all(part not in ("", ".", "..") for part in path.split("/")[1:]), "package")
    return path


def _check_hash(raw, path, artifact):
    _need(_line(raw) == artifact["sha256"] + "  " + path, "artifact")


def _installed(command, artifacts):
    packages = {}
    for role, package in zip(ROLES, PACKAGES):
        uid = _uid(command(_package_query(package), "package"), package)
        _need(uid is not None, "package")
        path = _apk_path(command(["cmd", "package", "path", "--user", "0", package], "package-path"))
        _check_hash(command(["sha256sum", path], "package-hash"), path, artifacts[role])
        packages[role] = dict(package=package, uid=uid, path=path)
    _need(len({row["uid"] for row in packages.values()}) == 2
          and len({row["path"] for row in packages.values()}) == 2, "package")
    return packages


def _exercise(command, artifacts, wait_boot):
    """Run or replay the only supported command sequence."""
    for attempt in range(MAX_BOOT_POLLS):
        raw = command(["getprop", "sys.boot_completed"], "boot")
        boot = "" if raw == b"" else _line(raw)
        if boot == "1":
            break
        _need(boot in ("", "0") and attempt + 1 < MAX_BOOT_POLLS, "boot")
        wait_boot()
    for prop, expected in PROPERTIES:
        _need(_line(command(["getprop", prop], "property")) == expected, "device")
    _need(_line(command(["am", "get-current-user"], "user")) == "0", "user")
    for package in PACKAGES:
        _need(command(_package_query(package), "package-absent") == b"", "package")
    for role, path in zip(ROLES, STAGED):
        source = artifacts[role]
        _need(command(["dd", "of=" + path, "bs=65536"], "apk-stage",
                      seconds=120, source=source) == b"", "artifact")
        _check_hash(command(["sha256sum", path], "staged-hash"), path, source)
        _need(_line(command(["pm", "install", "-r", "-t", "--user", "0", path],
                            "install", seconds=120)) == "Success", "install")
    before = _installed(command, artifacts)
    (kind, klass, method), = contract.INSTRUMENTATIONS
    raw = command(["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
                   contract.TEST + "/androidx.test.runner.AndroidJUnitRunner"],
                  kind, seconds=90, limit=MAX_BYTES)
    evidence = validate_instrumentation(raw, klass, [method])
    _need(_same(before, _installed(command, artifacts)), "package")
    return dict(installed=before, instrumentation=evidence)


def _command_output(row, index, argv, label, source, seconds, limit):
    _need(type(row["index"]) is int and row["index"] == index and row["label"] == label
          and _same(row["operation"], dict(argv=argv, stdin=source))
          and row["client_qualified"] is True and row["status"] == "completed"
          and type(row["returncode"]) is int and row["returncode"] == 0
          and type(row["effective_deadline_ms"]) is int
          and 0 < row["effective_deadline_ms"] <= seconds * 1000, "command")
    stdout, stderr = _raw(row["stdout"], limit), _raw(row["stderr"], limit)
    _need(len(stdout) + len(stderr) <= limit and (source is not None or stderr == b""), "capture")
    return stdout


def _replay(output, count, session, admission):
    contract._int(count, COMMANDS_AFTER_BOOT + 1, COMMANDS_AFTER_BOOT + MAX_BOOT_POLLS, "binding")
    rows = verification.require_current_clients(output, count, session, admission)
    _need(type(rows) is list and len(rows) == count, "binding")
    index = 0

    def consume(argv, label, *, seconds=15, source=None, limit=131072):
        nonlocal index
        _need(index < count, "binding")
        row = rows[index]
        index += 1
        return _command_output(row, index, argv, label, source, seconds, limit)

    trace = _exercise(consume, admission["artifacts"], lambda: None)
    _need(index == count, "binding")
    return trace


def _closed_roster(output, *, result=True):
    expected = {"request-v1.json", contract.SESSION_FILE, "clients", "proofs"}
    if result:
        expected.add("controller-result-v1.json")
    _need({path.name for path in output.iterdir()} == expected, "binding")


def _reason(error):
    if isinstance(error, KeyboardInterrupt):
        return "cancelled"
    if isinstance(error, TimeoutError) or (type(error) is env.EnvironmentRefused and error.args == ("deadline",)):
        return "deadline"
    return "checks_failed"


def run(admission_binding, running_binding):
    """Drive an existing owned target, then recheck and retain its evidence."""
    begin = time.monotonic()
    deadline = begin + SECONDS
    admission = _inputs(admission_binding, running_binding)
    output = env.safe_path(Path(admission["root"]) / "controller-v1", exists=False)
    output.mkdir()
    identity = _identity(output)
    live = cap = request_pin = session_pin = trace = observer_closed = None
    request = caller = None
    clean = True
    reason = None
    try:
        _need(time.monotonic() < deadline, "deadline")
        live = LiveOwnedRecordLargeTextUiTarget(admission_binding, running_binding)
        caller = copy.deepcopy(live.caller)
        request = _request(output, admission, admission_binding, running_binding, caller)
        request_pin = _write(output, identity, "request-v1.json", request)
        cap = OwnedRecordLargeTextUiSdkCapture(output / "clients", SECONDS, live)
        session_pin = cap.session_binding
        _session(output, session_pin, admission, admission_binding, running_binding, caller)
        boot_deadline = min(deadline, time.monotonic() + 120)

        def dispatch(argv, label, *, seconds=15, source=None, limit=131072):
            _need(_identity(output) == identity, "binding")
            live.guard()
            until = boot_deadline if label == "boot" else deadline
            budget = min(seconds, until - time.monotonic())
            _need(budget > 0, "deadline")
            previous = cap.count
            if source is None:
                raw = cap.shell(argv, label, seconds=budget, cap=limit)
            else:
                raw = cap.stream(argv, source, label, seconds=budget, cap=limit)
            _need(type(cap.count) is int and cap.count == previous + 1, "command")
            stem = output / "clients" / ("command-%04d" % cap.count)
            row = env.decode_json(files._read(stem.with_suffix(".json"), 2 * 1024 * 1024))
            for channel in ("stdout", "stderr"):
                _need(row[channel]["path"] == str(stem.with_suffix("." + channel + ".bin")), "binding")
            _need(_command_output(row, cap.count, argv, label, source, seconds, limit) == raw, "capture")
            _need(_identity(output) == identity, "binding")
            live.guard()
            _need(time.monotonic() < until, "deadline")
            return raw

        def wait_boot():
            _need(time.monotonic() + 2 < boot_deadline, "deadline")
            time.sleep(2)

        trace = _exercise(dispatch, admission["artifacts"], wait_boot)
    except BaseException as error:
        reason = _reason(error)
    finally:
        count = 0 if cap is None else cap.count
        if cap is not None:
            try:
                clean = cap.clean is True
                clean = cap.close() is None and clean
            except BaseException:
                clean = False
        if live is not None:
            try:
                observed = live.close()
                observer_closed = observed if type(observed) is bool else None
            except BaseException:
                observer_closed = None
            clean = observer_closed is True and clean
        if not clean:
            reason = "resource_uncertain"

    if reason is None:
        try:
            _need(trace is not None and observer_closed is True, "cleanup")
            _need(_same(_inputs(admission_binding, running_binding), admission), "binding")
            _session(output, session_pin, admission, admission_binding, running_binding, caller)
            _closed_roster(output, result=False)
            _need(time.monotonic() < deadline, "deadline")
            _need(_same(_replay(output, count, session_pin, admission), trace), "binding")
            _need(_same(_at(request_pin, output / "request-v1.json"), request)
                  and _same(_request(output, admission, admission_binding, running_binding, caller), request)
                  and _same(_inputs(admission_binding, running_binding), admission), "binding")
            _closed_roster(output, result=False)
            _need(time.monotonic() < deadline, "deadline")
        except BaseException as error:
            reason = _reason(error)

    result = dict(version=1, scope=SCOPE, request=request_pin, session=session_pin,
                  client_count=count, outcome="completed" if reason is None else "refused",
                  reason=reason, trace=trace, observer_handles_closed=observer_closed,
                  feature_acceptance=False, elapsed_ms=round(max(0, time.monotonic() - begin) * 1000))
    _write(output, identity, "controller-result-v1.json", result)
    return copy.deepcopy(result)


def verify_controller_result(result_binding, admission_binding, running_binding, expected_caller):
    """Verify the entire command and proof roster against independent owner inputs."""
    admission = _inputs(admission_binding, running_binding)
    output = env.safe_path(Path(admission["root"]) / "controller-v1", directory=True)
    identity = _identity(output)
    _closed_roster(output)
    result = _at(result_binding, output / "controller-result-v1.json")
    contract._obj(result, RESULT_KEYS, "binding")
    contract._int(result["version"], 1, 1, "binding")
    contract._int(result["elapsed_ms"], 0, SECONDS * 1000, "deadline")
    _need(result["scope"] == SCOPE and result["outcome"] == "completed" and result["reason"] is None
          and result["observer_handles_closed"] is True and result["feature_acceptance"] is False, "binding")
    request = _at(result["request"], output / "request-v1.json")
    _need(_same(request, _request(output, admission, admission_binding, running_binding, expected_caller)), "binding")
    _session(output, result["session"], admission, admission_binding, running_binding, expected_caller)
    trace = _replay(output, result["client_count"], result["session"], admission)
    _need(_same(trace, result["trace"]) and _same(_inputs(admission_binding, running_binding), admission)
          and _same(_at(result["request"], output / "request-v1.json"), request)
          and _same(_at(result_binding, output / "controller-result-v1.json"), result), "binding")
    _closed_roster(output)
    _need(_identity(output) == identity, "binding")
    return copy.deepcopy(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admission", required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--running", required=True)
    parser.add_argument("--running-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        pins = []
        for path, digest in ((args.admission, args.admission_sha256), (args.running, args.running_sha256)):
            pin, _ = file_guard._read_bound(
                file_guard._existing_D_file(path, "binding"), digest, 2 * 1024 * 1024, "binding")
            pins.append(pin)
        return 0 if run(*pins)["outcome"] == "completed" else 1
    except (env.EnvironmentRefused, OSError, ValueError, KeyError, TypeError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
