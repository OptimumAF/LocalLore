"""Disabled, explicitly admitted synthetic Android receipt qualification controller.

No operation runs at import. An immutable proposal, fresh matching authorization,
and owned stdin-barrier worker are required before the closed device command set.
Private identities and diagnostics belong only in the selected evidence folder.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
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
from android_phase_storage import parse_df

APP = "org.locallore.app.modelvolumeverify"
TEST = APP + ".test"
SERVICE = APP + ":receiptproof"
PROVIDER = TEST + ":model_picker_provider"
CLASS = "org.locallore.app.ReceiptVolumeQualificationTest"
PROOF_ROOT = "no_backup/receipt-android-proof-v2"
RECOVERY_ROOT = "no_backup/receipt-android-proof-v1"
RECOVERY_PHASES = ("ACCEPT", "CANCELLATION", "REFUSAL")
FIXTURE_SHA256 = "648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0"
USERDATA_FLOOR = 1024 ** 3 + 128 * 1024 ** 2
PROOF_USERDATA_FLOOR = 1_140_850_688
EXTERNAL_FLOOR = 2_147_483_648
OUTER_SECONDS = 180
AGGREGATE_SECONDS = 165
REQUEST = b"android-receipt-qualification-v1\n"
PHASES = {
    "ACCEPT": ("accept", "acceptsAndReopensReceipt", frozenset((
        "source_opened_once", "source_closed_once", "receipt_owner_exact", "accepted_marker_empty",
        "full_model_verified", "reopen_without_source", "accepted_discard_refused", "accepted_bytes_preserved"))),
    "CANCELLATION": ("cancellation", "cancelsAcrossAcceptanceBoundary", frozenset((
        "before_checkpoint_reached", "before_cancelled", "before_source_closed_once", "before_unaccepted_preserved",
        "before_installed_null", "after_checkpoint_reached", "after_cancelled", "after_source_closed_once",
        "after_accepted_verified", "after_reopen_without_source"))),
    "REFUSAL": ("refusal", "refusesForeignAndUncommittedData", frozenset((
        "partial_source_closed_once", "partial_installed_null", "partial_bytes_preserved", "unknown_discard_refused",
        "unknown_bytes_preserved", "explicit_partial_discarded", "discard_retry_accepted", "foreign_owner_refused",
        "foreign_source_unopened", "foreign_discard_preserved", "guard_revocation_refused", "guard_source_unopened",
        "guard_preserved", "guard_is_synthetic"))),
    "PROCESS": ("process", "recoversAfterOwnedProcessDeath", frozenset((
        "child_identity_verified", "pending_receipt_owner_exact", "pending_model_fullhash", "pending_unaccepted",
        "os_busy_all_operations", "child_halt_armed", "bound_connection_released", "child_death_observed",
        "lock_reacquired", "resumed_without_source", "accepted_fullhash"))),
}
METHODS = frozenset(value[1] for value in PHASES.values())
PROOF_FILES = frozenset(name for stem, _, _ in PHASES.values()
                        for name in (stem + "-v1.json", stem + "-ready-v1.txt"))
RECOVERY_FILES = frozenset(name for phase in RECOVERY_PHASES for name in
                          (PHASES[phase][0] + "-v1.json", PHASES[phase][0] + "-ready-v1.txt"))
PROOF_KEYS = frozenset(("version", "phase", "pid", "start", "uid", "process", "fixture_bytes", "fixture_sha256",
                       "candidate_root_absent", "publication_native_invoked", "sdk_invoked", "external_free_before",
                       "external_free_after", "userdata_free_before", "userdata_free_after", "checks"))
IDENTITY = (("getprop", "sys.boot_completed"), ("getprop", "ro.build.version.sdk"),
            ("getprop", "ro.product.cpu.abi"), ("getconf", "PAGESIZE"))
PACKAGE_SCRIPT = 'set -f; p=$(pm list packages org.locallore) || exit 1; for row in $p; do p=${row#package:}; case "$p" in org.locallore.*) ;; *) exit 1;; esac; q=$(pm path "$p") || exit 1; case "$q" in package:/data/app/*/base.apk) ;; *) exit 1;; esac; q=${q#package:}; h=$(sha256sum "$q") || exit 1; printf "%s|%s\\n" "$p" "$h"; done'
PACKAGES = ("sh", "-c", PACKAGE_SCRIPT)
UIDS = ("cmd", "package", "list", "packages", "-U", "org.locallore")
PS = ("ps", "-A", "-o", "PID,UID,NAME")
DF = ("df", "-k", "/data")
DEVICES = ("stat", "-L", "-c", "%d", "/data", "/data/user/0")
VOLUMES = ("sm", "list-volumes", "public")
PROOF_ABSENT = ("run-as", APP, "sh", "-c", "test ! -e " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT)
INTERNAL_CANDIDATE_ABSENT = ("run-as", APP, "sh", "-c", "test ! -e no_backup/local-model-v1 && test ! -L no_backup/local-model-v1")
PROOF_MANIFEST = ("run-as", APP, "sh", "-c", "test -d no_backup && test ! -L no_backup && test -d " +
                  PROOF_ROOT + " && test ! -L " + PROOF_ROOT + " && find " + PROOF_ROOT + " -mindepth 1 -maxdepth 1 -print")
RECOVERY_MANIFEST = ("run-as", APP, "sh", "-c", "test -d no_backup && test ! -L no_backup && test -d " +
                     RECOVERY_ROOT + " && test ! -L " + RECOVERY_ROOT + " && find " + RECOVERY_ROOT + " -mindepth 1 -maxdepth 1 -print")
INSTRUMENT = ("am", "instrument", "-w", "-r", "-e", "class", CLASS, TEST + "/androidx.test.runner.AndroidJUnitRunner")
SOURCE_FILES = (
    "scripts/android_receipt_qualification_probe.py", "benchmarks/runtime_spike.py", "benchmarks/android_phase_storage.py",
    "apps/android/app/src/litert/java/org/locallore/app/ReceiptModelTransaction.kt",
    "apps/android/app/src/litert/java/org/locallore/app/AndroidModelVolume.kt",
    "apps/android/app/src/litert/java/org/locallore/app/ModelVolumePolicy.kt",
    "apps/android/app/src/modelVolume/java/org/locallore/app/ReceiptAndroidFixture.kt",
    "apps/android/app/src/modelVolume/java/org/locallore/app/ReceiptProofService.kt",
    "apps/android/app/src/modelVolumeAndroidTest/java/org/locallore/app/ReceiptVolumeQualificationTest.kt",
    "apps/android/app/src/modelVolume/AndroidManifest.xml", "apps/android/app/build.gradle.kts",
    "scripts/audit_apk.py", "docs/native/MODEL_RECEIPT_ANDROID_PROTOCOL.md",
)
PROPOSAL_KEYS = frozenset(("version", "scope", "source_commit", "source_final", "artifacts_final", "allow_device_calls",
    "root_go_pending", "selected_alias", "serial", "adb_path", "apk_paths", "apk_sha256", "prior_packages", "prior_uid_map",
    "known_passive_provider_uids", "bindings", "evidence_root"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def normalized(raw, cap=65536):
    assert type(raw) is bytes and 0 < len(raw) <= cap
    if b"\r" in raw:
        value = raw.replace(b"\r\n", b"\n")
        assert b"\r" not in value and value.replace(b"\n", b"\r\n") == raw
        raw = value
    assert all(32 <= value <= 126 or value in (9, 10) for value in raw)
    return raw.decode("ascii")


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def strict_json(raw):
    assert type(raw) is bytes
    def refuse(_):
        raise ValueError("nonfinite_json")
    return json.loads(raw.decode("ascii"), object_pairs_hook=unique_pairs, parse_constant=refuse)


def parse_proof(raw, phase, uid):
    assert phase in PHASES and type(raw) is bytes and 0 < len(raw) <= 4096
    value = strict_json(raw)
    keys = PROOF_KEYS | ({"child_pid", "child_start", "child_uid"} if phase == "PROCESS" else set())
    assert type(value) is dict and set(value) == keys
    for key, lower, upper in (("version", 1, 1), ("pid", 1, 2 ** 31 - 1), ("start", 1, 2 ** 63 - 1),
                              ("uid", 10000, 2 ** 31 - 1), ("fixture_bytes", 63, 63)):
        assert type(value[key]) is int and lower <= value[key] <= upper
    assert value["phase"] == phase and value["uid"] == uid and value["process"] == APP
    assert value["fixture_sha256"] == FIXTURE_SHA256
    for key, wanted in (("candidate_root_absent", True), ("publication_native_invoked", False), ("sdk_invoked", False)):
        assert type(value[key]) is bool and value[key] is wanted
    for key in ("external_free_before", "external_free_after", "userdata_free_before", "userdata_free_after"):
        # Before-copy observation includes the fixed missing bytes; accepted/reopened
        # data retains the actual admit(0) floor, without an invented extra reserve.
        floor = (EXTERNAL_FLOOR + (63 if key.endswith("before") else 0)
                 if key.startswith("external") else PROOF_USERDATA_FLOOR)
        assert type(value[key]) is int and floor <= value[key] <= 2 ** 63 - 1
    checks = value["checks"]
    assert type(checks) is dict and set(checks) == PHASES[phase][2] and all(type(v) is bool and v for v in checks.values())
    if phase == "PROCESS":
        for key, upper in (("child_pid", 2 ** 31 - 1), ("child_start", 2 ** 63 - 1), ("child_uid", 2 ** 31 - 1)):
            assert type(value[key]) is int and 0 < value[key] <= upper
        assert value["child_pid"] != value["pid"] and value["child_uid"] == uid
    return value


def match_parent_identities(proofs, phases=PHASES):
    assert set(proofs) == set(phases)
    identities = {tuple(proofs[phase][key] for key in ("pid", "start", "uid", "process")) for phase in phases}
    assert len(identities) == 1
    return True


def parse_instrumentation(raw):
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
            assert sep and key == "stream" and result is None and not fields and not runner and len(records) == 8
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
    assert not fields and runner and len(records) == 8 and result is not None
    methods = []
    for index in range(4):
        start, end = records[index * 2:index * 2 + 2]
        assert start[0] == 1 and end[0] == 0
        method = start[1].get("test")
        assert method in METHODS and method not in methods
        methods.append(method)
        for code, fields, extra in (start, end):
            assert set(fields) <= {"class", "current", "id", "numtests", "stream", "test"}
            assert fields.get("class") == CLASS and fields.get("test") == method
            assert fields.get("current") == str(index + 1) and fields.get("numtests") == "4" and fields.get("id") == "AndroidJUnitRunner"
            body = "\n".join([fields.get("stream", "")] + extra)
            assert body in ("", "\n" + CLASS + ":", CLASS + ":") if code == 1 else body == "."
    summary = "\n".join(result)
    match = re.fullmatch(r"\n\nTime: ((?:0|[1-9][0-9]{0,5})(?:\.[0-9]{1,9})?)\n\nOK \(4 tests\)\n{1,3}", summary)
    assert match and 0 <= float(match[1]) <= 120
    return {"passed": 4, "failed": 0, "methods": methods}


def parse_recovery_failure(raw):
    """Bind the one consumed v1 failure, without treating it as qualification."""
    text = normalized(raw, 131072)
    records, fields, result_seen, runner = [], {}, False, False
    for line in text.split("\n"):
        if line.startswith("INSTRUMENTATION_STATUS: "):
            assert not result_seen and not runner
            key, separator, value = line[len("INSTRUMENTATION_STATUS: "):].partition("=")
            assert separator and key in ("class", "current", "id", "numtests", "stream", "stack", "test")
            if key in ("class", "current", "id", "numtests", "test"):
                assert key not in fields
                fields[key] = value
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            assert not result_seen and not runner
            code = line.split(": ", 1)[1]
            assert code in ("1", "0", "-2")
            records.append((int(code), fields))
            fields = {}
        elif line.startswith("INSTRUMENTATION_RESULT: "):
            assert len(records) == 8 and not fields and not result_seen and not runner
            assert line.startswith("INSTRUMENTATION_RESULT: stream=")
            result_seen = True
        elif line.startswith("INSTRUMENTATION_CODE: "):
            assert result_seen and len(records) == 8 and not fields and not runner and line == "INSTRUMENTATION_CODE: -1"
            runner = True
        elif line.startswith("INSTRUMENTATION_"):
            raise AssertionError("unexpected_recovery_machine_record")
    assert not fields and len(records) == 8 and result_seen and runner
    results = {}
    for index in range(4):
        start, end = records[index * 2:index * 2 + 2]
        method = start[1].get("test")
        assert start[0] == 1 and end[0] in (0, -2) and method in METHODS and method not in results
        for _, fields in (start, end):
            assert fields == {"class": CLASS, "current": str(index + 1), "id": "AndroidJUnitRunner", "numtests": "4", "test": method}
        results[method] = end[0]
    process_method = PHASES["PROCESS"][1]
    assert results[process_method] == -2 and all(code == 0 for name, code in results.items() if name != process_method)
    assert text.count("INSTRUMENTATION_CODE: -1") == 1 and "INSTRUMENTATION_ABORTED:" not in text
    assert "java.lang.IllegalStateException" in text
    return {"passed": 3, "failed": 1, "failed_method": process_method, "qualification_passed": False}


def parse_packages(raw):
    result = {}
    for line in normalized(raw).split("\n"):
        if not line:
            continue
        match = re.fullmatch(r"(org\.locallore(?:\.[A-Za-z0-9_]+)+)\|([a-f0-9]{64})  (/data/app/[A-Za-z0-9_~+=./-]+/base\.apk)", line)
        assert match and match[1] not in result and ".." not in match[3].split("/")
        result[match[1]] = match[2]
    assert len(result) == 35
    return result


def parse_uids(raw, packages):
    result = {}
    for line in normalized(raw).splitlines():
        match = re.fullmatch(r"package:(org\.locallore(?:\.[A-Za-z0-9_]+)+) uid:([1-9][0-9]{0,9})", line)
        assert match and match[1] in packages and match[1] not in result
        uid = int(match[2])
        assert 10000 <= uid < 2 ** 31
        result[match[1]] = uid
    assert set(result) == set(packages) and len(set(result.values())) == 35
    return result


def parse_processes(raw, uids, known_passive):
    lines = normalized(raw).splitlines()
    assert lines and lines[0].split() == ["PID", "UID", "NAME"]
    owned, passive, pids, names = [], [], set(), set()
    for line in lines[1:]:
        if not line.strip():
            continue
        fields = line.split()
        assert len(fields) == 3 and fields[0].isdigit() and fields[1].isdigit()
        pid, uid, name = int(fields[0]), int(fields[1]), fields[2]
        assert 0 < pid < 2 ** 31 and 0 <= uid < 2 ** 31 and pid not in pids
        pids.add(pid)
        if name == "org.locallore" or name.startswith(("org.locallore.", "org.locallore:")):
            assert name not in names
            names.add(name)
            row = {"pid": pid, "uid": uid, "name": name}
            if name in (APP, TEST, SERVICE, PROVIDER):
                assert uid == uids[APP if name in (APP, SERVICE) else TEST]
                owned.append(row)
            else:
                assert name in known_passive and name.endswith(".test:chooser_test_provider")
                assert uid == known_passive[name] == uids[name.split(":")[0]]
                passive.append(row)
    return {"owned": sorted(owned, key=lambda row: row["name"]), "passive": sorted(passive, key=lambda row: row["name"])}


def parse_storage(df, devices):
    match = re.fullmatch(r"([1-9][0-9]{0,18})\n([1-9][0-9]{0,18})\n", normalized(devices, 100))
    assert match
    value = parse_df(df, int(match[1]), int(match[2]))
    assert value is not None and value["available_bytes"] >= USERDATA_FLOOR
    return value


def parse_volume(raw):
    rows = normalized(raw, 4096).splitlines()
    assert len(rows) == 1
    match = re.fullmatch(r"(public:[0-9]{1,5},[0-9]{1,5}) mounted ([A-Fa-f0-9]{4}-[A-Fa-f0-9]{4})", rows[0])
    assert match
    return {"id": match[1], "uuid": match[2]}


def proof_command(name, uid, root=PROOF_ROOT):
    assert root in (PROOF_ROOT, RECOVERY_ROOT) and name in (RECOVERY_FILES if root == RECOVERY_ROOT else PROOF_FILES)
    assert type(uid) is int and 10000 <= uid < 2 ** 31
    path = root + "/" + name
    size = "-eq 0" if name.endswith(".txt") else "-gt 0"
    return ("run-as", APP, "sh", "-c", "test -d no_backup && test ! -L no_backup && test -d " + root +
            " && test ! -L " + root + " && test -f " + path + " && test ! -L " + path +
            " && test $(stat -c %u " + path + ") -eq " + str(uid) + " && test $(wc -c < " + path + ") " + size +
            " && test $(wc -c < " + path + ") -le 4096 && cat " + path)


def validate_proposal(proposal, final=True):
    assert type(proposal) is dict
    recovery = proposal.get("scope") == "android_receipt_recovery"
    assert set(proposal) == PROPOSAL_KEYS | ({"failure_path", "failure_sha256"} if recovery else set())
    assert type(proposal["version"]) is int and proposal["version"] == 1
    assert proposal["scope"] in ("android_receipt_qualification", "android_receipt_readiness", "android_receipt_recovery")
    readiness = proposal["scope"] in ("android_receipt_readiness", "android_receipt_recovery")
    assert proposal["allow_device_calls"] is False and proposal["root_go_pending"] is True
    assert proposal["selected_alias"] == "B" and re.fullmatch(r"emulator-[1-9][0-9]{3,5}", proposal["serial"])
    assert re.fullmatch(r"[a-f0-9]{40}", proposal["source_commit"])
    prior, uids = proposal["prior_packages"], proposal["prior_uid_map"]
    assert type(prior) is dict and type(uids) is dict and len(prior) == 35 and set(prior) == set(uids) and {APP, TEST} <= set(prior)
    assert all(re.fullmatch(r"org\.locallore(?:\.[A-Za-z0-9_]+)+", key) and re.fullmatch(r"[a-f0-9]{64}", value) for key, value in prior.items())
    assert all(type(value) is int and 10000 <= value < 2 ** 31 for value in uids.values()) and len(set(uids.values())) == 35
    passive = proposal["known_passive_provider_uids"]
    assert type(passive) is dict and len(passive) == 9
    assert all(name.endswith(".test:chooser_test_provider") and name.split(":")[0] in uids and type(uid) is int and uid == uids[name.split(":")[0]] for name, uid in passive.items())
    assert set(proposal["apk_paths"]) == set(proposal["apk_sha256"]) == (set() if readiness else {APP, TEST})
    if not readiness:
        for key, name in ((APP, "app-debug.apk"), (TEST, "app-debug-androidTest.apk")):
            path = Path(proposal["apk_paths"][key])
            assert path.is_absolute() and path.name == name
    assert Path(proposal["evidence_root"]).is_absolute() and Path(proposal["adb_path"]).is_absolute() and Path(proposal["adb_path"]).name == "adb.exe"
    assert type(proposal["source_final"]) is bool and type(proposal["artifacts_final"]) is bool and type(proposal["bindings"]) is dict
    if final:
        assert proposal["source_final"] is True and proposal["artifacts_final"] is (not readiness)
        sources = SOURCE_FILES[:3] if readiness else SOURCE_FILES
        assert all(str((ROOT / name).resolve()) in proposal["bindings"] for name in sources)
        for name, digest in proposal["bindings"].items():
            path = Path(name)
            assert path.is_absolute() and re.fullmatch(r"[a-f0-9]{64}", digest) and sha(path.read_bytes()) == digest
        for package, path in proposal["apk_paths"].items():
            assert re.fullmatch(r"[a-f0-9]{64}", proposal["apk_sha256"][package])
            assert sha(Path(path).read_bytes()) == proposal["apk_sha256"][package]
        if recovery:
            path = Path(proposal["failure_path"])
            assert path.is_absolute() and path.name == "command-0025.stdout.bin"
            assert proposal["bindings"].get(str(path.resolve())) == proposal["failure_sha256"]
            raw = path.read_bytes()
            assert sha(raw) == proposal["failure_sha256"]
            parse_recovery_failure(raw)
    return True


def authorize(proposal_path, authorization_path, evidence):
    raw = Path(proposal_path).read_bytes()
    proposal = strict_json(raw)
    authorization = strict_json(Path(authorization_path).read_bytes())
    assert type(authorization) is dict and set(authorization) == {"version", "proposal_sha256", "allow_device_calls", "root_go_pending"}
    assert type(authorization["version"]) is int and authorization["version"] == 1
    assert authorization["proposal_sha256"] == sha(raw) and authorization["allow_device_calls"] is True and authorization["root_go_pending"] is False
    assert Path(proposal["evidence_root"]).resolve() == Path(evidence).resolve()
    validate_proposal(proposal)
    return proposal


class Owner:
    def __init__(self, proposal):
        self.proposal = proposal
        self.directory = Path(proposal["evidence_root"]) / "cohort"
        self.directory.mkdir(exist_ok=False)
        self.commands = self.directory / "commands"
        self.commands.mkdir()
        self.stage, self.clean, self.count = "before", True, 0
        self.recovery = proposal["scope"] == "android_receipt_recovery"
        self.readiness = proposal["scope"] in ("android_receipt_readiness", "android_receipt_recovery")
        self.until = time.monotonic() + (75 if self.readiness else AGGREGATE_SECONDS)
        self.installs, self.methods = {APP: 0, TEST: 0}, 0
        self.inventories = 0
        self.pending_install, self.pending_read = None, None
        self.volume = None

    def dispatch(self, args, deadline=15, cap=65536):
        assert self.clean
        if args == ["devices", "-l"]:
            assert self.readiness and self.stage == "before" and self.inventories == 0
            self.inventories += 1
        elif args[0] == "install":
            package = self.pending_install
            assert not self.readiness and self.stage == "updating" and package in (APP, TEST) and self.installs[package] == 0
            assert args == ["install", "--no-streaming", "-r", self.proposal["apk_paths"][package]]
            self.installs[package] += 1
            self.pending_install = None
        else:
            assert len(args) == 2 and args[0] == "shell"
            op = tuple(shlex.split(args[1]))
            if op in (*IDENTITY, PACKAGES, UIDS, PS, DF, DEVICES, VOLUMES):
                assert self.stage in ("before", "installed", "after", "final")
            elif op == PROOF_ABSENT:
                assert self.stage in ("before", "installed", "final")
            elif op == INTERNAL_CANDIDATE_ABSENT:
                assert self.readiness and self.stage in ("before", "final")
            elif op == INSTRUMENT:
                assert not self.readiness and self.stage == "instrumentation" and self.methods == 0
                self.methods += 1
            elif op == PROOF_MANIFEST:
                assert not self.readiness and self.stage == "proofs" and self.pending_read is None
            elif op == RECOVERY_MANIFEST:
                assert self.recovery and self.stage == "proofs" and self.pending_read is None
            else:
                assert (not self.readiness or self.recovery) and self.stage == "proofs" and op == self.pending_read
                self.pending_read = None
        remaining = self.until - time.monotonic()
        assert remaining > 0
        deadline = min(deadline, remaining)
        self.count += 1
        stem = self.commands / ("command-%04d" % self.count)
        try:
            command = [self.proposal["adb_path"]] + ([] if args == ["devices", "-l"] else ["-s", self.proposal["serial"]]) + args
            value = host.run_process(command, deadline=deadline, max_output=cap)
        except BaseException:
            self.clean = False
            raise
        self.clean &= value.cleanup_complete is True
        try:
            with stem.with_suffix(".stdout.bin").open("xb") as stream:
                stream.write(value.stdout)
                stream.flush()
                os.fsync(stream.fileno())
            write_json(stem.with_suffix(".json"), {"index": self.count, "stage": self.stage, "alias": "inventory" if args == ["devices", "-l"] else "B", "args": args,
                "deadline_seconds": deadline, "cap_bytes": cap, "status": value.status, "returncode": value.returncode,
                "cleanup_complete": value.cleanup_complete, "stdout_bytes": len(value.stdout), "stdout_sha256": sha(value.stdout),
                "stderr_bytes": value.stderr_bytes})
        except BaseException:
            self.clean = False
            raise
        assert self.clean and value.status == "completed" and value.returncode == 0
        return value.stdout

    def shell(self, op, deadline=15, cap=65536):
        return self.dispatch(["shell", shlex.join(op)], deadline, cap)

    def facts(self, label, packages):
        host_free = {letter: shutil.disk_usage(letter + ":/").free for letter in ("C", "D")}
        assert host_free["C"] >= 4 * 1024 ** 3 + 128 * 1024 ** 2 and host_free["D"] >= 10 * 1024 ** 3
        for op, expected in zip(IDENTITY, ("1\n", "35\n", "x86_64\n", "4096\n")):
            assert normalized(self.shell(op), 128) == expected
        observed = parse_packages(self.shell(PACKAGES))
        assert observed == packages
        uids = parse_uids(self.shell(UIDS), packages)
        assert uids == self.proposal["prior_uid_map"]
        processes = parse_processes(self.shell(PS), uids, self.proposal["known_passive_provider_uids"])
        if not self.recovery:
            assert processes["owned"] == []
        volume = parse_volume(self.shell(VOLUMES, cap=4096))
        if self.volume is None:
            self.volume = volume
        assert volume == self.volume
        storage = parse_storage(self.shell(DF), self.shell(DEVICES, cap=128))
        value = {"version": 1, "packages": observed, "uid_map": uids, "processes": processes,
                 "volume": volume, "userdata": storage, "host_free": host_free}
        write_json(self.directory / (label + "-facts.json"), value)
        return value


def run_cohort(owner):
    proposal = owner.proposal
    prior = proposal["prior_packages"]
    owner.facts("before", prior)
    assert owner.shell(PROOF_ABSENT, cap=4096) == b""
    owner.stage = "updating"
    for package in (APP, TEST):
        path = Path(proposal["apk_paths"][package])
        assert sha(path.read_bytes()) == proposal["apk_sha256"][package]
        owner.pending_install = package
        output = owner.dispatch(["install", "--no-streaming", "-r", str(path)], deadline=35, cap=4096)
        assert normalized(output, 4096) in ("Success\n", "Performing Push Install\nSuccess\n")
    expected = {**prior, **proposal["apk_sha256"]}
    owner.stage = "installed"
    owner.facts("installed", expected)
    assert owner.shell(PROOF_ABSENT, cap=4096) == b""
    owner.stage = "instrumentation"
    tests = parse_instrumentation(owner.shell(INSTRUMENT, deadline=120, cap=131072))
    write_json(owner.directory / "instrumentation-v1.json", tests)
    owner.stage = "after"
    owner.facts("after", expected)
    owner.stage = "proofs"
    manifest = normalized(owner.shell(PROOF_MANIFEST, cap=4096), 4096).splitlines()
    assert len(manifest) == 8 and set(manifest) == {PROOF_ROOT + "/" + name for name in PROOF_FILES}
    proofs = {}
    for phase, (stem, _, _) in PHASES.items():
        ready = proof_command(stem + "-ready-v1.txt", proposal["prior_uid_map"][APP])
        owner.pending_read = ready
        assert owner.shell(ready, cap=4096) == b""
        command = proof_command(stem + "-v1.json", proposal["prior_uid_map"][APP])
        owner.pending_read = command
        proofs[phase] = parse_proof(owner.shell(command, cap=4096), phase, proposal["prior_uid_map"][APP])
        write_json(owner.directory / (stem + "-proof-v1.json"), proofs[phase])
    match_parent_identities(proofs)
    owner.stage = "final"
    final = owner.facts("final", expected)
    return {"tests": tests, "proofs": proofs, "final": final, "synthetic_only": True,
            "real_model_or_SDK_qualified": False, "physical_phone_qualified": False}


def run_readiness(owner):
    raw = normalized(owner.dispatch(["devices", "-l"], cap=8192), 8192).splitlines()
    assert raw and raw[0] == "List of devices attached"
    rows = [line.split() for line in raw[1:] if line.strip()]
    assert all(len(row) >= 2 for row in rows) and len({row[0] for row in rows}) == len(rows)
    assert sum(row[0] == owner.proposal["serial"] and row[1] == "device" for row in rows) == 1
    inventory = {"selected_ready": True, "emulators": sum(row[0].startswith("emulator-") for row in rows),
                 "other_devices": sum(not row[0].startswith("emulator-") for row in rows)}
    write_json(owner.directory / "inventory-v1.json", inventory)
    owner.facts("before", owner.proposal["prior_packages"])
    assert owner.shell(INTERNAL_CANDIDATE_ABSENT, cap=4096) == b""
    assert owner.shell(PROOF_ABSENT, cap=4096) == b""
    owner.stage = "final"
    final = owner.facts("final", owner.proposal["prior_packages"])
    assert owner.shell(INTERNAL_CANDIDATE_ABSENT, cap=4096) == b""
    assert owner.shell(PROOF_ABSENT, cap=4096) == b""
    return {"read_only": True, "inventory": inventory, "final": final, "receipt_qualification_executed": False,
            "internal_candidate_absent": True, "fresh_proof_namespace_absent": True,
            "external_candidate_absence_inferred": False}


def run_recovery(owner):
    """Read the fixed three existing v1 proofs; never repairs or retries v1."""
    failure = parse_recovery_failure(Path(owner.proposal["failure_path"]).read_bytes())
    before = owner.facts("before", owner.proposal["prior_packages"])
    assert owner.shell(PROOF_ABSENT, cap=4096) == b""  # Future v2 proof root must remain absent.
    owner.stage = "proofs"
    manifest = normalized(owner.shell(RECOVERY_MANIFEST, cap=4096), 4096).splitlines()
    assert len(manifest) == 6 and set(manifest) == {RECOVERY_ROOT + "/" + name for name in RECOVERY_FILES}
    proofs = {}
    for phase in RECOVERY_PHASES:
        stem = PHASES[phase][0]
        ready = proof_command(stem + "-ready-v1.txt", owner.proposal["prior_uid_map"][APP], RECOVERY_ROOT)
        owner.pending_read = ready
        assert owner.shell(ready, cap=4096) == b""
        command = proof_command(stem + "-v1.json", owner.proposal["prior_uid_map"][APP], RECOVERY_ROOT)
        owner.pending_read = command
        proofs[phase] = parse_proof(owner.shell(command, cap=4096), phase, owner.proposal["prior_uid_map"][APP])
        write_json(owner.directory / (stem + "-recovery-proof-v1.json"), proofs[phase])
    match_parent_identities(proofs, RECOVERY_PHASES)
    owner.stage = "final"
    final = owner.facts("final", owner.proposal["prior_packages"])
    assert owner.shell(PROOF_ABSENT, cap=4096) == b""
    return {"read_only": True, "original_failure": failure, "proofs": proofs, "before": before, "final": final,
            "owned_quiet_before": before["processes"]["owned"] == [], "owned_quiet_final": final["processes"]["owned"] == [],
            "process_proof_present": False, "fresh_v2_proof_absent": True, "qualification_passed": False,
            "receipt_qualification_executed": False}


def worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(64) == REQUEST
    proposal = authorize(proposal_path, authorization_path, evidence)
    owner = Owner(proposal)
    result, failure = None, None
    try:
        result = run_recovery(owner) if owner.recovery else run_readiness(owner) if owner.readiness else run_cohort(owner)
    except BaseException:
        failure = "receipt_qualification_stopped"
    value = {"version": 1, "scope": proposal["scope"], "status": "observed" if failure is None else "stopped",
             "failure": failure, "stage": owner.stage, "clients_cleaned": owner.clean, "command_count": owner.count,
             "instrumentation_commands": owner.methods, "installs": owner.installs, "result": result}
    write_json(owner.directory / "result-v1.json", value)
    print(json.dumps({key: value[key] for key in value if key != "result"}))
    return 0 if failure is None and owner.clean else 2


def run_owned(proposal_path, authorization_path, evidence):
    proposal = authorize(proposal_path, authorization_path, evidence)
    outer_seconds = 90 if proposal["scope"] in ("android_receipt_readiness", "android_receipt_recovery") else OUTER_SECONDS
    evidence = Path(evidence)
    write_json(evidence / "receipt-owned-start-v1.json", {"version": 1, "deadline_seconds": outer_seconds,
        "time_ns": time.time_ns(), "proposal_sha256": sha(Path(proposal_path).read_bytes()),
        "authorization_sha256": sha(Path(authorization_path).read_bytes())})
    value = host.run_process([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "worker",
        "--proposal", str(proposal_path), "--authorization", str(authorization_path), "--evidence", str(evidence)],
        request=REQUEST, deadline=outer_seconds, max_output=32768)
    with (evidence / "receipt-owned-stdout-v1.bin").open("xb") as stream:
        stream.write(value.stdout)
        stream.flush()
        os.fsync(stream.fileno())
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
