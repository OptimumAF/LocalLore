"""Independent file-audit and synthetic closed-plan boundary tests.

No SDK, socket, former process, model or credential operation is executed.
The plan fixture exercises real metadata contracts, not an execution verdict.
"""
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import closed_validation_profile as p
from scripts.tests import test_owned_restart_contract as f


def directory():
    return Path(tempfile.mkdtemp(prefix='locallore-closed-profile-boundary-', dir='D:/Dev/_Temp')).resolve(strict=True)


class PlanFixture:
    """Original synthetic provenance plus actual bound contract-shaped files."""
    def __init__(self):
        self.g = g = f.ClosedRestartGraph()
        self.base = g.base
        self.launch = g.base / 'controller-parent'
        g.admission = g.save(g.base / 'target-admission-v2.json', g.a)
        g.d['admission'] = g.admission
        g.running = g.save(g.running['path'], g.d)
        g.s.update(admission=g.admission, running=g.running, descriptor=g.d)
        caller = copy.deepcopy(g.d['worker'])
        caller.update(pid=8102, creation_filetime=108102)
        g.s['caller'] = caller
        self.session = g.save(g.session['path'], g.s)
        operation = dict(argv=['cmd', 'package', 'list', 'packages', '-U', '--user', '0', p.contract.TEST], stdin=None)
        digest = p.contract.operation_digest(operation)
        proofs = {}
        for phase in ('before', 'after'):
            value = f.proof(g.s, after=phase == 'after')
            value['session'] = self.session
            value['context'] = dict(index=55, phase=phase, label='package', operation_sha256=digest, transport_id=g.d['transport_id'])
            path = g.sdk / 'proofs' / ('command-0055-' + phase + '.json')
            value['queries'] = g.save(path.with_name(path.stem + '-queries-v1.json'), f.query_bundle(g.s))
            proofs[phase] = g.save(path, value)
        self.record = dict(version=5, protocol=p.contract.SDK_PROTOCOL, session=self.session, index=55,
            label='package', operation=operation, operation_sha256=digest, transport_id=g.d['transport_id'],
            status='completed', returncode=0, cleanup_complete=True, elapsed_ms=7932, effective_deadline_ms=7872,
            stdout=g.save(g.sdk / 'clients/command-0055.stdout.bin', b'package:synthetic uid:10422\n'),
            stderr=g.save(g.sdk / 'clients/command-0055.stderr.bin', b''), stdin_sha256=None, stdin_bytes=0,
            stdin_complete=True, server_before=proofs['before'], server_after=proofs['after'],
            client_qualified=False, socket_closed=True, sender_joined=True, input_closed=True)
        self.client = g.save(g.sdk / 'clients/command-0055.json', self.record)
        self.controller = dict(version=1, protocol='original-author-restart-controller-v1',
            request=f.f.pin(g.sdk / 'request-v1.json'), session=self.session, prerequisite=None,
            restart_instrumentation=None, boot_final=None, restart_proof=None,
            restart_artifacts={name: None for name in ('workspace-before-v1.json', 'recover-v1.json', 'snapshot-v1.json',
                'retry-v1.json', 'workspace-after-v1.json', 'archive-v1.json')}, client_count=55,
            outcome='refused', phase='death', reason='resource_uncertain', observer_handles_closed=True,
            feature_acceptance=False, elapsed_ms=1223032)
        result = g.save(g.sdk / 'controller-result-v1.json', self.controller)
        self.owner1 = dict(status='child_exited', worker_returncode=1, cleanup_complete=True,
            output_capture_complete=True, elapsed_ms=1248240, stdout_bytes=0, stderr_bytes=0)
        request = g.save(self.launch / 'launch-request-v1.json', dict(admission=g.admission, running=g.running,
            controller_root=str(g.sdk)))
        self.started = dict(request=request, worker=caller)
        started = g.save(self.launch / 'started-v1.json', self.started)
        g.save(self.launch / 'owner-result-v1.json', self.owner1)
        self.launch_value = dict(started=started, request=request, controller_result=result, passed=False,
            process_handles_closed=True, sources_equal=True, owner=self.owner1)
        launch = g.save(self.launch / 'launch-result-v1.json', self.launch_value)
        target_request = g.save(g.root / 'request-v1.json', dict(owner=g.d['owner']))
        self.target_started = dict(request=target_request, worker=copy.deepcopy(g.d['worker']))
        target_started = g.save(g.root / 'started-v1.json', self.target_started)
        owner0 = dict(self.owner1, worker_returncode=0)
        target_owner = g.save(g.root / 'owner-result-v1.json', owner0)
        target_worker = g.save(g.root / 'worker-result-v1.json', dict(worker=g.d['worker'], reason='stop_requested',
            stop_requested=True, cleanup={key: True for key in p.contract.CLEANUP_KEYS}))
        self.target_value = dict(admission=g.admission, started=target_started, request=target_request,
            qualified_target=True, reason='stop_requested', owner=target_owner, worker_result=target_worker)
        target = g.save(g.root / 'result-v1.json', self.target_value)
        self.plan = dict(version=1, scope=p.SCOPE, admission=g.admission, running=g.running, session=self.session,
            client=self.client, controller_launch=launch, controller_started=started,
            target_result=target, target_started=target_started, controller_result=result)

    def rewrite(self, role, value):
        self.plan[role] = self.g.save(self.plan[role]['path'], value)


def inventory_worker_fixture(mutation):
    """Existing ordinary synthetic inventory; never an executable SDK/model."""
    g = f.ClosedRestartGraph()
    sdk = g.base / 'synthetic-sdk'
    tools = []
    for old in g.a['server']['tools']:
        name = Path(old['path']).name
        data = b'synthetic tool data, never executed\n'
        if name == 'adb.exe':
            data += b'ADB_USB\0ADB_EMU\0ADB_MDNS\0'
        tools.append(g.save(sdk / 'platform-tools' / name, data))
    tools.sort(key=lambda item: item['path'])
    g.a['server']['tools'] = tools
    g.a['server']['adb'] = next(item for item in tools if Path(item['path']).name == 'adb.exe')
    g.a['server']['source_review'] = g.save(g.base / 'source-review.md', b'Original synthetic metadata only.\n')
    g.a['compatibility'] = g.save(g.base / 'compatibility.md', b'Original synthetic compatibility metadata.\n')
    g.a['guest'].update(
        proposal=g.save(g.base / 'guest-run-proposal.json', {}),
        authorization=g.save(g.base / 'guest-run-authorization.json', {}),
        emulator=g.save(sdk / 'emulator/emulator.exe', b'synthetic, not executable'),
        qemu=g.save(sdk / 'emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe', b'synthetic, not executable'),
        refuser=g.save(g.base / 'deny-adb-client.exe', b'synthetic, not executable'),
        refuser_source=p.env.binding(p.ROOT / 'benchmarks/native/deny_adb_client.c'))
    g.a['artifacts']['probe'] = p.env.binding(p.ROOT / 'benchmarks/fixtures/physical_model_probe_v1.txt')
    caproot = g.base / 'offline-capabilities'
    outputs = [g.save(caproot / 'command-01.stdout.bin', b'Android Debug Bridge version 1.0.41\nVersion 37.0.1-15733141\n'),
        g.save(caproot / 'command-02.stdout.bin', b'-L SOCKET server nodaemon ADB_LOCAL_TRANSPORT_MAX_PORT ADB_MDNS_AUTO_CONNECT\n')]
    watched = outputs[0]
    if mutation == 'alias':
        watched = g.save(g.base / 'harmless-secret-alias.bin', b'ordinary synthetic marker, no credentials/model')
        outputs[0] = watched
    elif mutation == 'bool_bytes':
        outputs[0] = dict(outputs[0], bytes=False)
    elif mutation == 'declared_overcap':
        outputs[0] = dict(outputs[0], bytes=p.CAP + 1)
    elif mutation == 'actual_overcap':
        Path(outputs[0]['path']).write_bytes(b'x' * (p.CAP + 1))
    else:
        raise AssertionError('unknown synthetic mutation')
    rows = [dict(index=index, argv=[g.a['server']['adb']['path'], command],
        owner=dict(status='completed', elapsed_ms=1, returncode=0, cleanup_complete=True, stderr_bytes=0),
        stdout=output) for index, command, output in zip((1, 2), ('version', 'help'), outputs)]
    g.a['server']['capabilities'] = g.save(caproot / 'result-v1.json', dict(version=1, passed=True,
        offline_CLI_calls=2, server_requests=0, device_calls=0, sources_equal=True, rows=rows))
    g.d = f.running(g.a)
    g.s = f.session(g.a)
    g.s['root'] = str(g.sdk)
    # Supply a constructed data fixture; no validator verdict is replaced.
    with patch.object(f, 'ClosedRestartGraph', return_value=g):
        fixture = PlanFixture()
    return fixture, watched


@unittest.skipUnless(os.name == 'nt', 'physical D file-audit fixtures')
class ReadObserverTests(unittest.TestCase):
    def observed(self):
        value = p.ReadObserver()
        sys.addaudithook(value.event)
        return value

    def test_real_reads_count_declared_file_size_per_open_not_actual_read_bytes(self):
        path = directory() / 'ordinary.txt'
        path.write_bytes(b'original-data')
        pin = p.env.binding(path)
        observer = self.observed()
        with observer.observe({str(path): pin}):
            with path.open('rb') as stream:
                self.assertEqual(stream.read(1), b'o')
            self.assertEqual(path.read_bytes(), b'original-data')
        result = observer.snapshot()
        self.assertEqual(result['read_open_calls'], 2)
        self.assertEqual(result['declared_size_times_opens'], 2 * pin['bytes'])
        self.assertFalse(result['actual_OS_bytes_measured'])

    def test_real_unknown_read_and_real_write_are_denied_without_changing_files(self):
        path = directory() / 'ordinary.txt'
        path.write_bytes(b'preserve')
        observer = self.observed()
        with observer.observe({}):
            with self.assertRaises(ValueError):
                path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'observer_failed'):
            observer.snapshot()
        observer = self.observed()
        with observer.observe({str(path): p.env.binding(path)}):
            with self.assertRaises(ValueError):
                path.open('wb')
        self.assertEqual(path.read_bytes(), b'preserve')
        with self.assertRaisesRegex(ValueError, 'observer_failed'):
            observer.snapshot()

    def test_caught_violation_permanently_invalidates_observer_even_on_reentry(self):
        observer = self.observed()
        with observer.observe({}):
            with self.assertRaises(ValueError):
                observer.event('open', ('D:\\Unadmitted\\file.txt', 'r', 0))
        with self.assertRaisesRegex(ValueError, 'observer_failed'):
            observer.snapshot()
        with self.assertRaises(ValueError):
            with observer.observe({}):
                pass

    def test_successful_observer_can_be_reused_with_fresh_counts(self):
        path = directory() / 'ordinary.txt'
        path.write_bytes(b'hello')
        pin = p.env.binding(path)
        observer = self.observed()
        for expected in (1, 2):
            with observer.observe({str(path): pin}):
                for _ in range(expected):
                    path.read_bytes()
            self.assertEqual(observer.snapshot()['read_open_calls'], expected)

    def test_readonly_installed_C_python_is_allowed_only_when_explicitly_declared(self):
        path = Path(sys.executable)
        self.assertEqual(path.drive.upper(), 'C:')
        pin = p.env.binding(path)
        observer = self.observed()
        with observer.observe({str(path): pin}):
            with path.open('rb') as stream:
                self.assertEqual(stream.read(2), b'MZ')
        self.assertEqual(observer.snapshot()['read_open_calls'], 1)
        observer = self.observed()
        with observer.observe({}):
            with self.assertRaises(ValueError):
                path.open('rb')
        self.assertTrue(observer.violation)

    def test_socket_and_process_audit_families_are_denied_without_native_calls(self):
        events = ('socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo',
            'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.posix_spawnp',
            'os.startfile', 'os.startfile/2', 'os.fork', 'os.forkpty')
        for event in events:
            with self.subTest(event=event):
                observer = p.ReadObserver()
                with observer.observe({}):
                    with self.assertRaises(ValueError):
                        observer.event(event, ())  # Only a synthetic audit event, never the API.
                self.assertTrue(observer.violation)

    def test_invalid_open_shapes_and_write_modes_are_denied(self):
        path = directory() / 'file.txt'
        path.write_bytes(b'x')
        pin = p.env.binding(path)
        variants = ((1, 'r', 0), (b'D:\\file.txt', 'r', 0), ('relative.txt', 'r', 0),
            (str(path), 'r+', 0), (str(path), 'w', 0), (str(path), None, os.O_CREAT),
            (str(path), None, os.O_RDWR), (str(path), 'r', True))
        for args in variants:
            with self.subTest(args=args):
                observer = p.ReadObserver()
                with observer.observe({str(path): pin}):
                    with self.assertRaises(ValueError):
                        observer.event('open', args)
                self.assertTrue(observer.violation)

    def test_snapshot_and_nested_observation_are_refused_while_active(self):
        observer = p.ReadObserver()
        with observer.observe({}):
            with self.assertRaises(ValueError):
                observer.snapshot()
            with self.assertRaises(ValueError):
                with observer.observe({}):
                    pass


@unittest.skipUnless(os.name == 'nt', 'physical D original closed-plan fixtures')
class ProfilePlanTests(unittest.TestCase):
    def test_nested_canonical_query_pin_is_strict_and_bounded_before_hashing(self):
        for mutation in ('extra_field', 'bool_bytes', 'float_bytes', 'declared_overcap', 'actual_overcap'):
            with self.subTest(mutation=mutation):
                fixture = PlanFixture()
                proof_pin = fixture.record['server_before']
                proof = p.env.read_json(proof_pin['path'])
                query = copy.deepcopy(proof['queries'])
                query_path = Path(query['path'])
                if mutation == 'extra_field':
                    query['extra'] = True
                elif mutation == 'bool_bytes':
                    query['bytes'] = False
                elif mutation == 'float_bytes':
                    query['bytes'] = float(query['bytes'])
                elif mutation == 'declared_overcap':
                    query['bytes'] = p.CAP + 1
                else:
                    # Stale small pin, harmless synthetic oversized JSON-name data.
                    # A bounded read or a before-open size refusal is acceptable.
                    query_path.write_bytes(b'x' * (p.CAP + 1))
                proof['queries'] = query
                fixture.record['server_before'] = fixture.g.save(proof_pin['path'], proof)
                fixture.rewrite('client', fixture.record)
                actual_hash, actual_open = p.env.binding, io.open
                def guarded_hash(path):
                    if Path(path) == query_path:
                        raise AssertionError('nested query must not use unbounded env.binding hashing')
                    return actual_hash(path)
                owner = self
                class BoundedRead:
                    def __init__(self, stream):
                        self.stream = stream
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        self.stream.close()
                    def read(self, size=-1):
                        owner.assertGreaterEqual(size, 0, 'no unbounded metadata read')
                        owner.assertLessEqual(size, p.CAP + 1, 'metadata read exceeds CAP+1')
                        return self.stream.read(size)
                    def __getattr__(self, name):
                        return getattr(self.stream, name)
                def guarded_open(path, *args, **kwargs):
                    if Path(path) == query_path:
                        if mutation != 'actual_overcap':
                            raise AssertionError('malformed nested pin must refuse before query open')
                        return BoundedRead(actual_open(path, *args, **kwargs))
                    return actual_open(path, *args, **kwargs)
                with patch.object(p.env, 'binding', side_effect=guarded_hash), patch.object(io, 'open', side_effect=guarded_open):
                    with self.assertRaises(ValueError):
                        p.prepare(fixture.plan)

    def test_terminal_stream_and_elapsed_counters_require_integers(self):
        baseline = dict(status='child_exited', worker_returncode=1, cleanup_complete=True,
            output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
        for field, values in (('stdout_bytes', (False, 0.0)), ('stderr_bytes', (False, 0.0)),
                              ('elapsed_ms', (False, 1.0))):
            for value in values:
                with self.subTest(field=field, value=value):
                    changed = dict(baseline, **{field: value})
                    with self.assertRaises(ValueError):
                        p.terminal(changed, 1)

    def test_noncanonical_proof_alias_refuses_before_reading_alias(self):
        for phase in ('before', 'after'):
            with self.subTest(phase=phase):
                fixture = PlanFixture()
                original = fixture.record['server_' + phase]
                value = p.env.read_json(original['path'])
                alias = fixture.g.save(fixture.base / ('borrowed-' + phase + '-proof.json'), value)
                fixture.record['server_' + phase] = alias
                fixture.rewrite('client', fixture.record)
                actual_read = p.read
                def guarded(binding):
                    if binding['path'] == alias['path']:
                        raise AssertionError('noncanonical proof must not be read')
                    return actual_read(binding)
                with patch.object(p, 'read', side_effect=guarded):
                    with self.assertRaises(ValueError):
                        p.prepare(fixture.plan)

    def test_noncanonical_queries_alias_refuses_before_reading_or_hashing_alias(self):
        for phase, name in (('before', 'borrowed-queries.json'), ('after', 'adbkey')):
            with self.subTest(phase=phase, name=name):
                fixture = PlanFixture()
                original = fixture.record['server_' + phase]
                value = p.env.read_json(original['path'])
                # A harmless synthetic JSON query bundle, never genuine key/model bytes.
                alias = fixture.g.save(fixture.base / name, p.env.read_json(value['queries']['path']))
                value['queries'] = alias
                fixture.record['server_' + phase] = fixture.g.save(original['path'], value)
                fixture.rewrite('client', fixture.record)
                actual_read, actual_hash = p.read, p.env.binding
                def guarded_read(binding):
                    if binding['path'] == alias['path']:
                        raise AssertionError('noncanonical queries must not be read')
                    return actual_read(binding)
                def guarded_hash(path):
                    if Path(path) == Path(alias['path']):
                        raise AssertionError('noncanonical queries must not be hashed')
                    return actual_hash(path)
                with patch.object(p, 'read', side_effect=guarded_read), patch.object(p.env, 'binding', side_effect=guarded_hash):
                    with self.assertRaises(ValueError):
                        p.prepare(fixture.plan)

    def test_real_metadata_prepare_joins_independent_started_workers_and_bound_proofs(self):
        fixture = PlanFixture()
        case = p.prepare(fixture.plan)
        self.assertEqual(case['caller'], fixture.started['worker'])
        self.assertNotEqual(case['caller'], fixture.target_started['worker'])
        self.assertEqual(set(case['proofs']), {'before', 'after'})
        self.assertFalse(fixture.record['client_qualified'])
        for phase in ('proof_before', 'proof_after', 'controller_refusal'):
            expected = 'refused_capability' if phase == 'controller_refusal' else 'returned'
            self.assertEqual(p.action(phase, fixture.plan, case), expected)
        # This is synthetic closed metadata, never an observed native execution.

    def test_plan_version_shape_and_scope_are_exact(self):
        for change in (lambda x: x.update(version=True), lambda x: x.update(scope='other'),
                       lambda x: x.update(extra=True), lambda x: x.pop('controller_started')):
            fixture = PlanFixture()
            change(fixture.plan)
            with self.assertRaises(ValueError):
                p.prepare(fixture.plan)

    def test_wrong_role_basename_refuses_before_any_role_read(self):
        fixture = PlanFixture()
        fixture.plan['target_started'] = dict(path=str(fixture.base / 'adbkey'), bytes=7, sha256='a' * 64)
        with patch.object(p, 'read', side_effect=AssertionError('no role may be read before basename checks')) as read:
            with self.assertRaises(ValueError):
                p.prepare(fixture.plan)
            read.assert_not_called()

    def test_metadata_pin_and_reader_refuse_non_JSON_before_hashing(self):
        path = directory() / 'ordinary.txt'
        path.write_bytes(b'ordinary test data, not credentials')
        binding = p.env.binding(path)
        with patch.object(p.env, 'binding', side_effect=AssertionError('non-JSON must not be hashed')) as hashed:
            with self.assertRaises(ValueError):
                p.pin(path)
            hashed.assert_not_called()
        with patch.object(p.env, 'binding', side_effect=AssertionError('non-JSON must not be hashed')) as hashed:
            with self.assertRaises(ValueError):
                p.read(binding)
            hashed.assert_not_called()

    def test_metadata_size_bound_is_checked_before_hashing(self):
        path = directory() / 'oversized.json'
        path.write_bytes(b'x' * (p.CAP + 1))
        with patch.object(p.env, 'binding', side_effect=AssertionError('oversized input must not be hashed')) as hashed:
            with self.assertRaisesRegex(ValueError, 'metadata_size'):
                p.pin(path)
            hashed.assert_not_called()

    def test_session_caller_cannot_replace_independent_controller_started_identity(self):
        fixture = PlanFixture()
        value = copy.deepcopy(fixture.g.s)
        value['caller']['pid'] += 1
        fixture.rewrite('session', value)
        fixture.controller['session'] = fixture.plan['session']
        fixture.rewrite('controller_result', fixture.controller)
        fixture.launch_value['controller_result'] = fixture.plan['controller_result']
        fixture.rewrite('controller_launch', fixture.launch_value)
        with self.assertRaisesRegex(ValueError, 'caller'):
            p.prepare(fixture.plan)

    def test_target_started_worker_is_bound_to_independent_running_and_terminal(self):
        fixture = PlanFixture()
        changed = copy.deepcopy(fixture.target_started)
        changed['worker']['pid'] += 1
        fixture.rewrite('target_started', changed)
        fixture.target_value['started'] = fixture.plan['target_started']
        fixture.rewrite('target_result', fixture.target_value)
        with self.assertRaisesRegex(ValueError, 'target_closed'):
            p.prepare(fixture.plan)

    def test_completed_controller_substitution_refuses_before_any_deep_action(self):
        fixture = PlanFixture()
        changed = dict(fixture.controller, outcome='completed', phase='completed', reason=None)
        fixture.rewrite('controller_result', changed)
        fixture.launch_value['controller_result'] = fixture.plan['controller_result']
        fixture.rewrite('controller_launch', fixture.launch_value)
        with self.assertRaisesRegex(ValueError, 'refusal_only'):
            p.prepare(fixture.plan)

    def test_same_byte_noncanonical_session_file_is_refused(self):
        fixture = PlanFixture()
        fixture.plan['session'] = fixture.g.save(fixture.base / 'borrowed-session.json', fixture.g.s)
        with self.assertRaisesRegex(ValueError, 'canonical_path'):
            p.prepare(fixture.plan)

    def test_refused_result_does_not_permit_changed_proof_context(self):
        fixture = PlanFixture()
        original = fixture.record['server_before']
        value = p.env.read_json(original['path'])
        value['context']['operation_sha256'] = '0' * 64
        fixture.record['server_before'] = fixture.g.save(original['path'], value)
        fixture.rewrite('client', fixture.record)
        with self.assertRaisesRegex(ValueError, 'proof_caller'):
            p.prepare(fixture.plan)

    def test_terminal_boolean_returncode_is_not_closed_execution(self):
        for code in (True, False, 0.0, 1.0):
            with self.subTest(code=code):
                value = dict(status='child_exited', worker_returncode=code, cleanup_complete=True,
                    output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                with self.assertRaisesRegex(ValueError, 'not_terminal'):
                    p.terminal(value, int(code))

    def test_input_inventory_does_not_follow_model_APK_or_private_key_bindings(self):
        fixture = PlanFixture()
        a = copy.deepcopy(fixture.g.a)
        cap = fixture.g.save(fixture.base / 'capabilities.json', dict(rows=[dict(stdout=fixture.g.save(fixture.base / 'offline.txt', b'fixed offline metadata'))]))
        a['server']['capabilities'] = cap
        ordinary = fixture.g.save(fixture.base / 'ordinary.bin', b'ordinary')
        a['server']['tools'] = [ordinary]
        a['server']['source_review'] = a['compatibility'] = ordinary
        for key in ('proposal', 'authorization', 'emulator', 'qemu', 'refuser', 'refuser_source'):
            a['guest'][key] = ordinary
        a['artifacts']['probe'] = ordinary
        pins = p.input_pins(a)
        for key in ('model', 'product_apk', 'test_apk', 'build', 'process_probe'):
            self.assertNotIn(a['artifacts'][key]['path'], pins)
        self.assertNotIn(a['server']['auth_key'], pins)


@unittest.skipUnless(os.name == 'nt', 'physical D launcher wiring boundaries')
class ProfileLauncherBoundaryTests(unittest.TestCase):
    def test_worker_rejects_capability_output_alias_and_bounds_before_asset_hash(self):
        for mutation in ('alias', 'bool_bytes', 'declared_overcap', 'actual_overcap'):
            with self.subTest(mutation=mutation):
                fixture, watched = inventory_worker_fixture(mutation)
                plan = fixture.g.save(fixture.base / 'profile-plan.json', fixture.plan)
                output = fixture.base / 'profile-worker'
                output.mkdir()
                request = output / 'request-v1.json'
                p.env.create_json(request, dict(version=1, scope='closed-validation-profile-owner-v1',
                    plan=plan, sources=p.sources(), output=str(output), repeat=1, seconds=180))
                actual_check = p.env.check_binding
                touched = []
                def guarded(binding):
                    if binding['path'] == watched['path']:
                        touched.append(binding)
                        raise AssertionError('untrusted capability stdout reached unbounded asset hash')
                    return actual_check(binding)
                with patch.object(p.sys, 'stdin', type('Input', (), {'buffer': io.BytesIO(p.GO)})()), \
                     patch.object(p.env, 'check_binding', side_effect=guarded):
                    with self.assertRaises(ValueError):
                        p.worker(output, p.env.digest(request))
                self.assertEqual(touched, [])

    def test_repeat_bounds_refuse_before_plan_IO_or_supervisor(self):
        for repeat in (True, False, 0, 4, 1.0):
            with self.subTest(repeat=repeat), patch.object(p, 'pin') as read, patch.object(p.env, 'supervise') as owner:
                with self.assertRaisesRegex(ValueError, 'repeat'):
                    p.run('D:\\not-opened.json', '0' * 64, directory() / 'out', repeat)
                read.assert_not_called()
                owner.assert_not_called()

    def test_another_Git_checkout_output_refuses_before_prepare_or_creation(self):
        fixture = PlanFixture()
        plan = fixture.g.save(fixture.base / 'profile-plan.json', fixture.plan)
        repo = fixture.base / 'other-checkout'
        repo.mkdir()
        (repo / '.git').mkdir()
        output = repo / 'capture'
        with patch.object(p, 'prepare', wraps=p.prepare) as prepare, patch.object(p.env, 'supervise', side_effect=AssertionError('native dispatch forbidden')) as owner:
            with self.assertRaises(ValueError):
                p.run(plan['path'], plan['sha256'], output, 1)
        self.assertFalse(output.exists())
        prepare.assert_not_called()
        owner.assert_not_called()

    def test_private_worker_rejects_other_Git_output_before_stdin(self):
        root = directory()
        (root / '.git').mkdir()
        output = root / 'capture'
        output.mkdir()
        with patch.object(p.sys, 'stdin') as stdin:
            stdin.buffer.read.side_effect = AssertionError('stdin must not be consumed')
            with self.assertRaises(ValueError):
                p.worker(output, '0' * 64)
            stdin.buffer.read.assert_not_called()

    def test_private_worker_rejects_C_output_before_stdin(self):
        with patch.object(p.sys, 'stdin') as stdin:
            stdin.buffer.read.side_effect = AssertionError('stdin must not be consumed')
            with self.assertRaises(ValueError):
                p.worker(Path(sys.executable).parent, '0' * 64)
            stdin.buffer.read.assert_not_called()

    def test_private_worker_rejects_source_change_before_prepare(self):
        output = directory()
        value = dict(version=1, scope='closed-validation-profile-owner-v1', plan={}, sources={}, output=str(output), repeat=1, seconds=180)
        request = output / 'request-v1.json'
        p.env.create_json(request, value)
        with patch.object(p.sys, 'stdin', type('Input', (), {'buffer': io.BytesIO(p.GO)})()), \
             patch.object(p, 'sources', return_value={'changed': '1' * 64}), \
             patch.object(p, 'prepare', side_effect=AssertionError('prepare must not run')) as prepare:
            with self.assertRaisesRegex(ValueError, 'source_changed'):
                p.worker(output, p.env.digest(request))
            prepare.assert_not_called()


if __name__ == '__main__':
    unittest.main()
