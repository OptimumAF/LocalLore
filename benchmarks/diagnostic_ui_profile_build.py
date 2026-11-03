"""Fixed SDK17 adapter over B104 attestation; no import-time file observation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys

from benchmarks import owned_diagnostic_ui_contract as contract
from benchmarks import diagnostic_ui_build as build

BuildRefused = build.BuildRefused
CHECKERS = (
    ('scripts/audit_physical_model_apk.py', 23249,
     '9a9f06d299e5182ffd026c3fe5dbce5b13a6edb11d2be32daf81a01da02eae9a'),
    ('scripts/audit_apk.py', 42803,
     '1c54e10dc9b8b24baa7ced0baf3ed8efdbf679e1ab9a6d0adf9639ab358562ad'),
)
EXPECTED_FACTS = {
    'source_tree_recomputed': True, 'current_file_revalidation': True,
    'recorded_jvm_cases': 427, 'recorded_jvm_suites': 49,
    'android_runtime_executed': False, 'model_material': False,
    'feature_acceptance': False, 'run_authority': False,
    'native_compilation_repeated': False, 'remote_rechecked': False,
    'tool_binary_revalidation': False,
}


def revalidate_checker():
    """Recheck fixed source and cached decoder/base origins without executing it."""
    from benchmarks import archive_ui_build as files
    root = Path(__file__).parents[1]
    try:
        contract._need(root.drive.upper() == 'D:' and root.resolve(strict=True) == root, 'source')
        for relative, size, sha in CHECKERS:
            files._bound(dict(path=str(root / relative), bytes=size, sha256=sha))
        origins = {
            'benchmarks.diagnostic_ui_build': root / 'benchmarks/diagnostic_ui_build.py',
            'benchmarks.archive_ui_build': root / 'benchmarks/archive_ui_build.py',
            'scripts.audit_physical_model_apk': root / 'scripts/audit_physical_model_apk.py',
            'scripts.audit_apk': root / 'scripts/audit_apk.py',
            'audit_apk': root / 'scripts/audit_apk.py',
        }
        for name, path in origins.items():
            module = sys.modules.get(name)
            if module is not None:
                contract._need(Path(module.__file__) == path, 'source')
        decoder = sys.modules.get('scripts.audit_physical_model_apk')
        if decoder is not None:
            contract._need(Path(decoder.base.__file__) == root / 'scripts/audit_apk.py', 'source')
    except (ValueError, OSError, KeyError, TypeError, AttributeError):
        raise contract.TargetRefused('source') from None


def verify_current(admission):
    """Validate exact SDK17 sources and return the unchanged verified B104 object."""
    value = contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    manifest = build.verify_frozen_product(value['artifacts'])
    contract._need(type(manifest) is dict and manifest.get('scope') == 'diagnostic-ui-build-v1' and
        manifest.get('mode') == 'fixed-b103-raw-git-attestation-v1', 'build')
    selected = manifest.get('selected_methods')
    contract._need(type(selected) is list and len(selected) == 6, 'build')
    contract._need(all(type(row) is dict and set(row) ==
        {'selector', 'class', 'method', 'instruction_units'} for row in selected), 'build')
    contract._need(contract._same([[row['selector'], row['class'], row['method']] for row in selected],
                                 [list(row) for row in contract.INSTRUMENTATIONS]), 'build')
    contract._need(all(type(row['instruction_units']) is int and row['instruction_units'] > 0
                       for row in selected), 'build')
    contract._need(type(manifest.get('facts')) is dict and
        contract._same(manifest['facts'], EXPECTED_FACTS), 'build')
    contract._need(contract._same(manifest.get('apks'),
        {role: value['artifacts'][role] for role in ('product_apk', 'test_apk')}), 'build')
    contract.revalidate_inputs(value)
    return manifest
