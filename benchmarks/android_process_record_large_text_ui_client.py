"""Concrete Story Record large-text client over the existing finite wire.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_record_large_text_ui_verification as verification
from benchmarks import owned_record_large_text_ui_contract as contract

ClientRefused = wire.ClientRefused


class OwnedRecordLargeTextUiSdkCapture(wire._OwnedTargetSdkCapture):
    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedRecordLargeTextUiSdkCapture, 'client_type')
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        return contract

    @property
    def _verification(self):
        return verification

    @property
    def _expected_lease_class(self):
        from benchmarks.owned_record_large_text_ui_owner import LiveOwnedRecordLargeTextUiTarget

        return LiveOwnedRecordLargeTextUiTarget
