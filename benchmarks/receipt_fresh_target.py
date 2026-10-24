"""Explicitly admitted synthetic receipt qualification on a new owned emulator.

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
    APP: "8232c5f81284b31d392e447968a0aa87ba853e2781fa2ae7245feaec405447f8",
    TEST: "a8aecff0610a45384531cf55de684741e766c466487e8a95daaa65de8a596b2a",
}
SOURCE_FILES = ("benchmarks/receipt_fresh_target.py", "benchmarks/receipt_avd_environment.py",
                "scripts/tests/test_receipt_fresh_target.py", *contract.SOURCE_FILES)
PROPOSAL_KEYS = frozenset(("version", "scope", "source_commit", "source_final", "artifacts_final",
    "allow_device_calls", "root_go_pending", "selected_alias", "environment_proposal_path", "running_path",
    "running_sha256", "adb_path", "apk_paths", "apk_sha256", "bindings", "evidence_root"))
REQUEST = b"receipt-fresh-target-v1\n"
BOOT_SECONDS = 60
AVD_NAME = ("emu", "avd", "name")
sha, write_json, normalized = contract.sha, contract.write_json, contract.normalized


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
    assert value["scope"] == "receipt_fresh_target" and value["selected_alias"] == "C"
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


class Owner:
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
        self.until = time.monotonic() + contract.AGGREGATE_SECONDS
        self.installs, self.methods = {APP: 0, TEST: 0}, 0
        self.pending_install, self.pending_read = None, None
        self.uid_map, self.volume = None, None
        self.boot_returncode, self.boot_stderr_bytes = None, None

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
            elif op in (contract.PROOF_ABSENT, contract.INTERNAL_CANDIDATE_ABSENT):
                assert self.stage == "installed"
            elif op == contract.INSTRUMENT:
                assert self.stage == "instrumentation" and self.methods == 0
                self.methods += 1
            elif op == contract.PROOF_MANIFEST:
                assert self.stage == "proofs" and self.pending_read is None
            else:
                assert self.stage == "proofs" and op == self.pending_read
                self.pending_read = None
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
            write_json(stem.with_suffix(".json"), {"index": self.count, "stage": self.stage, "alias": "C", "args": args,
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
        assert normalized(self.dispatch(list(AVD_NAME), cap=1024), 1024) == self.avd_name + "\nOK\n"
        for op, expected in zip(contract.IDENTITY, ("1\n", "35\n", "x86_64\n", "4096\n")):
            assert normalized(self.shell(op), 128) == expected
        observed = parse_packages(self.shell(contract.PACKAGES), packages)
        uids = parse_uids(self.shell(contract.UIDS), observed)
        if packages:
            if self.uid_map is None:
                assert label == "installed"
                self.uid_map = uids
            assert uids == self.uid_map
        processes = contract.parse_processes(self.shell(contract.PS), uids, {})
        assert processes == {"owned": [], "passive": []}
        volume = contract.parse_volume(self.shell(contract.VOLUMES, cap=4096))
        if self.volume is None:
            self.volume = volume
        assert volume == self.volume
        storage = contract.parse_storage(self.shell(contract.DF), self.shell(contract.DEVICES, cap=128))
        value = {"version": 1, "packages": observed, "uid_map": uids, "processes": processes,
                 "volume": volume, "userdata": storage, "host_free": host_free}
        write_json(self.directory / (label + "-facts.json"), value)
        return value


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
    assert owner.shell(contract.PROOF_ABSENT, cap=4096) == b""
    assert owner.shell(contract.INTERNAL_CANDIDATE_ABSENT, cap=4096) == b""
    owner.stage = "instrumentation"
    tests = contract.parse_instrumentation(owner.shell(contract.INSTRUMENT, deadline=120, cap=131072))
    write_json(owner.directory / "instrumentation-v1.json", tests)
    owner.stage = "after"
    owner.facts("after", owner.proposal["apk_sha256"])
    owner.stage = "proofs"
    manifest = normalized(owner.shell(contract.PROOF_MANIFEST, cap=4096), 4096).splitlines()
    assert len(manifest) == 8 and set(manifest) == {contract.PROOF_ROOT + "/" + name for name in contract.PROOF_FILES}
    proofs = {}
    for phase, (stem, _, _) in contract.PHASES.items():
        ready = contract.proof_command(stem + "-ready-v1.txt", owner.uid_map[APP])
        owner.pending_read = ready
        assert owner.shell(ready, cap=4096) == b""
        command = contract.proof_command(stem + "-v1.json", owner.uid_map[APP])
        owner.pending_read = command
        proofs[phase] = contract.parse_proof(owner.shell(command, cap=4096), phase, owner.uid_map[APP])
        write_json(owner.directory / (stem + "-proof-v1.json"), proofs[phase])
    contract.match_parent_identities(proofs)
    owner.stage = "final"
    final = owner.facts("final", owner.proposal["apk_sha256"])
    return {"tests": tests, "proofs": proofs, "before": before, "installed": installed, "final": final,
            "synthetic_only": True, "real_model_or_SDK_qualified": False, "physical_phone_qualified": False}


def worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(64) == REQUEST
    proposal = authorize(proposal_path, authorization_path, evidence)
    owner = Owner(proposal, open_lease(proposal))
    result, failure = None, None
    try:
        result = run_cohort(owner)
    except BaseException:
        failure = "fresh_target_qualification_stopped"
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
    write_json(evidence / "receipt-owned-start-v1.json", {"version": 1, "deadline_seconds": contract.OUTER_SECONDS,
        "time_ns": time.time_ns(), "proposal_sha256": sha(Path(proposal_path).read_bytes()),
        "authorization_sha256": sha(Path(authorization_path).read_bytes())})
    lease.check()
    value = host.run_process([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "worker",
        "--proposal", str(proposal_path), "--authorization", str(authorization_path), "--evidence", str(evidence)],
        request=REQUEST, deadline=contract.OUTER_SECONDS, max_output=32768)
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
