"""Opt-in original synthetic transfer controls; no weights, SDK or story writes.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receipt_real_candidate as r
import receipt_transfer_contract as c

q, e = r.q, r.environment
SCOPE = "receipt_synthetic_transfer_probe"
REQUEST = b"receipt-transfer-probe-v1\n"
STREAM_REQUEST = b"receipt-transfer-source-v1\n"
SOURCE_NAME = "locallore-transfer-fixture-v1.bin"
SUMMARY_KEYS = {"version", "mode", "source_bytes", "source_verified", "client_returncode",
                "remote_exit_status_known", "destination_verified", "client_elapsed_ms"}
SOURCE_FILES = (*r.SOURCE_FILES, "benchmarks/receipt_transfer_probe.py",
    "benchmarks/receipt_transfer_contract.py", "scripts/tests/test_receipt_transfer_contract.py",
    "scripts/tests/test_receipt_transfer_probe.py", "docs/native/RECEIPT_TRANSFER_PROBE_PROTOCOL.md",
    "docs/native/RECEIPT_TRANSFER_SOURCE_RESEARCH_2026-10-25.md")


def mode_value(mode):
    assert type(mode) is str and mode in c.MODES
    return mode


def stream_mode_value(mode):
    assert type(mode) is str and mode in (*c.MODES, "SHELL_BINARY")
    return mode


def source_path(source):
    assert type(source) is dict and set(source) == {"path", "bytes", "sha256"}
    assert type(source["path"]) is str
    path = Path(source["path"])
    assert path.is_absolute() and path.resolve() == path and path.name == SOURCE_NAME
    for part in (path, *path.parents):
        info = part.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400
    assert type(source["bytes"]) is int and source["bytes"] == c.SOURCE_BYTES
    assert source["sha256"] == c.SOURCE_SHA256
    assert path.is_file() and path.stat().st_size == c.SOURCE_BYTES
    return path


def create_source(output):
    """Explicit create-only host fixture generation, never an import side effect."""
    output = Path(output)
    assert output.is_absolute() and output.name == SOURCE_NAME and not output.exists()
    e.safe_path(output.parent, directory=True)
    block = c.fixture_block(); assert len(block) == c.BLOCK_BYTES
    digest = hashlib.sha256()
    with output.open("xb", buffering=0) as stream:
        for _ in range(c.SOURCE_BYTES // c.BLOCK_BYTES):
            assert stream.write(block) == len(block)
            digest.update(block)
        stream.flush(); os.fsync(stream.fileno())
    assert digest.hexdigest() == c.SOURCE_SHA256
    return source_path({"path": str(output), "bytes": c.SOURCE_BYTES, "sha256": c.SOURCE_SHA256})


def validate_proposal(value):
    assert type(value) is dict and set(value) == q.PROPOSAL_KEYS | {"source", "preflight"}
    assert value["scope"] == SCOPE
    base = {key: value[key] for key in q.PROPOSAL_KEYS}; base["scope"] = "receipt_setup_qualification"
    q.validate_proposal(base)
    assert all(str((q.ROOT / name).resolve()) in value["bindings"] for name in SOURCE_FILES)
    assert not os.environ.get("ADB_SERVER_SOCKET") and not os.environ.get("ANDROID_ADB_SERVER_PORT")
    environment = q.contract.strict_json(Path(value["environment_proposal_path"]).read_bytes())
    assert environment["memory_mib"] == 8192 and environment["cores"] == 4
    assert environment["host_available_memory_min"] == 12 * r.GIB
    source_path(value["source"])
    assert str(Path(value["source"]["path"]).resolve()) not in value["bindings"]
    # Reuse the actual, original preflight proof parser, without forging a
    # candidate grant or describing the synthetic bytes as a model.
    previous = value["preflight"]
    assert type(previous) is dict and set(previous) == {"result", "facts", "proof", "owned_result"}
    for item in previous.values():
        assert type(item) is dict and set(item) == {"path", "sha256"}
        path = Path(item["path"])
        assert path.is_absolute() and value["bindings"].get(str(path.resolve())) == item["sha256"]
    result = q.contract.strict_json(Path(previous["result"]["path"]).read_bytes())
    owned = q.contract.strict_json(Path(previous["owned_result"]["path"]).read_bytes())
    assert result["scope"] == r.SCOPE and result["phase"] == "preflight" and result["status"] == "observed"
    assert result["failure"] is None and result["clients_cleaned"] is True and result["owner_live"] is True
    assert result["running_sha256"] == value["running_sha256"]
    assert type(result["instrumentation_commands"]) is int and result["instrumentation_commands"] == 1
    assert owned["status"] == "child_exited"
    assert type(owned["worker_returncode"]) is int and owned["worker_returncode"] == 0
    assert owned["cleanup_complete"] is True and owned["output_capture_complete"] is True
    facts = q.contract.strict_json(Path(previous["facts"]["path"]).read_bytes())
    assert facts["packages"] == q.APK_HASHES and type(facts["uid_map"]) is dict and set(facts["uid_map"]) == {q.APP, q.TEST}
    for uid in facts["uid_map"].values(): r.integer(uid, 10000, 2 ** 31 - 1)
    assert len(set(facts["uid_map"].values())) == 2
    assert facts["processes"] == {"target": [], "test_helper": []}
    proof = r.parse_proof(Path(previous["proof"]["path"]).read_bytes(), "SOURCE_PREFLIGHT", facts["uid_map"][q.APP])
    assert result["result"]["proof"] == proof and result["result"]["after"] == facts
    return True


def authorize(proposal_path, authorization_path, evidence):
    raw = Path(proposal_path).read_bytes(); value = q.contract.strict_json(raw)
    auth = q.contract.strict_json(Path(authorization_path).read_bytes())
    assert type(auth) is dict and set(auth) == {"version", "proposal_sha256", "allow_device_calls",
                                             "root_go_pending", "allow_synthetic_copy"}
    assert type(auth["version"]) is int and auth["version"] == 1 and auth["proposal_sha256"] == q.sha(raw)
    assert auth["allow_device_calls"] is True and auth["root_go_pending"] is False and auth["allow_synthetic_copy"] is True
    assert Path(value["evidence_root"]).resolve() == Path(evidence).resolve()
    validate_proposal(value)
    return value


def parse_summary(raw, mode):
    stream_mode_value(mode)
    assert type(raw) is bytes and 0 < len(raw) <= 4096
    value = q.contract.strict_json(raw)
    assert type(value) is dict and set(value) == SUMMARY_KEYS
    assert type(value["version"]) is int and value["version"] == 1 and value["mode"] == mode
    expected = len(c.BINARY_PAYLOAD) if mode == "SHELL_BINARY" else c.SOURCE_BYTES
    assert type(value["source_bytes"]) is int and value["source_bytes"] == expected
    assert value["source_verified"] is True
    assert type(value["client_returncode"]) is int and value["client_returncode"] == 0
    assert value["remote_exit_status_known"] is False and value["destination_verified"] is False
    r.integer(value["client_elapsed_ms"], 0, 180000)
    return value


def stream_worker(proposal_path, authorization_path, evidence):
    raw = sys.stdin.buffer.read(128)
    assert raw.startswith(STREAM_REQUEST)
    match = re.fullmatch(rb"([A-Z][A-Z_0-9]{0,15})\n([1-9][0-9]{4,9})\n", raw[len(STREAM_REQUEST):])
    assert match
    mode, uid = stream_mode_value(match[1].decode("ascii")), int(match[2])
    value = authorize(proposal_path, authorization_path, evidence)
    return stream_authorized(value, mode, uid, proposal_path, authorization_path, evidence)


def stream_authorized(value, mode, uid, proposal_path, authorization_path, evidence):
    trace = None
    try:
        expected = len(c.BINARY_PAYLOAD) if mode == "SHELL_BINARY" else value["source"]["bytes"]
        trace = r.source_trace.SourceStreamTrace(expected)
    except BaseException:
        pass
    try:
        status = _stream_authorized(value, mode, uid, proposal_path, authorization_path, evidence, trace)
    except BaseException:
        r._stream_trace_emit(trace)
        raise
    if status != 0:
        r._stream_trace_emit(trace)
    return status


def _stream_authorized(value, mode, uid, proposal_path, authorization_path, evidence, trace):
    stream_mode_value(mode); r.integer(uid, 10000, 2 ** 31 - 1)
    lease = q.open_lease(value); lease.check()
    cohort = Path(evidence) / "cohort"; stem = "stream-" + mode.lower()
    parent_path = cohort / (stem + "-parent-v1.json")
    parent = q.contract.strict_json(parent_path.read_bytes())
    assert set(parent) == {"version", "parent", "proposal_sha256", "authorization_sha256", "mode", "uid", "facts_sha256", "deadline_epoch"}
    assert type(parent["version"]) is int and parent["version"] == 1
    assert os.getppid() == parent["parent"]["pid"]
    assert parent["parent"] == e.process_identity(parent["parent"]["pid"])
    assert parent["parent"]["executable"].lower() == str(Path(sys.executable)).lower()
    assert parent["proposal_sha256"] == q.sha(Path(proposal_path).read_bytes())
    assert parent["authorization_sha256"] == q.sha(Path(authorization_path).read_bytes())
    assert parent["mode"] == mode and type(parent["uid"]) is int and parent["uid"] == uid
    assert type(parent["deadline_epoch"]) in (int, float) and 0 < parent["deadline_epoch"] - time.time() <= 180
    prior = "continued-before" if mode == c.MODES[0] else "after-" + (
        "dd-1m" if mode == "SHELL_BINARY" else c.MODES[c.MODES.index(mode) - 1].lower().replace("_", "-"))
    fact_path = cohort / (prior + "-facts.json")
    assert q.sha(fact_path.read_bytes()) == parent["facts_sha256"]
    facts = q.contract.strict_json(fact_path.read_bytes())
    assert facts["packages"] == q.APK_HASHES and facts["uid_map"][q.APP] == uid
    assert facts["processes"] == {"target": [], "test_helper": []}
    assert r.integer(facts["userdata"]["available_bytes"]) >= c.SOURCE_BYTES + q.contract.USERDATA_FLOOR
    if mode == "SHELL_CAT":
        c.parse_binary_proof((cohort / "shell-binary-proof.raw.txt").read_bytes(), uid)
    q.write_json(cohort / (stem + "-worker-claimed-v1.json"), {"version": 1,
        "parent_sha256": q.sha(parent_path.read_bytes()), "proposal_sha256": q.sha(Path(proposal_path).read_bytes()),
        "worker": e.process_identity(os.getpid())})
    observe = r._stream_trace_observe
    observe(trace, "phase", r.source_trace.StreamPhase.SOURCE_OPEN)
    metadata = value["source"]
    if mode == "SHELL_BINARY":
        source = cohort / "shell-binary-source-v1.bin"
        # Fixed original bytes in a create-only regular file, inside the same
        # owned worker as the large copies. No pipe-vs-file qualification gap.
        with source.open("xb", buffering=0) as generated:
            assert generated.write(c.BINARY_PAYLOAD) == len(c.BINARY_PAYLOAD)
            generated.flush(); os.fsync(generated.fileno())
        metadata = {"bytes": len(c.BINARY_PAYLOAD), "sha256": c.BINARY_SHA256}
    else:
        source = source_path(metadata)
    operation = ["shell", "-T", "-e", "none"] if mode in ("SHELL_CAT", "SHELL_BINARY") else ["exec-in"]
    command = c.binary_write_command(uid) if mode == "SHELL_BINARY" else c.write_command(uid, mode)
    argv = [value["adb_path"], "-H", "127.0.0.1", "-P", "5037", "-s", lease.descriptor["serial"], *operation, shlex.join(command)]
    with source.open("rb", buffering=0) as stream:
        before = os.fstat(stream.fileno())
        observe(trace, "phase", r.source_trace.StreamPhase.SOURCE_HASH)
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""): digest.update(block)
        assert before.st_size == metadata["bytes"] and digest.hexdigest() == metadata["sha256"]
        observe(trace, "source_verified")
        stream.seek(0); lease.check()
        assert os.getppid() == parent["parent"]["pid"]
        assert parent["parent"] == e.process_identity(parent["parent"]["pid"])
        observe(trace, "phase", r.source_trace.StreamPhase.CLIENT)
        remaining = parent["deadline_epoch"] - time.time() - 5; assert remaining > 0
        timeout = min(150, remaining)
        observe(trace, "client_start", math.ceil(timeout * 1000))
        started = time.monotonic()
        try:
            result = subprocess.run(argv, stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW,
                env={key: item for key, item in os.environ.items() if key != "TERM"})
        except subprocess.TimeoutExpired:
            observe(trace, "client_timeout"); r._stream_trace_position(trace, stream)
            raise
        elapsed = int((time.monotonic() - started) * 1000)
        observe(trace, "client_return", result.returncode); r._stream_trace_position(trace, stream)
        observe(trace, "phase", r.source_trace.StreamPhase.SOURCE_POSTCHECK)
        after = os.fstat(stream.fileno())
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    observe(trace, "phase", r.source_trace.StreamPhase.LEASE_POSTCHECK)
    lease.check(); r.integer(elapsed, 0, 180000)
    observe(trace, "phase", r.source_trace.StreamPhase.COMPLETE)
    print(json.dumps({"version": 1, "mode": mode, "source_bytes": before.st_size, "source_verified": True,
        "client_returncode": result.returncode, "remote_exit_status_known": False, "destination_verified": False,
        "client_elapsed_ms": elapsed}))
    return 0 if result.returncode == 0 else 2


class ProcessBoundary:
    def __init__(self):
        self.next = 0
        self.refused = False

    def observe(self, raw, uids, *, label, stage, methods):
        try:
            labels = ("continued-before", *("after-" + mode.lower().replace("_", "-") for mode in c.MODES))
            assert not self.refused and self.next < len(labels)
            assert (label, stage, methods) == (labels[self.next], "before" if self.next == 0 else "after", 0)
            assert set(uids) == {q.APP, q.TEST}
            parsed = q.contract.parse_processes(raw, uids, {})
            assert parsed == {"passive": [], "owned": []}
            self.next += 1
            return {"target": [], "test_helper": []}
        except BaseException:
            self.refused = True
            raise


class Owner(q.Owner):
    instrumentation_steps = ()

    def __init__(self, value, lease):
        super().__init__(value, lease)
        facts = q.contract.strict_json(Path(value["preflight"]["facts"]["path"]).read_bytes())
        self.uid_map, self.volume = facts["uid_map"], facts["volume"]
        self.process_boundary = ProcessBoundary()
        self.until = time.monotonic() + 870
        self.proposal_path = self.authorization_path = None
        self.attempted, self.verified = [], []
        self.created = False
        self.binary_verified = False
        self.shell_gate_attempted = False
        self.binary_stream_attempted = False

    def dispatch(self, args, deadline=15, cap=65536):
        if self.stage == "probe-root":
            assert not self.created and not self.attempted and not self.verified
            assert args == ["shell", shlex.join(c.create_command(self.uid_map[q.APP]))]
            self.created = True
        elif self.stage == "binary-proof":
            assert not self.binary_verified and self.verified == ["CAT", "DD_1M"]
            assert args == ["shell", shlex.join(c.binary_proof_command(self.uid_map[q.APP]))]
        elif self.stage.startswith("proof-"):
            mode = self.stage[len("proof-"):]; mode_value(mode)
            assert self.attempted == [*self.verified, mode]
            assert args == ["shell", shlex.join(c.proof_command(self.uid_map[q.APP], mode))]
        else:
            return super().dispatch(args, deadline, cap)
        assert self.clean; self.check_owner()
        return self._dispatch_checked(args, deadline, cap)

    def transfer(self, mode):
        stream_mode_value(mode)
        assert self.created and self.clean and self.methods == 0
        if mode == "SHELL_BINARY":
            assert self.stage == "shell-gate-binary" and self.shell_gate_attempted and not self.binary_stream_attempted
            assert self.attempted == self.verified == ["CAT", "DD_1M"] and not self.binary_verified
            self.binary_stream_attempted = True
        else:
            assert self.stage == "source-stream"
            assert self.attempted == self.verified and mode == c.MODES[len(self.attempted)]
            assert mode != "SHELL_CAT" or self.binary_verified
            self.attempted.append(mode)  # Consumed even if a subsequent gate refuses.
        self.check_owner(); self.count += 1
        stem = self.commands / ("command-%04d" % self.count)
        remaining = self.until - time.monotonic(); assert remaining > 0
        prior = "continued-before" if mode == c.MODES[0] else "after-" + self.verified[-1].lower().replace("_", "-")
        facts = self.directory / (prior + "-facts.json")
        try:
            q.write_json(self.directory / ("stream-" + mode.lower() + "-parent-v1.json"), {"version": 1,
                "parent": e.process_identity(os.getpid()), "proposal_sha256": q.sha(Path(self.proposal_path).read_bytes()),
                "authorization_sha256": q.sha(Path(self.authorization_path).read_bytes()), "mode": mode,
                "uid": self.uid_map[q.APP], "facts_sha256": q.sha(facts.read_bytes()),
                "deadline_epoch": time.time() + min(180, remaining)})
            result = q.host.run_process([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "_stream",
                "--proposal", str(self.proposal_path), "--authorization", str(self.authorization_path),
                "--evidence", self.proposal["evidence_root"]],
                request=STREAM_REQUEST + mode.encode("ascii") + b"\n" + str(self.uid_map[q.APP]).encode("ascii") + b"\n",
                deadline=min(180, remaining), max_output=4096)
            self.clean &= result.cleanup_complete is True
            with stem.with_suffix(".stdout.bin").open("xb") as stream:
                stream.write(result.stdout); stream.flush(); os.fsync(stream.fileno())
            q.write_json(stem.with_suffix(".json"), {"index": self.count, "stage": self.stage, "mode": mode,
                "transport": "file-backed-stdin", "source_kind": "original_synthetic", "status": result.status,
                "returncode": result.returncode, "elapsed_ms": result.elapsed_ms,
                "cleanup_complete": result.cleanup_complete, "stdout_bytes": len(result.stdout),
                "stdout_sha256": q.sha(result.stdout), "stderr_bytes": result.stderr_bytes})
        except BaseException:
            self.clean = False
            raise
        self.check_owner()
        assert self.clean and result.status == "completed" and result.returncode == 0
        return parse_summary(result.stdout, mode)

    def shell_gate(self):
        """Fixed protocol and binary controls before the candidate large transfer."""
        assert self.stage == "shell-gate" and self.verified == ["CAT", "DD_1M"]
        assert self.attempted == self.verified and not self.binary_verified and "TERM" not in os.environ
        assert not self.shell_gate_attempted
        self.shell_gate_attempted = True
        prefix = [self.proposal["adb_path"], "-H", "127.0.0.1", "-P", "5037", "-s", self.serial]
        def control(args, expected, request=b""):
            assert self.clean; self.check_owner(); self.count += 1
            stem = self.commands / ("command-%04d" % self.count)
            remaining = self.until - time.monotonic(); assert remaining > 0
            try:
                result = q.host.run_process([*prefix, *args], request=request, deadline=min(10, remaining), max_output=4096)
                self.clean &= result.cleanup_complete is True
                with stem.with_suffix(".stdout.bin").open("xb") as stream:
                    stream.write(result.stdout); stream.flush(); os.fsync(stream.fileno())
                q.write_json(stem.with_suffix(".json"), {"index": self.count, "stage": self.stage, "args": args,
                    "status": result.status, "returncode": result.returncode, "elapsed_ms": result.elapsed_ms,
                    "cleanup_complete": result.cleanup_complete, "stdout_bytes": len(result.stdout),
                    "stdout_sha256": q.sha(result.stdout), "stderr_bytes": result.stderr_bytes})
            except BaseException:
                self.clean = False
                raise
            self.check_owner()
            assert self.clean and result.status == "completed" and result.returncode == expected
            return result.stdout
        raw = control(["features"], 0)
        lines = q.normalized(raw, 4096).splitlines()
        assert lines and len(lines) <= 128 and len(set(lines)) == len(lines)
        assert all(re.fullmatch(r"[A-Za-z0-9_]{1,80}", line) for line in lines) and "shell_v2" in lines
        for code in (42, 0):
            op = ("run-as", q.APP, "sh", "-c", "test $(id -u) -eq " + str(self.uid_map[q.APP]) + " && exit " + str(code))
            assert control(["shell", "-T", "-e", "none", shlex.join(op)], code) == b""
        self.stage = "shell-gate-binary"
        binary_transfer = self.transfer("SHELL_BINARY")
        q.write_json(self.directory / "shell-binary-transfer-v1.json", binary_transfer)
        self.stage = "binary-proof"
        raw = self.shell(c.binary_proof_command(self.uid_map[q.APP]), deadline=10, cap=1024)
        with (self.directory / "shell-binary-proof.raw.txt").open("xb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        proof = c.parse_binary_proof(raw, self.uid_map[q.APP])
        q.write_json(self.directory / "shell-binary-proof-v1.json", proof)
        self.binary_verified = True


def run_cohort(owner):
    owner.stage = "before"
    before = owner.facts("continued-before", q.APK_HASHES)
    assert before["userdata"]["available_bytes"] >= len(c.MODES) * c.SOURCE_BYTES + q.contract.USERDATA_FLOOR
    owner.stage = "probe-root"
    assert owner.shell(c.create_command(owner.uid_map[q.APP]), cap=4096) == b""
    rows = []
    for mode in c.MODES:
        if mode == "SHELL_CAT":
            owner.stage = "shell-gate"; owner.shell_gate()
        owner.stage = "source-stream"; transfer = owner.transfer(mode)
        owner.stage = "proof-" + mode
        raw = owner.shell(c.proof_command(owner.uid_map[q.APP], mode), deadline=60, cap=1024)
        proof = c.parse_proof(raw, owner.uid_map[q.APP], mode)
        with (owner.directory / (mode.lower() + "-proof.raw.txt")).open("xb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        q.write_json(owner.directory / (mode.lower() + "-proof-v1.json"), proof)
        owner.verified.append(mode)
        owner.stage = "after"
        after = owner.facts("after-" + mode.lower().replace("_", "-"), q.APK_HASHES)
        rows.append({"mode": mode, "transfer": transfer, "proof": proof, "after": after})
    return {"before": before, "controls": rows, "model_copied": False, "sdk_invoked": False,
            "story_mutated": False, "physical_phone_qualified": False}


def worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(64) == REQUEST
    os.environ.pop("TERM", None)  # Scoped probe child environment; production is untouched.
    value = authorize(proposal_path, authorization_path, evidence)
    owner = Owner(value, q.open_lease(value)); owner.proposal_path, owner.authorization_path = proposal_path, authorization_path
    result, failure = None, None
    try:
        result = run_cohort(owner)
    except BaseException:
        failure = "receipt_synthetic_transfer_stopped"
    body = {"version": 1, "scope": SCOPE, "status": "observed" if failure is None else "stopped",
        "failure": failure, "stage": owner.stage, "clients_cleaned": owner.clean, "owner_live": owner.owner_live,
        "command_count": owner.count, "instrumentation_commands": owner.methods, "installs": owner.installs,
        "attempted": owner.attempted, "verified": owner.verified, "result": result}
    q.write_json(owner.directory / "result-v1.json", body)
    print(json.dumps({key: body[key] for key in body if key != "result"}))
    return 0 if failure is None and owner.clean and owner.owner_live else 2


def run_owned(proposal_path, authorization_path, evidence):
    value = authorize(proposal_path, authorization_path, evidence); lease = q.open_lease(value); lease.check()
    assert lease.descriptor["deadline_epoch"] - time.time() >= 920
    root = Path(evidence); driver = root / "driver"; driver.mkdir(exist_ok=False)
    q.write_json(root / "receipt-owned-start-v1.json", {"version": 1, "deadline_seconds": 900,
        "proposal_sha256": q.sha(Path(proposal_path).read_bytes()), "authorization_sha256": q.sha(Path(authorization_path).read_bytes())})
    result = e.supervise([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "worker",
        "--proposal", str(proposal_path), "--authorization", str(authorization_path), "--evidence", str(evidence)],
        REQUEST, driver, 900, lambda child: True)
    q.write_json(root / "receipt-owned-result-v1.json", result); print(json.dumps(result))
    return 0 if result["status"] == "child_exited" and result["worker_returncode"] == 0 and result["cleanup_complete"] and result["output_capture_complete"] else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create-source", "run", "worker", "_stream"))
    for name in ("proposal", "authorization", "evidence", "output"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args(argv)
    if sys.flags.optimize: raise ValueError("optimized_controller_refused")
    if args.action == "create-source":
        assert args.output is not None and args.proposal is args.authorization is args.evidence is None
        create_source(args.output); return 0
    assert args.output is None and all(item is not None for item in (args.proposal, args.authorization, args.evidence))
    if args.action == "_stream":
        try: return stream_worker(args.proposal, args.authorization, args.evidence)
        except BaseException:
            print(json.dumps({"status": "stream_failed", "remote_exit_status_known": False})); return 2
    return (run_owned if args.action == "run" else worker)(args.proposal, args.authorization, args.evidence)


if __name__ == "__main__":
    raise SystemExit(main())
