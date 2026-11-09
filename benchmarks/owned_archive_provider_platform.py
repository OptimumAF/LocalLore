"""Observe and capture only the fixed archive provider cancellation profile.

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
from benchmarks import archive_provider_platform_binding as artifacts
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

PROTOCOL = "owned-emulator-archive-provider-platform-v1"
RUN_SCOPE = PROTOCOL
SDK_PROTOCOL = "sdk-archive-provider-platform-v1"
PROOF_PROTOCOL = "archive-provider-platform-socket-proof-v1"
CLIENT_VERSION = 26
SESSION_FILE = "sdk-session-v26.json"
OWNER_SCRIPT = "owned_archive_provider_platform.py"
BOOT_CLAIM_FILE = "owned-archive-provider-platform-boot-claim-v1.json"
HANDOFF_ENV = "LOCALLORE_ARCHIVE_PROVIDER_PLATFORM_HANDOFF_SHA256"
GUEST_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-archive-provider-platform-guest-v1/avd-v1")
APP = artifacts.APP
TEST = artifacts.TEST
MODEL_MATERIAL = False
INSTRUMENTATIONS = artifacts.INSTRUMENTATIONS
CLAIM_KINDS = tuple(kind for kind, _, _ in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(("build", "product_apk", "test_apk"))
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | {
    OWNER_SCRIPT, "archive_provider_platform_binding.py", "archive_ui_build.py",
    "archive_provider_platform_controller.py", "android_instrumentation_evidence.py",
    "archive_provider_platform_preparation.py", "archive_provider_platform_admission.py",
    "archive_provider_platform_handoff.py", "archive_provider_platform_closure.py",
    "archive_provider_platform_operation.py",
})
_DEX_AUDIT_SOURCES = ("audit_apk.py", "audit_physical_model_apk.py")


class _ArchiveProviderPlatformContract(core._Contract):
    def _sources(self, value):
        core._need(type(value) is list and len(value) in (
            len(SOURCE_NAMES) + len(_DEX_AUDIT_SOURCES),
            len(SOURCE_NAMES) + len(_DEX_AUDIT_SOURCES) + 1,
        ), "source")
        benchmark_pins = []
        audit_paths = []
        for pin in value:
            self.binding(pin)
            path = PureWindowsPath(pin["path"])
            if path.parent.name == "benchmarks":
                benchmark_pins.append(pin)
            else:
                audit_paths.append(pin["path"])
        paths = [pin["path"] for pin in value]
        core._need(paths == sorted(set(paths)), "source")
        super()._sources(benchmark_pins)
        scripts = PureWindowsPath(benchmark_pins[0]["path"]).parent.parent / "scripts"
        core._need(audit_paths == [str(scripts / name) for name in _DEX_AUDIT_SOURCES], "source")

    def source_bindings(self):
        pins = super().source_bindings()
        scripts = Path(pins[0]["path"]).parent.parent / "scripts"
        pins.extend(env.binding(scripts / name) for name in _DEX_AUDIT_SOURCES)
        return sorted(pins, key=lambda pin: pin["path"])

    def _install_argv(self, path):
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


_API = _ArchiveProviderPlatformContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))

for _name in (
    "PORT", "ADMISSION_KEYS", "GUEST_KEYS", "RUNNING_KEYS", "SESSION_KEYS",
    "CONTEXT_KEYS", "PROOF_KEYS", "QUERY_BUNDLE_KEYS", "QUERY_KEYS", "BRACKET_KEYS",
    "READY_KEYS", "JOB_KEYS", "REQUEST_KEYS", "WORKER_KEYS", "CLEANUP_KEYS", "CLIENT_KEYS",
    "TargetRefused", "_need", "_obj", "_int", "_same", "_path", "_process",
):
    globals()[_name] = getattr(core, _name)

for _name in (
    "binding", "_sources", "validate_admission", "_clock", "validate_running", "check_stop",
    "validate_session", "_relative", "validate_operation", "operation_digest", "_rows",
    "validate_observation", "_guest_observation", "validate_guest_observation",
    "validate_guest_prefix", "device_status", "device_transport", "validate_proof",
    "_brackets", "validate_query_bundle", "validate_guest_job", "validate_ready",
    "validate_claim", "validate_client_record", "source_bindings", "revalidate_inputs",
    "instrumentation_kind", "claim_record",
):
    globals()[_name] = getattr(_API, _name)
del _name

_CONTRACT = sys.modules[__name__]
REPLAY = verification._Verifier(_CONTRACT)


class LiveOwnedArchiveProviderPlatformTarget(mechanisms._LiveOwnedTarget):
    """Verify the exact artifacts before opening any observer handles."""

    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedArchiveProviderPlatformTarget, "owner_type")
        admission_binding = copy.deepcopy(admission_binding)
        running_binding = copy.deepcopy(running_binding)
        admission = _API.validate_admission(mechanisms._read_json(admission_binding, _contract=_CONTRACT))
        artifacts.verify_artifacts(admission["artifacts"])
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedArchiveProviderPlatformTarget, "owner_type")
        return _CONTRACT

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedArchiveProviderPlatformTarget, "owner_type")
        return REPLAY


class OwnedArchiveProviderPlatformSdkCapture(wire._OwnedTargetSdkCapture):
    """Use the shared capture only with this profile's exact observer class."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedArchiveProviderPlatformSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedArchiveProviderPlatformSdkCapture, "client_type")
        return _CONTRACT

    @property
    def _verification(self):
        wire._need(type(self) is OwnedArchiveProviderPlatformSdkCapture, "client_type")
        return REPLAY

    @property
    def _expected_lease_class(self):
        wire._need(type(self) is OwnedArchiveProviderPlatformSdkCapture, "client_type")
        return LiveOwnedArchiveProviderPlatformTarget


def _load_live_boot(admission_pin, admission):
    from benchmarks import archive_provider_platform_admission as candidate
    from benchmarks import archive_provider_platform_handoff as handoff

    pin = env.binding(candidate.HANDOFF)
    env.require(pin["sha256"] == os.environ.get(HANDOFF_ENV), "handoff")
    return (pin, *handoff.verify_boot(admission_pin, admission, pin))


def _live_boot(pin, record, approved, launch_inputs, parent=None, *, minimum_seconds=1220):
    """Hold the expected ancestor identities and check the current Windows Job."""
    from benchmarks import archive_provider_platform_admission as candidate
    from benchmarks import archive_provider_platform_handoff as handoff

    env.require(pin["path"] == str(candidate.HANDOFF) and pin["sha256"] == os.environ.get(HANDOFF_ENV),
                "handoff")
    supervisor = record["supervisor"]
    api = mechanisms._ProcessApi()
    handles = process.ProcessHandles(api)
    try:
        handles.add(supervisor["pid"], supervisor)
        members = set(api.current_job_pids())
        if parent is None:
            env.require(os.getppid() == supervisor["pid"] and {supervisor["pid"], os.getpid()} <= members,
                        "identity")
        else:
            parent_handle, _ = handles.add(parent["pid"], parent)
            # The owner worker is in the shared launcher's nested Job.
            env.require(os.getppid() == parent["pid"] and api.parent_pid(parent_handle) == supervisor["pid"]
                        and os.getpid() in members, "identity")
        handles.guard()
    finally:
        env.require(handles.close() is True, "identity")
    for binding in (pin, record["authority"], record["attempt"], approved["admission"], *launch_inputs):
        env.check_binding(binding)
    handoff.check_window(record["began_ns"], record["until_ns"], minimum_seconds=minimum_seconds)


def _check_resources(proposal):
    facts = env.resource_facts(proposal)
    env.require(facts["free_bytes"]["D:"] >= proposal["host_free_min"]["D:"] + 256 * 1024**2,
                "records_capacity")


class _ArchiveProviderPlatformRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        mechanisms._need(type(self) is _ArchiveProviderPlatformRuntime, "owner_type")
        self._launch = _load_live_boot(request["admission"], request["validated_admission"])
        _live_boot(*self._launch, parent=request["owner"])
        super().__init__(request, request_binding, root)

    @property
    def _contract(self):
        return _CONTRACT

    @property
    def _verification(self):
        return REPLAY

    def _prelaunch(self, proposal):
        _live_boot(*self._launch, parent=self.request["owner"])
        env.check_binding(self._launch[2]["ledger"])
        _check_resources(proposal)
        env.ports_free()
        _live_boot(*self._launch, parent=self.request["owner"])
        env.check_binding(self._launch[2]["ledger"])

    def start_server(self):
        from benchmarks import archive_provider_platform_admission as candidate
        from benchmarks import archive_provider_platform_preparation as prep

        pin = self.admission["guest"]["proposal"]
        self._prelaunch(env.decode_json(prep._bound(pin, candidate.RUN)))
        super().start_server()

    def guard(self):
        from benchmarks import archive_provider_platform_handoff as handoff

        super().guard()
        record = self._launch[1]
        minimum = handoff.LAUNCH_TAIL_SECONDS if self.guest_child is None else 0
        handoff.check_window(record["began_ns"], record["until_ns"], minimum_seconds=minimum)

    def _retain_guest(self):
        self._prelaunch(self.proposal)
        guest = self.admission["guest"]
        env.storage_transition(storage.record_state, Path(guest["root"]), "retained",
                               proposal_sha256=guest["proposal"]["sha256"],
                               expected_prepare_sha256=self.proposal["prepare_proposal"]["sha256"],
                               expected_ledger=self._launch[2]["ledger"])
        _live_boot(*self._launch, parent=self.request["owner"])

    def admit_guest(self):
        from benchmarks import archive_provider_platform_controller as controller

        ready = super().admit_guest()
        previous = self.clients_closed
        self.clients_closed = False
        try:
            _live_boot(*self._launch, parent=self.request["owner"])
            result = controller.run(self.binding, self.running_binding)
            self.clients_closed = (previous and result["outcome"] == "completed"
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
    from benchmarks import archive_provider_platform_admission as candidate
    from benchmarks import archive_provider_platform_closure as closure
    from benchmarks import archive_provider_platform_handoff as handoff

    args = sys.argv[1:] if argv is None else argv
    digest = os.environ.get(HANDOFF_ENV, "")
    if type(args) is not list or re.fullmatch("[0-9a-f]{64}", digest) is None:
        return 1
    if args != ["_worker"] and not (
        len(args) == 4 and args[:3] == ["--admission", str(candidate.ADMISSION), "--admission-sha256"]
        and type(args[3]) is str and re.fullmatch("[0-9a-f]{64}", args[3]) is not None
    ):
        return 1
    try:
        env.require(env.binding(candidate.HANDOFF)["sha256"] == digest, "handoff")
    except (OSError, RuntimeError, ValueError):
        return 1

    admission_pin = launch = owner_identity = None

    def check_admission(admission):
        nonlocal admission_pin, launch, owner_identity
        pin = env.binding(candidate.ADMISSION)
        env.require(pin["sha256"] == args[3] and not any(
            os.path.lexists(path) for path in (candidate.OWNED_ROOT, candidate.COMPLETION)
        ), "admission")
        launch = _load_live_boot(pin, admission)
        _live_boot(*launch)
        owner_identity = env.process_identity(os.getpid())
        env.require(owner_identity["executable"] == admission["python"]["executable"]["path"], "identity")
        admission_pin = pin

    status = mechanisms._main_profile(args, _contract=_CONTRACT, _verification=REPLAY,
                                      _runtime_type=_ArchiveProviderPlatformRuntime,
                                      _admission_check=check_admission)
    if status != 0 or args == ["_worker"]:
        return status
    try:
        env.require(admission_pin is not None and launch is not None and owner_identity is not None, "admission")
        handoff_pin, record, approved, inputs = launch
        window = (record["began_ns"], record["until_ns"])
        handoff.check_window(*window)
        evidence = closure.verify_result(admission_pin, owner_identity)
        for pin in (handoff_pin, record["authority"], record["attempt"], approved["candidate"],
                    admission_pin, *inputs, *evidence.values()):
            env.check_binding(pin)
        handoff.check_window(*window)
        env.create_json(candidate.COMPLETION, dict(version=1, scope=handoff.AUTHORITY_SCOPE,
                                                   admission=admission_pin, **evidence))
    except Exception:
        print(json.dumps(dict(passed=False, reason="activation_refused", feature_acceptance=False)), flush=True)
        return 1
    print(json.dumps(dict(passed=True, feature_acceptance=False)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
