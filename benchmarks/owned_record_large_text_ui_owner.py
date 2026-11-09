"""Concrete owner for the Story Record large-text profile.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))

from benchmarks import android_process_record_large_text_ui_verification as verification
from benchmarks import owned_record_large_text_ui_contract as contract
from benchmarks import owned_target_owner as mechanisms


class LiveOwnedRecordLargeTextUiTarget(mechanisms._LiveOwnedTarget):
    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedRecordLargeTextUiTarget, 'owner_type')
        contract.verify_current(mechanisms._read_json(admission_binding, _contract=contract))
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        return contract

    @property
    def _verification(self):
        return verification


class _RecordLargeTextUiTargetRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        mechanisms._need(type(self) is _RecordLargeTextUiTargetRuntime, 'owner_type')
        contract.verify_current(request['validated_admission'])
        super().__init__(request, request_binding, root)

    @property
    def _contract(self):
        return contract

    @property
    def _verification(self):
        return verification


def main(argv=None):
    return mechanisms._main_profile(
        argv, _contract=contract, _verification=verification,
        _runtime_type=_RecordLargeTextUiTargetRuntime, _admission_check=contract.verify_current,
    )


if __name__ == '__main__':
    raise SystemExit(main())
