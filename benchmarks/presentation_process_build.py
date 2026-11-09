"""SDK9's fixed, closed B43 product-build guard. No import I/O or tool execution.

Replays retained build evidence and rehashes source/artifacts; it does not run
Android, apksigner, the private launcher, or infer target acceptance from a build.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
import xml.etree.ElementTree as ET

from benchmarks import receipt_avd_environment as env

LAUNCH_ROOT = Path(__file__).parents[1]
SCOPE = 'presentation-process-build-v1'
APP = 'org.locallore.app.presentationprocessverify'
CONTROLLER = 'org.locallore.app.presentationprocesscontroller'
COMPONENT_CLASS = 'org.locallore.presentationprocessverify.PresentationProcessRestoreInstrumentation'
ROLES = ('product_apk', 'test_apk', 'controller_apk')
PACKAGES = (APP, APP + '.test', CONTROLLER)


class BuildRefused(ValueError):
    """Stable refusal with no private capture or signing values."""


def _need(value, reason='build'):
    if not value:
        raise BuildRefused(reason)


def _keys(value, names):
    _need(type(value) is dict and set(value) == set(names), 'shape')


def _same(left, right):
    return env.encoded(left) == env.encoded(right)


class _Reader:
    def __init__(self):
        self.until = time.monotonic() + 120
        self.checked = {}

    def raw(self, path, cap=64 * 1024 * 1024, *, installed=False):
        _need(time.monotonic() < self.until, 'deadline')
        path = Path(path)
        _need(path.is_absolute() and path.drive.upper() in (('C:', 'D:') if installed else ('D:',)), 'path')
        for parent in (path, *path.parents):
            info = parent.lstat()
            _need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 1024, 'path')
            _need(parent == path or stat.S_ISDIR(info.st_mode), 'path')
        before = path.lstat()
        _need(stat.S_ISREG(before.st_mode) and (installed or before.st_nlink == 1) and 0 <= before.st_size <= cap, 'file')
        with path.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            _need((before.st_dev, before.st_ino, before.st_size) ==
                  (opened.st_dev, opened.st_ino, opened.st_size), 'identity')
            raw = stream.read(before.st_size + 1)
        after = path.lstat()
        fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink', 'st_mode')
        _need(len(raw) == before.st_size and all(getattr(before, key) == getattr(after, key) for key in fields), 'changed')
        pin = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if path in self.checked:
            _need(_same(pin, self.checked[path][0]), 'changed')
        self.checked[path] = (pin, installed)
        return raw

    def pin(self, path, *, installed=False):
        self.raw(path, installed=installed)
        return copy.deepcopy(self.checked[Path(path)][0])

    def bound(self, value, *, installed=False):
        _keys(value, ('path', 'bytes', 'sha256'))
        _need(type(value['bytes']) is int and type(value['sha256']) is str and
              re.fullmatch('[0-9a-f]{64}', value['sha256']) is not None, 'binding')
        _need(_same(self.pin(value['path'], installed=installed), value), 'binding')
        return copy.deepcopy(value)

    def read(self, path):
        return env.decode_json(self.raw(path))

    def final(self):
        for path, (_, installed) in list(self.checked.items()):
            self.raw(path, installed=installed)


def _git(arguments):
    # Only these source queries are admitted; no SDK, native process observer,
    # credential reader, build, dependency fetch or user-supplied command.
    _need(arguments in (['rev-parse', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'],
                        ['ls-files', '-z']), 'git')
    answer = subprocess.run(['git', '--no-optional-locks', '-C', str(_SPEC['root'])] + arguments,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    _need(answer.returncode == 0 and answer.stderr == b'', 'source')
    return answer.stdout


def _source_head():
    _need(_git(['rev-parse', 'HEAD']).decode('ascii').strip() == _SPEC['head'] and
          _git(['status', '--porcelain', '--untracked-files=all']) == b'', 'source')


def _commands():
    root = _SPEC['root']
    java, python = _SPEC['java'], _SPEC['python']
    product, test, controller = (str(Path(_SPEC['apks'][role]['path'])) for role in ROLES)
    return [[java, '-classpath', str(root / 'apps/android/gradle/wrapper/gradle-wrapper.jar'),
             'org.gradle.wrapper.GradleWrapperMain', ':app:assembleDebug', ':app:assembleDebugAndroidTest',
             ':app:testDebugUnitTest', ':app:lintDebug', '--no-daemon', '--console=plain',
             '-Pandroid.builder.sdkDownload=false', ':presentation-process-controller:assembleDebug',
             ':presentation-process-controller:lintDebug', '-PlocalLoreInputDraftVerification=true',
             '-PlocalLorePresentationProcessVerification=true', '--project-cache-dir',
             '.gradle-presentation-process', '--offline'],
            [python, str(root / 'scripts/audit_apk.py'), product, '--presentation-process-verification'],
            [python, str(root / 'scripts/audit_instrumentation_apk.py'), product, test, '--presentation-process-verification'],
            [python, str(root / 'scripts/audit_process_controller.py'), controller, '--presentation-process-verification']]


def _reports(reader):
    root = _SPEC['root']
    reports = sorted((root / 'apps/android/app/build-presentation-process/test-results/testDebugUnitTest').glob('TEST-*.xml'))
    _need(len(reports) == 48, 'jvm')
    roster = []
    for path in reports:
        suite = ET.fromstring(reader.raw(path))
        cases = suite.findall('testcase')
        _need(suite.tag == 'testsuite' and int(suite.attrib['tests']) == len(cases), 'jvm')
        # Header counts and the direct roster cannot hide a nested outcome or
        # another suite/case. Gradle's report has one suite and direct cases.
        _need(list(suite.iter('testsuite')) == [suite] and list(suite.iter('testcase')) == cases and
              not any(list(suite.iter(key)) for key in ('failure', 'error', 'skipped')), 'jvm')
        _need(all(int(suite.attrib.get(key, '0')) == 0 for key in ('failures', 'errors', 'skipped')), 'jvm')
        for case in cases:
            _need(not any(case.findall(key) for key in ('failure', 'error', 'skipped')), 'jvm')
            roster.append(dict(classname=case.attrib['classname'], name=case.attrib['name']))
    identities = [(row['classname'], row['name']) for row in roster]
    _need(len(identities) == len(set(identities)) == 417, 'jvm')
    source = reader.raw(root / 'apps/android/app/src/test/java/org/locallore/app/PresentationProcessProofTest.kt').decode('utf-8')
    methods = set(re.findall(r'@Test\s+fun\s+(\w+)\s*\(', source))
    _need(len(methods) == 6 and {name for cls, name in identities if cls == 'org.locallore.app.PresentationProcessProofTest'} == methods, 'jvm')
    _need(_same(reader.read(_SPEC['review'] / 'jvm-roster-v1.json'), roster), 'jvm')
    lint = {}
    for role, path, wanted in (
        ('app', root / 'apps/android/app/build-presentation-process/reports/lint-results-debug.xml',
         Counter({('GradleDependency', 'Warning'): 1, ('AutoboxingStateCreation', 'Hint'): 1})),
        ('controller', root / 'apps/android/presentation-process-controller/build/reports/lint-results-debug.xml',
         Counter({('DataExtractionRules', 'Warning'): 1, ('MissingApplicationIcon', 'Warning'): 1}))):
        tree = ET.fromstring(reader.raw(path))
        actual_lint = Counter((row.get('id'), row.get('severity')) for row in tree.findall('issue'))
        _need(tree.tag == 'issues' and actual_lint == wanted, 'lint')
        lint[role] = [dict(id=issue, severity=severity, count=count) for (issue, severity), count in actual_lint.items()]
    return methods, lint


def _replay():
    reader = _Reader()
    root, capture, review = (_SPEC[key] for key in ('root', 'capture', 'review'))
    _source_head()
    for table, parent in ((_SPEC['capture_pins'], capture), (_SPEC['review_pins'], review)):
        for name, pin in table.items():
            _need(Path(pin['path']) == parent / name, 'binding')
            reader.bound(pin)
    before, after = (reader.read(capture / ('sources-' + phase + '-v1.json')) for phase in ('before', 'after'))
    _need(_same(before, after) and type(before) is dict and len(before) == _SPEC['source_count'], 'source')
    tracked = _git(['ls-files', '-z']).decode('utf-8').split('\0')
    _need(tracked[-1] == '' and set(tracked[:-1]) == set(before), 'source')
    for relative, digest in before.items():
        path = Path(relative)
        _need(not path.is_absolute() and not path.drive and path.parts and
              all(part not in ('', '.', '..') for part in relative.replace('\\', '/').split('/')), 'source')
        _need(reader.pin(root / path)['sha256'] == digest, 'source')
    for relative in _SPEC['shared']:
        product, launcher = reader.pin(root / relative), reader.pin(LAUNCH_ROOT / relative)
        _need(product['bytes'] == launcher['bytes'] and product['sha256'] == launcher['sha256'], 'shared_source')
    request = reader.read(capture / 'request-v1.json')
    _keys(request, ('version', 'scope', 'head', 'owner_seconds', 'command', 'sources', 'tools',
                    'signing_property_names', 'signing_values_logged'))
    _need(type(request['version']) is int and request['version'] == 1 and request['head'] == _SPEC['head'] and
          type(request['owner_seconds']) is int and request['owner_seconds'] == 900 and
          request['scope'] == 'actual reviewed public four-command presentation-process pipeline', 'request')
    _need(request['command'] == [_SPEC['python'], '-I', '-S', '-B', str(root / 'scripts/check.py'),
                               'android', '--presentation-process-verification', '--offline'], 'request')
    _need(request['signing_values_logged'] is False and request['signing_property_names'] == sorted(
        'android.injected.signing.' + suffix for suffix in ('store.file', 'store.password', 'key.alias', 'key.password')), 'signing')
    _need(_same(request['sources'], _SPEC['capture_pins']['sources-before-v1.json']), 'source')
    _need(type(request['tools']) is list and len(request['tools']) == 7 and
          _same(request['tools'], list(_SPEC['tools'])), 'tools')
    for pin in request['tools']:
        reader.bound(pin, installed=Path(pin['path']).drive.upper() == 'C:')
    actual = reader.read(capture / 'actual-child-v1.json')
    _keys(actual, ('pid', 'creation_filetime', 'executable'))
    _need(type(actual['pid']) is int and 0 < actual['pid'] <= 2**32-1 and
          type(actual['creation_filetime']) is int and actual['creation_filetime'] > 0 and
          actual['executable'] == _SPEC['python'], 'worker')
    _need(_same(reader.read(capture / 'started-v1.json'), dict(worker=actual,
          request=_SPEC['capture_pins']['request-v1.json'])), 'worker')
    result = reader.read(capture / 'result-v1.json')
    _keys(result, ('version', 'passed', 'feature_acceptance', 'sources_equal', 'tools_equal', 'owner'))
    _need(type(result['version']) is int and result['version'] == 1 and result['passed'] is True and
          result['feature_acceptance'] is False and result['sources_equal'] is True and result['tools_equal'] is True, 'owner')
    owner = result['owner']
    _keys(owner, ('status', 'worker_returncode', 'cleanup_complete', 'output_capture_complete',
                  'stdout_bytes', 'stderr_bytes', 'elapsed_ms'))
    _need(owner['status'] == 'child_exited' and type(owner['worker_returncode']) is int and owner['worker_returncode'] == 0 and
          owner['cleanup_complete'] is True and owner['output_capture_complete'] is True and
          type(owner['elapsed_ms']) is int and 0 <= owner['elapsed_ms'] <= 900000, 'owner')
    public = reader.read(capture / 'public-result-v1.json')
    _keys(public, ('returncode', 'elapsed_ms'))
    _need(type(public['returncode']) is int and public['returncode'] == 0 and
          type(public['elapsed_ms']) is int and 0 <= public['elapsed_ms'] <= owner['elapsed_ms'], 'public')
    stdout, stderr = reader.raw(capture / 'owner-stdout-v1.bin'), reader.raw(capture / 'owner-stderr-v1.bin')
    _need(type(owner['stdout_bytes']) is int and len(stdout) == owner['stdout_bytes'] and
          type(owner['stderr_bytes']) is int and len(stderr) == owner['stderr_bytes'], 'capture')
    text = stdout.decode('utf-8')
    lines = text.splitlines()
    heads = [index for index, line in enumerate(lines) if line.startswith('+ ')]
    _need(len(heads) == 4 and [ast.literal_eval(lines[index][2:]) for index in heads] == _commands(), 'commands')
    for task in (':app:buildRustAndroid', ':app:testDebugUnitTest', ':app:lintDebug', ':app:compileDebugAndroidTestKotlin',
                 ':presentation-process-controller:assembleDebug', ':presentation-process-controller:lintDebug'):
        rows = [line for line in lines if line == '> Task ' + task or line.startswith('> Task ' + task + ' ')]
        _need(rows and all(row == '> Task ' + task for row in rows), 'executed')
    _need(sum(re.fullmatch(r'BUILD SUCCESSFUL in [^\r\n]+', line) is not None for line in lines) == 1 and all(marker in text for marker in (
        'Building LocalLore Rust JNI: x86_64-linux-android -> x86_64',
        'Building LocalLore Rust JNI: aarch64-linux-android -> arm64-v8a')), 'executed')
    audits = []
    for index in (1, 2, 3):
        end = heads[index+1] if index < 3 else len(lines)
        audits.append(env.decode_json('\n'.join(lines[heads[index]+1:end]).strip().encode('utf-8')))
    _need(all(type(value) is dict and value.get('status') == 'passed' for value in audits), 'audit')
    product, pair, controller = audits
    _keys(product, ('status', 'permissions', 'libraries'))
    _keys(pair, ('status', 'package', 'test_package', 'test_permissions', 'certificate_sha256', 'app', 'test'))
    _keys(controller, ('version', 'scope', 'status', 'package', 'instrumentation', 'target', 'min_sdk',
                       'target_sdk', 'permissions', 'components', 'zip_entries', 'apk_sha256'))
    _need(product['permissions'] == [APP + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'] and
          type(product['libraries']) is list and len(product['libraries']) == 4 and
          {row['entry'] for row in product['libraries']} == {'lib/' + abi + '/' + library
            for abi in ('arm64-v8a', 'x86_64') for library in ('liblocallore_android.so', 'libandroidx.graphics.path.so')} and
          all(type(row) is dict and set(row) == {'entry', 'elf_load_alignment'} and
              type(row['elf_load_alignment']) is list and 0 < len(row['elf_load_alignment']) <= 64 and
              all(type(n) is int and n >= 16384 and n % 16384 == 0 for n in row['elf_load_alignment'])
              for row in product['libraries']), 'native')
    _need(pair['package'] == APP and pair['test_package'] == APP + '.test' and
          pair['test_permissions'] == ['android.permission.REORDER_TASKS'], 'packages')
    for role in ROLES:
        reader.bound(_SPEC['apks'][role])
    for role, key in (('product_apk', 'app'), ('test_apk', 'test')):
        _need(_same(pair[key], {name: _SPEC['apks'][role][name] for name in ('bytes', 'sha256')}), 'apk')
    _need(controller['package'] == controller['target'] == CONTROLLER and controller['instrumentation'] == COMPONENT_CLASS and
          type(controller['version']) is int and controller['version'] == 1 and
          type(controller['min_sdk']) is int and controller['min_sdk'] == 26 and
          type(controller['target_sdk']) is int and controller['target_sdk'] == 36 and
          type(controller['zip_entries']) is int and controller['zip_entries'] == 5 and
          controller['apk_sha256'] == _SPEC['apks']['controller_apk']['sha256'] and controller['permissions'] == [] and
          type(controller['components']) is int and controller['components'] == 0 and
          controller['scope'] == 'locallore_presentation_process_controller_apk_audit_v1', 'controller')
    certificate = pair['certificate_sha256']
    _need(type(certificate) is str and re.fullmatch('[0-9a-f]{64}', certificate) is not None, 'certificate')
    signers = []
    for role, short in zip(ROLES, ('product', 'test', 'controller')):
        record = reader.read(review / ('signer-' + short + '-result-v1.json'))
        _keys(record, ('role', 'command', 'status', 'returncode', 'cleanup_complete', 'elapsed_ms', 'stderr_bytes', 'stdout'))
        _need(record['role'] == short and record['command'] == [_SPEC['java'], '-jar', _SPEC['signer_jar'],
              'verify', '--verbose', '--print-certs', _SPEC['apks'][role]['path']] and record['status'] == 'completed' and
              type(record['returncode']) is int and record['returncode'] == 0 and record['cleanup_complete'] is True and
              type(record['elapsed_ms']) is int and 0 <= record['elapsed_ms'] <= 15000 and
              type(record['stderr_bytes']) is int and record['stderr_bytes'] == 0 and
              _same(record['stdout'], _SPEC['review_pins']['signer-' + short + '-stdout-v1.bin']), 'signer')
        signer = reader.raw(record['stdout']['path']).decode('utf-8')
        _need(re.findall(r'^Number of signers: (\d+)\r?$', signer, re.M) == ['1'] and
              [value.lower() for value in re.findall(r'^Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]{64})\r?$', signer, re.M)] == [certificate], 'signer')
        signers.append(dict(record, certificate_sha256=certificate))
    methods, lint = _reports(reader)
    closed = reader.read(review / 'result-v1.json')
    _keys(closed, ('passed', 'summary', 'elapsed_ms', 'hashed_bytes', 'hashed_files'))
    _need(closed['passed'] is True and all(type(closed[key]) is int for key in ('elapsed_ms', 'hashed_bytes', 'hashed_files')) and
          0 <= closed['elapsed_ms'] <= 150000 and 0 < closed['hashed_bytes'] <= 1024**3 and
          _SPEC['source_count'] <= closed['hashed_files'] <= 10000, 'review')
    summary = closed['summary']
    _keys(summary, ('head', 'source_files', 'public_commands', 'owner_elapsed_ms', 'public_elapsed_ms', 'JVM_tests',
                    'JVM_XML', 'new_JVM_methods', 'failures', 'errors', 'skips', 'lint', 'APKs',
                    'common_certificate_sha256', 'static_signer_checks', 'pipeline_exit_attribution', 'limits'))
    _need(summary['head'] == _SPEC['head'] and type(summary['source_files']) is int and
          summary['source_files'] == _SPEC['source_count'] and type(summary['JVM_tests']) is int and summary['JVM_tests'] == 417 and
          type(summary['JVM_XML']) is int and summary['JVM_XML'] == 48 and summary['new_JVM_methods'] == sorted(methods) and
          all(type(summary[key]) is int and summary[key] == 0 for key in ('failures', 'errors', 'skips')) and
          _same(summary['owner_elapsed_ms'], owner['elapsed_ms']) and _same(summary['public_elapsed_ms'], public['elapsed_ms']) and
          summary['common_certificate_sha256'] == certificate and summary['public_commands'] == _commands() and
          _same(summary['lint'], lint) and _same(summary['static_signer_checks'], signers) and
          _same(summary['APKs'], {short: _SPEC['apks'][role] for role, short in zip(ROLES, ('product', 'test', 'controller'))}) and
          type(summary['limits']) is list and len(summary['limits']) == 3 and all(type(x) is str and x for x in summary['limits']) and
          summary['pipeline_exit_attribution'] == 'One successful unmodified public runner plus four command headers/three successful audit outputs; no separate per-command RC receipts invented.', 'review')
    manifest = dict(version=1, scope=SCOPE,
        product_source=dict(head=_SPEC['head'], sources=copy.deepcopy(_SPEC['capture_pins']['sources-before-v1.json'])),
        public_execution={key: copy.deepcopy(_SPEC['capture_pins'][name]) for key, name in (
            ('request', 'request-v1.json'), ('actual_child', 'actual-child-v1.json'), ('owner', 'result-v1.json'),
            ('public_result', 'public-result-v1.json'), ('stdout', 'owner-stdout-v1.bin'), ('stderr', 'owner-stderr-v1.bin'))},
        apks={role: dict(binding=copy.deepcopy(_SPEC['apks'][role]), package=package, certificate_sha256=certificate)
              for role, package in zip(ROLES, PACKAGES)})
    manifest['public_execution']['closed_review'] = copy.deepcopy(_SPEC['review_pins']['result-v1.json'])
    reader.final()
    _source_head()
    return manifest


def create_manifest():
    """Seal only the fixed create-only manifest; grants no preparation or boot."""
    try:
        manifest = _replay()
        env.create_json(_SPEC['manifest_path'], manifest)
        return _Reader().pin(_SPEC['manifest_path'])
    except BuildRefused:
        raise
    except Exception:
        raise BuildRefused('product') from None


def verify_frozen_product(artifacts):
    """Artifacts-only pre-prepare check, with no selectable verifier or root."""
    try:
        _keys(artifacts, ('build', *ROLES))
        _need(all(_same(artifacts[role], _SPEC['apks'][role]) for role in ROLES), 'artifact')
        reader = _Reader()
        _need(Path(artifacts['build']['path']) == _SPEC['manifest_path'], 'artifact')
        reader.bound(artifacts['build'])
        manifest = reader.read(_SPEC['manifest_path'])
        _need(_same(manifest, _replay()), 'manifest')
        reader.final()
        return copy.deepcopy(manifest)
    except BuildRefused:
        raise
    except Exception:
        raise BuildRefused('product') from None


def verify_current(admission):
    from benchmarks import owned_presentation_process_contract as contract
    value = contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    manifest = verify_frozen_product(value['artifacts'])
    contract.revalidate_inputs(value)
    return manifest

# _SPEC is source-fixed below. It is data, never an admission/CLI-selected mode.

_SPEC = {'root': Path('D:/Worktrees/LocalLore-presentation-process-core-v1'),
 'head': '6302cb45b0a4397ee1313cc7b21e3d8cfe8f8fc8',
 'source_count': 2537,
 'capture': Path('D:/Dev/Experiments/LocalLore/2026-11-01-presentation-process-v3/public-android-v1/run-v1'),
 'review': Path('D:/Dev/Experiments/LocalLore/2026-11-01-presentation-process-v3/closed-build-review-v1'),
 'manifest_path': Path('D:/Dev/Experiments/LocalLore/2026-11-01-presentation-process-runner-v1/build-v1.json'),
 'capture_pins': {'request-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\request-v1.json',
                                      'bytes': 2131,
                                      'sha256': '8fc70ea81b27d3b353053fecad4cecb1974b43edae9a9a36dd4927124d1eaa0a'},
                  'actual-child-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\actual-child-v1.json',
                                           'bytes': 142,
                                           'sha256': 'c6d5a45b77901a5c662c076c32318571e210fb6f562588f6c130e0b7050e96e4'},
                  'started-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\started-v1.json',
                                      'bytes': 375,
                                      'sha256': '919c5bc65d6153043cb388e4f08e2150421abbeaa16a4de9eec1c2255b9b30a4'},
                  'result-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\result-v1.json',
                                     'bytes': 266,
                                     'sha256': 'c77612c0e9024a32259750cab157139b763713168332ff29ba87120ed147f811'},
                  'public-result-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\public-result-v1.json',
                                            'bytes': 37,
                                            'sha256': '87ce3aa46157a32bb122da54c2ac1ff30ce15ff80ac44d5c71d4529b4938e518'},
                  'sources-before-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\sources-before-v1.json',
                                             'bytes': 314784,
                                             'sha256': 'a9f925095e07f464f63141003dd579ef3db6f501857cae2fc753ea7cb0073902'},
                  'sources-after-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\sources-after-v1.json',
                                            'bytes': 314784,
                                            'sha256': 'a9f925095e07f464f63141003dd579ef3db6f501857cae2fc753ea7cb0073902'},
                  'owner-stdout-v1.bin': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\owner-stdout-v1.bin',
                                          'bytes': 16198,
                                          'sha256': 'e434640edbce70529a09e4f70f07a40c7bd6ee7429d92b7fafa5dac3478d3a73'},
                  'owner-stderr-v1.bin': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-v1\\owner-stderr-v1.bin',
                                          'bytes': 295,
                                          'sha256': '716c8eb3d5786c2c8ed7b51ae0b46f874c822614b72153accc0c684b552e000e'}},
 'review_pins': {'result-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\closed-build-review-v1\\result-v1.json',
                                    'bytes': 8366,
                                    'sha256': '2a7a7d25e2430bd8ac8514739a38e0a50cc73f000b49dd5a85f44d309251f5a2'},
                 'jvm-roster-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\closed-build-review-v1\\jvm-roster-v1.json',
                                        'bytes': 62099,
                                        'sha256': '5fb881fbec8b77b5e4cec9646a14f33084476cef090164c080d3ee5692915563'},
                 'signer-product-result-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\closed-build-review-v1\\signer-product-result-v1.json',
                                                   'bytes': 770,
                                                   'sha256': '7eb73dbe628072fb392940749c2178abe691365f3202db41a509606a344a2927'},
                 'signer-product-stdout-v1.bin': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\closed-build-review-v1\\signer-product-stdout-v1.bin',
                                                  'bytes': 972,
                                                  'sha256': '8a1aaeac93aeb0cc091c0ec3c14e432749f5e146575f23f00411dc0d32400a50'},
                 'signer-test-result-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\closed-build-review-v1\\signer-test-result-v1.json',
                                                'bytes': 789,
                                                'sha256': 'c7360537595527c47df39c21c44346625a3e0c6152668d605b677d74cc2e9fa5'},
                 'signer-test-stdout-v1.bin': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\closed-build-review-v1\\signer-test-stdout-v1.bin',
                                               'bytes': 972,
                                               'sha256': '8a1aaeac93aeb0cc091c0ec3c14e432749f5e146575f23f00411dc0d32400a50'},
                 'signer-controller-result-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\closed-build-review-v1\\signer-controller-result-v1.json',
                                                      'bytes': 811,
                                                      'sha256': 'b5a718a50c7a5c283d82048ccdb6c0d0925e1a8972860f8ca24d7dbe9f98044a'},
                 'signer-controller-stdout-v1.bin': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\closed-build-review-v1\\signer-controller-stdout-v1.bin',
                                                     'bytes': 972,
                                                     'sha256': '8a1aaeac93aeb0cc091c0ec3c14e432749f5e146575f23f00411dc0d32400a50'}},
 'tools': ({'bytes': 6124,
            'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-presentation-process-v3\\public-android-v1\\run-public-v1.py',
            'sha256': '40e540d5eec11c8ed0592143a0ee3ad6ed93b9b29015b8001ef8cfd2f9a43ca1'},
           {'bytes': 106208,
            'path': 'C:\\Users\\Avery\\AppData\\Local\\Programs\\Python\\Python314\\python.exe',
            'sha256': '4942b86a6597e5aee0128daa00050ed79bc21f6e709a78eb19cbfeb0c2f39ac9'},
           {'bytes': 54384,
            'path': 'C:\\Program Files\\Java\\jdk-21\\bin\\java.exe',
            'sha256': '6f792b96630815e9349602c379960c46460065b17432c719902439f9a147064a'},
           {'bytes': 13331568,
            'path': 'C:\\Program Files\\Java\\jdk-21\\bin\\server\\jvm.dll',
            'sha256': '2ea52695dd8c186dbda86b9b038a489d4d2d6185542d625cfbfd3430c3b54c70'},
           {'bytes': 4740896,
            'path': 'C:\\Users\\Avery\\AppData\\Local\\Android\\Sdk\\build-tools\\35.0.0\\aapt2.exe',
            'sha256': 'cbfe5deda5f7074ce47b6f33818b456ee8046a076a11af13e29c837d3c80c564'},
           {'bytes': 1074241,
            'path': 'C:\\Users\\Avery\\AppData\\Local\\Android\\Sdk\\build-tools\\35.0.0\\lib\\apksigner.jar',
            'sha256': '00ef9948f843fe395d2440ae3ef41405b8040a6d5d46493bd1902ac0ee6deae7'},
           {'bytes': 15761,
            'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-10-30-public-android-gate-v1\\signing-review-v1\\signing-compatibility-v1.json',
            'sha256': '2e3de2518d0bb3ffcb8d410a3cd9bc82d008522130305b0e9ac6433c218b2dac'}),
 'apks': {'product_apk': {'bytes': 28012692,
                          'path': 'D:\\Worktrees\\LocalLore-presentation-process-core-v1\\apps\\android\\app\\build-presentation-process\\outputs\\apk\\debug\\app-debug.apk',
                          'sha256': '9d4e8235dccd9575670e01606194489937f4abcf96e6717e7443f688caf3bc42'},
          'test_apk': {'bytes': 2265924,
                       'path': 'D:\\Worktrees\\LocalLore-presentation-process-core-v1\\apps\\android\\app\\build-presentation-process\\outputs\\apk\\androidTest\\debug\\app-debug-androidTest.apk',
                       'sha256': '6dc98854829078920055e5bc4ffb223327a55bf7e3ff0fe107edb7918a26bd33'},
          'controller_apk': {'bytes': 39265,
                             'path': 'D:\\Worktrees\\LocalLore-presentation-process-core-v1\\apps\\android\\presentation-process-controller\\build\\outputs\\apk\\debug\\presentation-process-controller-debug.apk',
                             'sha256': 'b4e77b813b5af1d7f8053cc36bfe150708cbea10ed22bc9fd39b44b747780508'}},
 'python': 'C:\\Users\\Avery\\AppData\\Local\\Programs\\Python\\Python314\\python.exe',
 'java': 'C:\\Program Files\\Java\\jdk-21\\bin\\java.exe',
 'signer_jar': 'C:\\Users\\Avery\\AppData\\Local\\Android\\Sdk\\build-tools\\35.0.0\\lib\\apksigner.jar',
 'shared': ('benchmarks/adb_held_socket.py',
            'benchmarks/adb_held_socket_probe.py',
            'benchmarks/adb_held_socket_windows.py',
            'benchmarks/android_instrumentation_evidence.py',
            'benchmarks/android_presentation_process_evidence.py',
            'benchmarks/android_process_client_v4.py',
            'benchmarks/android_process_verification.py',
            'benchmarks/android_process_verification_v4.py',
            'benchmarks/host_commit_capacity.py',
            'benchmarks/isolated_adb_lease.py',
            'benchmarks/isolated_adb_owner.py',
            'benchmarks/owned_target_contract.py',
            'benchmarks/owned_target_owner.py',
            'benchmarks/receipt_avd_environment.py',
            'benchmarks/receipt_avd_storage.py',
            'benchmarks/runtime_spike.py',
            'benchmarks/windows_tcp_control.py',
            'benchmarks/windows_tcp_observation.py')}
