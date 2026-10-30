"""Byte-backed original SDK6 graphs, not device or human execution evidence.

All graph files are fresh retained D fixtures. Real fixed readers replay every
query/proof/client/claim binding; no verifier or authority verdict is replaced.
"""
import copy
import hashlib
import io
import os
from pathlib import Path, PureWindowsPath
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import android_process_verification_v6 as reader
from benchmarks import owned_live_death_contract as c
from benchmarks import owned_target_contract as legacy
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_owned_restart_contract as prior
from scripts.tests import test_owned_live_death_contract as profile
from scripts.tests import test_original_author_prompt_provenance as original


class ClosedLiveGraph:
    """Two distinct synthetic host processes/sessions and complete bound bytes."""

    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-live-closed-', dir='D:/Dev/_Temp')).resolve()
        self.root, self.sdk = self.base/'owner', self.base/'control'
        self.docs, self.writes = {}, set()
        self.a = profile.admission()
        self.a.update(root=str(self.root), seconds=1700)
        self.a['server'].update(root=str(self.root/'server'), seconds=1700)
        self.a['sources'] = c.source_bindings()
        self.a['server']['sources'] = [copy.deepcopy(pin) for pin in self.a['sources']
            if PureWindowsPath(pin['path']).name in legacy.base.SOURCE_NAMES | {'__init__.py'}]
        dll = Path(sys.executable).with_name('python%d%d.dll' % sys.version_info[:2])
        self.a['python'] = dict(executable=env.binding(Path(sys.executable)),
            runtime_dll=env.binding(dll) if dll.is_file() else None)
        self.a['server']['python'] = copy.deepcopy(self.a['python'])
        self.a['artifacts']['process_probe_source'] = env.binding(
            Path(c.__file__).parent/'native/android_author_process_probe.c')
        self.admission = self.save(self.base/'admission-v1.json', self.a)
        self.d = prior.f.running(self.a); self.d['protocol'] = c.PROTOCOL
        self.d['admission'] = self.admission
        self.running = self.save(self.root/'running-v1.json', self.d)
        self.s = self.session(self.sdk, 7201, 1200, 1800000010.0)
        self.control_pin = self.save(self.sdk/c.SESSION_FILE, self.s)
        self.pending_root = self.sdk/'pending-author-v1'
        self.child = self.session(self.pending_root/'capture-v1', 7202, 240, 1800000020.0)
        self.child_pin = self.save(Path(self.child['root'])/c.SESSION_FILE, self.child)
        self.rows = {self.s['root']: [], self.child['root']: []}
        bundle = original.fixture(original.CURRENT)
        self.authored = original.f.raw(bundle['author'])
        self.author_process = bundle['author']['process']
        self.imported, self.artifacts = bundle['imported'], bundle['artifacts']
        self.uid, self.pid = self.author_process['uid'], self.author_process['pid']
        self.ready_ns = self.author_process['start_elapsed_ms']*1000000 + 1000000000
        self.checkpoint = dict(version=1, protocol='original-author-live-checkpoint-v1',
            package=c.APP, process={**self.author_process, 'start_ticks': 90001},
            author_proof_sha256=self.sha(self.authored), import_proof_sha256=self.sha(self.imported),
            catalog_sha256=self.sha(self.artifacts['workspace-created-v1.json']),
            snapshot_sha256=self.sha(self.artifacts['snapshot-created-v1.json']),
            workspace_open=True, model_owner_closed=True, pending=False,
            ready_elapsed_ns=self.ready_ns, expires_elapsed_ns=self.ready_ns+120000000000)
        self.checkpoint_files = dict(zip(reader.CHECKPOINT_FILES, (
            env.encoded(self.checkpoint), self.artifacts['workspace-created-v1.json'],
            self.artifacts['snapshot-created-v1.json'])))
        pending = self.pending()
        boot = self.add(self.s, [c.PROCESS_PROBE, '--boot'],
                        env.encoded(prior.process_packet(mode='boot')), 'boot-initial')
        imported_call = self.add(self.s, reader.instrument_argv('import'), prior.junit_bytes('import'), 'import')
        imported_pin = self.save(self.sdk/'import-proof/import-v1.json', self.imported)
        self.collection('no_backup/original-author-import-proof-v1', {'import-v1.json': self.imported})
        packages = self.packages()
        ready = self.save(self.sdk/'ready-captured-v1.json', self.checkpoint_files['ready-v1.json'])
        ready_call = self.add(self.s, ['run-as', c.APP, '--user', '0', 'cat', reader.CHECKPOINT_ROOT+'/ready-v1.json'],
                              self.checkpoint_files['ready-v1.json'], 'ready')
        authored_files = {'proof-v1.json': self.authored, **self.artifacts}
        preflight_values = {'no_backup/original-author-proof-v1/'+name: raw for name, raw in authored_files.items()}
        preflight_values.update({reader.CHECKPOINT_ROOT+'/'+name: raw for name, raw in self.checkpoint_files.items()})
        preflight = self.add(self.s, ['run-as', c.APP, '--user', '0', 'tar', '-cf', '-', *reader.preflight_paths()],
                             self.tar(preflight_values), 'preflight')
        preflight_pins = {group: {name: self.save(self.sdk/'live-preflight'/group/name, raw)
                                 for name, raw in values.items()}
                          for group, values in (('author', authored_files), ('checkpoint', self.checkpoint_files))}
        probe = [c.PROCESS_PROBE, '--snapshot-v2', str(self.pid), str(self.uid)]
        before = self.add(self.s, probe, env.encoded(self.packet()), 'alive')
        stopped = self.add(self.s, ['am', 'force-stop', '--user', '0', c.APP], b'', 'force-stop')
        after = self.add(self.s, probe, env.encoded(self.packet('absent', self.ready_ns+2000000000)), 'gone')
        self.checkpoint_list = self.collection(reader.CHECKPOINT_ROOT, self.checkpoint_files)
        self.collection('no_backup/original-author-proof-v1', authored_files)
        self.prerequisite_path = self.root/'restart-prerequisite-v1.json'
        self.save(self.prerequisite_path, dict(version=1, protocol='original-author-live-death-prerequisite-v1',
            admission=self.admission, running=self.running, build=self.a['artifacts']['build'],
            control_session=self.control_pin, author_session=self.child_pin, pending=pending,
            ready=ready, ready_client=ready_call, preflight_client=preflight, preflight_artifacts=preflight_pins,
            checkpoint_artifacts={name: env.binding(self.sdk/'checkpoint-proof'/name) for name in self.checkpoint_files},
            boot_initial=boot, probe_before=before, force_stop=stopped, probe_after=after,
            import_proof=imported_pin, author_proof=env.binding(self.sdk/'author-proof/proof-v1.json'),
            author_artifacts={name: env.binding(self.sdk/'author-proof'/name) for name in self.artifacts},
            import_instrumentation=imported_call, package_checks=packages))

    @staticmethod
    def sha(raw):
        return hashlib.sha256(raw).hexdigest()

    def save(self, path, value):
        path = Path(path).resolve(strict=False)
        if path.drive.upper() != 'D:' or not path.is_relative_to(self.base):
            raise AssertionError('synthetic graph escaped its retained D directory')
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = value if type(value) is bytes else env.encoded(value)
        path.write_bytes(raw); self.writes.add(path)
        if type(value) is dict:
            self.docs[path] = copy.deepcopy(value)
        return env.binding(path)

    def session(self, root, pid, seconds, started):
        value = prior.f.session(self.a)
        value.update(protocol=c.SDK_PROTOCOL, admission=self.admission, running=self.running,
            descriptor=self.d, root=str(root), seconds=seconds, started_epoch=started,
            deadline_epoch=started+seconds,
            caller=dict(pid=pid, creation_filetime=100000+pid, executable=self.a['python']['executable']['path']))
        return value

    def add(self, session, argv, stdout, label):
        rows = self.rows[session['root']]; index = len(rows)+1
        root = Path(session['root']); session_pin = env.binding(root/c.SESSION_FILE)
        operation = dict(argv=copy.deepcopy(argv), stdin=None); digest = c.operation_digest(operation)
        proofs = {}
        for phase in ('before', 'after'):
            proof = prior.f.proof(session, after=phase == 'after')
            proof.update(protocol=c.PROOF_PROTOCOL, session=session_pin)
            proof['context'].update(index=index, label=label, operation_sha256=digest)
            path = root/'proofs'/('command-%04d-%s.json' % (index, phase))
            query = prior.f.query_bundle(session); query['protocol'] = c.PROOF_PROTOCOL
            proof['queries'] = self.save(path.with_name(path.stem+'-queries-v1.json'), query)
            proofs[phase] = self.save(path, proof)
        stem = root/'clients'/('command-%04d' % index)
        value = dict(version=6, protocol=c.SDK_PROTOCOL, session=session_pin, index=index, label=label,
            operation=operation, operation_sha256=digest, transport_id=self.d['transport_id'], status='completed',
            returncode=0, cleanup_complete=True, elapsed_ms=7, effective_deadline_ms=15000,
            stdout=self.save(stem.with_suffix('.stdout.bin'), stdout), stderr=self.save(stem.with_suffix('.stderr.bin'), b''),
            stdin_sha256=None, stdin_bytes=0, stdin_complete=True, server_before=proofs['before'], server_after=proofs['after'],
            client_qualified=True, socket_closed=True, sender_joined=True, input_closed=True)
        pin = self.save(stem.with_suffix('.json'), value); rows.append(pin)
        if argv[:2] == ['am', 'instrument']:
            kind = c.instrumentation_kind(argv)
            self.save(self.root/'claims-v1'/(kind+'-v1.json'), c.claim_record(
                self.admission, session['caller'], kind, digest))
        return pin

    def pending(self):
        request = self.save(self.pending_root/'request-v1.json', dict(version=1,
            protocol='owned-live-author-request-v1', admission=self.admission, running=self.running,
            control_session=self.control_pin, root=str(self.pending_root), sources=self.a['sources'],
            python=self.a['python'], controller=next(p for p in self.a['sources']
            if PureWindowsPath(p['path']).name == 'original_author_live_death_controller.py'), seconds=240, owner_seconds=270))
        started = self.save(self.pending_root/'started-v1.json', dict(request=request, worker=self.child['caller']))
        crash = b'INSTRUMENTATION_RESULT: shortMsg=Process crashed.\nINSTRUMENTATION_CODE: 0\n'
        client = self.add(self.child, reader.instrument_argv('author_live'), crash, 'author-live')
        worker = self.save(self.pending_root/'worker-result-v1.json', dict(version=1,
            protocol='owned-live-author-worker-v1', request=request, session=self.child_pin, client=client,
            client_count=1, outcome='captured', observer_handles_closed=True))
        owner = self.save(self.pending_root/'owner-result-v1.json', dict(status='child_exited', cleanup_complete=True,
            elapsed_ms=60000, worker_returncode=0, stdout_bytes=0, stderr_bytes=0, output_capture_complete=True))
        for channel in ('stdout', 'stderr'):
            self.save(self.pending_root/'worker-output-v1'/('owner-'+channel+'-v1.bin'), b'')
        after = self.save(self.pending_root/'after-v1.json', dict(request=request, worker=self.child['caller'],
            sources=self.a['sources'], python=self.a['python'], process_handles_closed=True))
        return self.save(self.pending_root/'result-v1.json', dict(version=1, protocol='owned-live-author-result-v1',
            request=request, started=started, worker=worker, owner=owner, after=after))

    def packet(self, state='alive', clock=None):
        packet = prior.process_packet(pid=self.pid, uid=self.uid, state=state, boot=prior.BOOT)
        packet.update(version=2, protocol='android-author-process-probe-v2',
                      observed_boottime_ns=self.ready_ns+1000000000 if clock is None else clock)
        return packet

    def packages(self):
        result = {}; prefix = 'package:'+c.APP+' uid:'+str(self.uid)+'\npackage:'+c.TEST+' uid:'+str(self.uid+1)+'\n'
        for kind, package, artifact in (('product', c.APP, 'product_apk'), ('tests', c.TEST, 'test_apk')):
            path = '/data/app/~~synthetic-'+kind+'/base.apk'
            result[kind] = dict(uid=self.add(self.s, ['cmd','package','list','packages','-U','--user','0',package], prefix.encode(), kind+'-uid'),
                path=self.add(self.s, ['cmd','package','path','--user','0',package], ('package:'+path+'\n').encode(), kind+'-path'),
                sha256=self.add(self.s, ['sha256sum',path], (self.a['artifacts'][artifact]['sha256']+'  '+path+'\n').encode(), kind+'-hash'))
        return result

    def tar(self, values):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as packed:
            for name, raw in values.items():
                member = tarfile.TarInfo(name); member.uid = self.uid; member.size = len(raw)
                packed.addfile(member, io.BytesIO(raw))
        return stream.getvalue()

    def collection(self, remote, values):
        local = {'no_backup/original-author-import-proof-v1':'import-proof',
                 'no_backup/original-author-proof-v1':'author-proof', reader.CHECKPOINT_ROOT:'checkpoint-proof'}[remote]
        for name, raw in values.items():
            self.save(self.sdk/local/name, raw)
        directories = ('workspace-v1', 'archive-staging') if local == 'author-proof' else ()
        paths = {remote+'/'+name: raw for name, raw in values.items()}
        prefix = ['run-as', c.APP, '--user', '0']
        listed = self.add(self.s, prefix+['ls', remote], ('\n'.join((*values, *directories))+'\n').encode(), 'list')
        hashes = ''.join(self.sha(raw)+'  '+name+'\n' for name, raw in paths.items()).encode()
        self.add(self.s, prefix+['sha256sum', *paths], hashes, 'hash')
        self.add(self.s, prefix+['tar', '-cf', '-', *paths], self.tar(paths), 'tar')
        self.add(self.s, prefix+['sha256sum', *paths], hashes, 'post-hash')
        return listed

    def rewrite(self, path, value):
        """Recompute all transitive byte bindings for a coherent original attack."""
        queue = [self.save(path, value)]
        while queue:
            pin = queue.pop(0)
            for selected, document in list(self.docs.items()):
                if selected == Path(pin['path']):
                    continue
                changed = prior.ClosedRestartGraph.replace_reference(self, document, pin['path'], pin)
                if changed != document:
                    queue.append(self.save(selected, changed))

    replace_reference = prior.ClosedRestartGraph.replace_reference

    def change_stdout(self, client_pin, raw):
        row = env.read_json(client_pin['path'])
        self.rewrite(row['stdout']['path'], raw)

    def validate(self):
        return reader.verify_restart_prerequisite(env.binding(self.prerequisite_path), self.a,
            self.admission, self.running, self.s['caller'])


@unittest.skipUnless(os.name == 'nt', 'retained physical D synthetic closed graphs')
class LiveDeathClosedReplayTests(unittest.TestCase):
    def refused(self, action):
        with self.assertRaises((ValueError, OSError, env.EnvironmentRefused)):
            action()

    def test_complete_original_graph_replays_both_sessions_without_verdict_stubs(self):
        graph = ClosedLiveGraph(); before = copy.deepcopy(graph.docs)
        selected = graph.validate()
        self.assertEqual(selected, graph.docs[graph.prerequisite_path])
        self.assertEqual(graph.docs, before)
        self.assertEqual(len(graph.rows[graph.s['root']]), 25)
        self.assertEqual(len(graph.rows[graph.child['root']]), 1)
        self.assertNotEqual(graph.s['caller'], graph.child['caller'])
        self.assertTrue(all(path.drive.upper() == 'D:' and path.is_relative_to(graph.base) for path in graph.writes))
        selected['ready']['sha256'] = '0'*64
        self.assertNotEqual(selected, graph.docs[graph.prerequisite_path])

    def test_child_session_cannot_precede_the_control_session_that_created_it(self):
        graph = ClosedLiveGraph()
        changed = copy.deepcopy(graph.child)
        changed.update(started_epoch=1800000001.0, deadline_epoch=1800000241.0)
        graph.rewrite(Path(graph.child['root'])/c.SESSION_FILE, changed)
        self.refused(graph.validate)

    def test_foreign_ready_role_is_refused_before_any_foreign_file_open(self):
        graph = ClosedLiveGraph()
        foreign = graph.base/'unrelated-ready-v1.json'
        pin = graph.save(foreign, graph.checkpoint_files['ready-v1.json'])
        value = copy.deepcopy(graph.docs[graph.prerequisite_path]); value['ready'] = pin
        graph.rewrite(graph.prerequisite_path, value)
        real_open, opened = Path.open, []
        def observed_open(path, *args, **kwargs):
            if path == foreign:
                opened.append(str(path))
            return real_open(path, *args, **kwargs)
        refused = False
        with patch.object(Path, 'open', observed_open):
            try:
                graph.validate()
            except c.TargetRefused:
                refused = True
        self.assertEqual(opened, [], 'role-path rejection must precede opening unrelated bytes')
        self.assertTrue(refused, 'an equivalent foreign file is not the canonical ready role')

    def test_pending_capture_cannot_invent_known_cleanup_or_zero_typed_counters(self):
        for key, bad in (('cleanup_complete', False), ('stdout_bytes', False),
                         ('stderr_bytes', 0.0), ('worker_returncode', True), ('elapsed_ms', 282001)):
            with self.subTest(key=key):
                graph = ClosedLiveGraph(); path = graph.pending_root/'owner-result-v1.json'
                value = copy.deepcopy(graph.docs[path]); value[key] = bad
                graph.rewrite(path, value); self.refused(graph.validate)

    def test_distinct_child_worker_session_and_claim_caller_are_bound(self):
        for target in ('started', 'session', 'claim'):
            with self.subTest(target=target):
                graph = ClosedLiveGraph()
                if target == 'started':
                    path = graph.pending_root/'started-v1.json'
                    value = copy.deepcopy(graph.docs[path]); value['worker']['pid'] += 1
                elif target == 'session':
                    path = Path(graph.child['root'])/c.SESSION_FILE
                    value = copy.deepcopy(graph.docs[path]); value['caller'] = graph.s['caller']
                else:
                    path = graph.root/'claims-v1/author_live-v1.json'
                    value = copy.deepcopy(graph.docs[path]); value['caller'] = graph.s['caller']
                graph.rewrite(path, value); self.refused(graph.validate)

    def test_absent_before_expired_after_or_reused_pid_never_proves_live_fault(self):
        for change in ('absent_before', 'expired_after', 'reused_ticks', 'changed_boot', 'wrong_uid'):
            with self.subTest(change=change):
                graph = ClosedLiveGraph(); p = graph.docs[graph.prerequisite_path]
                selected = p['probe_before'] if change == 'absent_before' else p['probe_after']
                packet = graph.packet('absent' if change in ('absent_before','expired_after') else 'exited', graph.ready_ns+2000000000)
                if change == 'expired_after': packet['observed_boottime_ns'] = graph.checkpoint['expires_elapsed_ns']
                if change == 'reused_ticks': packet['start_ticks'] += 1
                if change == 'changed_boot': packet['boot_id'] = '11223344-5566-7788-99aa-bbccddeeff00'
                if change == 'wrong_uid': packet['expected_uid'] += 1; packet['observed_uid'] += 1
                graph.change_stdout(selected, env.encoded(packet)); self.refused(graph.validate)

    def test_post_fault_terminal_refusal_or_ordinary_junit_pass_cannot_be_promoted(self):
        graph = ClosedLiveGraph()
        names = '\n'.join((*reader.CHECKPOINT_FILES, 'terminal-v1.json'))+'\n'
        graph.change_stdout(graph.checkpoint_list, names.encode()); self.refused(graph.validate)
        graph = ClosedLiveGraph(); pin = graph.rows[graph.child['root']][0]
        graph.change_stdout(pin, prior.junit_bytes('author')); self.refused(graph.validate)

    def test_prerequisite_schema_build_and_foreign_source_role_are_required(self):
        for key, bad in (('protocol', 'original-author-restart-prerequisite-v1'),
                         ('version', True), ('extra', True), ('build', prior.f.pin('D:/Synthetic/foreign-build.json'))):
            with self.subTest(key=key):
                graph = ClosedLiveGraph(); value = copy.deepcopy(graph.docs[graph.prerequisite_path]); value[key] = bad
                graph.rewrite(graph.prerequisite_path, value); self.refused(graph.validate)


if __name__ == '__main__':
    unittest.main()
