"""Concrete current-chat UI owner over unchanged finite/storage mechanisms.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from benchmarks import owned_target_owner as mechanisms
from benchmarks import owned_chat_ui_contract as contract
from benchmarks import android_process_chat_ui_verification as verification

OwnerRefused = mechanisms.OwnerRefused


def _verify_build(admission):
    # Fixed lazy import: no implementation, root or callback comes from admission.
    from benchmarks.chat_ui_build import verify_current
    return verify_current(admission)


class LiveOwnedChatUiTarget(mechanisms._LiveOwnedTarget):
    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedChatUiTarget, 'owner_type')
        admission = contract.validate_admission(mechanisms._read_json(admission_binding, _contract=contract))
        _verify_build(admission)
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedChatUiTarget, 'owner_type')
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedChatUiTarget, 'owner_type')
        return verification


class _ChatUiTargetRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        mechanisms._need(type(self) is _ChatUiTargetRuntime, 'owner_type')
        _verify_build(contract.validate_admission(request['validated_admission']))
        super().__init__(request, request_binding, root)

    @property
    def _contract(self):
        mechanisms._need(type(self) is _ChatUiTargetRuntime, 'owner_type')
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is _ChatUiTargetRuntime, 'owner_type')
        return verification


def main(argv=None):
    return mechanisms._main_profile(argv, _contract=contract, _verification=verification,
        _runtime_type=_ChatUiTargetRuntime, _admission_check=_verify_build)


if __name__ == '__main__':
    raise SystemExit(main())
