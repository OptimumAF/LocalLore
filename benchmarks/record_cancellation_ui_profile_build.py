"""Fixed SDK18 adapter over B111 attestation; no import-time observation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
import sys

from benchmarks import owned_record_cancellation_ui_contract as contract
from benchmarks import record_cancellation_ui_build as build

BuildRefused = build.BuildRefused
CHECKERS = (
    ('scripts/audit_physical_model_apk.py', 23249,
     '9a9f06d299e5182ffd026c3fe5dbce5b13a6edb11d2be32daf81a01da02eae9a'),
    ('scripts/audit_apk.py', 42803,
     '1c54e10dc9b8b24baa7ced0baf3ed8efdbf679e1ab9a6d0adf9639ab358562ad'),
)
EXPECTED_FACTS = dict(recorded_jvm_cases=425, recorded_jvm_suites=50,
    jvm_failures=0, jvm_errors=0, jvm_skips=0, compiled_ui_methods=5,
    selected_runtime_methods=5, android_runtime_executed=False,
    model_material=False, run_authority=False, feature_acceptance=False,
    native_runtime_executed=False, native_compilation_repeated=False,
    remote_rechecked=False, tool_binary_revalidation=False,
    intermediate_cohorts_additive=False,
    source_encoding='Exact recorded raw Git snapshot bytes; no newline normalization')
UNITS = (381, 536, 317, 518, 529)
MANIFEST_KEYS = frozenset(('version', 'scope', 'mode', 'product', 'artifacts',
    'current_native_bindings', 'evidence', 'facts', 'instrumentations'))


def revalidate_checker():
    """Recheck decoder/base bytes and cached origins; never execute a checker."""
    from benchmarks import archive_ui_build as files
    root = Path(__file__).parents[1]
    try:
        contract._need(root.drive.upper() == 'D:' and root.resolve(strict=True) == root, 'source')
        for relative, size, sha in CHECKERS:
            files._bound(dict(path=str(root / relative), bytes=size, sha256=sha))
        origins = {
            'benchmarks.record_cancellation_ui_build': root / 'benchmarks/record_cancellation_ui_build.py',
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
        contract._need(Path(build.shared.__file__) == root / 'benchmarks/diagnostic_ui_build.py', 'source')
        decoder = sys.modules.get('scripts.audit_physical_model_apk')
        if decoder is not None:
            contract._need(Path(decoder.base.__file__) == root / 'scripts/audit_apk.py', 'source')
    except contract.TargetRefused:
        raise
    except Exception:
        raise contract.TargetRefused('source') from None


def project_manifest(raw):
    """Return only a detached controller view of the fixed B111 facts."""
    try:
        contract._obj(raw, MANIFEST_KEYS, 'build')
        contract._need(type(raw['version']) is int and raw['version'] == 1 and
            raw['scope'] == 'record-cancellation-ui-build-v1' and
            raw['mode'] == 'fixed-b110-byte-attestation-v1', 'build')
        product = raw['product']
        contract._need(type(product) is dict and
            product.get('head') == '7e29fb724ed781e953f321385f66a5f8982ad0f1' and
            product.get('tree') == '39adcae73aae5448f9a3052d5125f1d4cc0d0033', 'build')
        contract._need(type(raw['evidence']) is dict and type(raw['current_native_bindings']) is list, 'build')
        apks = raw['artifacts']
        contract._obj(apks, ('product_apk', 'test_apk'), 'build')
        for pin in apks.values():
            contract.binding(pin, max_bytes=64 * 1024 ** 2)
        expected = [list(row) for row in contract.INSTRUMENTATIONS]
        contract._need(contract._same(raw['instrumentations'], expected), 'build')
        facts = raw['facts']
        contract._obj(facts, set(EXPECTED_FACTS) | {'selected_methods', 'package_audit'}, 'build')
        contract._need(contract._same({k: facts[k] for k in EXPECTED_FACTS}, EXPECTED_FACTS), 'build')
        selected = facts['selected_methods']
        contract._need(type(selected) is list and len(selected) == 5, 'build')
        for row, triple, units in zip(selected, contract.INSTRUMENTATIONS, UNITS):
            contract._obj(row, ('selector', 'class_name', 'method', 'instruction_units'), 'build')
            contract._need(contract._same([row['selector'], row['class_name'], row['method']], list(triple)) and
                type(row['instruction_units']) is int and row['instruction_units'] == units, 'build')
        short = lambda pin: {k: pin[k] for k in ('bytes', 'sha256')}
        audit = dict(status='passed', package=contract.APP, test_package=contract.TEST,
            certificate_sha256=contract.CERTIFICATE_SHA256,
            app=short(apks['product_apk']), test=short(apks['test_apk']),
            test_permissions=['android.permission.REORDER_TASKS'])
        contract._need(contract._same(facts['package_audit'], audit), 'build')
        return copy.deepcopy(dict(roster=expected, apks={
            role: dict(binding=apks[role], package=package,
                       certificate_sha256=contract.CERTIFICATE_SHA256)
            for role, package in zip(('product_apk', 'test_apk'), (contract.APP, contract.TEST))}))
    except contract.TargetRefused:
        raise
    except Exception:
        raise contract.TargetRefused('build') from None


def verify_current(admission):
    """Revalidate exact SDK18 input sources around the fixed B111 verifier."""
    value = contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    try:
        manifest = build.verify_frozen_product(value['artifacts'])
        project_manifest(manifest)
        contract._need(contract._same(manifest['artifacts'],
            {role: value['artifacts'][role] for role in ('product_apk', 'test_apk')}), 'build')
    except contract.TargetRefused:
        raise
    except Exception:
        raise contract.TargetRefused('build') from None
    contract.revalidate_inputs(value)
    return manifest
