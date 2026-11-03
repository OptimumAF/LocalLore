"""Tiny SDK17 metadata/wire fixtures; no tool or target is ever dispatched.

The accepted in-tree archive controller fixture supplies only its synthetic
wire/native observation ports. B104 artifact verification is explicitly fake
here and is tested separately through the actual profile wrapper.
"""
import contextlib
import copy
import json
import os
from pathlib import Path, PureWindowsPath
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from benchmarks import owned_diagnostic_ui_contract as contract
from benchmarks import owned_target_contract as core
from benchmarks import diagnostic_ui_profile_build as build
from benchmarks import diagnostic_ui_controller as controller
from benchmarks import owned_diagnostic_ui_owner as owner
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests import test_archive_ui_controller_fixtures as accepted

PROTOCOL = 'owned-emulator-diagnostic-ui-v1'
SDK_PROTOCOL = 'sdk-diagnostic-ui-v1'
PROOF_PROTOCOL = 'diagnostic-ui-socket-proof-v1'
SESSION_FILE = 'sdk-session-v17.json'
APP = 'org.locallore.app'
TEST = APP + '.test'
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-03-diagnostic-ui-v1/avd-v1')
CERTIFICATE = '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564'
INSTRUMENTATIONS = (
    ('diagnostic_1', 'org.locallore.app.DiagnosticsIntegrationTest', 'actualNativeOutcomesAreSanitizedAndClearingCannotChangeCanon'),
    ('diagnostic_2', 'org.locallore.app.DiagnosticsIntegrationTest', 'reviewedSnapshotAndPendingConsentSurviveActivityRecreation'),
    ('diagnostic_3', 'org.locallore.app.DiagnosticsIntegrationTest', 'revokingPickerAndLateResultDoesNotOpenDestination'),
    ('diagnostic_4', 'org.locallore.app.DiagnosticsIntegrationTest', 'cancelAndMalformedGenerationProduceOnlyFixedDiagnosticCategories'),
    ('diagnostic_5', 'org.locallore.app.DiagnosticsIntegrationTest', 'retiredReviewCannotClearOrCloseTheReplacementNativePreview'),
    ('diagnostic_6', 'org.locallore.app.DiagnosticsIntegrationTest', 'staleScopedExportCannotBorrowTheCurrentReviewAcrossRecreation'),
)


def encoded(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()


def pin(path):
    return env.binding(Path(path))


def admission():
    value = legacy.admission()
    value['protocol'] = PROTOCOL
    value['guest']['root'] = str(GUEST_ROOT)
    value['artifacts'] = {role: value['artifacts'][role] for role in ('build', 'product_apk', 'test_apk')}
    value['sources'] = sorted([legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
                               for name in contract.SOURCE_NAMES], key=lambda row: row['path'])
    sources = {PureWindowsPath(row['path']).name: row for row in value['sources']}
    value['server']['sources'] = [copy.deepcopy(sources[PureWindowsPath(row['path']).name])
                                  for row in value['server']['sources']]
    return value


def running(value=None):
    result = legacy.running(admission() if value is None else value)
    result['protocol'] = PROTOCOL
    return result


def session(value=None):
    value = admission() if value is None else value
    result = legacy.session(value)
    result.update(protocol=SDK_PROTOCOL, descriptor=running(value))
    return result


def proof(value, *, after=False):
    result = legacy.proof(value, after=after)
    result.update(protocol=PROOF_PROTOCOL,
                  session=legacy.pin(PureWindowsPath(value['root']) / SESSION_FILE))
    return result


def query_bundle(value):
    result = legacy.query_bundle(value)
    result['protocol'] = PROOF_PROTOCOL
    return result


def instrument(triple):
    return ['am', 'instrument', '-w', '-r', '-e', 'class', triple[1] + '#' + triple[2],
            TEST + '/androidx.test.runner.AndroidJUnitRunner']


def raw_manifest(artifacts=None):
    """Raw B104 shape, not the legacy controller roster/apks projection."""
    root = Path(__file__).resolve().parents[2]
    baseline = json.loads((root / 'benchmarks/diagnostic_ui_build_baseline.json').read_bytes())
    if artifacts is None:
        artifacts = admission()['artifacts']
    return dict(version=1, scope='diagnostic-ui-build-v1', mode='fixed-b103-raw-git-attestation-v1',
        source_encoding=baseline['source_encoding'], product=copy.deepcopy(baseline['product']),
        counts=copy.deepcopy(baseline['counts']), records=copy.deepcopy(baseline['records']),
        apks={role: copy.deepcopy(artifacts[role]) for role in ('product_apk', 'test_apk')},
        jvm_reports=copy.deepcopy(baseline['jvm_reports']),
        selected_methods=[dict(selector=kind, **{'class': klass}, method=method, instruction_units=units)
            for (kind, klass, method), units in zip(INSTRUMENTATIONS, (296, 185, 78, 157, 304, 407))],
        facts=dict(source_tree_recomputed=True, current_file_revalidation=True,
            recorded_jvm_cases=427, recorded_jvm_suites=49, android_runtime_executed=False,
            model_material=False, feature_acceptance=False, run_authority=False,
            native_compilation_repeated=False, remote_rechecked=False, tool_binary_revalidation=False))


class TinyBuild:
    """Retained metadata only. Never copies/rebuilds APKs or historic captures."""
    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix='sdk17-diagnostic-metadata-'))
        if os.name == 'nt':
            assert self.base.drive.upper() == 'D:'
        self.root = self.base / 'product'
        self.root.mkdir()
        self.apks = {}
        for role in ('product_apk', 'test_apk'):
            path = self.base / (role + '.apk')
            self.write(path, b'NOT_AN_APK_ONLY_SYNTHETIC_METADATA_' + role.encode())
            self.apks[role] = path
        self.manifest = raw_manifest({role: pin(path) for role, path in self.apks.items()})
        self.manifest_path = self.base / 'build-v1.json'
        self.write(self.manifest_path, encoded(self.manifest))

    def write(self, path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw.encode() if isinstance(raw, str) else raw)

    def admission(self):
        return dict(artifacts=dict(build=pin(self.manifest_path),
            **{role: pin(path) for role, path in self.apks.items()}))

    @contextlib.contextmanager
    def inputs(self, module):
        # Deliberate artifact-only port. All source/session/proof/client/claim,
        # runtime byte bindings and production replay validators remain active.
        with patch.object(module, 'verify_current', return_value=self.manifest), \
             patch.object(controller, 'verify_current', return_value=self.manifest):
            yield


class ControllerGraph(accepted.ControllerGraph):
    @contextlib.contextmanager
    def modules(self):
        with contextlib.ExitStack() as stack:
            for name, value in (('build', build), ('controller', controller), ('contract', contract),
                    ('owner', owner), ('f', sys.modules[__name__]),
                    ('builds', SimpleNamespace(BuildGraph=TinyBuild, pin=pin, encoded=encoded))):
                stack.enter_context(patch.object(accepted, name, value))
            yield

    def __init__(self, **kwargs):
        with self.modules():
            super().__init__(**kwargs)

    def prove(self, live, path, value, context, sock, anchor, after=False):
        result = proof(value, after=after)
        result.update(context=copy.deepcopy(context), anchor=copy.deepcopy(anchor),
                      session=pin(Path(value['root']) / SESSION_FILE))
        queries = path.with_name(path.stem + '-queries-v1.json')
        env.create_json(queries, query_bundle(value))
        result['queries'] = pin(queries)
        env.create_json(path, result)
        self.proofs.append((context['index'], context['phase']))
        return pin(path)

    @contextlib.contextmanager
    def inputs(self):
        with self.modules(), super().inputs():
            yield

    def response(self, argv):
        if argv[:4] == ['cmd', 'package', 'list', 'packages']:
            # Android15 runListPackages uses packageName.contains(filter).
            # Preserve stable UIDs and record this observed command exactly once.
            self.calls.append(list(argv))
            query = argv[-1]
            raw = ''.join('package:' + package + ' uid:' + str(10001 + index) + '\n'
                for index, package in enumerate((APP, TEST))
                if package in self.installed and query in package)
            return raw.encode(), b''
        return super().response(argv)

    def run(self):
        return controller.run(self.admission, self.running)

    def verify(self, caller=None):
        return controller.verify_controller_result(pin(self.output / 'controller-result-v1.json'),
            self.admission, self.running, self.caller if caller is None else caller)

    def replace(self, path, value):
        self.g.write(path, encoded(value))
        return pin(path)
