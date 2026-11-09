"""Record one separately approved storage closure for the failed SDK24 guest.

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

from benchmarks import cross_owner_deletion_ui_failed_closure as review
from benchmarks import cross_owner_deletion_ui_handoff as h
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

OUT = h.OUT.parent / "2026-11-09-sdk24-guarded-failed-close-v1"
REVIEW = h.OUT.parent / "2026-11-09-sdk24-failed-closure-review-v1" / "actual-review-6ba52b47.json"
PLAN = OUT / "closure-plan-v1.json"
AUTHORITY = OUT / "closure-authority-v1.json"
CLAIM = OUT / "closure-claim-v1.json"
BEFORE = OUT / "ledger-before-v1.json"
AFTER = OUT / "verified-teardown-v1.json"
PLAN_SCOPE = "sdk24-failed-registration-closure-plan-v1"
AUTHORITY_SCOPE = "sdk24-failed-registration-closure-authority-v1"
CLOSURE_SCOPE = storage.FAILED_SDK24_CLOSURE_SCOPE
AFTER_SCOPE = "sdk24-failed-registration-verified-teardown-v1"
PLAN_KEYS = ("version", "scope", "root", "ledger", "review", "proposal_sha256", "sources",
             "guest_files", "guest_bytes", "retained_bytes")
_need = env.require
_same = owned._same


def _closure_path():
    return h.GUEST / "guest-storage-closure-v1.json"


def _sources():
    pins = owned.source_bindings()
    pins.extend(storage.binding(Path(module.__file__).resolve())
                for module in (sys.modules[__name__], review, review.native))
    return sorted(pins, key=lambda pin: pin["path"])


def _report_identities(report):
    owned._obj(report, ("version", "scope", "disposition", "existing_retirement_eligible",
                        "execution_authorized", "evidence", "processes"), "review")
    rows = report["processes"]
    _need(_same(report["version"], 1) and report["scope"] == review.SCOPE
          and report["disposition"] == "guarded_closure_review_required"
          and report["existing_retirement_eligible"] is False and report["execution_authorized"] is False
          and type(report["evidence"]) is dict and 1 <= len(report["evidence"]) <= 128
          and type(rows) is list and len(rows) == 7, "review")
    identities = []
    for row in rows:
        owned._obj(row, ("identity", "status"), "review")
        _need(row["status"] in ("pid_absent", "pid_reused", "exited"), "review")
        owned._process(row["identity"])
        identities.append(row["identity"])
    _need(len({identity["pid"] for identity in identities}) == 7, "review")
    return identities


def _fresh_review(review_pin, ledger_pin, *, locked_entry=None):
    prior = h.at(review_pin, REVIEW)
    identities = _report_identities(prior)
    evidence = prior["evidence"]
    _need(_same(evidence["ledger"], ledger_pin), "ledger")
    current = review._inspect(evidence["operation"], evidence["observed"], ledger_pin,
                              locked_entry=locked_entry)
    _need(_same(current["evidence"], evidence) and _same(_report_identities(current), identities), "review")
    return current


def _inventory():
    files = storage._files(h.GUEST)
    return [{"relative": name, "bytes": files[name].stat().st_size} for name in sorted(files)]


def _plan(review_pin, verified, ledger_pin):
    evidence = verified["evidence"]
    _need(_same(evidence["ledger"], ledger_pin), "ledger")
    files = _inventory()
    return dict(version=1, scope=PLAN_SCOPE, root=str(h.GUEST), ledger=ledger_pin, review=review_pin,
                proposal_sha256=evidence["run"]["sha256"], sources=_sources(), guest_files=files,
                guest_bytes=sum(item["bytes"] for item in files), retained_bytes=storage.RESERVATION_BYTES)


def _unused():
    for path in (CLAIM, BEFORE, AFTER, _closure_path()):
        storage.safe_path(path)
        _need(not os.path.lexists(path), "already_used")


def build_plan(review_pin):
    """Build a file-only plan for the exact already retained guest."""
    _unused()
    ledger_pin = storage.binding(h.LEDGER)
    verified = _fresh_review(review_pin, ledger_pin)
    plan = _plan(review_pin, verified, ledger_pin)
    for pin in (review_pin, ledger_pin, *plan["sources"]):
        storage.check_binding(pin)
    _unused()
    return plan


def _read_authority(authority_pin):
    value = h.at(authority_pin, AUTHORITY, 16_384)
    owned._obj(value, ("version", "scope", "plan", "approval_reference", "allow_close",
                       "allow_retirement", "allow_boot"), "authority")
    reference = value["approval_reference"]
    _need(_same(value["version"], 1) and value["scope"] == AUTHORITY_SCOPE
          and value["allow_close"] is True and value["allow_retirement"] is False and value["allow_boot"] is False
          and type(reference) is str and 0 < len(reference) <= 256 and reference.strip() == reference
          and all(32 <= ord(char) <= 126 for char in reference), "authority")
    return value


def _read_plan(plan_pin):
    plan = h.at(plan_pin, PLAN)
    owned._obj(plan, PLAN_KEYS, "plan")
    _need(_same(plan["version"], 1) and plan["scope"] == PLAN_SCOPE and plan["root"] == str(h.GUEST)
          and _same(plan["retained_bytes"], storage.RESERVATION_BYTES), "plan")
    owned.binding(plan["ledger"], max_bytes=h.STORAGE_CAP)
    _need(plan["ledger"]["path"] == str(h.LEDGER), "ledger")
    return plan


def _claim(plan_pin, authority_pin):
    return dict(version=1, scope=AUTHORITY_SCOPE, plan=plan_pin, authority=authority_pin, no_retry=True)


def _copy_ledger(ledger_pin):
    path = storage.safe_path(h.LEDGER, exists=True)
    with path.open("rb") as stream:
        data = stream.read(ledger_pin["bytes"] + 1)
    _need(len(data) == ledger_pin["bytes"] and hashlib.sha256(data).hexdigest() == ledger_pin["sha256"], "ledger")
    with storage.safe_path(BEFORE).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return storage.binding(BEFORE)


def _closure_value(evidence, after_pin):
    return dict(version=1, scope=CLOSURE_SCOPE, proposal_sha256=evidence["run"]["sha256"],
                closure_verified=True, cleanup_complete=True, admission=evidence["admission"],
                owner_result=evidence["inner_terminal"], worker_result=evidence["worker"], after=after_pin)


def retirement_identities(entry, closure):
    """Validate the separate post-failure proof without inventing a normal owner result."""
    after_pin = closure["after"]
    after = h.at(after_pin, AFTER)
    owned._obj(after, ("version", "scope", "plan", "authority", "claim", "before", "review"), "closure")
    _need(_same(after["version"], 1) and after["scope"] == AFTER_SCOPE, "closure")
    plan_pin = after["plan"]
    plan = _read_plan(plan_pin)
    authority = _read_authority(after["authority"])
    _need(_same(authority["plan"], plan_pin)
          and _same(h.at(after["claim"], CLAIM), _claim(plan_pin, after["authority"])), "authority")
    before = after["before"]
    ledger_before = h.at(before, BEFORE, h.STORAGE_CAP)
    _need(all(_same(before[key], plan["ledger"][key]) for key in ("bytes", "sha256"))
          and _same(ledger_before["version"], 2), "ledger")
    report = after["review"]
    identities = _report_identities(report)
    expected = h.at(plan["review"], REVIEW)
    evidence = report["evidence"]
    _need(_same(evidence, expected["evidence"]) and _same(identities, _report_identities(expected))
          and _same(evidence["ledger"], plan["ledger"]), "review")
    review._check_retained(storage._entry(ledger_before, h.GUEST), evidence["run"])
    _need(entry["root"] == str(h.GUEST) and entry["proposal_sha256"] == plan["proposal_sha256"]
          and _same(closure, _closure_value(evidence, after_pin))
          and closure["proposal_sha256"] == entry["proposal_sha256"], "closure")
    for pin in (after_pin, plan_pin, after["authority"], after["claim"], before, plan["review"],
                *plan["sources"], *(pin for role, pin in evidence.items() if role != "ledger")):
        storage.check_binding(pin)
    return identities


def execute(authority_pin):
    """Spend one exact closure-only approval and account for the verified closed guest."""
    authority = _read_authority(authority_pin)
    plan_pin = authority["plan"]
    plan = _read_plan(plan_pin)
    ledger_pin = plan["ledger"]
    registry = storage.DEFAULT_REGISTRY
    _need(h.LEDGER == registry / "ledger-v1.json", "ledger")
    _unused()
    with storage._locked(registry, expected_ledger=ledger_pin) as ledger:
        _need(_same(ledger["version"], 2), "ledger")
        lock_pin = storage.binding(registry / "admission.lock")
        entry = storage._entry(ledger, h.GUEST)
        verified = _fresh_review(plan["review"], ledger_pin, locked_entry=entry)
        evidence = verified["evidence"]
        review._check_retained(entry, evidence["run"])
        _need(_same(plan, _plan(plan["review"], verified, ledger_pin)), "plan")
        for pin in (authority_pin, plan_pin, ledger_pin, plan["review"], *plan["sources"], *evidence.values()):
            storage.check_binding(pin)
        _unused()
        env.create_json(CLAIM, _claim(plan_pin, authority_pin))
        claim_pin = storage.binding(CLAIM)
        before = _copy_ledger(ledger_pin)
        env.create_json(AFTER, dict(version=1, scope=AFTER_SCOPE, plan=plan_pin, authority=authority_pin,
                                   claim=claim_pin, before=before, review=verified))
        after_pin = storage.binding(AFTER)
        closure = _closure_value(evidence, after_pin)
        retirement_identities(entry, closure)
        _need(_same(_inventory(), plan["guest_files"]), "guest_inventory")
        storage.check_binding(ledger_pin)
        storage.check_binding(lock_pin)
        closure_path = _closure_path()
        env.create_json(closure_path, closure)
        storage._record_closed_locked(h.GUEST, closure_path, registry, ledger,
                                      failed_sdk24=True, expected_ledger=ledger_pin)
        current = storage.binding(h.LEDGER)
        updated = storage._entry(storage.read_json(h.LEDGER, expected=current), h.GUEST)
        _need(updated["state"] == "closed" and _same(updated["closure"], storage.binding(closure_path))
              and updated["retirement"] is None, "closure")
        return dict(closure=updated["closure"], ledger=current, reserved_bytes=updated["reserved_bytes"],
                    android_methods_executed=0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--review-sha256")
    mode.add_argument("--authority-sha256")
    args = parser.parse_args(argv)
    try:
        planning = args.review_sha256 is not None
        sha = args.review_sha256 if planning else args.authority_sha256
        _need(re.fullmatch("[0-9a-f]{64}", sha) is not None, "digest")
        pin = storage.binding(REVIEW if planning else AUTHORITY)
        _need(pin["sha256"] == sha, "digest")
        if planning:
            env.create_json(PLAN, build_plan(pin))
            print(json.dumps(dict(plan=storage.binding(PLAN), execution_authorized=False)), flush=True)
        else:
            print(json.dumps(execute(pin), sort_keys=True), flush=True)
        return 0
    except (OSError, RuntimeError, TypeError, ValueError, KeyError):
        print(json.dumps(dict(scope=AUTHORITY_SCOPE, outcome="refused")), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
