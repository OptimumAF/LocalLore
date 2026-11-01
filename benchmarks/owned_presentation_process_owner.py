"""Fixed presentation process owner over shared finite ownership and storage guards.

Import performs no native, credential, process, socket or device operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from benchmarks import owned_target_owner as mechanisms
from benchmarks import owned_presentation_process_contract as contract
from benchmarks import android_process_presentation_process_verification as verification
from benchmarks import presentation_process_build as build

OwnerRefused = mechanisms.OwnerRefused


class LiveOwnedPresentationProcessTarget(mechanisms._LiveOwnedTarget):
    """An exact concrete observer for the fixed presentation process target."""

    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedPresentationProcessTarget, 'owner_type')
        admission = contract.validate_admission(mechanisms._read_json(
            admission_binding, _contract=contract))
        build.verify_current(admission)
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedPresentationProcessTarget, 'owner_type')
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedPresentationProcessTarget, 'owner_type')
        return verification


class _PresentationProcessTargetRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        mechanisms._need(type(self) is _PresentationProcessTargetRuntime, 'owner_type')
        build.verify_current(contract.validate_admission(request['validated_admission']))
        super().__init__(request, request_binding, root)

    @property
    def _contract(self):
        mechanisms._need(type(self) is _PresentationProcessTargetRuntime, 'owner_type')
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is _PresentationProcessTargetRuntime, 'owner_type')
        return verification


def main(argv=None):
    return mechanisms._main_profile(
        argv, _contract=contract, _verification=verification,
        _runtime_type=_PresentationProcessTargetRuntime, _admission_check=build.verify_current)


if __name__ == '__main__':
    raise SystemExit(main())
