"""Concrete SDK17 capture; no caller-selected implementations or lease types.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_diagnostic_ui_contract as contract
from benchmarks import android_process_diagnostic_ui_verification as verification

ClientRefused = wire.ClientRefused


def _lease_class():
    from benchmarks.owned_diagnostic_ui_owner import LiveOwnedDiagnosticUiTarget
    return LiveOwnedDiagnosticUiTarget


class OwnedDiagnosticUiSdkCapture(wire._OwnedTargetSdkCapture):
    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedDiagnosticUiSdkCapture, 'client_type')
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedDiagnosticUiSdkCapture, 'client_type')
        return contract

    @property
    def _verification(self):
        wire._need(type(self) is OwnedDiagnosticUiSdkCapture, 'client_type')
        return verification

    @property
    def _expected_lease_class(self):
        wire._need(type(self) is OwnedDiagnosticUiSdkCapture, 'client_type')
        return _lease_class()
