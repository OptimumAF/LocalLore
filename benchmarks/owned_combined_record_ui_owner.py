"""Observe an already running combined Story Record target.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy

from benchmarks import android_process_verification_v4 as verification
from benchmarks import combined_record_ui_binding as artifact_policy
from benchmarks import owned_combined_record_ui_contract as contract
from benchmarks import owned_target_owner as mechanisms

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
