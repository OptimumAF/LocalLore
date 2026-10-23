"""Opt-in fixed-cohort Android investigation; never installs or clears app data.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys

from android_app_restart_smoke import APP, TEST_APP, RUNNER, ProbeFailure, Transport, apk_digest
from android_instrumentation_result import analyse_instrumentation

FRAMEWORK_CLASS = "org.locallore.app.FrameworkInterruptionTest"
CANCEL_CLASS = "org.locallore.app.ShellInstrumentedTest"
CANCEL_METHOD = "cancelAndResetDuringDelayCannotPublishOldResult"
CANCEL = CANCEL_CLASS + "#" + CANCEL_METHOD
FRAMEWORK = tuple(FRAMEWORK_CLASS + "#" + method for method in (
    "realFrameworkDestructionFencesLateReplyAndRetainedCallbacksWithoutDeletingSavedCanon",
    "realFrameworkStopCancelsUndeliveredReadyTurnAndLateReplyCannotAttachToNewStory",
    "realFrameworkRecreationCancelsRunningTurnAndRetainsOnlyTheCurrentAcceptedReceipt"))
COHORTS = {
    "cancel_only": (CANCEL, (CANCEL,), CANCEL, CANCEL),
    "framework_then_cancel": (FRAMEWORK_CLASS + "," + CANCEL, FRAMEWORK + (CANCEL,), None, CANCEL),
    "cancel_then_framework": (CANCEL + "," + FRAMEWORK_CLASS, (CANCEL,) + FRAMEWORK, CANCEL, None),
}


def instrument(transport, selection):
    """Keep partial protocol evidence on timeout/crash without trusting ADB exit zero."""
    if not transport.clients_cleaned:
        raise ProbeFailure("checkpoint")
    try:
        result = transport.process([transport.adb, "-s", transport.serial, "shell", "am", "instrument",
                                    "-w", "-r", "-e", "class", selection, RUNNER],
                                   deadline=180, max_output=131_072)
    except Exception:
        transport.clients_cleaned = False
        raise ProbeFailure("checkpoint") from None
    transport.clients_cleaned = transport.clients_cleaned and result.cleanup_complete is True
    status = result.status if result.status in {
        "completed", "timeout", "cancelled", "output_limit", "spawn_failed", "cleanup_failed"} else "invalid"
    code = result.returncode if type(result.returncode) is int else None
    output = result.stdout if isinstance(result.stdout, bytes) and len(result.stdout) <= 131_072 else b""
    meta = {"status": status, "returncode": code, "client_cleanup": transport.clients_cleaned}
    return output, meta


class Journal:
    """Exclusive append-only JSONL. Durable start records precede any device operation."""
    def __init__(self, path):
        self.stream = Path(path).open("x", encoding="utf-8", newline="\n")

    def append(self, record):
        self.stream.write(json.dumps(record, sort_keys=True) + "\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


def execute(transport, apk, test_apk, repetitions, cohorts, emit):
    """Fixed metadata only; no report field comes directly from command output."""
    if (type(repetitions) is not int or repetitions not in (1, 2) or
            not isinstance(cohorts, tuple) or not cohorts or len(cohorts) > 3 or
            any(type(name) is not str or name not in COHORTS for name in cohorts) or
            len(set(cohorts)) != len(cohorts)):
        raise ValueError("invalid_plan")
    planned = repetitions * len(cohorts)
    summary = {"event": "complete", "status": "failed", "attempts_planned": planned,
               "attempts_started": 0, "attempts_finished": 0, "cohorts_passed": 0,
               "case_passes": 0, "unexecuted": planned, "graphics_signature_attempts": 0,
               "app_process_absent": False, "adb_clients_cleaned": True,
               "cause_fixed": False, "failure_stage": "none"}
    try:
        expected = (apk_digest(apk), apk_digest(test_apk))
    except (OSError, ValueError):
        emit({"event": "plan", "version": 1, "status": "local_apk_unavailable",
              "cohorts": list(cohorts), "repetitions": repetitions})
        summary["failure_stage"] = "local_apk"
        emit(summary)
        return summary
    emit({"event": "plan", "version": 1, "scope": "fixed_synthetic_android_cohorts",
          "apk_sha256": expected[0], "test_apk_sha256": expected[1],
          "cohorts": list(cohorts), "repetitions": repetitions, "attempts_planned": planned,
          "cases_planned": repetitions * sum(len(COHORTS[name][1]) for name in cohorts)})

    def identities():
        if apk_digest(apk) != expected[0] or apk_digest(test_apk) != expected[1]:
            raise ProbeFailure("local_apk")
        transport.identity(APP, expected[0], "app_identity")
        transport.identity(TEST_APP, expected[1], "test_identity")

    def stop():
        if apk_digest(apk) != expected[0]:
            raise ProbeFailure("local_apk")
        transport.stop(expected[0], ("stop_identity", "stop_command", "stop_absence"))

    stop_plan = False
    for repetition in range(1, repetitions + 1):
        for name in cohorts:
            index = summary["attempts_started"] + 1
            emit({"event": "attempt_started", "index": index, "repetition": repetition, "cohort": name})
            summary["attempts_started"] = index
            selection, cases, first, last = COHORTS[name]
            row = {"event": "attempt_finished", "index": index, "repetition": repetition,
                   "cohort": name, "passed": False, "failure_stage": "none",
                   "transport_error_stage": "none", "app_absent_before": False,
                   "app_absent_after": False, "adb_clients_cleaned": transport.clients_cleaned,
                   "execution": None, "result": None}
            stage = "identity_before"
            try:
                identities()
                stage = "stop_before"
                stop()
                row["app_absent_before"] = True
                stage = "identity_for_instrumentation"
                identities()
                stage = "instrumentation"
                output, execution = instrument(transport, selection)
                row["execution"] = execution
                stage = "protocol"
                result = analyse_instrumentation(output, cases, required_first=first, required_last=last)
                row["result"] = result
                if execution["status"] in {"cancelled", "invalid"}:
                    stop_plan = True
                transport_ok = (execution["status"] == "completed" and execution["returncode"] == 0
                                and execution["returncode"] is not None and execution["client_cleanup"])
                stage = "identity_after"
                if transport.clients_cleaned:
                    identities()
                row["passed"] = transport_ok and result["status"] == "passed"
                if not row["passed"]:
                    row["failure_stage"] = "instrumentation_result" if transport_ok else "instrumentation_transport"
            except ProbeFailure as failure:
                row["failure_stage"] = stage
                row["transport_error_stage"] = failure.stage
                if stage.startswith("identity"):
                    stop_plan = True
            except KeyboardInterrupt:
                row["failure_stage"] = "interrupted"
                stop_plan = True
            except OSError:
                row["failure_stage"] = "local_apk"
                stop_plan = True
            except Exception:
                row["failure_stage"] = "internal"
                stop_plan = True
            finally:
                # A matching app may still be stopped after test-identity failure. An
                # unowned ADB client or changed app identity prevents any absence claim.
                if transport.clients_cleaned:
                    try:
                        stop()
                        row["app_absent_after"] = True
                    except (ProbeFailure, OSError, ValueError):
                        row["passed"] = False
                        if row["failure_stage"] == "none":
                            row["failure_stage"] = "stop_after"
                        stop_plan = True
                else:
                    row["passed"] = False
                    stop_plan = True
                row["adb_clients_cleaned"] = transport.clients_cleaned
                if not row["app_absent_after"]:
                    row["passed"] = False
                # If this write fails, the durable start still marks an unknown outcome;
                # stop was attempted first and no next attempt is dispatched.
                emit(row)
            summary["attempts_finished"] += 1
            summary["cohorts_passed"] += int(row["passed"])
            if row["result"] is not None:
                summary["case_passes"] += row["result"]["passed"]
                summary["graphics_signature_attempts"] += int(row["result"]["graphics_watchdog_signature"])
            summary["app_process_absent"] = row["app_absent_after"]
            summary["adb_clients_cleaned"] = row["adb_clients_cleaned"]
            if row["failure_stage"] != "none" and summary["failure_stage"] == "none":
                summary["failure_stage"] = row["failure_stage"]
            if stop_plan:
                break
        if stop_plan:
            break
    summary["unexecuted"] = planned - summary["attempts_started"]
    if summary["cohorts_passed"] == planned and summary["app_process_absent"] and summary["adb_clients_cleaned"]:
        summary["status"] = "passed"
    emit(summary)
    return summary


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # Command-line mistakes must not echo supplied private values to report output.
        raise ValueError("arguments")


def main(argv=None):
    parser = _Parser(description=__doc__)
    for name in ("adb", "apk", "test-apk", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--cohort", action="append")
    try:
        args = parser.parse_args(argv)
        cohorts = tuple(args.cohort) if args.cohort else tuple(COHORTS)
        if (not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", args.serial) or
                args.repetitions not in (1, 2) or len(set(cohorts)) != len(cohorts) or
                not cohorts or len(cohorts) > 3 or any(name not in COHORTS for name in cohorts)):
            raise ValueError("arguments")
    except (ValueError, argparse.ArgumentError):
        print('{"status":"failed","failure_stage":"arguments"}')
        return 2
    try:
        journal = Journal(args.output)
    except OSError:
        print('{"status":"failed","failure_stage":"journal_open"}')
        return 2
    try:
        try:
            summary = execute(Transport(args.adb, args.serial), args.apk, args.test_apk,
                              args.repetitions, cohorts, journal.append)
        finally:
            journal.close()
    except (OSError, ValueError):
        print('{"status":"failed","failure_stage":"journal_or_local_io"}')
        return 2
    print(json.dumps(summary))
    return 0 if summary["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
