"""One fixed model-free presentation process restoration case on an independently owned guest.

Importing this module performs no target, process or filesystem observation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import copy
import os
from pathlib import Path
import re
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).parents[1]))

from benchmarks import receipt_avd_environment as env
from benchmarks import owned_presentation_process_contract as contract
from benchmarks.owned_presentation_process_owner import LiveOwnedPresentationProcessTarget
from benchmarks.android_process_presentation_process_client import OwnedPresentationProcessSdkCapture
from benchmarks import android_process_presentation_process_verification as verification
from benchmarks.presentation_process_build import verify_current
from benchmarks.android_presentation_process_evidence import validate_result
from benchmarks import android_process_client_v4 as directory_checks

MAX_BYTES = 131072
FRAME_CAP = 32768
PROBE_CAP = 4096

SECONDS = 1200
SCOPE = "presentation-process-controller-v1"
REQUEST_SCOPE = "presentation-process-controller-request-v1"
SETUP_SCOPE = "presentation-process-controller-setup-v1"
INSTALLED_SCOPE = "presentation-process-controller-installed-v1"
ROLES = ("product_apk", "test_apk", "controller_apk")
STAGED = ("/data/local/tmp/locallore-product-v1.apk", "/data/local/tmp/locallore-test-v1.apk",
          "/data/local/tmp/locallore-presentation-controller-v1.apk")
RESULT_KEYS = frozenset(("version", "scope", "request", "session", "setup", "installed_before", "execution", "product_records", "evidence",
                         "installed_after", "client_count", "outcome", "phase", "reason",
                         "observer_handles_closed", "feature_acceptance", "elapsed_ms"))
REQUEST_KEYS = frozenset(("version", "scope", "admission", "running", "build", "root", "controller",
                          "sources", "python", "caller", "seconds"))


def _need(condition, reason="checks_failed"):
    env.require(condition, reason)


def _object(value, keys):
    _need(type(value) is dict and set(value) == set(keys))


def _same(left, right):
    # JSON values such as true and 1 must not alias in closed provenance joins.
    return env.encoded(left) == env.encoded(right)


def _pin(value, limit=64 * 1024 * 1024):
    contract.binding(value, max_bytes=limit)
    env.check_binding(value)
    return value


def _raw(value, limit=2 * 1024 * 1024):
    _pin(value, limit)
    with env.safe_path(Path(value["path"]), exists=True).open("rb") as stream:
        raw = stream.read(value["bytes"] + 1)
    _pin(value, limit)
    _need(len(raw) == value["bytes"])
    return raw


def _json(value):
    return env.decode_json(_raw(value, 2 * 1024 * 1024))


def _at(value, path):
    _need(type(value) is dict and Path(value.get("path", "")) == path)
    return _json(value)


def _output(admission):
    return env.safe_path(Path(admission["root"]) / "controller-v1", exists=False)


def _directory_identity(path):
    env.safe_path(path, exists=True, directory=True)
    return directory_checks._identity(path)


def _write(output, identity, name, value):
    _need(_directory_identity(output) == identity)
    env.create_json(output / name, value)
    _need(_directory_identity(output) == identity)
    return env.binding(output / name)


def _inputs(admission_binding, running_binding):
    admission = contract.validate_admission(_json(admission_binding))
    contract.validate_running(_json(running_binding), admission, admission_binding)
    contract.revalidate_inputs(admission)
    _need(_same(contract.source_bindings(), admission["sources"]))
    manifest = verify_current(admission)
    _object(manifest, ("version", "scope", "product_source", "public_execution", "apks"))
    apks = manifest["apks"]
    _object(apks, ROLES)
    for role, package in zip(ROLES, (contract.APP, contract.TEST, contract.CONTROLLER)):
        _object(apks[role], ("binding", "package", "certificate_sha256"))
        _need(_same(apks[role]["binding"], admission["artifacts"][role]) and apks[role]["package"] == package)
        _need(type(apks[role]["certificate_sha256"]) is str and
              re.fullmatch("[0-9a-f]{64}", apks[role]["certificate_sha256"]) is not None)
    _need(len({apks[role]["certificate_sha256"] for role in ROLES}) == 1)
    return admission, manifest


def _line(raw):
    lines = raw.decode("ascii").splitlines()
    _need(len(lines) == 1)
    return lines[0]


def _boot_value(raw):
    # sys.boot_completed can be unset while a fresh guest is still booting.
    return "" if raw == b"" else _line(raw)


def _uid(raw, package):
    _need(package in (contract.APP, contract.TEST, contract.CONTROLLER))
    values = {}
    lines = raw.decode("ascii").splitlines()
    _need(len(lines) <= 3)
    for line in lines:
        match = re.fullmatch(r"package:([^\s]+) uid:([1-9][0-9]*)", line)
        _need(match is not None and match[1] in (contract.APP, contract.TEST, contract.CONTROLLER) and
              package in match[1] and match[1] not in values)
        value = int(match[2])
        _need(10000 <= value <= 99999)
        values[match[1]] = value
    return values.get(package)


def _apk_path(raw, package):
    _need(package in (contract.APP, contract.TEST, contract.CONTROLLER))
    line = _line(raw)
    match = re.fullmatch(r"package:(/data/app/(?:~~[A-Za-z0-9_=-]+/)?" + re.escape(package) +
                         r"-[A-Za-z0-9_~=-]+/base\.apk)", line)
    _need(match is not None)
    return match[1]


def _record(cap, previous):
    _need(type(cap.count) is int and cap.count == previous + 1)
    return env.binding(cap.directory / ("command-%04d.json" % cap.count))


def _known_attempt(cap, previous):
    if type(cap.count) is int and cap.count == previous + 1:
        path = cap.directory / ("command-%04d.json" % cap.count)
        if os.path.lexists(path):
            return env.binding(path)
    return None


def _command(cap, live, until, argv, label, *, seconds=15, source=None, limit=131072):
    _need(time.monotonic() < until, "deadline")
    live.guard()
    previous = cap.count
    if source is None:
        raw = cap.shell(argv, label, seconds=seconds, cap=limit)
    else:
        raw = cap.stream(argv, source, label, seconds=seconds, cap=limit)
    pin = _record(cap, previous)
    record = _json(pin)
    _need(record["client_qualified"] is True and record["status"] == "completed" and
          type(record["returncode"]) is int and record["returncode"] == 0)
    _need(_raw(record["stdout"], limit) == raw)
    if source is None:
        _need(_raw(record["stderr"], limit) == b"")
    live.guard()
    _need(time.monotonic() < until, "deadline")
    return raw, pin


def _installed(cap, live, until, manifest):
    packages = {}
    for role in ROLES:
        apk = manifest["apks"][role]
        package = apk["package"]
        raw, uid_pin = _command(cap, live, until,
            ["cmd", "package", "list", "packages", "-U", "--user", "0", package], "package")
        uid = _uid(raw, package)
        _need(uid is not None)
        raw, path_pin = _command(cap, live, until,
            ["cmd", "package", "path", "--user", "0", package], "package-path")
        path = _apk_path(raw, package)
        raw, hash_pin = _command(cap, live, until, ["sha256sum", path], "package-hash")
        _need(_line(raw) == apk["binding"]["sha256"] + "  " + path)
        packages[role] = dict(package=package, uid=uid, path=path,
                              checks=dict(uid=uid_pin, path=path_pin, sha256=hash_pin))
    _need(len({v["uid"] for v in packages.values()}) == 3)
    return packages


def _same_installed(before, after):
    return all({k: before[role][k] for k in ("package", "uid", "path")} ==
               {k: after[role][k] for k in ("package", "uid", "path")} for role in ROLES)


def _expected(admission, manifest, installed):
    return dict(run_id=contract.controller_run_id(admission), product_sha256=admission["artifacts"]["product_apk"]["sha256"],
                product_uid=installed["product_apk"]["uid"], controller_uid=installed["controller_apk"]["uid"],
                signature_sha256=manifest["apks"]["product_apk"]["certificate_sha256"])


def run(admission_binding, running_binding):
    """The caller owns finite process supervision and the actual worker receipt."""
    begin = time.monotonic()
    admission = contract.validate_admission(_json(admission_binding))
    output = _output(admission)
    output.mkdir()
    identity = _directory_identity(output)
    request_pin = session_pin = setup_pin = before_pin = after_pin = None
    live = cap = None
    phase, outcome, reason = "admission", "refused", "checks_failed"
    observer_closed = None
    execution = dict(kind=contract.CLAIM_KIND, case=contract.CASE, record=None)
    product_records = dict.fromkeys(("created", "saved", "commands"))
    evidence_pin = None
    setup = dict(version=1, scope=SETUP_SCOPE, session=None, boot=[],
                 properties=dict(api=None, abi=None, qemu=None), user=None,
                 packages_absent={role: None for role in ROLES},
                 staged={role: dict(transfer=None, sha256=None) for role in ROLES},
                 installs={role: None for role in ROLES})
    try:
        admission, manifest = _inputs(admission_binding, running_binding)
        live = LiveOwnedPresentationProcessTarget(admission_binding, running_binding)
        _need(type(live) is LiveOwnedPresentationProcessTarget)
        request = dict(version=1, scope=REQUEST_SCOPE, admission=copy.deepcopy(admission_binding),
                       running=copy.deepcopy(running_binding), build=copy.deepcopy(admission["artifacts"]["build"]),
                       root=str(output), controller=env.binding(Path(__file__).resolve()),
                       sources=copy.deepcopy(admission["sources"]), python=copy.deepcopy(admission["python"]),
                       caller=copy.deepcopy(live.caller), seconds=SECONDS)
        request_pin = _write(output, identity, "request-v1.json", request)
        cap = OwnedPresentationProcessSdkCapture(output / "clients", SECONDS, live)
        _need(type(cap) is OwnedPresentationProcessSdkCapture)
        session_pin = cap.session_binding
        setup["session"] = copy.deepcopy(session_pin)
        until = begin + SECONDS
        phase = "setup"
        boot_until = min(until, time.monotonic() + 120)
        while True:
            previous = cap.count
            try:
                raw, _ = _command(cap, live, boot_until, ["getprop", "sys.boot_completed"], "boot")
            finally:
                pin = _known_attempt(cap, previous)
                if pin is not None:
                    setup["boot"].append(pin)
            value = _boot_value(raw)
            _need(value in ("", "0", "1"))
            if value == "1":
                break
            _need(time.monotonic() + 2 < boot_until, "deadline")
            time.sleep(2)
        for key, prop, expected in (("api", "ro.build.version.sdk", "35"),
                                    ("abi", "ro.product.cpu.abi", "x86_64"),
                                    ("qemu", "ro.kernel.qemu", "1")):
            previous = cap.count
            try:
                raw, _ = _command(cap, live, until, ["getprop", prop], "property")
            finally:
                setup["properties"][key] = _known_attempt(cap, previous)
            _need(_line(raw) == expected)
        previous = cap.count
        try:
            raw, _ = _command(cap, live, until, ["am", "get-current-user"], "user")
        finally:
            setup["user"] = _known_attempt(cap, previous)
        _need(_line(raw) == "0")
        for role in ROLES:
            package = manifest["apks"][role]["package"]
            previous = cap.count
            try:
                raw, _ = _command(cap, live, until,
                    ["cmd", "package", "list", "packages", "-U", "--user", "0", package], "package-absent")
            finally:
                setup["packages_absent"][role] = _known_attempt(cap, previous)
            _need(_uid(raw, package) is None)
        phase = "install"
        for role, path in zip(ROLES, STAGED):
            source = admission["artifacts"][role]
            previous = cap.count
            try:
                raw, _ = _command(cap, live, until, ["dd", "of=" + path, "bs=65536"],
                                   "apk-stage", source=source, seconds=120)
            finally:
                setup["staged"][role]["transfer"] = _known_attempt(cap, previous)
            _need(raw == b"")
            previous = cap.count
            try:
                raw, _ = _command(cap, live, until, ["sha256sum", path], "staged-hash")
            finally:
                setup["staged"][role]["sha256"] = _known_attempt(cap, previous)
            _need(_line(raw) == source["sha256"] + "  " + path)
            previous = cap.count
            try:
                raw, _ = _command(cap, live, until, ["pm", "install", "-r", "-t", "--user", "0", path],
                                   "install", seconds=120)
            finally:
                setup["installs"][role] = _known_attempt(cap, previous)
            _need(_line(raw) == "Success")
        before = _installed(cap, live, until, manifest)
        before_pin = _write(output, identity, "installed-before-v1.json",
                            dict(version=1, scope=INSTALLED_SCOPE, session=session_pin, packages=before))
        phase = "instrument"
        previous = cap.count
        try:
            frame, _ = _command(cap, live, until, contract.instrument_argv(admission),
                                contract.CLAIM_KIND, seconds=180, limit=FRAME_CAP)
        finally:
            execution["record"] = _known_attempt(cap, previous)
        phase = "records"
        raw_records = {}
        for leaf in ("created", "saved", "commands"):
            previous = cap.count
            try:
                raw, _ = _command(cap, live, until, contract.probe_read_argv(admission, leaf),
                                  "probe-" + leaf, limit=PROBE_CAP)
            finally:
                pin = _known_attempt(cap, previous)
                if pin is not None:
                    product_records[leaf] = dict(record=pin, raw=_json(pin)["stdout"])
            raw_records[leaf] = raw
        evidence = validate_result(frame, _expected(admission, manifest, before), raw_records)
        evidence_pin = _write(output, identity, "presentation-evidence-v1.json", evidence)
        phase = "verify"
        after = _installed(cap, live, until, manifest)
        after_pin = _write(output, identity, "installed-after-v1.json",
                           dict(version=1, scope=INSTALLED_SCOPE, session=session_pin, packages=after))
        _need(_same_installed(before, after))
        _need(type(cap.count) is int and cap.count == len(setup["boot"]) + 38)
        phase, outcome, reason = "completed", "completed", None
    except BaseException as error:
        outcome = "refused"
        reason = "deadline" if isinstance(error, TimeoutError) or str(error) in ("deadline", "expired") else "checks_failed"
    finally:
        count = 0 if cap is None else cap.count
        if cap is not None:
            try:
                if cap.clean:
                    verification.require_current_clients(output, count, session_pin, admission)
                else:
                    outcome, reason = "refused", "resource_uncertain"
            except BaseException:
                outcome, reason = "refused", "checks_failed"
            try:
                cap.close()
            except BaseException:
                outcome, reason = "refused", "resource_uncertain"
        if live is not None:
            try:
                observed = live.close()
                observer_closed = observed if type(observed) is bool else None
            except BaseException:
                observer_closed = None
            if observer_closed is not True:
                outcome, reason = "refused", "resource_uncertain"
        try:
            _inputs(admission_binding, running_binding)
            if request_pin is not None:
                _need(_same(_json(request_pin), request))
            if outcome == "completed":
                _need(time.monotonic() - begin < SECONDS, "deadline")
        except BaseException:
            outcome, reason = "refused", "checks_failed"
        if cap is not None:
            try:
                setup_pin = _write(output, identity, "setup-v1.json", setup)
            except BaseException:
                outcome, reason = "refused", "checks_failed"
        result = dict(version=1, scope=SCOPE, request=request_pin, session=session_pin, setup=setup_pin,
                      installed_before=before_pin, execution=execution, product_records=product_records, evidence=evidence_pin, installed_after=after_pin,
                      client_count=count, outcome=outcome, phase=phase, reason=reason,
                      observer_handles_closed=observer_closed, feature_acceptance=False,
                      elapsed_ms=round(max(0, time.monotonic() - begin) * 1000))
        _write(output, identity, "controller-result-v1.json", result)
    return copy.deepcopy(result)


def verify_controller_result(result_binding, admission_binding, running_binding, expected_caller):
    """Replay fixed source, raw clients, the one external claim and v3 process proof without target calls."""
    admission, manifest = _inputs(admission_binding, running_binding)
    output = _output(admission)
    result = _at(result_binding, output / "controller-result-v1.json")
    _object(result, RESULT_KEYS)
    _need(type(result["version"]) is int and result["version"] == 1 and result["scope"] == SCOPE and
          result["outcome"] == result["phase"] == "completed" and result["reason"] is None and
          result["observer_handles_closed"] is True and result["feature_acceptance"] is False and
          type(result["elapsed_ms"]) is int and 0 <= result["elapsed_ms"] <= SECONDS * 1000)
    request = _at(result["request"], output / "request-v1.json")
    _object(request, REQUEST_KEYS)
    _need(type(request["version"]) is int and request["version"] == 1 and request["scope"] == REQUEST_SCOPE and
          _same(request["admission"], admission_binding) and _same(request["running"], running_binding) and
          _same(request["build"], admission["artifacts"]["build"]) and request["root"] == str(output) and
          _same(request["controller"], env.binding(Path(__file__).resolve())) and
          _same(request["sources"], admission["sources"]) and _same(request["python"], admission["python"]) and
          _same(request["caller"], expected_caller) and type(request["seconds"]) is int and request["seconds"] == SECONDS)
    session = _at(result["session"], output / contract.SESSION_FILE)
    contract.validate_session(session, admission)
    _need(_same(session["admission"], admission_binding) and _same(session["running"], running_binding) and
          _same(session["caller"], expected_caller) and session["seconds"] == SECONDS)
    count = result["client_count"]
    _need(type(count) is int and 1 <= count <= 10000)
    rows = verification.require_current_clients(output, count, result["session"], admission)
    cursor = 0

    def consume(pin, argv, label, *, source=None, stderr_empty=True, limit=MAX_BYTES, seconds=15):
        nonlocal cursor
        _need(cursor < len(rows))
        row = rows[cursor]
        cursor += 1
        _need(_same(pin, env.binding(output / "clients" / ("command-%04d.json" % cursor))))
        _need(row["index"] == cursor and _same(row["operation"], dict(argv=argv, stdin=source)) and
              row["client_qualified"] is True and row["status"] == "completed" and row["label"] == label and
              type(row["returncode"]) is int and row["returncode"] == 0 and
              type(row["effective_deadline_ms"]) is int and 0 < row["effective_deadline_ms"] <= seconds * 1000)
        stdout, stderr = _raw(row["stdout"], limit), _raw(row["stderr"], limit)
        _need(len(stdout) + len(stderr) <= limit)
        if stderr_empty:
            _need(stderr == b"")
        return stdout

    setup = _at(result["setup"], output / "setup-v1.json")
    _object(setup, ("version", "scope", "session", "boot", "properties", "user", "packages_absent", "staged", "installs"))
    _need(type(setup["version"]) is int and setup["version"] == 1 and setup["scope"] == SETUP_SCOPE and
          _same(setup["session"], result["session"]) and type(setup["boot"]) is list and 1 <= len(setup["boot"]) <= 61)
    for index, pin in enumerate(setup["boot"]):
        value = _boot_value(consume(pin, ["getprop", "sys.boot_completed"], "boot"))
        _need(value == "1" if index == len(setup["boot"]) - 1 else value in ("", "0"))
    _object(setup["properties"], ("api", "abi", "qemu"))
    for key, prop, wanted in (("api", "ro.build.version.sdk", "35"),
                              ("abi", "ro.product.cpu.abi", "x86_64"), ("qemu", "ro.kernel.qemu", "1")):
        _need(_line(consume(setup["properties"][key], ["getprop", prop], "property")) == wanted)
    _need(_line(consume(setup["user"], ["am", "get-current-user"], "user")) == "0")
    for key in ("packages_absent", "staged", "installs"):
        _object(setup[key], ROLES)
    for role in ROLES:
        package = manifest["apks"][role]["package"]
        _need(_uid(consume(setup["packages_absent"][role],
            ["cmd", "package", "list", "packages", "-U", "--user", "0", package], "package-absent"), package) is None)
    for role, path in zip(ROLES, STAGED):
        staged = setup["staged"][role]
        _object(staged, ("transfer", "sha256"))
        source = admission["artifacts"][role]
        _need(consume(staged["transfer"], ["dd", "of=" + path, "bs=65536"], "apk-stage", source=source, stderr_empty=False, seconds=120) == b"")
        _need(_line(consume(staged["sha256"], ["sha256sum", path], "staged-hash")) == source["sha256"] + "  " + path)
        _need(_line(consume(setup["installs"][role], ["pm", "install", "-r", "-t", "--user", "0", path], "install", seconds=120)) == "Success")

    def installed(pin, name):
        value = _at(pin, output / name)
        _object(value, ("version", "scope", "session", "packages"))
        _need(type(value["version"]) is int and value["version"] == 1 and value["scope"] == INSTALLED_SCOPE and
              _same(value["session"], result["session"]))
        _object(value["packages"], ROLES)
        for role in ROLES:
            entry = value["packages"][role]
            _object(entry, ("package", "uid", "path", "checks"))
            package = manifest["apks"][role]["package"]
            _need(entry["package"] == package and type(entry["uid"]) is int)
            _object(entry["checks"], ("uid", "path", "sha256"))
            checks = entry["checks"]
            _need(_uid(consume(checks["uid"], ["cmd", "package", "list", "packages", "-U", "--user", "0", package], "package"), package) == entry["uid"])
            _need(_apk_path(consume(checks["path"], ["cmd", "package", "path", "--user", "0", package], "package-path"), package) == entry["path"])
            _need(_line(consume(checks["sha256"], ["sha256sum", entry["path"]], "package-hash")) == manifest["apks"][role]["binding"]["sha256"] + "  " + entry["path"])
        _need(len({p["uid"] for p in value["packages"].values()}) == 3)
        return value["packages"]

    before = installed(result["installed_before"], "installed-before-v1.json")
    execution = result["execution"]
    _object(execution, ("kind", "case", "record"))
    _need(execution["kind"] == contract.CLAIM_KIND and execution["case"] == contract.CASE)
    frame = consume(execution["record"], contract.instrument_argv(admission), contract.CLAIM_KIND,
                    limit=FRAME_CAP, seconds=180)
    _object(result["product_records"], ("created", "saved", "commands"))
    raw_records = {}
    for leaf in ("created", "saved", "commands"):
        entry = result["product_records"][leaf]
        _object(entry, ("record", "raw"))
        raw = consume(entry["record"], contract.probe_read_argv(admission, leaf), "probe-" + leaf, limit=PROBE_CAP)
        _need(_same(entry["raw"], rows[cursor - 1]["stdout"]) and _raw(entry["raw"], PROBE_CAP) == raw)
        raw_records[leaf] = raw
    evidence = validate_result(frame, _expected(admission, manifest, before), raw_records)
    _need(_same(_at(result["evidence"], output / "presentation-evidence-v1.json"), evidence))
    after = installed(result["installed_after"], "installed-after-v1.json")
    _need(_same_installed(before, after) and cursor == count == len(rows) == len(setup["boot"]) + 38)
    _need({path.name for path in output.iterdir()} == {"request-v1.json", contract.SESSION_FILE, "setup-v1.json",
        "installed-before-v1.json", "installed-after-v1.json", "presentation-evidence-v1.json", "controller-result-v1.json", "clients", "proofs"})
    _inputs(admission_binding, running_binding)
    _need(_same(_at(result_binding, output / "controller-result-v1.json"), result))
    return copy.deepcopy(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admission", required=True, type=Path)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--running", required=True, type=Path)
    parser.add_argument("--running-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        admission = env.binding(env.safe_path(args.admission, exists=True))
        running = env.binding(env.safe_path(args.running, exists=True))
        _need(admission["sha256"] == args.admission_sha256 and running["sha256"] == args.running_sha256)
        return 0 if run(admission, running)["outcome"] == "completed" else 1
    except (env.EnvironmentRefused, OSError, ValueError, KeyError, TypeError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
