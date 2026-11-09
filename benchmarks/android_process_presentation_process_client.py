"""Fixed SDK9 presentation process profile over the shared bounded binary wire.

No caller-supplied contract, verifier, lease type or legacy fallback.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_presentation_process_contract as contract
from benchmarks import android_process_presentation_process_verification as verification

ClientRefused = wire.ClientRefused


def _lease_class():
    from benchmarks.owned_presentation_process_owner import LiveOwnedPresentationProcessTarget
    return LiveOwnedPresentationProcessTarget


class OwnedPresentationProcessSdkCapture(wire._OwnedTargetSdkCapture):
    """Only this concrete client chooses the fixed model-free UI profile."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedPresentationProcessSdkCapture, 'client_type')
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedPresentationProcessSdkCapture, 'client_type')
        return contract

    @property
    def _verification(self):
        wire._need(type(self) is OwnedPresentationProcessSdkCapture, 'client_type')
        return verification

    @property
    def _expected_lease_class(self):
        wire._need(type(self) is OwnedPresentationProcessSdkCapture, 'client_type')
        return _lease_class()
