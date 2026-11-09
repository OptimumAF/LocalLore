"""Dedicated observer, capture and replay profile for the two storage-opener tests.

An independently admitted owner supplies the running target and owns its
lifecycle. There is no launch entry point in this profile.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path, PureWindowsPath
import sys
import time

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_verification_v4 as verification
from benchmarks import combined_record_ui_controller as owner_checks
from benchmarks import owned_combined_record_ui_contract as precedent
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import storage_opener_capture as artifacts
from benchmarks import storage_opener_journey as journey

PROTOCOL = "owned-emulator-storage-opener-v1"
SDK_PROTOCOL = "sdk-storage-opener-v1"
PROOF_PROTOCOL = "storage-opener-socket-proof-v1"
CLIENT_VERSION = 27
SESSION_FILE = "sdk-session-v27.json"
OWNER_SCRIPT = "owned_storage_opener.py"
BOOT_CLAIM_FILE = "owned-storage-opener-boot-claim-v1.json"
GUEST_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-storage-opener-owned-guest-v1/avd-v1")
SECONDS = 1200
APP = artifacts.APP
TEST = artifacts.TEST
MODEL_MATERIAL = False
CLAIM_KINDS = artifacts.KINDS
INSTRUMENTATIONS = tuple((kind, *artifacts.instrumentation_argv(kind)[6].split("#"))
                         for kind in CLAIM_KINDS)
ARTIFACT_KEYS = frozenset(("build", "product_apk", "test_apk"))
SOURCE_NAMES = precedent.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | {
    OWNER_SCRIPT, "storage_opener_capture.py", "storage_opener_journey.py",
}
SCRIPT_SOURCE_NAMES = frozenset(("audit_apk.py", "audit_instrumentation_apk.py",
                                 "audit_physical_model_apk.py", "check.py"))


def _source_paths(root):
    return sorted((root / folder / name for folder, names in
                   (("benchmarks", SOURCE_NAMES), ("scripts", SCRIPT_SOURCE_NAMES))
                   for name in names), key=str)


class _StorageOpenerContract(core._Contract):
    def _sources(self, value):
        core._need(type(value) is list and len(value) == len(SOURCE_NAMES) + len(SCRIPT_SOURCE_NAMES), "source")
        for pin in value:
            self.binding(pin)
        paths = [pin["path"] for pin in value]
        root = PureWindowsPath(paths[0]).parent.parent
        core._need(paths == [str(path) for path in _source_paths(root)], "source")

    def source_bindings(self):
        root = Path(__file__).resolve().parents[1]
        core._need(root.drive.upper() == "D:" and root.resolve(strict=True) == root, "source")
        return [env.binding(path) for path in _source_paths(root)]

    def validate_admission(self, value):
        admission = super().validate_admission(value)
        core._need(core._same(admission["artifacts"], artifacts.artifact_bindings()), "binding")
        return admission

    def validate_session(self, value, admission):
        session = super().validate_session(value, admission)
        expected_root = PureWindowsPath(admission["root"]) / "controller-v1"
        core._need(PureWindowsPath(session["root"]) == expected_root and session["seconds"] == SECONDS, "binding")
        return session

    def _install_argv(self, path):
        return ["pm", "install", "-R", "-t", "--user", "0", path]

    def validate_operation(self, value, admission):
        operation = super().validate_operation(value, admission)
        argv = operation["argv"]
        core._need(argv[:1] != ["pidof"] and argv[:2] != ["am", "force-stop"], "capability")
        return operation


_API = _StorageOpenerContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES, CLIENT_VERSION,
    SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE, INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))
for _name in ("PORT", "REQUEST_KEYS", "WORKER_KEYS", "CLEANUP_KEYS", "TargetRefused",
              "_int", "_need", "_obj", "_path", "_process", "_same"):
    globals()[_name] = getattr(core, _name)
for _name in (
    "binding", "_rows", "validate_admission", "validate_running", "validate_session", "check_stop",
    "validate_operation", "operation_digest", "validate_observation", "validate_guest_observation",
    "validate_guest_prefix", "device_status", "device_transport", "validate_proof", "validate_query_bundle",
    "validate_guest_job", "validate_ready", "validate_claim", "validate_client_record",
    "source_bindings", "revalidate_inputs", "instrumentation_kind", "claim_record",
):
    globals()[_name] = getattr(_API, _name)
del _name

_CONTRACT = sys.modules[__name__]
REPLAY = verification._Verifier(_CONTRACT)


class LiveOwnedStorageOpenerTarget(mechanisms._LiveOwnedTarget):
    """Verify the APK pair before acquiring observer handles."""

    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedStorageOpenerTarget, "owner_type")
        admission_binding = copy.deepcopy(admission_binding)
        running_binding = copy.deepcopy(running_binding)
        admission = validate_admission(mechanisms._read_json(admission_binding, _contract=_CONTRACT))
        artifacts.verify_artifacts(admission["artifacts"])
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedStorageOpenerTarget, "owner_type")
        return _CONTRACT

    @property
    def _verification(self):
        return REPLAY


class OwnedStorageOpenerSdkCapture(wire._OwnedTargetSdkCapture):
    """Bind the v4 capture to this profile's observer and verifier."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedStorageOpenerSdkCapture and core._same(seconds, SECONDS), "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedStorageOpenerSdkCapture, "client_type")
        return _CONTRACT

    @property
    def _verification(self):
        return REPLAY

    @property
    def _expected_lease_class(self):
        return LiveOwnedStorageOpenerTarget


def replay_owned_journey(admission_binding, running_binding, session_binding, count):
    """Replay only the specified owner's controller session and complete rows."""
    core._int(count, 1 + journey.COMMANDS_AFTER_BOOT, journey.MAX_BOOT_POLLS + journey.COMMANDS_AFTER_BOOT, "binding")
    admission = validate_admission(REPLAY._json(admission_binding))
    root = Path(admission["root"]) / "controller-v1"
    session = validate_session(REPLAY._at(session_binding, root / SESSION_FILE), admission)
    core._need(core._same(session["admission"], admission_binding) and
               core._same(session["running"], running_binding), "binding")
    rows = REPLAY.require_current_clients(root, count, session_binding, admission)
    return journey.replay_journey(admission["artifacts"], rows, REPLAY._raw)


def run_owned_journey(client):
    """Execute the fixed journey on a fresh capture owned by the caller."""
    wire._need(type(client) is OwnedStorageOpenerSdkCapture and client.clean and client.count == 0, "client_guard")
    session = client.session
    admission = validate_admission(REPLAY._json(session["admission"]))
    validate_session(session, admission)
    until = client.until
    boot_until = min(until, time.monotonic() + 120)

    def command(argv, label, *, source=None, seconds=15, limit=131072):
        deadline = boot_until if label == "boot" else until
        budget = min(seconds, owner_checks._remaining(deadline))
        previous = client.count
        client.until = deadline
        try:
            if source is None:
                raw = client.shell(argv, label, seconds=budget, cap=limit)
            else:
                raw = client.stream(argv, source, label, seconds=budget, cap=limit)
        finally:
            client.until = until
        owner_checks._remaining(deadline)
        core._need(client.count == previous + 1, "binding")
        row = REPLAY._json(REPLAY._pin(client.directory / f"command-{client.count:04d}.json"))
        owner_checks._check_command(row, client.count, argv, label, source, seconds)
        core._need(REPLAY._raw(row["stdout"], cap=limit) == raw, "binding")
        stderr = REPLAY._raw(row["stderr"], cap=limit)
        core._need(source is not None or stderr == b"", "checks_failed")
        return raw

    def pause():
        client.lease.guard(min_seconds=2)
        core._need(owner_checks._remaining(boot_until) > 2, "deadline")
        time.sleep(2)

    result = journey.run_journey(admission["artifacts"], command, pause)
    core._need(client.clean and core._same(result, replay_owned_journey(
        session["admission"], session["running"], client.session_binding, client.count)), "binding")
    revalidate_inputs(admission)
    owner_checks._remaining(until)
    return result
