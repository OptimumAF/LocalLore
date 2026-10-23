"""Strict, bounded AndroidJUnitRunner result parsing; never operates a device.

Only expected case identifiers and fixed aggregate evidence leave this module.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import re

MAX_BYTES = 262_144
CASE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*#[A-Za-z_$][A-Za-z0-9_$]*")
STATUS_KEYS = {"class", "test", "current", "numtests", "id", "stream", "stack"}
RESULT_KEYS = {"stream", "shortMsg", "longMsg", "stack"}
WATCHDOG = ("ReferenceQueueDaemon", "TimeoutException", "HardwareRenderer$DestroyContextRunnable")


def analyse_instrumentation(data: bytes, expected: tuple[str, ...],
                            required_first: str | None = None,
                            required_last: str | None = None) -> dict:
    """Parse full or interrupted cohorts without returning logs or unknown names.

    A started case is paired with exactly one terminal result, with matching
    identity/current/count. Malformed later input cannot erase valid earlier
    pairs. A success summary cannot replace missing or failed case records.
    """
    report = {"status": "invalid", "passed": 0, "failed": 0, "skipped": 0,
              "completed": [], "started_unfinished": 0,
              "graphics_watchdog_signature": False, "order_verified": False,
              "final_success": False}
    if (type(data) is not bytes or len(data) > MAX_BYTES or type(expected) is not tuple
            or not 1 <= len(expected) <= 256
            or any(type(case) is not str or CASE.fullmatch(case) is None for case in expected)
            or len(set(expected)) != len(expected)
            or (required_first is not None and (type(required_first) is not str or required_first not in expected))
            or (required_last is not None and (type(required_last) is not str or required_last not in expected))):
        return report
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeError:
        return report
    if "\x00" in text:
        return report

    fields, result, active, seen = {}, {}, None, set()
    order = []
    continuation = None
    final_code = None
    final_started = False
    invalid = False
    aborted = False

    def watchdog(stack):
        if all(fragment in stack for fragment in WATCHDOG):
            report["graphics_watchdog_signature"] = True

    def status_record(number):
        nonlocal active, invalid
        required = {"class", "test", "current", "numtests", "id"}
        if (not required <= fields.keys() or not fields.keys() <= STATUS_KEYS
                or fields["id"] != "AndroidJUnitRunner"
                or fields["numtests"] != str(len(expected))):
            invalid = True
            return
        case = fields["class"] + "#" + fields["test"]
        current = str(len(order) + 1)
        if case not in expected or fields["current"] != current:
            invalid = True
            return
        if number == "1":
            if active is not None or case in seen or "stack" in fields:
                invalid = True
                return
            active = case
            report["started_unfinished"] = 1
            return
        if number not in ("0", "-1", "-2", "-3", "-4") or active != case:
            invalid = True
            return
        if number == "0" and "stack" in fields:
            invalid = True
            return
        outcome = "passed" if number == "0" else ("skipped" if number in ("-3", "-4") else "failed")
        watchdog(fields.get("stack", ""))
        report[outcome] += 1
        report["completed"].append({"case": case, "outcome": outcome})
        seen.add(case)
        order.append(case)
        active = None
        report["started_unfinished"] = 0

    for line in text.splitlines():
        if not line:
            continue  # Windows ADB can double every CRLF between bundle fields.
        if line.startswith("INSTRUMENTATION_STATUS: "):
            if final_started or final_code is not None:
                invalid = True
                break
            key, separator, value = line[24:].partition("=")
            if not separator or key not in STATUS_KEYS or key in fields:
                invalid = True
                break
            fields[key] = value
            continuation = (fields, key)
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            if final_started or final_code is not None:
                invalid = True
                break
            status_record(line[29:])
            if invalid:
                break
            fields = {}
            continuation = None
        elif line.startswith("INSTRUMENTATION_RESULT: "):
            if fields or final_code is not None:
                invalid = True
                break
            final_started = True
            key, separator, value = line[24:].partition("=")
            if not separator or key not in RESULT_KEYS or key in result:
                invalid = True
                break
            result[key] = value
            continuation = (result, key)
        elif line.startswith("INSTRUMENTATION_CODE: "):
            if fields or final_code is not None or line[22:] not in ("-1", "0", "1"):
                invalid = True
                break
            final_started = True
            final_code = line[22:]
            continuation = None
        elif line.startswith("INSTRUMENTATION_FAILED: "):
            # Explicit infrastructure abort. Its message is neither copied nor interpreted.
            if fields or final_code is not None:
                invalid = True
                break
            final_started = True
            aborted = True
            continuation = None
        elif line.startswith("INSTRUMENTATION_"):
            invalid = True
            break
        elif continuation is not None and continuation[1] in ("stream", "stack", "longMsg"):
            values, key = continuation
            values[key] += "\n" + line
        else:
            invalid = True
            break

    if fields:
        # A truncated bundle is incomplete, not a validated test result. Its
        # stack cannot classify a watchdog until its matching record completes.
        if final_started:
            invalid = True
    if result.get("stack"):
        watchdog(result["stack"])
    complete = len(order) == len(expected) and seen == set(expected) and active is None
    order_ok = (complete and (required_first is None or order[0] == required_first)
                and (required_last is None or order[-1] == required_last))
    report["order_verified"] = order_ok and not invalid
    noun = "test" if len(expected) == 1 else "tests"
    summary = re.fullmatch(r"\s*Time: (?:0|[1-9][0-9]*)(?:\.[0-9]+)?\s+OK \("
                           + str(len(expected)) + " " + noun + r"\)\s*", result.get("stream", ""))
    aborted = aborted or "shortMsg" in result or "longMsg" in result or "stack" in result or final_code in ("0", "1")
    report["final_success"] = bool(final_code == "-1" and summary and set(result) == {"stream"}
                                   and complete and not fields and not report["failed"]
                                   and not report["skipped"] and not invalid and not aborted)
    if invalid:
        report["status"] = "invalid"
    elif aborted:
        report["status"] = "aborted"
    elif report["failed"] or report["skipped"]:
        report["status"] = "failed"
    elif complete and order_ok and report["final_success"]:
        report["status"] = "passed"
    elif complete and not order_ok:
        report["status"] = "failed"
    else:
        report["status"] = "incomplete"
    return report
