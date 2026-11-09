"""Final Windows archive replay over a fully verified SDK25 exchange.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path

from benchmarks import archive_roundtrip_bridge as bridge
from benchmarks import archive_roundtrip_build as build
from benchmarks import archive_roundtrip_outbound as outbound
from benchmarks import archive_roundtrip_return as returning
from benchmarks import owned_archive_roundtrip_client as client
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import runtime_spike as process
from benchmarks import windows_tcp_control as output_control

DIRECTORY = "windows-final-v1"
SCOPE = "archive-windows-final-v1"
INPUT = "android-final.json"
ORACLE = "expected-android-final.json"
MODE = "check-final"


class FinalRefused(ValueError):
    """A fixed refusal without raw evidence or local paths."""


def _need(condition, reason):
    if not condition:
        raise FinalRefused(reason)


def _root(admission):
    return Path(admission["root"]) / outbound.OUTPUT / DIRECTORY


def _request(admission, returned):
    root = _root(admission)
    executable = admission["artifacts"]["fixture_executable"]
    fixtures = bridge._root(admission) / "windows"
    expected = bridge._pin(fixtures / ORACLE, contract.MAX_BYTES)
    raw = bridge._read(expected, fixtures / ORACLE, contract.MAX_BYTES)
    _need(raw == returned["final"] and raw, "final_archive")
    argv = [executable["path"], "--owned-stdin", "--development-fixtures", MODE,
            "--directory", str(root / "checked"), "--inputs", str(root / "input"),
            "--fixtures", str(fixtures)]
    return dict(version=1, scope=SCOPE, session=returned["session"], bridge=returned["bridge"],
                outbound_records=list(returned["outbound_records"]), records=list(returned["records"]),
                write_claim=returned["write_claim"], instrumentation=returned["instrumentation"],
                executable=executable, oracle=expected, argv=argv, deadline=bridge.DEADLINE,
                capture_cap=bridge.TERMINAL_CAP,
                input=bridge._pin_bytes(root / "input" / INPUT, raw))


def _input(root, request, raw):
    directory = env.safe_path(root / "input", directory=True)
    _need({path.name for path in directory.iterdir()} == {INPUT}, "input")
    _need(bridge._read(request["input"], directory / INPUT, contract.MAX_BYTES) == raw, "input")


def _inventory(root, *, published):
    names = {"checked", "input", "request.json", "stdout.bin", "terminal.json"}
    if published:
        names.add("receipt.json")
    directory = env.safe_path(root, directory=True)
    _need({path.name for path in directory.iterdir()} == names, "outputs")


def _outputs(root):
    checked = env.safe_path(root / "checked", directory=True)
    sizes = {"result.json": bridge.TERMINAL_CAP, "android-final.sqlite3": bridge.DATABASE_CAP}
    _need({path.name for path in checked.iterdir()} == set(sizes), "outputs")
    outputs = {name: bridge._pin(checked / name, cap) for name, cap in sizes.items()}
    _need(all(pin["bytes"] > 0 for pin in outputs.values()), "outputs")
    report = env.decode_json(bridge._read(outputs["result.json"], checked / "result.json", bridge.TERMINAL_CAP))
    _need(contract._same(report, dict(version=1, fixture="locallore-platform-roundtrip-v1",
                                      status="passed", mode=MODE)), "outputs")
    return outputs


def run(admission, returned):
    """Execute only the pinned final Rust check for the exact closed return."""
    admission = contract.validate_admission(admission)
    replayed = returning.replay(admission, returned["session"], returned["bridge"])
    _need(contract._same(replayed, returned), "return_evidence")
    build.verify_current(admission)
    request = _request(admission, replayed)
    request_bytes = env.encoded(request)
    _need(0 < len(request_bytes) <= bridge.RECEIPT_CAP, "request")
    root = output_control.validate_output(str(_root(admission)))
    root.mkdir()
    (root / "input").mkdir()
    _need(bridge._write(root / "input" / INPUT, replayed["final"]) == request["input"], "input")
    _input(root, request, replayed["final"])
    request_path = root / "request.json"
    env.create_json(request_path, request)
    request_pin = bridge._pin_bytes(request_path, request_bytes)
    _need(bridge._read(request_pin, request_path, bridge.RECEIPT_CAP) == request_bytes, "request")
    child = process.run_process(request["argv"], deadline=bridge.DEADLINE, max_output=bridge.TERMINAL_CAP)
    terminal = dict(status=child.status, exit_code=child.returncode,
                    stderr_bytes=child.stderr_bytes, elapsed_ms=child.elapsed_ms,
                    cleanup_complete=child.cleanup_complete,
                    stdout=bridge._write(root / "stdout.bin", child.stdout))
    terminal_path = root / "terminal.json"
    env.create_json(terminal_path, terminal)
    terminal_pin = bridge._pin_bytes(terminal_path, env.encoded(terminal))
    bridge._check_terminal(terminal, root, mode=MODE)

    build.verify_current(admission)
    after = returning.replay(admission, request["session"], request["bridge"])
    _need(contract._same(after, replayed) and contract._same(_request(admission, after), request),
          "return_evidence")
    _input(root, request, after["final"])
    _inventory(root, published=False)
    outputs = _outputs(root)
    _need(bridge._pin(request_path, bridge.RECEIPT_CAP) == request_pin, "request")
    _need(bridge._pin(terminal_path, bridge.RECEIPT_CAP) == terminal_pin, "terminal")
    bridge._check_terminal(terminal, root, mode=MODE)
    receipt_path = root / "receipt.json"
    receipt = dict(version=1, scope=SCOPE, request=request_pin, terminal=terminal_pin, outputs=outputs)
    env.create_json(receipt_path, receipt)
    receipt_pin = bridge._pin_bytes(receipt_path, env.encoded(receipt))
    _need(bridge._pin(receipt_path, bridge.RECEIPT_CAP) == receipt_pin, "receipt")
    return receipt_pin


def verify(admission, expected_session, expected_bridge, receipt_pin):
    """Recheck exact Android records and the retained final Windows receipt."""
    admission = contract.validate_admission(admission)
    root = _root(admission)
    _inventory(root, published=True)
    cap = bridge.RECEIPT_CAP
    receipt = env.decode_json(bridge._read(receipt_pin, root / "receipt.json", cap))
    _need(type(receipt) is dict and set(receipt) == {"version", "scope", "request", "terminal", "outputs"}
          and type(receipt["version"]) is int and receipt["version"] == 1 and
          receipt["scope"] == SCOPE, "receipt")
    request = env.decode_json(bridge._read(receipt["request"], root / "request.json", cap))
    _need(type(request) is dict and contract._same(request.get("session"), expected_session) and
          contract._same(request.get("bridge"), expected_bridge), "request")
    returned = returning.replay(admission, expected_session, expected_bridge)
    build.verify_current(admission)
    _need(contract._same(request, _request(admission, returned)), "request")
    _input(root, request, returned["final"])
    terminal = env.decode_json(bridge._read(receipt["terminal"], root / "terminal.json", cap))
    bridge._check_terminal(terminal, root, mode=MODE)
    _need(contract._same(_outputs(root), receipt["outputs"]), "outputs")
    return receipt


def exchange(capture):
    """Run all four transfer legs over a caller-owned, already-admitted SDK25 lease."""
    _need(type(capture) is client.OwnedArchiveRoundtripSdkCapture and capture.clean is True, "client")
    try:
        admission = contract.validate_admission(capture.lease.admission)
        initial = outbound.run(capture)
        middle = bridge.run(admission, initial)
        returned = returning.run(capture, middle)
        final = run(admission, returned)
        return dict(session=initial["session"], bridge=middle, final=final)
    finally:
        if capture.clean:
            capture.close()
