"""Explicit current Rust/SDK Android experiment; no downloads or model provisioning.

Only bounded synthetic aggregate evidence leaves the isolated SDK application.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import time
import uuid

import android_runtime_spike as spike

CASES = {"gift", "dialogue", "unlearned", "spent", "cancel"}
OUTCOMES = {"committed", "rejected", "cancelled", "failed"}
ERRORS = spike.host.DOMAIN_ERRORS | spike.host.WORKER_ERRORS | {
    "cancel_not_observed", "Busy", "Full", "Database", "Integrity", "Io", "Internal", "UnknownTurn",
    "InvalidHandle", "InvalidTicket", "Profile", "WorkspaceLimit", "Session", "Closed", "Unsupported"}
GENERATION_KEYS = {"role", "status", "error", "load_ms", "generation_ms", "input_tokens", "output_tokens",
                   "schema_enforced", "thinking_disabled", "template_applied"}
COUNTS = {"roles": 3, "director_calls": 2, "narrator_calls": 1, "revision_before": 100,
          "revision_after": 100, "receipts_before": 100, "receipts_after": 100, "repairs": 1}
BOOLS = {"exact_retry", "reopen_equal", "canon_unchanged", "model_initialized", "fallback",
         "first_output_observed", "owner_drained"}
TURN_KEYS = set(COUNTS) | BOOLS | {"outcome", "error", "generations"}
RESULT_KEYS = set(COUNTS) | BOOLS | {"version", "case", "outcome", "error", "gift_seeded", "workspace_retained", "turns"}
PROFILE_PATH = Path(__file__).resolve().parents[1] / "docs/runtime/android/PLAY_PROFILE_V1.json"
MARKER = "locallore-android-play-probe-v1"


def number(value, cap, integral=False, nullable=False):
    return (nullable and value is None) or (type(value) is int if integral else type(value) in (int, float)) and \
        0 <= value <= cap and math.isfinite(value)


def fixed_error(value):
    return value is None or type(value) is str and value in ERRORS


def valid_generation(value):
    if type(value) is not dict or set(value) != GENERATION_KEYS:
        return False
    if value["role"] not in ("director", "narrator") or value["status"] not in ("completed", "error", "cancelled"):
        return False
    if not fixed_error(value["error"]) or any(type(value[k]) is not bool for k in
            ("schema_enforced", "thinking_disabled", "template_applied")):
        return False
    if any(not number(value[k], 180000, nullable=True) for k in ("load_ms", "generation_ms")):
        return False
    if not number(value["input_tokens"], 4096, integral=True, nullable=True) or not number(
            value["output_tokens"], 350 if value["role"] == "director" else 220, integral=True, nullable=True):
        return False
    if value["status"] == "completed":
        return value["error"] is None and all(value[k] for k in ("schema_enforced", "thinking_disabled", "template_applied")) and \
            all(value[k] is not None for k in ("load_ms", "generation_ms", "input_tokens", "output_tokens")) and \
            value["input_tokens"] > 0 and value["output_tokens"] > 0 and value["input_tokens"] + value["output_tokens"] <= 4096
    return value["error"] is not None


def valid_turn(value):
    if type(value) is not dict or set(value) != TURN_KEYS or value["outcome"] not in OUTCOMES or not fixed_error(value["error"]):
        return False
    if any(not number(value[k], cap, integral=True) for k, cap in COUNTS.items()) or any(type(value[k]) is not bool for k in BOOLS):
        return False
    generations = value["generations"]
    if type(generations) is not list or len(generations) != value["roles"] or not all(valid_generation(g) for g in generations):
        return False
    if any(value[k] != sum(g["role"] == role for g in generations) for k, role in
            (("director_calls", "director"), ("narrator_calls", "narrator"))):
        return False
    changed = value["revision_after"] != value["revision_before"] or value["receipts_after"] != value["receipts_before"]
    if value["canon_unchanged"] == changed:
        return False
    if value["outcome"] == "committed":
        return value["error"] is None and changed and value["owner_drained"] and value["model_initialized"] and \
            value["exact_retry"] and value["reopen_equal"] and value["director_calls"] >= 1 and value["narrator_calls"] == 1 and \
            value["revision_after"] > value["revision_before"] and value["receipts_after"] == value["receipts_before"] + 1 and \
            all(g["status"] == "completed" for g in generations) and \
            [g["role"] for g in generations] == ["director"] * value["director_calls"] + ["narrator"] and \
            value["repairs"] == value["director_calls"] - 1
    if value["outcome"] == "cancelled":
        return not changed and value["error"] == "Cancelled" and value["first_output_observed"] and bool(generations) and \
            generations[-1]["status"] == "cancelled" and generations[-1]["error"] == "Cancelled"
    return value["error"] is not None and not changed


def validate_play_result(value, metrics, case):
    """Shared strict receipt proof; transport-specific ownership metrics are checked by the caller."""
    try:
        if case not in CASES:
            return None
        if type(value) is not dict or set(value) != RESULT_KEYS or type(value["version"]) is not int or value["version"] != 1 or value["case"] != case:
            return None
        turns = value["turns"]
        if type(turns) is not list or not 1 <= len(turns) <= (2 if case == "spent" else 1) or not all(valid_turn(t) for t in turns):
            return None
        if value["outcome"] != turns[-1]["outcome"] or value["error"] != turns[-1]["error"]:
            return None
        if any(type(value[k]) is not bool for k in BOOLS | {"gift_seeded", "workspace_retained"}) or not value["workspace_retained"]:
            return None
        for key in ("roles", "director_calls", "narrator_calls", "repairs"):
            if not number(value[key], COUNTS[key] * len(turns), integral=True) or value[key] != sum(t[key] for t in turns):
                return None
        for key in ("revision_before", "receipts_before"):
            if type(value[key]) is not int or value[key] != turns[0][key]:
                return None
        for key in ("revision_after", "receipts_after"):
            if type(value[key]) is not int or value[key] != turns[-1][key]:
                return None
        if any(turns[i]["revision_before"] != turns[i-1]["revision_after"] or turns[i]["receipts_before"] != turns[i-1]["receipts_after"]
               for i in range(1, len(turns))):
            return None
        if value["gift_seeded"] != (case == "spent" and turns[0]["outcome"] == "committed"):
            return None
        if value["owner_drained"] != all(t["owner_drained"] for t in turns):
            return None
        if any(value[k] != any(t[k] for t in turns) for k in ("model_initialized", "fallback", "first_output_observed")):
            return None
        changed = value["revision_before"] != value["revision_after"] or value["receipts_before"] != value["receipts_after"]
        if value["canon_unchanged"] == changed:
            return None
        for key in ("exact_retry", "reopen_equal"):
            if value[key] != all(t[key] for t in turns):
                return None
        initialized = sum(t["model_initialized"] for t in turns)
        generations = [g for t in turns for g in t["generations"]]
        conversations = metrics["conversations_opened"]
        if metrics["engines_opened"] != initialized or not sum(g["status"] in ("completed", "cancelled") for g in generations) <= conversations <= len(generations):
            return None
        if any(t["model_initialized"] is False and any(g["status"] in ("completed", "cancelled") for g in t["generations"]) for t in turns):
            return None
        # Other aggregate booleans are interpreted only alongside each strict per-turn proof.
        return value, metrics
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
        return None


def parse_result(raw, case):
    try:
        if type(raw) is not bytes or len(raw) > 131072 or case not in CASES:
            return None
        codes = re.findall(rb"^INSTRUMENTATION_CODE: (-?\d+)\r?$", raw, re.M)
        rows = re.findall(rb"^INSTRUMENTATION_RESULT: play_result=(.*)\r?$", raw, re.M)
        if codes != [b"-1"] or len(rows) != 1 or b"INSTRUMENTATION_FAILED" in raw:
            return None
        terminal = spike.sdk_response(raw)
        if terminal is None:
            return None
        worker = spike.host.parse_worker(terminal[0])
        if worker["text"] or worker["status"] != "completed" or terminal[1].get("cleanup_requires_process_termination") is True:
            return None
        metrics = re.findall(rb"^INSTRUMENTATION_RESULT: metrics=(.*)\r?$", raw, re.M)
        original_metrics = spike.strict_json(metrics[0])
        if original_metrics.get("mode") != "play" or type(original_metrics.get("version")) is not int or original_metrics["version"] != 1:
            return None
        value = spike.strict_json(rows[0])
        return validate_play_result(value, terminal[1], case)
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
        return None


def make_profile(apk_sha):
    if type(apk_sha) is not str or not re.fullmatch("[0-9a-f]{64}", apk_sha):
        raise ValueError("Invalid artifact identity")
    raw = PROFILE_PATH.read_bytes()
    manifest = spike.strict_json(raw)
    value = {k: manifest[k] for k in ("id", "model_sha256", "runtime_revision", "context_tokens", "director_tokens",
                                     "narrator_tokens", "deadline_ms", "repair_limit")}
    value.update(template_sha256=value["model_sha256"], worker_sha256=apk_sha,
                 profile_manifest_sha256=hashlib.sha256(raw).hexdigest())
    return value


class TrackedDevice(spike.Device):
    def __init__(self, adb, serial):
        super().__init__(adb, serial)
        self.clients_cleaned = True

    def raw(self, *args, **kwargs):
        if not self.clients_cleaned:
            raise spike.Failure("unconfirmed_client_cleanup")
        result = super().raw(*args, **kwargs)
        self.clients_cleaned &= result.cleanup_complete is True
        return result


def cleanup_workspace(device, token):
    if not re.fullmatch("[0-9a-f]{32}", token):
        raise ValueError("Invalid session token")
    directory = "no_backup/play-probe-" + token
    names = ("owner-v1", "stories.sqlite3", "stories.sqlite3-wal", "stories.sqlite3-shm", "stories.sqlite3-journal")
    q = shlex.quote(directory)
    script = (f"[ -d {q} ] && [ ! -L {q} ] && [ \"$(cat {q}/owner-v1)\" = {MARKER} ] || exit 1; "
              f"for f in {q}/* {q}/.[!.]* {q}/..?*; do [ ! -e \"$f\" ] && [ ! -L \"$f\" ] && continue; "
              "[ -f \"$f\" ] && [ ! -L \"$f\" ] || exit 1; case \"${f##*/}\" in " + "|".join(names) + ") ;; *) exit 1;; esac; done; "
              "rm -f -- " + " ".join(q + "/" + n for n in names) + "; rmdir -- " + q + "; [ ! -e " + q + " ] && [ ! -L " + q + " ]")
    device.shell("run-as", spike.PACKAGE, "/system/bin/sh", "-c", script)


def run_probe(device, apk_sha, case, allow_missing=False, raw_sink=None):
    if case not in CASES:
        raise ValueError("Invalid case")
    token = uuid.uuid4().hex
    report = {"version": 1, "scope": "android_current_rust_play_probe", "case": case, "status": "setup_failed",
              "result": None, "sdk": None, "process_absent": False, "clients_cleaned": False,
              "workspace_removed": False, "check_passed": False, "phone_qualified": False}
    report["model_verified"] = False
    report["raw_protocol_retained"] = False
    sdk = spike.SdkWorker(device, apk_sha)
    started = time.monotonic()
    launched = False
    stage = "package_identity"
    try:
        sdk.verify_package()
        stage = "initial_stop"
        if not sdk.stop():
            raise spike.Failure("cleanup_failed")
        stage = "model_identity"
        model = "files/gemma4-e2b.litertlm"
        observed = device.shell("run-as", spike.PACKAGE, "/system/bin/sh", "-c",
            f"if [ -f {model} ] && [ ! -L {model} ]; then sha256sum {model}; elif [ ! -e {model} ] && [ ! -L {model} ]; then printf absent; else exit 1; fi", deadline=180).strip()
        missing = observed == b"absent"
        if missing and not allow_missing:
            report["status"] = "model_missing"
            return report
        if not missing and (not observed or observed.split()[0].decode("ascii") != spike.host.ARTIFACTS["litert"][2]):
            raise spike.Failure("model_identity_failed")
        report["model_verified"] = not missing
        profile = base64.b64encode(json.dumps(make_profile(apk_sha), separators=(",", ":")).encode("utf-8")).decode("ascii")
        stage = "instrumentation"
        remote = shlex.join(["am", "instrument", "-w", "-r", "-e", "mode", "play", "-e", "session", token,
            "-e", "play_case", case, "-e", "profile_base64", profile, spike.PACKAGE + "/.SpikeInstrumentation"])
        launched = True
        execution = device.raw(["shell", remote], deadline=110)
        if raw_sink is not None and len(execution.stdout) <= 131072:
            raw_sink(execution.stdout)
            report["raw_protocol_retained"] = True
        if execution.status != "completed" or execution.returncode != 0 or not execution.cleanup_complete:
            report["status"] = "invalid_terminal"
            return report
        decoded = parse_result(execution.stdout, case)
        if decoded is None:
            report["status"] = "invalid_terminal"
            return report
        result, metrics = decoded
        report.update(status="observed", result=result, sdk=metrics)
        expected = {"gift": "committed", "dialogue": "committed", "unlearned": "rejected", "spent": "rejected", "cancel": "cancelled"}[case]
        last = result["turns"][-1]
        report["check_passed"] = last["outcome"] == expected and last["owner_drained"] and last["reopen_equal"]
        if expected == "committed":
            report["check_passed"] &= report["model_verified"]
        if case == "spent":
            report["check_passed"] &= result["gift_seeded"] and len(result["turns"]) == 2
        if case in ("spent", "unlearned"):
            report["check_passed"] &= last["error"] == {"spent": "Inventory", "unlearned": "Ability"}[case] and last["canon_unchanged"]
        if case == "cancel":
            report["check_passed"] &= last["first_output_observed"] and metrics.get("cancel_called") is True and metrics.get("cancel_terminal_callback") is True
        if allow_missing and missing:
            report["check_passed"] = last["outcome"] == "failed" and last["error"] == "model_missing" and last["owner_drained"] and last["canon_unchanged"] and \
                not last["model_initialized"] and metrics["engines_opened"] == 0 and metrics["conversations_opened"] == 0
    except (spike.Failure, OSError, ValueError, KeyError, UnicodeError):
        report.update(status="setup_failed", failure_stage=stage)
    finally:
        if device.clients_cleaned:
            try:
                report["process_absent"] = sdk.stop()
                if launched and report["process_absent"] and report["result"] is not None and report["result"]["owner_drained"]:
                    cleanup_workspace(device, token)
                    report["workspace_removed"] = True
            except (spike.Failure, OSError, ValueError):
                report["status"] = "cleanup_failed"
        report["clients_cleaned"] = device.clients_cleaned
        if not report["process_absent"] or not report["clients_cleaned"] or launched and not report["workspace_removed"]:
            report["check_passed"] = False
        report["wall_ms"] = round((time.monotonic() - started) * 1000)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--case", choices=sorted(CASES), default="gift")
    parser.add_argument("--allow-missing-model-probe", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    identity = spike.sha256(args.apk)
    # Record admission before any device mutation; crashes retain a started/unfinished attempt.
    # Never overwrite a previous attempt, even if it has no terminal record.
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps({"event": "started", "version": 1, "case": args.case, "apk_sha256": identity}) + "\n")
        output.flush(); os.fsync(output.fileno())
        def retain_raw(raw):
            private = spike.ROOT / "target/android-play-probe/raw"
            private.mkdir(parents=True, exist_ok=True)
            name = hashlib.sha256(str(args.output.resolve()).encode("utf-8")).hexdigest() + ".txt"
            with (private / name).open("xb") as protocol:
                protocol.write(raw)
        report = run_probe(TrackedDevice(args.adb, args.serial), identity, args.case, args.allow_missing_model_probe, retain_raw)
        report.update(event="finished", apk_sha256=identity)
        if spike.sha256(args.apk) != identity:
            report.update(status="artifact_changed", check_passed=False)
        output.write(json.dumps(report, allow_nan=False) + "\n")
        output.flush(); os.fsync(output.fileno())
    print(json.dumps(report, allow_nan=False))
    return 0 if report["check_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
