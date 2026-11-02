"""SDK16 admission adapter over the unchanged B88 data-only build attestor.

Importing performs no I/O. No manifest conversion, publication, target operation
or caller-selected implementation is added by this profile adapter.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import owned_knowledge_ui_contract as contract
from benchmarks import knowledge_ui_build as build

BuildRefused = build.BuildRefused


def verify_current(admission):
    """Validate exact current SDK16 sources and return B88's manifest unchanged."""
    value = contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    manifest = build.verify_frozen_product(value['artifacts'])
    contract._need(type(manifest) is dict and
        contract._same(manifest.get('instrumentations'),
                       [list(row) for row in contract.INSTRUMENTATIONS]), 'build')
    contract.revalidate_inputs(value)
    return manifest
