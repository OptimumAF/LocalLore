"""Original owned-target metadata and byte-row adversaries; no live target IO."""
import copy
import hashlib
import os
from pathlib import Path, PureWindowsPath
import struct
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

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
      queries=pin(PureWindowsPath(s['root'])/'proofs'/('command-0001-%s-queries-v1.json'%context['phase'])),
      after_request=after,elapsed_ms=1)


def query_bundle(s=None):
    s=session()if s is None else s;p=proof(s);queries=[]
    for kind,request,response in(('version',b'000Chost:version',p['version_response_hex']),
                                   ('devices',b'000Ehost:devices-l',p['devices_response_hex'])):
        queries.append(dict(kind=kind,request_hex=request.hex(),response_hex=response,endpoint=copy.deepcopy(p['endpoint']),
          anchor=copy.deepcopy(p['anchor']),brackets=copy.deepcopy(p['brackets']),observation_before=copy.deepcopy(p['observation']),
          observation_after=copy.deepcopy(p['observation']),tables_before=copy.deepcopy(p['tables']),tables_after=copy.deepcopy(p['tables']),
          eof=True,socket_closed=True,elapsed_ms=2))
    return dict(version=1,protocol='owned-target-socket-proof-v1',admission=s['admission'],running=s['running'],caller=s['caller'],queries=queries)


def table_metadata(observation):
    result=[]
    for family,stride in((2,24),(23,56)):
        rows=[row for row in observation['rows']if row['family']==family]
        count=max((row['ordinal']for row in rows),default=-1)+1;raw=bytearray(struct.pack('<I',count)+b'\0'*(count*stride))
        for row in rows:raw[4+row['ordinal']*stride:4+(row['ordinal']+1)*stride]=bytes.fromhex(row['raw_hex'])
        result.append(dict(family=family,table_class=5,allocated_bytes=len(raw),returned_bytes=len(raw),count=count,
          raw_sha256=hashlib.sha256(raw).hexdigest(),abi_checked=True))
    return result


def ready(a=None,d=None):
    a=admission()if a is None else a;d=running(a)if d is None else d
    obs=dict(version=1,ports=[5592,5593],families=[2,23],rows=[host_fixture.row4(lp=5592,pid=d['guest']['pid'],ordinal=1),
      host_fixture.row4(lp=5593,pid=d['guest']['pid'],ordinal=2)])
    return dict(version=1,protocol=PROTOCOL,admission=d['admission'],identities={key:copy.deepcopy(d[key])for key in('owner','worker','server','launcher','guest')},
      guest_ancestry=copy.deepcopy(d['guest_ancestry']),guest_job=pin(PureWindowsPath(a['root'])/'guest-job-v1.json'),
      guest_observation=obs,guest_tables=table_metadata(obs),queries=pin(PureWindowsPath(a['root'])/'target-registration-v1.json'),
      sources=copy.deepcopy(a['sources']),python=copy.deepcopy(a['python']))


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
    def test_actual_qemu_internal_adb_bridge_both_endpoints_are_owned_not_foreign(self):
        d=running();rows=[host_fixture.row4(lp=5592,pid=d['guest']['pid'],ordinal=1),
          host_fixture.row4(lp=5593,pid=d['guest']['pid'],ordinal=2),
          host_fixture.row4(role='server',lp=5593,rp=43150,pid=d['guest']['pid'],ordinal=10),
          host_fixture.row4(role='client',lp=43150,rp=5593,pid=d['guest']['pid'],ordinal=11)]
        value=dict(version=1,ports=[5592,5593],families=[2,23],rows=rows)
        with self.subTest(owner='actual-qemu'):
            self.assertIsNone(n.validate_guest_observation(value,d['guest'],d['server']))
        for pid in(d['launcher']['pid'],99999):
            changed=copy.deepcopy(value);changed['rows'][-1]=host_fixture.row4(role='client',lp=43150,rp=5593,pid=pid,ordinal=11)
            with self.subTest(owner='foreign',pid=pid):
                with self.assertRaises(n.TargetRefused):n.validate_guest_observation(changed,d['guest'],d['server'])

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


class QueryReadyJobTests(unittest.TestCase):
    def validate(self,value,*,require_device=True):
        s=session();return n.validate_query_bundle(value,s['descriptor'],s['caller'],s['admission'],s['running'],require_device=require_device)

    def test_complete_two_closed_original_guarded_queries_return_transport_without_io(self):
        value=query_bundle();before=copy.deepcopy(value)
        with patch.object(Path,'open',side_effect=AssertionError('unexpected IO')):
            self.assertEqual(self.validate(value),7)
        self.assertEqual(value,before)

    def test_query_pair_kind_request_and_closed_key_roster_cannot_be_borrowed(self):
        for change in(lambda v:v['queries'].reverse(),lambda v:v['queries'].pop(),
                      lambda v:v['queries'][0].update(kind='devices'),lambda v:v['queries'][0].update(request_hex=b'000Chost:devices'.hex()),
                      lambda v:v['queries'][0].update(private_rows='SYNTHETIC_PRIVATE_CANARY')):
            value=query_bundle();change(value)
            with self.assertRaises(n.TargetRefused):self.validate(value)

    def test_query_refuses_unknown_eof_cleanup_type_deadline_and_wrong_live_brackets(self):
        for key,bad in(('eof',False),('eof',1),('socket_closed',False),('elapsed_ms',True),('elapsed_ms',3001)):
            value=query_bundle();value['queries'][0][key]=bad
            with self.subTest(key=key):
                with self.assertRaises(n.TargetRefused):self.validate(value)
        value=query_bundle();value['queries'][0]['brackets']['after']['guest']['pid']=999
        with self.assertRaises(n.TargetRefused):self.validate(value)

    def test_query_before_requires_actual_caller_tuple_and_raw_table_bounds(self):
        for change in(lambda q:q['observation_before']['rows'].__setitem__(2,host_fixture.row4(role='client',pid=0,ordinal=8)),
                      lambda q:q['tables_before'][0].update(count=1),lambda q:q['anchor'].update(local_port=43102)):
            value=query_bundle();change(value['queries'][0])
            with self.assertRaises(n.TargetRefused):self.validate(value)

    def test_query_exact_frame_declared_length_and_registered_device_are_not_reply_only_authority(self):
        for raw in(b'OKAY00040028',b'OKAY0000',b'OKAY00040029X',b'FAIL0000'):
            value=query_bundle();value['queries'][0]['response_hex']=raw.hex()
            with self.assertRaises(n.TargetRefused):self.validate(value)
        value=query_bundle();value['queries'][1]['response_hex']=b'OKAY0000'.hex()
        with self.assertRaises(n.TargetRefused):self.validate(value)

    def test_only_explicit_startup_null_running_accepts_empty_or_owned_offline_prefix(self):
        s=session()
        for raw,expected in((b'',None),(b'emulator-5592 offline transport_id:7\n',7)):
            value=query_bundle();value['running']=None
            value['queries'][1]['response_hex']=(b'OKAY'+('%04x'%len(raw)).encode()+raw).hex()
            self.assertEqual(n.validate_query_bundle(value,s['descriptor'],s['caller'],s['admission'],None,require_device=False),expected)
            with self.assertRaises(n.TargetRefused):n.validate_query_bundle(value,s['descriptor'],s['caller'],s['admission'],None)
        with self.assertRaises(n.TargetRefused):self.validate(query_bundle(),require_device=False)
        for flag in(0,1,None,'false'):
            with self.assertRaises(n.TargetRefused):self.validate(query_bundle(),require_device=flag)

    def test_device_status_does_not_normalize_foreign_duplicate_or_unauthorized_targets(self):
        self.assertEqual(n.device_status(b''),('empty',None));self.assertEqual(n.device_status(b'emulator-5592 offline\n'),('offline',None))
        for raw in(b'emulator-5592 unauthorized transport_id:7\n',b'emulator-5594 device transport_id:7\n',
                   b'emulator-5592 device transport_id:7 transport_id:7\n',b'emulator-5592 device\n',
                   b'emulator-5592 device transport_id:7\n127.0.0.1:5593 device transport_id:8\n'):
            with self.assertRaises(n.TargetRefused):n.device_status(raw)

    def test_main_proof_requires_exact_bound_phase_query_path_not_old_inline_hex(self):
        for change in(lambda p:p.pop('queries'),lambda p:p['queries'].update(path='D:/Synthetic/inline-only.json'),
                      lambda p:p['queries'].update(path='D:/Synthetic/sdk-v4/proofs/command-0001-after-queries-v1.json')):
            value=proof();change(value)
            with self.assertRaises(n.TargetRefused):n.validate_proof(value,session(),value['context'])

    def test_startup_job_requires_actual_worker_all_held_processes_and_checked_receipt(self):
        d=running();identities={key:copy.deepcopy(d[key])for key in('worker','server','launcher','guest')}
        value=dict(version=1,protocol=PROTOCOL,worker=d['worker'],processes=sorted(p['pid']for p in identities.values()),
          identities=identities,checked=True,source='QueryInformationJobObject(NULL,JobObjectBasicProcessIdList)')
        self.assertEqual(n.validate_guest_job(value,d),value)
        for change in(lambda v:v.update(checked=1),lambda v:v['processes'].pop(),lambda v:v['processes'].append(v['processes'][0]),
                      lambda v:v['identities']['guest'].update(pid=d['launcher']['pid'])):
            bad=copy.deepcopy(value);change(bad)
            with self.assertRaises(n.TargetRefused):n.validate_guest_job(bad,d)

    def test_partial_guest_prefix_never_substitutes_for_complete_ready_listeners(self):
        d=running();value=dict(version=1,ports=[5592,5593],families=[2,23],rows=[])
        self.assertIsNone(n.validate_guest_prefix(value,d['guest'],d['server']))
        with self.assertRaises(n.TargetRefused):n.validate_guest_observation(value,d['guest'],d['server'])
        value['rows']=[host_fixture.row4(lp=5593,pid=999,ordinal=1)]
        with self.assertRaises(n.TargetRefused):n.validate_guest_prefix(value,d['guest'],d['server'])

    def test_ready_requires_complete_guest_actual_five_identities_and_bound_startup_evidence(self):
        a=admission();d=running(a);value=ready(a,d)
        self.assertEqual(n.validate_ready(value,d,a),value)
        for change in(lambda v:v['identities'].update(guest=copy.deepcopy(d['launcher'])),
                      lambda v:v['guest_ancestry'].reverse(),lambda v:v['guest_observation']['rows'].pop(),
                      lambda v:v['guest_job'].update(path='D:/Synthetic/foreign-job.json'),
                      lambda v:v['queries'].update(path='D:/Synthetic/legacy-v2-proof.json'),
                      lambda v:v['guest_tables'][0].update(count=1)):
            bad=copy.deepcopy(value);change(bad)
            with self.assertRaises(n.TargetRefused):n.validate_ready(bad,d,a)




class ClosedTargetFixture:
    """One complete original data-only graph, retained under physical D."""
    def __init__(self,*,instrument=False):
        from benchmarks import receipt_avd_environment as env
        self.env=env;self.base=Path(tempfile.mkdtemp(prefix='locallore-owned-graph-',dir='D:/Dev/_Temp'))
        self.a=admission();self.root=self.base/'lease';self.root.mkdir();self.a['root']=str(self.root);self.a['server']['root']=str(self.root/'server')
        self.admission=self.save(self.base/'admission-v1.json',self.a);self.d=running(self.a);self.d['admission']=self.admission
        self.running=self.save(self.root/'running-v1.json',self.d);self.s=session(self.a);self.s.update(admission=self.admission,running=self.running,descriptor=self.d,root=str(self.base/'sdk'))
        self.sdk=Path(self.s['root']);self.sdk.mkdir();(self.sdk/'clients').mkdir();(self.sdk/'proofs').mkdir()
        self.session=self.save(self.sdk/'sdk-session-v4.json',self.s)
        operation=dict(argv=['getprop','sys.boot_completed'],stdin=None)
        if instrument:operation['argv']=['am','instrument','-w','-r','-e','class',n.CLASS+'#'+n.METHODS[0],n.TEST+'/androidx.test.runner.AndroidJUnitRunner']
        digest=n.operation_digest(operation);proofs={}
        for phase in('before','after'):
            p=proof(self.s,after=phase=='after');p['session']=self.session;p['context'].update(operation_sha256=digest,label='command')
            path=self.sdk/'proofs'/('command-0001-'+phase+'.json')
            p['queries']=self.save(path.with_name(path.stem+'-queries-v1.json'),query_bundle(self.s));proofs[phase]=self.save(path,p)
        raw=self.sdk/'clients/command-0001.stdout.bin';raw.write_bytes(b'original\0\x1a\xff\r\n');err=raw.with_name('command-0001.stderr.bin');err.write_bytes(b'')
        self.row=GuestAndRecordTests().record();self.row.update(session=self.session,label='command',operation=operation,operation_sha256=digest,
          stdout=env.binding(raw),stderr=env.binding(err),server_before=proofs['before'],server_after=proofs['after'])
        self.record=self.save(self.sdk/'clients/command-0001.json',self.row)
        if instrument:
            (self.root/'claims-v1').mkdir();self.claim=self.save(self.root/'claims-v1/import-v1.json',dict(version=1,protocol=PROTOCOL,
              admission_sha256=self.admission['sha256'],kind='import',operation_sha256=digest,caller=self.s['caller']))

    def save(self,path,value):
        self.env.create_json(path,value);return self.env.binding(path)

    def rewrite(self,path,value):
        Path(path).write_bytes(self.env.encoded(value));return self.env.binding(path)

    def mutate_proof(self,phase,change):
        key='server_'+phase;p=self.env.read_json(self.row[key]['path']);change(p)
        self.row[key]=self.rewrite(self.row[key]['path'],p);self.record=self.rewrite(self.record['path'],self.row)

    def mutate_queries(self,phase,change):
        def update(p):
            q=self.env.read_json(p['queries']['path']);change(q);p['queries']=self.rewrite(p['queries']['path'],q)
        self.mutate_proof(phase,update)

    def validate(self):
        from benchmarks import android_process_verification_v4 as reader
        return reader.verify_client_record(self.record,self.s,self.a)


@unittest.skipUnless(os.name=='nt','physical D bound-file fixtures')
class ClosedTargetReaderTests(unittest.TestCase):
    def refused(self,call):
        from benchmarks.receipt_avd_environment import EnvironmentRefused
        with self.assertRaises((n.TargetRefused,EnvironmentRefused,OSError)):call()

    def test_complete_original_bound_binary_graph_replays_without_live_side_effects(self):
        from benchmarks import android_process_verification_v4 as reader
        f=ClosedTargetFixture()
        with patch.object(f.env,'process_identity',side_effect=AssertionError('no native identity')):
            self.assertEqual(f.validate(),f.row)
            self.assertEqual(reader.require_current_clients(f.sdk,1,f.session,f.a),[f.row])

    def test_raw_stdout_and_query_bytes_are_checked_against_bound_hashes(self):
        f=ClosedTargetFixture();Path(f.row['stdout']['path']).write_bytes(b'changed\0\x1a');self.refused(f.validate)
        f=ClosedTargetFixture();p=f.env.read_json(f.row['server_before']['path']);Path(p['queries']['path']).write_bytes(b'{}');self.refused(f.validate)

    def test_postproof_cannot_borrow_another_phase_context_or_owned_socket(self):
        for change in(lambda p:p['context'].update(phase='before'),lambda p:p['context'].update(label='foreign'),
                      lambda p:p['anchor'].update(handle=p['anchor']['handle']+1)):
            f=ClosedTargetFixture();f.mutate_proof('after',change);self.refused(f.validate)

    def test_complete_rebound_query_graph_still_requires_eof_closure_source_and_live_tuple(self):
        for change in(lambda q:q['queries'][0].update(eof=False),lambda q:q['queries'][0].update(socket_closed=False),
                      lambda q:q['queries'][0]['brackets']['after']['sources'][0].update(sha256='0'*64),
                      lambda q:q['queries'][0]['observation_before']['rows'].__setitem__(2,host_fixture.row4(role='client',pid=0,ordinal=8)),
                      lambda q:q['queries'].reverse()):
            f=ClosedTargetFixture();f.mutate_queries('before',change);self.refused(f.validate)

    def test_rebound_query_transport_cannot_replace_current_target_or_main_reply(self):
        f=ClosedTargetFixture()
        def change(q):
            raw=b'emulator-5592 device transport_id:8\n';q['queries'][1]['response_hex']=(b'OKAY'+('%04x'%len(raw)).encode()+raw).hex()
        f.mutate_queries('after',change);self.refused(f.validate)

    def test_bound_admission_running_and_session_contents_must_join_exactly(self):
        for field in('admission','running','session'):
            f=ClosedTargetFixture();binding=getattr(f,field);value=f.env.read_json(binding['path'])
            value['protocol']='isolated-adb-lease-v2';f.rewrite(binding['path'],value);self.refused(f.validate)

    def test_complete_output_does_not_qualify_unqualified_record(self):
        f=ClosedTargetFixture();f.row['client_qualified']=False;f.record=f.rewrite(f.record['path'],f.row);self.refused(f.validate)

    def test_current_client_reader_requires_exact_nonempty_contiguous_rosters(self):
        from benchmarks import android_process_verification_v4 as reader
        for folder in('clients','proofs'):
            f=ClosedTargetFixture();(f.sdk/folder/'unrelated.json').write_bytes(b'{}')
            self.refused(lambda:reader.require_current_clients(f.sdk,1,f.session,f.a))
        f=ClosedTargetFixture();self.refused(lambda:reader.require_current_clients(f.sdk,0,f.session,f.a))
        self.refused(lambda:reader.require_current_clients(f.sdk,2,f.session,f.a))

    def test_instrumentation_requires_original_once_claim_bound_to_actual_caller(self):
        f=ClosedTargetFixture(instrument=True);self.assertEqual(f.validate(),f.row)
        value=f.env.read_json(f.claim['path']);value['caller']['pid']=999;f.rewrite(f.claim['path'],value);self.refused(f.validate)


@unittest.skipUnless(os.name=='nt','physical D owned observer fixtures')
class ActualOwnerMockTests(unittest.TestCase):
    def setUp(self):
        from benchmarks import owned_target_owner as owner
        self.o=owner;self.f=ClosedTargetFixture();self.clock=100.0;self.wall=1800000010.0
        self.identities={p['pid']:copy.deepcopy(p)for p in(self.f.d[k]for k in('owner','worker','server','launcher','guest'))}
        self.caller=dict(pid=7106,creation_filetime=107106,executable=self.f.a['python']['executable']['path']);self.identities[7106]=self.caller
        self.handles={};self.closed=[];self.next_handle=100;self.bad_pid=None
        self.api=SimpleNamespace(open_process=self.open_process,identity=self.identity,alive=lambda handle:True,
          close_handle=self.close_handle,parent_pid=lambda handle:self.f.d['launcher']['pid'],current_job_pids=Mock())
        self.enter(patch.object(owner,'_ProcessApi',return_value=self.api));self.enter(patch.object(owner.os,'getpid',return_value=7106))
        self.enter(patch.object(owner.time,'monotonic',side_effect=lambda:self.clock));self.enter(patch.object(owner.time,'time',side_effect=lambda:self.wall))
        self.inputs=self.enter(patch.object(owner.contract,'revalidate_inputs'))
        self.enter(patch.object(owner.contract,'source_bindings',return_value=self.f.a['sources']))
        self.enter(patch.object(owner.file_guard,'_python_bindings',return_value=self.f.a['python']))
        self.observe=self.enter(patch.object(owner,'_observe',side_effect=self.capture))
        self.native_socket=self.enter(patch.object(owner.socket,'socket',side_effect=AssertionError('unmocked socket')))
        self.popen=self.enter(patch.object(owner.subprocess,'Popen',side_effect=AssertionError('no process launch')))
    def enter(self,context):
        value=context.__enter__();self.addCleanup(context.__exit__,None,None,None);return value
    def open_process(self,pid):
        self.next_handle+=1;self.handles[self.next_handle]=pid;return self.next_handle
    def identity(self,handle):
        pid=self.handles[handle]
        if pid==self.bad_pid:raise OSError('synthetic identity refusal')
        return copy.deepcopy(self.identities[pid])
    def close_handle(self,handle):self.closed.append(handle);return True
    def capture(self,api,*,guest=False):
        if guest:
            value=ready(self.f.a,self.f.d)['guest_observation']
        else:
            value=host_fixture.observation(host_fixture.row4(pid=self.f.d['server']['pid']),
              host_fixture.row4(role='server',pid=self.f.d['server']['pid'],ordinal=4),
              host_fixture.row4(role='client',pid=self.caller['pid'],ordinal=8))
        return value,table_metadata(value)
    def live(self):return self.o.LiveOwnedTarget(self.f.admission,self.f.running)

    def test_actual_live_constructor_holds_each_identity_returns_copies_and_closes_owned_handles(self):
        live=self.live();self.assertEqual(live.caller,self.caller);live.descriptor['guest']['pid']=99
        self.assertEqual(live.descriptor,self.f.d);self.assertTrue(live.close())
        self.assertEqual(set(self.closed),set(self.handles));self.api.current_job_pids.assert_not_called();self.native_socket.assert_not_called();self.popen.assert_not_called()

    def test_partial_identity_acquisition_closes_all_acquired_handles_without_launch(self):
        self.bad_pid=self.f.d['server']['pid']
        with self.assertRaises(self.o.OwnerRefused):self.live()
        self.assertEqual(set(self.closed),set(self.handles));self.assertGreater(len(self.closed),1);self.popen.assert_not_called()

    def test_actual_fast_guard_rejects_wall_expiry_monotonic_rollback_and_bound_stop(self):
        for mode in('wall','clock','stop'):
            self.clock=100;self.wall=1800000010;live=self.live()
            if mode=='wall':self.wall=self.f.d['deadline_epoch']
            elif mode=='clock':self.clock=99
            else:self.f.save(self.f.root/'stop-v1.json',dict(version=1,protocol=PROTOCOL,admission_sha256=self.f.admission['sha256'],action='stop'))
            with self.assertRaises(self.o.OwnerRefused):live.fast_guard()
            live.close()

    def test_concurrent_fast_guards_serialize_monotonic_read_check_and_update(self):
        live=self.live();older_read=threading.Event();newer_finished=threading.Event();errors=[]
        original_finite=self.o.math.isfinite
        def tick():return 100.1 if threading.current_thread().name=='target-older'else 100.2
        def finite(value):
            if threading.current_thread().name=='target-older'and value==100.1:
                older_read.set();newer_finished.wait(timeout=.1)
            return original_finite(value)
        def run():
            try:live.fast_guard()
            except BaseException as error:errors.append((threading.current_thread().name,type(error).__name__,str(error)))
            finally:
                if threading.current_thread().name=='target-newer':newer_finished.set()
        with patch.object(self.o.time,'monotonic',side_effect=tick),patch.object(self.o.math,'isfinite',side_effect=finite):
            older=threading.Thread(target=run,name='target-older');newer=threading.Thread(target=run,name='target-newer')
            older.start();self.assertTrue(older_read.wait(timeout=1));newer.start();older.join(timeout=2);newer.join(timeout=2)
        self.assertFalse(older.is_alive());self.assertFalse(newer.is_alive());self.assertEqual(errors,[],'overlapping valid monotonic samples must not manufacture rollback')
        live.close()

    def test_actual_claim_is_create_only_admission_wide_across_observers_and_spent_after_guard_failure(self):
        first=self.live();second=self.live();digest='a'*64;first.claim_once('import',digest)
        with self.assertRaises((self.o.OwnerRefused,self.o.output_control.ControlRefused,FileExistsError)):second.claim_once('import',digest)
        claim=self.f.env.read_json(self.f.root/'claims-v1/import-v1.json')
        self.assertEqual(n.validate_claim(claim,self.f.admission,self.caller,'import',digest),claim)
        original=first.guard;calls=0
        def after_claim_guard(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:raise self.o.OwnerRefused('source')
            return original(*args,**kwargs)
        with patch.object(first,'guard',side_effect=after_claim_guard):
            with self.assertRaises(self.o.OwnerRefused):first.claim_once('author','b'*64)
        self.assertTrue((self.f.root/'claims-v1/author-v1.json').is_file());first.close();second.close()

    def test_actual_query_uses_original_raw_tuple_before_send_and_records_exact_eof_closed_socket(self):
        from scripts.tests.test_android_process_client_v4 import FakeSocket
        live=self.live();sock=FakeSocket(b'OKAY00040029')
        with patch.object(self.o.socket,'socket',return_value=sock)as factory:
            record,failure=live._query('version')
        self.assertIsNone(failure);self.assertEqual(sock.sent,b'000Chost:version');self.assertEqual(sock.connects,[('127.0.0.1',15937)])
        self.assertTrue(record['eof']);self.assertTrue(record['socket_closed']);self.assertEqual(record['response_hex'],b'OKAY00040029'.hex())
        factory.assert_called_once();live.close()

    def test_query_foreign_current_pid_refuses_without_sending_or_retry(self):
        from scripts.tests.test_android_process_client_v4 import FakeSocket
        live=self.live();sock=FakeSocket(b'OKAY00040029');original=self.capture
        def capture(api,*,guest=False):
            value,tables=original(api,guest=guest)
            if not guest:value['rows'][2]=host_fixture.row4(role='client',pid=999,ordinal=8);tables=table_metadata(value)
            return value,tables
        with patch.object(self.o.socket,'socket',return_value=sock),patch.object(self.o,'_observe',side_effect=capture):
            record,failure=live._query('version')
        self.assertIsNotNone(failure);self.assertEqual(sock.sent,b'');self.assertTrue(record['socket_closed']);self.assertFalse(record['eof']);live.close()

    def test_runtime_constructor_and_bad_receipt_do_not_reach_auth_ports_or_processes(self):
        request=dict(validated_admission=self.f.a,admission=self.f.admission,owner=self.f.d['owner'])
        runtime=self.o._TargetRuntime(request,self.f.admission,self.f.root);runtime.worker=self.f.d['worker'];runtime.processes=SimpleNamespace(guard=Mock())
        self.f.save(self.f.root/'started-v1.json',dict(worker=dict(runtime.worker,pid=99),request=self.f.admission))
        with patch.object(self.o.primitives.AuthKeyGuard,'open')as auth,patch.object(self.o,'_guest_preflight')as ports:
            with self.assertRaises(self.o.OwnerRefused):runtime.wait_receipt()
        auth.assert_not_called();ports.assert_not_called();self.popen.assert_not_called();self.native_socket.assert_not_called()

    def test_current_job_return_struct_requires_complete_bounded_unique_positive_pid_roster(self):
        api=object.__new__(self.o._ProcessApi)
        def acquire(*,assigned=4,pids=(7102,7103,7104,7105),returned=None,success=True):
            def call(job,kind,pointer,size,returned_pointer):
                self.assertIsNone(job);self.assertEqual(kind,3)
                value=self.o.ctypes.cast(pointer,self.o.ctypes.POINTER(self.o._JobProcessIds)).contents
                value.assigned=assigned;value.count=len(pids)
                for i,pid in enumerate(pids):value.pids[i]=pid
                count=8+len(pids)*self.o.ctypes.sizeof(self.o.ctypes.c_size_t)if returned is None else returned
                self.o.ctypes.cast(returned_pointer,self.o.ctypes.POINTER(self.o.wintypes.DWORD)).contents.value=count
                return success
            api._job=call;return api.current_job_pids()
        self.assertEqual(acquire(),[7102,7103,7104,7105])
        for change in(dict(assigned=5),dict(pids=(7102,7102)),dict(pids=(0,7102)),dict(returned=8),dict(success=False)):
            with self.subTest(change=change):
                with self.assertRaises(self.o.OwnerRefused):acquire(**change)

    def test_parent_pbi_native_return_struct_binds_queried_pid_size_and_actual_parent(self):
        api=object.__new__(self.o._ProcessApi);api.identity=lambda handle:self.f.d['guest']
        def acquire(*,status=0,size=48,pid=None,parent=None):
            def call(handle,kind,pointer,length,returned_pointer):
                self.assertEqual((handle,kind,length),(901,0,48))
                value=self.o.ctypes.cast(pointer,self.o.ctypes.POINTER(self.o._BasicProcessInformation)).contents
                value.pid=self.f.d['guest']['pid']if pid is None else pid
                value.parent_pid=self.f.d['launcher']['pid']if parent is None else parent
                self.o.ctypes.cast(returned_pointer,self.o.ctypes.POINTER(self.o.wintypes.ULONG)).contents.value=size
                return status
            api._basic=call;return api.parent_pid(901)
        self.assertEqual(acquire(),self.f.d['launcher']['pid'])
        for change in(dict(status=1),dict(size=47),dict(pid=999),dict(parent=0)):
            with self.subTest(change=change):
                with self.assertRaises(self.o.OwnerRefused):acquire(**change)

    def test_cleanup_terminates_actual_held_guest_before_launcher_then_server_and_retains_uncertainty(self):
        for wait_fails in(False,True):
            events=[]
            def child(name):
                handle=SimpleNamespace(closed=False)
                handle.Close=lambda:(events.append(name+'-close'),setattr(handle,'closed',True))
                return SimpleNamespace(poll=lambda:None,terminate=lambda:events.append(name+'-terminate'),
                  wait=lambda timeout:(events.append(name+'-wait')or 7),_handle=handle)
            def wait(handle):
                events.append('qemu-wait')
                if wait_fails:raise OSError('uncertain actual VM exit')
                return 1
            runtime=SimpleNamespace(root=self.f.base/('cleanup-'+str(wait_fails)),guest_stop_verified=True,guest_stop_handle=901,
              guest=self.f.d['guest'],server=self.f.d['server'],launcher=self.f.d['launcher'],
              api=SimpleNamespace(alive=lambda handle:True,terminate_guest=lambda handle:events.append('qemu-terminate'),wait_guest=wait),
              processes=SimpleNamespace(release=lambda handle:(events.append('qemu-close')or True),close=lambda:True),
              guest_child=child('launcher'),child=child('server'),capture=None,guest_capture=None,auth=SimpleNamespace(close=lambda:True),clients_closed=True)
            runtime.root.mkdir();cleanup,*_=self.o._cleanup(runtime,dict(created_mask=1,close_attempted_mask=1,closed_mask=1),
              dict(created_mask=15,close_attempted_mask=15,closed_mask=15))
            self.assertLess(events.index('qemu-wait'),events.index('launcher-terminate'))
            if wait_fails:self.assertNotIn('server-terminate',events);self.assertFalse(cleanup['guest_wait_completed'])
            else:self.assertLess(events.index('launcher-wait'),events.index('server-terminate'));self.assertTrue(cleanup['guest_process_handle_closed'])


class ClosedLifecycleFixture:
    """Every write is contained in a new synthetic D tree, never the prepared AVD."""
    def __init__(self):
        from benchmarks import receipt_avd_environment as env
        self.env=env;self.base=Path(tempfile.mkdtemp(prefix='locallore-target-lifecycle-',dir='D:/Dev/_Temp')).resolve(strict=True)
        self.root=self.base/'owner';self.guest_root=self.base/'synthetic-guest';self.writes=[]
        self.a=admission();self.a.update(root=str(self.root));self.a['server']['root']=str(self.root/'server');self.a['guest']['root']=str(self.guest_root)
        config=self.save(self.guest_root/'avd/config.ini',b'avd.name=synthetic\n')
        prepare_proposal=self.save(self.base/'prepare-proposal.json',dict(original='synthetic data only'))
        prepared=self.save(self.base/'prepared.json',dict(proposal_sha256=prepare_proposal['sha256'],avd_name='locallore_receipt_api35_v1',
          guest_boot_verified=False,userdata_absent=True,immutable=[config]))
        prepare_result=self.save(self.base/'prepare-result.json',dict(version=1,proposal_sha256=prepare_proposal['sha256'],status='completed',
          closure_verified=True,child_cleanup_complete=True,prepared_created=True))
        proposal=dict(version=1,phase='run',paths=dict(root=str(self.guest_root)),serial='emulator-5592',memory_mib=8192,cores=4,
          max_seconds=1800,console_port=5592,adb_path=self.a['server']['adb']['path'],prepared=prepared,prepare_result=prepare_result,
          prepare_proposal=prepare_proposal,token=dict(original_metadata='synthetic token metadata, no credential bytes'),
          old_avd=dict(original_metadata='synthetic old registry'),bindings=[pin('C:/Synthetic/installed-sdk-tool.exe')],host_free_min={'D:':40*1024**3})
        self.a['guest']['proposal']=self.save(self.base/'run-proposal.json',proposal)
        self.a['guest']['authorization']=self.save(self.base/'run-authorization.json',dict(version=1,phase='run',
          proposal_sha256=self.a['guest']['proposal']['sha256'],allow_environment_calls=True,root_go_pending=False))
        self.admission=self.save(self.base/'admission-v1.json',self.a);self.d=running(self.a);self.d['admission']=self.admission
        script=next(p for p in self.a['sources']if PureWindowsPath(p['path']).name=='owned_target_owner.py')
        self.request=self.save(self.root/'request-v1.json',dict(version=1,protocol=PROTOCOL,admission=self.admission,validated_admission=self.a,
          owner=self.d['owner'],sources=self.a['sources'],python=self.a['python'],worker_script=script,owner_seconds=1230))
        self.auth=dict(path=self.a['server']['auth_key'],native_profile='C:\\Users\\Synthetic',metadata=dict(volume_serial=3,file_index=9,
          bytes=2048,attributes=0x20,creation_filetime=1001,write_filetime=1002,links=1))
        empty=host_fixture.observation();pre=dict(observation=empty,tables=table_metadata(empty),created_mask=1,close_attempted_mask=1,closed_mask=1,exclusive_bind_succeeded=True)
        preflight=self.save(self.root/'server/preflight-v1.json',pre)
        guest_empty=dict(version=1,ports=[5592,5593],families=[2,23],rows=[])
        guest_preflight=self.save(self.root/'guest-preflight-v1.json',dict(observation=guest_empty,tables=table_metadata(guest_empty),
          created_mask=15,close_attempted_mask=15,closed_mask=15,exclusive_bind_succeeded=True))
        server_admission=self.save(self.root/'server/admission-v1.json',self.a['server'])
        helper=SimpleNamespace(admission=self.a['server'],admission_pin=server_admission,auth=self.auth,tables=table_metadata)
        for kind,port,history in(('version',43101,()),('devices',43102,(43101,))):
            p=host_fixture.ClosedLeaseFixture.proof(helper,kind,port,history)
            p.update(worker=self.d['worker'],client=self.d['worker'],server=self.d['server'])
            for b in p['brackets'].values():b.update(worker=self.d['worker'],server=self.d['server'])
            self.save(self.root/'server'/('proof-'+kind+'-v1.json'),p)
        obs=host_fixture.observation(host_fixture.row4(pid=self.d['server']['pid']))
        self.save(self.root/'server/readiness-v1.json',[dict(observation=obs,tables=table_metadata(obs))])
        identities={key:copy.deepcopy(self.d[key])for key in('worker','server','launcher','guest')}
        job=self.save(self.root/'guest-job-v1.json',dict(version=1,protocol=PROTOCOL,worker=self.d['worker'],
          processes=sorted(p['pid']for p in identities.values()),identities=identities,checked=True,
          source='QueryInformationJobObject(NULL,JobObjectBasicProcessIdList)'))
        s=session(self.a);s.update(admission=self.admission,running=None,descriptor=self.d,caller=self.d['worker'])
        registration=self.save(self.root/'target-registration-v1.json',query_bundle(s))
        ready_value=ready(self.a,self.d);ready_value.update(guest_job=job,queries=registration)
        ready_pin=self.save(self.root/'target-ready-v1.json',ready_value);self.d['ready']=ready_pin
        running_pin=self.save(self.root/'running-v1.json',self.d)
        readiness=self.save(self.root/'readiness-v1.json',[
          dict(elapsed_ms=1,stage='guest_process',observation=None,tables=None,queries=None),
          dict(elapsed_ms=2,stage='guest_ports',observation=ready_value['guest_observation'],tables=ready_value['guest_tables'],queries=None),
          dict(elapsed_ms=3,stage='registration',observation=ready_value['guest_observation'],tables=ready_value['guest_tables'],queries=registration)])
        guest_inputs=self.save(self.root/'guest-inputs-v1.json',dict(version=1,protocol=PROTOCOL,admission=self.admission,
          proposal=self.a['guest']['proposal'],authorization=self.a['guest']['authorization'],prepared=prepared,prepare_result=prepare_result,
          token=proposal['token'],original_avd=proposal['old_avd'],configuration=[config],tools=proposal['bindings'],
          facts=dict(free_bytes={'D:':50*1024**3},available_memory=16*1024**3,logical_cpus=12,commit_capacity={}),
          timer=dict(key='test.quitAfterBootTimeOut',actual=None,effective=-1,default_used=True,enabled=False)))
        boot=self.save(self.guest_root/'owned-target-boot-claim-v1.json',dict(version=1,protocol=PROTOCOL,admission=self.admission,
          worker=self.d['worker'],proposal=self.a['guest']['proposal']))
        terminal=self.save(self.root/'guest-terminal-v1.json',dict(version=1,protocol=PROTOCOL,guest=self.d['guest'],
          terminate_attempted=True,wait_completed=True,returncode=1,handle_closed=True))
        self.result=dict(version=1,protocol=PROTOCOL,admission=self.admission,request=self.request,worker=self.d['worker'],
          server=self.d['server'],launcher=self.d['launcher'],guest=self.d['guest'],guest_ancestry=self.d['guest_ancestry'],auth=self.auth,
          preflight=preflight,guest_preflight=guest_preflight,readiness=readiness,ready=ready_pin,running=running_pin,
          server_capture=self.capture('server',self.d['server'],7),guest_capture=self.capture('guest',self.d['launcher'],1),
          server_returncode=7,guest_returncode=1,reason='stop_requested',cleanup={key:True for key in n.CLEANUP_KEYS},
          sources_after=dict(sources=self.a['sources'],python=self.a['python'],tools=self.a['server']['tools'],auth=self.auth),
          stop_requested=True,elapsed_ms=1000,guest_job=job,guest_inputs=guest_inputs,guest_terminal=terminal,boot_claim=boot)
        self.save(self.root/'stop-v1.json',dict(version=1,protocol=PROTOCOL,admission_sha256=self.admission['sha256'],action='stop'))
        self.result_pin=self.save(self.root/'worker-result-v1.json',self.result)

    def save(self,path,value):
        path=Path(path).resolve(strict=False)
        if path.drive.upper()!='D:'or not path.is_relative_to(self.base):raise AssertionError('synthetic write escaped test root')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value if type(value)is bytes else self.env.encoded(value));self.writes.append(path)
        return self.env.binding(path)

    def capture(self,kind,identity,code):
        stdout=self.save(self.root/(kind+'-output-v1/owner-stdout-v1.bin'),b'original synthetic '+kind.encode()+b' output\n')
        stderr=self.save(self.root/(kind+'-output-v1/owner-stderr-v1.bin'),b'')
        return self.save(self.root/(kind+'-capture-v1.json'),dict(version=1,protocol=PROTOCOL,server=identity,status='terminated',returncode=code,
          stdout=stdout,stderr=stderr,stdout_bytes=stdout['bytes'],stderr_bytes=0,capture_complete=True,pipes_closed=True))

    def mutate(self,key,change):
        value=self.env.read_json(self.result[key]['path']);change(value);self.result[key]=self.save(self.result[key]['path'],value)
        self.result_pin=self.save(self.result_pin['path'],self.result)

    def validate(self):
        from benchmarks import android_process_verification_v4 as reader
        with patch.object(n,'GUEST_ROOT',PureWindowsPath(str(self.guest_root))),patch.object(n,'revalidate_inputs'):
            return reader.verify_owned_target_result(self.result_pin,self.a,self.admission,self.request,self.d['worker'])


@unittest.skipUnless(os.name=='nt','physical D synthetic full lifecycle graph')
class ClosedLifecycleReaderTests(unittest.TestCase):
    def refused(self,call):
        from benchmarks.receipt_avd_environment import EnvironmentRefused
        with self.assertRaises((n.TargetRefused,EnvironmentRefused,OSError)):call()

    def test_complete_original_lifecycle_graph_replays_with_all_writes_in_synthetic_tree(self):
        original=n.GUEST_ROOT;f=ClosedLifecycleFixture();self.assertEqual(f.validate(),f.result)
        self.assertEqual(n.GUEST_ROOT,original);self.assertTrue(all(p.is_relative_to(f.base)for p in f.writes))
        self.assertNotEqual(PureWindowsPath(str(f.guest_root)),original);self.assertEqual(f.result['server_returncode'],7)

    def test_every_failed_cleanup_flag_and_missing_required_stage_refuses(self):
        f=ClosedLifecycleFixture()
        for key in n.CLEANUP_KEYS:
            value=copy.deepcopy(f.result);value['cleanup'][key]=False;f.result_pin=f.save(f.result_pin['path'],value);self.refused(f.validate)
        f.result_pin=f.save(f.result_pin['path'],f.result)
        for key in('guest_inputs','guest_terminal','boot_claim','ready','guest_job','server_capture'):
            value=copy.deepcopy(f.result);value[key]=None;f.result_pin=f.save(f.result_pin['path'],value);self.refused(f.validate)

    def test_bound_capture_counts_process_identity_and_actual_terminal_return_are_required(self):
        for key,change in(('server_capture',lambda v:v.update(stdout_bytes=v['stdout_bytes']+1)),
                           ('guest_capture',lambda v:v['server'].update(pid=999)),
                           ('guest_terminal',lambda v:v.update(wait_completed=False)),
                           ('guest_terminal',lambda v:v.update(handle_closed=False))):
            f=ClosedLifecycleFixture();f.mutate(key,change);self.refused(f.validate)

    def test_guest_authorization_timer_and_prepared_configuration_cannot_be_reinterpreted(self):
        for change in(lambda v:v['timer'].update(actual='60',effective=60,default_used=False,enabled=True),
                      lambda v:v['facts'].update(available_memory=4*1024**3),
                      lambda v:v.update(proposal=pin('D:/Synthetic/foreign-proposal.json'))):
            f=ClosedLifecycleFixture();f.mutate('guest_inputs',change);self.refused(f.validate)

    def test_raw_table_abi_masks_query_closure_and_job_membership_fail_closed(self):
        for key,change in(('guest_preflight',lambda v:v.update(closed_mask=7)),
                           ('ready',lambda v:v['guest_tables'][0].update(abi_checked=False)),
                           ('guest_job',lambda v:v['processes'].pop())):
            f=ClosedLifecycleFixture();f.mutate(key,change);self.refused(f.validate)


if __name__=='__main__':unittest.main()
