"""Fixed SDK21 capture for the combined Story Record target.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_combined_record_ui_contract as contract
from benchmarks.owned_combined_record_ui_owner import LiveOwnedCombinedRecordUiTarget, REPLAY


class OwnedCombinedRecordUiSdkCapture(wire._OwnedTargetSdkCapture):
    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedCombinedRecordUiSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedCombinedRecordUiSdkCapture, "client_type")
        return contract

    @property
    def _verification(self):
        wire._need(type(self) is OwnedCombinedRecordUiSdkCapture, "client_type")
        return REPLAY

    @property
    def _expected_lease_class(self):
        wire._need(type(self) is OwnedCombinedRecordUiSdkCapture, "client_type")
        return LiveOwnedCombinedRecordUiTarget
