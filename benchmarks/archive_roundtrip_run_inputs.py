"""Stage the fixed SDK25 run inputs and publish them only with exact boot authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys

from benchmarks import adb_held_socket_probe as python_tools
from benchmarks import archive_roundtrip_admission as gate
from benchmarks import archive_roundtrip_prepare as preparation
from benchmarks import archive_roundtrip_supervisor as supervisor
from benchmarks import isolated_adb_lease as server

env = gate.env
contract = gate.contract
bridge = gate.lifecycle.bridge
output_control = gate.output_control

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "sdk25-archive-roundtrip-run-inputs-v1"
INSTALLATION = gate.CONTROL / "run-installation-v1.json"
PREPARED_KEYS = ("prepare_proposal", "prepared", "prepare_result")
INSTALLATION_ROLES = {"refuser": ".exe", "capabilities": ".json", "source_review": ".md", "compatibility": ".md"}
# Exact compiled helper and source from OWNED_TARGET_VERIFICATION_2026-10-29.
REFUSER_SHA256 = "6d48de140b83bf86b9edc9a4a95b2f2a5fdacdbe10066cb4469e3702d7833c7f"
REFUSER_SOURCE_SHA256 = "145b9d8b2860ce77e41889202e3a95a74bd8e21a26f9598b7c4439091e85fdba"
PLAN_KEYS = ("version", "scope", "receipt", "installation", "proposal", "ledger", "authorization",
             "admission", "execution_authorized")

_need = gate._need
_same = contract._same
_read = gate.lifecycle._read
_at = gate.lifecycle._at


def _pin(path, value):
    return bridge._pin_bytes(path, env.encoded(value))


def _plan_path(digest):
    _need(type(digest) is str and re.fullmatch("[0-9a-f]{64}", digest) is not None, "plan")
    return gate.CONTROL / f"run-inputs-v1-{digest}.json"


def _verify_json(pin, cap=gate.lifecycle.RECORD_CAP):
    _at(pin, Path(pin["path"]), cap)


def _save_exact(pin, value):
    path = Path(pin["path"])
    _need(_same(pin, _pin(path, value)), "publication")
    if not os.path.lexists(path):
        path = output_control.validate_output(str(path))
        pending = path.with_name(path.name + ".pending")
        pending_pin = _pin(pending, value)
        if os.path.lexists(pending):
            _verify_json(pending_pin)
        else:
            pending = output_control.validate_output(str(pending))
            _need(_same(supervisor._save(pending, value), pending_pin), "publication")
        # Windows rename refuses a competing destination.
        pending.rename(path)
    _verify_json(pin)
    return pin


def _unspent():
    for path in (gate.ATTEMPT, gate.OWNED_ROOT, preparation.GUEST / contract.BOOT_CLAIM_FILE):
        env.safe_path(path, exists=False)
        _need(not os.path.lexists(path), "already_used")


def _installed(pin):
    value = _at(pin, INSTALLATION, gate.AUTHORITY_CAP)
    contract._obj(value, ("version", *INSTALLATION_ROLES), "installed")
    _need(_same(value["version"], 1), "installed")
    for role, suffix in INSTALLATION_ROLES.items():
        contract.binding(value[role], max_bytes=64 * 1024 * 1024)
        path = PureWindowsPath(value[role]["path"])
        _need(path.suffix.lower() == suffix and ".android" not in {part.casefold() for part in path.parts},
              "installed")
    refuser = value["refuser"]
    _need(PureWindowsPath(refuser["path"]).name == "deny-adb-client.exe"
          and refuser["bytes"] == 95_744 and refuser["sha256"] == REFUSER_SHA256, "installed")
    return value


def _prepared(receipt_pin, ledger_pin):
    receipt = _at(receipt_pin, preparation.RESULT)
    approval = preparation._authority(receipt["authority"])
    pins = dict(prepare_proposal=approval["prepare"], prepared=receipt["prepared"],
                prepare_result=receipt["prepare_result"])
    expected_paths = (gate.PREPARE_PROPOSAL, preparation.GUEST / "prepared-v1.json",
                      preparation.GUEST / "prepare-result-v1.json")
    for key, path in zip(PREPARED_KEYS, expected_paths, strict=True):
        contract.binding(pins[key])
        _need(pins[key]["path"] == str(path), "prepared")
    preparation.verify_receipt(receipt_pin, pins, approval["artifacts"])
    gate._prepared_entry(ledger_pin, {"guest": {"root": str(preparation.GUEST)}}, pins)
    for pin in pins.values():
        _verify_json(pin)
    return pins, approval["artifacts"]


def _proposal(run_pin, pins):
    value = _at(run_pin, gate.RUN_PROPOSAL)
    env.validate_proposal(value, "run")
    _need(value["paths"]["root"] == str(preparation.GUEST)
          and _same((value["memory_mib"], value["cores"], value["max_seconds"]), (8192, 4, gate.GUEST_SECONDS))
          and all(_same(value[key], pins[key]) for key in PREPARED_KEYS), "proposal")
    return value


def _prospective(receipt_pin, installed_pin, run_pin, proposal, artifacts):
    installed = _installed(installed_pin)
    run_id = hashlib.sha256(env.encoded([receipt_pin, installed_pin, run_pin])).hexdigest()[:32]
    tools_root = Path(proposal["sdk"]) / "platform-tools"
    emulator = Path(proposal["sdk"]) / "emulator"
    bindings = {item["path"]: item for item in proposal["bindings"]}
    tools = [bindings[str(tools_root / name)] for name in sorted(server.TOOL_NAMES)]
    adb = bindings[str(tools_root / "adb.exe")]
    _need(adb["path"] == proposal["adb_path"], "installed")

    sources = contract.source_bindings()
    python = python_tools._python_bindings()
    refuser_source = env.binding(ROOT / "benchmarks/native/deny_adb_client.c")
    _need(refuser_source["bytes"] == 189 and refuser_source["sha256"] == REFUSER_SOURCE_SHA256, "installed")
    authorization = dict(version=1, phase="run", run_scope=contract.RUN_SCOPE, proposal_sha256=run_pin["sha256"],
                         allow_environment_calls=True, root_go_pending=False)
    guest = dict(root=str(preparation.GUEST), proposal=run_pin,
                 authorization=_pin(gate.RUN_AUTHORIZATION, authorization),
                 emulator=bindings[str(emulator / "emulator.exe")],
                 qemu=bindings[str(emulator / "qemu/windows-x86_64/qemu-system-x86_64-headless.exe")],
                 refuser=installed["refuser"], refuser_source=refuser_source,
                 console_port=5592, adb_port=5593, serial="emulator-5592", memory_mib=8192, cores=4,
                 max_seconds=gate.GUEST_SECONDS, api=35, abi="x86_64")
    lease = dict(version=1, protocol=server.PROTOCOL, run_id=run_id, root=str(gate.OWNED_ROOT / "server"),
                 port=contract.PORT, seconds=gate.OWNER_SECONDS, adb=adb, tools=tools,
                 sdk_version=server.SDK_VERSION, expected_version="0029",
                 sources=[pin for pin in sources
                          if PureWindowsPath(pin["path"]).name in server.SOURCE_NAMES | {"__init__.py"}],
                 python=python, auth_key=str(Path(env.token_path()).parent / ".android/adbkey"),
                 capabilities=installed["capabilities"], source_review=installed["source_review"])
    admitted = contract.validate_admission(dict(version=1, protocol=contract.PROTOCOL, run_id=run_id,
        root=str(gate.OWNED_ROOT), seconds=gate.OWNER_SECONDS, server=lease, guest=guest, artifacts=artifacts,
        sources=sources, python=python, compatibility=installed["compatibility"]))
    gate.build.verify_current(admitted)
    server.revalidate_inputs(admitted["server"])
    for pin in (guest["emulator"], guest["qemu"], guest["refuser"], guest["refuser_source"],
                installed["compatibility"]):
        env.check_binding(pin)
    return authorization, admitted


def _review(receipt_pin, installed_pin, run_pin, ledger_pin, admitted):
    return dict(version=1, scope=SCOPE, receipt=receipt_pin, installation=installed_pin, proposal=run_pin,
                ledger=ledger_pin, authorization=admitted["guest"]["authorization"],
                admission=_pin(gate.ADMISSION, admitted), execution_authorized=False)


def _check_existing(plan):
    for pin in (plan["authorization"], plan["admission"]):
        if os.path.lexists(pin["path"]):
            _verify_json(pin)


def _recheck(plan):
    for key in ("receipt", "installation", "proposal"):
        _verify_json(plan[key])
    _verify_json(plan["ledger"], gate.lifecycle.LEDGER_CAP)
    gate._check_ledger_unlocked()
    _unspent()


def stage(receipt_pin, installed_pin):
    """Write the shared proposal and a review packet, without any runnable grant."""
    _need(os.name == "nt", "platform")
    output_control._prepare_environment()
    _unspent()
    _installed(installed_pin)
    gate._check_ledger_unlocked()
    ledger_pin, _ = _read(preparation.LEDGER, gate.lifecycle.LEDGER_CAP)
    pins, artifacts = _prepared(receipt_pin, ledger_pin)
    created = None
    if not os.path.lexists(gate.RUN_PROPOSAL):
        path = output_control.validate_output(str(gate.RUN_PROPOSAL))
        created = env.plan_run(pins["prepare_proposal"]["path"], pins["prepared"]["path"], path,
                               max_seconds=gate.GUEST_SECONDS)
    run_pin, _ = _read(gate.RUN_PROPOSAL)
    proposal = _proposal(run_pin, pins)
    if created is None:
        env.verify_prepared(proposal, initial=True)
    else:
        _need(_same(created, proposal), "proposal")
    _, admitted = _prospective(receipt_pin, installed_pin, run_pin, proposal, artifacts)
    plan = _review(receipt_pin, installed_pin, run_pin, ledger_pin, admitted)
    _check_existing(plan)
    _recheck(plan)
    digest = hashlib.sha256(env.encoded(plan)).hexdigest()
    return _save_exact(_pin(_plan_path(digest), plan), plan)


def materialize(plan_pin, authority_pin):
    """Publish only the two approved inputs. The existing supervisor owns execution."""
    _need(os.name == "nt", "platform")
    output_control._prepare_environment()
    _unspent()
    plan = _at(plan_pin, _plan_path(plan_pin["sha256"]), gate.AUTHORITY_CAP)
    contract._obj(plan, PLAN_KEYS, "plan")
    _need(_same(plan["version"], 1) and plan["scope"] == SCOPE and plan["execution_authorized"] is False, "plan")
    authority = gate._authority(authority_pin)
    _need(_same(authority["admission"], plan["admission"]) and _same(authority["ledger"], plan["ledger"])
          and _same(authority["prepare_receipt"], plan["receipt"]), "authority")
    pins, artifacts = _prepared(plan["receipt"], plan["ledger"])
    proposal = _proposal(plan["proposal"], pins)
    env.verify_prepared(proposal, initial=True)
    authorization, admitted = _prospective(plan["receipt"], plan["installation"], plan["proposal"],
                                           proposal, artifacts)
    _need(_same(plan, _review(plan["receipt"], plan["installation"], plan["proposal"], plan["ledger"], admitted)),
          "plan")
    _check_existing(plan)
    _recheck(plan)
    for pin in (plan_pin, authority_pin):
        _verify_json(pin, gate.AUTHORITY_CAP)
    _save_exact(plan["authorization"], authorization)
    _recheck(plan)
    _verify_json(authority_pin, gate.AUTHORITY_CAP)
    result = _save_exact(plan["admission"], admitted)
    _recheck(plan)
    for pin in (authority_pin, plan["authorization"], result):
        _verify_json(pin)
    return result


def _by_digest(path, expected, cap=gate.AUTHORITY_CAP):
    pin, _ = _read(path, cap)
    _need(pin["sha256"] == expected, "binding")
    return pin


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    review = sub.add_parser("stage")
    review.add_argument("--receipt-sha256", required=True)
    review.add_argument("--installation-sha256", required=True)
    publish = sub.add_parser("materialize")
    publish.add_argument("--plan-sha256", required=True)
    publish.add_argument("--authority-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        _need(os.name == "nt" and all(re.fullmatch("[0-9a-f]{64}", value) is not None
              for key, value in vars(args).items() if key.endswith("_sha256")), "binding")
        if args.action == "stage":
            result = stage(_by_digest(preparation.RESULT, args.receipt_sha256),
                           _by_digest(INSTALLATION, args.installation_sha256))
        else:
            result = materialize(_by_digest(_plan_path(args.plan_sha256), args.plan_sha256),
                                 _by_digest(gate.AUTHORITY, args.authority_sha256))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError):
        print("SDK25 run inputs refused", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
