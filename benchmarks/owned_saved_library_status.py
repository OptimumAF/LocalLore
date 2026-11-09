"""Observe or start one approved, prepared saved-library status guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path, PureWindowsPath
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_verification_v4 as verification
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as environment
from benchmarks import receipt_avd_storage as storage
from benchmarks import saved_library_status_binding as artifacts

PROTOCOL = "owned-emulator-saved-library-status-v1"
RUN_SCOPE = PROTOCOL
SDK_PROTOCOL = "sdk-saved-library-status-v1"
PROOF_PROTOCOL = "saved-library-status-socket-proof-v1"
CLIENT_VERSION = 23
SESSION_FILE = "sdk-session-v23.json"
OWNER_SCRIPT = "owned_saved_library_status.py"
BOOT_CLAIM_FILE = "owned-saved-library-status-boot-claim-v1.json"
GUEST_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-saved-library-owned-guest-v1/avd-v1")
APP = artifacts.APP
TEST = artifacts.TEST
MODEL_MATERIAL = False
INSTRUMENTATIONS = artifacts.INSTRUMENTATIONS
CLAIM_KINDS = tuple(kind for kind, _, _ in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(("build", "product_apk", "test_apk"))
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | {
    OWNER_SCRIPT, "saved_library_status_binding.py", "saved_library_status_controller.py",
    "saved_library_status_handoff.py", "saved_library_status_preparation.py",
    "saved_library_status_activation.py", "saved_library_status_closure.py",
    "saved_library_status_operation.py", "archive_ui_build.py", "android_instrumentation_evidence.py",
    "prepare_recovery_contract.py",
})
_DEX_AUDIT_SOURCES = ("audit_apk.py", "audit_physical_model_apk.py")
OwnerRefused = mechanisms.OwnerRefused
ClientRefused = wire.ClientRefused


class _SavedLibraryStatusContract(core._Contract):
    def _sources(self, value):
        # The APK binding uses a DEX auditor and its shared audit primitives.
        # Both are exact siblings of the closed benchmark roster.
        count = len(self.profile.SOURCE_NAMES) + len(_DEX_AUDIT_SOURCES)
        core._need(type(value) is list and len(value) in (count, count + 1), "source")
        benchmark_pins = []
        audit_paths = []
        for pin in value:
            self.binding(pin)
            path = PureWindowsPath(pin["path"])
            if path.parent.name == "benchmarks":
                benchmark_pins.append(pin)
            else:
                audit_paths.append(path)
        paths = [pin["path"] for pin in value]
        core._need(paths == sorted(set(paths)), "source")
        super()._sources(benchmark_pins)
        scripts = PureWindowsPath(benchmark_pins[0]["path"]).parent.parent / "scripts"
        core._need(audit_paths == [scripts / name for name in _DEX_AUDIT_SOURCES], "source")

    def source_bindings(self):
        pins = super().source_bindings()
        scripts = Path(pins[0]["path"]).parent.parent / "scripts"
        pins.extend(environment.binding(scripts / name) for name in _DEX_AUDIT_SOURCES)
        return sorted(pins, key=lambda pin: pin["path"])

    def _install_argv(self, path):
        # Android 15 enables replacement by default unless -R clears it.
        return ["pm", "install", "-R", "-t", "--user", "0", path]

    def validate_admission(self, value):
        admission = super().validate_admission(value)
        core._need(core._same(admission["artifacts"], artifacts.artifact_bindings()), "binding")
        return admission

    def validate_operation(self, value, admission):
        operation = super().validate_operation(value, admission)
        argv = operation["argv"]
        core._need(argv[:1] != ["pidof"] and argv[:2] != ["am", "force-stop"], "capability")
        return operation


_API = _SavedLibraryStatusContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))

for _name in (
    "PORT", "ADMISSION_KEYS", "GUEST_KEYS", "RUNNING_KEYS", "SESSION_KEYS",
    "CONTEXT_KEYS", "PROOF_KEYS", "QUERY_BUNDLE_KEYS", "QUERY_KEYS", "BRACKET_KEYS",
    "READY_KEYS", "JOB_KEYS", "REQUEST_KEYS", "WORKER_KEYS", "CLEANUP_KEYS",
    "CLIENT_KEYS", "TargetRefused", "_need", "_obj", "_int", "_same", "_path", "_process",
):
    globals()[_name] = getattr(core, _name)

for _name in (
    "binding", "_sources", "validate_admission", "_clock", "validate_running", "check_stop",
    "validate_session", "_relative", "validate_operation", "operation_digest", "_rows",
    "validate_observation", "_guest_observation", "validate_guest_observation", "validate_guest_prefix",
    "device_status", "device_transport", "validate_proof", "_brackets", "validate_query_bundle",
    "validate_guest_job", "validate_ready", "validate_claim", "validate_client_record",
    "source_bindings", "revalidate_inputs", "instrumentation_kind", "claim_record",
):
    globals()[_name] = getattr(_API, _name)
del _name

_CONTRACT = sys.modules[__name__]
REPLAY = verification._Verifier(_CONTRACT)


class LiveOwnedSavedLibraryStatusTarget(mechanisms._LiveOwnedTarget):
    """Verify the fixed signed pair before opening any live observer handles."""

    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedSavedLibraryStatusTarget, "owner_type")
        admission_binding = copy.deepcopy(admission_binding)
        running_binding = copy.deepcopy(running_binding)
        admission = _API.validate_admission(mechanisms._read_json(
            admission_binding, _contract=_CONTRACT))
        artifacts.verify_artifacts(admission["artifacts"])
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedSavedLibraryStatusTarget, "owner_type")
        return _CONTRACT

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedSavedLibraryStatusTarget, "owner_type")
        return REPLAY


class OwnedSavedLibraryStatusSdkCapture(wire._OwnedTargetSdkCapture):
    """Use only this profile and its exact live observer class."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedSavedLibraryStatusSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedSavedLibraryStatusSdkCapture, "client_type")
        return _CONTRACT

    @property
    def _verification(self):
        wire._need(type(self) is OwnedSavedLibraryStatusSdkCapture, "client_type")
        return REPLAY

    @property
    def _expected_lease_class(self):
        wire._need(type(self) is OwnedSavedLibraryStatusSdkCapture, "client_type")
        return LiveOwnedSavedLibraryStatusTarget


def _live_boot(pin, approved, launch_inputs, parent=None):
    """Recheck the pinned handoff and the actual enclosing process identities."""
    from benchmarks import saved_library_status_handoff as handoff

    current_pin, current = handoff.read(handoff.HANDOFF)
    environment.require(
        pin["sha256"] == os.environ.get(handoff.HANDOFF_ENV)
        and _same(current_pin, pin) and _same(current, approved), "handoff",
    )
    supervisor = approved["supervisor"]
    api = mechanisms._ProcessApi()
    handles = process.ProcessHandles(api)
    try:
        handles.add(supervisor["pid"], supervisor)
        if parent is None:
            environment.require(os.getppid() == supervisor["pid"]
                        and {supervisor["pid"], os.getpid()} <= set(api.current_job_pids()), "identity")
        else:
            parent_handle, _ = handles.add(parent["pid"], parent)
            environment.require(os.getppid() == parent["pid"] and api.parent_pid(parent_handle) == supervisor["pid"]
                        and os.getpid() in api.current_job_pids(), "identity")
        handles.guard()
    finally:
        environment.require(handles.close() is True, "identity")
    for binding in (pin, approved["authority"], approved["attempt"], approved["admission"], *launch_inputs):
        environment.check_binding(binding)
    handoff.check_launch_window(approved["began_ns"], approved["until_ns"])


class _SavedLibraryStatusRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        from benchmarks import saved_library_status_handoff as handoff

        mechanisms._need(type(self) is _SavedLibraryStatusRuntime, "owner_type")
        self._handoff_pin, self._handoff, self._launch_inputs = handoff.verify_boot_handoff(
            request["admission"], request["validated_admission"])
        _live_boot(self._handoff_pin, self._handoff, self._launch_inputs, request["owner"])
        super().__init__(request, request_binding, root)

    def start_server(self):
        _live_boot(self._handoff_pin, self._handoff, self._launch_inputs, self.request["owner"])
        super().start_server()

    def guard(self):
        from benchmarks import saved_library_status_handoff as handoff

        super().guard()
        window = handoff.check_launch_window if self.guest_child is None else handoff.check_window
        window(self._handoff["began_ns"], self._handoff["until_ns"])

    def _retain_guest(self):
        _live_boot(self._handoff_pin, self._handoff, self._launch_inputs, self.request["owner"])
        guest = self.admission["guest"]
        environment.storage_transition(
            storage.record_state, Path(guest["root"]), "retained",
            proposal_sha256=guest["proposal"]["sha256"],
            expected_prepare_sha256=self.proposal["prepare_proposal"]["sha256"],
        )
        _live_boot(self._handoff_pin, self._handoff, self._launch_inputs, self.request["owner"])

    @property
    def _contract(self):
        return _CONTRACT

    @property
    def _verification(self):
        return REPLAY


def main(argv=None):
    from benchmarks import saved_library_status_handoff as handoff

    args = sys.argv[1:] if argv is None else argv
    if type(args) is not list or (args != ["_worker"] and not (
        len(args) == 4 and args[:3] == ["--admission", str(handoff.ADMISSION), "--admission-sha256"]
    )):
        return 1

    def check_admission(admission):
        pin, current = handoff.read(handoff.ADMISSION)
        environment.require(pin["sha256"] == args[3] and _same(current, admission), "admission")
        environment.require(not os.path.lexists(handoff.OWNED_ROOT), "already_used")
        _live_boot(*handoff.verify_boot_handoff(pin, admission))

    return mechanisms._main_profile(args, _contract=_CONTRACT, _verification=REPLAY,
                                    _runtime_type=_SavedLibraryStatusRuntime,
                                    _admission_check=check_admission)


if __name__ == "__main__":
    raise SystemExit(main())
