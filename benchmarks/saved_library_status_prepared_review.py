"""Review the preserved SDK23 prepared guest before proposing any reuse.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import os
from io import BytesIO
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from zipfile import BadZipFile, ZipFile
from zlib import error as DeflateError

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import adb_held_socket_probe as python_pins
from benchmarks import owned_saved_library_status as owner
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import saved_library_status_binding as artifacts
from benchmarks import saved_library_status_handoff as h

RECOVERY = Path("D:/Dev/Recovery/LocalLore/2026-11-09-saved-library-owned-operation-v1")
MANIFEST = RECOVERY / "records-manifest-v1.json"
ARCHIVE = RECOVERY / "records-v1.zip"
RECORD_ROOTS = {
    "launch": h.OUT.with_name("2026-11-09-saved-library-approved-run-v1"),
    "attempt": h.ATTEMPT_ROOT,
    "guest-receipts": h.GUEST,
    "plan": h.OUT,
}
EXECUTED_ROOT = Path("D:/Worktrees/LocalLore-saved-library-readiness-v1")
EXECUTED_HEAD = "edbb6124b3a68c27e5d9f24f5645a66da0c90aa8"
SCOPE = "sdk23-saved-library-prepared-review-v1"
REVIEW_CAP = 16 * 1024**2
_need = env.require
_same = owner._same


def _archive(manifest_pin):
    manifest = h.at(manifest_pin, MANIFEST)
    owner._obj(manifest, ("archive", "original_and_archive_bytes", "original_bytes", "records", "records_allowance",
                         "records_by_name", "terminal", "verification"), "archive")
    pins = manifest["records_by_name"]
    count = manifest["records"]
    owner._int(count, 1, 128, "archive")
    _need(type(pins) is dict and len(pins) == count, "archive")
    for name, pin in pins.items():
        rel = PurePosixPath(name)
        _need(rel.as_posix() == name and not rel.is_absolute() and ".." not in rel.parts and "\\" not in name and ":" not in name
              and len(rel.parts) > 1 and rel.parts[0] in RECORD_ROOTS, "archive")
        owner.binding(pin, max_bytes=h.RECORD_CAP)
        _need(pin["path"] == str(RECORD_ROOTS[rel.parts[0]].joinpath(*rel.parts[1:])), "archive")
    _need(len({name.casefold() for name in pins}) == count, "archive")
    for field, name in (("terminal", "launch/launch-terminal-v1.json"),
                        ("verification", "launch/terminal-verification-v1.json")):
        _need(name in pins and _same(manifest[field], pins[name]), "archive")

    archive = manifest["archive"]
    h._pin_at(archive, ARCHIVE, REVIEW_CAP)
    size = sum(pin["bytes"] for pin in pins.values())
    _need(0 < size <= REVIEW_CAP and _same(manifest["original_bytes"], size)
          and _same(manifest["original_and_archive_bytes"], size + archive["bytes"])
          and _same(manifest["records_allowance"], 256 * 1024**2), "archive")
    raw_records = {}
    with ZipFile(BytesIO(h.files._bound(archive, cap=REVIEW_CAP))) as snapshot:
        rows = snapshot.infolist()
        _need(len(rows) == count and {row.filename for row in rows} == set(pins), "archive")
        for row in rows:
            pin = pins[row.filename]
            _need(not row.is_dir() and row.file_size == pin["bytes"], "archive")
            raw = h.files._bound(pin, cap=h.RECORD_CAP)
            _need(snapshot.read(row) == raw, "archive")
            raw_records[row.filename] = raw
    return pins, raw_records


def _check_supervisor(row):
    owner._obj(row, ("status", "worker_returncode", "cleanup_complete", "output_capture_complete",
                    "elapsed_ms", "stderr_bytes", "stdout_bytes"), "supervisor")
    _need(row["status"] == "child_exited" and _same(row["worker_returncode"], 1)
          and row["cleanup_complete"] is True and row["output_capture_complete"] is True, "supervisor")
    for field in ("elapsed_ms", "stderr_bytes", "stdout_bytes"):
        owner._int(row[field], 0, 2**31 - 1, "supervisor")


def _check_preboot(worker):
    owner._obj(worker, owner.WORKER_KEYS, "preboot")
    _need(_same(worker["version"], 1) and worker["protocol"] == owner.PROTOCOL
          and worker["reason"] == "not_authorized" and worker["stop_requested"] is False
          and _same(worker["guest_ancestry"], [])
          and all(worker[key] is None for key in (
              "launcher", "guest", "guest_capture", "guest_inputs", "guest_job", "guest_preflight",
              "guest_returncode", "guest_terminal", "boot_claim", "readiness", "ready", "running",
          )), "preboot")
    owner._process(worker["worker"])
    owner._process(worker["server"])
    owner._int(worker["server_returncode"], 1, 1, "preboot")
    owner.binding(worker["server_capture"])
    cleanup = worker["cleanup"]
    owner._obj(cleanup, owner.CLEANUP_KEYS, "preboot")
    _need(all(cleanup[key] is (not key.startswith("guest_")) for key in owner.CLEANUP_KEYS), "preboot")


def _check_ledger_entry(entry, prepare_digest):
    _need(entry["root"] == str(h.GUEST) and entry["state"] == "prepared"
          and _same(entry["reserved_bytes"], storage.RESERVATION_BYTES)
          and entry["proposal_sha256"] == prepare_digest
          and all(entry[key] is None for key in ("closure", "recovery", "retirement", "retirement_receipt")),
          "ledger")


def _failure(pins, raw):
    from benchmarks import saved_library_status_activation as activation
    from benchmarks import saved_library_status_operation as operation

    unbound = object()

    def record(name, expected=unbound):
        _need(name in pins and (expected is unbound or _same(pins[name], expected)), "failure")
        return env.decode_json(raw[name])

    claim = record("launch/launch-claim-v1.json")
    terminal = record("launch/launch-terminal-v1.json")
    _need(claim["source"] == EXECUTED_HEAD and claim["no_retry"] is True and terminal["no_retry"] is True
          and _same(terminal["returncode"], 1) and terminal["timed_out"] is False, "failure")
    result = record("attempt/operation-result-v1.json")
    _need(result["scope"] == h.OPERATION_SCOPE and result["passed"] is False
          and result["feature_acceptance"] is False and result["reason"] == "owner"
          and _same(result["authority"], claim["authority"]), "failure")
    _check_supervisor(record("attempt/operation-supervisor-v1.json", result["supervisor"]))
    stage = record("attempt/operation-stage-v1.json", result["stages"])
    _need(stage["phase"] == "activation" and stage["reason"] == "activation"
          and stage["passed"] is False and stage["closure"] is None
          and _same(stage["authority"], result["authority"]) and _same(stage["attempt"], result["attempt"]),
          "failure")
    authority, plan = h.approved_plan(result["authority"], result["attempt"])
    _need(_same(authority["proposal"], claim["proposal"])
          and authority["approval_reference"] == claim["approval_reference"], "failure")
    operation._verify_prepare(stage["prepare"], plan["prepare"])
    _need(_same(stage["prepare_evidence"], operation._prepare_evidence(plan["prepare"], stage["worker"])),
          "prepared")

    active = record("attempt/activation-v1/activation-result-v1.json", stage["activation"])
    _need(active["scope"] == activation.SCOPE and active["passed"] is False
          and active["feature_acceptance"] is False and active["reason"] == "owner_terminal"
          and all(_same(active[key], stage[key]) for key in ("authority", "attempt", "admission")), "failure")
    _check_supervisor(record("attempt/activation-v1/runtime-supervisor-v1.json", active["supervisor"]))
    runtime = record("attempt/activation-v1/runtime-result-v1.json", active["runtime"])
    _need(runtime["reason"] == "owner_not_ready" and runtime["passed"] is False
          and _same(runtime["admission"], stage["admission"])
          and all(runtime[key] is None for key in ("running", "controller", "controller_supervisor", "closure")),
          "failure")
    stopped = record("attempt/activation-v1/owner-terminal-v1.json", runtime["owner_terminal"])
    started = record("attempt/activation-v1/owner-started-v1.json", runtime["owner_started"])
    _need(_same(stopped["returncode"], 1) and stopped["capture_closed"] is True
          and stopped["stop_published"] is False and stopped["observer_closed"] is False
          and _same(stopped["owner"], started["owner"]) and _same(started["admission"], stage["admission"]),
          "preboot")

    public = record("attempt/owned-v1/result-v1.json")
    _need(public["protocol"] == owner.PROTOCOL and public["qualified_target"] is False
          and public["feature_acceptance"] is False and _same(public["admission"], stage["admission"]), "preboot")
    request = record("attempt/owned-v1/request-v1.json", public["request"])
    announced = record("attempt/owned-v1/started-v1.json", public["started"])
    _check_supervisor(record("attempt/owned-v1/owner-result-v1.json", public["owner"]))
    worker = record("attempt/owned-v1/worker-result-v1.json", public["worker_result"])
    _check_preboot(worker)
    _need(_same(request["owner"], started["owner"]) and _same(announced["request"], public["request"])
          and _same(worker["request"], public["request"]) and _same(worker["worker"], announced["worker"])
          and _same(worker["admission"], stage["admission"]), "preboot")
    server = record("attempt/owned-v1/server-capture-v1.json", worker["server_capture"])
    _need(server["status"] == "terminated" and server["capture_complete"] is True and server["pipes_closed"] is True
          and _same(server["server"], worker["server"]) and _same(server["returncode"], worker["server_returncode"]),
          "preboot")

    admission = record("attempt/admission-v1.json", stage["admission"])
    receipt = pins["attempt/owned-v1/guest-inputs-v1.json"]
    artifacts.verify_artifacts(admission["artifacts"])
    owner.REPLAY.verify_guest_inputs(receipt, admission, stage["admission"])
    proposal = record("attempt/run-proposal-v1.json", admission["guest"]["proposal"])
    _need(_same(proposal["prepare_proposal"], plan["prepare"]) and _same(proposal["prepare_result"], stage["prepare"]),
          "prepared")
    return receipt, proposal, plan


def _verify_original_preparation(proposal, plan):
    # The installed-file pins deliberately include absolute paths to the
    # original checkout. Replay under that checkout's unchanged reader.
    _need(Path(plan["source_root"]) == EXECUTED_ROOT
          and _same(plan["python"], python_pins._python_bindings()), "source")
    sources = plan["sources"]
    names = {Path(pin["path"]).relative_to(EXECUTED_ROOT) for pin in sources}
    current_names = {Path(pin["path"]).relative_to(h.ROOT) for pin in owner.source_bindings()}
    _need(names == current_names and len(names) == len(sources), "source")
    for pin in sources:
        env.check_binding(pin)
    command = (
        "import sys; sys.path.insert(0, str(__import__('pathlib').Path.cwd())); "
        "from benchmarks import receipt_avd_environment as env; "
        "value=env.decode_json(sys.stdin.buffer.read()); "
        "env.validate_proposal(value, 'run'); "
        "sys.stdout.buffer.write(env.encoded(env.verify_prepared(value, initial=True)))"
    )
    result = subprocess.run([plan["python"]["executable"]["path"], "-I", "-S", "-B", "-c", command],
                            cwd=EXECUTED_ROOT, input=env.encoded(proposal), capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW, timeout=120)
    _need(result.returncode == 0 and result.stderr == b"" and len(result.stdout) <= h.RECORD_CAP, "prepared")
    prepared = env.decode_json(result.stdout)
    _need(_same(prepared, h.at(proposal["prepared"], h.GUEST / "prepared-v1.json")), "prepared")
    for pin in sources:
        env.check_binding(pin)
    return prepared


def inspect(manifest_pin, ledger_pin):
    """Verify existing records and the prepared guest without taking a lock."""
    absent = (h.GUEST / owner.BOOT_CLAIM_FILE, h.GUEST / "guest-storage-closure-v1.json",
              h.OWNED_ROOT / "running-v1.json", h.OWNED_ROOT / "guest-output-v1")
    _need(not any(os.path.lexists(path) for path in absent), "already_used")
    lock = h.LEDGER.with_name("admission.lock")
    _need(not os.path.lexists(lock), "ledger")
    current_ledger, entry = h.ledger_entry(h.GUEST)
    _need(_same(ledger_pin, current_ledger), "ledger")
    pins, raw = _archive(manifest_pin)
    receipt, proposal, plan = _failure(pins, raw)
    _check_ledger_entry(entry, proposal["prepare_proposal"]["sha256"])
    prepared = _verify_original_preparation(proposal, plan)
    archive_pin = h.at(manifest_pin, MANIFEST)["archive"]
    for pin in (manifest_pin, archive_pin, ledger_pin, *pins.values(), *prepared["immutable"]):
        env.check_binding(pin)
    _need(not os.path.lexists(lock), "ledger")
    userdata = Path(proposal["paths"]["content"]) / "userdata-qemu.img"
    _need(not any(os.path.lexists(path) for path in (*absent, userdata)), "already_used")
    return dict(version=1, scope=SCOPE, status="prepared_candidate", manifest=manifest_pin, ledger=ledger_pin,
                guest_inputs=receipt, reserved_bytes=entry["reserved_bytes"], execution_authorized=False)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        _need(type(args) is list and len(args) == 4 and args[0] == "--manifest-sha256"
              and args[2] == "--ledger-sha256"
              and all(type(args[i]) is str and re.fullmatch("[0-9a-f]{64}", args[i]) for i in (1, 3)), "binding")
        manifest, _ = h.read(MANIFEST)
        ledger, _ = h.read(h.LEDGER, h.STORAGE_CAP)
        _need(manifest["sha256"] == args[1] and ledger["sha256"] == args[3], "binding")
        result, status = inspect(manifest, ledger), 0
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, BadZipFile, DeflateError, subprocess.TimeoutExpired):
        result, status = dict(version=1, scope=SCOPE, status="refused", execution_authorized=False), 1
    print(json.dumps(result, sort_keys=True), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
