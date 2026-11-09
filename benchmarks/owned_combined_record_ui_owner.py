"""Observe or start one approved, prepared combined Story Record target.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import android_process_verification_v4 as verification
from benchmarks import combined_record_ui_binding as artifact_policy
from benchmarks import combined_record_ui_handoff as handoff
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_combined_record_ui_contract as contract
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

REPLAY = verification._Verifier(contract)


class LiveOwnedCombinedRecordUiTarget(mechanisms._LiveOwnedTarget):
    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedCombinedRecordUiTarget, "owner_type")
        admission_binding = copy.deepcopy(admission_binding)
        running_binding = copy.deepcopy(running_binding)
        admission = contract.validate_admission(mechanisms._read_json(
            admission_binding, _contract=contract))
        artifact_policy.verify_artifacts(admission["artifacts"])
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedCombinedRecordUiTarget, "owner_type")
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedCombinedRecordUiTarget, "owner_type")
        return REPLAY


def _live_boot(pin, approved, parent=None):
    """Recheck the pinned handoff and the actual enclosing process identities."""
    current_pin, current = handoff.read(handoff.HANDOFF)
    env.require(pin["sha256"] == os.environ.get(handoff.HANDOFF_ENV)
                and contract._same(current_pin, pin) and contract._same(current, approved), "handoff")
    supervisor = approved["supervisor"]
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
    for binding in (pin, approved["authority"], approved["attempt"], approved["admission"]):
        env.check_binding(binding)
    handoff.check_launch_window(approved["began_ns"], approved["until_ns"])


class _CombinedRecordUiTargetRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        mechanisms._need(type(self) is _CombinedRecordUiTargetRuntime, "owner_type")
        self._handoff_pin, self._handoff = handoff.verify_boot_handoff(
            request["admission"], request["validated_admission"])
        _live_boot(self._handoff_pin, self._handoff, request["owner"])
        super().__init__(request, request_binding, root)

    def start_server(self):
        _live_boot(self._handoff_pin, self._handoff, self.request["owner"])
        super().start_server()

    def guard(self):
        super().guard()
        window = handoff.check_launch_window if self.guest_child is None else handoff.check_window
        window(self._handoff["began_ns"], self._handoff["until_ns"])

    def _retain_guest(self):
        _live_boot(self._handoff_pin, self._handoff, self.request["owner"])
        guest = self.admission["guest"]
        env.storage_transition(storage.record_state, Path(guest["root"]), "retained",
                               proposal_sha256=guest["proposal"]["sha256"],
                               expected_prepare_sha256=self.proposal["prepare_proposal"]["sha256"])
        _live_boot(self._handoff_pin, self._handoff, self.request["owner"])

    @property
    def _contract(self):
        return contract

    @property
    def _verification(self):
        return REPLAY


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if type(args) is not list or (args != ["_worker"] and not (
        len(args) == 4 and args[:3] == ["--admission", str(handoff.ADMISSION), "--admission-sha256"]
    )):
        return 1

    def check_admission(admission):
        pin, current = handoff.read(handoff.ADMISSION)
        env.require(pin["sha256"] == args[3] and contract._same(current, admission), "admission")
        env.require(not os.path.lexists(handoff.OWNED_ROOT), "already_used")
        _live_boot(*handoff.verify_boot_handoff(pin, admission))

    return mechanisms._main_profile(args, _contract=contract, _verification=REPLAY,
                                    _runtime_type=_CombinedRecordUiTargetRuntime,
                                    _admission_check=check_admission)


if __name__ == "__main__":
    raise SystemExit(main())
