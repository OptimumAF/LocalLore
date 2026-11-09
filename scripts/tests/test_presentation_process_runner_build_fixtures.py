"""Byte-backed synthetic three-APK public-build graph, with a real tiny Git root.

Only the production module's fixed _SPEC is substituted. No validator verdict,
Git discovery, source hash, XML parser, command parser or signer parser is mocked.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from scripts.tests import test_audit_apk as apk_f
from scripts.tests import test_presentation_process_runner_fixtures as f

METHODS = (
    'presentationAndLegacyAttemptsAreSeparateAndUnknownOperationsRemainVisible',
    'metadataAndCreationAliasesDoNotHideOtherUnknownAttempts',
    'exactRuntimeAndScopeDigestFieldsDoNotRetainScopeOrMutableCounters',
    'invalidOrMissingHintProducesNoScopeDigest',
    'counterShapeAndBoundsCannotBeExpandedByInput',
    'runtimeIdentityAndRunBoundsRejectMalformedProofInputs',
)
SIGNER = 'a' * 64
CAPTURE_NAMES = ('request-v1.json', 'actual-child-v1.json', 'started-v1.json', 'result-v1.json',
                 'public-result-v1.json', 'sources-before-v1.json', 'sources-after-v1.json',
                 'owner-stdout-v1.bin', 'owner-stderr-v1.bin')
REVIEW_NAMES = ('result-v1.json', 'jvm-roster-v1.json',
                'signer-product-result-v1.json', 'signer-product-stdout-v1.bin',
                'signer-test-result-v1.json', 'signer-test-stdout-v1.bin',
                'signer-controller-result-v1.json', 'signer-controller-stdout-v1.bin')


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class BuildGraph:
    def __init__(self, build):
        self.build = build
        self.base = Path(tempfile.mkdtemp(prefix='locallore-sdk9-build-'))
        assert self.base.drive.upper() == 'D:'
        self.root, self.capture, self.review = (self.base / name for name in ('product', 'capture', 'review'))
        self.root.mkdir()
        self.spec = dict(root=self.root, capture=self.capture, review=self.review,
                         manifest_path=self.base / 'build-v1.json', shared=tuple(build._SPEC['shared']))
        self.write(self.root / '.gitignore', 'apps/android/app/build-presentation-process/\napps/android/presentation-process-controller/build/\n')
        self.write(self.root / '.gitattributes', '* -text\n')
        self.write(self.root / 'scripts/check.py', '# inert synthetic source; never executed\n')
        self.write(self.root / 'apps/android/gradle/wrapper/gradle-wrapper.jar', b'inert wrapper source bytes')
        self.proof_source = self.root / 'apps/android/app/src/test/java/org/locallore/app/PresentationProcessProofTest.kt'
        self.write(self.proof_source, 'class PresentationProcessProofTest {\n' +
                   ''.join('@Test fun ' + method + '() {}\n' for method in METHODS) + '}\n')
        for relative in self.spec['shared']:
            self.write(self.root / relative, (build.LAUNCH_ROOT / relative).read_bytes())
        hooks = self.base / 'empty-hooks'
        hooks.mkdir()
        self.git_prefix = ['git', '-c', 'core.hooksPath=' + str(hooks),
                           '-c', 'user.name=Synthetic Fixture', '-c', 'user.email=fixture@example.invalid',
                           '-C', str(self.root)]
        self.git('init', '-q')
        self.git('add', '--all')
        self.git('commit', '-q', '-m', 'Synthetic fixed build inputs')
        self.spec['head'] = self.git('rev-parse', 'HEAD').decode().strip()
        names = self.git('ls-files', '-z').decode().split('\0')[:-1]
        self.sources = {name: pin(self.root / name)['sha256'] for name in names}
        self.spec['source_count'] = len(self.sources)
        self.tool_paths = [self.base / 'tools' / name for name in
                           ('python.exe', 'java.exe', 'apksigner.jar', 'rustc.exe', 'cargo.exe', 'aapt2.exe', 'runtime.dll')]
        for path in self.tool_paths:
            self.write(path, b'INERT SYNTHETIC TOOL; NEVER EXECUTED ' + path.name.encode())
        self.spec.update(python=str(self.tool_paths[0]), java=str(self.tool_paths[1]),
                         signer_jar=str(self.tool_paths[2]), tools=tuple(pin(path) for path in self.tool_paths))
        self.apks = {
            'product_apk': self.root / 'apps/android/app/build-presentation-process/outputs/apk/debug/app-debug.apk',
            'test_apk': self.root / 'apps/android/app/build-presentation-process/outputs/apk/androidTest/debug/app-debug-androidTest.apk',
            'controller_apk': self.root / 'apps/android/presentation-process-controller/build/outputs/apk/debug/presentation-process-controller-debug.apk',
        }
        for role, path in self.apks.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if role == 'product_apk':
                generated = apk_f.ApkAuditTests().archive(path.parent)
                generated.rename(path)
            else:
                with zipfile.ZipFile(path, 'x') as archive:
                    archive.writestr('AndroidManifest.xml', b'SYNTHETIC compiled manifest ' + role.encode())
                    archive.writestr('classes.dex', b'SYNTHETIC retained byte identity ' + role.encode())
        self.spec['apks'] = {role: pin(path) for role, path in self.apks.items()}
        self.reports = self.root / 'apps/android/app/build-presentation-process/test-results/testDebugUnitTest'
        self.roster = []
        self.xml('org.locallore.app.PresentationProcessProofTest', METHODS)
        for index in range(47):
            self.xml('synthetic.Suite%02d' % index, tuple('case%02d' % n for n in range(9 if index < 35 else 8)))
        assert len(self.roster) == 417
        for module, issues in (
                ('app/build-presentation-process', (('GradleDependency', 'Warning'), ('AutoboxingStateCreation', 'Hint'))),
                ('presentation-process-controller/build', (('DataExtractionRules', 'Warning'), ('MissingApplicationIcon', 'Warning')))):
            document = ET.Element('issues')
            for identity, severity in issues:
                ET.SubElement(document, 'issue', id=identity, severity=severity)
            self.write(self.root / ('apps/android/' + module + '/reports/lint-results-debug.xml'), ET.tostring(document))
        self.commands = self.command_vectors()
        self.gradle_lines = ['> Task ' + task for task in (
            ':app:buildRustAndroid', ':app:testDebugUnitTest', ':app:lintDebug', ':app:compileDebugAndroidTestKotlin',
            ':presentation-process-controller:assembleDebug', ':presentation-process-controller:lintDebug')]
        self.gradle_lines += ['Building LocalLore Rust JNI: x86_64-linux-android -> x86_64',
                              'Building LocalLore Rust JNI: aarch64-linux-android -> arm64-v8a', 'BUILD SUCCESSFUL in 1s']
        identity = lambda role: {name: self.spec['apks'][role][name] for name in ('bytes', 'sha256')}
        self.audits = [
            dict(status='passed', permissions=[f.APP + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'],
                 libraries=[dict(entry='lib/' + abi + '/' + library, elf_load_alignment=[16384])
                            for abi in ('arm64-v8a', 'x86_64')
                            for library in ('liblocallore_android.so', 'libandroidx.graphics.path.so')]),
            dict(status='passed', package=f.APP, test_package=f.TEST, test_permissions=['android.permission.REORDER_TASKS'],
                 certificate_sha256=SIGNER, app=identity('product_apk'), test=identity('test_apk')),
            dict(version=1, scope='locallore_presentation_process_controller_apk_audit_v1', status='passed',
                 package=f.CONTROL, target=f.CONTROL, instrumentation=f.COMPONENT.split('/')[1],
                 min_sdk=26, target_sdk=36, permissions=[], components=0, zip_entries=5,
                 apk_sha256=self.spec['apks']['controller_apk']['sha256']),
        ]
        self.request = dict(version=1, scope='actual reviewed public four-command presentation-process pipeline',
                            head=self.spec['head'], owner_seconds=900,
                            command=[self.spec['python'], '-I', '-S', '-B', str(self.root / 'scripts/check.py'),
                                     'android', '--presentation-process-verification', '--offline'],
                            tools=list(self.spec['tools']), signing_values_logged=False,
                            signing_property_names=sorted('android.injected.signing.' + key for key in
                                                          ('store.file', 'store.password', 'key.alias', 'key.password')))
        self.actual_child = dict(pid=111, creation_filetime=123456, executable=self.spec['python'])
        self.owner = dict(status='child_exited', worker_returncode=0, cleanup_complete=True,
                          output_capture_complete=True, elapsed_ms=1000)
        self.public = dict(returncode=0, elapsed_ms=900)
        self.closed = dict(passed=True, elapsed_ms=1, hashed_bytes=100000, hashed_files=self.spec['source_count'] + 70,
            summary=dict(head=self.spec['head'], source_files=self.spec['source_count'],
            JVM_tests=417, JVM_XML=48, new_JVM_methods=sorted(METHODS), failures=0, errors=0, skips=0,
            common_certificate_sha256=SIGNER, public_commands=copy.deepcopy(self.commands),
            owner_elapsed_ms=1000, public_elapsed_ms=900,
            APKs={short: self.spec['apks'][role] for role, short in zip(self.apks, ('product', 'test', 'controller'))},
            lint={'app': [dict(id='GradleDependency', severity='Warning', count=1),
                          dict(id='AutoboxingStateCreation', severity='Hint', count=1)],
                  'controller': [dict(id='DataExtractionRules', severity='Warning', count=1),
                                 dict(id='MissingApplicationIcon', severity='Warning', count=1)]},
            limits=['Synthetic host graph only.', 'No Android execution.', 'No model or lifecycle qualification.'],
            pipeline_exit_attribution='One successful unmodified public runner plus four command headers/three successful audit outputs; no separate per-command RC receipts invented.'))
        self.signer_outputs = {role: 'Number of signers: 1\nSigner #1 certificate SHA-256 digest: ' + SIGNER + '\n'
                               for role in self.apks}
        self.publish()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode() if isinstance(value, str) else value)

    def git(self, *args):
        return subprocess.check_output(self.git_prefix + list(args), timeout=15, stderr=subprocess.STDOUT)

    def xml(self, classname, methods):
        suite = ET.Element('testsuite', name=classname, tests=str(len(methods)), failures='0', errors='0', skipped='0')
        for name in methods:
            ET.SubElement(suite, 'testcase', classname=classname, name=name)
            self.roster.append(dict(classname=classname, name=name))
        self.write(self.reports / ('TEST-' + classname + '.xml'), ET.tostring(suite))

    def command_vectors(self):
        app, test, control = (str(self.apks[role]) for role in ('product_apk', 'test_apk', 'controller_apk'))
        return [[self.spec['java'], '-classpath', str(self.root / 'apps/android/gradle/wrapper/gradle-wrapper.jar'),
                 'org.gradle.wrapper.GradleWrapperMain', ':app:assembleDebug', ':app:assembleDebugAndroidTest',
                 ':app:testDebugUnitTest', ':app:lintDebug', '--no-daemon', '--console=plain',
                 '-Pandroid.builder.sdkDownload=false', ':presentation-process-controller:assembleDebug',
                 ':presentation-process-controller:lintDebug', '-PlocalLoreInputDraftVerification=true',
                 '-PlocalLorePresentationProcessVerification=true', '--project-cache-dir',
                 '.gradle-presentation-process', '--offline'],
                [self.spec['python'], str(self.root / 'scripts/audit_apk.py'), app, '--presentation-process-verification'],
                [self.spec['python'], str(self.root / 'scripts/audit_instrumentation_apk.py'), app, test, '--presentation-process-verification'],
                [self.spec['python'], str(self.root / 'scripts/audit_process_controller.py'), control, '--presentation-process-verification']]

    def publish(self):
        for phase in ('before', 'after'):
            self.write(self.capture / ('sources-' + phase + '-v1.json'), encoded(self.sources))
        self.request['sources'] = pin(self.capture / 'sources-before-v1.json')
        self.write(self.capture / 'request-v1.json', encoded(self.request))
        self.write(self.capture / 'actual-child-v1.json', encoded(self.actual_child))
        self.write(self.capture / 'started-v1.json', encoded(dict(worker=self.actual_child, request=pin(self.capture / 'request-v1.json'))))
        lines = ['+ ' + repr(self.commands[0]), *self.gradle_lines]
        for command, audit in zip(self.commands[1:], self.audits):
            lines.extend(('+ ' + repr(command), json.dumps(audit, sort_keys=True)))
        stdout = ('\n'.join(lines) + '\n').encode()
        self.write(self.capture / 'owner-stdout-v1.bin', stdout)
        self.write(self.capture / 'owner-stderr-v1.bin', b'')
        self.owner.update(stdout_bytes=len(stdout), stderr_bytes=0)
        self.write(self.capture / 'result-v1.json', encoded(dict(version=1, passed=True, feature_acceptance=False,
                   sources_equal=True, tools_equal=True, owner=self.owner)))
        self.write(self.capture / 'public-result-v1.json', encoded(self.public))
        self.write(self.review / 'jvm-roster-v1.json', encoded(self.roster))
        signers = []
        for role, short in zip(('product_apk', 'test_apk', 'controller_apk'), ('product', 'test', 'controller')):
            output = self.review / ('signer-' + short + '-stdout-v1.bin')
            self.write(output, self.signer_outputs[role])
            record = dict(
                role=short, command=[self.spec['java'], '-jar', self.spec['signer_jar'], 'verify', '--verbose', '--print-certs',
                                     str(self.apks[role])], status='completed', returncode=0, cleanup_complete=True,
                elapsed_ms=1, stderr_bytes=0, stdout=pin(output))
            self.write(self.review / ('signer-' + short + '-result-v1.json'), encoded(record))
            signers.append(dict(record, certificate_sha256=SIGNER))
        self.closed['summary']['static_signer_checks'] = signers
        self.write(self.review / 'result-v1.json', encoded(self.closed))
        self.spec['capture_pins'] = {name: pin(self.capture / name) for name in CAPTURE_NAMES}
        self.spec['review_pins'] = {name: pin(self.review / name) for name in REVIEW_NAMES}

    def artifacts(self, build=None):
        return dict(build=pin(self.spec['manifest_path']), **copy.deepcopy(self.spec['apks']))

    @contextmanager
    def inputs(self, build):
        with patch.object(build, '_SPEC', self.spec):
            yield

    def admission(self):
        from benchmarks import owned_presentation_process_contract as contract
        with self.inputs(self.build):
            if not self.spec['manifest_path'].exists():
                self.build.create_manifest()
        value = f.admission(contract)
        value['artifacts'] = self.artifacts()
        return value
