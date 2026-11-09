"""Inspect a frozen SDK19 plan using the operation's read-only preflight.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import os
from pathlib import Path
import re
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import record_large_text_ui_operation as operation


env = operation.env
REPORT = Path("D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-readiness-v1/readiness-v1.json")
SCOPE = "sdk19-record-large-text-readiness-v1"


def _require_unstarted():
    for path in (operation.AUTHORITY, operation.LIVE, operation.GUEST, operation.activation.RUNTIME):
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")


def inspect(plan_sha256):
    """Retain one advisory observation without touching operation authority or state."""
    env.require(type(plan_sha256) is str and re.fullmatch("[0-9a-f]{64}", plan_sha256),
                "binding")
    env.safe_path(REPORT.parent, directory=True)
    env.safe_path(REPORT, exists=False)
    env.require(not os.path.lexists(REPORT), "report_exists")
    start = time.monotonic()
    result = dict(version=1, scope=SCOPE, ready=False, execution_authorized=False,
                  admission_granted=False, feature_acceptance=False, plan=None, ledger=None,
                  observations=None, observed_unix_ns=time.time_ns(), reason=None)
    try:
        _require_unstarted()
        plan_pin, _ = operation._read(operation.PLAN, 131072)
        env.require(plan_pin["sha256"] == plan_sha256, "binding")
        result["plan"] = plan_pin
        plan, prepare = operation._plan(plan_pin)
        ledger = env.binding(operation.LEDGER)
        result["ledger"] = ledger
        facts = operation._preflight(ledger, plan, prepare)
        operation._check_sources(plan)
        for pin in (plan_pin, plan["prepare"], ledger):
            env.check_binding(pin)
        _require_unstarted()
        result.update(ready=True, reason="ok", observations=facts)
    except (Exception, KeyboardInterrupt) as error:
        result["reason"] = operation._reason(error)
    result["elapsed_ms"] = round((time.monotonic() - start) * 1000)
    env.create_json(REPORT, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-sha256", required=True)
    try:
        result = inspect(parser.parse_args(argv).plan_sha256)
    except (OSError, env.EnvironmentRefused, KeyboardInterrupt):
        print("SDK19 readiness report unavailable", file=sys.stderr)
        return 1
    print("SDK19 readiness: " + result["reason"])
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
