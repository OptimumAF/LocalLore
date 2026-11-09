"""Ordered Android return under the exact SDK25 lease and Windows receipt.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path

from benchmarks import android_instrumentation_evidence as instrumentation
from benchmarks import archive_roundtrip_bridge as bridge
from benchmarks import archive_roundtrip_outbound as outbound
from benchmarks import owned_archive_roundtrip_client as client
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_archive_roundtrip_owner as owner

COMMANDS = 18


class ReturnRefused(ValueError):
    """A fixed refusal without raw evidence or local paths."""


def _need(condition, reason):
    if not condition:
        raise ReturnRefused(reason)


class _ReturnCommands(outbound._Commands):
    def __init__(self, admission, session, count, *, start, capture=None, receipt=None):
        super().__init__(admission, session, count, capture, start=start)
        self.receipt = receipt

    def _capture_command(self, argv, label, source, seconds, cap):
        kind = contract.return_kind(argv, self.admission)
        if kind is None:
            return super()._capture_command(argv, label, source, seconds, cap)
        capture = self.capture
        _need(capture._return_permit is None, "return_authority")
        operation = (argv, source, label, seconds, cap, source is not None)
        capture._return_permit = copy.deepcopy((self.receipt, operation))
        try:
            return super()._capture_command(argv, label, source, seconds, cap)
        finally:
            capture._return_permit = None


def _claim(admission, session, source):
    verifier = owner.VERIFIER
    path = Path(admission["root"]) / "claims-v1" / (contract.RETURN_WRITE + "-v1.json")
    pin = verifier._pin(path)
    record = verifier._at(pin, path)
    operation = {"argv": contract.return_write_argv(admission), "stdin": source}
    contract.validate_claim(record, session["admission"], session["caller"],
                            contract.RETURN_WRITE, contract.operation_digest(operation))
    return pin


def _marker(admission, command):
    raw = command(contract.read_argv(admission, "owner-v1"), "owner-marker")
    _need(raw == contract.MARKER, "owner_marker")


def _terminal(raw):
    class_name, method = contract.SELECTOR.split("#")
    return instrumentation.validate_instrumentation(raw, class_name, [method])


def _write_operation(admission, context):
    return (contract.return_write_argv(admission), context["outputs"]["android-return.json"],
            contract.RETURN_WRITE, 120, outbound.SETUP_CAP, True)


def _readback_operation(admission):
    return (contract.read_argv(admission, "android-return.json"), None, "return-readback",
            15, contract.MAX_BYTES, False)


def _return_operation(admission):
    return (contract.return_argv(admission), None, contract.RETURN, 120, contract.MAX_BYTES, False)


def _evidence(command, operation):
    argv, source, label, seconds, cap, _ = operation
    return command(argv, label, source=source, seconds=seconds, cap=cap)


def authorize_dispatch(capture, receipt, kind, operation):
    """Recheck the fixed receipt and prerequisites before any return-only wire dispatch."""
    _need(type(capture) is client.OwnedArchiveRoundtripSdkCapture and capture.clean is True,
          "client_type")
    admission = contract.validate_admission(capture.lease.admission)
    session, context, start = _context(admission, capture.session_binding, receipt)
    _need(contract._same(session, capture.session), "session")
    _need(kind == contract.return_kind(operation[0], admission), "return_authority")
    count = capture.count
    source = context["outputs"]["android-return.json"]
    write = _write_operation(admission, context)
    readback = _readback_operation(admission)
    run_return = _return_operation(admission)
    final_read = (contract.read_argv(admission, "android-final.json"), None, "return-final",
                  15, contract.MAX_BYTES, False)
    if kind == contract.RETURN_WRITE:
        _need(count == start + 7 and contract._same(operation, write), "return_authority")
        prior = outbound._Commands(admission, session, count, start=start)
        _need(outbound._installed(admission, prior) == context["installed"], "package_drift")
        _marker(admission, prior)
        digest = contract.operation_digest({"argv": write[0], "stdin": source})
        capture.lease.claim_once(kind, digest)
        return

    _need((count == start + 8 and contract._same(operation, readback)) or
          (count == start + 9 and contract._same(operation, run_return)) or
          (count == start + 11 and contract._same(operation, final_read)), "return_authority")
    prior = outbound._Commands(admission, session, count, start=start + 7)
    _need(_evidence(prior, write) == b"", "return_write")
    _claim(admission, session, source)
    if count >= start + 9:
        path = bridge._root(admission) / "windows" / "android-return.json"
        expected = bridge._read(source, path, contract.MAX_BYTES)
        _need(_evidence(prior, readback) == expected and expected, "return_readback")
    if count == start + 11:
        _terminal(_evidence(prior, run_return))
        _marker(admission, prior)


def _sequence(admission, context, command):
    installed = context["installed"]
    _need(outbound._installed(admission, command) == installed, "package_drift")
    _marker(admission, command)
    outputs = context["outputs"]
    source = outputs["android-return.json"]
    root = bridge._root(admission) / "windows"
    expected_return = bridge._read(source, root / "android-return.json", contract.MAX_BYTES)
    expected_final = bridge._read(outputs["expected-android-final.json"],
                                  root / "expected-android-final.json", contract.MAX_BYTES)
    raw = command(contract.return_write_argv(admission), contract.RETURN_WRITE,
                  source=source, seconds=120)
    _need(raw == b"", "return_write")
    write_claim = _claim(admission, command.session, source)
    raw = command(contract.read_argv(admission, "android-return.json"),
                  "return-readback", cap=contract.MAX_BYTES)
    _need(raw == expected_return and raw, "return_readback")
    raw = command(contract.return_argv(admission), contract.RETURN, seconds=120,
                  cap=contract.MAX_BYTES)
    terminal = _terminal(raw)
    _marker(admission, command)
    final = command(contract.read_argv(admission, "android-final.json"),
                    "return-final", cap=contract.MAX_BYTES)
    _need(final == expected_final and final, "final_archive")
    _need(outbound._installed(admission, command) == installed, "package_drift")
    _need(_claim(admission, command.session, source) == write_claim, "return_write")
    return dict(final=final, instrumentation=terminal, write_claim=write_claim)


def _context(admission, session_binding, receipt):
    session = outbound._session(admission, session_binding)
    context = bridge.verify_context(admission, session_binding, receipt)
    start = len(context["records"])
    return session, context, start


def _result(result, commands, session_binding, receipt, context):
    _need(len(commands.records) == COMMANDS, "command_count")
    expected = tuple(context["records"]) + tuple(commands.records)
    verifier = owner.VERIFIER
    root = Path(commands.session["root"])
    rows = verifier.require_current_clients(root, len(expected), session_binding, commands.admission)
    _need(len(rows) == len(expected) and all(
        verifier._pin(root / "clients" / f"command-{index:04d}.json") == pin
        for index, pin in enumerate(expected, 1)), "command_roster")
    _need(verifier._pin(Path(result["write_claim"]["path"])) == result["write_claim"], "return_write")
    return dict(result, session=session_binding, bridge=receipt,
                outbound_records=context["records"], records=tuple(commands.records))


def run(capture, receipt):
    """Write once, verify byte-exact readback, then run the distinct return test."""
    _need(type(capture) is client.OwnedArchiveRoundtripSdkCapture and capture.clean is True,
          "client_type")
    try:
        admission = contract.validate_admission(capture.lease.admission)
        session_binding = capture.session_binding
        session, context, start = _context(admission, session_binding, receipt)
        _need(contract._same(session, capture.session) and capture.count == start, "session")
        commands = _ReturnCommands(admission, session, start + COMMANDS, start=start, capture=capture, receipt=receipt)
        result = _sequence(admission, context, commands)
        _need(capture.count == start + COMMANDS, "command_count")
        return _result(result, commands, session_binding, receipt, context)
    finally:
        capture.close()


def replay(admission, session_binding, receipt):
    """Verify the exact closed return segment and hand off the final archive bytes."""
    admission = contract.validate_admission(admission)
    session, context, start = _context(admission, session_binding, receipt)
    commands = _ReturnCommands(admission, session, start + COMMANDS, start=start)
    result = _sequence(admission, context, commands)
    return _result(result, commands, session_binding, receipt, context)
