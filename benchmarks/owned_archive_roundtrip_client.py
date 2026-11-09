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
    _return_permit = None

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedArchiveRoundtripSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    def _execute(self, argv, source_binding, label, seconds, cap, full_budget):
        if type(cap) is not int or not 0 < cap <= contract.MAX_BYTES:
            self._poison()
            raise wire.ClientRefused("capture")
        if type(argv) is list and argv[:1] in (["am"], ["run-as"]):
            kind = contract.return_kind(argv, self._admission)
            if kind is not None:
                permit = self._return_permit
                self._return_permit = None
                operation = (argv, source_binding, label, seconds, cap, full_budget)
                if (type(permit) is not tuple or len(permit) != 2 or
                        not contract._same(permit[1], operation)):
                    self._poison()
                    raise wire.ClientRefused("return_authority")
                # Import here to keep the profile's source-only worker entry acyclic.
                from benchmarks import archive_roundtrip_return as returning
                try:
                    returning.authorize_dispatch(self, permit[0], kind, operation)
                except BaseException:
                    self._poison()
                    raise
        return super()._execute(argv, source_binding, label, seconds, cap, full_budget)
