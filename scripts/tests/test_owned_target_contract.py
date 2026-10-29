"""Original owned-target metadata and byte-row adversaries; no live target IO."""
import copy
import hashlib
from pathlib import Path, PureWindowsPath
import struct
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
        emulator=pin('C:/Synthetic/Android/emulator/emulator.exe'),qemu=pin('C:/Synthetic/Android/emulator/qemu/windows-x86_64/qemu-system-x86_64.exe'),
        refuser=pin('D:/Synthetic/deny-adb-client.exe'),refuser_source=pin('D:/Synthetic/deny_adb_client.c'),
        console_port=5592,adb_port=5593,serial='emulator-5592',memory_mib=8192,cores=4,max_seconds=1800,api=35,abi='x86_64'),
      artifacts=dict(build=pin('D:/Synthetic/build-v1.json'),product_apk=pin('D:/Synthetic/product-debug.apk'),
        test_apk=pin('D:/Synthetic/test-debug.apk'),model=pin('D:/Synthetic/model.task',size=2588147712,sha=MODEL_SHA),
        probe=pin('D:/Synthetic/physical_model_probe_v1.txt')),
      sources=sources,python=copy.deepcopy(server['python']),compatibility=pin('D:/Synthetic/compatibility-review.md'))


def running(a=None):
    a=admission()if a is None else a
    def process(pid,path):return dict(pid=pid,creation_filetime=100000+pid,executable=path)
    owner=process(7101,a['python']['executable']['path']);worker=process(7102,a['python']['executable']['path'])
    server=process(7103,a['server']['adb']['path']);launcher=process(7104,a['guest']['emulator']['path'])
    guest=process(7105,a['guest']['qemu']['path'])
    return dict(version=1,protocol=PROTOCOL,admission=pin('D:/Synthetic/admission-v1.json'),run_id=a['run_id'],root=a['root'],
      owner=owner,worker=worker,server=server,launcher=launcher,guest=guest,guest_ancestry=[launcher,guest],
      started_epoch=1800000000.0,deadline_epoch=1800000000.0+a['seconds'],sdk_port=15937,console_port=5592,adb_port=5593,
      serial='emulator-5592',transport_id=7,sources=copy.deepcopy(a['sources']),python=copy.deepcopy(a['python']),
      ready=pin(PureWindowsPath(a['root'])/'target-ready-v1.json'))


def session(a=None):
    a=admission()if a is None else a;d=running(a)
    return dict(version=1,protocol='sdk-owned-target-v1',admission=d['admission'],
      running=pin(PureWindowsPath(a['root'])/'running-v1.json'),descriptor=d,caller=d['worker'],
      sources=copy.deepcopy(a['sources']),python=copy.deepcopy(a['python']),root='D:/Synthetic/sdk-v4',
      seconds=100,started_epoch=1800000010.0,deadline_epoch=1800000110.0)


def proof(s=None,*,after=False):
    s=session()if s is None else s;d=s['descriptor'];operation=dict(argv=['getprop','sys.boot_completed'],stdin=None)
    context=dict(index=1,phase='after'if after else'before',label='boot',operation_sha256=n.operation_digest(operation),transport_id=7)
    obs=host_fixture.observation(host_fixture.row4(pid=d['server']['pid']),
      host_fixture.row4(role='server',pid=d['server']['pid'],ordinal=4),host_fixture.row4(role='client',pid=s['caller']['pid'],ordinal=8))
    tables=[]
    for family,stride in((2,24),(23,56)):
        rows=[r for r in obs['rows']if r['family']==family];count=max((r['ordinal']for r in rows),default=-1)+1
        raw=bytearray(struct.pack('<I',count)+b'\0'*(count*stride))
        for row in rows:raw[4+row['ordinal']*stride:4+(row['ordinal']+1)*stride]=bytes.fromhex(row['raw_hex'])
        tables.append(dict(family=family,table_class=5,allocated_bytes=len(raw),returned_bytes=len(raw),count=count,
          raw_sha256=hashlib.sha256(raw).hexdigest(),abi_checked=True))
    bracket={k:copy.deepcopy(d[k])for k in('owner','worker','server','launcher','guest')}
    bracket.update(sources=s['sources'],python=s['python'],server_alive=True,guest_alive=True)
    devices=b'emulator-5592 device product:synthetic transport_id:7\n'
    return dict(version=1,protocol='owned-target-socket-proof-v1',session=pin(PureWindowsPath(s['root'])/'sdk-session-v4.json'),
      context=context,admission=s['admission'],running=s['running'],caller=s['caller'],endpoint=host_fixture.endpoint(),
      anchor=dict(handle=81,socket_id=12345,local_address='127.0.0.1',local_port=43101),
      brackets=dict(before=copy.deepcopy(bracket),after=copy.deepcopy(bracket)),observation=obs,tables=tables,
      version_response_hex=b'OKAY00040029'.hex(),devices_response_hex=(b'OKAY'+('%04x'%len(devices)).encode()+devices).hex(),
      after_request=after,elapsed_ms=1)


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


class RunningSessionRecipeTests(unittest.TestCase):
    def refused(self,call):
        with self.assertRaises(n.TargetRefused):call()

    def test_running_and_session_original_five_process_graph_copies(self):
        a=admission();d=running(a);s=session(a)
        self.assertEqual(n.validate_running(d,a,d['admission']),d);self.assertEqual(n.validate_session(s,a),s)
        changed=n.validate_running(d,a,d['admission']);changed['guest']['pid']=1;self.assertEqual(d['guest']['pid'],7105)

    def test_wrong_reused_guest_launcher_server_and_route_are_not_target_identity(self):
        a=admission()
        for key,field,bad in(('guest','pid',7104),('guest','executable',a['guest']['emulator']['path']),
                              ('server','executable','C:/Synthetic/foreign-adb.exe')):
            d=running(a);d[key][field]=bad
            with self.subTest(key=key,field=field):self.refused(lambda:n.validate_running(d,a,d['admission']))
        for key,bad in(('sdk_port',5037),('adb_port',5595),('console_port',True),('transport_id',True),('serial','127.0.0.1:5593')):
            d=running(a);d[key]=bad;self.refused(lambda:n.validate_running(d,a,d['admission']))

    def test_ancestry_source_ready_and_deadline_bindings_are_not_interchangeable(self):
        a=admission()
        for change in(lambda d:d['guest_ancestry'].reverse(),lambda d:d['guest_ancestry'].append(copy.deepcopy(d['guest'])),
                      lambda d:d.update(deadline_epoch=d['deadline_epoch']+1),lambda d:d['ready'].update(path='D:/Synthetic/ready.json'),
                      lambda d:d['sources'][0].update(sha256='0'*64)):
            d=running(a);change(d);self.refused(lambda:n.validate_running(d,a,d['admission']))

    def test_session_cannot_extend_lease_use_foreign_caller_or_legacy_sdk_protocol(self):
        a=admission()
        for change in(lambda s:s.update(protocol='sdk-owned-server-v3'),lambda s:s.update(caller=copy.deepcopy(s['descriptor']['guest'])),
                      lambda s:s.update(started_epoch=s['descriptor']['deadline_epoch'],deadline_epoch=s['descriptor']['deadline_epoch']+100),
                      lambda s:s['running'].update(path='D:/Synthetic/foreign-running.json')):
            s=session(a);change(s);self.refused(lambda:n.validate_session(s,a))

    def test_exact_read_recipes_and_binary_sources_validate_without_io(self):
        a=admission()
        operations=[dict(argv=['getprop','sys.boot_completed'],stdin=None),dict(argv=['screencap','-p'],stdin=None),
          dict(argv=['dd','of=/data/local/tmp/locallore-product-v1.apk','bs=65536'],stdin=a['artifacts']['product_apk']),
          dict(argv=['run-as',n.APP,'--user','0','dd','of=no_backup/original-author-source-v1/model.litertlm','bs=65536'],stdin=a['artifacts']['model'])]
        for value in operations:
            before=copy.deepcopy(value);self.assertEqual(n.validate_operation(value,a),before);self.assertEqual(value,before)
        self.assertNotEqual(n.operation_digest(operations[0]),n.operation_digest(operations[1]))

    def test_arbitrary_shell_global_adb_target_and_unbound_input_never_become_recipes(self):
        a=admission()
        for argv in(['sh','-c','id'],['adb','start-server'],['getprop'],['getprop','ro.serialno'],
                     ['run-as','foreign.package','--user','0','cat','files/x'],
                     ['run-as',n.APP,'--user','0','cat','no_backup/../secret'],['pm','install','/foreign.apk']):
            value=dict(argv=argv,stdin=None);self.refused(lambda:n.validate_operation(value,a))
        value=dict(argv=['dd','of=/data/local/tmp/locallore-product-v1.apk','bs=65536'],stdin=copy.deepcopy(a['artifacts']['product_apk']))
        value['stdin']['sha256']='0'*64;self.refused(lambda:n.validate_operation(value,a))
        self.refused(lambda:n.validate_operation(dict(argv=['getprop','sys.boot_completed'],stdin=a['artifacts']['probe']),a))

    def test_only_exact_two_instrumentation_methods_are_admitted(self):
        a=admission()
        for method in n.METHODS:
            value=dict(argv=['am','instrument','-w','-r','-e','class',n.CLASS+'#'+method,n.TEST+'/androidx.test.runner.AndroidJUnitRunner'],stdin=None)
            self.assertEqual(n.validate_operation(value,a),value)
        value['argv'][6]=n.CLASS+'#SYNTHETIC_PRIVATE_CANARY';self.refused(lambda:n.validate_operation(value,a))


class ProofContractTests(unittest.TestCase):
    def refused(self,value,s=None,context=None):
        with self.assertRaises(n.TargetRefused):n.validate_proof(value,session()if s is None else s,value['context']if context is None else context)

    def test_original_complete_before_and_after_proofs_retain_exact_states(self):
        for after in(False,True):
            value=proof(after=after);before=copy.deepcopy(value)
            self.assertEqual(n.validate_proof(value,session(),value['context']),before);self.assertEqual(value,before)

    def test_context_binding_process_source_and_same_socket_anchor_mutations_refuse(self):
        for change in(lambda p:p['context'].update(transport_id=8),lambda p:p['caller'].update(pid=99),
                      lambda p:p['brackets']['after']['guest'].update(pid=99),lambda p:p['brackets']['before'].update(server_alive=1),
                      lambda p:p['anchor'].update(local_port=43102),lambda p:p['brackets']['after']['sources'][0].update(sha256='0'*64)):
            value=proof();change(value);self.refused(value)
        value=proof();context=dict(value['context'],label='different');self.refused(value,context=context)

    def test_version_registered_serial_transport_and_exact_frames_are_required(self):
        for field,bad in(('version_response_hex',b'OKAY00040028'.hex()),('devices_response_hex',b'OKAY0000'.hex()),
                         ('after_request',True),('elapsed_ms',True),('elapsed_ms',15001)):
            value=proof();value[field]=bad
            with self.subTest(field=field):self.refused(value)
        for raw in(b'emulator-5594 device transport_id:7\n',b'emulator-5592 device transport_id:8\n',
                   b'emulator-5592 device transport_id:7\n127.0.0.1:5593 device transport_id:9\n'):
            value=proof();value['devices_response_hex']=(b'OKAY'+('%04x'%len(raw)).encode()+raw).hex();self.refused(value)

    def test_missing_family_abi_counts_ordinal_caps_and_private_extras_refuse(self):
        for change in(lambda p:p['tables'].pop(),lambda p:p['tables'][0].update(abi_checked=False),
                      lambda p:p['tables'][0].update(count=1),lambda p:p['tables'][0].update(returned_bytes=4),
                      lambda p:p.update(private_rows='SYNTHETIC_PRIVATE_CANARY')):
            value=proof();change(value);self.refused(value)


class GuestAndRecordTests(unittest.TestCase):
    def test_guest_ipv4_and_optional_ipv6_listeners_belong_to_qemu_not_launcher(self):
        d=running();rows=[host_fixture.row4(lp=5592,pid=d['guest']['pid'],ordinal=1),
          host_fixture.row4(lp=5593,pid=d['guest']['pid'],ordinal=2),
          host_fixture.row6(lp=5592,pid=d['guest']['pid'],ordinal=1),host_fixture.row6(lp=5593,pid=d['guest']['pid'],ordinal=2)]
        value=dict(version=1,ports=[5592,5593],families=[2,23],rows=rows)
        self.assertIsNone(n.validate_guest_observation(value,d['guest'],d['server']))
        for change in(lambda v:v['rows'].pop(0),lambda v:v['rows'][0].update(pid=d['launcher']['pid']),
                      lambda v:v.update(ports=[5593,5592])):
            changed=copy.deepcopy(value);change(changed)
            with self.assertRaises(n.TargetRefused):n.validate_guest_observation(changed,d['guest'],d['server'])

    def record(self):
        s=session();operation=dict(argv=['getprop','sys.boot_completed'],stdin=None)
        return dict(version=4,protocol='sdk-owned-target-v1',session=pin(PureWindowsPath(s['root'])/'sdk-session-v4.json'),
          index=1,label='boot',operation=operation,operation_sha256=n.operation_digest(operation),transport_id=7,
          status='completed',returncode=0,cleanup_complete=True,elapsed_ms=7,effective_deadline_ms=15000,
          stdout=pin(PureWindowsPath(s['root'])/'clients/command-0001.stdout.bin'),stderr=pin(PureWindowsPath(s['root'])/'clients/command-0001.stderr.bin'),
          stdin_sha256=None,stdin_bytes=0,stdin_complete=True,server_before=pin(PureWindowsPath(s['root'])/'proofs/command-0001-before.json'),
          server_after=pin(PureWindowsPath(s['root'])/'proofs/command-0001-after.json'),client_qualified=True,
          socket_closed=True,sender_joined=True,input_closed=True)

    def test_qualified_record_requires_actual_success_all_closure_and_both_proofs(self):
        value=self.record();self.assertEqual(n.validate_client_record(value,session()),value)
        for key,bad in(('returncode',1),('status','cancelled'),('cleanup_complete',False),('elapsed_ms',None),
                         ('stdin_complete',False),('socket_closed',False),('sender_joined',False),('input_closed',False),
                         ('server_before',None),('server_after',None),('client_qualified',1)):
            changed=copy.deepcopy(value);changed[key]=bad
            with self.subTest(key=key):
                with self.assertRaises(n.TargetRefused):n.validate_client_record(changed,session())

    def test_unqualified_partial_record_retains_measured_failure_without_inferred_success(self):
        value=self.record();value.update(client_qualified=False,status='cancelled',returncode=None,elapsed_ms=9,
          cleanup_complete=False,socket_closed=False,server_after=None)
        self.assertEqual(n.validate_client_record(value,session()),value)
        for key,bad in(('returncode',True),('elapsed_ms',True),('stdin_bytes',True),('operation_sha256','0'*64),('transport_id',8)):
            changed=copy.deepcopy(value);changed[key]=bad
            with self.subTest(key=key):
                with self.assertRaises(n.TargetRefused):n.validate_client_record(changed,session())



if __name__=='__main__':unittest.main()
