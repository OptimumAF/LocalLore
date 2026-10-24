"""One explicitly admitted frozen cacheprobe SDK experiment; never provisions or removes files.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import base64
import copy
import json
import re
import shlex
import time
import uuid

import android_cache_result as cache_result
import android_cache_volume as admission
import android_play_probe as play
import android_runtime_spike as spike

PACKAGE = "org.locallore.runtimebench.litert.cacheprobe"
INSTRUMENTATION = "org.locallore.runtimebench.litert.CacheProbeInstrumentation"
APK_SHA256 = "04eef96b7177aaef275574f9ee45d25efa9b181bab4fcb0a363d8077a4e4fb7d"
MODEL_SHA256 = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
MODEL_BYTES = 2_588_147_712
MODEL_KEYS = {"verified", "volume_uuid", "sha256", "bytes", "diagnostic"}
MODEL_DIAGNOSTICS = {"verified", "absent", "mismatch", "unstable", "incomplete", "not_regular",
                     "wrong_volume", "invalid_receipt", "read_failed"}


class _Failure(Exception):
    """Only local fixed categories; original callback/device exceptions never enter reports."""


class TrackedDevice(spike.Device):
    """Dedicated sticky client fence; inherits only generic explicitly targeted transport."""
    def __init__(self, adb, serial):
        super().__init__(adb, serial)
        self.clients_cleaned = True

    def raw(self, *args, **kwargs):
        if not self.clients_cleaned:
            raise spike.Failure("unconfirmed_client_cleanup")
        result = super().raw(*args, **kwargs)
        self.clients_cleaned &= result.cleanup_complete is True
        return result


class _Client:
    def __init__(self, device):
        self.device = device
        self.clean = getattr(device, "clients_cleaned", None) is True
        self.stage = "none"

    def known(self):
        self.clean &= getattr(self.device, "clients_cleaned", None) is True
        return self.clean

    def raw(self, arguments, deadline=20, retain_unclean=False):
        if not self.known():
            raise _Failure("client_cleanup_unknown")
        try:
            result = self.device.raw(arguments, deadline=deadline)
        except Exception as error:
            self.clean &= getattr(error, "command_cleaned", None) is True
            self.known()
            raise _Failure("device_call_failed") from None
        self.clean &= getattr(result, "cleanup_complete", None) is True
        if not self.known() and not retain_unclean:
            raise _Failure("client_cleanup_unknown")
        return result

    def shell(self, *arguments, deadline=20):
        result = self.raw(["shell", shlex.join(str(value) for value in arguments)], deadline)
        output = getattr(result, "stdout", None)
        if (getattr(result, "status", None) != "completed" or type(getattr(result, "returncode", None)) is not int
                or result.returncode != 0 or type(output) is not bytes or len(output) > 4096):
            raise _Failure("device_response_failed")
        return output


def _package(client, phase):
    client.stage = phase + "_package_path"
    raw = client.shell("pm", "path", PACKAGE)
    match = re.fullmatch(rb"package:(/data/app/[A-Za-z0-9_~+=./-]{1,512}/base\.apk)\r?\n?", raw)
    if match is None:
        raise _Failure("package_identity_failed")
    path = match[1].decode("ascii")
    if any(part in (".", "..") for part in path.split("/")):
        raise _Failure("package_identity_failed")
    client.stage = phase + "_package_hash"
    hashed = client.shell("sha256sum", path)
    expected = APK_SHA256.encode("ascii") + b"  " + match[1]
    if hashed not in (expected, expected + b"\n", expected + b"\r\n"):
        raise _Failure("package_identity_failed")


def _process(client, phase, deadline=20):
    client.stage = phase + "_process_probe"
    result = client.raw(["shell", shlex.join(["pidof", PACKAGE])], deadline)
    raw = getattr(result, "stdout", None)
    if getattr(result, "status", None) != "completed" or type(raw) is not bytes:
        raise _Failure("process_probe_failed")
    code = getattr(result, "returncode", None)
    if type(code) is int and code == 1 and raw == b"":
        return None
    if type(code) is not int or code != 0 or re.fullmatch(rb"[1-9][0-9]{0,9}\r?\n?", raw) is None:
        raise _Failure("process_probe_failed")
    pid = int(raw)
    if pid > 2147483647:
        raise _Failure("process_identity_failed")
    client.stage = phase + "_process_identity"
    command = client.shell("cat", f"/proc/{pid}/cmdline", deadline=deadline)
    ticks = spike.parse_stat(client.shell("cat", f"/proc/{pid}/stat", deadline=deadline), pid)
    if command.rstrip(b"\0") != PACKAGE.encode("ascii") or type(ticks) is not int or not 0 < ticks < 2 ** 64:
        raise _Failure("process_identity_failed")
    return pid, ticks  # Private only; never publish PIDs/start times.


def _stop(client, phase, package_verified=False):
    if not package_verified:
        _package(client, phase)
    _process(client, phase)
    client.stage = phase + "_force_stop"
    client.shell("am", "force-stop", PACKAGE)
    until = time.monotonic() + 5
    while time.monotonic() < until:
        if _process(client, phase, deadline=max(0.01, min(20, until - time.monotonic()))) is None:
            return
        time.sleep(0.05)
    client.stage = phase + "_absence"
    raise _Failure("process_absence_failed")


def _model(value, expected_uuid):
    if (type(value) is not dict or set(value) != MODEL_KEYS or type(value["verified"]) is not bool
            or type(value["volume_uuid"]) is not str or not admission.UUID.fullmatch(value["volume_uuid"])
            or type(value["sha256"]) is not str or not re.fullmatch(r"(?:[0-9a-f]{64})?", value["sha256"])
            or type(value["bytes"]) is not int or not 0 <= value["bytes"] <= admission.MAX_BYTES
            or type(value["diagnostic"]) is not str or value["diagnostic"] not in MODEL_DIAGNOSTICS):
        return False, "invalid_receipt"
    verified = (value["verified"] and value["diagnostic"] == "verified" and value["volume_uuid"] == expected_uuid
                and value["sha256"] == MODEL_SHA256 and value["bytes"] == MODEL_BYTES)
    return verified, value["diagnostic"]


def _expected(result, metrics, case):
    last = result["turns"][-1]
    expected = {"gift": "committed", "dialogue": "committed", "unlearned": "rejected",
                "spent": "rejected", "cancel": "cancelled"}[case]
    okay = last["outcome"] == expected and last["owner_drained"] and last["reopen_equal"]
    if case == "spent":
        okay &= result["gift_seeded"] and len(result["turns"]) == 2
    if case in ("spent", "unlearned"):
        okay &= last["error"] == {"spent": "Inventory", "unlearned": "Ability"}[case] and last["canon_unchanged"]
    if case == "cancel":
        okay &= last["first_output_observed"] and metrics.get("cancel_called") is True and metrics.get("cancel_terminal_callback") is True
    return bool(okay)


def run_control(device, apk_sha, case, expected_uuid, measure, model_identity, raw_sink=None):
    """One attempt, no provisioning/retry/removal. Callbacks are trusted bounded evidence adapters.

    model_identity must use THIS tracked device (or update its sticky clients_cleaned
    on every ADB call). measure has the same ownership obligation. raw_sink only
    retains bytes in caller-owned private host evidence; it must not dispatch devices.
    Original callback diagnostics belong in that caller's private journal.
    """
    report = {"version": 1, "scope": "android_explicit_cache_sdk_control", "case": case if type(case) is str and case in play.CASES else "invalid",
              "status": "input_refused", "result": None, "sdk": None, "model_verified": False,
              "model_diagnostic": "invalid_receipt", "failure_stage": "none", "cleanup_failure_stage": "none",
              "worker_status": None, "worker_error": None, "storage_samples_valid": False,
              "transport_valid": False,
              "process_absent": False, "clients_cleaned": False, "check_passed": False,
              "raw_protocol_retained": False, "artifacts_retained": True,
              "admission": None, "post": None, "storage_checks_passed": False, "dispatched": False,
              "phone_qualified": False, "wall_ms": 0}
    started = time.monotonic()
    client = _Client(device)
    if (type(apk_sha) is not str or apk_sha != APK_SHA256 or type(case) is not str or case not in play.CASES
            or type(expected_uuid) is not str or not admission.UUID.fullmatch(expected_uuid)
            or not callable(measure) or not callable(model_identity) or raw_sink is not None and not callable(raw_sink)):
        report["failure_stage"] = "input"
        return report
    if not client.known():
        report.update(status="ownership_unknown", failure_stage="initial_client_cleanup")
        return report

    def operation():
        established = False
        report["status"] = "setup_failed"
        try:
            _package(client, "initial")
            established = True
            _stop(client, "initial", package_verified=True)
            client.stage = "model_identity"
            try:
                value = model_identity()
            except Exception as error:
                client.clean &= getattr(error, "command_cleaned", None) is True
                client.known()
                report["model_diagnostic"] = "read_failed"
                raise _Failure("model_identity_failed") from None
            if not client.known():
                raise _Failure("client_cleanup_unknown")
            report["model_verified"], report["model_diagnostic"] = _model(value, expected_uuid)
            if not report["model_verified"]:
                raise _Failure("model_identity_failed")
            # App-domain verification can leave its instrumentation process alive.
            # Re-bind the installed bytes/process identity and stop before SDK play.
            _stop(client, "verified_model")
            client.stage = "profile"
            profile = base64.b64encode(json.dumps(play.make_profile(apk_sha), separators=(",", ":")).encode("utf-8")).decode("ascii")
            command = shlex.join(["am", "instrument", "-w", "-r", "-e", "operation", "play", "-e", "session", uuid.uuid4().hex,
                "-e", "volume_uuid", expected_uuid, "-e", "play_case", case, "-e", "profile_base64", profile,
                PACKAGE + "/" + INSTRUMENTATION])
            client.stage = "instrumentation"
            execution = client.raw(["shell", command], deadline=110, retain_unclean=True)
            raw = getattr(execution, "stdout", None)
            if type(raw) is bytes and len(raw) <= 131072 and raw_sink is not None:
                try:
                    raw_sink(raw)
                    report["raw_protocol_retained"] = True
                except Exception:
                    report["failure_stage"] = "raw_retention"
            report["transport_valid"] = (getattr(execution, "status", None) == "completed"
                and type(getattr(execution, "returncode", None)) is int and execution.returncode == 0 and client.known())
            if type(raw) is not bytes or len(raw) > 131072:
                report["status"] = "invalid_terminal"
                raise _Failure("invalid_terminal")
            client.stage = "terminal_parse"
            decoded = cache_result.parse_result(raw, case, expected_uuid)
            if decoded is None:
                report["status"] = "invalid_terminal"
                raise _Failure("invalid_terminal")
            # Assign accepted evidence BEFORE interpreting a later SDK/storage failure.
            report["result"] = copy.deepcopy(decoded["result"])
            report["sdk"] = copy.deepcopy(decoded["sdk"])
            report["worker_status"] = decoded["status"]
            report["worker_error"] = decoded["error"]
            report["storage_samples_valid"] = decoded["storage_samples_valid"]
            report["status"] = "observed"
            if not report["transport_valid"]:
                if report["failure_stage"] == "none":
                    report["failure_stage"] = "instrumentation"
            elif decoded["status"] != "completed" or decoded["error"] is not None or not decoded["storage_samples_valid"]:
                if report["failure_stage"] == "none":
                    report["failure_stage"] = "sdk_report"
            elif report["result"] is not None:
                report["check_passed"] = _expected(report["result"], report["sdk"], case)
        except Exception:
            if report["failure_stage"] == "none":
                report["failure_stage"] = client.stage
        finally:
            if client.known() and established:
                try:
                    _stop(client, "final")
                    report["process_absent"] = True
                except Exception:
                    report["cleanup_failure_stage"] = client.stage
            elif not client.known():
                report["cleanup_failure_stage"] = "client_cleanup_unknown"
            report["clients_cleaned"] = client.known()
            report["check_passed"] &= (report["process_absent"] and report["clients_cleaned"]
                and report["failure_stage"] == "none" and report["cleanup_failure_stage"] == "none")
        return report

    observed = admission.run_with_admission(measure, operation, expected_uuid)
    report["admission"], report["post"] = observed.admission, observed.post
    report["dispatched"] = observed.dispatched
    report["storage_checks_passed"] = observed.metadata()["storage_checks_passed"]
    report["clients_cleaned"] = client.known()
    if not report["clients_cleaned"]:
        report["process_absent"] = False
    if not observed.dispatched:
        report["status"] = "admission_blocked"
    report["check_passed"] &= report["storage_checks_passed"] and report["clients_cleaned"] and observed.failure is None
    report["wall_ms"] = round((time.monotonic() - started) * 1000)
    return report
