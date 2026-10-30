"""Canonical byte-backed capture replay tests; no acquisition or human authority.

Only expected installed-runtime metadata is replaced with a tiny D: fixture.
All graph, source, hash, version, roster, proposal and identity readers run.
"""
import ast
import copy
from contextlib import contextmanager, redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import phone_identity_enrollment_io as enrollment_io
from benchmarks import phone_identity_enrollment as enrollment
from benchmarks import adb_device_roster_probe as roster_cli
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_adb_device_roster as roster_fixture
from scripts.tests import test_adb_held_socket as held
from scripts.tests import test_phone_identity_enrollment as pure


class Capture:
    """Original fixed-path file graph, with real pure version/roster reports."""
    def __init__(self, parent, ordinal):
        self.bundle = parent/('bundle-%02d' % ordinal); self.bundle.mkdir()
        self.output = self.bundle/'roster-v1'; self.output.mkdir()
        self.runtime = parent/('runtime-%02d.bin' % ordinal); self.runtime.write_bytes(b'synthetic Python file metadata')
        self.python = dict(executable=env.binding(self.runtime), runtime_dll=None)
        self.sources = roster_cli._source_bindings()
        self.worker = dict(pid=held.CLIENT_PID, creation_filetime=223456789, executable=str(self.runtime))
        self.admitted = roster_fixture.admission()
        env.create_json(self.bundle/'admission-v1.json', self.admitted)
        version_backend = held.FakeBackend()
        roster_backend = roster_fixture.RosterBackend()
        for backend in (version_backend, roster_backend):
            for bracket in backend.brackets: bracket['client'] = copy.deepcopy(self.worker)
        self.version = roster_fixture.legacy.probe(version_backend, held.admission())
        self.report = roster_fixture.roster.probe(roster_backend, self.admitted, self.version)
        if not roster_fixture.roster.report_verified(self.report, self.admitted):
            raise AssertionError('invalid original capture proof')
        self.write('version-report-v1.json', self.version)
        (self.output/'version-bytes-v1.bin').write_bytes(bytes.fromhex(self.version['response_hex']))
        self.write('report-v1.json', self.report)
        self.owner = dict(status='child_exited', worker_returncode=0, cleanup_complete=True,
                         output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
        self.write('owner-result-v1.json', self.owner)
        (self.output/'owner-stdout-v1.bin').write_bytes(b'')
        (self.output/'owner-stderr-v1.bin').write_bytes(b'')
        self.request = dict(version=1, protocol=roster_cli.PROTOCOL, output=str(self.output),
            admission=env.binding(self.bundle/'admission-v1.json'), validated_admission=self.admitted,
            owner_seconds=30, parent=dict(pid=9101, creation_filetime=12345, executable=str(self.runtime)),
            source_closure=self.sources, python=self.python)
        self.write('request-v1.json', self.request)
        self.started = dict(worker=self.worker, request=env.binding(self.output/'request-v1.json'))
        self.write('started-v1.json', self.started)
        for phase in ('before', 'after', 'final'):
            self.write('source-closure-'+phase+'-v1.json', dict(version=1, status='completed', reason=None, bindings=self.sources))
            self.write('python-'+phase+'-v1.json', dict(version=1, status='completed', reason=None, bindings=self.python))
        self.result = dict(version=1, protocol=roster_cli.PROTOCOL, status='observed', reason=None,
            acquisition_completed=True, roster_observed=True, feature_acceptance=False,
            sources_equal=True, python_equal=True, admission=env.binding(self.bundle/'admission-v1.json'),
            request=env.binding(self.output/'request-v1.json'), owner=env.binding(self.output/'owner-result-v1.json'),
            version_report=env.binding(self.output/'version-report-v1.json'),
            version_bytes=env.binding(self.output/'version-bytes-v1.bin'), report=env.binding(self.output/'report-v1.json'),
            worker=env.binding(self.output/'started-v1.json'))
        self.seal()

    def write(self, name, value):
        (self.output/name).write_bytes(env.encoded(value))

    def seal(self):
        self.write('result-v1.json', self.result)
        self.sha = env.digest(self.output/'result-v1.json')

    def rebind(self, name, value):
        if type(value) is bytes: (self.output/name).write_bytes(value)
        else: self.write(name, value)
        field = {'owner-result-v1.json':'owner', 'request-v1.json':'request', 'started-v1.json':'worker',
                 'version-report-v1.json':'version_report', 'version-bytes-v1.bin':'version_bytes',
                 'report-v1.json':'report'}.get(name)
        if name == 'request-v1.json':
            self.started['request'] = env.binding(self.output/name)
            self.write('started-v1.json', self.started)
            self.result['worker'] = env.binding(self.output/'started-v1.json')
        if field: self.result[field] = env.binding(self.output/name)
        self.seal()


class PhoneIdentityEnrollmentIoTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-enrollment-', dir='D:/Dev/_Temp')).resolve()
        self.captures = []

    def capture(self):
        value = Capture(self.base, len(self.captures)); self.captures.append(value)
        return value

    @contextmanager
    def runtime(self, captured):
        with patch.object(roster_cli, '_python_bindings', side_effect=lambda: copy.deepcopy(captured.python)):
            yield

    def prepare_choice(self, captured):
        enrollment_io.prepare(captured.bundle, captured.sha)
        review = captured.bundle/'review-v1'
        proposal = env.read_json(review/'proposal-v1.json')
        proposal_pin = env.binding(review/'proposal-v1.json')
        decision = dict(version=1, protocol='phone-identity-choice-v1', proposal_sha256=proposal_pin['sha256'],
            candidate_id=proposal['candidates'][0]['candidate_id'], action='select_for_read_only_inventory',
            human_choice_recorded=True)
        env.create_json(review/'human-choice-v1.json', decision)
        return review, proposal_pin['sha256'], env.digest(review/'human-choice-v1.json')

    def test_fixed_capture_prepare_explicit_choice_confirm_and_load_replay_real_graph(self):
        captured = self.capture()
        with self.runtime(captured):
            value = enrollment_io.read_capture(captured.bundle, captured.sha)
            self.assertEqual(value['admission'], captured.admitted)
            self.assertEqual(value['report'], captured.report)
            review, proposal_sha, decision_sha = self.prepare_choice(captured)
            self.assertFalse((review/'identity-v1.json').exists())
            enrollment_io.confirm(captured.bundle, proposal_sha, decision_sha)
            identity_pin = env.binding(review/'identity-v1.json')
            identity = enrollment_io.load_identity(captured.bundle, identity_pin['sha256'])
            self.assertEqual(identity['identity'], {'serial': 'ORIGINAL_USB'})
            self.assertFalse(identity['grants_device_actions'])
            self.assertEqual(enrollment.inventory_admission(captured.admitted, identity)['authorized_serial'], 'ORIGINAL_USB')
            before = (review/'identity-v1.json').read_bytes()
            with self.assertRaises((ValueError, OSError)): enrollment_io.confirm(captured.bundle, proposal_sha, decision_sha)
            self.assertEqual((review/'identity-v1.json').read_bytes(), before)

    def test_every_embedded_pin_is_canonical_before_any_foreign_content_read(self):
        for field in ('admission', 'request', 'owner', 'worker', 'report', 'version_report', 'version_bytes'):
            captured = self.capture()
            original = Path(captured.result[field]['path'])
            foreign = self.base/('foreign-%s.bin' % field); foreign.write_bytes(original.read_bytes())
            captured.result[field] = env.binding(foreign); captured.seal()
            opened = []
            raw_open = Path.open
            def guarded_open(path, *args, **kwargs):
                if path == foreign:
                    opened.append(str(path)); raise AssertionError('foreign content read before path refusal')
                return raw_open(path, *args, **kwargs)
            with self.subTest(field=field), self.runtime(captured), patch.object(Path, 'open', new=guarded_open):
                with self.assertRaises(ValueError): enrollment_io.prepare(captured.bundle, captured.sha)
            self.assertEqual(opened, [])
            self.assertFalse((captured.bundle/'review-v1').exists())

    def test_coherently_rebound_owner_worker_sidecar_and_proof_failures_block_publication(self):
        for fault in ('bool_exit', 'bool_stdout', 'cleanup', 'capture', 'worker', 'request', 'raw', 'version', 'roster'):
            captured = self.capture()
            if fault in ('bool_exit', 'bool_stdout', 'cleanup', 'capture'):
                field = {'bool_exit':'worker_returncode', 'bool_stdout':'stdout_bytes',
                         'cleanup':'cleanup_complete', 'capture':'output_capture_complete'}[fault]
                captured.owner[field] = True if fault.startswith('bool') else False
                captured.rebind('owner-result-v1.json', captured.owner)
            elif fault == 'worker':
                captured.started['worker'] = {**captured.worker, 'creation_filetime':223456790}
                captured.rebind('started-v1.json', captured.started)
            elif fault == 'request':
                captured.request['owner_seconds'] = True
                captured.rebind('request-v1.json', captured.request)
            elif fault == 'raw': captured.rebind('version-bytes-v1.bin', b'OKAY0004002a')
            elif fault == 'version':
                bad = copy.deepcopy(captured.version); bad['client_raw_state'] = 14
                captured.rebind('version-report-v1.json', bad)
            else:
                bad = copy.deepcopy(captured.report); bad['rows'][0]['serial'] = 'BORROWED_USB'
                captured.rebind('report-v1.json', bad)
            with self.subTest(fault=fault), self.runtime(captured), self.assertRaises(ValueError):
                enrollment_io.prepare(captured.bundle, captured.sha)
            self.assertFalse((captured.bundle/'review-v1').exists())

    def test_each_source_python_snapshot_and_real_owner_stream_must_match(self):
        for kind in ('source-closure', 'python'):
            for phase in ('before', 'after', 'final'):
                captured = self.capture(); name = kind+'-'+phase+'-v1.json'
                value = env.read_json(captured.output/name)
                value['bindings'] = [] if kind == 'source-closure' else dict(executable=None, runtime_dll=None)
                captured.write(name, value)
                with self.subTest(kind=kind, phase=phase), self.runtime(captured), self.assertRaises(ValueError):
                    enrollment_io.prepare(captured.bundle, captured.sha)
                self.assertFalse((captured.bundle/'review-v1').exists())
        for stream in ('owner-stdout-v1.bin', 'owner-stderr-v1.bin'):
            captured = self.capture(); (captured.output/stream).write_bytes(b'PRIVATE_STREAM_CANARY')
            with self.subTest(stream=stream), self.runtime(captured), self.assertRaises(ValueError):
                enrollment_io.prepare(captured.bundle, captured.sha)

    def test_hardlink_or_reparse_metadata_refuses_before_data_open(self):
        class Metadata:
            def __init__(self, original, fault): self.original, self.fault = original, fault
            def __getattr__(self, name):
                if name == 'st_nlink' and self.fault == 'hardlink': return 2
                if name == 'st_file_attributes' and self.fault == 'reparse': return 0x400
                return getattr(self.original, name)
        for fault in ('hardlink', 'reparse'):
            captured = self.capture(); target = captured.output/'report-v1.json'
            raw_lstat, raw_stat, raw_open = Path.lstat, Path.stat, Path.open
            def lstat(path, *args, **kwargs):
                value = raw_lstat(path, *args, **kwargs)
                return Metadata(value, fault) if path == target else value
            def stat(path, *args, **kwargs):
                value = raw_stat(path, *args, **kwargs)
                return Metadata(value, fault) if path == target else value
            def open_file(path, *args, **kwargs):
                if path == target: raise AssertionError('unsafe file reached data IO')
                return raw_open(path, *args, **kwargs)
            with self.subTest(fault=fault), self.runtime(captured), \
                 patch.object(Path, 'lstat', new=lstat), patch.object(Path, 'stat', new=stat), \
                 patch.object(Path, 'open', new=open_file):
                with self.assertRaises((ValueError, env.EnvironmentRefused)):
                    enrollment_io.prepare(captured.bundle, captured.sha)
            self.assertFalse((captured.bundle/'review-v1').exists())

    def test_existing_or_partial_review_directory_is_preserved_without_retry(self):
        for partial in (False, True):
            captured = self.capture(); review = captured.bundle/'review-v1'; review.mkdir()
            marker = review/('proposal-v1.json' if partial else 'original.txt')
            marker.write_bytes(b'preserved original partial output')
            with self.subTest(partial=partial), self.runtime(captured), self.assertRaises((ValueError, OSError)):
                enrollment_io.prepare(captured.bundle, captured.sha)
            self.assertEqual(marker.read_bytes(), b'preserved original partial output')
            self.assertEqual(list(review.iterdir()), [marker])

    def test_confirm_reconstructs_capture_and_rejects_wrong_choice_without_identity(self):
        for fault in ('proposal_hash', 'candidate', 'scope', 'human', 'capture'):
            captured = self.capture()
            with self.runtime(captured):
                review, proposal_sha, decision_sha = self.prepare_choice(captured)
                decision = env.read_json(review/'human-choice-v1.json')
                if fault == 'proposal_hash': decision['proposal_sha256'] = 'b'*64
                elif fault == 'candidate': decision['candidate_id'] = 'b'*64
                elif fault == 'scope': decision['action'] = 'install'
                elif fault == 'human': decision['human_choice_recorded'] = False
                else:
                    captured.result['acquisition_completed'] = False; captured.seal()
                if fault != 'capture':
                    (review/'human-choice-v1.json').write_bytes(env.encoded(decision))
                    decision_sha = env.digest(review/'human-choice-v1.json')
                with self.subTest(fault=fault), self.assertRaises(ValueError):
                    enrollment_io.confirm(captured.bundle, proposal_sha, decision_sha)
                self.assertFalse((review/'identity-v1.json').exists())

    def test_enrollment_code_pins_cover_actual_transitive_project_imports(self):
        root = Path(enrollment_io.__file__).absolute().parents[1]
        inherited = {Path(binding['path']) for binding in roster_cli._source_bindings()}
        pending = [Path(enrollment.__file__).absolute(), Path(enrollment_io.__file__).absolute()]
        required = set()
        while pending:
            path = pending.pop()
            if path in required or path in inherited: continue
            required.add(path)
            for node in ast.walk(ast.parse(path.read_bytes())):
                if isinstance(node, ast.ImportFrom) and node.module == 'benchmarks':
                    for alias in node.names:
                        dependency = root/'benchmarks'/(alias.name+'.py')
                        if dependency.is_file(): pending.append(dependency)
                elif isinstance(node, ast.ImportFrom) and (node.module or '').startswith('benchmarks.'):
                    dependency = root/Path(node.module.replace('.', '/')+'.py')
                    if dependency.is_file(): pending.append(dependency)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('benchmarks.'):
                            dependency = root/Path(alias.name.replace('.', '/')+'.py')
                            if dependency.is_file(): pending.append(dependency)
        self.assertIn(root/'benchmarks/physical_phone_inventory.py', required)
        declared = {Path(binding['path']) for binding in enrollment_io._code_pins()}
        self.assertTrue(required <= declared, 'current enrollment code pins omit imported project code')

    def test_runtime_change_during_real_publication_refuses_before_success_record(self):
        for operation in ('prepare', 'confirm'):
            captured = self.capture()
            def current_python():
                return dict(executable=env.binding(captured.runtime), runtime_dll=None)
            with patch.object(roster_cli, '_python_bindings', side_effect=current_python):
                if operation == 'confirm': review, proposal_sha, decision_sha = self.prepare_choice(captured)
                else: review = captured.bundle/'review-v1'
                trigger = review/('proposal-v1.json' if operation == 'prepare' else 'identity-v1.json')
                actual_write = enrollment_io._write
                changed = []
                def write_then_change(path, raw):
                    result = actual_write(path, raw)
                    if path == trigger:
                        captured.runtime.write_bytes(b'changed synthetic Python runtime metadata')
                        changed.append(True)
                    return result
                failure = None
                with patch.object(enrollment_io, '_write', side_effect=write_then_change):
                    try:
                        if operation == 'prepare': enrollment_io.prepare(captured.bundle, captured.sha)
                        else: enrollment_io.confirm(captured.bundle, proposal_sha, decision_sha)
                    except (ValueError, OSError, env.EnvironmentRefused) as error:
                        failure = error
                self.assertEqual(changed, [True])
                with self.subTest(operation=operation, boundary='refusal'):
                    self.assertIsNotNone(failure, 'runtime drift during publication must refuse')
                with self.subTest(operation=operation, boundary='success_record'):
                    self.assertFalse((review/(operation+'-result-v1.json')).exists())

    def test_main_missing_bundle_returns_static_refusal_instead_of_escaping(self):
        missing = self.base/'PRIVATE_MISSING_BUNDLE_CANARY'
        stdout, stderr = io.StringIO(), io.StringIO()
        escaped, code = None, None
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = enrollment_io.main(['prepare', '--bundle', str(missing), '--result-sha256', '0'*64])
            except Exception as error:
                escaped = error
        self.assertIsNone(escaped, 'file-only CLI must translate missing bundle to static refusal')
        self.assertEqual(code, 1)
        public = json.loads(stdout.getvalue())
        self.assertEqual(set(public), {'status', 'reason', 'feature_acceptance',
                                      'authority_authenticated', 'grants_device_actions'})
        self.assertEqual(public['status'], 'refused')
        for flag in ('feature_acceptance', 'authority_authenticated', 'grants_device_actions'):
            self.assertIs(public[flag], False)
        self.assertEqual(stderr.getvalue(), '')
        self.assertNotIn('PRIVATE_MISSING_BUNDLE_CANARY', stdout.getvalue())
        self.assertNotIn(str(self.base), stdout.getvalue())


if __name__ == '__main__': unittest.main()
