"""Fixed SDK9 presentation-process authority; importing grants no target access.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import PureWindowsPath
import re

from benchmarks import owned_target_contract as core

PROTOCOL = 'owned-emulator-presentation-process-v1'
SDK_PROTOCOL = 'sdk-presentation-process-v1'
PROOF_PROTOCOL = 'presentation-process-socket-proof-v1'
CLIENT_VERSION = 9
SESSION_FILE = 'sdk-session-v9.json'
OWNER_SCRIPT = 'owned_presentation_process_owner.py'
BOOT_CLAIM_FILE = 'owned-presentation-process-boot-claim-v1.json'
APP = 'org.locallore.app.presentationprocessverify'
TEST = APP + '.test'
CONTROLLER = CONTROL = 'org.locallore.app.presentationprocesscontroller'
COMPONENT = CONTROLLER + '/org.locallore.presentationprocessverify.PresentationProcessRestoreInstrumentation'
CASE = 'restore_player_presentation'
CLAIM_KIND = 'presentation_process'
CLAIM_KINDS = (CLAIM_KIND,)
INSTRUMENTATIONS = ()
MODEL_MATERIAL = False
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-01-presentation-process-target-v1/avd-v1')
ARTIFACT_KEYS = frozenset(('build', 'product_apk', 'test_apk', 'controller_apk'))
STAGED = {
    'product_apk': '/data/local/tmp/locallore-product-v1.apk',
    'test_apk': '/data/local/tmp/locallore-test-v1.apk',
    'controller_apk': '/data/local/tmp/locallore-presentation-controller-v1.apk',
}
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | {
    'owned_presentation_process_contract.py', 'owned_presentation_process_owner.py',
    'android_process_presentation_process_client.py',
    'android_process_presentation_process_verification.py',
    'presentation_process_build.py', 'presentation_process_controller.py',
    'android_presentation_process_evidence.py', 'android_process_verification.py',
    'android_instrumentation_evidence.py',
})


class _PresentationContract(core._Contract):
    def controller_run_id(self, admission):
        return self.validate_admission(admission)['run_id'][:16]

    def instrument_argv(self, admission):
        value = self.validate_admission(admission)
        return ['am', 'instrument', '-w', '-r', '-e', 'case', CASE,
                '-e', 'run_id', value['run_id'][:16], '-e', 'product_sha256',
                value['artifacts']['product_apk']['sha256'], COMPONENT]

    def instrumentation_kind(self, argv):
        if (type(argv) is list and len(argv) == 14 and
                argv[:9] == ['am', 'instrument', '-w', '-r', '-e', 'case', CASE, '-e', 'run_id'] and
                type(argv[9]) is str and re.fullmatch('[0-9a-f]{16}', argv[9]) and
                argv[10:12] == ['-e', 'product_sha256'] and type(argv[12]) is str and
                re.fullmatch('[0-9a-f]{64}', argv[12]) and argv[13] == COMPONENT):
            return CLAIM_KIND
        return None

    def probe_read_argv(self, admission, leaf):
        run_id = self.controller_run_id(admission)
        core._need(type(leaf) is str and leaf in ('created', 'saved', 'commands'), 'command')
        directory = 'no_backup/process-verify-v3/' + run_id
        path = directory + '/' + leaf + '.json'
        # The source fixes every path and predicate. The package's own UID is
        # derived inside run-as; no caller can supply a UID or a shell fragment.
        # Directories may have multiple links. Only the regular leaf needs nlink1.
        checks = ['u=$(id -u)', 'case "$u" in ""|*[!0-9]*) exit 1;; esac',
                  '[ "$u" -ge 10000 ]', '[ "$u" -le 99999 ]']
        for parent in ('no_backup', 'no_backup/process-verify-v3', directory):
            checks += ['[ ! -L ' + parent + ' ]', '[ -d ' + parent + ' ]',
                       '[ "$(stat -c %u ' + parent + ')" = "$u" ]']
        checks += ['[ ! -L ' + path + ' ]', '[ -f ' + path + ' ]',
                   '[ "$(stat -c %u ' + path + ')" = "$u" ]',
                   '[ "$(stat -c %h ' + path + ')" = 1 ]',
                   's=$(stat -c %s ' + path + ')',
                   'case "$s" in ""|*[!0-9]*) exit 1;; esac',
                   '[ "$s" -gt 0 ]', '[ "$s" -le 4096 ]', 'cat ' + path]
        return ['run-as', APP, '--user', '0', 'sh', '-c', ' && '.join(checks)]

    def validate_operation(self, value, admission):
        a = self.validate_admission(admission)
        core._obj(value, ('argv', 'stdin'), 'command')
        argv = value['argv']
        core._need(type(argv) is list and 1 <= len(argv) <= 64 and all(
            type(x) is str and x and len(x.encode('utf-8')) <= 8192 and
            not any(ord(c) < 32 for c in x) for x in argv), 'command')
        core._need(len(str(argv).encode('utf-8')) <= 16384, 'command')
        expected, ok = None, False
        if argv[:1] == ['getprop']:
            ok = len(argv) == 2 and argv[1] in ('sys.boot_completed', 'ro.build.version.sdk',
                                             'ro.product.cpu.abi', 'ro.kernel.qemu')
        elif argv == ['am', 'get-current-user'] or argv == self.instrument_argv(a):
            ok = True
        elif argv[:1] == ['cmd']:
            ok = any(argv in (['cmd', 'package', 'list', 'packages', '-U', '--user', '0', package],
                              ['cmd', 'package', 'path', '--user', '0', package])
                     for package in (APP, TEST, CONTROLLER))
        elif argv[:1] == ['pm']:
            ok = any(argv == ['pm', 'install', '-r', '-t', '--user', '0', path]
                     for path in STAGED.values())
        elif argv[:1] == ['sha256sum'] and len(argv) == 2:
            packages = '(?:' + '|'.join(re.escape(p) for p in (APP, TEST, CONTROLLER)) + ')'
            ok = argv[1] in STAGED.values() or re.fullmatch(
                '/data/app/(?:~~[A-Za-z0-9_=-]+/)?' + packages + '-[A-Za-z0-9_~=-]+/base\\.apk', argv[1]) is not None
        elif argv[:1] == ['dd']:
            for role, path in STAGED.items():
                if argv == ['dd', 'of=' + path, 'bs=65536']:
                    ok, expected = True, a['artifacts'][role]
        elif argv[:1] == ['run-as']:
            ok = any(argv == self.probe_read_argv(a, leaf) for leaf in ('created', 'saved', 'commands'))
        # No inherited generic run-as, force-stop, pidof, model or JUnit grammar.
        core._need(ok and core._same(value['stdin'], expected), 'command')
        if expected is not None:
            self.binding(expected, max_bytes=256 * 1024 * 1024)
        return copy.deepcopy(value)


_API = _PresentationContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS, APP=APP, TEST=TEST,
    MODEL_MATERIAL=MODEL_MATERIAL))

for _name in ('PORT', 'ADMISSION_KEYS', 'GUEST_KEYS', 'RUNNING_KEYS', 'SESSION_KEYS',
              'CONTEXT_KEYS', 'PROOF_KEYS', 'QUERY_BUNDLE_KEYS', 'QUERY_KEYS',
              'BRACKET_KEYS', 'READY_KEYS', 'JOB_KEYS', 'REQUEST_KEYS', 'WORKER_KEYS',
              'CLEANUP_KEYS', 'CLIENT_KEYS', 'TargetRefused', '_need', '_obj', '_int',
              '_same', '_path', '_process'):
    globals()[_name] = getattr(core, _name)
for _name in ('binding', '_sources', 'validate_admission', '_clock', 'validate_running',
              'check_stop', 'validate_session', '_relative', 'validate_operation',
              'operation_digest', '_rows', 'validate_observation', '_guest_observation',
              'validate_guest_observation', 'validate_guest_prefix', 'device_status',
              'device_transport', 'validate_proof', '_brackets', 'validate_query_bundle',
              'validate_guest_job', 'validate_ready', 'validate_claim', 'validate_client_record',
              'source_bindings', 'revalidate_inputs', 'instrumentation_kind', 'claim_record',
              'controller_run_id', 'instrument_argv', 'probe_read_argv'):
    globals()[_name] = getattr(_API, _name)
del _name
