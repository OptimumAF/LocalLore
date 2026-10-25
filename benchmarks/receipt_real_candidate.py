"""Fixed receipt-candidate staging/import/SDK/reopen experiment, disabled by default.

Preflight transfers only an original 61-byte probe. A separate candidate scope
requires new destination consent before local weights or SDK calls. No download.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receipt_setup_qualification as q
import receipt_avd_environment as environment
import litert_worker_trace as worker_trace

GIB = 1024 ** 3
SCOPE = "receipt_real_candidate"
REQUEST = b"receipt-real-candidate-v1\n"
STREAM_REQUEST = b"receipt-real-source-stream-v1\n"
MODEL_BYTES = 2_588_147_712
MODEL_SHA = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
PROBE_BYTES = 61
PROBE_SHA = "a4ab41067238a10078cec646fcf00a952c1c58511661d5d8dc4632b37ea017af"
PROBE_PATH = q.ROOT / "benchmarks/fixtures/receipt_real_source_probe_v1.txt"
SOURCE_ROOT = "no_backup/receipt-real-source-v1"
PROOF_ROOT = "no_backup/receipt-real-proof-v1"
PHASES = {
    "SOURCE_PREFLIGHT": ("source-preflight", "ReceiptRealSourcePreflightTest", "verifiesTrustedSourceBeforeModelCopy", 30_000, frozenset((
        "build_identity_exact", "source_context_confined", "source_owner_exact", "probe_exact", "source_whitelist_exact",
        "staged_model_absent", "candidate_access_receipt", "candidate_roots_absent", "candidate_installed_null_noncreating",
        "memory_eligible", "userdata_copy_capacity", "external_import_capacity"))),
    "IMPORT": ("import", "ReceiptRealImportTest", "importsFixedRealCandidateThroughProductionSetup", 150_000, frozenset((
        "source_context_confined", "source_owner_probe_exact", "source_whitelist_exact", "source_model_regular_uid",
        "source_fullhash_exact", "source_verify_closed_once", "candidate_access_receipt", "preaccept_runtime_refused",
        "setup_missing_before_import", "import_source_off_main_closed_once", "import_source_exact_bytes", "setup_ready_after_import",
        "accepted_full_recheck", "accepted_receipt_owner_exact", "memory_eligible", "capacity_eligible"))),
    "PLAY": ("play", "ReceiptRealPlayTest", "commitsOneGuardedRealSdkGift", 170_000, frozenset((
        "memory_eligible", "accepted_full_recheck", "runtime_guard_passed", "production_transport_local", "native_worker_off_main",
        "initial_revision_zero", "fixed_free_text_submitted_once", "prepared_after_known_worker_close",
        "accepted_post_sdk_full_recheck", "canonical_revision_one", "canonical_given_to_mira", "canonical_single_receipt",
        "local_profile_exact", "candidate_owner_retained", "native_handle_closed"))),
    "REOPEN": ("reopen", "ReceiptRealReopenTest", "reopensReceiptAndGiftAfterProcessRestart", 120_000, frozenset((
        "prior_play_proof_exact", "process_identity_changed", "source_unopened", "candidate_access_receipt", "accepted_full_recheck",
        "runtime_guard_passed", "setup_ready_after_reopen", "production_transport_local", "no_free_text_call", "canonical_revision_one",
        "canonical_gift_receipt_unchanged", "native_handle_closed", "memory_eligible"))),
}
COMMON_KEYS = frozenset(("version", "phase", "pid", "start", "uid", "process", "model_bytes", "model_sha256",
    "source_verify_opened", "source_verify_closed", "source_verify_bytes", "source_import_opened", "source_import_closed",
    "source_import_bytes", "sdk_invoked", "publication_native_invoked", "elapsed_ms", "userdata_free_before", "userdata_free_after",
    "external_free_before", "external_free_after", "memory_total_bytes", "memory_available_before", "memory_available_after", "checks"))
EXTRA_KEYS = frozenset(("phase", "source", "preflight", "human_consent"))
SOURCE_FILES = (*q.SOURCE_FILES, "benchmarks/receipt_real_candidate.py", "scripts/tests/test_receipt_real_candidate.py",
    "benchmarks/litert_worker_trace.py", "scripts/tests/test_litert_worker_trace.py",
    "apps/android/app/src/litert/java/org/locallore/app/LiteRtWorkerTrace.kt",
    "apps/android/app/src/litertTest/java/org/locallore/app/LiteRtWorkerTraceTest.kt",
    "apps/android/app/src/modelReceipt/java/org/locallore/app/ReceiptWorkerFailureReporter.kt",
    "apps/android/app/src/modelReceiptTest/java/org/locallore/app/ReceiptWorkerFailureReporterTest.kt",
    "docs/native/LITERT_WORKER_TRACE_CONTRACT.md",
    "docs/native/LITERT_WORKER_TRACE_V2_CONTRACT.md",
    "scripts/tests/test_receipt_real_stream_guards.py",
    "apps/android/app/src/modelReceiptAndroidTest/java/org/locallore/app/ReceiptRealCandidateTest.kt",
    "scripts/audit_apk.py", "scripts/tests/test_audit_apk.py", "scripts/tests/test_receipt_avd_environment.py",
    "benchmarks/fixtures/receipt_real_source_probe_v1.txt", "docs/native/RECEIPT_REAL_CANDIDATE_PROTOCOL.md")


def selection(phase):
    assert phase in PHASES
    return ("am", "instrument", "-w", "-r", "-e", "class", "org.locallore.app." + PHASES[phase][1],
            q.TEST + "/androidx.test.runner.AndroidJUnitRunner")


def parse_runner(raw, phase):
    assert phase in PHASES
    return q._parse_selected_instrumentation(raw, "org.locallore.app." + PHASES[phase][1], frozenset((PHASES[phase][2],)))


def integer(value, low=0, high=2 ** 63 - 1):
    assert type(value) is int and low <= value <= high
    return value


def parse_proof(raw, phase, uid):
    assert phase in PHASES
    assert type(raw) is bytes and 0 < len(raw) <= 4096
    integer(uid, 10000, 2 ** 31 - 1)
    value = q.contract.strict_json(raw)
    extras = set()
    if phase != "SOURCE_PREFLIGHT":
        prior = {"IMPORT": "preflight", "PLAY": "import", "REOPEN": "play"}[phase]
        extras |= {"prior_pid", "prior_start", "prior_" + prior + "_sha256"}
    if phase in ("PLAY", "REOPEN"):
        extras |= {"revision", "receipt_count", "receipt_sha256"}
    if phase == "PLAY": extras |= {"repairs", "fallback"}
    assert type(value) is dict and set(value) == COMMON_KEYS | extras
    assert type(value["version"]) is int and value["version"] == 1 and value["phase"] == phase
    integer(value["pid"], 1, 2 ** 31 - 1); integer(value["start"], 0)
    assert type(value["uid"]) is int and value["uid"] == uid and value["process"] == q.APP
    assert type(value["model_bytes"]) is int and value["model_bytes"] == MODEL_BYTES and value["model_sha256"] == MODEL_SHA
    for kind in ("verify", "import"):
        for suffix in ("opened", "closed", "bytes"):
            expected = (MODEL_BYTES if suffix == "bytes" else 1) if phase == "IMPORT" else 0
            assert type(value["source_" + kind + "_" + suffix]) is int and value["source_" + kind + "_" + suffix] == expected
    assert value["sdk_invoked"] is (phase == "PLAY") and value["publication_native_invoked"] is False
    integer(value["elapsed_ms"], 0, PHASES[phase][3])
    total = integer(value["memory_total_bytes"], 7 * GIB, 8 * GIB)
    integer(value["memory_available_before"], 4 * GIB, total)
    integer(value["memory_available_after"], 0, total)
    for when in ("before", "after"):
        minimum = q.contract.USERDATA_FLOOR + (MODEL_BYTES if phase == "SOURCE_PREFLIGHT" else 0)
        integer(value["userdata_free_" + when], minimum)
        minimum_external = 2 * GIB + (MODEL_BYTES if phase == "SOURCE_PREFLIGHT" or phase == "IMPORT" and when == "before" else 0)
        integer(value["external_free_" + when], minimum_external)
    checks = value["checks"]
    assert type(checks) is dict and set(checks) == PHASES[phase][4] and all(check is True for check in checks.values())
    if phase != "SOURCE_PREFLIGHT":
        integer(value["prior_pid"], 1, 2 ** 31 - 1); integer(value["prior_start"], 0)
        assert type(value["prior_" + prior + "_sha256"]) is str and re.fullmatch(r"[a-f0-9]{64}", value["prior_" + prior + "_sha256"])
    if phase in ("PLAY", "REOPEN"):
        assert type(value["revision"]) is int and value["revision"] == 1
        assert type(value["receipt_count"]) is int and value["receipt_count"] == 1
        assert type(value["receipt_sha256"]) is str and re.fullmatch(r"[a-f0-9]{64}", value["receipt_sha256"])
    if phase == "PLAY":
        integer(value["repairs"], 0, 1); assert type(value["fallback"]) is bool
    return value


def link_proofs(prior, prior_raw, current):
    assert q.contract.strict_json(prior_raw) == prior
    wanted = {"IMPORT": "SOURCE_PREFLIGHT", "PLAY": "IMPORT", "REOPEN": "PLAY"}[current["phase"]]
    assert prior["phase"] == wanted
    key = {"SOURCE_PREFLIGHT": "preflight", "IMPORT": "import", "PLAY": "play"}[wanted]
    assert (current["prior_pid"], current["prior_start"], current["prior_" + key + "_sha256"]) == (prior["pid"], prior["start"], q.sha(prior_raw))
    assert (current["uid"], current["process"]) == (prior["uid"], prior["process"])
    if current["phase"] == "REOPEN":
        assert (current["pid"], current["start"]) != (prior["pid"], prior["start"])
        assert current["receipt_sha256"] == prior["receipt_sha256"]
    return True


def source_path(source, phase):
    """Validate closed identity/path/size. Full contents are hashed on the held transfer FD."""
    assert type(source) is dict and set(source) == {"path", "bytes", "sha256"}
    path = Path(source["path"])
    assert path.is_absolute() and path.resolve() == path
    for part in (path, *path.parents):
        info = part.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400
    expected = (PROBE_BYTES, PROBE_SHA) if phase == "preflight" else (MODEL_BYTES, MODEL_SHA)
    assert type(source["bytes"]) is int and (source["bytes"], source["sha256"]) == expected
    assert path.is_file() and path.stat().st_size == expected[0]
    if phase == "preflight": assert path == PROBE_PATH.resolve()
    return path


def validate_proposal(value):
    assert type(value) is dict and set(value) == q.PROPOSAL_KEYS | EXTRA_KEYS and value["scope"] == SCOPE
    assert value["phase"] in ("preflight", "candidate")
    base = {key: value[key] for key in q.PROPOSAL_KEYS}; base["scope"] = "receipt_setup_qualification"
    q.validate_proposal(base)
    assert all(str((q.ROOT / name).resolve()) in value["bindings"] for name in SOURCE_FILES)
    assert not os.environ.get("ADB_SERVER_SOCKET") and not os.environ.get("ANDROID_ADB_SERVER_PORT")
    env = q.contract.strict_json(Path(value["environment_proposal_path"]).read_bytes())
    assert env["memory_mib"] == 8192 and env["host_available_memory_min"] == 12 * GIB
    assert type(env["cores"]) is int and env["cores"] in (2, 4)
    source_path(value["source"], value["phase"])
    if value["phase"] == "preflight":
        assert value["preflight"] is None and value["human_consent"] is None
    else:
        # A weight file is independently stream-hashed, never loaded by the
        # generic read_bytes binding validator or copied into an input archive.
        assert str(Path(value["source"]["path"]).resolve()) not in value["bindings"]
        consent = value["human_consent"]
        assert type(consent) is dict and set(consent) == {"reference", "action", "model_sha256", "destination_package"}
        assert type(consent["reference"]) is str and re.fullmatch(r"[A-Za-z0-9_:-]{1,128}", consent["reference"])
        assert consent["action"] == "local_copy_and_sdk_fresh_receipt_emulator" and consent["model_sha256"] == MODEL_SHA
        assert consent["destination_package"] == q.APP
        previous = value["preflight"]
        assert type(previous) is dict and set(previous) == {"result", "facts", "proof", "owned_result"}
        for item in previous.values():
            assert type(item) is dict and set(item) == {"path", "sha256"}
            path = Path(item["path"]); assert path.is_absolute() and value["bindings"].get(str(path.resolve())) == item["sha256"]
        result = q.contract.strict_json(Path(previous["result"]["path"]).read_bytes())
        owned = q.contract.strict_json(Path(previous["owned_result"]["path"]).read_bytes())
        assert result["scope"] == SCOPE and result["phase"] == "preflight" and result["status"] == "observed"
        assert result["failure"] is None and result["clients_cleaned"] is True and result["owner_live"] is True
        assert result["running_sha256"] == value["running_sha256"] and result["instrumentation_commands"] == 1
        assert owned["status"] == "child_exited" and owned["worker_returncode"] == 0
        assert owned["cleanup_complete"] is True and owned["output_capture_complete"] is True
        facts = q.contract.strict_json(Path(previous["facts"]["path"]).read_bytes())
        assert facts["packages"] == q.APK_HASHES and set(facts["uid_map"]) == {q.APP, q.TEST}
        proof = parse_proof(Path(previous["proof"]["path"]).read_bytes(), "SOURCE_PREFLIGHT", facts["uid_map"][q.APP])
        assert result["result"]["proof"] == proof and result["result"]["after"] == facts
    return True


def authorize(proposal_path, authorization_path, evidence):
    raw = Path(proposal_path).read_bytes(); value = q.contract.strict_json(raw)
    auth = q.contract.strict_json(Path(authorization_path).read_bytes())
    assert type(auth) is dict and set(auth) == {"version", "proposal_sha256", "allow_device_calls", "root_go_pending", "allow_local_weight_copy", "allow_sdk_calls"}
    assert type(auth["version"]) is int and auth["version"] == 1 and auth["proposal_sha256"] == q.sha(raw)
    assert auth["allow_device_calls"] is True and auth["root_go_pending"] is False
    assert auth["allow_local_weight_copy"] is (value["phase"] == "candidate") and auth["allow_sdk_calls"] is (value["phase"] == "candidate")
    assert Path(value["evidence_root"]).resolve() == Path(evidence).resolve()
    validate_proposal(value)
    return value


def source_create(uid):
    integer(uid, 10000, 2 ** 31 - 1)
    script = "umask 077; test $(id -u) -eq " + str(uid) + " && "
    script += "if test -e no_backup || test -L no_backup; then test -d no_backup && test ! -L no_backup && test $(stat -c %u no_backup) -eq " + str(uid) + "; else mkdir no_backup; fi && "
    script += "test ! -e " + SOURCE_ROOT + " && test ! -L " + SOURCE_ROOT + " && mkdir " + SOURCE_ROOT
    script += " && (set -C; echo locallore-real-source-v1 > " + SOURCE_ROOT + "/source.owner)"
    return ("run-as", q.APP, "sh", "-c", script)


def source_write(uid, phase):
    integer(uid, 10000, 2 ** 31 - 1); assert phase in ("preflight", "candidate")
    name = "probe.txt" if phase == "preflight" else "model.litertlm"
    root = SOURCE_ROOT
    script = "umask 077; set -C; test $(id -u) -eq " + str(uid)
    script += " && test -d no_backup && test ! -L no_backup && test -d " + root + " && test ! -L " + root
    script += " && test $(stat -c %u " + root + ") -eq " + str(uid)
    script += " && test -f " + root + "/source.owner && test ! -L " + root + "/source.owner"
    script += " && test $(stat -c %u " + root + "/source.owner) -eq " + str(uid)
    script += " && test $(wc -c < " + root + "/source.owner) -eq 25"
    script += " && test \"$(cat " + root + "/source.owner)\" = locallore-real-source-v1"
    script += " && test ! -e " + root + "/" + name + " && test ! -L " + root + "/" + name
    script += " && cat > " + root + "/" + name
    return ("run-as", q.APP, "sh", "-c", script)


def stream_worker(proposal_path, authorization_path, evidence):
    raw = sys.stdin.buffer.read(128)
    assert raw.startswith(STREAM_REQUEST) and re.fullmatch(rb"[1-9][0-9]{4,9}\n", raw[len(STREAM_REQUEST):])
    uid = int(raw[len(STREAM_REQUEST):]); integer(uid, 10000, 2 ** 31 - 1)
    value = authorize(proposal_path, authorization_path, evidence); lease = q.open_lease(value); lease.check()
    cohort = Path(evidence) / "cohort"
    parent_path = cohort / "stream-parent-v1.json"
    parent = q.contract.strict_json(parent_path.read_bytes())
    assert set(parent) == {"version", "parent", "proposal_sha256", "authorization_sha256", "phase", "uid", "facts_sha256", "deadline_epoch"}
    assert type(parent["version"]) is int and parent["version"] == 1
    assert os.getppid() == parent["parent"]["pid"]
    assert parent["parent"] == environment.process_identity(parent["parent"]["pid"])
    assert parent["parent"]["executable"].lower() == str(Path(sys.executable)).lower()
    assert parent["proposal_sha256"] == q.sha(Path(proposal_path).read_bytes())
    assert parent["authorization_sha256"] == q.sha(Path(authorization_path).read_bytes())
    assert parent["phase"] == value["phase"] and type(parent["uid"]) is int and parent["uid"] == uid
    assert type(parent["deadline_epoch"]) in (int, float) and 0 < parent["deadline_epoch"] - time.time() <= 180
    fact_path = cohort / ("installed-facts.json" if value["phase"] == "preflight" else "continued-before-facts.json")
    assert q.sha(fact_path.read_bytes()) == parent["facts_sha256"]
    facts = q.contract.strict_json(fact_path.read_bytes())
    assert facts["packages"] == q.APK_HASHES and facts["uid_map"][q.APP] == uid and facts["processes"]["target"] == []
    required = value["source"]["bytes"] + q.contract.USERDATA_FLOOR
    assert integer(facts["userdata"]["available_bytes"]) >= required
    q.write_json(cohort / "stream-worker-claimed-v1.json", {"version": 1,
        "parent_sha256": q.sha(parent_path.read_bytes()), "proposal_sha256": q.sha(Path(proposal_path).read_bytes()),
        "worker": environment.process_identity(os.getpid())})
    source = source_path(value["source"], value["phase"])
    argv = [value["adb_path"], "-H", "127.0.0.1", "-P", "5037", "-s", lease.descriptor["serial"], "exec-in", shlex.join(source_write(uid, value["phase"]))]
    # The parent assigned this barrier worker to its Job before sending REQUEST.
    # The transfer child inherits that Job; model bytes never enter Python memory.
    with source.open("rb", buffering=0) as stream:
        before = os.fstat(stream.fileno())
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""): digest.update(block)
        assert before.st_size == value["source"]["bytes"] and digest.hexdigest() == value["source"]["sha256"]
        stream.seek(0)
        lease.check()
        assert os.getppid() == parent["parent"]["pid"]
        assert parent["parent"] == environment.process_identity(parent["parent"]["pid"])
        remaining = parent["deadline_epoch"] - time.time() - 5
        assert remaining > 0
        result = subprocess.run(argv, stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=min(150, remaining),
                                creationflags=subprocess.CREATE_NO_WINDOW)
        after = os.fstat(stream.fileno())
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    lease.check()
    print(json.dumps({"version": 1, "source_bytes": before.st_size, "source_verified": True, "client_returncode": result.returncode,
                      "remote_exit_status_known": False, "destination_verified": False}))
    return 0 if result.returncode == 0 else 2


def proof_command(phase, uid, ready=False):
    assert phase in PHASES; integer(uid, 10000, 2 ** 31 - 1); assert type(ready) is bool
    path = PROOF_ROOT + "/" + PHASES[phase][0] + ("-ready-v1.txt" if ready else "-v1.json")
    size = "-eq 0" if ready else "-gt 0"
    script = "test -d no_backup && test ! -L no_backup && test -d " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT
    script += " && test -f " + path + " && test ! -L " + path + " && test $(stat -c %u " + path + ") -eq " + str(uid)
    script += " && test $(wc -c < " + path + ") " + size + " && test $(wc -c < " + path + ") -le 4096 && cat " + path
    return ("run-as", q.APP, "sh", "-c", script)


class PreflightBoundary(q.ProcessBoundary):
    observations = (("before", "before", 0), ("installed", "installed", 0), ("after-preflight", "after", 1))


class ContinuedBoundary:
    def __init__(self, previous):
        assert set(previous) == {"target", "test_helper"} and previous["target"] == [] and len(previous["test_helper"]) <= 1
        self.helper = json.loads(json.dumps(previous["test_helper"]))
        self.retired = not self.helper; self.next = 0; self.refused = False
        # The no-UI source preflight can legitimately have no framework helper.
        # Only the first UI import, after its exact pass/proof, may bind one.
        self.bind_after_import = not self.helper

    def observe(self, raw, uids, *, label, stage, methods):
        try:
            assert not self.refused and self.next < 4
            expected = (("continued-before", "before", 0), ("after-import", "after", 1), ("after-play", "after", 2), ("after-reopen", "after", 3))[self.next]
            assert (label, stage, methods) == expected
            parsed = q.contract.parse_processes(raw, uids, {})
            assert parsed["passive"] == [] and len(parsed["owned"]) <= 1
            rows = parsed["owned"]; assert all(row["name"] == q.TEST for row in rows)
            if self.next == 1 and self.bind_after_import:
                self.helper = json.loads(json.dumps(rows))
                self.retired = not rows
                self.bind_after_import = False
            elif rows: assert not self.retired and rows == self.helper
            else: self.retired = True
            self.next += 1
            return {"target": [], "test_helper": [dict(row) for row in rows]}
        except BaseException:
            self.refused = True
            raise


class Owner(q.Owner):
    def __init__(self, value, lease):
        super().__init__(value, lease)
        self.proposal_path = self.authorization_path = None
        self.stream_attempted = False
        self.guest_cpu_check_attempted = False
        self.real_phase = value["phase"]
        phases = ("SOURCE_PREFLIGHT",) if self.real_phase == "preflight" else ("IMPORT", "PLAY", "REOPEN")
        self.instrumentation_steps = tuple((selection(phase), "instrument-" + phase, index) for index, phase in enumerate(phases))
        self.until = time.monotonic() + (165 if self.real_phase == "preflight" else 870)
        if self.real_phase == "preflight": self.process_boundary = PreflightBoundary()
        else:
            facts = q.contract.strict_json(Path(value["preflight"]["facts"]["path"]).read_bytes())
            self.uid_map = facts["uid_map"]; self.volume = facts["volume"]
            self.process_boundary = ContinuedBoundary(facts["processes"])

    def dispatch(self, args, deadline=15, cap=65536):
        if self.stage == "guest-cpus":
            assert self.guest_cpu_check_attempted and self.methods == 0
            assert args == ["shell", "cat /sys/devices/system/cpu/online"]
            assert self.clean; self.check_owner()
            return self._dispatch_checked(args, deadline, cap)
        if self.stage == "source-root":
            assert self.real_phase == "preflight" and self.methods == 0
            assert args == ["shell", shlex.join(source_create(self.uid_map[q.APP]))]
            assert self.clean; self.check_owner()
            return self._dispatch_checked(args, deadline, cap)
        assert self.stage in {"boot", "before", "updating", "installed", "after", "proofs", *(step[1] for step in self.instrumentation_steps)}
        return super().dispatch(args, deadline, cap)

    def check_guest_cpu_profile(self):
        """One pre-work observation for the explicit four-core experiment only."""
        assert self.stage == "before" and self.methods == 0 and not self.guest_cpu_check_attempted
        self.guest_cpu_check_attempted = True
        env = q.contract.strict_json(Path(self.proposal["environment_proposal_path"]).read_bytes())
        assert type(env["cores"]) is int and env["cores"] in (2, 4)
        if env["cores"] == 2:
            return
        assert env["memory_mib"] == 8192 and env["host_available_memory_min"] == 12 * GIB
        self.stage = "guest-cpus"
        raw = self.shell(("cat", "/sys/devices/system/cpu/online"), deadline=5, cap=128)
        assert q.normalized(raw, 128) == "0-3\n"
        q.write_json(self.directory / "guest-cpu-profile-v1.json",
                     {"version": 1, "requested_cores": 4, "observed_online_cores": 4})
        self.stage = "before"

    def transfer(self):
        assert self.stage == "source-stream" and self.clean and self.methods == 0 and not self.stream_attempted
        self.stream_attempted = True
        self.check_owner(); self.count += 1
        stem = self.commands / ("command-%04d" % self.count)
        remaining = self.until - time.monotonic(); assert remaining > 0
        facts = self.directory / ("installed-facts.json" if self.real_phase == "preflight" else "continued-before-facts.json")
        try:
            q.write_json(self.directory / "stream-parent-v1.json", {"version": 1,
                "parent": environment.process_identity(os.getpid()), "proposal_sha256": q.sha(Path(self.proposal_path).read_bytes()),
                "authorization_sha256": q.sha(Path(self.authorization_path).read_bytes()), "phase": self.real_phase,
                "uid": self.uid_map[q.APP], "facts_sha256": q.sha(facts.read_bytes()), "deadline_epoch": time.time() + min(180, remaining)})
            result = q.host.run_process([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "_stream",
                "--proposal", str(self.proposal_path), "--authorization", str(self.authorization_path),
                "--evidence", self.proposal["evidence_root"]],
                request=STREAM_REQUEST + str(self.uid_map[q.APP]).encode("ascii") + b"\n", deadline=min(180, remaining), max_output=4096)
            self.clean &= result.cleanup_complete is True
            with stem.with_suffix(".stdout.bin").open("xb") as stream:
                stream.write(result.stdout); stream.flush(); os.fsync(stream.fileno())
            q.write_json(stem.with_suffix(".json"), {"index": self.count, "stage": self.stage, "transport": "file-backed-stdin",
                "source_kind": self.real_phase, "status": result.status, "returncode": result.returncode,
                "cleanup_complete": result.cleanup_complete, "stdout_bytes": len(result.stdout), "stdout_sha256": q.sha(result.stdout),
                "stderr_bytes": result.stderr_bytes})
        except BaseException:
            self.clean = False
            raise
        self.check_owner()
        assert self.clean and result.status == "completed" and result.returncode == 0
        body = q.contract.strict_json(result.stdout)
        assert set(body) == {"version", "source_bytes", "source_verified", "client_returncode", "remote_exit_status_known", "destination_verified"}
        assert type(body["version"]) is int and body["version"] == 1
        assert type(body["source_bytes"]) is int and body["source_bytes"] == self.proposal["source"]["bytes"]
        assert body["source_verified"] is True
        assert type(body["client_returncode"]) is int and body["client_returncode"] == 0
        assert body["remote_exit_status_known"] is False and body["destination_verified"] is False
        return body


def read_proof(owner, phase):
    owner.stage = "proofs"
    ready = proof_command(phase, owner.uid_map[q.APP], True); owner.pending_read = ready
    assert owner.shell(ready, cap=4096) == b""
    command = proof_command(phase, owner.uid_map[q.APP]); owner.pending_read = command
    raw = owner.shell(command, cap=4096)
    value = parse_proof(raw, phase, owner.uid_map[q.APP])
    with (owner.directory / (PHASES[phase][0] + "-proof.raw.json")).open("xb") as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    q.write_json(owner.directory / (PHASES[phase][0] + "-proof-v1.json"), value)
    return value, raw


def run_selected(owner, phase):
    owner.stage = "instrument-" + phase
    raw = owner.shell(selection(phase), deadline=180 if phase != "SOURCE_PREFLIGHT" else 60, cap=131072)
    worker_trace.observe_worker_trace(owner, raw, phase)
    if phase != "PLAY":
        q.observe_failure_trace(owner, raw, "initial" if phase in ("SOURCE_PREFLIGHT", "IMPORT") else "restart")
    result = parse_runner(raw, phase)
    q.write_json(owner.directory / (PHASES[phase][0] + "-instrumentation-v1.json"), result)
    return read_proof(owner, phase)


def run_cohort(owner):
    owner.wait_boot()
    owner.check_guest_cpu_profile()
    if owner.real_phase == "preflight":
        before = owner.facts("before", {})
        sizes = q.validate_apks(owner.proposal)
        assert before["userdata"]["available_bytes"] - q.contract.USERDATA_FLOOR >= sum(sizes.values()) + MODEL_BYTES
        owner.stage = "updating"
        for package in (q.APP, q.TEST):
            owner.pending_install = package
            raw = owner.dispatch(["install", "--no-streaming", owner.proposal["apk_paths"][package]], deadline=35, cap=4096)
            assert q.normalized(raw, 4096) in ("Success\n", "Performing Push Install\nSuccess\n")
        owner.stage = "installed"; installed = owner.facts("installed", q.APK_HASHES)
        assert owner.shell(q.PROOF_ABSENT, cap=4096) == b""
        assert owner.shell(q.contract.INTERNAL_CANDIDATE_ABSENT, cap=4096) == b""
        owner.stage = "source-root"; assert owner.shell(source_create(owner.uid_map[q.APP]), cap=4096) == b""
        owner.stage = "source-stream"; transfer = owner.transfer()
        proof, _ = run_selected(owner, "SOURCE_PREFLIGHT")
        owner.stage = "after"; after = owner.facts("after-preflight", q.APK_HASHES)
        return {"before": before, "installed": installed, "transfer": transfer, "proof": proof, "after": after,
                "model_copied": False, "guarded_sdk_gift_observed": False, "physical_phone_qualified": False}
    before = owner.facts("continued-before", q.APK_HASHES)
    assert before["userdata"]["available_bytes"] - q.contract.USERDATA_FLOOR >= MODEL_BYTES
    owner.stage = "source-stream"; transfer = owner.transfer()
    previous_raw = Path(owner.proposal["preflight"]["proof"]["path"]).read_bytes()
    previous = parse_proof(previous_raw, "SOURCE_PREFLIGHT", owner.uid_map[q.APP])
    proofs = {}
    for phase in ("IMPORT", "PLAY", "REOPEN"):
        value, raw = run_selected(owner, phase); link_proofs(previous, previous_raw, value)
        proofs[phase] = value; previous, previous_raw = value, raw
        owner.stage = "after"; owner.facts("after-" + phase.lower(), q.APK_HASHES)
    return {"before": before, "transfer": transfer, "proofs": proofs, "model_copied": True,
            "guarded_sdk_gift_observed": True, "physical_phone_qualified": False, "DocumentsUI_qualified": False}


def worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(128) == REQUEST
    value = authorize(proposal_path, authorization_path, evidence)
    owner = Owner(value, q.open_lease(value)); owner.proposal_path = proposal_path; owner.authorization_path = authorization_path
    result, failure = None, None
    try: result = run_cohort(owner)
    except BaseException: failure = "receipt_real_candidate_stopped"
    result_value = {"version": 1, "scope": SCOPE, "phase": value["phase"], "status": "observed" if failure is None else "stopped",
        "failure": failure, "running_sha256": value["running_sha256"], "stage": owner.stage, "clients_cleaned": owner.clean,
        "owner_live": owner.owner_live, "command_count": owner.count, "instrumentation_commands": owner.methods,
        "installs": owner.installs, "result": result}
    q.write_json(owner.directory / "result-v1.json", result_value)
    print(json.dumps({key: result_value[key] for key in result_value if key != "result"}))
    return 0 if failure is None and owner.clean and owner.owner_live else 2


def run_owned(proposal_path, authorization_path, evidence):
    value = authorize(proposal_path, authorization_path, evidence); lease = q.open_lease(value); lease.check()
    seconds = 180 if value["phase"] == "preflight" else 900
    assert lease.descriptor["deadline_epoch"] - time.time() >= seconds + 20
    root = Path(evidence); driver = root / "driver"; driver.mkdir(exist_ok=False)
    q.write_json(root / "receipt-owned-start-v1.json", {"version": 1, "deadline_seconds": seconds,
        "proposal_sha256": q.sha(Path(proposal_path).read_bytes()), "authorization_sha256": q.sha(Path(authorization_path).read_bytes())})
    result = environment.supervise([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "worker",
        "--proposal", str(proposal_path), "--authorization", str(authorization_path), "--evidence", str(evidence)],
        REQUEST, driver, seconds, lambda child: True)
    q.write_json(root / "receipt-owned-result-v1.json", result); print(json.dumps(result))
    return 0 if result["status"] == "child_exited" and result["worker_returncode"] == 0 and result["cleanup_complete"] and result["output_capture_complete"] else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "worker", "_stream"))
    for name in ("proposal", "authorization", "evidence"): parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    if sys.flags.optimize: raise ValueError("optimized_controller_refused")
    if args.action == "_stream":
        try: return stream_worker(args.proposal, args.authorization, args.evidence)
        except BaseException:
            print(json.dumps({"status": "stream_failed", "remote_exit_status_known": False})); return 2
    return (run_owned if args.action == "run" else worker)(args.proposal, args.authorization, args.evidence)


if __name__ == "__main__":
    raise SystemExit(main())
