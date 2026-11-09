"""Verify SDK26 preparation and stage a non-authorizing owner candidate.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path, PureWindowsPath
import uuid

from benchmarks import archive_provider_platform_binding as artifacts
from benchmarks import archive_provider_platform_preparation as prep
from benchmarks import isolated_adb_lease as server
from benchmarks import owned_archive_provider_platform as owned
from benchmarks import receipt_avd_environment as env

OUT = prep.GUEST.parent / "activation-v1"
RUN = OUT / "run-proposal-v1.json"
ADMISSION = OUT / "admission-v1.json"
PROPOSAL = OUT / "PROPOSED_OPERATION.md"
CANDIDATE = OUT / "candidate-v1.json"
RUN_AUTHORITY = OUT / "run-authorization-v1.json"
HANDOFF = OUT / "boot-handoff-v1.json"
OWNED_ROOT = OUT / "owned-v1"
COMPLETION = OUT / "activation-completion-v1.json"
SCOPE = "sdk26-archive-provider-activation-candidate-v1"
OWNER_SECONDS = 1700
_SERVER_INPUTS = ("adb", "tools", "capabilities", "source_review", "auth_key")
_GUEST_INPUTS = ("emulator", "qemu", "refuser", "refuser_source")
_REFUSER = {
    "path": str(PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-10-29-owned-target-v1/refuser-build-v1/deny-adb-client.exe")),
    "bytes": 95_744,
    "sha256": "6d48de140b83bf86b9edc9a4a95b2f2a5fdacdbe10066cb4469e3702d7833c7f",
}
_COMPATIBILITY = {
    "path": str(PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-10-29-owned-target-v1/target-compat-final-review-v1.md")),
    "bytes": 5_335,
    "sha256": "34ec87a31bf8bb1187244feaf81b3ca9d757f7a393411143c1ae294fc4020024",
}


def _unused(*, staging=False):
    paths = (RUN_AUTHORITY, HANDOFF, OWNED_ROOT, COMPLETION, prep.GUEST / owned.BOOT_CLAIM_FILE)
    if staging:
        paths += (OUT,)
    for path in paths:
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")


def _recheck_preparation(plan_pin, preparation_pin, plan, proof, current):
    proposal = prep._read_authority(proof["authority"])["proposal"]
    for pin in (preparation_pin, plan_pin, plan["prepare"], proof["authority"], proposal,
                proof["claim"], proof["authorization"], proof["prepared"], proof["result"],
                current, *proof["evidence"].values()):
        env.check_binding(pin)


def verify_preparation(plan_pin, preparation_pin):
    """Read the exact preparation proof and observe the current prepared charge."""
    proof = env.decode_json(prep._bound(preparation_pin, prep.RESULT))
    owned._obj(proof, ("version", "scope", "authority", "claim", "plan", "authorization",
                       "ledger", "prepared", "result", "evidence", "activation_authorized"), "prepared")
    env.require(owned._same(proof["version"], 1) and proof["scope"] == prep.PREPARE_SCOPE
                and owned._same(proof["plan"], plan_pin) and proof["activation_authorized"] is False, "prepared")
    authority = prep._read_authority(proof["authority"])
    claim = env.decode_json(prep._bound(proof["claim"], prep.CLAIM, 16_384))
    env.require(owned._same(authority["plan"], plan_pin)
                and owned._same(claim, prep._claim(proof["authority"])), "authority")
    plan, proposal = prep.load_plan(plan_pin)
    authorization = env.decode_json(prep._bound(proof["authorization"], prep.PREPARE_AUTH, 4096))
    env.check_authorization(authorization, "prepare", plan["prepare"]["sha256"], prepare_scope=prep.PREPARE_SCOPE)
    prepared, result, evidence = prep._prepared_records(plan, proposal)
    env.require(owned._same(proof["prepared"], prepared) and owned._same(proof["result"], result)
                and owned._same(proof["evidence"], evidence), "prepared")
    # The receipt retains the original ledger observation. An unrelated ledger
    # change requires a new activation candidate, not a replacement receipt.
    owned.binding(proof["ledger"], max_bytes=16 * 1024**2)
    env.require(proof["ledger"]["path"] == str(prep.LEDGER), "ledger")
    current = prep._prepared_ledger(plan["prepare"])
    _recheck_preparation(plan_pin, preparation_pin, plan, proof, current)
    return plan, proposal, proof, current


def _run(plan, prepare, proof):
    run = dict(prepare, phase="run", prepare_proposal=plan["prepare"], prepared=proof["prepared"],
               prepare_result=proof["result"], max_seconds=env.REAL_MAX_SECONDS)
    env.validate_proposal(run, "run")
    return run


def _pin_for_bytes(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def _authorization(run_pin):
    return dict(version=1, phase="run", run_scope=owned.PROTOCOL,
                proposal_sha256=run_pin["sha256"], allow_environment_calls=True, root_go_pending=False)


def _admission(plan, run_pin, installed, run_id):
    owned._obj(installed, (*_SERVER_INPUTS, *_GUEST_INPUTS, "compatibility"), "tool")
    sources = [pin for pin in plan["sources"]
               if PureWindowsPath(pin["path"]).name in server.SOURCE_NAMES | {"__init__.py"}]
    lease = dict(version=1, protocol=server.PROTOCOL, run_id=run_id, root=str(OWNED_ROOT / "server"),
                 port=owned.PORT, seconds=OWNER_SECONDS, sdk_version=server.SDK_VERSION,
                 expected_version="0029", sources=sources, python=plan["python"],
                 **{key: installed[key] for key in _SERVER_INPUTS})
    auth = env.encoded(_authorization(run_pin))
    guest = dict(root=str(prep.GUEST), proposal=run_pin, authorization=_pin_for_bytes(RUN_AUTHORITY, auth),
                 console_port=5592, adb_port=5593, serial="emulator-5592", memory_mib=8192, cores=4,
                 max_seconds=env.REAL_MAX_SECONDS, api=35, abi="x86_64",
                 **{key: installed[key] for key in _GUEST_INPUTS})
    return owned.validate_admission(dict(
        version=1, protocol=owned.PROTOCOL, run_id=run_id, root=str(OWNED_ROOT),
        seconds=OWNER_SECONDS, server=lease, guest=guest, artifacts=plan["artifacts"],
        sources=plan["sources"], python=plan["python"], compatibility=installed["compatibility"],
    ))


def _check_inputs(admission, run):
    lease, guest = admission["server"], admission["guest"]
    sdk = Path(run["sdk"])
    env.require(lease["adb"]["path"] == run["adb_path"]
                and guest["emulator"]["path"] == str(sdk / "emulator/emulator.exe")
                and guest["qemu"]["path"] == str(sdk / "emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe"),
                "tool")
    pinned = {row["path"]: row for row in run["bindings"]}
    env.require(all(owned._same(pinned.get(pin["path"]), pin)
                    for pin in lease["tools"] + [guest["emulator"], guest["qemu"]]), "tool")
    refuser_source = env.binding(prep.ROOT / "benchmarks/native/deny_adb_client.c")
    env.require(owned._same(guest["refuser"], _REFUSER) and owned._same(guest["refuser_source"], refuser_source)
                and owned._same(admission["compatibility"], _COMPATIBILITY), "tool")
    key = Path(env.token_path()).parent / ".android/adbkey"
    env.require(lease["auth_key"] == str(key), "auth")
    key_info = env.safe_path(key).stat()
    env.require(key_info.st_size > 0 and key_info.st_nlink == 1, "auth")
    env.verify_installation(run)
    env.check_external_state(run)
    server.revalidate_inputs(lease)
    for pin in (_REFUSER, refuser_source, _COMPATIBILITY):
        env.check_binding(pin)


def _review_bytes(admission_pin, ledger_pin):
    pins = artifacts.artifact_bindings()
    tests = "".join(f"- `{klass}#{method}`\n" for _, klass, method in owned.INSTRUMENTATIONS)
    return (f"# Activate the prepared LocalLore SDK26 test guest once\n\n"
            f"Admission SHA-256 {admission_pin['sha256']}\nLedger SHA-256 {ledger_pin['sha256']}\n\n"
            f"Boot the prepared API 35 x86_64 guest at {prep.GUEST} with 8 GiB RAM and four cores. "
            "Reuse its existing 40 GiB reservation. The guest ceiling is 30 minutes. "
            "Allow up to 256 MiB for local records and recovery.\n\n"
            "Run these two model-free methods in order under the 20-minute controller budget.\n\n"
            f"{tests}\nProduct APK SHA-256 {pins['product_apk']['sha256']}\n"
            f"Test APK SHA-256 {pins['test_apk']['sha256']}\n\n"
            f"Only the owned emulator on ports 5592 and 5593 and its private ADB service on port {owned.PORT} "
            "may start and stop. "
            "Fresh storage, host, port and ownership checks are required. "
            "The scope is activation and testing of the prepared guest.\n").encode("utf-8")


def create_candidate(plan_pin, preparation_pin, installed):
    """Write review inputs without creating authorization or an owned process."""
    _unused(staging=True)
    plan, prepare, proof, ledger = verify_preparation(plan_pin, preparation_pin)
    run = _run(plan, prepare, proof)
    run_pin = _pin_for_bytes(RUN, env.encoded(run))
    admission = _admission(plan, run_pin, installed, uuid.uuid4().hex)
    _check_inputs(admission, run)
    env.verify_prepared(run, initial=True)
    _recheck_preparation(plan_pin, preparation_pin, plan, proof, ledger)
    _unused(staging=True)
    OUT.mkdir(exist_ok=False)
    env.require(owned._same(prep._save(RUN, run), run_pin), "publication")
    admission_pin = prep._save(ADMISSION, admission)
    markdown = _review_bytes(admission_pin, ledger)
    proposal = _pin_for_bytes(PROPOSAL, markdown)
    with env.safe_path(PROPOSAL, exists=False).open("xb") as output:
        output.write(markdown)
        output.flush()
        os.fsync(output.fileno())
    for pin in (plan_pin, preparation_pin, ledger, run_pin, admission_pin, proposal):
        env.check_binding(pin)
    _unused()
    return prep._save(CANDIDATE, dict(
        version=1, scope=SCOPE, plan=plan_pin, preparation=preparation_pin, ledger=ledger,
        admission=admission_pin, proposal=proposal, execution_authorized=False,
    ))


def _read_candidate(candidate_pin, ledger_pin):
    candidate = env.decode_json(prep._bound(candidate_pin, CANDIDATE))
    owned._obj(candidate, ("version", "scope", "plan", "preparation", "ledger", "admission",
                           "proposal", "execution_authorized"), "candidate")
    env.require(owned._same(candidate["version"], 1) and candidate["scope"] == SCOPE
                and candidate["execution_authorized"] is False
                and owned._same(candidate["ledger"], ledger_pin), "candidate")
    return candidate


def _verify_candidate(candidate_pin, ledger_pin):
    candidate = _read_candidate(candidate_pin, ledger_pin)
    plan, prepare, proof, current = verify_preparation(candidate["plan"], candidate["preparation"])
    env.require(owned._same(current, ledger_pin), "ledger")
    admission = owned.validate_admission(env.decode_json(prep._bound(candidate["admission"], ADMISSION)))
    run_pin = admission["guest"]["proposal"]
    run = env.decode_json(prep._bound(run_pin, RUN))
    installed = {key: admission["server"][key] for key in _SERVER_INPUTS}
    installed.update({key: admission["guest"][key] for key in _GUEST_INPUTS},
                     compatibility=admission["compatibility"])
    env.require(owned._same(run, _run(plan, prepare, proof))
                and owned._same(admission, _admission(plan, run_pin, installed, admission["run_id"])), "admission")
    env.require(prep._bound(candidate["proposal"], PROPOSAL, 65_536)
                == _review_bytes(candidate["admission"], ledger_pin), "proposal")
    _check_inputs(admission, run)
    env.verify_prepared(run, initial=True)
    _recheck_preparation(candidate["plan"], candidate["preparation"], plan, proof, current)
    for pin in (candidate_pin, candidate["admission"], candidate["proposal"], run_pin):
        env.check_binding(pin)
    return admission


def verify_candidate(candidate_pin, ledger_pin):
    """Recheck the complete candidate before considering a separate activation grant."""
    _unused()
    admission = _verify_candidate(candidate_pin, ledger_pin)
    _unused()
    return admission
