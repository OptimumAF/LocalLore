"""Guarded owner and fixed contract for the isolated story-deletion UI capture.

Importing this module defines the contract without creating a guest or running
any command. A live owner needs separately admitted source and operation scope.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_verification_v4 as verification
from benchmarks import cross_owner_deletion_ui_binding as artifacts
from benchmarks import cross_owner_deletion_ui_capture as capture
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks.owned_target_contract import (
    CLEANUP_KEYS, PORT, REQUEST_KEYS, WORKER_KEYS, TargetRefused, _int, _need, _obj,
    _path, _process, _same,
)

PROTOCOL = "owned-emulator-cross-owner-deletion-ui-v1"
RUN_SCOPE = PROTOCOL
SDK_PROTOCOL = "sdk-cross-owner-deletion-ui-v1"
PROOF_PROTOCOL = "cross-owner-deletion-ui-socket-proof-v1"
CLIENT_VERSION = 24
SESSION_FILE = "sdk-session-v24.json"
OWNER_SCRIPT = "owned_cross_owner_deletion_ui.py"
BOOT_CLAIM_FILE = "owned-cross-owner-deletion-ui-boot-claim-v1.json"
GUEST_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-cross-owner-deletion-owned-guest-v1/avd-v1")

APP = artifacts.APP
TEST = artifacts.TEST
MODEL_MATERIAL = False
INSTRUMENTATIONS = artifacts.INSTRUMENTATIONS
CLAIM_KINDS = tuple(kind for kind, _, _ in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(artifacts.artifact_bindings())
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | {
    OWNER_SCRIPT, "cross_owner_deletion_ui_binding.py", "cross_owner_deletion_ui_capture.py",
    "cross_owner_deletion_ui_replay.py", "cross_owner_deletion_ui_controller.py",
    "cross_owner_deletion_ui_boot.py", "cross_owner_deletion_ui_handoff.py",
    "cross_owner_deletion_ui_closure.py", "cross_owner_deletion_ui_operation.py",
    "cross_owner_deletion_ui_admission.py", "cross_owner_deletion_ui_preparation.py",
    "saved_library_status_binding.py",
    "archive_ui_build.py", "android_instrumentation_evidence.py",
})
_AUDIT_SOURCES = ("audit_apk.py", "audit_physical_model_apk.py")


class _CrossOwnerDeletionContract(core._Contract):
    def _sources(self, value):
        count = len(self.profile.SOURCE_NAMES) + len(_AUDIT_SOURCES)
        _need(type(value) is list and len(value) in (count, count + 1), "source")
        benchmark_pins = []
        script_paths = []
        for pin in value:
            self.binding(pin)
            path = PureWindowsPath(pin["path"])
            if path.parent.name == "benchmarks":
                benchmark_pins.append(pin)
            else:
                script_paths.append(path)
        paths = [pin["path"] for pin in value]
        _need(paths == sorted(set(paths)), "source")
        super()._sources(benchmark_pins)
        scripts = PureWindowsPath(benchmark_pins[0]["path"]).parent.parent / "scripts"
        _need(script_paths == [scripts / name for name in _AUDIT_SOURCES], "source")

    def source_bindings(self):
        pins = super().source_bindings()
        scripts = Path(pins[0]["path"]).parent.parent / "scripts"
        pins.extend(env.binding(scripts / name) for name in _AUDIT_SOURCES)
        return sorted(pins, key=lambda pin: pin["path"])

    def _install_argv(self, path):
        return ["pm", "install", "-R", "-t", "--user", "0", path]

    def validate_admission(self, value):
        admission = super().validate_admission(value)
        _need(_same(admission["artifacts"], artifacts.artifact_bindings()), "binding")
        return admission

    def validate_operation(self, value, admission):
        operation = super().validate_operation(value, admission)
        argv = operation["argv"]
        _need(argv[:1] != ["pidof"] and argv[:2] != ["am", "force-stop"], "capability")
        return operation


_API = _CrossOwnerDeletionContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))

# Fixed facade for the shared verifier's contract interface.
for _name in (
    "binding", "validate_admission", "validate_running", "validate_session",
    "validate_operation", "operation_digest", "validate_client_record",
    "validate_proof", "validate_query_bundle", "validate_claim", "claim_record",
    "instrumentation_kind", "source_bindings", "revalidate_inputs", "check_stop", "_rows",
    "validate_observation", "validate_guest_observation", "validate_guest_prefix",
    "device_transport", "validate_guest_job", "validate_ready",
):
    globals()[_name] = getattr(_API, _name)
del _name


_CONTRACT = sys.modules[__name__]
REPLAY = verification._Verifier(_CONTRACT)


class LiveOwnedCrossOwnerDeletionTarget(mechanisms._LiveOwnedTarget):
    """Observe one already owned target after checking the exact APK pair."""

    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedCrossOwnerDeletionTarget, "owner_type")
        admission_binding, running_binding = copy.deepcopy((admission_binding, running_binding))
        admission = validate_admission(REPLAY._json(admission_binding))
        artifacts.verify_artifacts(admission["artifacts"])
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedCrossOwnerDeletionTarget, "owner_type")
        return _CONTRACT

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedCrossOwnerDeletionTarget, "owner_type")
        return REPLAY


class OwnedCrossOwnerDeletionSdkCapture(wire._OwnedTargetSdkCapture):
    """Capture commands only through the fixed cross-owner deletion observer."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedCrossOwnerDeletionSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedCrossOwnerDeletionSdkCapture, "client_type")
        return _CONTRACT

    @property
    def _verification(self):
        wire._need(type(self) is OwnedCrossOwnerDeletionSdkCapture, "client_type")
        return REPLAY

    @property
    def _expected_lease_class(self):
        return LiveOwnedCrossOwnerDeletionTarget


def verify_capture(admission_binding, running_binding, session_binding, expected_caller):
    return capture.verify_capture(sys.modules[__name__], admission_binding, running_binding,
                                  session_binding, expected_caller)


def _live_boot(pin, record, approval, launch_inputs, parent=None):
    """Check the sealed handoff and held supervisor ancestry before dispatch."""
    from benchmarks import cross_owner_deletion_ui_handoff as handoff

    env.require(pin["path"] == str(handoff.HANDOFF)
                and pin["sha256"] == os.environ.get(handoff.HANDOFF_ENV), "handoff")
    supervisor = record["supervisor"]
    api = mechanisms._ProcessApi()
    handles = process.ProcessHandles(api)
    try:
        handles.add(supervisor["pid"], supervisor)
        if parent is None:
            env.require(os.getppid() == supervisor["pid"]
                        and {supervisor["pid"], os.getpid()} <= set(api.current_job_pids()), "identity")
        else:
            parent_handle, _ = handles.add(parent["pid"], parent)
            env.require(os.getppid() == parent["pid"] and api.parent_pid(parent_handle) == supervisor["pid"]
                        and os.getpid() in api.current_job_pids(), "identity")
        handles.guard()
    finally:
        env.require(handles.close() is True, "identity")
    for binding in (pin, record["authority"], record["attempt"], approval["admission"], *launch_inputs):
        env.check_binding(binding)
    handoff.check_window(record["began_ns"], record["until_ns"], minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)


class _CrossOwnerDeletionRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        from benchmarks import cross_owner_deletion_ui_handoff as handoff

        mechanisms._need(type(self) is _CrossOwnerDeletionRuntime, "owner_type")
        self._launch = handoff.verify_boot(request["admission"], request["validated_admission"])
        _live_boot(*self._launch, parent=request["owner"])
        super().__init__(request, request_binding, root)

    @property
    def _contract(self):
        return _CONTRACT

    @property
    def _verification(self):
        return REPLAY

    def start_server(self):
        _live_boot(*self._launch, parent=self.request["owner"])
        env.check_binding(self._launch[2]["ledger"])
        super().start_server()

    def guard(self):
        from benchmarks import cross_owner_deletion_ui_handoff as handoff

        super().guard()
        record = self._launch[1]
        minimum = handoff.LAUNCH_TAIL_SECONDS if self.guest_child is None else 0
        handoff.check_window(record["began_ns"], record["until_ns"], minimum_seconds=minimum)

    def _retain_guest(self):
        _live_boot(*self._launch, parent=self.request["owner"])
        guest = self.admission["guest"]
        env.storage_transition(storage.record_state, Path(guest["root"]), "retained",
                               proposal_sha256=guest["proposal"]["sha256"],
                               expected_prepare_sha256=self.proposal["prepare_proposal"]["sha256"],
                               expected_ledger=self._launch[2]["ledger"])
        _live_boot(*self._launch, parent=self.request["owner"])

    def admit_guest(self):
        from benchmarks import cross_owner_deletion_ui_controller as controller

        ready = super().admit_guest()
        _live_boot(*self._launch, parent=self.request["owner"])
        # An uncertain controller leaves the full storage charge. The owned
        # worker still takes its normal stop path and preserves the evidence.
        owner_clients_closed = self.clients_closed
        self.clients_closed = False
        try:
            result = controller.run(self.binding, self.running_binding)
            self.clients_closed = (owner_clients_closed and result["outcome"] == "completed"
                                   and result["observer_handles_closed"] is True)
        finally:
            self.guard()
            stop = dict(version=1, protocol=PROTOCOL, admission_sha256=self.binding["sha256"], action="stop")
            check_stop(stop, self.binding["sha256"])
            pending = self.root / "stop.pending-v1.json"
            env.create_json(pending, stop)
            self.guard()
            pending.rename(self.root / "stop-v1.json")
        return ready


def main(argv=None):
    from benchmarks import cross_owner_deletion_ui_handoff as handoff

    args = sys.argv[1:] if argv is None else argv
    digest = os.environ.get(handoff.HANDOFF_ENV, "")
    if type(args) is not list or re.fullmatch("[0-9a-f]{64}", digest) is None:
        return 1
    if args != ["_worker"] and not (
        len(args) == 4 and args[:3] == ["--admission", str(handoff.ADMISSION), "--admission-sha256"]
        and type(args[3]) is str and re.fullmatch("[0-9a-f]{64}", args[3]) is not None
    ):
        return 1

    admission_pin = launch = None

    def check_admission(admission):
        nonlocal admission_pin, launch
        pin, current = handoff.read(handoff.ADMISSION)
        env.require(pin["sha256"] == args[3] and _same(current, admission), "admission")
        env.require(not any(os.path.lexists(path) for path in (handoff.OWNED_ROOT, handoff.COMPLETION)),
                    "already_used")
        launch = handoff.verify_boot(pin, admission)
        _live_boot(*launch)
        admission_pin = pin

    status = mechanisms._main_profile(args, _contract=_CONTRACT, _verification=REPLAY,
                                      _runtime_type=_CrossOwnerDeletionRuntime, _admission_check=check_admission)
    if status != 0 or args == ["_worker"]:
        return status

    from benchmarks import cross_owner_deletion_ui_closure as closure

    try:
        env.require(admission_pin is not None and launch is not None, "admission")
        handoff_pin, record, _, _ = launch
        handoff.check_window(record["began_ns"], record["until_ns"])
        result = closure.verify_result(admission_pin)
        for pin in (handoff_pin, record["authority"], record["attempt"], admission_pin):
            env.check_binding(pin)
        handoff.check_window(record["began_ns"], record["until_ns"])
        env.create_json(handoff.COMPLETION, dict(version=1, scope=handoff.AUTHORITY_SCOPE,
                                                 admission=admission_pin, **result))
    except Exception:
        print(json.dumps(dict(passed=False, reason="activation_refused", feature_acceptance=False)), flush=True)
        return 1
    print(json.dumps(dict(passed=True, feature_acceptance=False)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
