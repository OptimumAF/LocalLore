"""Fixed restart-target owner and observer using the shared finite mechanisms.

Neither JSON nor public constructors select a module, verifier or runtime type.
Import performs no native/credential/process/socket/device operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from benchmarks import owned_target_owner as mechanisms
from benchmarks import owned_restart_contract as contract
from benchmarks import android_process_verification_v5 as verification

OwnerRefused = mechanisms.OwnerRefused


class LiveOwnedRestartTarget(mechanisms._LiveOwnedTarget):
    """Only this concrete class admits the fixed restart authority profile."""

    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedRestartTarget, "owner_type")
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedRestartTarget, "owner_type")
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedRestartTarget, "owner_type")
        return verification


class _RestartTargetRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        mechanisms._need(type(self) is _RestartTargetRuntime, "owner_type")
        super().__init__(request, request_binding, root)

    @property
    def _contract(self):
        mechanisms._need(type(self) is _RestartTargetRuntime, "owner_type")
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is _RestartTargetRuntime, "owner_type")
        return verification


def main(argv=None):
    return mechanisms._main_profile(argv, _contract=contract, _verification=verification,
                                    _runtime_type=_RestartTargetRuntime)


if __name__ == "__main__":
    raise SystemExit(main())
