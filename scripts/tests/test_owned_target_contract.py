"""Original owned-target metadata and byte-row adversaries; no live target IO."""
import copy
import hashlib
from pathlib import Path, PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import owned_target_contract as n
from scripts.tests import test_isolated_adb_lease as host_fixture


PROTOCOL='owned-emulator-target-v1'
SOURCE_NAMES=(*host_fixture.SOURCE_NAMES,'owned_target_contract.py','owned_target_owner.py',
              'android_process_client_v4.py','android_process_verification_v4.py')
MODEL_SHA='181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c'


def pin(path,*,size=101,sha=None):
    return dict(path=str(path),bytes=size,sha256=sha or hashlib.sha256(('original-target-fixture:'+str(path)).encode()).hexdigest())


def admission():
    root=PureWindowsPath('D:/Synthetic/owned-target-v1')
    server=host_fixture.admission();server.update(root=str(root/'server'),seconds=1200)
    sources=[pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks')/name)for name in SOURCE_NAMES]
    sources.sort(key=lambda item:item['path'])
    by_name={PureWindowsPath(item['path']).name:item for item in sources}
    server['sources']=[copy.deepcopy(by_name[PureWindowsPath(item['path']).name])for item in server['sources']]
    return dict(version=1,protocol=PROTOCOL,run_id=server['run_id'],root=str(root),seconds=1200,
      server=server,guest=dict(root='D:/Dev/Experiments/LocalLore/2026-10-28-author-player-contract-v1/avd-v1',
        proposal=pin('D:/Synthetic/guest-proposal.json'),authorization=pin('D:/Synthetic/guest-authorization.json'),
        emulator=pin('C:/Synthetic/Android/emulator/emulator.exe'),qemu=pin('C:/Synthetic/Android/emulator/qemu-system-x86_64.exe'),
        refuser=pin('D:/Synthetic/deny-adb-client.exe'),refuser_source=pin('D:/Synthetic/deny_adb_client.c'),
        console_port=5592,adb_port=5593,serial='emulator-5592',memory_mib=8192,cores=4,max_seconds=1800,api=35,abi='x86_64'),
      artifacts=dict(build=pin('D:/Synthetic/build-v1.json'),product_apk=pin('D:/Synthetic/product-debug.apk'),
        test_apk=pin('D:/Synthetic/test-debug.apk'),model=pin('D:/Synthetic/model.task',size=2588147712,sha=MODEL_SHA),
        probe=pin('D:/Synthetic/physical_model_probe_v1.txt')),
      sources=sources,python=copy.deepcopy(server['python']),compatibility={})


class AdmissionContractTests(unittest.TestCase):
    def refused(self,call):
        with self.assertRaises(n.TargetRefused)as error:call()
        self.assertNotIn('SYNTHETIC_PRIVATE_CANARY',str(error.exception))

    def test_complete_original_admission_copies_without_filesystem_or_native_io(self):
        value=admission();before=copy.deepcopy(value)
        with patch.object(Path,'open',side_effect=AssertionError('unexpected byte read')), \
             patch.object(Path,'stat',side_effect=AssertionError('unexpected metadata read')):
            result=n.validate_admission(value)
        self.assertEqual(result,before);result['guest']['memory_mib']=1;result['artifacts']['model']['bytes']=1
        self.assertEqual(value,before)

    def test_embedded_host_v2_is_not_target_authority(self):
        self.refused(lambda:n.validate_admission(host_fixture.admission()))
        value=admission();value['protocol']='isolated-adb-lease-v2'
        self.refused(lambda:n.validate_admission(value))

    def test_target_protocol_version_closed_keys_and_budget_are_strict(self):
        for field,bad in(('version',True),('version',2),('protocol','owned-emulator-target-v2'),
                         ('seconds',True),('seconds',1199),('seconds',1701),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            value=admission();value[field]=bad
            with self.subTest(field=field,bad=bad):self.refused(lambda:n.validate_admission(value))

    def test_target_and_embedded_server_root_run_budget_and_python_must_join(self):
        for key,bad in(('root','D:/Synthetic/foreign-server'),('run_id','f'*32),('seconds',1201)):
            value=admission();value['server'][key]=bad
            with self.subTest(key=key):self.refused(lambda:n.validate_admission(value))
        value=admission();value['server']['python']['executable']['sha256']='0'*64
        self.refused(lambda:n.validate_admission(value))

    def test_prepared_guest_identity_resource_profile_and_ports_cannot_be_retargeted(self):
        for key,bad in(('root','D:/Synthetic/other-avd'),('console_port',5594),('adb_port',5037),('serial','emulator-5594'),
                         ('memory_mib',4096),('cores',8),('max_seconds',1801),('api',34),('abi','arm64-v8a'),
                         ('console_port',True),('cores',True),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            value=admission();value['guest'][key]=bad
            with self.subTest(key=key,bad=bad):self.refused(lambda:n.validate_admission(value))

    def test_model_size_hash_and_all_artifact_roster_are_exact(self):
        for key,bad in(('bytes',True),('bytes',2588147711),('sha256','0'*64)):
            value=admission();value['artifacts']['model'][key]=bad
            with self.subTest(key=key):self.refused(lambda:n.validate_admission(value))
        value=admission();value['artifacts'].pop('probe');self.refused(lambda:n.validate_admission(value))
        value=admission();value['artifacts']['private_rows']='SYNTHETIC_PRIVATE_CANARY'
        self.refused(lambda:n.validate_admission(value))

    def test_complete_common_source_roster_is_not_a_nonempty_subset(self):
        for change in(lambda value:value['sources'].pop(),lambda value:value['sources'].reverse(),
                      lambda value:value['sources'][0].update(path='D:/Foreign/benchmarks/adb_held_socket.py')):
            value=admission();change(value);self.refused(lambda:n.validate_admission(value))
        value=admission();value['server']['sources'][0]['sha256']='0'*64
        self.refused(lambda:n.validate_admission(value))

    def test_target_project_paths_and_windows_aliases_are_refused(self):
        for bad in('C:/Synthetic/project','E:/Synthetic/project','relative','D:relative','D:/Synthetic/NUL',
                   'D:/Synthetic/project.','D:/Synthetic/project:stream','D:/Synthetic/../project'):
            value=admission();value['root']=bad
            with self.subTest(root=bad):self.refused(lambda:n.validate_admission(value))

    def test_target_stop_does_not_accept_old_protocol_or_arbitrary_process_controls(self):
        stop=dict(version=1,protocol=PROTOCOL,admission_sha256='a'*64,action='stop')
        self.assertIsNone(n.check_stop(stop,'a'*64))
        for change in(dict(protocol='isolated-adb-lease-v2'),dict(protocol='isolated-adb-lease-v1'),
                      dict(pid=123),dict(action='kill'),dict(version=True),dict(admission_sha256='b'*64)):
            value=dict(stop,**change);before=copy.deepcopy(value)
            with self.subTest(change=change):self.refused(lambda:n.check_stop(value,'a'*64))
            self.assertEqual(value,before)


class ObservationContractTests(unittest.TestCase):
    server=host_fixture.SERVER
    caller=host_fixture.CLIENT
    guest=dict(pid=7104,creation_filetime=1234567890124,executable='C:\\Synthetic\\Android\\qemu-system-x86_64.exe')

    def validate(self,value,*,after=False):
        return n.validate_observation(value,self.server,self.caller,host_fixture.endpoint(),self.guest,after=after)

    def refused(self,value,*,after=False):
        with self.assertRaises(n.TargetRefused):self.validate(value,after=after)

    def test_current_reciprocal_pid_ownership_is_independent_of_raw_tcp_states(self):
        for server_state,client_state in((0,1),(2,2),(5,5),(0xffffffff,9)):
            value=host_fixture.connected(server_state=server_state,client_state=client_state);before=copy.deepcopy(value)
            self.assertIsNone(self.validate(value));self.assertEqual(value,before)

    def test_current_pid_zero_missing_foreign_or_duplicate_rows_refuse_before_dispatch(self):
        for index in(1,2):
            for pid in(0,99999):
                rows=host_fixture.connected()['rows'];role='server'if index==1 else'client'
                rows[index]=host_fixture.row4(role=role,pid=pid,ordinal=rows[index]['ordinal'])
                with self.subTest(index=index,pid=pid):self.refused(host_fixture.observation(*rows))
            rows=host_fixture.connected()['rows'];rows.pop(index);self.refused(host_fixture.observation(*rows))
        rows=host_fixture.connected()['rows'];rows.append(host_fixture.row4(role='server',ordinal=12))
        self.refused(host_fixture.observation(*rows))

    def test_post_eof_mode_is_explicit_and_keeps_unique_owned_listener(self):
        self.assertIsNone(self.validate(host_fixture.observation(host_fixture.row4()),after=True))
        rows=host_fixture.connected()['rows'];rows[1]=host_fixture.row4(role='server',pid=0,ordinal=4)
        rows[2]=host_fixture.row4(role='client',pid=0,ordinal=8)
        self.assertIsNone(self.validate(host_fixture.observation(*rows),after=True));self.refused(host_fixture.observation(*rows))
        for value in(host_fixture.observation(),host_fixture.observation(host_fixture.row4(pid=0)),
                     host_fixture.observation(host_fixture.row4(),host_fixture.row4(ordinal=9))):
            self.refused(value,after=True)

    def test_auxiliary_rows_keep_only_scoped_server_caller_and_qemu_pid_allowances(self):
        for client_pid in(0,self.caller['pid'],self.guest['pid']):
            rows=host_fixture.connected()['rows']
            rows.extend((host_fixture.row4(role='server',rp=43109,pid=0,ordinal=10),
                         host_fixture.row4(role='client',lp=43109,pid=client_pid,ordinal=11)))
            value=host_fixture.observation(*rows);before=copy.deepcopy(value)
            self.assertIsNone(self.validate(value));self.assertEqual(value,before)
        for role,pid in(('server',self.guest['pid']),('client',99999)):
            rows=host_fixture.connected()['rows'];rows.append(host_fixture.row4(role=role,lp=43109 if role=='client'else None,
              rp=43109 if role=='server'else None,pid=pid,ordinal=10))
            self.refused(host_fixture.observation(*rows))

    def test_auxiliary_rows_cannot_hide_foreign_or_unscoped_endpoints(self):
        for row in(host_fixture.row4(role='client',lp=43109,remote='192.0.2.10',ordinal=10),
                   host_fixture.row4(role='client',lp=43109,rp=5037,ordinal=10),
                   host_fixture.row4(role='server',rp=43109,local='0.0.0.0',ordinal=10),
                   host_fixture.row6(ordinal=10)):
            self.refused(host_fixture.observation(*host_fixture.connected()['rows'],row))

    def test_raw_bytes_fields_family_roster_and_exact_scalar_types_must_agree(self):
        for field,bad in(('pid',True),('state',True),('ordinal',16384),('family',True),
                         ('raw_hex','00'),('local_port',True),('remote_port',5037),('local_scope_id',1)):
            value=host_fixture.connected();value['rows'][1][field]=bad
            with self.subTest(field=field):self.refused(value)
        for families in([2],[23,2],[True,23]):
            value=host_fixture.connected();value['families']=families;self.refused(value)
        for after in(0,1,None,'true'):
            with self.subTest(after=after):self.refused(host_fixture.connected(),after=after)


if __name__=='__main__':unittest.main()
