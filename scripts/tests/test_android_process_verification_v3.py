"""Original finite SDK3 bundles. No saved live evidence or native/SDK calls."""
import copy
import hashlib
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from benchmarks import android_process_verification_v3 as v
from scripts.tests import test_adb_held_socket as h


class OriginalBundle:
    """Build canonical original synthetic bytes, including both owner terminals."""
    def __init__(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-sdk3-reader-',dir='D:/Dev/_Temp'))
        self.clients=self.base/'clients';self.clients.mkdir()
        self.proofs=self.base/'server-proofs-v3';self.proofs.mkdir()
        self.adb=self.base/'adb.exe';self.adb.write_bytes(b'original synthetic ADB; not executable')
        self.ps=self.base/'powershell.exe';self.ps.write_bytes(b'original synthetic PS; not executable')
        self.py=self.base/'python.exe';self.py.write_bytes(b'original synthetic interpreter; not executable')
        self.dll=self.base/'python314.dll';self.dll.write_bytes(b'original synthetic DLL; never loaded')
        admitted=h.admission();admitted['server']['executable']=str(self.adb)
        s=self.adb.stat();admitted['adb_file']=dict(path=str(self.adb),bytes=s.st_size,
          sha256=hashlib.sha256(self.adb.read_bytes()).hexdigest(),identity=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns])
        self.admission_path=self.base/'admission-v1.json';v.env.create_json(self.admission_path,admitted)
        self.owner=dict(pid=9001,creation_filetime=900100,executable=str(self.py))
        self.CLI=dict(pid=9003,creation_filetime=900300,executable=str(self.py))
        self.worker=dict(pid=h.CLIENT_PID,creation_filetime=223456789,executable=str(self.py))
        self.session=dict(version=1,protocol=v.SDK_PROTOCOL,server_admission=v.env.binding(self.admission_path),
          admission=admitted,sdk_sources=v.sdk_source_bindings(),held_sources=v.probe_cli._source_bindings(),
          python=dict(executable=v.env.binding(self.py),runtime_dll=v.env.binding(self.dll)),
          adb=v.env.binding(self.adb),powershell=v.env.binding(self.ps),owner=self.owner,launcher=None)
        self.session_path=self.base/'sdk-session-v3.json';v.env.create_json(self.session_path,self.session)
        self.session_pin=v.env.binding(self.session_path)
        self.bundles=[]

    def argv(self,transport=None):
        return [str(self.adb),'-H','127.0.0.1','-P','5037']+(['devices','-l']if transport is None else ['-t',str(transport),'get-state'])

    def context(self,phase='before',index=1,transport=None,kind='command',label='devices',argv=None):
        return dict(kind=kind,index=index,phase='check'if kind=='check'else phase,
          label='check-server'if kind=='check'else label,
          command_sha256=None if kind=='check'else v.command_digest(argv or self.argv(transport)),transport_id=transport)

    def make(self,context=None,client_state=0,*,root_ready=False,held_only=False):
        context=self.context()if context is None else copy.deepcopy(context)
        name='check-%04d'%context['index']if context['kind']=='check'else '%s-%04d-%s'%(context['kind'],context['index'],context['phase'])
        root=self.proofs/name
        if not root_ready:root.mkdir();(root/'launch').mkdir()
        (root/'held').mkdir()
        backend=h.FakeBackend(client_state=client_state)
        for bracket in backend.brackets:
            bracket['server']=copy.deepcopy(self.session['admission']['server'])
            bracket['adb_file']=copy.deepcopy(self.session['admission']['adb_file'])
            bracket['client']=copy.deepcopy(self.worker)
        report=h.t.probe(backend,self.session['admission'])
        terminal=dict(status='verified',reason=None,acquisition_completed=True,server_proof_verified=True,feature_acceptance=False)
        objects={
          'launch/request-v1.json':dict(version=1,protocol=v.BUNDLE_PROTOCOL,session=self.session_pin,
            context=context,caller=self.owner,sdk_sources=self.session['sdk_sources'],held_sources=self.session['held_sources'],
            python=self.session['python'],command=[str(self.py),'-I','-S','-B',str(v.ROOT/'benchmarks/adb_held_socket_probe.py'),
              '--admission',str(self.admission_path),'--admission-sha256',self.session['server_admission']['sha256'],
              '--output',str(root/'held')],owner_seconds=10),
          'launch/started-v1.json':dict(CLI=self.CLI),
          'launch/source-after-v1.json':{key:self.session[key]for key in ('sdk_sources','held_sources','python')}|dict(caller=self.owner),
          'launch/owner-stdout-v1.bin':v.env.encoded(terminal),'launch/owner-stderr-v1.bin':b'',
          'held/request-v1.json':dict(version=1,protocol=h.t.PROTOCOL,output=str(root/'held'),
            admission=self.session['server_admission'],validated_admission=self.session['admission'],owner_seconds=30,
            parent=self.CLI,source_closure=self.session['held_sources'],python=self.session['python']),
          'held/started-v1.json':dict(worker=self.worker),'held/report-v1.json':report,
          'held/owner-stdout-v1.bin':b'held_socket_probe_report_acquired\n','held/owner-stderr-v1.bin':b''}
        for phase in ('before','after','final'):
            for prefix,bindings in (('source-closure',self.session['held_sources']),('python',self.session['python'])):
                objects[f'held/{prefix}-{phase}-v1.json']=dict(version=1,status='completed',reason=None,bindings=bindings)
        for part in ('launch','held'):
            objects[f'{part}/owner-result-v1.json']=dict(status='child_exited',cleanup_complete=True,elapsed_ms=3,
              output_capture_complete=True,worker_returncode=0,stdout_bytes=len(objects[f'{part}/owner-stdout-v1.bin']),stderr_bytes=0)
        objects['held/result-v1.json']=dict(version=1,protocol=h.t.PROTOCOL,status='verified',reason=None,
          acquisition_completed=True,server_proof_verified=True,feature_acceptance=False,sources_equal=True,python_equal=True,
          admission=self.session['server_admission'],request=None,owner=None,report=None,worker=None)
        value=dict(root=root,context=context,objects={name:copy.deepcopy(item)for name,item in objects.items()})
        self.bundles.append(value);return self.seal(value,held_only=held_only)

    def seal(self,bundle,*,held_only=False):
        # These are original adversarial fixtures constructed before verification,
        # never repairs or rebindings of a historical captured result.
        root=bundle['root'];objects=bundle['objects']
        for name,value in objects.items():
            if name=='held/result-v1.json':continue
            if held_only and not name.startswith('held/'):continue
            (root/name).write_bytes(value if type(value)is bytes else v.env.encoded(value))
        result=objects['held/result-v1.json']
        for key,name in (('request','request-v1.json'),('owner','owner-result-v1.json'),('report','report-v1.json'),('worker','started-v1.json')):
            result[key]=v.env.binding(root/'held'/name)
        (root/'held/result-v1.json').write_bytes(v.env.encoded(result))
        if held_only:return bundle
        manifest=dict(version=1,protocol=v.BUNDLE_PROTOCOL,session=self.session_pin,context=copy.deepcopy(bundle['context']),
          verified=True,files=[dict(relative=name,binding=v.env.binding(root/name))for name in v.PROOF_FILES])
        (root/'bundle-v1.json').write_bytes(v.env.encoded(manifest));bundle['pin']=v.env.binding(root/'bundle-v1.json')
        return bundle

    def row(self,index=1,transport=None):
        before=self.make(self.context('before',index,transport));after=self.make(self.context('after',index,transport))
        raw=b'original synthetic SDK bytes\x00\x1a\xff\r\n'
        stem=self.clients/f'command-{index:04d}';stem.with_suffix('.stdout.bin').write_bytes(raw)
        row=dict(version=3,protocol=v.SDK_PROTOCOL,index=index,label='devices',status='completed',returncode=0,
          cleanup_complete=True,stdout_bytes=len(raw),stdout_sha256=hashlib.sha256(raw).hexdigest(),stderr_bytes=0,
          elapsed_ms=7,effective_deadline_ms=15000,client_qualified=True,server_admission=self.session['server_admission'],
          server_before=before['pin'],server_after=after['pin'],transport_id=transport,
          argv=self.argv(transport),command_sha256=v.command_digest(self.argv(transport)))
        stem.with_suffix('.json').write_bytes(v.env.encoded(row));return row


@unittest.skipUnless(os.name=='nt','physical D: proof fixtures require Windows')
class Sdk3ReaderTests(unittest.TestCase):
    def setUp(self):self.f=OriginalBundle()

    def verify(self,b):return v.verify_owned_server_bundle(b['pin'],self.f.session,b['context'])

    def refused(self,call):
        with self.assertRaises(v.Sdk3Refused):call()

    def test_original_complete_bundle_and_raw_client_states(self):
        for index,state in enumerate((0,1,5,4294967295),1):
            with self.subTest(state=state):
                b=self.f.make(self.f.context(index=index),client_state=state)
                self.assertTrue(self.verify(b));self.assertEqual(b['objects']['held/report-v1.json']['client_raw_state'],state)

    def test_session_requires_complete_sdk_source_roster(self):
        value=copy.deepcopy(self.f.session)
        value['sdk_sources']=[p for p in value['sdk_sources']if not p['path'].endswith('android_process_client_v3.py')]
        self.refused(lambda:v.validate_session(value))

    def test_session_requires_complete_held_source_roster(self):
        value=copy.deepcopy(self.f.session);value['held_sources']=value['held_sources'][1:]
        self.refused(lambda:v.validate_session(value))

    def test_bundle_rechecks_bound_admission_json_bytes(self):
        b=self.f.make();self.f.admission_path.write_bytes(b'{"original-synthetic-admission":"changed"}')
        self.refused(lambda:self.verify(b))

    def test_expected_context_cannot_swap_phase_command_or_session(self):
        b=self.f.make()
        for change in (dict(phase='after'),dict(index=2),dict(command_sha256='0'*64)):
            with self.subTest(change=change):
                context=dict(b['context'],**change)
                self.refused(lambda:v.verify_owned_server_bundle(b['pin'],self.f.session,context))
        session=copy.deepcopy(self.f.session);session['owner']['creation_filetime']+=1
        self.refused(lambda:v.verify_owned_server_bundle(b['pin'],session,b['context']))

    def test_actual_cli_and_worker_identity_joins_are_required(self):
        for index,name in enumerate(('launch/started-v1.json','held/started-v1.json'),1):
            b=self.f.make(self.f.context(index=index));who='CLI'if name.startswith('launch')else'worker'
            b['objects'][name][who]['creation_filetime']+=1;self.f.seal(b)
            self.refused(lambda:self.verify(b))

    def test_after_source_and_caller_snapshots_cannot_borrow_initial_pins(self):
        b=self.f.make();b['objects']['launch/source-after-v1.json']['caller']['creation_filetime']+=1
        self.f.seal(b);self.refused(lambda:self.verify(b))

    def test_nested_private_canaries_are_rejected_after_hashes_rebind(self):
        for index,name in enumerate(('held/report-v1.json','held/request-v1.json','launch/request-v1.json'),1):
            b=self.f.make(self.f.context(index=index))
            if name.endswith('report-v1.json'):b['objects'][name]['stages'][0]['bracket']['private_full_table']='SYNTHETIC_CANARY'
            else:b['objects'][name]['private_full_table']='SYNTHETIC_CANARY'
            self.f.seal(b);self.refused(lambda:self.verify(b))

    def test_current_clients_accept_exact_v3_binary_pairs(self):
        self.f.row();self.assertIsNone(v.require_current_clients_v3(self.f.base,1,self.f.session))

    def test_current_clients_reject_reused_before_bundle_as_after(self):
        row=self.f.row();row['server_after']=row['server_before']
        (self.f.clients/'command-0001.json').write_bytes(v.env.encoded(row))
        self.refused(lambda:v.require_current_clients_v3(self.f.base,1,self.f.session))

    def test_current_clients_refuse_completed_but_unqualified_sdk_result(self):
        row=self.f.row();row['client_qualified']=False
        self.assertTrue(v.client_record_shape_v3(row))
        (self.f.clients/'command-0001.json').write_bytes(v.env.encoded(row))
        self.refused(lambda:v.require_current_clients_v3(self.f.base,1,self.f.session))

    def test_row_shape_rejects_legacy_versions_and_coerced_qualification(self):
        row=self.f.row()
        for change in (dict(version=1),dict(version=2),dict(version=True),dict(client_qualified=1),dict(index=True)):
            with self.subTest(change=change):self.assertFalse(v.client_record_shape_v3(dict(row,**change)))

    def rewrite_manifest(self,b,change):
        path=b['root']/'bundle-v1.json';value=v.env.read_json(path);change(value)
        path.write_bytes(v.env.encoded(value));b['pin']=v.env.binding(path)

    def test_manifest_refused_duplicate_reordered_missing_and_unknown_rosters(self):
        changes=(lambda x:x.update(verified=False),lambda x:x.update(version=True),
          lambda x:x['files'].reverse(),lambda x:x['files'].pop(),
          lambda x:x['files'].__setitem__(-1,copy.deepcopy(x['files'][0])))
        for index,change in enumerate(changes,1):
            b=self.f.make(self.f.context(index=index));self.rewrite_manifest(b,change)
            with self.subTest(index=index):self.refused(lambda:self.verify(b))

    def test_unknown_bundle_file_or_subdirectory_refuses(self):
        for index,folder in enumerate((False,True),1):
            b=self.f.make(self.f.context(index=index));path=b['root']/'unlisted'
            path.mkdir()if folder else path.write_bytes(b'original synthetic extra')
            with self.subTest(folder=folder):self.refused(lambda:self.verify(b))

    def test_manifest_hash_and_size_are_byte_bound(self):
        b=self.f.make();pin=copy.deepcopy(b['pin'])
        for change in (dict(bytes=True),dict(bytes=pin['bytes']+1),dict(sha256='0'*64)):
            with self.subTest(change=change):
                self.refused(lambda:v.verify_owned_server_bundle(dict(pin,**change),self.f.session,b['context']))

    def test_foreign_binding_refuses_before_foreign_bytes_are_read(self):
        b=self.f.make();foreign=self.f.base/'foreign-private.json';foreign.write_bytes(b'SYNTHETIC_PRIVATE_CANARY')
        self.rewrite_manifest(b,lambda m:m['files'][0].update(binding=v.env.binding(foreign)))
        original=v._read_pin;reads=[]
        def track(pin):reads.append(pin['path']);return original(pin)
        with patch.object(v,'_read_pin',side_effect=track):self.refused(lambda:self.verify(b))
        self.assertNotIn(str(foreign),reads)

    def test_both_owner_terminal_flags_are_strict(self):
        index=0
        for folder in ('launch','held'):
            for change in (dict(worker_returncode=1),dict(worker_returncode=True),dict(cleanup_complete=False),
                           dict(output_capture_complete=False),dict(status='timeout')):
                index+=1;b=self.f.make(self.f.context(index=index))
                b['objects'][folder+'/owner-result-v1.json'].update(change);self.f.seal(b)
                with self.subTest(folder=folder,change=change):self.refused(lambda:self.verify(b))

    def test_nested_terminal_and_source_canaries_cannot_be_rebound_as_proof(self):
        b=self.f.make();terminal=v.env.decode_json(b['objects']['launch/owner-stdout-v1.bin'])
        terminal['private_rows']='SYNTHETIC_CANARY';raw=v.env.encoded(terminal)
        b['objects']['launch/owner-stdout-v1.bin']=raw
        b['objects']['launch/owner-result-v1.json']['stdout_bytes']=len(raw)
        self.f.seal(b);self.refused(lambda:self.verify(b))

    def test_complete_source_rosters_cannot_mix_benchmark_parents(self):
        value=copy.deepcopy(self.f.session);pin=value['sdk_sources'][0]
        pin['path']=str(self.f.base/'other-benchmarks'/Path(pin['path']).name)
        value['sdk_sources'].sort(key=lambda p:p['path'])
        self.refused(lambda:v.validate_session(value))

    def test_strict_manifest_json_rejects_duplicate_keys_nan_and_invalid_utf8(self):
        for index,raw in enumerate((b'{"version":1,"version":1}',b'{"x":NaN}',b'\xff'),1):
            b=self.f.make(self.f.context(index=index));path=b['root']/'bundle-v1.json'
            path.write_bytes(raw);b['pin']=v.env.binding(path)
            with self.subTest(index=index):self.refused(lambda:self.verify(b))

    def test_command_digest_and_policy_are_closed_and_transport_specific(self):
        self.assertEqual(v.command_digest(self.f.argv()),hashlib.sha256(v.env.encoded(self.f.argv())).hexdigest())
        v.validate_command(self.f.argv(),str(self.f.adb),None);v.validate_command(self.f.argv(7),str(self.f.adb),7)
        for command,transport in ((self.f.argv(),7),(self.f.argv(8),7),
            ([str(self.f.adb),'-H','127.0.0.1','-P','5037','kill-server'],None),
            ([str(self.f.adb),'-H','0.0.0.0','-P','5037','devices','-l'],None)):
            with self.subTest(command=command):self.refused(lambda:v.validate_command(command,str(self.f.adb),transport))
        for bad in (tuple(self.f.argv()),['x',True],['x\0'],[]):
            with self.subTest(bad=bad):self.refused(lambda:v.command_digest(bad))

    def test_current_clients_raw_bytes_and_pair_roster_cannot_change(self):
        self.f.row();raw=self.f.clients/'command-0001.stdout.bin';raw.write_bytes(raw.read_bytes()+b'changed')
        self.refused(lambda:v.require_current_clients_v3(self.f.base,1,self.f.session))
        self.refused(lambda:v.require_current_clients_v3(self.f.base,0,self.f.session))

    def test_current_clients_reject_retargeting_or_discovery_after_selection(self):
        for second in (8,None):
            with self.subTest(second=second):
                f=OriginalBundle();f.row(1,7);f.row(2,second)
                self.refused(lambda:v.require_current_clients_v3(f.base,2,f.session))

    def test_external_pairs_cover_context_without_proving_a_transfer(self):
        self.f.row(transport=7)
        for phase in ('before','after'):
            self.f.make(self.f.context(phase,transport=7,kind='external',label='stream'))
        self.assertIsNone(v.require_current_clients_v3(self.f.base,1,self.f.session))
        self.assertEqual({p.name for p in self.f.clients.iterdir()},{'command-0001.json','command-0001.stdout.bin'})
        self.assertFalse((self.f.base/'stream-record.json').exists())

    def test_external_pair_requires_matching_after_command_context(self):
        self.f.row(transport=7)
        self.f.make(self.f.context('before',transport=7,kind='external',label='stream'))
        self.refused(lambda:v.require_current_clients_v3(self.f.base,1,self.f.session))
        context=self.f.context('after',transport=7,kind='external',label='stream');context['command_sha256']='0'*64
        self.f.make(context);self.refused(lambda:v.require_current_clients_v3(self.f.base,1,self.f.session))

    def test_explicit_host_checks_accept_zero_sdk_without_fabricated_rows(self):
        for index in (1,2):self.f.make(self.f.context(index=index,kind='check'))
        self.assertIsNone(v.require_host_checks_v3(self.f.base,self.f.session));self.assertEqual(list(self.f.clients.iterdir()),[])
        self.refused(lambda:v.require_current_clients_v3(self.f.base,0,self.f.session))

    def test_host_checks_reject_empty_gaps_and_nonnull_target(self):
        self.refused(lambda:v.require_host_checks_v3(self.f.base,self.f.session))
        self.f.make(self.f.context(index=2,kind='check'))
        self.refused(lambda:v.require_host_checks_v3(self.f.base,self.f.session))
        f=OriginalBundle();f.make(f.context(kind='check',transport=7))
        self.refused(lambda:v.require_host_checks_v3(f.base,f.session))

    def test_host_checks_reject_command_rows_and_foreign_namespace(self):
        self.f.make(self.f.context(kind='check'));(self.f.clients/'untrusted.stdout.bin').write_bytes(b'synthetic')
        self.refused(lambda:v.require_host_checks_v3(self.f.base,self.f.session))
        f=OriginalBundle();f.make(f.context())
        self.refused(lambda:v.require_host_checks_v3(f.base,f.session))

    def acquisition(self,*,failed=False,changed_caller=False):
        context=self.f.context();root=self.f.proofs/'command-0001-before';calls=[]
        def identity(pid):
            if pid==self.f.CLI['pid']:return copy.deepcopy(self.f.CLI)
            self.assertEqual(pid,self.f.owner['pid']);value=copy.deepcopy(self.f.owner)
            if changed_caller and calls:value['creation_filetime']+=1
            return value
        def supervise(command,barrier,out,seconds,started):
            calls.append(command);self.assertEqual(barrier,b'');self.assertEqual(out,root/'launch');self.assertEqual(seconds,10)
            self.assertEqual(command,[str(self.f.py),'-I','-S','-B',str(v.ROOT/'benchmarks/adb_held_socket_probe.py'),
              '--admission',str(self.f.admission_path),'--admission-sha256',self.f.session['server_admission']['sha256'],
              '--output',str(root/'held')])
            self.assertTrue(started(SimpleNamespace(pid=self.f.CLI['pid'])))
            terminal=v.env.encoded(dict(status='verified',reason=None,acquisition_completed=True,server_proof_verified=True,feature_acceptance=False))
            (out/'owner-stdout-v1.bin').write_bytes(terminal);(out/'owner-stderr-v1.bin').write_bytes(b'')
            if not failed:self.f.make(context,root_ready=True,held_only=True)
            return dict(status='child_exited',cleanup_complete=True,elapsed_ms=3,output_capture_complete=True,
                        worker_returncode=1 if failed else 0,stdout_bytes=len(terminal),stderr_bytes=0)
        with patch.object(v,'python_bindings',return_value=self.f.session['python']), \
             patch.object(v.os,'getpid',return_value=self.f.owner['pid']), \
             patch.object(v.env,'process_identity',side_effect=identity), \
             patch.object(v.env,'supervise',side_effect=supervise)as owner:
            binding=v.acquire_owned_server_bundle(root,self.f.session_pin,context,10)
        owner.assert_called_once();return binding,context

    def test_acquisition_uses_one_fixed_owned_cli_and_actual_terminal_join(self):
        binding,context=self.acquisition()
        self.assertTrue(v.verify_owned_server_bundle(binding,self.f.session,context))

    def test_failed_acquisition_retains_refused_manifest_without_retry(self):
        binding,context=self.acquisition(failed=True)
        self.assertIs(v.env.read_json(binding['path'])['verified'],False)
        self.refused(lambda:v.verify_owned_server_bundle(binding,self.f.session,context))

    def test_acquisition_caller_change_is_retained_as_refused_bundle(self):
        binding,context=self.acquisition(changed_caller=True)
        self.assertIs(v.env.read_json(binding['path'])['verified'],False)
        self.refused(lambda:v.verify_owned_server_bundle(binding,self.f.session,context))

    def test_acquisition_budget_and_callback_substitution_refuse_before_dispatch(self):
        root=self.f.proofs/'command-0001-before'
        with patch.object(v.env,'supervise')as owner:
            for seconds in (True,0,46,0.5):
                with self.subTest(seconds=seconds):
                    self.refused(lambda:v.acquire_owned_server_bundle(root,self.f.session_pin,self.f.context(),seconds))
            with self.assertRaises(TypeError):
                v.acquire_owned_server_bundle(root,self.f.session_pin,self.f.context(),10,proof_provider=lambda:True)
        owner.assert_not_called();self.assertFalse(root.exists())

    def identity_read(self,*,birth=77,cross=None,mutation=None):
        raw=b'original synthetic receipt\0';path_info=SimpleNamespace(st_dev=3,st_ino=7,st_size=len(raw),st_mtime_ns=100,st_ctime_ns=101,st_birthtime_ns=77)
        held_info=SimpleNamespace(st_dev=3,st_ino=7,st_size=len(raw),st_mtime_ns=100,st_ctime_ns=202,st_birthtime_ns=birth)
        if birth is None:del held_info.st_birthtime_ns
        if cross:setattr(held_info,cross,getattr(held_info,cross)+1)
        path_after=copy.deepcopy(path_info);held_after=copy.deepcopy(held_info)
        if mutation:
            target,field=mutation;selected=path_after if target=='path'else held_after
            setattr(selected,field,getattr(selected,field)+1)
        class Memory(io.BytesIO):
            def fileno(self):return 941
        path=Mock();path.stat.side_effect=[path_info,path_after];path.open.return_value=Memory(raw)
        pin=dict(path='D:\\Synthetic\\receipt.bin',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        with patch.object(v,'_dpath',return_value=path),patch.object(v.os,'fstat',side_effect=[held_info,held_after]):
            return v._read_pin(pin)

    def test_read_pin_accepts_distinct_stable_ctimes_with_equal_birth(self):
        self.assertEqual(self.identity_read(),b'original synthetic receipt\0')

    def test_read_pin_birth_cross_identity_and_per_api_mutations_refuse(self):
        for birth in (None,True,-1,77.0,78):
            with self.subTest(birth=birth):self.refused(lambda:self.identity_read(birth=birth))
        for field in ('st_dev','st_ino','st_size','st_mtime_ns'):
            with self.subTest(cross=field):self.refused(lambda:self.identity_read(cross=field))
        for target in ('path','held'):
            for field in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_birthtime_ns'):
                with self.subTest(target=target,field=field):self.refused(lambda:self.identity_read(mutation=(target,field)))


if __name__=='__main__':unittest.main()
