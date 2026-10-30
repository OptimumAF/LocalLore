"""Fixed SDK6 profile over the shared bounded binary wire mechanism.

No caller selects a contract, verifier or lease implementation. Import performs
no native, process, socket or device operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_live_death_contract as contract
from benchmarks import android_process_verification_v6 as verification

ClientRefused = wire.ClientRefused


def _lease_class():
    from benchmarks.owned_live_death_owner import LiveOwnedLiveDeathTarget
    return LiveOwnedLiveDeathTarget


class OwnedLiveDeathSdkCapture(wire._OwnedTargetSdkCapture):
    """The concrete client selects only its source-bound SDK6 profile."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedLiveDeathSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedLiveDeathSdkCapture, "client_type")
        return contract

    @property
    def _verification(self):
        wire._need(type(self) is OwnedLiveDeathSdkCapture, "client_type")
        return verification

    @property
    def _expected_lease_class(self):
        wire._need(type(self) is OwnedLiveDeathSdkCapture, "client_type")
        return _lease_class()
