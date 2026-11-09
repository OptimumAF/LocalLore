"""Bind archive operations to the shared bounded binary client and exact lease.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_archive_roundtrip_owner as owner


class OwnedArchiveRoundtripSdkCapture(wire._OwnedTargetSdkCapture):
    _contract = contract
    _verification = owner.VERIFIER
    _expected_lease_class = owner.LiveOwnedArchiveRoundtripTarget

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedArchiveRoundtripSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    def _execute(self, argv, source_binding, label, seconds, cap, full_budget):
        if type(cap) is not int or not 0 < cap <= contract.MAX_BYTES:
            self._poison()
            raise wire.ClientRefused("capture")
        return super()._execute(argv, source_binding, label, seconds, cap, full_budget)
