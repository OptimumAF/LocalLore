"""Owned Windows continuation between SDK25 outbound and return.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path

from benchmarks import archive_roundtrip_build as build
from benchmarks import archive_roundtrip_outbound as outbound
from benchmarks import archive_ui_build as files
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import runtime_spike as process
from benchmarks import windows_tcp_control as output_control

DIRECTORY = contract.BRIDGE_DIRECTORY
SCOPE = "archive-windows-continuation-v1"
INPUTS = ("windows-return.json", "windows-continued.json", "android-origin.json")
OUTPUTS = ("android-return.json", "expected-android-final.json", "result.json",
           "windows-return.sqlite3", "windows-continued.sqlite3",
           "android-origin.sqlite3", "android-final-control.sqlite3")
DEADLINE = 120
TERMINAL_CAP = 4096
RECEIPT_CAP = 128 * 1024
DATABASE_CAP = 1024 * 1024


class BridgeRefused(ValueError):
    """A fixed refusal category without raw bytes or physical paths."""


def _need(condition, reason):
    if not condition:
        raise BridgeRefused(reason)


def _pin_bytes(path, raw):
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _pin(path, limit):
    return _pin_bytes(path, files._read(path, limit))


def _read(pin, expected_path, limit):
    contract.binding(pin, max_bytes=limit)
    _need(pin["path"] == str(expected_path), "path")
    return files._bound(pin, cap=limit)


def _write(path, raw):
    with env.safe_path(path, exists=False).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return _pin_bytes(path, raw)


def _root(admission):
    return Path(admission["root"]) / outbound.OUTPUT / DIRECTORY


def _replay(admission, session, records):
    _need(type(records) in (tuple, list), "outbound")
    result = outbound.replay_prefix(admission, session, len(records))
    _need(contract._same(list(result["records"]), list(records)), "outbound")
    return result


def _request(admission, outbound_result):
    root = _root(admission)
    artifacts = admission["artifacts"]
    executable = artifacts["fixture_executable"]
    fixtures = Path(artifacts["expectations"]["path"]).parent
    argv = [executable["path"], "--owned-stdin", "--development-fixtures", "verify",
            "--directory", str(root / "windows"), "--inputs", str(root / "outbound"),
            "--fixtures", str(fixtures)]
    inputs = {name: _pin_bytes(root / "outbound" / name, outbound_result["files"][name])
              for name in INPUTS}
    return dict(version=1, scope=SCOPE, session=outbound_result["session"],
                records=list(outbound_result["records"]), executable=executable,
                fixtures={key: artifacts[key] for key in
                          ("expectations", "windows_origin", "windows_continued", "fixture_preflight")},
                inputs=inputs, argv=argv, deadline=DEADLINE, capture_cap=TERMINAL_CAP)


def _check_inputs(request, root, outbound_result):
    directory = env.safe_path(root / "outbound", directory=True)
    _need({path.name for path in directory.iterdir()} == set(INPUTS), "inputs")
    for name, pin in request["inputs"].items():
        _need(_read(pin, directory / name, contract.MAX_BYTES) == outbound_result["files"][name],
              "inputs")


def _check_terminal(terminal, root):
    keys = {"status", "exit_code", "stderr_bytes", "elapsed_ms", "cleanup_complete", "stdout"}
    _need(type(terminal) is dict and set(terminal) == keys and
          terminal["status"] == "completed" and terminal["cleanup_complete"] is True and
          type(terminal["exit_code"]) is int and terminal["exit_code"] == 0 and
          type(terminal["stderr_bytes"]) is int and terminal["stderr_bytes"] == 0 and
          type(terminal["elapsed_ms"]) is int and 0 <= terminal["elapsed_ms"] <= DEADLINE * 1000,
          "terminal")
    raw = _read(terminal["stdout"], root / "stdout.bin", TERMINAL_CAP)
    _need(raw in (b'{"status":"passed","mode":"verify"}\n',
                  b'{"status":"passed","mode":"verify"}\r\n'), "terminal")


def _inventory(root, *, published):
    names = {"outbound", "windows", "request.json", "stdout.bin", "terminal.json"}
    if published:
        names.add("receipt.json")
    directory = env.safe_path(root, directory=True)
    _need({path.name for path in directory.iterdir()} == names, "outputs")


def _outputs(root):
    directory = env.safe_path(root / "windows", directory=True)
    _need({path.name for path in directory.iterdir()} == set(OUTPUTS), "outputs")
    output = {}
    for name in OUTPUTS:
        cap = DATABASE_CAP if name.endswith(".sqlite3") else contract.MAX_BYTES
        output[name] = _pin(directory / name, cap)
        _need(output[name]["bytes"] > 0, "outputs")
    result = env.decode_json(_read(output["result.json"], directory / "result.json", TERMINAL_CAP))
    _need(contract._same(result, dict(version=1, fixture="locallore-platform-roundtrip-v1",
                                      status="passed", mode="verify")), "outputs")
    return output


def run(admission, outbound_result):
    """Run the one pinned Windows child and publish a receipt only after closure."""
    admission = contract.validate_admission(admission)
    replayed = _replay(admission, outbound_result["session"], outbound_result["records"])
    _need(contract._same(replayed, outbound_result), "outbound")
    build.verify_current(admission)
    root = output_control.validate_output(str(_root(admission)))
    root.mkdir()
    (root / "outbound").mkdir()
    request = _request(admission, replayed)
    for name in INPUTS:
        _need(_write(root / "outbound" / name, replayed["files"][name]) == request["inputs"][name],
              "inputs")
    _check_inputs(request, root, replayed)
    request_path = root / "request.json"
    env.create_json(request_path, request)
    request_pin = _pin(request_path, RECEIPT_CAP)
    result = process.run_process(request["argv"], deadline=DEADLINE, max_output=TERMINAL_CAP)
    terminal = dict(status=result.status, exit_code=result.returncode,
                    stderr_bytes=result.stderr_bytes, elapsed_ms=result.elapsed_ms,
                    cleanup_complete=result.cleanup_complete, stdout=_write(root / "stdout.bin", result.stdout))
    terminal_path = root / "terminal.json"
    env.create_json(terminal_path, terminal)
    terminal_pin = _pin_bytes(terminal_path, env.encoded(terminal))
    _check_terminal(terminal, root)
    build.verify_current(admission)
    after = _replay(admission, request["session"], request["records"])
    _need(contract._same(after, replayed), "outbound")
    _check_inputs(request, root, after)
    _need(env.decode_json(_read(request_pin, request_path, RECEIPT_CAP)) == request, "request")
    _inventory(root, published=False)
    outputs = _outputs(root)
    _need(_pin(terminal_path, RECEIPT_CAP) == terminal_pin, "terminal")
    _check_terminal(terminal, root)
    receipt = dict(version=1, scope=SCOPE, request=request_pin,
                   terminal=terminal_pin, outputs=outputs)
    path = root / "receipt.json"
    env.create_json(path, receipt)
    return _pin(path, RECEIPT_CAP)


def verify_context(admission, expected_session, receipt_pin):
    """Revalidate the retained bridge and expose the verified prefix and output pins."""
    admission = contract.validate_admission(admission)
    root = _root(admission)
    _inventory(root, published=True)
    receipt = env.decode_json(_read(receipt_pin, root / "receipt.json", RECEIPT_CAP))
    _need(type(receipt) is dict and set(receipt) == {"version", "scope", "request", "terminal", "outputs"}
          and type(receipt["version"]) is int and receipt["version"] == 1 and
          receipt["scope"] == SCOPE, "receipt")
    request = env.decode_json(_read(receipt["request"], root / "request.json", RECEIPT_CAP))
    _need(type(request) is dict and contract._same(request.get("session"), expected_session), "session")
    replayed = _replay(admission, expected_session, request.get("records"))
    _need(contract._same(request, _request(admission, replayed)), "request")
    build.verify_current(admission)
    _check_inputs(request, root, replayed)
    terminal = env.decode_json(_read(receipt["terminal"], root / "terminal.json", RECEIPT_CAP))
    _check_terminal(terminal, root)
    outputs = _outputs(root)
    _need(contract._same(outputs, receipt["outputs"]), "outputs")
    return dict(outputs={name: outputs[name] for name in OUTPUTS[:2]},
                records=replayed["records"], installed=replayed["installed"])


def verify(admission, expected_session, receipt_pin):
    """Revalidate retained continuation evidence and return its two exact archive pins."""
    return verify_context(admission, expected_session, receipt_pin)["outputs"]
