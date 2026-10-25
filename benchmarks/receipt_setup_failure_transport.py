"""Admitted negative-only qualification of receipt instrumentation status transport.

The selected test MUST fail. This never qualifies setup, restart or real inference.
No device operation runs at import. Private raw evidence stays outside Git.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receipt_setup_qualification as q

SCOPE = "receipt_setup_failure_transport"
REQUEST = b"receipt-setup-failure-transport-v1\n"
CLASS = "org.locallore.app.ReceiptSetupFailureTransportTest"
METHOD = "preservesOriginalFailureAfterDedicatedStatus"
SENTINEL = "java.lang.AssertionError: receipt_setup_failure_transport_v1"
INSTRUMENT = ("am", "instrument", "-w", "-r", "-e", "class", CLASS,
              q.TEST + "/androidx.test.runner.AndroidJUnitRunner")
SOURCE_FILES = (*q.SOURCE_FILES, "benchmarks/receipt_setup_failure_transport.py",
                "scripts/tests/test_receipt_setup_failure_transport.py",
                "apps/android/app/src/modelReceiptAndroidTest/java/org/locallore/app/ReceiptSetupFailureTransportTest.kt",
                "docs/native/RECEIPT_SETUP_FAILURE_TRANSPORT_PROTOCOL.md")


def expected_trace():
    return {"version": 1, "case": "ACCEPT", "expected": "READY", "actual": "MISSING", "error": "NONE",
            "events_total": 2, "events_saturated": False, "events": ["CHECK_START", "CHECK_MISSING"],
            "source": {"opened": 0, "closed": 0, "active": 0, "reads": 0, "bytes": 0,
                       "reads_saturated": False, "bytes_saturated": False}}


def parse_negative_instrumentation(raw):
    """Only this original synthetic failure qualifies transport; no pass is produced."""
    trace = q.extract_failure_trace(raw)
    assert trace == expected_trace()
    text = q.normalized(raw, 131072)
    records, fields, result, stream, terminal = [], {}, None, None, False
    for line in text.split("\n"):
        if line.startswith("INSTRUMENTATION_STATUS: "):
            assert result is None and not terminal
            key, sep, value = line[len("INSTRUMENTATION_STATUS: "):].partition("=")
            assert sep and key in {"class", "current", "id", "numtests", "stream", "test", "stack",
                                   "locallore_receipt_failure_v1"} and key not in fields
            fields[key] = [value]
            stream = key if key in {"stream", "stack"} else None
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            code = line.split(": ", 1)[1]
            assert result is None and not terminal and code in {"1", "1337", "-2"}
            records.append((code, {key: "\n".join(value) for key, value in fields.items()}))
            fields, stream = {}, None
        elif line.startswith("INSTRUMENTATION_RESULT: "):
            assert result is None and not terminal and not fields and len(records) == 3
            assert line == "INSTRUMENTATION_RESULT: stream="
            result, stream = [""], "result"
        elif line.startswith("INSTRUMENTATION_CODE: "):
            assert line == "INSTRUMENTATION_CODE: -1" and result is not None and not terminal and not fields
            terminal, stream = True, None
        elif line.startswith("INSTRUMENTATION_"):
            raise AssertionError("unexpected_negative_machine_record")
        elif stream == "result":
            result.append(line)
        elif stream is not None:
            fields[stream].append(line)
        else:
            assert not line.strip()
    assert not fields and terminal and result is not None and [row[0] for row in records] == ["1", "1337", "-2"]
    start, diagnostic, end = (row[1] for row in records)
    standard = {"class": CLASS, "current": "1", "id": "AndroidJUnitRunner", "numtests": "1", "test": METHOD}
    assert set(start) == set(standard) | {"stream"} and all(start[key] == value for key, value in standard.items())
    assert start["stream"].strip("\n") in ("", CLASS + ":")
    assert set(diagnostic) == {"locallore_receipt_failure_v1"}
    assert q.parse_failure_trace(diagnostic["locallore_receipt_failure_v1"].encode("ascii")) == trace
    assert set(end) == set(standard) | {"stack", "stream"} and all(end[key] == value for key, value in standard.items())
    stack = end["stack"].strip("\n")
    frames = stack.split("\n")
    assert frames[0] == SENTINEL and 2 <= len(frames) <= 128
    assert all(re.fullmatch(r"\tat [A-Za-z0-9_.$<>]+\([A-Za-z0-9_. :+-]+\)", line) for line in frames[1:])
    assert any(CLASS in line and "ReceiptSetupFailureTransportTest.kt:" in line for line in frames[1:])
    assert end["stream"].strip("\n") == "Error in " + METHOD + "(" + CLASS + "):\n" + stack
    summary = "\n".join(result).strip("\n")
    prefix = re.fullmatch(r"Time: ((?:0|[1-9][0-9]{0,5})(?:\.[0-9]{1,9})?)\nThere was 1 failure:\n"
                          + re.escape("1) " + METHOD + "(" + CLASS + ")\n" + stack)
                          + r"\n\nFAILURES!!!\nTests run: 1,  Failures: 1", summary)
    assert prefix and 0 <= float(prefix[1]) <= 120
    try:
        q.parse_instrumentation(raw, q.INITIAL_CLASS, q.INITIAL_METHODS)
    except AssertionError:
        pass
    else:
        raise AssertionError("normal_setup_gate_must_refuse")
    return {"version": 1, "negative_transport_observed": True, "failed_methods": 1,
            "original_failure_sentinel": True, "normal_setup_gate_rejected": True, "trace": trace}


def validate_proposal(value):
    assert type(value) is dict and value.get("scope") == SCOPE
    # Reuse the same closed immutable admission shape, without accepting its
    # ordinary scope or changing the original object/normal controller.
    q.validate_proposal(dict(value, scope="receipt_setup_qualification"))
    assert all(str((q.ROOT / name).resolve()) in value["bindings"] for name in SOURCE_FILES)
    return True


def authorize(proposal_path, authorization_path, evidence):
    raw = Path(proposal_path).read_bytes()
    proposal = q.contract.strict_json(raw)
    auth = q.contract.strict_json(Path(authorization_path).read_bytes())
    assert type(auth) is dict and set(auth) == {"version", "proposal_sha256", "allow_device_calls", "root_go_pending"}
    assert type(auth["version"]) is int and auth["version"] == 1
    assert auth["proposal_sha256"] == q.sha(raw) and auth["allow_device_calls"] is True and auth["root_go_pending"] is False
    assert Path(proposal["evidence_root"]).resolve() == Path(evidence).resolve()
    validate_proposal(proposal)
    return proposal


class NegativeOwner(q.Owner):
    instrumentation_steps = ((INSTRUMENT, "negative", 0),)

    def dispatch(self, args, deadline=15, cap=65536):
        assert self.stage in {"boot", "before", "updating", "installed", "negative"}
        return super().dispatch(args, deadline, cap)


def run_cohort(owner):
    owner.wait_boot()
    before = owner.facts("before", {})
    sizes = q.validate_apks(owner.proposal)
    remaining = before["userdata"]["available_bytes"] - q.contract.USERDATA_FLOOR
    for package in (q.APP, q.TEST):
        assert sizes[package] <= remaining
        remaining -= sizes[package]
    owner.stage = "updating"
    for package in (q.APP, q.TEST):
        path = Path(owner.proposal["apk_paths"][package])
        assert q.sha(path.read_bytes()) == owner.proposal["apk_sha256"][package]
        owner.pending_install = package
        raw = owner.dispatch(["install", "--no-streaming", str(path)], deadline=35, cap=4096)
        assert q.normalized(raw, 4096) in ("Success\n", "Performing Push Install\nSuccess\n")
    owner.stage = "installed"
    installed = owner.facts("installed", owner.proposal["apk_sha256"])
    assert owner.shell(q.PROOF_ABSENT, cap=4096) == b""
    assert owner.shell(q.contract.INTERNAL_CANDIDATE_ABSENT, cap=4096) == b""
    owner.stage = "negative"
    raw = owner.shell(INSTRUMENT, deadline=120, cap=131072)
    q.observe_failure_trace(owner, raw, "initial")
    observed = parse_negative_instrumentation(raw)
    q.write_json(owner.directory / "negative-transport-v1.json", observed)
    # Deliberately no helper binding, proof reads or restart after a failed test.
    return {"negative_transport": observed, "before": before, "installed": installed,
            "normal_setup_qualified": False, "restart_qualified": False,
            "real_model_or_SDK_qualified": False, "physical_phone_qualified": False}


def worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(64) == REQUEST
    proposal = authorize(proposal_path, authorization_path, evidence)
    owner = NegativeOwner(proposal, q.open_lease(proposal))
    result, failure = None, None
    try:
        result = run_cohort(owner)
    except BaseException:
        failure = "receipt_failure_transport_stopped"
    value = {"version": 1, "scope": SCOPE, "status": "observed" if failure is None else "stopped",
             "failure": failure, "stage": owner.stage, "clients_cleaned": owner.clean, "owner_live": owner.owner_live,
             "command_count": owner.count, "instrumentation_commands": owner.methods,
             "installs": owner.installs, "result": result}
    q.write_json(owner.directory / "result-v1.json", value)
    print(json.dumps({key: value[key] for key in value if key != "result"}))
    return 0 if failure is None and owner.clean and owner.owner_live else 2


def run_owned(proposal_path, authorization_path, evidence):
    proposal = authorize(proposal_path, authorization_path, evidence)
    lease = q.open_lease(proposal)
    evidence = Path(evidence)
    q.write_json(evidence / "receipt-owned-start-v1.json", {"version": 1, "deadline_seconds": q.OUTER_SECONDS,
        "time_ns": time.time_ns(), "proposal_sha256": q.sha(Path(proposal_path).read_bytes()),
        "authorization_sha256": q.sha(Path(authorization_path).read_bytes())})
    lease.check()
    value = q.host.run_process([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "worker",
        "--proposal", str(proposal_path), "--authorization", str(authorization_path), "--evidence", str(evidence)],
        request=REQUEST, deadline=q.OUTER_SECONDS, max_output=32768)
    with (evidence / "receipt-owned-stdout-v1.bin").open("xb") as handle:
        handle.write(value.stdout)
        handle.flush()
        os.fsync(handle.fileno())
    result = {"version": 1, "status": value.status, "returncode": value.returncode, "elapsed_ms": value.elapsed_ms,
              "cleanup_complete": value.cleanup_complete, "stdout_bytes": len(value.stdout),
              "stdout_sha256": q.sha(value.stdout), "stderr_bytes": value.stderr_bytes}
    q.write_json(evidence / "receipt-owned-result-v1.json", result)
    print(json.dumps(result))
    return 0 if value.status == "completed" and value.returncode == 0 and value.cleanup_complete else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "worker"))
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    if sys.flags.optimize:
        raise ValueError("optimized_controller_refused")
    return (run_owned if args.action == "run" else worker)(args.proposal, args.authorization, args.evidence)


if __name__ == "__main__":
    raise SystemExit(main())
