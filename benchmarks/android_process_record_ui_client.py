"""Fixed SDK7 record UI profile over the shared bounded binary wire.

No caller-supplied contract, verifier, lease type or legacy fallback.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_record_ui_contract as contract
from benchmarks import android_process_record_ui_verification as verification

ClientRefused = wire.ClientRefused


def _lease_class():
    from benchmarks.owned_record_ui_owner import LiveOwnedRecordUiTarget
    return LiveOwnedRecordUiTarget


class OwnedRecordUiSdkCapture(wire._OwnedTargetSdkCapture):
    """Only this concrete client chooses the fixed model-free UI profile."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedRecordUiSdkCapture, 'client_type')
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedRecordUiSdkCapture, 'client_type')
        return contract

    @property
    def _verification(self):
        wire._need(type(self) is OwnedRecordUiSdkCapture, 'client_type')
        return verification

    @property
    def _expected_lease_class(self):
        wire._need(type(self) is OwnedRecordUiSdkCapture, 'client_type')
        return _lease_class()
