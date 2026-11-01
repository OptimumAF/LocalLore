"""Fixed live-death owner profile over the unchanged finite owner mechanisms.

No import performs native, credential, process, socket or device operations.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from benchmarks import owned_target_owner as mechanisms
from benchmarks import owned_live_death_contract as contract
from benchmarks import android_process_verification_v6 as verification

OwnerRefused = mechanisms.OwnerRefused


class LiveOwnedLiveDeathTarget(mechanisms._LiveOwnedTarget):
    """Only this concrete class admits the fixed live-process witness profile."""

    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedLiveDeathTarget, "owner_type")
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedLiveDeathTarget, "owner_type")
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedLiveDeathTarget, "owner_type")
        return verification


class _LiveDeathTargetRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        mechanisms._need(type(self) is _LiveDeathTargetRuntime, "owner_type")
        super().__init__(request, request_binding, root)

    @property
    def _contract(self):
        mechanisms._need(type(self) is _LiveDeathTargetRuntime, "owner_type")
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is _LiveDeathTargetRuntime, "owner_type")
        return verification


def main(argv=None):
    return mechanisms._main_profile(argv, _contract=contract, _verification=verification,
                                    _runtime_type=_LiveDeathTargetRuntime)


if __name__ == "__main__":
    raise SystemExit(main())
