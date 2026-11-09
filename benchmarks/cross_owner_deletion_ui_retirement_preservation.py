"""Preserve SDK24 retirement evidence without changing its storage disposition.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import cross_owner_deletion_ui_failed_close as close
from benchmarks import cross_owner_deletion_ui_handoff as h
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage

OUT = h.OUT.parent / "2026-11-09-sdk24-retirement-preservation-v1"
RECORDS = OUT / "records"
STAGED = OUT / "staged-v1.json"
CREDENTIALS = OUT / "existing-credentials-v1.json"
MANIFEST = OUT / "manifest-v1.json"
STAGE_SCOPE = "sdk24-retirement-records-staged-v1"
CREDENTIAL_NAMES = frozenset(("emulator/adbkey", "emulator/adbkey.pub"))
MAX_COPY_BYTES = 16 * 1024**2
_need = env.require
_same = owned._same


def _ledger(ledger_pin):
    registry = storage.DEFAULT_REGISTRY
    _need(h.LEDGER == registry / "ledger-v1.json", "ledger")
    lock = storage.safe_path(registry / "admission.lock")
    _need(not os.path.lexists(lock), "registry_locked")
    ledger = storage.read_json(h.LEDGER, expected=ledger_pin)
    storage._validate(ledger, registry)
    _need(_same(ledger["version"], 2) and not os.path.lexists(lock), "ledger")
    storage.check_binding(ledger_pin)
    return ledger


def _outside(path, ledger):
    registry = storage.DEFAULT_REGISTRY
    roots = [Path(entry["root"]) for entry in ledger["entries"]]
    _need(not any(storage._contains(root, path) or storage._contains(path, root)
                  for root in (registry, *roots)), "output_overlap")


def _copy(source_pin, destination):
    source = storage.safe_path(source_pin["path"], exists=True)
    destination = storage.safe_path(destination)
    _need(source_pin["bytes"] <= MAX_COPY_BYTES and storage._contains(RECORDS, destination)
          and not os.path.lexists(destination), "copy")
    with source.open("rb") as stream:
        data = stream.read(source_pin["bytes"] + 1)
    _need(len(data) == source_pin["bytes"] and hashlib.sha256(data).hexdigest() == source_pin["sha256"],
          "copy")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with storage.safe_path(destination).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    copied = storage.binding(destination)
    _need(all(_same(copied[key], source_pin[key]) for key in ("bytes", "sha256")), "copy")
    storage.check_binding(source_pin)
    return copied


def _ordinary(files):
    return sorted(set(files) - storage.DISPOSABLE - CREDENTIAL_NAMES)


def _copies(staged, files, names):
    records = staged["records"]
    _need(type(records) is list and len(records) == len(names), "staged")
    copies = []
    for item, name in zip(records, names):
        owned._obj(item, ("relative", "original", "binding"), "staged")
        source, backup = item["original"], item["binding"]
        _need(item["relative"] == name and source["path"] == str(files[name])
              and backup["path"] == str(RECORDS / name)
              and all(_same(source[key], backup[key]) for key in ("bytes", "sha256")), "staged")
        storage.check_binding(source)
        storage.check_binding(backup)
        copies.append(dict(relative=name, binding=backup))
    return copies


def stage(plan_pin):
    """Copy ordinary records from the retained guest named by the exact close plan."""
    plan = close._read_plan(plan_pin)
    ledger_pin = plan["ledger"]
    ledger = _ledger(ledger_pin)
    output = storage.safe_path(OUT, exists=True, directory=True)
    _outside(output, ledger)
    for path in (RECORDS, STAGED, MANIFEST):
        storage.safe_path(path)
        _need(not os.path.lexists(path), "already_used")
    verified = close._fresh_review(plan["review"], ledger_pin)
    proposal = verified["evidence"]["run"]
    close.review._check_retained(storage._entry(ledger, h.GUEST), proposal)
    _need(plan["proposal_sha256"] == proposal["sha256"] and _same(close._inventory(), plan["guest_files"]),
          "plan")
    files = storage._files(h.GUEST)
    names = _ordinary(files)
    _need(CREDENTIAL_NAMES <= files.keys() and bool(names)
          and sum(files[name].stat().st_size for name in names) <= MAX_COPY_BYTES, "copy_budget")
    for pin in (plan_pin, plan["review"], *plan["sources"]):
        storage.check_binding(pin)
    original = {name: storage.binding(files[name]) for name in names}
    _need(sum(pin["bytes"] for pin in original.values()) <= MAX_COPY_BYTES, "copy_budget")
    RECORDS.mkdir(exist_ok=False)
    records = [dict(relative=name, original=original[name], binding=_copy(original[name], RECORDS / name))
               for name in names]
    staged = dict(version=1, scope=STAGE_SCOPE, plan=plan_pin, records=records,
                  deferred_credentials=sorted(CREDENTIAL_NAMES), manifest_complete=False,
                  execution_authorized=False)
    _copies(staged, files, names)
    _need(_same(close._inventory(), plan["guest_files"]), "guest_inventory")
    _ledger(ledger_pin)
    storage.check_binding(plan_pin)
    env.create_json(STAGED, staged)
    return storage.binding(STAGED)


def _existing_credentials(credentials_pin, files, ledger):
    value = h.at(credentials_pin, CREDENTIALS)
    owned._obj(value, ("version", "root", "files"), "credentials")
    items = value["files"]
    _need(_same(value["version"], 1) and value["root"] == str(h.GUEST)
          and type(items) is list and len(items) == len(CREDENTIAL_NAMES), "credentials")
    by_name = {}
    paths = set()
    for item in items:
        owned._obj(item, ("relative", "binding"), "credentials")
        name, pin = item["relative"], item["binding"]
        _need(type(name) is str and name in CREDENTIAL_NAMES and name not in by_name, "credentials")
        owned.binding(pin, max_bytes=16_384)
        destination = storage.safe_path(pin["path"], exists=True)
        _outside(destination, ledger)
        _need(str(destination).casefold() not in paths, "credentials")
        paths.add(str(destination).casefold())
        original = storage.binding(files[name])
        _need(all(_same(original[key], pin[key]) for key in ("bytes", "sha256")), "credentials")
        storage.check_binding(pin)
        by_name[name] = item
    return [by_name[name] for name in sorted(by_name)]


def complete(staged_pin, credentials_pin, ledger_pin):
    """Complete a manifest using verified copies of both already preserved credentials."""
    staged = h.at(staged_pin, STAGED)
    owned._obj(staged, ("version", "scope", "plan", "records", "deferred_credentials",
                        "manifest_complete", "execution_authorized"), "staged")
    _need(_same(staged["version"], 1) and staged["scope"] == STAGE_SCOPE
          and _same(staged["deferred_credentials"], sorted(CREDENTIAL_NAMES))
          and staged["manifest_complete"] is False and staged["execution_authorized"] is False, "staged")
    plan = close._read_plan(staged["plan"])
    ledger = _ledger(ledger_pin)
    _outside(storage.safe_path(OUT, exists=True, directory=True), ledger)
    entry = storage._entry(ledger, h.GUEST)
    closure_path = close._closure_path()
    _need(entry["state"] == "closed" and entry["retirement"] is None
          and entry["proposal_sha256"] == plan["proposal_sha256"]
          and entry["closure"]["path"] == str(closure_path), "guest_not_closed")
    closure_pin = entry["closure"]
    closure = h.at(closure_pin, closure_path)
    _need(closure.get("scope") == close.CLOSURE_SCOPE, "closure")
    retirement._closure(entry)
    after = h.at(closure["after"], close.AFTER)
    _need(_same(after["plan"], staged["plan"]), "closure")

    closure_name = closure_path.name
    destination = RECORDS / closure_name
    pending = MANIFEST.with_suffix(".pending.json")
    for path in (destination, pending, MANIFEST):
        storage.safe_path(path)
        _need(not os.path.lexists(path), "already_used")
    inventory = [item for item in close._inventory() if item["relative"] != closure_name]
    _need(_same(inventory, plan["guest_files"]), "guest_inventory")
    files = storage._files(h.GUEST)
    names = [name for name in _ordinary(files) if name != closure_name]
    copies = _copies(staged, files, names)
    copies.extend(_existing_credentials(credentials_pin, files, ledger))
    _need(sum(item["binding"]["bytes"] for item in copies if item["relative"] not in CREDENTIAL_NAMES)
          + closure_pin["bytes"] <= MAX_COPY_BYTES, "copy_budget")
    copies.append(dict(relative=closure_name, binding=_copy(closure_pin, destination)))
    manifest = dict(version=1, root=str(h.GUEST), complete=True,
                    files=sorted(copies, key=lambda item: item["relative"]))
    for pin in (staged_pin, credentials_pin, closure_pin, staged["plan"]):
        storage.check_binding(pin)
    _ledger(ledger_pin)
    env.create_json(pending, manifest)
    preserved = {name: path for name, path in storage._files(h.GUEST).items() if name not in storage.DISPOSABLE}
    verified = storage._evidence(h.GUEST, pending, preserved, closure_pin)
    _ledger(ledger_pin)
    pending.rename(MANIFEST)
    result = storage._evidence(h.GUEST, MANIFEST, preserved, closure_pin)
    _need(all(_same(result[key], verified[key]) for key in ("bytes", "sha256")), "manifest")
    _ledger(ledger_pin)
    return result


def _pin(path, sha):
    _need(type(sha) is str and re.fullmatch("[0-9a-f]{64}", sha) is not None, "digest")
    pin = storage.binding(path)
    _need(pin["sha256"] == sha, "digest")
    return pin


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-sha256")
    mode.add_argument("--staged-sha256")
    parser.add_argument("--credentials-sha256")
    parser.add_argument("--ledger-sha256")
    args = parser.parse_args(argv)
    try:
        if args.plan_sha256 is not None:
            _need(args.credentials_sha256 is None and args.ledger_sha256 is None, "arguments")
            result = dict(staged=stage(_pin(close.PLAN, args.plan_sha256)), manifest_complete=False)
        else:
            result = dict(manifest=complete(_pin(STAGED, args.staged_sha256),
                                            _pin(CREDENTIALS, args.credentials_sha256),
                                            _pin(h.LEDGER, args.ledger_sha256)), manifest_complete=True)
    except (OSError, RuntimeError, TypeError, ValueError, KeyError):
        print(json.dumps(dict(outcome="refused", execution_authorized=False)), flush=True)
        return 1
    print(json.dumps(dict(result, execution_authorized=False), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
