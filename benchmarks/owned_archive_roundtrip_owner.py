"""Archive transfer adapter for the existing guarded owner and ledger.

Only the inherited worker barrier is available. An operator parent entry point
requires the complete bidirectional controller and a reviewed admission.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import android_process_verification_v4 as replay
from benchmarks import archive_roundtrip_build as build
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_target_owner as shared

class _ArchiveReplay(replay._Verifier):
    def verify_guest_inputs(self, pin, admission, admission_binding):
        build.verify_current(contract.validate_admission(admission))
        return super().verify_guest_inputs(pin, admission, admission_binding)


VERIFIER = _ArchiveReplay(contract)


class _ArchiveRuntime(shared._TargetRuntimeCore):
    _contract = contract
    _verification = VERIFIER

    def __init__(self, request, request_binding, root):
        shared._need(type(self) is _ArchiveRuntime, "owner_type")
        build.verify_current(contract.validate_admission(request["validated_admission"]))
        super().__init__(request, request_binding, root)


class LiveOwnedArchiveRoundtripTarget(shared._LiveOwnedTarget):
    _contract = contract
    _verification = VERIFIER

    def __init__(self, admission_binding, running_binding):
        shared._need(type(self) is LiveOwnedArchiveRoundtripTarget, "owner_type")
        admission = contract.validate_admission(shared._read_json(admission_binding, _contract=contract))
        build.verify_current(admission)
        super().__init__(admission_binding, running_binding)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args != ["_worker"]:
        return 1
    return shared._main_profile(args, _contract=contract, _verification=VERIFIER,
                                _runtime_type=_ArchiveRuntime)


if __name__ == "__main__":
    raise SystemExit(main())
