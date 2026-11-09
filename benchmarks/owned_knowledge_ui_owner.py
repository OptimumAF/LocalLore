"""Concrete SDK16 owner over unchanged finite and storage mechanisms.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from benchmarks import owned_target_owner as mechanisms
from benchmarks import owned_knowledge_ui_contract as contract
from benchmarks import android_process_knowledge_ui_verification as verification

OwnerRefused = mechanisms.OwnerRefused


def _verify_build(admission):
    # Fixed lazy dependency: admission cannot select a root or implementation.
    from benchmarks.knowledge_ui_profile_build import verify_current
    return verify_current(admission)


class LiveOwnedKnowledgeUiTarget(mechanisms._LiveOwnedTarget):
    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedKnowledgeUiTarget, 'owner_type')
        admission = contract.validate_admission(mechanisms._read_json(admission_binding, _contract=contract))
        _verify_build(admission)
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedKnowledgeUiTarget, 'owner_type')
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedKnowledgeUiTarget, 'owner_type')
        return verification


class _KnowledgeUiTargetRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        mechanisms._need(type(self) is _KnowledgeUiTargetRuntime, 'owner_type')
        _verify_build(contract.validate_admission(request['validated_admission']))
        super().__init__(request, request_binding, root)

    @property
    def _contract(self):
        mechanisms._need(type(self) is _KnowledgeUiTargetRuntime, 'owner_type')
        return contract

    @property
    def _verification(self):
        mechanisms._need(type(self) is _KnowledgeUiTargetRuntime, 'owner_type')
        return verification


def main(argv=None):
    return mechanisms._main_profile(argv, _contract=contract, _verification=verification,
        _runtime_type=_KnowledgeUiTargetRuntime, _admission_check=_verify_build)


if __name__ == '__main__':
    raise SystemExit(main())
