"""Observe SDK22 synthetic picker readiness without creating an attempt.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import model_picker_action_preparation as preparation
from benchmarks import model_picker_action_handoff as handoff
from benchmarks import owned_model_picker_action as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

SCOPE = "sdk22-model-picker-action-readiness-v1"
COMMIT_FIELDS = ("version", "commit_total_bytes", "commit_limit_bytes", "available_commit_bytes",
                 "guest_memory_bytes", "required_commit_bytes", "reserve_bytes")
STORAGE_FIELDS = ("max_guests", "budget_bytes", "reservation_bytes", "active_count",
                  "charged_bytes", "projected_bytes")
STORAGE_FLAGS = dict(root_limit_exceeded=False, byte_limit_exceeded=False, would_fit=True,
                     admission_granted=False)
REFUSALS = frozenset((
    "already_used", "auth", "binding", "binding_changed", "binding_set_changed", "console_token_changed",
    "facts", "host_capacity",
    "host_commit_capacity", "host_commit_unavailable", "host_cpu_capacity", "installed", "invalid_ledger",
    "invalid_proposal", "ledger", "ledger_missing", "linked_or_special_file", "linked_path", "memory_unavailable",
    "missing_path", "old_registry_changed", "plan", "ports_unavailable",
    "preview_changed", "profile", "registry_locked", "root_already_tracked", "source", "storage_capacity",
    "target_exists", "unsafe_path", "windows_required",
))


def _result(status):
    return dict(version=1, scope=SCOPE, status=status, readiness_only=True, execution_authorized=False)


def _pending():
    env.require(not any(os.path.lexists(path) for path in (handoff.AUTHORITY, handoff.ATTEMPT_ROOT, handoff.GUEST)),
                "already_used")


def _numbers(row, keys):
    env.require(type(row) is dict and all(type(row.get(key)) is int and row[key] >= 0 for key in keys), "facts")
    return {key: row[key] for key in keys}


def inspect(plan_pin, ledger_pin):
    """Check the fixed plan and ledger, then return bounded advisory facts."""
    _pending()
    plan = handoff.at(plan_pin, handoff.PLAN, cap=131072)
    handoff._pin_at(ledger_pin, handoff.LEDGER, handoff.STORAGE_CAP)
    prepare = handoff.prepare_plan(plan)
    facts = preparation.preflight_pending(ledger_pin, plan, prepare)
    env.check_binding(plan["prepare"])
    env.check_binding(plan_pin)
    env.check_binding(ledger_pin)
    _pending()

    env.require(type(facts) is dict and all(type(facts.get(key)) is dict for key in ("resources", "storage")), "facts")
    resources = facts["resources"]
    preview = facts["storage"]
    env.require(contract._same(preview.get("ledger"), ledger_pin)
                and preview.get("root") == str(handoff.GUEST), "binding")
    env.require(facts["ports_free"] is True and all(preview.get(key) is value
                                                    for key, value in STORAGE_FLAGS.items()), "facts")
    host = dict(_numbers(resources, ("available_memory", "logical_cpus")),
                free_bytes=_numbers(resources["free_bytes"], ("C:", "D:")),
                commit_capacity=_numbers(resources["commit_capacity"], COMMIT_FIELDS))
    capacity = dict(_numbers(preview, STORAGE_FIELDS), **STORAGE_FLAGS)
    return dict(_result("ready"), plan=plan_pin, ledger=ledger_pin, host=host, storage=capacity, ports_free=True)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        env.require(type(args) is list and len(args) == 4 and args[0] == "--plan-sha256"
                    and args[2] == "--ledger-sha256"
                    and all(type(args[i]) is str and re.fullmatch("[0-9a-f]{64}", args[i]) is not None
                            for i in (1, 3)), "binding")
        plan_pin, _ = handoff.read(handoff.PLAN, 131072)
        ledger_pin, _ = handoff.read(handoff.LEDGER, handoff.STORAGE_CAP)
        env.require(plan_pin["sha256"] == args[1] and ledger_pin["sha256"] == args[3], "binding")
        result = inspect(plan_pin, ledger_pin)
        status = 0
    except (OSError, RuntimeError, ValueError, TypeError, KeyError) as error:
        reason = str(error) if isinstance(error, (env.EnvironmentRefused, storage.StorageRefused,
                                                  contract.TargetRefused)) else None
        result = dict(_result("refused"), reason=reason if reason in REFUSALS else "readiness_refused")
        status = 1
    print(json.dumps(result, sort_keys=True), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
