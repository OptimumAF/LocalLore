"""Fixed SDK5 restart profile over the shared bounded binary wire mechanism.

No caller-supplied contract, verifier, lease implementation or legacy fallback.
Import performs no native observation or device operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_restart_contract as contract
from benchmarks import android_process_verification_v5 as verification

ClientRefused = wire.ClientRefused


def _lease_class():
    from benchmarks.owned_restart_owner import LiveOwnedRestartTarget
    return LiveOwnedRestartTarget


class OwnedRestartSdkCapture(wire._OwnedTargetSdkCapture):
    """The concrete restart client selects only its fixed source-bound profile."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedRestartSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedRestartSdkCapture, "client_type")
        return contract

    @property
    def _verification(self):
        wire._need(type(self) is OwnedRestartSdkCapture, "client_type")
        return verification

    @property
    def _expected_lease_class(self):
        wire._need(type(self) is OwnedRestartSdkCapture, "client_type")
        return _lease_class()
