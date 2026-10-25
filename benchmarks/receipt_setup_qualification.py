"""Explicitly admitted Compose receipt setup qualification on a new owned emulator.

No operation runs at import. This controller never manages emulator lifecycle.
Private identities and raw diagnostics belong in the admitted evidence folder.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
import runtime_spike as host
_spec = importlib.util.spec_from_file_location("receipt_contract", ROOT / "scripts/android_receipt_qualification_probe.py")
contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contract)

APP, TEST = contract.APP, contract.TEST
APK_HASHES = {
    APP: "83797af66672e5bab89e17d53339478eb7c57bee66773c9c72edd13466911a8a",
    TEST: "e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d",
}
SOURCE_FILES = ("benchmarks/receipt_setup_qualification.py", "benchmarks/receipt_avd_environment.py",
    "benchmarks/receipt_fresh_target.py", "scripts/tests/test_receipt_setup_qualification.py",
    "scripts/tests/test_receipt_setup_helper.py",
    "scripts/tests/test_receipt_setup_failure.py",
    "apps/android/app/src/litert/java/org/locallore/app/CandidateModelAccess.kt",
    "apps/android/app/src/litert/java/org/locallore/app/ReceiptCandidateModelAccess.kt",
    "apps/android/app/src/litert/java/org/locallore/app/AndroidReceiptModelAccess.kt",
    "apps/android/app/src/litert/java/org/locallore/app/CandidateLocalModel.kt",
    "apps/android/app/src/litert/java/org/locallore/app/LocalModelSetupActivity.kt",
    "apps/android/app/src/litert/java/org/locallore/app/LocalModelSetupViewModel.kt",
    "apps/android/app/src/litert/java/org/locallore/app/LiteRtRoleWorker.kt",
    "apps/android/app/src/litert/java/org/locallore/app/FiniteSchemaRegex.kt",
    "apps/android/app/src/litertTest/java/org/locallore/app/FiniteSchemaRegexTest.kt",
    "apps/android/app/src/litertTest/java/org/locallore/app/LiteRtResponseFormatTest.kt",
    "apps/android/app/src/modelReceipt/java/org/locallore/app/ReceiptSetupFixtureActivity.kt",
    "apps/android/app/src/modelReceipt/java/org/locallore/app/ReceiptSetupFailureTrace.kt",
    "apps/android/app/src/modelReceiptTest/java/org/locallore/app/ReceiptSetupFailureTraceTest.kt",
    "apps/android/app/src/modelReceiptAndroidTest/java/org/locallore/app/ReceiptSetupQualificationTest.kt",
    "apps/android/app/src/modelReceipt/AndroidManifest.xml", "docs/native/RECEIPT_SETUP_CONTRACT.md",
    "docs/native/RECEIPT_SETUP_PROTOCOL.md", *contract.SOURCE_FILES)
PROPOSAL_KEYS = frozenset(("version", "scope", "source_commit", "source_final", "artifacts_final",
    "allow_device_calls", "root_go_pending", "selected_alias", "environment_proposal_path", "running_path",
    "running_sha256", "adb_path", "apk_paths", "apk_sha256", "bindings", "evidence_root"))
REQUEST = b"receipt-setup-qualification-v1\n"
OUTER_SECONDS = 180
AGGREGATE_SECONDS = 165
BOOT_SECONDS = 60
AVD_NAME = ("emu", "avd", "name")
sha, write_json, normalized = contract.sha, contract.write_json, contract.normalized
INITIAL_CLASS = "org.locallore.app.ReceiptSetupQualificationTest"
RESTART_CLASS = "org.locallore.app.ReceiptSetupRestartTest"
PHASES = {
    "SETUP": ("setup", "importsAndRechecksThroughActualReceiptSetup", frozenset((
        "candidate_access_receipt", "candidate_identity_fixed", "candidate_roots_context", "candidate_absent_noncreating",
        "source_opened_once", "source_closed_once", "accepted_records_exact", "ui_ready_after_import", "ui_recheck_ready",
        "activity_recreation_ready", "reopen_source_unopened", "sdk_not_opened"))),
    "CANCELLATION": ("cancellation", "cancelsBeforeAndAfterAcceptanceThroughCompose", frozenset((
        "before_checkpoint_reached", "before_stopping_held", "before_busy_refused", "before_source_closed_once",
        "before_unaccepted_preserved", "before_not_ready_after_drain", "before_recheck_missing", "after_checkpoint_reached",
        "after_stopping_held", "after_busy_refused", "after_source_closed_once", "after_accepted_preserved",
        "after_not_ready_after_drain", "after_recheck_ready"))),
    "DRAIN": ("drain", "disposedScopeRetainsSourceUntilActualDrain", frozenset((
        "read_blocked", "stopping_holds_source", "contender_busy", "original_scope_disposed", "fresh_scope_busy_failed",
        "source_closed_after_release", "actual_reservation_drained", "original_never_ready", "fresh_recheck_missing",
        "unaccepted_preserved", "source_opened_once"))),
    "REOPEN": ("reopen", "reopensAcceptedCopyAfterActualProcessRestart", frozenset((
        "previous_proof_valid", "process_identity_changed", "actual_adapter_receipt", "ui_ready_after_reopen",
        "accepted_records_exact", "source_unopened", "sdk_not_opened"))),
}
INITIAL_METHODS = frozenset(PHASES[phase][1] for phase in ("SETUP", "CANCELLATION", "DRAIN"))
RESTART_METHODS = frozenset((PHASES["REOPEN"][1],))
INITIAL_INSTRUMENT = ("am", "instrument", "-w", "-r", "-e", "class", INITIAL_CLASS, TEST + "/androidx.test.runner.AndroidJUnitRunner")
RESTART_INSTRUMENT = ("am", "instrument", "-w", "-r", "-e", "class", RESTART_CLASS, TEST + "/androidx.test.runner.AndroidJUnitRunner")
PROOF_ROOT = "no_backup/receipt-setup-proof-v1"
PROOF_ABSENT = ("run-as", APP, "sh", "-c", "test ! -e " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT)
PROOF_MANIFEST = ("run-as", APP, "sh", "-c", "test -d no_backup && test ! -L no_backup && test -d " +
                  PROOF_ROOT + " && test ! -L " + PROOF_ROOT + " && find " + PROOF_ROOT + " -mindepth 1 -maxdepth 1 -print")
PROOF_KEYS = frozenset(("version", "phase", "pid", "start", "uid", "process", "fixture_bytes", "fixture_sha256",
    "direct_callback", "candidate_roots_absent", "publication_native_invoked", "sdk_invoked", "external_free_before",
    "external_free_after", "userdata_free_before", "userdata_free_after", "source_opened", "source_closed", "checks"))
FAILURE_PREFIX = "INSTRUMENTATION_STATUS: locallore_receipt_failure_v1="
FAILURE_STATUS = "INSTRUMENTATION_STATUS_CODE: 1337"
FAILURE_PHASES = frozenset(("UNCHECKED", "CHECKING", "MISSING", "PICKING", "IMPORTING", "STOPPING", "READY",
                            "FAILED", "OPENING", "SESSION_HELD"))
FAILURE_EVENTS = frozenset(("CREATE", "START", "RESUME", "PAUSE", "STOP", "DESTROY", "CHECK_START",
    "CHECK_PRESENT", "CHECK_MISSING", "CHECK_CANCELLED", "CHECK_FAILED", "IMPORT_START", "IMPORT_RETURNED",
    "IMPORT_CANCELLED", "IMPORT_FAILED"))
FAILURE_CODES = frozenset(("NONE", "CANCELLED", "BUSY", "NO_SPACE", "INVALID_MODEL", "UNSAFE_PATH", "STORAGE", "OTHER"))
FAILURE_LIMIT = 1_000_000


def parse_failure_trace(raw):
    """A bounded observation only: never evidence of READY, acceptance or cleanup."""
    assert type(raw) is bytes and 0 < len(raw) <= 2048 - len(FAILURE_PREFIX.encode("ascii"))
    assert all(32 <= byte <= 126 for byte in raw)
    value = contract.strict_json(raw)
    assert type(value) is dict and set(value) == {"version", "case", "expected", "actual", "error",
                                                "events_total", "events_saturated", "events", "source"}
    assert type(value["version"]) is int and value["version"] == 1
    for key, options in (("case", {"ACCEPT", "CANCEL_BEFORE", "CANCEL_AFTER", "DRAIN"}),
                         ("expected", FAILURE_PHASES), ("actual", FAILURE_PHASES), ("error", FAILURE_CODES)):
        assert type(value[key]) is str and value[key] in options
    events = value["events"]
    assert type(events) is list and len(events) <= 16
    assert all(type(event) is str and event in FAILURE_EVENTS for event in events)
    assert type(value["events_total"]) is int and len(events) <= value["events_total"] <= FAILURE_LIMIT
    assert type(value["events_saturated"]) is bool
    assert not value["events_saturated"] or value["events_total"] == FAILURE_LIMIT
    source = value["source"]
    assert type(source) is dict and set(source) == {"opened", "closed", "active", "reads", "bytes",
                                                  "reads_saturated", "bytes_saturated"}
    for key in ("opened", "closed", "active", "reads", "bytes"):
        assert type(source[key]) is int and 0 <= source[key] <= FAILURE_LIMIT
    for key, count in (("reads_saturated", "reads"), ("bytes_saturated", "bytes")):
        assert type(source[key]) is bool and (not source[key] or source[count] == FAILURE_LIMIT)
    return value


def extract_failure_trace(raw):
    text = normalized(raw, 131072)
    lines = text.splitlines()
    positions = [index for index, line in enumerate(lines) if line.startswith(FAILURE_PREFIX)]
    codes = [index for index, line in enumerate(lines) if line == FAILURE_STATUS]
    if not positions and not codes:
        assert "locallore_receipt_failure_v1" not in text
        return None
    assert len(positions) == len(codes) == 1 and codes[0] == positions[0] + 1
    assert text.count("locallore_receipt_failure_v1") == 1
    # A diagnostic can never explain away a passing runner or replace its proof.
    assert not re.search(r"^OK \([0-9]+ tests?\)$", text, re.MULTILINE)
    return parse_failure_trace(lines[positions[0]][len(FAILURE_PREFIX):].encode("ascii"))


def observe_failure_trace(owner, raw, label):
    assert label in ("initial", "restart")
    value = extract_failure_trace(raw)
    if value is not None:
        write_json(owner.directory / (label + "-failure-trace-v1.json"), value)
    # The caller still applies the unchanged strict runner gate to the RAW stream.
    return value


def parse_proof(raw, phase, uid):
    assert phase in PHASES and type(raw) is bytes and 0 < len(raw) <= 4096
    value = contract.strict_json(raw)
    keys = PROOF_KEYS | ({"prior_pid", "prior_start"} if phase == "REOPEN" else set())
    assert type(value) is dict and set(value) == keys
    for key, lower, upper in (("version", 1, 1), ("pid", 1, 2 ** 31 - 1), ("start", 1, 2 ** 63 - 1),
                              ("uid", 10000, 2 ** 31 - 1), ("fixture_bytes", 63, 63)):
        assert type(value[key]) is int and lower <= value[key] <= upper
    assert value["phase"] == phase and value["uid"] == uid and value["process"] == APP
    assert value["fixture_sha256"] == contract.FIXTURE_SHA256
    for key, wanted in (("direct_callback", True), ("candidate_roots_absent", True),
                        ("publication_native_invoked", False), ("sdk_invoked", False)):
        assert type(value[key]) is bool and value[key] is wanted
    for key in ("external_free_before", "external_free_after", "userdata_free_before", "userdata_free_after"):
        floor = (contract.EXTERNAL_FLOOR + (63 if key.endswith("before") else 0)
                 if key.startswith("external") else contract.PROOF_USERDATA_FLOOR)
        assert type(value[key]) is int and floor <= value[key] <= 2 ** 63 - 1
    count = {"SETUP": 1, "CANCELLATION": 2, "DRAIN": 1, "REOPEN": 0}[phase]
    assert all(type(value[key]) is int and value[key] == count for key in ("source_opened", "source_closed"))
    if phase == "REOPEN":
        assert type(value["prior_pid"]) is int and 1 <= value["prior_pid"] < 2 ** 31
        assert type(value["prior_start"]) is int and 1 <= value["prior_start"] < 2 ** 63
    assert type(value["checks"]) is dict and set(value["checks"]) == PHASES[phase][2]
    assert all(type(v) is bool and v is True for v in value["checks"].values())
    return value


def match_restart(proofs):
    assert set(proofs) == set(PHASES)
    setup, reopened = proofs["SETUP"], proofs["REOPEN"]
    initial = {(proofs[p]["pid"], proofs[p]["start"], proofs[p]["uid"], proofs[p]["process"])
               for p in ("SETUP", "CANCELLATION", "DRAIN")}
    assert len(initial) == 1
    assert (reopened["prior_pid"], reopened["prior_start"]) == (setup["pid"], setup["start"])
    assert (reopened["pid"], reopened["start"]) != (setup["pid"], setup["start"])
    assert (reopened["uid"], reopened["process"]) == (setup["uid"], setup["process"])
    return True


def proof_command(name, uid):
    names = {stem + suffix for stem, _, _ in PHASES.values() for suffix in ("-v1.json", "-ready-v1.txt")}
    assert name in names and type(uid) is int and 10000 <= uid < 2 ** 31
    path = PROOF_ROOT + "/" + name
    size = "-eq 0" if name.endswith(".txt") else "-gt 0"
    return ("run-as", APP, "sh", "-c", "test -d no_backup && test ! -L no_backup && test -d " + PROOF_ROOT +
            " && test ! -L " + PROOF_ROOT + " && test -f " + path + " && test ! -L " + path +
            " && test $(stat -c %u " + path + ") -eq " + str(uid) + " && test $(wc -c < " + path + ") " + size +
            " && test $(wc -c < " + path + ") -le 4096 && cat " + path)


def parse_instrumentation(raw, expected_class, expected_methods):
    assert (expected_class, expected_methods) in ((INITIAL_CLASS, INITIAL_METHODS), (RESTART_CLASS, RESTART_METHODS))
    return _parse_selected_instrumentation(raw, expected_class, expected_methods)


def _parse_selected_instrumentation(raw, expected_class, expected_methods):
    """Trusted fixed experiments share framing, never caller-selected dispatch authority."""
    count = len(expected_methods)
    text = normalized(raw, 131072)
    records, fields, extra, result = [], {}, [], None
    stream = None
    runner = False
    for line in text.split("\n"):
        if line.startswith("INSTRUMENTATION_STATUS: "):
            assert result is None and not runner
            key, sep, value = line[len("INSTRUMENTATION_STATUS: "):].partition("=")
            assert sep and key in {"class", "current", "id", "numtests", "stream", "test"} and key not in fields
            fields[key] = value
            stream = "status" if key == "stream" else None
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            value = line.split(": ", 1)[1]
            code = int(value)
            assert str(code) == value and result is None and not runner
            records.append((code, fields, extra))
            fields, extra, stream = {}, [], None
        elif line.startswith("INSTRUMENTATION_RESULT: "):
            key, sep, value = line[len("INSTRUMENTATION_RESULT: "):].partition("=")
            assert sep and key == "stream" and result is None and not fields and not runner and len(records) == count * 2
            result, stream = [value], "result"
        elif line.startswith("INSTRUMENTATION_CODE: "):
            assert not runner and result is not None and not fields and line.split(": ", 1)[1] == "-1"
            runner, stream = True, None
        elif line.startswith("INSTRUMENTATION_"):
            raise AssertionError("unexpected_machine_record")
        elif stream == "status":
            extra.append(line)
        elif stream == "result":
            result.append(line)
        else:
            assert not line.strip()
    assert not fields and runner and len(records) == count * 2 and result is not None
    methods = []
    for index in range(count):
        start, end = records[index * 2:index * 2 + 2]
        assert start[0] == 1 and end[0] == 0
        method = start[1].get("test")
        assert method in expected_methods and method not in methods
        methods.append(method)
        for code, fields, extra in (start, end):
            assert set(fields) <= {"class", "current", "id", "numtests", "stream", "test"}
            assert fields.get("class") == expected_class and fields.get("test") == method
            assert fields.get("current") == str(index + 1) and fields.get("numtests") == str(count) and fields.get("id") == "AndroidJUnitRunner"
            body = "\n".join([fields.get("stream", "")] + extra)
            assert body in ("", "\n" + expected_class + ":", expected_class + ":") if code == 1 else body == "."
    summary = "\n".join(result)
    match = re.fullmatch(r"\n\nTime: ((?:0|[1-9][0-9]{0,5})(?:\.[0-9]{1,9})?)\n\nOK \(" + str(count) + (" test" if count == 1 else " tests") + r"\)\n{1,3}", summary)
    assert match and 0 <= float(match[1]) <= 120
    return {"passed": count, "failed": 0, "methods": methods}


def parse_console_name(raw, expected):
    """The emulator console can double CR; accept only its exact two lines."""
    assert type(raw) is bytes and type(expected) is str
    assert re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", expected)
    name = expected.encode("ascii")
    assert raw in {name + ending + b"OK" + ending for ending in (b"\n", b"\r\n", b"\r\r\n")}
    return expected


def open_lease(proposal):
    # The exact environment module is integrated before admission. No fallback.
    from receipt_avd_environment import open_live_owner
    lease = open_live_owner(proposal["environment_proposal_path"], proposal["running_path"], proposal["running_sha256"])
    descriptor = lease.descriptor
    assert re.fullmatch(r"emulator-[1-9][0-9]{3,5}", descriptor["serial"])
    assert re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", descriptor["avd_name"])
    assert Path(descriptor["adb_path"]).is_absolute()
    assert Path(descriptor["adb_path"]).resolve() == Path(proposal["adb_path"]).resolve()
    lease.check()
    return lease


def validate_apks(proposal):
    sizes = {}
    for package, name in ((APP, "app-debug.apk"), (TEST, "app-debug-androidTest.apk")):
        path = Path(proposal["apk_paths"][package])
        assert path.is_absolute() and path.name == name
        size = path.stat().st_size
        assert 1 <= size <= 1024 ** 3
        raw = path.read_bytes()
        assert len(raw) == size and sha(raw) == proposal["apk_sha256"][package]
        sizes[package] = size
    return sizes


def validate_proposal(value):
    assert type(value) is dict and set(value) == PROPOSAL_KEYS
    assert type(value["version"]) is int and value["version"] == 1
    assert value["scope"] == "receipt_setup_qualification" and value["selected_alias"] == "S"
    assert value["source_final"] is True and value["artifacts_final"] is True
    assert value["allow_device_calls"] is False and value["root_go_pending"] is True
    assert re.fullmatch(r"[a-f0-9]{40}", value["source_commit"])
    for key in ("environment_proposal_path", "running_path", "adb_path", "evidence_root"):
        assert type(value[key]) is str and Path(value[key]).is_absolute()
    assert Path(value["adb_path"]).name == "adb.exe"
    assert re.fullmatch(r"[a-f0-9]{64}", value["running_sha256"])
    assert type(value["apk_paths"]) is dict and set(value["apk_paths"]) == {APP, TEST}
    assert value["apk_sha256"] == APK_HASHES
    bindings = value["bindings"]
    assert type(bindings) is dict and 1 <= len(bindings) <= 128
    assert all(str((ROOT / name).resolve()) in bindings for name in SOURCE_FILES)
    for key in ("environment_proposal_path", "running_path", "adb_path"):
        assert str(Path(value[key]).resolve()) in bindings
    assert bindings[str(Path(value["running_path"]).resolve())] == value["running_sha256"]
    for package, name in value["apk_paths"].items():
        assert bindings.get(str(Path(name).resolve())) == value["apk_sha256"][package]
    for name, digest in bindings.items():
        path = Path(name)
        assert path.is_absolute() and re.fullmatch(r"[a-f0-9]{64}", digest)
        assert sha(path.read_bytes()) == digest
    validate_apks(value)
    return True


def authorize(proposal_path, authorization_path, evidence):
    raw = Path(proposal_path).read_bytes()
    proposal = contract.strict_json(raw)
    auth = contract.strict_json(Path(authorization_path).read_bytes())
    assert type(auth) is dict and set(auth) == {"version", "proposal_sha256", "allow_device_calls", "root_go_pending"}
    assert type(auth["version"]) is int and auth["version"] == 1
    assert auth["proposal_sha256"] == sha(raw) and auth["allow_device_calls"] is True and auth["root_go_pending"] is False
    assert Path(proposal["evidence_root"]).resolve() == Path(evidence).resolve()
    validate_proposal(proposal)
    return proposal


def parse_packages(raw, expected):
    """Fresh bootstrap is exactly empty, then exactly the isolated pair."""
    assert set(expected) in (set(), {APP, TEST})
    if not expected:
        assert raw == b""
        return {}
    result = {}
    for line in normalized(raw).splitlines():
        match = re.fullmatch(r"(org\.locallore(?:\.[A-Za-z0-9_]+)+)\|([a-f0-9]{64})  (/data/app/[A-Za-z0-9_~+=./-]+/base\.apk)", line)
        assert match and match[1] not in result and ".." not in match[3].split("/")
        result[match[1]] = match[2]
    assert result == expected
    return result


def parse_uids(raw, packages):
    if not packages:
        assert raw == b""
        return {}
    result = {}
    for line in normalized(raw).splitlines():
        match = re.fullmatch(r"package:(org\.locallore(?:\.[A-Za-z0-9_]+)+) uid:([1-9][0-9]{0,9})", line)
        assert match and match[1] in packages and match[1] not in result
        uid = int(match[2])
        assert 10000 <= uid < 2 ** 31
        result[match[1]] = uid
    assert set(result) == {APP, TEST} and len(set(result.values())) == 2
    return result


class ProcessBoundary:
    """Track the distinct TEST process without granting it target-app authority."""
    observations = (("before", "before", 0), ("installed", "installed", 0),
                    ("after-initial", "after", 1), ("after-restart", "after", 2), ("final", "final", 2))

    def __init__(self):
        self._next = 0
        self._helper = None
        self._retired = False
        self._refused = False

    def observe(self, raw, uids, *, label, stage, methods):
        try:
            assert not self._refused and self._next < len(self.observations)
            assert type(label) is str and type(stage) is str and type(methods) is int
            assert (label, stage, methods) == self.observations[self._next]
            assert type(uids) is dict
            if self._next == 0:
                assert uids == {}
            else:
                assert set(uids) == {APP, TEST} and all(type(uid) is int and 10000 <= uid < 2 ** 31 for uid in uids.values())
                assert uids[APP] != uids[TEST]
            parsed = contract.parse_processes(raw, uids, {})
            assert parsed["passive"] == []
            rows = parsed["owned"]
            if self._next < 2:
                assert rows == []
            else:
                # APP, its service, provider and every foreign LocalLore row refuse.
                assert len(rows) <= 1 and all(row["name"] == TEST for row in rows)
                helper = (rows[0]["pid"], rows[0]["uid"], rows[0]["name"]) if rows else None
                if self._next == 2:
                    # The sole binding point follows exact initial passes and APP absence.
                    self._helper = helper
                elif helper is not None:
                    assert not self._retired and helper == self._helper
                elif self._helper is not None:
                    self._retired = True
            self._next += 1
            # Copies prevent diagnostic consumers from modifying the bound tuple.
            return {"target": [], "test_helper": [dict(row) for row in rows]}
        except Exception:
            self._refused = True
            raise


class Owner:
    # Trusted subclasses may define a separate fixed experiment. No proposal,
    # class name or command argument can alter this ordinary cohort's choices.
    instrumentation_steps = ((INITIAL_INSTRUMENT, "instrumentation", 0), (RESTART_INSTRUMENT, "restart", 1))

    def __init__(self, proposal, lease):
        self.proposal, self.lease = proposal, lease
        # Capture the admitted identity once; never accept a later replacement.
        self.serial = lease.descriptor["serial"]
        self.avd_name = lease.descriptor["avd_name"]
        assert Path(lease.descriptor["adb_path"]).resolve() == Path(proposal["adb_path"]).resolve()
        self.directory = Path(proposal["evidence_root"]) / "cohort"
        self.directory.mkdir(exist_ok=False)
        self.commands = self.directory / "commands"
        self.commands.mkdir()
        self.stage, self.clean, self.owner_live, self.count = "boot", True, True, 0
        self.until = time.monotonic() + AGGREGATE_SECONDS
        self.installs, self.methods = {APP: 0, TEST: 0}, 0
        self.pending_install, self.pending_read = None, None
        self.uid_map, self.volume = None, None
        self.boot_returncode, self.boot_stderr_bytes = None, None
        self.process_boundary = ProcessBoundary()

    def check_owner(self):
        assert self.owner_live
        try:
            self.lease.check()
            assert self.lease.descriptor["serial"] == self.serial and self.lease.descriptor["avd_name"] == self.avd_name
            assert Path(self.lease.descriptor["adb_path"]).resolve() == Path(self.proposal["adb_path"]).resolve()
        except BaseException:
            self.owner_live = False
            raise

    def dispatch(self, args, deadline=15, cap=65536):
        assert self.clean
        self.check_owner()
        boot = self.stage == "boot"
        if boot:
            assert args == ["shell", shlex.join(contract.IDENTITY[0])]
        elif args == list(AVD_NAME):
            assert self.stage in ("before", "installed", "after", "final")
        elif args[0] == "install":
            package = self.pending_install
            assert self.stage == "updating" and package in (APP, TEST) and self.installs[package] == 0
            # The new factory target has no prior package; no replace/adopt mode.
            assert args == ["install", "--no-streaming", self.proposal["apk_paths"][package]]
            self.installs[package] += 1
            self.pending_install = None
        else:
            assert len(args) == 2 and args[0] == "shell"
            op = tuple(shlex.split(args[1]))
            if op in (*contract.IDENTITY, contract.PACKAGES, contract.UIDS, contract.PS,
                      contract.VOLUMES, contract.DF, contract.DEVICES):
                assert self.stage in ("before", "installed", "after", "final")
            elif op in (PROOF_ABSENT, contract.INTERNAL_CANDIDATE_ABSENT):
                assert self.stage == "installed"
            elif op in tuple(step[0] for step in self.instrumentation_steps):
                assert (op, self.stage, self.methods) in self.instrumentation_steps
                self.methods += 1
            elif op == PROOF_MANIFEST:
                assert self.stage == "proofs" and self.pending_read is None
            else:
                assert self.stage == "proofs" and op == self.pending_read
                self.pending_read = None
        return self._dispatch_checked(args, deadline, cap, boot=boot)

    def _dispatch_checked(self, args, deadline, cap, *, boot=False):
        """Execute only after a trusted fixed experiment has checked its grammar."""
        remaining = self.until - time.monotonic()
        assert remaining > 0
        deadline = min(deadline, remaining)
        self.count += 1
        stem = self.commands / ("command-%04d" % self.count)
        command = [self.proposal["adb_path"], "-s", self.serial, *args]
        try:
            value = host.run_process(command, deadline=deadline, max_output=cap)
        except BaseException:
            self.clean = False
            raise
        self.clean &= value.cleanup_complete is True
        try:
            with stem.with_suffix(".stdout.bin").open("xb") as handle:
                handle.write(value.stdout)
                handle.flush()
                os.fsync(handle.fileno())
            write_json(stem.with_suffix(".json"), {"index": self.count, "stage": self.stage, "alias": "S", "args": args,
                "deadline_seconds": deadline, "cap_bytes": cap, "status": value.status, "returncode": value.returncode,
                "cleanup_complete": value.cleanup_complete, "stdout_bytes": len(value.stdout), "stdout_sha256": sha(value.stdout),
                "stderr_bytes": value.stderr_bytes})
        except BaseException:
            self.clean = False
            raise
        # Retain raw output before interpreting either client or owner state.
        self.check_owner()
        assert self.clean and value.status == "completed"
        if boot:
            assert value.returncode in (0, 1)
            self.boot_returncode, self.boot_stderr_bytes = value.returncode, value.stderr_bytes
        else:
            assert value.returncode == 0
        return value.stdout

    def shell(self, op, deadline=15, cap=65536):
        return self.dispatch(["shell", shlex.join(op)], deadline, cap)

    def wait_boot(self):
        assert self.stage == "boot"
        end = min(self.until, time.monotonic() + BOOT_SECONDS)
        while True:
            remaining = end - time.monotonic()
            assert remaining > 0
            raw = self.shell(contract.IDENTITY[0], deadline=min(5, remaining), cap=4096)
            assert time.monotonic() <= end
            if self.boot_returncode == 0:
                text = normalized(raw, 4096) if raw else ""
                if text == "1\n":
                    self.stage = "before"
                    return
                assert text in ("", "\n", "0\n")
            else:
                # Runtime retains stderr counts, not text: do not claim an
                # offline diagnosis from this bounded boot-only client refusal.
                assert raw == b"" and 1 <= self.boot_stderr_bytes <= 4096
            remaining = end - time.monotonic()
            assert remaining > 0
            time.sleep(min(1, remaining))

    def facts(self, label, packages):
        host_free = {letter: shutil.disk_usage(letter + ":/").free for letter in ("C", "D")}
        assert host_free["C"] >= 4 * 1024 ** 3 + 128 * 1024 ** 2 and host_free["D"] >= 10 * 1024 ** 3
        assert parse_console_name(self.dispatch(list(AVD_NAME), cap=1024), self.avd_name) == self.avd_name
        for op, expected in zip(contract.IDENTITY, ("1\n", "35\n", "x86_64\n", "4096\n")):
            assert normalized(self.shell(op), 128) == expected
        observed = parse_packages(self.shell(contract.PACKAGES), packages)
        uids = parse_uids(self.shell(contract.UIDS), observed)
        if packages:
            if self.uid_map is None:
                assert label == "installed"
                self.uid_map = uids
            assert uids == self.uid_map
        processes = self.process_boundary.observe(self.shell(contract.PS), uids,
            label=label, stage=self.stage, methods=self.methods)
        volume = contract.parse_volume(self.shell(contract.VOLUMES, cap=4096))
        if self.volume is None:
            self.volume = volume
        assert volume == self.volume
        storage = contract.parse_storage(self.shell(contract.DF), self.shell(contract.DEVICES, cap=128))
        value = {"version": 2, "packages": observed, "uid_map": uids, "processes": processes,
                 "volume": volume, "userdata": storage, "host_free": host_free}
        write_json(self.directory / (label + "-facts.json"), value)
        return value


def read_proofs(owner, phases):
    owner.stage = "proofs"
    manifest = normalized(owner.shell(PROOF_MANIFEST, cap=4096), 4096).splitlines()
    present = set(PHASES) if "REOPEN" in phases else set(PHASES) - {"REOPEN"}
    wanted = {PROOF_ROOT + "/" + PHASES[phase][0] + suffix for phase in present
              for suffix in ("-v1.json", "-ready-v1.txt")}
    assert len(manifest) == len(wanted) and set(manifest) == wanted
    proofs = {}
    for phase in phases:
        stem = PHASES[phase][0]
        ready = proof_command(stem + "-ready-v1.txt", owner.uid_map[APP])
        owner.pending_read = ready
        assert owner.shell(ready, cap=4096) == b""
        command = proof_command(stem + "-v1.json", owner.uid_map[APP])
        owner.pending_read = command
        proofs[phase] = parse_proof(owner.shell(command, cap=4096), phase, owner.uid_map[APP])
        write_json(owner.directory / (stem + "-proof-v1.json"), proofs[phase])
    return proofs


def run_cohort(owner):
    owner.wait_boot()
    before = owner.facts("before", {})
    sizes = validate_apks(owner.proposal)
    remaining = before["userdata"]["available_bytes"] - contract.USERDATA_FLOOR
    for package in (APP, TEST):
        assert sizes[package] <= remaining
        remaining -= sizes[package]
    owner.stage = "updating"
    for package in (APP, TEST):
        path = Path(owner.proposal["apk_paths"][package])
        assert sha(path.read_bytes()) == owner.proposal["apk_sha256"][package]
        owner.pending_install = package
        raw = owner.dispatch(["install", "--no-streaming", str(path)], deadline=35, cap=4096)
        assert normalized(raw, 4096) in ("Success\n", "Performing Push Install\nSuccess\n")
    owner.stage = "installed"
    installed = owner.facts("installed", owner.proposal["apk_sha256"])
    assert owner.shell(PROOF_ABSENT, cap=4096) == b""
    assert owner.shell(contract.INTERNAL_CANDIDATE_ABSENT, cap=4096) == b""
    owner.stage = "instrumentation"
    initial_raw = owner.shell(INITIAL_INSTRUMENT, deadline=120, cap=131072)
    observe_failure_trace(owner, initial_raw, "initial")
    initial = parse_instrumentation(initial_raw, INITIAL_CLASS, INITIAL_METHODS)
    write_json(owner.directory / "initial-instrumentation-v1.json", initial)
    owner.stage = "after"
    # APP absence is mandatory; a bound distinct-UID TEST row is recorded separately.
    after_initial = owner.facts("after-initial", owner.proposal["apk_sha256"])
    proofs = read_proofs(owner, ("SETUP", "CANCELLATION", "DRAIN"))
    assert len({(v["pid"], v["start"], v["uid"], v["process"]) for v in proofs.values()}) == 1
    owner.stage = "restart"
    restart_raw = owner.shell(RESTART_INSTRUMENT, deadline=60, cap=131072)
    observe_failure_trace(owner, restart_raw, "restart")
    reopened = parse_instrumentation(restart_raw, RESTART_CLASS, RESTART_METHODS)
    write_json(owner.directory / "restart-instrumentation-v1.json", reopened)
    owner.stage = "after"
    owner.facts("after-restart", owner.proposal["apk_sha256"])
    proofs.update(read_proofs(owner, ("REOPEN",)))
    match_restart(proofs)
    owner.stage = "final"
    final = owner.facts("final", owner.proposal["apk_sha256"])
    return {"initial_tests": initial, "restart_test": reopened, "proofs": proofs, "before": before,
            "installed": installed, "after_initial": after_initial, "final": final,
            "synthetic_only": True, "direct_callback_only": True, "DocumentsUI_qualified": False,
            "real_model_or_SDK_qualified": False, "physical_phone_qualified": False}


def worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(64) == REQUEST
    proposal = authorize(proposal_path, authorization_path, evidence)
    owner = Owner(proposal, open_lease(proposal))
    result, failure = None, None
    try:
        result = run_cohort(owner)
    except BaseException:
        failure = "receipt_setup_qualification_stopped"
    value = {"version": 1, "scope": proposal["scope"], "status": "observed" if failure is None else "stopped",
        "failure": failure, "stage": owner.stage, "clients_cleaned": owner.clean, "owner_live": owner.owner_live,
        "command_count": owner.count, "instrumentation_commands": owner.methods, "installs": owner.installs, "result": result}
    write_json(owner.directory / "result-v1.json", value)
    print(json.dumps({key: value[key] for key in value if key != "result"}))
    return 0 if failure is None and owner.clean and owner.owner_live else 2


def run_owned(proposal_path, authorization_path, evidence):
    proposal = authorize(proposal_path, authorization_path, evidence)
    lease = open_lease(proposal)
    evidence = Path(evidence)
    write_json(evidence / "receipt-owned-start-v1.json", {"version": 1, "deadline_seconds": OUTER_SECONDS,
        "time_ns": time.time_ns(), "proposal_sha256": sha(Path(proposal_path).read_bytes()),
        "authorization_sha256": sha(Path(authorization_path).read_bytes())})
    lease.check()
    value = host.run_process([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "worker",
        "--proposal", str(proposal_path), "--authorization", str(authorization_path), "--evidence", str(evidence)],
        request=REQUEST, deadline=OUTER_SECONDS, max_output=32768)
    with (evidence / "receipt-owned-stdout-v1.bin").open("xb") as handle:
        handle.write(value.stdout)
        handle.flush()
        os.fsync(handle.fileno())
    result = {"version": 1, "status": value.status, "returncode": value.returncode, "elapsed_ms": value.elapsed_ms,
        "cleanup_complete": value.cleanup_complete, "stdout_bytes": len(value.stdout), "stdout_sha256": sha(value.stdout),
        "stderr_bytes": value.stderr_bytes}
    write_json(evidence / "receipt-owned-result-v1.json", result)
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
