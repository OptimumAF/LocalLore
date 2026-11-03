"""Tiny SDK18 metadata/wire fixtures; no tool or target is ever dispatched.

The accepted in-tree archive controller fixture supplies only its synthetic
wire/native observation ports. B111 artifact verification is explicitly fake
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
from unittest.mock import Mock, patch

from benchmarks import record_cancellation_ui_activation as activation
from benchmarks import owned_record_cancellation_ui_contract as contract
c = contract
from benchmarks import owned_target_contract as core
from benchmarks import record_cancellation_ui_profile_build as build
from benchmarks import record_cancellation_ui_controller as controller
from benchmarks import owned_record_cancellation_ui_owner as owner
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests import test_archive_ui_controller_fixtures as accepted

PROTOCOL = 'owned-emulator-record-cancellation-ui-v1'
SDK_PROTOCOL = 'sdk-record-cancellation-ui-v1'
PROOF_PROTOCOL = 'record-cancellation-ui-socket-proof-v1'
SESSION_FILE = 'sdk-session-v18.json'
APP = 'org.locallore.app'
TEST = APP + '.test'
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1/avd-v1')
CERTIFICATE = '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564'
UI_CLASS = 'org.locallore.app.StoryRecordCancellationScreenTest'
INSTRUMENTATIONS = (
    ('record_cancel_1', UI_CLASS, 'cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor'),
    ('record_cancel_2', UI_CLASS, 'cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens'),
    ('record_cancel_3', UI_CLASS, 'obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords'),
    ('record_cancel_4', UI_CLASS, 'oldDetailCancellationAfterBackCannotFinishTheReplacementDetail'),
    ('record_cancel_5', UI_CLASS, 'disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks'),
)
UNITS = (381, 536, 317, 518, 529)
FACTS = dict(recorded_jvm_cases=425, recorded_jvm_suites=50, jvm_failures=0,
    jvm_errors=0, jvm_skips=0, compiled_ui_methods=5, selected_runtime_methods=5,
    android_runtime_executed=False, model_material=False, run_authority=False,
    feature_acceptance=False, native_runtime_executed=False, native_compilation_repeated=False,
    remote_rechecked=False, tool_binary_revalidation=False, intermediate_cohorts_additive=False,
    source_encoding='Exact recorded raw Git snapshot bytes; no newline normalization')



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
    """Independent tiny B111 metadata port; no artifact is a qualified APK."""
    artifacts = admission()['artifacts'] if artifacts is None else artifacts
    apks = {role: copy.deepcopy(artifacts[role]) for role in ('product_apk', 'test_apk')}
    facts = copy.deepcopy(FACTS)
    facts['selected_methods'] = [dict(selector=kind, class_name=klass, method=method, instruction_units=units)
        for (kind, klass, method), units in zip(INSTRUMENTATIONS, UNITS)]
    facts['package_audit'] = dict(status='passed', package=APP, test_package=TEST,
        certificate_sha256=CERTIFICATE, test_permissions=['android.permission.REORDER_TASKS'],
        app={k: apks['product_apk'][k] for k in ('bytes', 'sha256')},
        test={k: apks['test_apk'][k] for k in ('bytes', 'sha256')})
    return dict(version=1, scope='record-cancellation-ui-build-v1', mode='fixed-b110-byte-attestation-v1',
        product=dict(head='7e29fb724ed781e953f321385f66a5f8982ad0f1', tree='39adcae73aae5448f9a3052d5125f1d4cc0d0033'),
        artifacts=apks, current_native_bindings=[], evidence={}, facts=facts,
        instrumentations=[list(row) for row in INSTRUMENTATIONS])


class TinyBuild:
    """Retained metadata only. Never copies/rebuilds APKs or historic captures."""
    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix='sdk18-record-cancellation-metadata-'))
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


# Explicit metadata-only activation observation ports.
def input_value():
    return dict(version=1, scope='record-cancellation-ui-run-input-v1',
        admission=legacy.pin(activation.RUNTIME / 'admission-v1.json'), helper=legacy.pin(activation.HELPER))


def admitted():
    a = admission()
    a['root'] = str(activation.RUNTIME / 'owned-v1')
    a['server']['root'] = str(Path(a['root']) / 'server')
    a['seconds'] = a['server']['seconds'] = 1700
    return a


def qualification():
    """Positive graph through actual qualify, with every external port explicit."""
    runtime = object.__new__(activation._Runtime)
    runtime.admission = a = admitted()
    runtime.value = value = input_value()
    runtime.request = dict(input=legacy.pin(activation.INPUT))
    runtime.original_owner = dict(pid=21, created_filetime=9000)
    runtime.running = legacy.pin('D:/Synthetic/running-v1.json')
    runtime.caller = dict(pid=22, created_filetime=9001)
    runtime.controller_result = legacy.pin('D:/Synthetic/controller-result-v1.json')
    runtime.stop_published = True
    runtime.result = dict(passed=False, cleanup_known=True, owner_wait_known=True,
        original_owner_returncode=0, capture_complete=True, capture_evidence_known=True,
        owner_terminal_published=True, controller_passed=True, observer_closed=True)
    owner_request = legacy.pin('D:/Synthetic/owner-request-v1.json')
    worker_result = legacy.pin('D:/Synthetic/worker-result-v1.json')
    started = legacy.pin('D:/Synthetic/started-v1.json')
    owner_result = legacy.pin('D:/Synthetic/owner-result-v1.json')
    after = legacy.pin('D:/Synthetic/after-v1.json')
    closure_path = Path(a['guest']['root']) / 'guest-storage-closure-v1.json'
    closure_pin = legacy.pin(closure_path)
    registry = Path('D:/Synthetic/metadata-only-registry')
    ledger_pin = legacy.pin(registry / 'ledger-v1.json')
    public = dict(qualified_target=True, reason='stop_requested', admission=value['admission'],
        request=owner_request, worker_result=worker_result, started=started, owner=owner_result, after=after)
    closure = dict(closure_verified=True, cleanup_complete=True, admission=value['admission'],
        worker_result=worker_result, owner_result=owner_result, after=after,
        proposal_sha256=a['guest']['proposal']['sha256'])
    bound = {
        str(Path(a['root']) / 'result-v1.json'): public,
        owner_request['path']: dict(owner=runtime.original_owner),
        started['path']: dict(worker=dict(pid=23, created_filetime=9002)),
        str(closure_path): closure,
        str(registry / 'ledger-v1.json'): dict(entries=[dict(root=a['guest']['root'], state='closed',
            closure=closure_pin, proposal_sha256=a['guest']['proposal']['sha256'])]),
    }
    verify = Mock(return_value=dict(reason='stop_requested', cleanup={key: True for key in c.CLEANUP_KEYS}))
    replay = Mock(return_value=dict(outcome='completed'))
    check = Mock()
    api = SimpleNamespace(contract=c,
        env=SimpleNamespace(binding=legacy.pin, encoded=env.encoded, check_binding=check,
                            guest_storage=SimpleNamespace(DEFAULT_REGISTRY=registry)),
        verification=SimpleNamespace(verify_owned_target_result=verify),
        controller=SimpleNamespace(verify_controller_result=replay))
    return runtime, api, copy.deepcopy(bound), verify, replay, check
