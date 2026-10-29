"""Original finite SDK3 bundles. No saved live evidence or native/SDK calls."""
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def make(self,context=None,client_state=0):
        context=self.context()if context is None else copy.deepcopy(context)
        name='check-%04d'%context['index']if context['kind']=='check'else '%s-%04d-%s'%(context['kind'],context['index'],context['phase'])
        root=self.proofs/name;root.mkdir();(root/'launch').mkdir();(root/'held').mkdir()
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
        self.bundles.append(value);return self.seal(value)

    def seal(self,bundle):
        # These are original adversarial fixtures constructed before verification,
        # never repairs or rebindings of a historical captured result.
        root=bundle['root'];objects=bundle['objects']
        for name,value in objects.items():
            if name=='held/result-v1.json':continue
            (root/name).write_bytes(value if type(value)is bytes else v.env.encoded(value))
        result=objects['held/result-v1.json']
        for key,name in (('request','request-v1.json'),('owner','owner-result-v1.json'),('report','report-v1.json'),('worker','started-v1.json')):
            result[key]=v.env.binding(root/'held'/name)
        (root/'held/result-v1.json').write_bytes(v.env.encoded(result))
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


if __name__=='__main__':unittest.main()
