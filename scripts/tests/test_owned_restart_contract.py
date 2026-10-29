"""Original fixed-profile restart authority fixtures; no device/kernel/model IO."""
import copy
import json
from pathlib import Path,PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import owned_restart_contract as r
from benchmarks import android_process_verification_v5 as reader
from benchmarks import owned_target_contract as legacy
from scripts.tests import test_owned_target_contract as f

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


if __name__=='__main__':unittest.main()
