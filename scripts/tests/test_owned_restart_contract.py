"""Original fixed-profile restart authority fixtures; no device/kernel/model IO."""
import copy
import json
from pathlib import Path,PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import owned_restart_contract as r
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
      observed_uid=uid,start_ticks=start,state=state,pidfd_opened=True,poll_revents=0,pidfd_closed=True,error=None,errno=0)
    if mode=='boot':value.update(pid=None,expected_uid=None,observed_uid=None,start_ticks=None,state='boot',pidfd_opened=False,poll_revents=None,pidfd_closed=None)
    elif state=='absent':value.update(observed_uid=None,start_ticks=None,pidfd_opened=False,poll_revents=None,pidfd_closed=None,errno=3)
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


if __name__=='__main__':unittest.main()
