"""Private CLI boundary checks with synthetic files and a fake supervisor only."""
import copy
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from contextlib import ExitStack, redirect_stdout
from unittest.mock import Mock, patch

from benchmarks import adb_held_socket as core
from benchmarks import adb_held_socket_probe as cli
from scripts.tests import test_adb_held_socket as f


def report(client_path=None, refused=False):
    backend = f.FakeBackend()
    if client_path:
        for bracket in backend.brackets:
            bracket['client']['executable'] = str(client_path)
    if refused: backend.errors[('connect', 0)] = OSError('synthetic refused acquisition')
    return core.probe(backend, f.admission())


@unittest.skipUnless(os.name == 'nt', 'physical D: CLI fixtures require Windows')
class CliTests(unittest.TestCase):
    def setUp(self):
        # Keep fixtures for reproducibility. No cleanup deletes old captures.
        self.base = Path(tempfile.mkdtemp(prefix='locallore-held-cli-', dir='D:/Dev/_Temp'))
        self.input = self.base/'admission.json'
        self.input.write_bytes(cli.env.encoded(f.admission()))
        self.pin = cli.env.binding(self.input)

    def refused(self, call):
        with self.assertRaises((cli.CliRefused, cli.env.EnvironmentRefused, ValueError, OSError)): call()

    def test_arguments_allow_each_unique_flag_order(self):
        values = [('--admission', 'a'), ('--admission-sha256', 'b'), ('--output', 'c')]
        for ordering in itertools.permutations(values):
            self.assertEqual(cli._arguments([v for pair in ordering for v in pair]), dict(values))

    def test_arguments_refuse_duplicates_unknown_types_and_lengths(self):
        for args in ([], (), ['--admission','a']*3,
                     ['--admission','a','--other','b','--output','c'],
                     ['--admission',1,'--admission-sha256','b','--output','c']):
            with self.subTest(args=args): self.refused(lambda: cli._arguments(args))

    def test_nonwindows_refuses_before_any_validation_or_dispatch(self):
        with patch.object(cli, 'os', types.SimpleNamespace(name='posix')), \
             patch.object(cli, '_load_admission') as load, \
             patch.object(cli.output_control, 'validate_output') as output, \
             patch.object(cli, '_dispatch') as dispatch, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['anything']), 1)
        load.assert_not_called(); output.assert_not_called(); dispatch.assert_not_called()

    def test_invalid_output_refuses_before_admission_dispatch_and_writes(self):
        for output in ('C:\\Synthetic\\new', 'E:\\Synthetic\\new', 'relative', str(self.base),
                       str(self.base/'trailing.'), str(self.base/'NUL')):
            with self.subTest(output=output), patch.object(cli, '_load_admission') as load, \
                 patch.object(cli, '_dispatch') as dispatch, redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(['--admission',str(self.input),'--admission-sha256',self.pin['sha256'],'--output',output]), 1)
                load.assert_not_called(); dispatch.assert_not_called()

    def test_invalid_admission_never_dispatches_or_creates_output(self):
        output = self.base/'never-created'
        with patch.object(cli, '_dispatch') as dispatch, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['--output',str(output),'--admission',str(self.input),
                                       '--admission-sha256','0'*64]), 1)
        dispatch.assert_not_called(); self.assertFalse(output.exists())

    def test_valid_bound_admission_is_independent(self):
        binding, value = cli._load_admission(str(self.input), self.pin['sha256'])
        self.assertEqual(binding, self.pin); self.assertEqual(value, f.admission())
        value['server']['pid'] += 1
        self.assertEqual(json.loads(self.input.read_bytes()), f.admission())

    def test_admission_rejects_malformed_utf8_duplicates_nan_oversize_and_contract(self):
        valid = cli.env.encoded(f.admission())
        bad_contract = f.admission(); bad_contract['expected_version'] = '002A'
        for index, raw in enumerate((b'\xff', b'{"version":1,"version":1}', b'{"x":NaN}',
                                     b' '*16385, cli.env.encoded(bad_contract), valid+b'{}')):
            with self.subTest(index=index):
                path = self.base/f'bad-{index}.json'; path.write_bytes(raw)
                self.refused(lambda: cli._load_admission(str(path), hashlib.sha256(raw).hexdigest()))

    def test_admission_hash_is_exact_lowercase_and_byte_bound(self):
        for bad in ('0'*64, self.pin['sha256'].upper(), True, None, {}, self.pin['sha256'][:-1]):
            with self.subTest(bad=bad): self.refused(lambda: cli._load_admission(str(self.input), bad))

    def test_admission_paths_require_existing_physical_D(self):
        for path in ('C:\\Synthetic\\admission.json','relative.json', str(self.base/'missing.json')):
            with self.subTest(path=path): self.refused(lambda: cli._load_admission(path,self.pin['sha256']))

    def test_serialization_accepts_bounded_success_and_partial_refusal(self):
        for refused in (False, True):
            value = report(refused=refused)
            self.assertEqual(json.loads(cli._report_bytes(value,f.admission())),value)
            self.assertFalse(value['feature_acceptance'])

    def test_serialization_rejects_unrelated_raw_row(self):
        value = report()
        raw = f.row4(local_port=44999)
        record = value['stages'][0]['snapshot']['rows'][0]
        record['raw_hex'] = raw.hex(); record['raw_sha256'] = hashlib.sha256(raw).hexdigest()
        self.refused(lambda: cli._report_bytes(value,f.admission()))

    def test_serialization_rejects_extra_nested_decoded_row_payload(self):
        for refused in (False, True):
            with self.subTest(refused=refused):
                value = report(refused=refused)
                value['stages'][0]['snapshot']['rows'][0]['row']['unrelated_native_table'] = 'SYNTHETIC_CANARY'
                self.refused(lambda: cli._report_bytes(value,f.admission()))

    def test_serialization_rejects_extra_nested_bracket_payload(self):
        value = report(refused=True)
        value['stages'][0]['bracket']['unrelated_native_table'] = 'SYNTHETIC_CANARY'
        self.refused(lambda: cli._report_bytes(value,f.admission()))

    def test_serialization_rejects_extra_nested_endpoint_payload(self):
        value = report(); value['stages'][1]['endpoint']['full_native_table'] = 'SYNTHETIC_CANARY'
        self.refused(lambda: cli._report_bytes(value,f.admission()))

    def test_serialization_rejects_nested_table_metadata_payload(self):
        value = report()
        value['stages'][0]['snapshot']['tables'][0]['raw_sha256'] = {'full_table':'SYNTHETIC_CANARY'}
        self.refused(lambda: cli._report_bytes(value,f.admission()))

    def test_worker_identity_requires_exact_observed_process_and_python_pin(self):
        value = report(); worker = value['stages'][0]['bracket']['client']
        python = dict(executable=dict(path=worker['executable']),runtime_dll=None)
        self.assertTrue(cli._worker_identity(value,dict(worker=worker),python))
        for key, bad in (('pid',True),('pid',f.CLIENT_PID+1),('creation_filetime',223456790),
                         ('executable','D:\\Synthetic\\foreign.exe'),('extra',True)):
            changed = copy.deepcopy(worker); changed[key] = bad
            with self.subTest(key=key): self.assertFalse(cli._worker_identity(value,dict(worker=changed),python))
        self.assertFalse(cli._worker_identity(value,{},python))

    def dispatch(self, *, owner_changes=None, worker_change=None, omitted=False, refused=False,
                 source_change=False, python_change=False, admission_change=False, missing_started=False):
        output = self.base/'output'
        source = self.base/'synthetic-source.py'; source.write_bytes(b'# synthetic source\n')
        python_file = self.base/'synthetic-python.bin'; python_file.write_bytes(b'synthetic interpreter pin')
        sources = [cli.env.binding(source)]
        python = dict(executable=cli.env.binding(python_file),runtime_dll=None)
        value = report(python_file,refused=refused)
        worker = copy.deepcopy(value['stages'][0]['bracket']['client'])
        parent = dict(pid=8000,creation_filetime=1000000,executable=str(python_file))
        source_calls = 0; python_calls = 0
        def source_snapshot():
            nonlocal source_calls
            source_calls += 1
            result = copy.deepcopy(sources)
            if source_change and source_calls >= 5: result[0]['sha256'] = '0'*64
            return result
        def python_snapshot():
            nonlocal python_calls
            python_calls += 1
            result = copy.deepcopy(python)
            if python_change and python_calls >= 5: result['executable']['sha256'] = '0'*64
            return result
        def identity(pid):
            if pid != f.CLIENT_PID: return copy.deepcopy(parent)
            changed = copy.deepcopy(worker)
            if worker_change: changed.update(worker_change)
            return changed
        def supervise(argv,barrier,target,seconds,started):
            self.assertIn('-I',argv); self.assertIn('-S',argv); self.assertIn('-B',argv)
            self.assertEqual(seconds,30); self.assertEqual(barrier,cli.BARRIER); self.assertEqual(target,output)
            if not missing_started: self.assertTrue(started(types.SimpleNamespace(pid=f.CLIENT_PID)))
            if not omitted: cli._write_bytes(output/'report-v1.json',cli._report_bytes(value,f.admission()))
            if admission_change: self.input.write_bytes(b'{"changed":true}')
            result = dict(status='child_exited',worker_returncode=0,cleanup_complete=True,
                          output_capture_complete=True,stderr_bytes=0,stdout_bytes=0,elapsed_ms=1)
            result.update(owner_changes or {})
            return result
        with ExitStack() as stack:
            stack.enter_context(patch.object(cli,'_source_bindings',side_effect=source_snapshot))
            stack.enter_context(patch.object(cli,'_python_bindings',side_effect=python_snapshot))
            stack.enter_context(patch.object(cli.env,'process_identity',side_effect=identity))
            supervisor = stack.enter_context(patch.object(cli.env,'supervise',side_effect=supervise))
            stack.enter_context(redirect_stdout(io.StringIO()))
            code = cli._dispatch(output,self.pin,f.admission())
        supervisor.assert_called_once()
        return code, cli.env.read_json(output/'result-v1.json')

    def test_fake_supervision_qualifies_only_fully_bound_report(self):
        code, result = self.dispatch()
        self.assertEqual(code,0); self.assertEqual(result['status'],'verified')
        self.assertTrue(result['acquisition_completed']); self.assertTrue(result['server_proof_verified'])
        self.assertFalse(result['feature_acceptance'])

    def test_known_worker_refusal_is_acquired_without_server_proof(self):
        code, result = self.dispatch(refused=True)
        self.assertEqual(code,1); self.assertTrue(result['acquisition_completed'])
        self.assertFalse(result['server_proof_verified']); self.assertFalse(result['feature_acceptance'])

    def test_unknown_owner_or_incomplete_capture_never_acquires(self):
        for index, change in enumerate((dict(status='timeout'),dict(worker_returncode=1),dict(worker_returncode=True),
                                       dict(cleanup_complete=False),dict(output_capture_complete=False),dict(stderr_bytes=1))):
            with self.subTest(change=change):
                self.base = self.base/f'owner-{index}'; self.base.mkdir()
                code, result = self.dispatch(owner_changes=change)
                self.assertEqual(code,1); self.assertFalse(result['acquisition_completed'])
                self.assertFalse(result['server_proof_verified'])

    def test_worker_identity_mismatch_keeps_acquisition_separate(self):
        code, result = self.dispatch(worker_change=dict(creation_filetime=223456790))
        self.assertEqual(code,1); self.assertTrue(result['acquisition_completed'])
        self.assertFalse(result['server_proof_verified']); self.assertEqual(result['reason'],'worker_identity')

    def test_missing_worker_record_never_qualifies(self):
        code, result = self.dispatch(missing_started=True)
        self.assertEqual(code,1); self.assertTrue(result['acquisition_completed']); self.assertFalse(result['server_proof_verified'])

    def test_missing_report_never_acquires(self):
        code, result = self.dispatch(omitted=True)
        self.assertEqual(code,1); self.assertFalse(result['acquisition_completed']); self.assertEqual(result['reason'],'report_missing')

    def test_final_source_mutation_clears_previously_verified_result(self):
        code, result = self.dispatch(source_change=True)
        self.assertEqual(code,1); self.assertFalse(result['sources_equal'])
        self.assertFalse(result['acquisition_completed']); self.assertFalse(result['server_proof_verified'])

    def test_final_python_mutation_clears_previously_verified_result(self):
        code, result = self.dispatch(python_change=True)
        self.assertEqual(code,1); self.assertFalse(result['python_equal'])
        self.assertFalse(result['acquisition_completed']); self.assertFalse(result['server_proof_verified'])

    def test_admission_mutation_after_worker_invalidates_acquisition(self):
        code, result = self.dispatch(admission_change=True)
        self.assertEqual(code,1); self.assertEqual(result['reason'],'admission_changed')
        self.assertFalse(result['acquisition_completed']); self.assertFalse(result['server_proof_verified'])

    def bound_reader(self, *, held_ctime=202, held_birth=77, path_birth=77, mutate=None, cross=None):
        raw = b'{"synthetic":true}'
        path_info = types.SimpleNamespace(st_dev=3,st_ino=7,st_size=len(raw),st_mtime_ns=100,
                                          st_ctime_ns=101,st_birthtime_ns=path_birth)
        held_info = types.SimpleNamespace(st_dev=3,st_ino=7,st_size=len(raw),st_mtime_ns=100,
                                          st_ctime_ns=held_ctime,st_birthtime_ns=held_birth)
        if held_birth is None: del held_info.st_birthtime_ns
        if path_birth is None: del path_info.st_birthtime_ns
        if cross: setattr(held_info,cross,getattr(held_info,cross)+1)
        path_after = copy.deepcopy(path_info); held_after = copy.deepcopy(held_info)
        if mutate:
            target, field = mutate
            selected = path_after if target == 'path' else held_after
            setattr(selected,field,getattr(selected,field)+1)
        class MemoryFile(io.BytesIO):
            def fileno(self): return 941
        path = Mock()
        path.stat.side_effect = [path_info,path_after]
        path.open.return_value = MemoryFile(raw)
        with patch.object(cli.env,'safe_path',return_value=path), \
             patch.object(cli.os,'fstat',side_effect=[held_info,held_after]):
            return cli._read_bound(path,hashlib.sha256(raw).hexdigest(),16384,'admission')

    def test_reader_accepts_distinct_ctimes_with_equal_birth_and_stable_per_api_identity(self):
        binding, value = self.bound_reader()
        self.assertEqual(value,dict(synthetic=True)); self.assertGreater(binding['bytes'],0)

    def test_reader_refuses_missing_mismatched_or_malformed_birthtime(self):
        for options in (dict(held_birth=None),dict(path_birth=None),dict(held_birth=78),
                        dict(held_birth=True),dict(held_birth=77.0),dict(path_birth=-1)):
            with self.subTest(options=options): self.refused(lambda:self.bound_reader(**options))

    def test_reader_refuses_each_api_identity_or_birthtime_mutation(self):
        for target in ('path','held'):
            for field in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_birthtime_ns'):
                with self.subTest(target=target,field=field):
                    self.refused(lambda:self.bound_reader(mutate=(target,field)))
        for field in ('st_dev','st_ino','st_size','st_mtime_ns'):
            with self.subTest(cross_api_field=field): self.refused(lambda:self.bound_reader(cross=field))

    def worker_preflight(self, *, invalid_parent=False, source_failure=False, admission_mutation=False, git_marker=False):
        output = self.base/'worker-output'; output.mkdir()
        if git_marker: (output/'.git').write_bytes(b'synthetic marker, not a repository')
        request_path = output/'request-v1.json'
        parent = dict(pid=8000,creation_filetime=1000000,executable='D:\\Synthetic\\python.exe')
        request = dict(version=1,protocol=cli.PROTOCOL,output=str(output),admission=self.pin,
                       validated_admission=f.admission(),owner_seconds=30,parent=parent,
                       source_closure=[],python={})
        observed = dict(parent)
        if invalid_parent: observed['creation_filetime'] += 1
        normalized = f.admission()
        if admission_mutation: normalized['expected_version'] = '002a'
        check = Mock(side_effect=cli.CliRefused('source') if source_failure else None)
        with patch.object(cli.sys,'stdin',types.SimpleNamespace(buffer=io.BytesIO(cli.BARRIER))), \
             patch.object(cli,'_existing_D_file',return_value=request_path), \
             patch.object(cli,'_read_bound',return_value=({},request)), \
             patch.object(cli.env,'process_identity',return_value=observed), \
             patch.object(cli,'_check_bindings',check), \
             patch.object(cli,'_load_admission',return_value=(self.pin,normalized)), \
             patch.object(cli.importlib,'import_module') as module:
            self.refused(lambda:cli._worker(request_path,'0'*64))
        module.assert_not_called()
        self.assertFalse((output/'report-v1.json').exists())
        return check

    def test_worker_changed_parent_refuses_before_backend_import(self):
        self.worker_preflight(invalid_parent=True).assert_not_called()

    def test_worker_changed_source_refuses_before_backend_import(self):
        self.worker_preflight(source_failure=True).assert_called_once()

    def test_worker_changed_admission_refuses_before_backend_import(self):
        self.worker_preflight(admission_mutation=True).assert_called_once()

    def test_worker_new_git_ancestor_refuses_before_backend_import(self):
        self.worker_preflight(git_marker=True).assert_not_called()


if __name__ == '__main__': unittest.main()
