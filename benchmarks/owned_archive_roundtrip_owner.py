"""Archive transfer adapter for the existing guarded owner and ledger.

Parent and worker require the exact spent operator handoff and job ancestry.
The operator supervisor is a separate entry point.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import android_process_verification_v4 as replay
from benchmarks import archive_roundtrip_build as build
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_target_owner as shared
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

class _ArchiveReplay(replay._Verifier):
    def verify_guest_inputs(self, pin, admission, admission_binding):
        build.verify_current(contract.validate_admission(admission))
        return super().verify_guest_inputs(pin, admission, admission_binding)


VERIFIER = _ArchiveReplay(contract)


class _ArchiveRuntime(shared._TargetRuntimeCore):
    _contract = contract
    _verification = VERIFIER

    def __init__(self, request, request_binding, root):
        from benchmarks import archive_roundtrip_handoff as handoff

        shared._need(type(self) is _ArchiveRuntime, "owner_type")
        self._launch = handoff.verify_boot(request["admission"], request["validated_admission"],
                                           parent=request["owner"])
        super().__init__(request, request_binding, root)

    def _launch_guard(self):
        from benchmarks import archive_roundtrip_handoff as handoff

        pin, record, _ = self._launch
        handoff.live(pin, record, parent=self.request["owner"])

    def start_server(self):
        self._launch_guard()
        env.check_binding(self._launch[2]["ledger"])
        super().start_server()

    def guard(self):
        from benchmarks import archive_roundtrip_handoff as handoff

        super().guard()
        if self.guest_child is None:
            self._launch_guard()
        else:
            handoff.check_window(self._launch[1])

    def _retain_guest(self):
        self._launch_guard()
        context = self._launch[2]
        guest = self.admission["guest"]
        shared._need(self.proposal["prepare_proposal"]["sha256"] == context["prepare_sha256"], "prepared")
        env.storage_transition(storage.record_state, Path(guest["root"]), "retained",
                               proposal_sha256=guest["proposal"]["sha256"],
                               expected_prepare_sha256=context["prepare_sha256"],
                               expected_ledger=context["ledger"])
        self._launch_guard()


class LiveOwnedArchiveRoundtripTarget(shared._LiveOwnedTarget):
    _contract = contract
    _verification = VERIFIER

    def __init__(self, admission_binding, running_binding):
        shared._need(type(self) is LiveOwnedArchiveRoundtripTarget, "owner_type")
        admission = contract.validate_admission(shared._read_json(admission_binding, _contract=contract))
        build.verify_current(admission)
        super().__init__(admission_binding, running_binding)


def main(argv=None):
    from benchmarks import archive_roundtrip_handoff as handoff

    args = sys.argv[1:] if argv is None else argv
    if type(args) is not list or re.fullmatch("[0-9a-f]{64}", os.environ.get(handoff.HANDOFF_ENV, "")) is None:
        return 1
    expected = ["--admission", str(handoff.admission.ADMISSION), "--admission-sha256"]
    if args != ["_worker"] and not (
        len(args) == 4 and args[:3] == expected and type(args[3]) is str
        and re.fullmatch("[0-9a-f]{64}", args[3]) is not None
    ):
        return 1

    def check_admission(admitted):
        pin, value = handoff.lifecycle._read(handoff.admission.ADMISSION)
        shared._need(pin["sha256"] == args[3] and contract._same(value, admitted), "admission")
        handoff.verify_boot(pin, admitted)

    return shared._main_profile(args, _contract=contract, _verification=VERIFIER,
                                _runtime_type=_ArchiveRuntime, _admission_check=check_admission)


if __name__ == "__main__":
    raise SystemExit(main())
