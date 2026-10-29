"""Original fixed-profile restart authority fixtures; no device/kernel/model IO."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path,PureWindowsPath
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import owned_restart_contract as r
from benchmarks import android_process_verification_v5 as reader
from benchmarks import owned_target_contract as legacy
from scripts.tests import test_owned_target_contract as f
from scripts.tests import test_original_author_prompt_provenance as author_fixture
from scripts.tests import test_android_instrumentation_evidence as junit_fixture

PROTOCOL='owned-emulator-restart-target-v1'
SDK_PROTOCOL='sdk-owned-restart-v1'
PROOF_PROTOCOL='owned-restart-socket-proof-v1'
GUEST_ROOT='D:/Dev/Experiments/LocalLore/2026-10-29-author-restart-controller-v1/avd-v1'
PROBE_PATH='/data/local/tmp/locallore-author-process-probe-v1'
RESTART_CLASS='org.locallore.app.OriginalAuthorRestartInstrumentedTest'
RESTART_METHOD='recordsOriginalAuthorAfterExternalRestartWithoutInference'
SOURCE_NAMES=(*f.SOURCE_NAMES,'owned_restart_contract.py','owned_restart_owner.py','android_process_client_v5.py',
 'android_process_verification_v5.py','original_author_restart_controller.py','original_author_model_proof.py',
 'original_author_diagnostic.py','original_author_restart_proof.py','android_instrumentation_evidence.py')
BOOT='6ed5f4a0-52f8-4fbc-83d9-a45f8c3fa674'


def admission():
    """Construct fresh original metadata, never relabel captured proof bytes."""
    value=f.admission();value.update(protocol=PROTOCOL,root='D:\\Synthetic\\restart-owner')
    value['server']['root']=str(PureWindowsPath(value['root'])/'server');value['guest']['root']=GUEST_ROOT
    value['sources']=[f.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks')/name)for name in SOURCE_NAMES]
    value['sources'].sort(key=lambda row:row['path']);by_name={PureWindowsPath(row['path']).name:row for row in value['sources']}
    value['server']['sources']=[copy.deepcopy(by_name[PureWindowsPath(row['path']).name])for row in value['server']['sources']]
    value['artifacts'].update(process_probe=f.pin('D:/Synthetic/android-author-process-probe-v1'),
      process_probe_source=f.pin('D:/Synthetic/LocalLore/benchmarks/native/android_author_process_probe.c'))
    return value


def running(a=None):
    a=admission()if a is None else a;value=f.running(a);value['protocol']=PROTOCOL;return value


def session(a=None):
    a=admission()if a is None else a;value=f.session(a)
    value.update(protocol=SDK_PROTOCOL,descriptor=running(a),root='D:\\Synthetic\\sdk-v5');return value


def proof(s=None,*,after=False):
    s=session()if s is None else s;value=f.proof(s,after=after)
    value.update(protocol=PROOF_PROTOCOL,session=f.pin(PureWindowsPath(s['root'])/'sdk-session-v5.json'));return value


def query_bundle(s=None):
    s=session()if s is None else s;value=f.query_bundle(s);value['protocol']=PROOF_PROTOCOL;return value


def instrumentation(kind):
    selected={
      'import':legacy.CLASS+'#'+legacy.METHODS[0],
      'author':legacy.CLASS+'#'+legacy.METHODS[1],
      'restart':RESTART_CLASS+'#'+RESTART_METHOD}[kind]
    return ['am','instrument','-w','-r','-e','class',selected,legacy.TEST+'/androidx.test.runner.AndroidJUnitRunner']


def process_packet(*,mode='snapshot',state='alive',pid=8021,uid=10421,start=90001,boot=BOOT):
    value=dict(version=1,protocol='android-author-process-probe-v1',mode=mode,boot_id=boot,pid=pid,expected_uid=uid,
      observed_uid=uid,start_ticks=start,state=state,pidfd_opened=True,poll_revents=0,pidfd_closed=True,proc_opened=True,proc_closed=True,error=None,errno=0)
    if mode=='boot':value.update(pid=None,expected_uid=None,observed_uid=None,start_ticks=None,state='boot',pidfd_opened=False,poll_revents=None,pidfd_closed=None,proc_opened=False,proc_closed=None)
    elif state=='absent':value.update(observed_uid=None,start_ticks=None,pidfd_opened=False,poll_revents=None,pidfd_closed=None,proc_opened=False,proc_closed=None,errno=3)
    elif state=='exited':value['poll_revents']=1
    return value


def junit_bytes(kind):
    selected=instrumentation(kind)[6];cl,method=selected.split('#')
    return (junit_fixture.bundle(method,1,1,cls=cl,count=1,stream='\n'+cl+':')+
      junit_fixture.bundle(method,1,0,cls=cl,count=1,stream='.')+junit_fixture.ending(1)).encode()


class ClosedRestartGraph:
    """Fresh synthetic complete SDK records and original prerequisite sidecars."""
    def __init__(self,*,duplicate_kind=None):
        from benchmarks import receipt_avd_environment as env
        self.env=env;self.base=Path(tempfile.mkdtemp(prefix='locallore-restart-graph-',dir='D:/Dev/_Temp')).resolve(strict=True)
        self.root=self.base/'owner';self.sdk=self.base/'sdk';self.writes=[]
        self.a=admission();self.a.update(root=str(self.root));self.a['server']['root']=str(self.root/'server')
        self.a['sources']=r.source_bindings()
        self.a['server']['sources']=[copy.deepcopy(row)for row in self.a['sources']if PureWindowsPath(row['path']).name in legacy.base.SOURCE_NAMES|{'__init__.py'}]
        dll=Path(sys.executable).with_name('python%d%d.dll'%sys.version_info[:2])
        self.a['python']=dict(executable=env.binding(Path(sys.executable)),runtime_dll=env.binding(dll)if dll.is_file()else None)
        self.a['server']['python']=copy.deepcopy(self.a['python'])
        self.a['artifacts']['process_probe_source']=env.binding(Path(r.__file__).parent/'native/android_author_process_probe.c')
        self.admission=self.save(self.base/'admission-v1.json',self.a);self.d=running(self.a);self.d['admission']=self.admission
        self.running=self.save(self.root/'running-v1.json',self.d);self.s=session(self.a)
        self.s.update(root=str(self.sdk),admission=self.admission,running=self.running,descriptor=self.d)
        self.session=self.save(self.sdk/'sdk-session-v5.json',self.s);self.rows=[];self.row_pins=[]
        baseline=author_fixture.fixture(author_fixture.CURRENT);bf=author_fixture.f
        self.import_proof=self.save(self.sdk/'import-proof/import-v1.json',baseline['imported'])
        self.author=baseline['author'];self.author_raw=bf.raw(self.author)
        self.author_proof=self.save(self.sdk/'author-proof/proof-v1.json',self.author_raw)
        self.author_artifacts={name:self.save(self.sdk/'author-proof'/name,raw)for name,raw in baseline['artifacts'].items()}
        for name in('workspace-v1','archive-staging'):(self.sdk/'author-proof'/name).mkdir()
        pid=self.author['process']['pid'];uid=self.author['process']['uid']
        boot=self.add([PROBE_PATH,'--boot'],self.encode(process_packet(mode='boot')),'boot-initial')
        imported=self.add(instrumentation('import'),junit_bytes('import'),'import')
        self.collection('no_backup/original-author-import-proof-v1',{'import-v1.json':baseline['imported']},uid)
        if duplicate_kind=='import':self.add(instrumentation('import'),junit_bytes('import'),'duplicate-import')
        authored=self.add(instrumentation('author'),junit_bytes('author'),'author')
        author_names=('proof-v1.json',*author_fixture.f.p.RECORDS,*author_fixture.f.p.TRACES)
        self.collection('no_backup/original-author-proof-v1',
          {name:self.author_raw if name=='proof-v1.json'else baseline['artifacts'][name]for name in author_names},uid)
        if duplicate_kind=='author':self.add(instrumentation('author'),junit_bytes('author'),'duplicate-author')
        packages={}
        for kind,name,package_uid,apk in(('product',r.APP,uid,'product_apk'),('tests',r.TEST,uid+1,'test_apk')):
            path='/data/app/~~original-'+kind+'/base.apk'
            uid_stdout=('package:'+r.APP+' uid:'+str(uid)+'\npackage:'+r.TEST+' uid:'+str(uid+1)+'\n').encode()
            packages[kind]=dict(uid=self.add(['cmd','package','list','packages','-U','--user','0',name],uid_stdout,kind+'-uid'),
              path=self.add(['cmd','package','path','--user','0',name],('package:'+path+'\n').encode(),kind+'-path'),
              sha256=self.add(['sha256sum',path],(self.a['artifacts'][apk]['sha256']+'  '+path+'\n').encode(),kind+'-hash'))
        before=self.add([PROBE_PATH,'--snapshot',str(pid),str(uid)],self.encode(process_packet(pid=pid,uid=uid)),'before')
        stop=self.add(['am','force-stop','--user','0',r.APP],b'','force-stop')
        after=self.add([PROBE_PATH,'--snapshot',str(pid),str(uid)],self.encode(process_packet(pid=pid,uid=uid,state='absent')),'after')
        self.prerequisite=dict(version=1,protocol='original-author-restart-prerequisite-v1',admission=self.admission,running=self.running,
          session=self.session,caller=self.s['caller'],import_proof=self.import_proof,author_proof=self.author_proof,
          author_artifacts=self.author_artifacts,import_instrumentation=imported,author_instrumentation=authored,
          boot_initial=boot,probe_before=before,force_stop=stop,probe_after=after,package_checks=packages)
        self.prerequisite_pin=self.save(self.root/'restart-prerequisite-v1.json',self.prerequisite)
        # Keep the original twelve selected-witness view stable for earlier
        # negative bodies; all actual SDK rows/indices remain separately kept.
        self.all_rows=self.rows;self.all_row_pins=self.row_pins
        selected=[boot,imported,authored,*[packages[kind][key]for kind in('product','tests')for key in('uid','path','sha256')],before,stop,after]
        self.rows=[self.all_rows[self.env.read_json(pin['path'])['index']-1]for pin in selected]
        self.row_pins=selected

    def encode(self,value):return self.env.encoded(value)
    def save(self,path,value):
        path=Path(path).resolve(strict=False)
        if path.drive.upper()!='D:'or not path.is_relative_to(self.base):raise AssertionError('synthetic graph write escaped D root')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value if type(value)is bytes else self.encode(value));self.writes.append(path)
        return self.env.binding(path)
    def add(self,argv,stdout,label):
        index=len(self.rows)+1;operation=dict(argv=copy.deepcopy(argv),stdin=None);digest=r.operation_digest(operation);proofs={}
        for phase in('before','after'):
            p=proof(self.s,after=phase=='after');p['session']=self.session;p['context'].update(index=index,label=label,operation_sha256=digest)
            path=self.sdk/'proofs'/('command-%04d-%s.json'%(index,phase));queries=path.with_name(path.stem+'-queries-v1.json')
            p['queries']=self.save(queries,query_bundle(self.s));proofs[phase]=self.save(path,p)
        stem=self.sdk/'clients'/('command-%04d'%index)
        row=dict(version=5,protocol=SDK_PROTOCOL,session=self.session,index=index,label=label,operation=operation,operation_sha256=digest,
          transport_id=self.d['transport_id'],status='completed',returncode=0,cleanup_complete=True,elapsed_ms=7,effective_deadline_ms=15000,
          stdout=self.save(stem.with_suffix('.stdout.bin'),stdout),stderr=self.save(stem.with_suffix('.stderr.bin'),b''),
          stdin_sha256=None,stdin_bytes=0,stdin_complete=True,server_before=proofs['before'],server_after=proofs['after'],
          client_qualified=True,socket_closed=True,sender_joined=True,input_closed=True)
        self.rows.append(row);pin=self.save(stem.with_suffix('.json'),row);self.row_pins.append(pin)
        if argv[:2]==['am','instrument']:
            kind=r.instrumentation_kind(argv)
            self.save(self.root/'claims-v1'/(kind+'-v1.json'),r.claim_record(self.admission,self.s['caller'],kind,digest))
        return pin

    def collection(self,remote,values,uid):
        names=tuple(values);paths=[remote+'/'+name for name in names]
        dirs=('workspace-v1','archive-staging')if remote.endswith('/original-author-proof-v1')else()
        prefix=['run-as',r.APP,'--user','0']
        self.add(prefix+['ls',remote],('\n'.join((*names,*dirs))+'\n').encode(),'sidecar-list')
        hashes=''.join(hashlib.sha256(values[name]).hexdigest()+'  '+path+'\n'for name,path in zip(names,paths)).encode()
        self.add(prefix+['sha256sum',*paths],hashes,'sidecar-hash')
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w')as archive:
            for name,path in zip(names,paths):
                item=tarfile.TarInfo(path);item.uid=uid;item.size=len(values[name]);archive.addfile(item,io.BytesIO(values[name]))
        self.add(prefix+['tar','-cf','-',*paths],stream.getvalue(),'sidecar-tar')
        self.add(prefix+['sha256sum',*paths],hashes,'sidecar-post-hash')

    def validate(self):
        return reader.verify_restart_prerequisite(self.prerequisite_pin,self.a,self.admission,self.running,self.s['caller'])

    def replace_reference(self,value,path,pin):
        if type(value)is dict:
            if set(value)=={'path','bytes','sha256'}and value['path']==path:return copy.deepcopy(pin)
            return {key:self.replace_reference(item,path,pin)for key,item in value.items()}
        if type(value)is list:return [self.replace_reference(item,path,pin)for item in value]
        return value

    def mutate_stdout(self,index,raw):
        row=self.rows[index-1];row['stdout']=self.save(row['stdout']['path'],raw);new=self.save(self.row_pins[index-1]['path'],row)
        self.prerequisite=self.replace_reference(self.prerequisite,new['path'],new);self.row_pins[index-1]=new
        self.prerequisite_pin=self.save(self.prerequisite_pin['path'],self.prerequisite)


class RestartProfileTests(unittest.TestCase):
    def refused(self,call):
        with self.assertRaises(r.TargetRefused):call()

    def test_complete_restart_profile_is_copied_and_pure(self):
        value=admission();before=copy.deepcopy(value)
        with patch.object(Path,'open',side_effect=AssertionError('unexpected IO')),patch.object(Path,'stat',side_effect=AssertionError('unexpected metadata IO')):
            result=r.validate_admission(value)
        self.assertEqual(result,before);result['guest']['cores']=1;self.assertEqual(value,before)

    def test_fixed_new_and_old_profile_admissions_are_not_interchangeable(self):
        value=admission();self.refused(lambda:r.validate_admission(f.admission()))
        with self.assertRaises(legacy.TargetRefused):legacy.validate_admission(value)
        value['protocol']='owned-emulator-target-v1';self.refused(lambda:r.validate_admission(value))

    def test_new_source_closure_is_complete_sorted_and_pinned_to_one_parent(self):
        value=admission();self.assertEqual(len(value['sources']),23)
        for change in(lambda v:v['sources'].pop(),lambda v:v['sources'].reverse(),lambda v:v['sources'][0].update(path='D:/Foreign/benchmarks/owned_target_contract.py')):
            value=admission();change(value);self.refused(lambda:r.validate_admission(value))

    def test_new_artifacts_and_guest_root_do_not_select_old_boot_authority(self):
        for change in(lambda v:v['artifacts'].pop('process_probe'),lambda v:v['artifacts']['process_probe'].update(bytes=64*1024*1024+1),
                      lambda v:v['guest'].update(root=f.admission()['guest']['root']),lambda v:v['artifacts']['process_probe_source'].update(path='D:/Synthetic/foreign.c')):
            value=admission();change(value);self.refused(lambda:r.validate_admission(value))

    def test_old_sdk4_still_rejects_third_method_new_probe_and_new_artifact_roster(self):
        for operation in(dict(argv=instrumentation('restart'),stdin=None),dict(argv=[PROBE_PATH,'--boot'],stdin=None)):
            with self.assertRaises(legacy.TargetRefused):legacy.validate_operation(operation,f.admission())
        with self.assertRaises(legacy.TargetRefused):legacy.validate_admission(admission())

    def test_exact_three_instrumentation_methods_have_distinct_fixed_kinds(self):
        for kind in('import','author','restart'):
            argv=instrumentation(kind);operation=dict(argv=argv,stdin=None)
            self.assertEqual(r.instrumentation_kind(argv),kind);self.assertEqual(r.validate_operation(operation,admission()),operation)
        for argv in(instrumentation('restart')[:-1],['am','instrument','foreign'],['sh','-c','am instrument']):
            self.refused(lambda:r.validate_operation(dict(argv=argv,stdin=None),admission()))

    def test_exact_probe_recipes_bind_only_current_binary_and_valid_decimal_identity(self):
        value=admission()
        for argv in([PROBE_PATH,'--boot'],[PROBE_PATH,'--snapshot','8021','10421'],['sha256sum',PROBE_PATH],['chmod','700',PROBE_PATH]):
            op=dict(argv=argv,stdin=None);self.assertEqual(r.validate_operation(op,value),op)
        op=dict(argv=['dd','of='+PROBE_PATH,'bs=65536'],stdin=value['artifacts']['process_probe']);self.assertEqual(r.validate_operation(op,value),op)
        for argv in([PROBE_PATH,'--snapshot','0','10421'],[PROBE_PATH,'--snapshot','8021','9999'],[PROBE_PATH,'--snapshot','+8021','10421'],
                     [PROBE_PATH,'--snapshot','8021','10421','extra'],['/foreign-probe','--boot'],['kill','8021']):
            self.refused(lambda:r.validate_operation(dict(argv=argv,stdin=None),value))
        op['stdin']=value['artifacts']['probe'];self.refused(lambda:r.validate_operation(op,value))

    def test_running_session_and_proof_tags_stay_new_without_legacy_fallback(self):
        value=admission();d=running(value);s=session(value)
        self.assertEqual(r.validate_running(d,value,d['admission']),d);self.assertEqual(r.validate_session(s,value),s)
        p=proof(s);self.assertEqual(r.validate_proof(p,s,p['context']),p)
        with self.assertRaises(legacy.TargetRefused):legacy.validate_session(s,f.admission())
        for key,bad in(('protocol','sdk-owned-target-v1'),('descriptor',f.running())):
            changed=copy.deepcopy(s);changed[key]=bad;self.refused(lambda:r.validate_session(changed,value))


class NativeProbePacketTests(unittest.TestCase):
    def raw(self,value):return json.dumps(value,separators=(',',':'),allow_nan=False).encode()
    def refused(self,call):
        from benchmarks.receipt_avd_environment import EnvironmentRefused
        with self.assertRaises((ValueError,EnvironmentRefused)):call()

    def test_original_boot_alive_exited_and_esrch_packets_are_distinct_and_copied(self):
        for mode,state in(('boot','boot'),('snapshot','alive'),('snapshot','exited'),('snapshot','absent')):
            value=process_packet(mode=mode,state=state);before=copy.deepcopy(value)
            expected={}if mode=='boot'else dict(pid=8021,uid=10421)
            self.assertEqual(reader.validate_probe_packet(self.raw(value)),value)
            self.assertEqual(reader.parse_probe(self.raw(value),mode,**expected),value);self.assertEqual(value,before)

    def test_exact_expected_pid_uid_and_mode_cannot_borrow_another_observation(self):
        raw=self.raw(process_packet())
        for expected in(dict(pid=8022,uid=10421),dict(pid=8021,uid=10422),dict(pid=True,uid=10421),dict(pid=8021,uid=True)):
            self.refused(lambda:reader.parse_probe(raw,'snapshot',**expected))
        self.refused(lambda:reader.parse_probe(raw,'boot'))

    def test_esrch_is_only_absence_and_preserves_closed_proc_directory_if_opened(self):
        value=process_packet(state='absent');value.update(proc_opened=True,proc_closed=True)
        self.assertEqual(reader.parse_probe(self.raw(value),'snapshot',pid=8021,uid=10421),value)
        for field,bad in(('errno',0),('errno',1),('errno',38),('observed_uid',10421),('start_ticks',90001),
                         ('pidfd_opened',True),('proc_closed',None)):
            changed=copy.deepcopy(value);changed[field]=bad
            with self.subTest(field=field):self.refused(lambda:reader.parse_probe(self.raw(changed),'snapshot',pid=8021,uid=10421))

    def test_unknown_or_failed_fd_close_never_qualifies_alive_or_exited(self):
        for state in('alive','exited'):
            for field,bad in(('pidfd_closed',None),('pidfd_closed',False),('proc_closed',None),('proc_closed',False),
                             ('pidfd_opened',False),('proc_opened',False),('error','close'),('errno',5)):
                value=process_packet(state=state);value[field]=bad
                with self.subTest(state=state,field=field):self.refused(lambda:reader.parse_probe(self.raw(value),'snapshot',pid=8021,uid=10421))

    def test_raw_poll_event_bits_and_positive_ticks_are_never_relabelled(self):
        for revents in(1,16,17):
            value=process_packet(state='exited');value['poll_revents']=revents
            self.assertEqual(reader.parse_probe(self.raw(value),'snapshot',pid=8021,uid=10421),value)
        for state,field,bad in(('alive','poll_revents',1),('exited','poll_revents',0),('exited','poll_revents',2),
                               ('exited','poll_revents',32),('alive','start_ticks',0),('alive','start_ticks',True)):
            value=process_packet(state=state);value[field]=bad
            with self.subTest(state=state,field=field):self.refused(lambda:reader.parse_probe(self.raw(value),'snapshot',pid=8021,uid=10421))

    def test_boot_requires_no_process_or_fd_claim_and_canonical_uuid(self):
        for field,bad in(('pid',8021),('observed_uid',10421),('pidfd_opened',True),('proc_opened',True),('proc_closed',True),
                         ('poll_revents',0),('boot_id',BOOT.upper()),('boot_id','not-a-boot-id'),('errno',True)):
            value=process_packet(mode='boot');value[field]=bad
            with self.subTest(field=field):self.refused(lambda:reader.parse_probe(self.raw(value),'boot'))

    def test_packet_utf8_unique_keys_scalars_closed_schema_and_cap_are_strict(self):
        for raw in(b'',b'\xff',b'{"version":1,"version":1}',b'{"x":NaN}',b'{"x":Infinity}',b'{} trailing',b' '*4097):
            with self.subTest(raw=raw[:20]):self.refused(lambda:reader.validate_probe_packet(raw))
        for field,bad in(('version',True),('pid',True),('expected_uid',9999),('observed_uid',True),('start_ticks',1.5),
                         ('proc_opened',1),('private','SYNTHETIC_PRIVATE_CANARY')):
            value=process_packet();value[field]=bad
            with self.subTest(field=field):self.refused(lambda:reader.validate_probe_packet(self.raw(value)))


@unittest.skipUnless(os.name=='nt','physical D original closed graphs')
class RestartPrerequisiteGraphTests(unittest.TestCase):
    def refused(self,call):
        from benchmarks.receipt_avd_environment import EnvironmentRefused
        from benchmarks.android_instrumentation_evidence import EvidenceRefused
        with self.assertRaises((ValueError,EnvironmentRefused,EvidenceRefused,OSError)):call()
    def publish(self,g):g.prerequisite_pin=g.save(g.prerequisite_pin['path'],g.prerequisite)

    def test_complete_original_prerequisite_uses_actual_bound_readers_without_mutation(self):
        g=ClosedRestartGraph();before=copy.deepcopy(g.prerequisite);g.validate()
        self.assertEqual(g.prerequisite,before);self.assertEqual(len(g.rows),12)
        self.assertTrue(all(path.is_relative_to(g.base)for path in g.writes))
        self.assertNotEqual(PureWindowsPath(str(g.base)),r.GUEST_ROOT)

    def test_missing_extra_legacy_or_wrong_admission_fields_never_qualify(self):
        for change in(lambda v:v.pop('author_proof'),lambda v:v.update(protocol='original-author-restart-prerequisite-v0'),
                      lambda v:v.update(extra=True),lambda v:v['author_artifacts'].pop('worker-v2.json'),
                      lambda v:v['caller'].update(pid=999)):
            g=ClosedRestartGraph();change(g.prerequisite);self.publish(g);self.refused(g.validate)

    def test_selected_sdk_witness_order_and_operation_are_bound_not_just_success(self):
        for left,right in(('boot_initial','probe_after'),('import_instrumentation','author_instrumentation'),('force_stop','probe_before')):
            g=ClosedRestartGraph();g.prerequisite[left]=g.prerequisite[right];self.publish(g);self.refused(g.validate)

    def test_changed_boot_id_after_original_author_is_not_same_boot_death(self):
        g=ClosedRestartGraph();pid=g.author['process']['pid'];uid=g.author['process']['uid']
        g.mutate_stdout(12,g.encode(process_packet(pid=pid,uid=uid,state='absent',boot='9c1d9900-9a62-43fb-8440-c8be4364d762')))
        self.refused(g.validate)

    def test_wrong_pid_uid_or_still_alive_after_scoped_force_stop_refuses(self):
        for change in(dict(pid=8021),dict(uid=10422),dict(state='alive')):
            g=ClosedRestartGraph();values=dict(pid=g.author['process']['pid'],uid=g.author['process']['uid'],state='absent');values.update(change)
            g.mutate_stdout(12,g.encode(process_packet(**values)));self.refused(g.validate)

    def test_exited_pid_reuse_must_keep_original_before_kernel_start_ticks(self):
        g=ClosedRestartGraph();pid=g.author['process']['pid'];uid=g.author['process']['uid']
        g.mutate_stdout(12,g.encode(process_packet(pid=pid,uid=uid,state='exited',start=90002)));self.refused(g.validate)

    def test_wrapper_exit_zero_does_not_promote_refused_native_packet_or_unknown_fd_close(self):
        g=ClosedRestartGraph();value=process_packet(pid=g.author['process']['pid'],uid=g.author['process']['uid'])
        value.update(state='refused',error='close',errno=5,proc_closed=None)
        self.assertEqual(reader.validate_probe_packet(g.encode(value)),value)
        g.mutate_stdout(10,g.encode(value));self.assertEqual(g.rows[9]['returncode'],0);self.refused(g.validate)

    def test_original_baseline_and_actual_junit_must_pass_not_caller_summary(self):
        g=ClosedRestartGraph();g.mutate_stdout(3,b'OK (1 test)\n');self.refused(g.validate)
        g=ClosedRestartGraph();value=copy.deepcopy(g.author);value['review_sha256']='0'*64
        g.prerequisite['author_proof']=g.save(g.author_proof['path'],author_fixture.f.raw(value));self.publish(g);self.refused(g.validate)

    def test_package_uid_apk_hash_and_separate_claim_binding_cannot_be_swapped(self):
        g=ClosedRestartGraph();g.prerequisite['package_checks']['product']['uid']=g.prerequisite['package_checks']['tests']['uid'];self.publish(g);self.refused(g.validate)
        g=ClosedRestartGraph();g.mutate_stdout(6,('0'*64+'  /data/app/~~original-product/base.apk\n').encode());self.refused(g.validate)
        g=ClosedRestartGraph();path=g.root/'claims-v1/import-v1.json';value=g.env.read_json(path);value['prerequisite']=g.prerequisite_pin;g.save(path,value);self.refused(g.validate)

    def test_duplicate_qualified_import_or_author_cannot_borrow_one_spent_claim(self):
        for kind in('import','author'):
            with self.subTest(kind=kind):
                g=ClosedRestartGraph(duplicate_kind=kind);self.refused(g.validate)

    def test_same_byte_session_copy_outside_its_declared_sdk_root_is_not_authority(self):
        g=ClosedRestartGraph();g.prerequisite['session']=g.save(g.base/'borrowed-session-v5.json',Path(g.session['path']).read_bytes())
        self.publish(g);self.refused(g.validate)

    def test_same_byte_author_sidecar_copy_outside_canonical_collection_refuses(self):
        g=ClosedRestartGraph();name='worker-v2.json';original=g.prerequisite['author_artifacts'][name]
        g.prerequisite['author_artifacts'][name]=g.save(g.base/'borrowed-author'/name,Path(original['path']).read_bytes())
        self.publish(g);self.refused(g.validate)

    def test_qualified_sdk_tar_cannot_disagree_with_retained_original_author_files(self):
        g=ClosedRestartGraph();row=next(row for row in g.all_rows if row['label']=='sidecar-tar'and
            'no_backup/original-author-proof-v1/proof-v1.json'in row['operation']['argv'])
        original=Path(row['stdout']['path']).read_bytes();stream=io.BytesIO()
        with tarfile.open(fileobj=io.BytesIO(original),mode='r:')as source,tarfile.open(fileobj=stream,mode='w')as target:
            for member in source.getmembers():
                raw=source.extractfile(member).read()
                if member.name.endswith('/worker-v2.json'):raw=raw.replace(b'"',b' ',1)
                target.addfile(member,io.BytesIO(raw))
        row['stdout']=g.save(row['stdout']['path'],stream.getvalue());g.save(g.all_row_pins[row['index']-1]['path'],row)
        self.assertNotEqual(original,stream.getvalue());self.refused(g.validate)


if __name__=='__main__':unittest.main()
