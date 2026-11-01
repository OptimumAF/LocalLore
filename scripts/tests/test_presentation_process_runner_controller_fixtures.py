"""Full SDK9 graph with real build/evidence/replay and mocked native/wire IO.

The only byte-authentication exception is the existing EXACT synthetic adb pin
with its historical fixed hash; every other file/source/build validator is real.
This exercises no Android, ADB executable, native process or production ledger.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from benchmarks import presentation_process_build as build
from benchmarks import presentation_process_controller as controller
from benchmarks import owned_presentation_process_contract as contract
from benchmarks import owned_presentation_process_owner as owner
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_archive_ui_controller_fixtures as previous
from scripts.tests import test_android_presentation_process_evidence as receipts
from scripts.tests import test_presentation_process_runner_build_fixtures as builds
from scripts.tests import test_presentation_process_runner_fixtures as f

ROLES = ('product_apk', 'test_apk', 'controller_apk')
PACKAGES = (f.APP, f.TEST, f.CONTROL)
UIDS = dict(zip(PACKAGES, (12345, 12346, 12347)))


class ControllerGraph(previous.ControllerGraph):
    @contextlib.contextmanager
    def modules(self):
        metadata = SimpleNamespace(admission=lambda: f.admission(contract), running=f.running, core=core)
        factory = SimpleNamespace(BuildGraph=lambda: builds.BuildGraph(build), pin=builds.pin, encoded=builds.encoded)
        with contextlib.ExitStack() as stack:
            for name, value in (('build', build), ('controller', controller), ('contract', contract),
                                ('owner', owner), ('f', metadata), ('builds', factory)):
                stack.enter_context(patch.object(previous, name, value))
            yield

    def __init__(self, **kwargs):
        with self.modules():
            super().__init__(**kwargs)
        self.result, records, _ = receipts.result_graph()
        run = self.a['run_id'][:16]
        self.result['run_id'] = run
        self.result['controller']['uid'] = UIDS[f.CONTROL]
        self.result['fixture'].update(controller_uid=UIDS[f.CONTROL], product_uid=UIDS[f.APP],
                                      signature_sha256=builds.SIGNER, origin_run_id=run,
                                      origin_product_sha256=self.a['artifacts']['product_apk']['sha256'])
        for observation in self.result['observations']:
            observation['uid'] = UIDS[f.APP]
        self.records = {}
        for leaf, raw in records.items():
            value = json.loads(raw)
            value.update(run_id=run, uid=UIDS[f.APP])
            self.records[leaf] = receipts.encoded(value)

    @contextlib.contextmanager
    def inputs(self):
        with self.modules(), super().inputs():
            yield

    def prove(self, live, path, session, context, sock, anchor, after=False):
        value = f.proof(session, after=after)
        value.update(context=copy.deepcopy(context), anchor=copy.deepcopy(anchor),
                     session=env.binding(Path(session['root']) / 'sdk-session-v9.json'))
        queries = path.with_name(path.stem + '-queries-v1.json')
        env.create_json(queries, f.query_bundle(session))
        value['queries'] = env.binding(queries)
        env.create_json(path, value)
        self.proofs.append((context['index'], context['phase']))
        return env.binding(path)

    def response(self, argv):
        self.calls.append(list(argv))
        stderr = b''
        if argv == ['getprop', 'sys.boot_completed']:
            return self.boot.pop(0), stderr
        if argv[:1] == ['getprop']:
            return {'ro.build.version.sdk': b'35\n', 'ro.product.cpu.abi': b'x86_64\n',
                    'ro.kernel.qemu': b'1\n'}[argv[1]], stderr
        if argv == ['am', 'get-current-user']:
            return b'0\n', stderr
        if argv[:4] == ['cmd', 'package', 'list', 'packages']:
            requested = argv[-1]
            return ''.join('package:' + package + ' uid:' + str(UIDS[package]) + '\n'
                           for package in PACKAGES if package in self.installed and requested in package).encode(), stderr
        if argv[:3] == ['cmd', 'package', 'path']:
            package = argv[-1]
            if self.fail == 'wrong_installed_path' and package == f.CONTROL:
                package = f.APP
            return ('package:/data/app/~~synthetic/' + package + '-opaque==/base.apk\n').encode(), stderr
        if argv[:1] == ['dd']:
            return b'', b'SYNTHETIC dd copied fixture input\n'
        if argv[:2] == ['pm', 'install']:
            role = next(role for role, path in f.STAGED.items() if path == argv[-1])
            self.installed.add(PACKAGES[ROLES.index(role)])
            return b'Success\n', stderr
        if argv[:1] == ['sha256sum']:
            role = next(role for role, package in zip(ROLES, PACKAGES)
                        if argv[1] == f.STAGED[role] or ('/' + package + '-opaque==/') in argv[1])
            return (self.a['artifacts'][role]['sha256'] + '  ' + argv[1] + '\n').encode(), stderr
        if argv[:2] == ['am', 'instrument']:
            assert argv == f.instrument(self.a)
            self.instrumented.append('presentation_process')
            if self.fail == 'invalid_exit_zero':
                return b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n', stderr
            if self.fail == 'source_after':
                with Path(self.python['executable']['path']).open('ab') as stream:
                    stream.write(b'changed after original dispatch')
            return receipts.frame(self.result), stderr
        if argv[:1] == ['run-as']:
            leaf = next(name for name in ('created', 'saved', 'commands') if name + '.json' in argv[-1])
            assert argv == contract.probe_read_argv(self.a, leaf)
            if self.fail == 'wrong_leaf_uid' and leaf == 'saved':
                value = json.loads(self.records[leaf])
                value['uid'] = UIDS[f.CONTROL]
                return receipts.encoded(value), stderr
            return self.records[leaf], stderr
        raise AssertionError('Unplanned synthetic SDK9 command: ' + repr(argv))

    def run(self):
        return controller.run(self.admission, self.running)

    def verify(self, caller=None):
        return controller.verify_controller_result(builds.pin(self.output / 'controller-result-v1.json'),
            self.admission, self.running, self.caller if caller is None else caller)

    def rebind_admission(self):
        self.g.write(self.ap, builds.encoded(self.a))
        self.admission = builds.pin(self.ap)
        self.d['admission'] = self.admission
        self.g.write(self.rp, builds.encoded(self.d))
        self.running = builds.pin(self.rp)
