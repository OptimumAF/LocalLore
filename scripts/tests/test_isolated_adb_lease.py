"""Original isolated-lease metadata and raw-row adversaries. Never start ADB.

Pins below describe synthetic values, not an authenticated build or live lease.
No profile key, service, device, emulator, model or private capture is opened.
"""
import copy
import hashlib
import ipaddress
import math
import os
from pathlib import Path,PureWindowsPath
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from benchmarks import isolated_adb_lease as n


PROTOCOL='isolated-adb-lease-v1'
PORT=15937
CLIENT_PORT=43101
OLD_PORT=43102
OLDER_PORT=43103
ADB_SHA='b4a6b455702684652cccf7b46258b29e653538904359a58fd4931cf3ef286b3f'
TOOL_DIR=PureWindowsPath('C:/Synthetic/platform-tools')
PYTHON='C:\\Synthetic\\Python\\python.exe'
SERVER=dict(pid=7103,creation_filetime=1234567890123,executable=str(TOOL_DIR/'adb.exe'))
CLIENT=dict(pid=7102,creation_filetime=1234567890122,executable=PYTHON)
OWNER=dict(pid=7101,creation_filetime=1234567890121,executable=PYTHON)
SOURCE_NAMES=('adb_held_socket.py','adb_held_socket_probe.py','adb_held_socket_windows.py',
 'windows_tcp_control.py','windows_tcp_observation.py','receipt_avd_environment.py',
 'runtime_spike.py','host_commit_capacity.py','isolated_adb_lease.py','isolated_adb_owner.py')


def pin(path,*,sha=None,size=101):
    return dict(path=str(path),bytes=size,sha256=sha or hashlib.sha256(('synthetic:'+str(path)).encode()).hexdigest())


def admission():
    tools=[pin(TOOL_DIR/name,sha=ADB_SHA if name=='adb.exe'else None)
           for name in('adb.exe','AdbWinApi.dll','AdbWinUsbApi.dll','libwinpthread-1.dll','source.properties','NOTICE.txt')]
    tools.sort(key=lambda p:p['path'])
    sources=[pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks')/name)for name in SOURCE_NAMES]
    sources.sort(key=lambda p:p['path'])
    return dict(version=1,protocol=PROTOCOL,run_id='0123456789abcdef0123456789abcdef',
      root='D:\\Synthetic\\packet\\lease-v1',port=PORT,seconds=120,
      adb=copy.deepcopy(next(p for p in tools if PureWindowsPath(p['path']).name=='adb.exe')),
      tools=tools,sdk_version='37.0.1-15733141',expected_version='0029',sources=sources,
      python=dict(executable=pin(PYTHON),runtime_dll=pin('C:\\Synthetic\\Python\\python314.dll')),
      auth_key='C:\\Users\\Synthetic\\.android\\adbkey',
      capabilities=pin('D:\\Synthetic\\packet\\capabilities-v1.json'),
      source_review=pin('D:\\Synthetic\\packet\\source-review-v1.md'))


def admitted_binding():return pin('D:\\Synthetic\\packet\\admission-v1.json')


def running(value=None):
    value=admission()if value is None else value
    return dict(version=1,protocol=PROTOCOL,admission=admitted_binding(),run_id=value['run_id'],port=PORT,
      owner=copy.deepcopy(OWNER),worker=copy.deepcopy(CLIENT),server=copy.deepcopy(SERVER),
      started_epoch=1800000000.25,deadline_epoch=1800000000.25+value['seconds'],sources=copy.deepcopy(value['sources']),
      adb=copy.deepcopy(value['adb']),version_proof=pin(PureWindowsPath(value['root'])/'proof-version-v1.json'),
      devices_proof=pin(PureWindowsPath(value['root'])/'proof-devices-v1.json'))


def endpoint():
    return dict(local_address='127.0.0.1',local_port=CLIENT_PORT,peer_address='127.0.0.1',peer_port=PORT)


def row4(*,role='listener',state=0,pid=None,ordinal=1,local='127.0.0.1',remote=None,lp=None,rp=None,high=0):
    if role=='listener':local_port,remote_port,address=PORT,0,'0.0.0.0';owner=SERVER['pid']
    elif role=='server':local_port,remote_port,address=PORT,CLIENT_PORT,'127.0.0.1';owner=SERVER['pid']
    elif role=='client':local_port,remote_port,address=CLIENT_PORT,PORT,'127.0.0.1';owner=CLIENT['pid']
    else:raise ValueError('synthetic role')
    local_port=local_port if lp is None else lp;remote_port=remote_port if rp is None else rp
    address=address if remote is None else remote;owner=owner if pid is None else pid
    a=lambda text:int.from_bytes(ipaddress.IPv4Address(text).packed,'little')
    p=lambda port:high|int.from_bytes(port.to_bytes(2,'big'),'little')
    raw=struct.pack('<6I',state,a(local),p(local_port),a(address),p(remote_port),owner)
    return dict(family=2,local_address=local,local_port=local_port,remote_address=address,remote_port=remote_port,
      local_scope_id=0,remote_scope_id=0,state=state,pid=owner,ordinal=ordinal,raw_hex=raw.hex())


def row6(*,state=0,pid=None,ordinal=1,local='::1',remote='::',lp=PORT,rp=0,local_scope=0,remote_scope=0):
    p=lambda port:int.from_bytes(port.to_bytes(2,'big'),'little')
    scope=lambda number:int.from_bytes(number.to_bytes(4,'big'),'little')
    owner=SERVER['pid']if pid is None else pid
    raw=struct.pack('<16sII16sIIII',ipaddress.IPv6Address(local).packed,scope(local_scope),p(lp),
      ipaddress.IPv6Address(remote).packed,scope(remote_scope),p(rp),state,owner)
    return dict(family=23,local_address=local,local_port=lp,remote_address=remote,remote_port=rp,
      local_scope_id=local_scope,remote_scope_id=remote_scope,state=state,pid=owner,ordinal=ordinal,raw_hex=raw.hex())


def observation(*rows):return dict(version=1,port=PORT,rows=list(rows),families=[2,23])


def connected(*,server_state=0,client_state=1):
    return observation(row4(ordinal=1),row4(role='server',state=server_state,ordinal=4),
                       row4(role='client',state=client_state,ordinal=8))


class AdmissionTests(unittest.TestCase):
    def refused(self,call):
        with self.assertRaises(n.LeaseRefused)as error:call()
        self.assertNotIn('SYNTHETIC_PRIVATE_CANARY',str(error.exception))

    def test_complete_synthetic_admission_is_copied_without_io_or_key_access(self):
        value=admission();before=copy.deepcopy(value)
        with patch.object(Path,'open',side_effect=AssertionError('file open')), \
             patch.object(Path,'stat',side_effect=AssertionError('file stat')), \
             patch.object(Path,'lstat',side_effect=AssertionError('file lstat')):
            result=n.validate_admission(value)
        self.assertEqual(result,before);result['tools'][0]['sha256']='0'*64
        result['sources'][0]['bytes']+=1;result['python']['executable']['bytes']+=1
        self.assertEqual(value,before)

    def test_top_level_keys_protocol_bounds_and_exact_scalar_types(self):
        for field,bad in(('version',True),('version',2),('protocol','SDK3'),('run_id','A'*32),('run_id','f'*31),
                         ('port',5037),('port',True),('seconds',True),('seconds',29),('seconds',1701),
                         ('sdk_version','37.0.0'),('expected_version','002A'),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            value=admission();value[field]=bad
            with self.subTest(field=field,bad=bad):self.refused(lambda:n.validate_admission(value))
        for seconds in(30,1700):
            value=admission();value['seconds']=seconds;self.assertEqual(n.validate_admission(value)['seconds'],seconds)

    def test_output_root_is_absolute_D_and_aliases_or_ads_do_not_pass(self):
        for bad in('C:\\Synthetic\\lease','E:\\Synthetic\\lease','relative','D:relative',
                   'D:\\Synthetic\\..\\lease','D:\\Synthetic\\lease:stream','D:\\Synthetic\\lease.',
                   'D:\\Synthetic\\lease ','D:\\Synthetic\\NUL'):
            value=admission();value['root']=bad
            with self.subTest(root=bad):self.refused(lambda:n.validate_admission(value))

    def test_tool_roster_is_complete_unique_sorted_and_one_directory(self):
        transforms=(lambda a:a['tools'].pop(),lambda a:a['tools'].reverse(),
          lambda a:a['tools'].__setitem__(0,copy.deepcopy(a['tools'][1])),
          lambda a:a['tools'][0].update(path='C:\\Foreign\\AdbWinApi.dll'))
        for index,change in enumerate(transforms):
            value=admission();change(value)
            with self.subTest(index=index):self.refused(lambda:n.validate_admission(value))
        value=admission();value['adb']['sha256']='0'*64
        self.refused(lambda:n.validate_admission(value))

    def test_binding_shapes_hashes_sizes_and_private_data_roots_are_strict(self):
        for field in('adb','capabilities','source_review'):
            for key,bad in(('bytes',True),('bytes',-1),('sha256','A'*64),('sha256',True),
                           ('path','relative.json'),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
                value=admission();value[field][key]=bad
                with self.subTest(field=field,key=key):self.refused(lambda:n.validate_admission(value))
        for field in('capabilities','source_review'):
            value=admission();value[field]['path']='C:\\Synthetic\\project-result.json'
            with self.subTest(field=field):self.refused(lambda:n.validate_admission(value))

    def test_source_roster_and_python_binding_closed_fields(self):
        for change in(lambda a:a['sources'].pop(),lambda a:a['sources'].reverse(),
                      lambda a:a['sources'][0].update(path='D:\\Foreign\\benchmarks\\adb_held_socket.py')):
            value=admission();change(value);self.refused(lambda:n.validate_admission(value))
        value=admission();value['python']['private_rows']='SYNTHETIC_PRIVATE_CANARY'
        self.refused(lambda:n.validate_admission(value))

    def test_foreground_command_has_no_daemon_recovery_or_target_route(self):
        value=admission();command=n.server_command(value)
        self.assertEqual(command,[value['adb']['path'],'-L','tcp:127.0.0.1:15937','server','nodaemon'])
        self.assertNotIn('--one-device',command);self.assertEqual(value,admission())

    def test_process_local_environment_purges_case_insensitive_inherited_aliases(self):
        value=admission();inherited=dict(PATH='synthetic PATH',SystemRoot='C:\\Windows',HOME='C:\\Users\\Synthetic',
          USERPROFILE='C:\\Users\\Synthetic',ADB_VENDOR_KEYS='SYNTHETIC_PRIVATE_CANARY',adb_usb='1',AdB_TRACE='all',
          ANDROID_SERIAL='foreign',android_user_home='D:\\Foreign',AdBHOST='remote',adbport='5037',
          ADBSERVERPORT='5037',ANDROIDADBPORT='5037',Temp='C:\\Synthetic\\temp',tmp='C:\\Synthetic\\tmp')
        original=copy.deepcopy(inherited);result=n.child_environment(value,inherited)
        self.assertEqual(inherited,original)
        expected=dict(ADB_USB='0',ADB_EMU='0',ADB_MDNS='0',ADB_MDNS_AUTO_CONNECT='0',ADB_LOCAL_TRANSPORT_MAX_PORT='0',
          ANDROID_ADB_LOG_PATH=str(PureWindowsPath(value['root'])/'adb.log'),TEMP='D:\\Dev\\_Temp',TMP='D:\\Dev\\_Temp',TMPDIR='D:\\Dev\\_Temp')
        for key,text in expected.items():self.assertEqual(result[key],text)
        allowed=set(expected)
        self.assertTrue(all(not k.upper().startswith(('ADB_','ANDROID_'))or k in allowed for k in result))
        self.assertFalse(any(k.upper()in{'ADBHOST','ADBPORT','ADBSERVERPORT','ANDROIDADBPORT'}for k in result))
        self.assertFalse(any(k.upper()in{'TEMP','TMP','TMPDIR'}and k not in expected for k in result))
        for key in('PATH','SystemRoot','HOME','USERPROFILE'):self.assertEqual(result[key],inherited[key])
        self.assertNotIn('SYNTHETIC_PRIVATE_CANARY',result.values())

    def test_environment_rejects_non_string_or_nul_values_without_mutation(self):
        for inherited in({'PATH':True},{True:'x'},{'PATH':'x\0y'},['PATH=x']):
            before=copy.deepcopy(inherited)
            with self.subTest(inherited=inherited):self.refused(lambda:n.child_environment(admission(),inherited))
            self.assertEqual(inherited,before)

    def test_running_exact_process_source_deadline_and_binding_joins(self):
        admitted=admission();value=running(admitted);expected=copy.deepcopy(value)
        result=n.validate_running(value,admitted,admitted_binding());self.assertEqual(result,expected)
        result['server']['pid']+=1;self.assertEqual(value,expected)
        for path,bad in((('server','pid'),CLIENT['pid']),(('worker','pid'),OWNER['pid']),
                         (('owner','executable'),SERVER['executable']),(('server','executable'),PYTHON),
                         (('admission','sha256'),'0'*64)):
            changed=running(admitted);changed[path[0]][path[1]]=bad
            with self.subTest(path=path):self.refused(lambda:n.validate_running(changed,admitted,admitted_binding()))

    def test_running_saved_descriptor_does_not_claim_current_liveness(self):
        value=running();value['started_epoch']=1.0;value['deadline_epoch']=121.0
        self.assertEqual(n.validate_running(value,admission(),admitted_binding()),value)

    def test_running_bounds_closed_keys_and_finite_epoch_numbers(self):
        for field,bad in(('version',True),('port',5037),('run_id','f'*32),('started_epoch',True),
                         ('started_epoch',math.nan),('started_epoch',math.inf),('deadline_epoch',math.inf),
                         ('deadline_epoch',1800000000.25+121),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            value=running();value[field]=bad
            with self.subTest(field=field):self.refused(lambda:n.validate_running(value,admission(),admitted_binding()))
        value=running();value['sources'][0]['sha256']='0'*64
        self.refused(lambda:n.validate_running(value,admission(),admitted_binding()))

    def test_stop_is_exact_admission_bound_and_cannot_address_arbitrary_pid(self):
        digest='a'*64;value=dict(version=1,protocol=PROTOCOL,admission_sha256=digest,action='stop')
        self.assertIsNone(n.check_stop(value,digest))
        for change in(dict(version=True),dict(protocol='SDK3'),dict(action='kill-server'),
                      dict(admission_sha256='b'*64),dict(pid=SERVER['pid'])):
            with self.subTest(change=change):self.refused(lambda:n.check_stop(dict(value,**change),digest))

    def test_windows_reserved_alias_extensions_and_unc_roots_refuse(self):
        for bad in('D:\\Synthetic\\con.txt','D:\\Synthetic\\lPt1.log',
                   '\\\\host\\share\\lease','\\\\?\\D:\\Synthetic\\lease'):
            value=admission();value['root']=bad
            with self.subTest(root=bad):self.refused(lambda:n.validate_admission(value))
        value=admission();value['root']="D:\\Synthetic\\Éowyn's notes\\lease-v1"
        self.assertEqual(n.validate_admission(value),value)

    def test_running_proof_binding_paths_cannot_swap_or_escape_private_root(self):
        for field,bad in(('version_proof',running()['devices_proof']),
                         ('devices_proof',pin('C:\\Synthetic\\proof-devices-v1.json'))):
            value=running();value[field]=bad
            with self.subTest(field=field):self.refused(lambda:n.validate_running(value,admission(),admitted_binding()))

    def test_environment_does_not_export_changes_to_this_process(self):
        before=dict(os.environ);n.child_environment(admission(),dict(before,ADB_VENDOR_KEYS='synthetic vendor path'))
        self.assertEqual(dict(os.environ),before)


class ObservationTests(unittest.TestCase):
    def check(self,value,*,client=None,ep=None,**kwargs):
        return n.validate_observation(value,SERVER,client,ep,**kwargs)

    def refused(self,call):
        with self.assertRaises(n.LeaseRefused)as error:call()
        self.assertNotIn('SYNTHETIC_PRIVATE_CANARY',str(error.exception))

    def test_empty_preflight_requires_both_families_and_no_actual_process(self):
        self.assertIsNone(n.validate_observation(observation(),None,None,None,require_empty=True))
        self.refused(lambda:n.validate_observation(observation(row4()),None,None,None,require_empty=True))

    def test_ready_listener_states_are_opaque_and_never_promoted(self):
        for state in(0,1,2,5,4294967295):
            value=observation(row4(state=state));before=copy.deepcopy(value)
            with self.subTest(state=state):self.assertIsNone(self.check(value))
            self.assertEqual(value,before)

    def test_reciprocal_owned_tuple_states_do_not_select_roles(self):
        for state in(0,1,2,5,4294967295):
            with self.subTest(state=state):
                self.assertIsNone(self.check(connected(server_state=state,client_state=state),client=CLIENT,ep=endpoint()))

    def test_after_request_is_explicit_and_retains_teardown_or_absence(self):
        for rows in((row4(),),(row4(),row4(role='server',pid=0,ordinal=4)),
                     (row4(),row4(role='client',pid=0,ordinal=8)),
                     (row4(),row4(role='server',pid=0,ordinal=4),row4(role='client',pid=0,ordinal=8))):
            with self.subTest(rows=len(rows)):
                self.assertIsNone(self.check(observation(*rows),client=CLIENT,ep=endpoint(),after_request=True))

    def test_current_pid_zero_cannot_be_used_as_pre_send_ownership(self):
        for role,index in(('server',1),('client',2)):
            value=connected();value['rows'][index]=row4(role=role,pid=0,ordinal=4 if role=='server'else 8)
            with self.subTest(role=role):self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint()))

    def test_after_request_does_not_allow_missing_zero_or_foreign_listener(self):
        for listener in(None,row4(pid=0),row4(pid=SERVER['pid']+1)):
            rows=[]if listener is None else[listener]
            with self.subTest(listener=listener is None):
                self.refused(lambda:self.check(observation(*rows),client=CLIENT,ep=endpoint(),after_request=True))

    def test_foreign_pid_is_not_hidden_by_state_or_after_request(self):
        for after in(False,True):
            value=connected();value['rows'][1]=row4(role='server',state=0,pid=SERVER['pid']+1,ordinal=4)
            with self.subTest(after=after):self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint(),after_request=after))

    def test_missing_duplicate_and_swapped_reciprocal_rows_refuse(self):
        for action in('missing','duplicate','swapped'):
            value=connected()
            if action=='missing':value['rows'].pop()
            elif action=='duplicate':value['rows'][2]=row4(role='server',ordinal=8)
            else:value['rows'][1]=row4(role='server',rp=CLIENT_PORT+1,ordinal=4)
            with self.subTest(action=action):self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint()))

    def test_wildcards_other_loopback_and_ipv6_private_owners_refuse(self):
        for row in(row4(local='0.0.0.0'),row4(local='127.0.0.2'),row6(),
                   row6(local_scope=42,remote_scope=4294967295),row6(pid=0)):
            with self.subTest(family=row['family']):self.refused(lambda:self.check(observation(row)))

    def test_v1_candidate_predicate_uses_zero_remote_fields_not_state(self):
        for state in(0,2,5):
            value=observation(row4(state=state,remote='127.0.0.1',rp=9999))
            with self.subTest(state=state):self.refused(lambda:self.check(value))

    def test_unrelated_ports_or_nonreciprocal_client_local_rows_are_private_noise(self):
        value=connected();value['rows'].append(row4(role='client',lp=49999,ordinal=10))
        self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint()))
        value=connected();value['rows'][2]=row4(role='client',remote='192.0.2.44',ordinal=8)
        self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint()))

    def test_row_fields_must_exactly_match_original_raw_bytes_and_types(self):
        for key,bad in(('state',False),('local_scope_id',False),('local_port',15937.0),
                       ('local_address','127.000.0.1'),('pid',SERVER['pid']+1),
                       ('raw_hex','00'),('raw_hex',row4()['raw_hex'].upper()),
                       ('raw_hex','zz'*24),('raw_hex',True),('ordinal',True),('ordinal',-1),
                       ('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            value=observation(row4());value['rows'][0][key]=bad
            with self.subTest(key=key,bad_type=type(bad).__name__):self.refused(lambda:self.check(value))

    def test_row_order_is_not_a_state_or_ownership_selection_rule(self):
        value=connected();value['rows'].reverse()
        self.assertIsNone(self.check(value,client=CLIENT,ep=endpoint()))
        value=connected();value['rows'][0]['ordinal']=value['rows'][1]['ordinal']
        self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint()))

    def test_observation_closed_shape_family_roster_and_row_cap(self):
        for change in(dict(version=True),dict(port=5037),dict(families=[2]),dict(families=[23,2]),
                      dict(families=[2,2]),dict(rows=()),dict(private_rows='SYNTHETIC_PRIVATE_CANARY')):
            with self.subTest(change=change):self.refused(lambda:self.check(dict(observation(row4()),**change)))
        self.refused(lambda:self.check(observation(*[row4(ordinal=i)for i in range(65)])))

    def test_endpoint_and_client_identity_are_complete_exact_and_pinned(self):
        for key,bad in(('local_address','0.0.0.0'),('peer_address','127.0.0.2'),('peer_port',5037),
                       ('local_port',5037),('local_port',PORT),('local_port',True),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            ep=endpoint();ep[key]=bad
            with self.subTest(key=key):self.refused(lambda:self.check(connected(),client=CLIENT,ep=ep))
        client=dict(CLIENT,creation_filetime=True)
        self.refused(lambda:self.check(connected(),client=client,ep=endpoint()))
        self.refused(lambda:self.check(connected(),client=None,ep=endpoint()))

    def test_mode_flags_are_exact_and_final_mode_cannot_replace_preflight(self):
        for kwargs in(dict(after_request=1),dict(require_empty=1),dict(after_request=True),
                      dict(require_empty=True,after_request=True)):
            with self.subTest(kwargs=kwargs):self.refused(lambda:self.check(observation(row4()),**kwargs))

    def test_history_allows_only_previously_completed_server_local_teardowns(self):
        for pid in(0,SERVER['pid']):
            history=row4(role='server',pid=pid,rp=OLD_PORT,ordinal=10)
            value=connected();value['rows'].append(history)
            with self.subTest(pid=pid):
                self.assertIsNone(self.check(value,client=CLIENT,ep=endpoint(),completed_ports=(OLD_PORT,)))
                self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint()))
        ready=observation(row4(),row4(role='server',pid=0,rp=OLD_PORT,ordinal=10))
        self.assertIsNone(self.check(ready,completed_ports=(OLD_PORT,)))

    def test_history_never_admits_current_pid_zero_or_foreign_process(self):
        value=connected();value['rows'][1]=row4(role='server',pid=0,ordinal=4)
        self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint(),completed_ports=(CLIENT_PORT,)))
        value=connected();value['rows'].append(row4(role='server',pid=SERVER['pid']+1,rp=OLD_PORT,ordinal=10))
        self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint(),completed_ports=(OLD_PORT,)))

    def test_history_is_bounded_unique_and_cannot_hide_unrelated_client_local_rows(self):
        for ports in((True,),(0,),(5037,),(PORT,),(65536,),(OLD_PORT,OLD_PORT),(OLD_PORT,OLDER_PORT,49999)):
            with self.subTest(ports=ports):self.refused(lambda:self.check(observation(row4()),completed_ports=ports))
        value=connected();value['rows'].append(row4(role='client',pid=0,lp=OLD_PORT,ordinal=10))
        self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint(),completed_ports=(OLD_PORT,)))

    def test_history_does_not_relax_unique_listener_or_tuple_ambiguity(self):
        value=connected();value['rows'].append(row4(pid=0,ordinal=10))
        self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint(),after_request=True,completed_ports=(OLD_PORT,)))
        value=connected();value['rows'].extend((row4(role='server',pid=0,rp=OLD_PORT,ordinal=10),
                                               row4(role='server',pid=0,rp=OLD_PORT,ordinal=11)))
        self.refused(lambda:self.check(value,client=CLIENT,ep=endpoint(),completed_ports=(OLD_PORT,)))

    def test_exact_ordinal_cap_and_family_numeric_types(self):
        self.assertIsNone(self.check(observation(row4(ordinal=16383))))
        self.refused(lambda:self.check(observation(row4(ordinal=16384))))
        for families in([2.0,23],[2,23.0]):
            with self.subTest(families=families):self.refused(lambda:self.check(dict(observation(row4()),families=families)))

    def test_empty_preflight_and_history_container_cannot_borrow_later_authority(self):
        for kwargs in(dict(completed_ports=(OLD_PORT,)),dict(after_request=True)):
            with self.subTest(kwargs=kwargs):
                self.refused(lambda:n.validate_observation(observation(),None,None,None,require_empty=True,**kwargs))
        for ports in([OLD_PORT],None,{'port':OLD_PORT},str(OLD_PORT)):
            with self.subTest(type=type(ports).__name__):self.refused(lambda:self.check(observation(row4()),completed_ports=ports))

    def test_two_verified_history_ports_are_distinct_from_current_connection(self):
        value=connected();value['rows'].extend((row4(role='server',pid=0,rp=OLD_PORT,ordinal=10),
                                               row4(role='server',pid=SERVER['pid'],rp=OLDER_PORT,ordinal=11)))
        self.assertIsNone(self.check(value,client=CLIENT,ep=endpoint(),completed_ports=(OLD_PORT,OLDER_PORT)))


@unittest.skipUnless(os.name=='nt','physical D: capability files require Windows')
class CapabilityReadbackTests(unittest.TestCase):
    def setUp(self):
        from benchmarks import receipt_avd_environment as env
        self.env=env;self.base=Path(tempfile.mkdtemp(prefix='locallore-isolated-capability-',dir='D:/Dev/_Temp'))
        self.value=admission();self.value['root']=str(self.base/'lease-v1')
        version=b'Android Debug Bridge version 1.0.41\nVersion 37.0.1-15733141\nInstalled as synthetic path\n'
        help_text=b'Original synthetic offline help\n-L SOCKET\nserver nodaemon\nADB_LOCAL_TRANSPORT_MAX_PORT\nADB_MDNS_AUTO_CONNECT\n'
        self.rows=[]
        for index,command,raw in((1,'version',version),(2,'help',help_text)):
            path=self.base/('command-%02d.stdout.bin'%index);path.write_bytes(raw)
            self.rows.append(dict(index=index,argv=[self.value['adb']['path'],command],
              owner=dict(status='completed',elapsed_ms=7,returncode=0,cleanup_complete=True,stderr_bytes=0),
              stdout=env.binding(path)))
        self.cap=dict(version=1,passed=True,offline_CLI_calls=2,server_requests=0,device_calls=0,sources_equal=True,rows=self.rows)
        self.path=self.base/'capabilities-v1.json';self.save()
        review=self.base/'source-review-v1.md';review.write_bytes(b'Original synthetic source-review text; no authority.\n')
        self.value['source_review']=env.binding(review)

    def save(self,raw=None):
        self.path.write_bytes(self.env.encoded(self.cap)if raw is None else raw)
        self.value['capabilities']=self.env.binding(self.path)

    def refused(self,call):
        # Explicit filesystem helpers may retain the existing fixed IO refusal
        # types. None of these paths may turn an IO failure into qualification.
        with self.assertRaises((n.LeaseRefused,self.env.EnvironmentRefused,OSError))as error:call()
        self.assertNotIn('SYNTHETIC_PRIVATE_CANARY',str(error.exception))

    def read(self):return n.validate_capabilities(self.value['capabilities'],self.value)

    def test_original_offline_capability_bytes_are_read_not_executed(self):
        with patch('subprocess.Popen',side_effect=AssertionError('no SDK execution')):
            result=self.read()
        self.assertEqual(result,self.cap);result['rows'][0]['owner']['elapsed_ms']=999
        self.assertEqual(self.env.read_json(self.path),self.cap)

    def test_capability_closed_keys_owner_and_no_device_or_server_claims(self):
        changes=(lambda x:x.update(server_requests=1),lambda x:x.update(device_calls=1),
          lambda x:x.update(passed=1),lambda x:x.update(offline_CLI_calls=True),
          lambda x:x.update(private_rows='SYNTHETIC_PRIVATE_CANARY'),
          lambda x:x['rows'][0]['owner'].update(returncode=True),
          lambda x:x['rows'][1]['owner'].update(cleanup_complete=False),
          lambda x:x['rows'][0].update(argv=[self.value['adb']['path'],'devices','-l']))
        original=copy.deepcopy(self.cap)
        for index,change in enumerate(changes):
            self.cap=copy.deepcopy(original);change(self.cap);self.save()
            with self.subTest(index=index):self.refused(self.read)

    def test_capability_stdout_hash_and_exact_private_filenames_are_bound(self):
        raw_path=Path(self.rows[0]['stdout']['path']);raw_path.write_bytes(b'changed synthetic output')
        self.refused(self.read)
        # A new original adversarial record cannot substitute a differently named file.
        other=self.base/'foreign-output.bin';other.write_bytes(b'original synthetic bytes')
        self.cap['rows'][0]['stdout']=self.env.binding(other);self.save();self.refused(self.read)

    def test_capability_version_and_help_tokens_are_required(self):
        original=copy.deepcopy(self.cap)
        original_bytes=[Path(row['stdout']['path']).read_bytes()for row in original['rows']]
        for index,raw in((0,b'Android Debug Bridge version 1.0.41\nVersion 37.0.0\n'),(1,b'original help missing startup controls')):
            self.cap=copy.deepcopy(original)
            for row,data in zip(self.cap['rows'],original_bytes):Path(row['stdout']['path']).write_bytes(data)
            path=Path(self.cap['rows'][index]['stdout']['path']);path.write_bytes(raw)
            self.cap['rows'][index]['stdout']=self.env.binding(path);self.save()
            with self.subTest(index=index):self.refused(self.read)

    def test_strict_capability_json_and_record_hash_refuse(self):
        original=self.env.encoded(self.cap)
        for raw in(b'{"version":1,"version":1}',b'{"x":NaN}',b'\xff'):
            self.save(raw)
            with self.subTest(raw_type=raw[:1]):self.refused(self.read)
        self.save(original);self.path.write_bytes(original+b' ')
        self.refused(self.read)

    def revalidate(self,*,markers=True,source_changed=False):
        from benchmarks import adb_held_socket_probe as probe
        checked=[];read_pins=[];original=n._read_bound
        def check(pin_value):checked.append(copy.deepcopy(pin_value))
        def read_bound(pin_value,**kwargs):
            read_pins.append(copy.deepcopy(pin_value))
            if pin_value['path']==self.value['adb']['path']:
                return b'original synthetic executable ADB_USB\0ADB_EMU\0ADB_MDNS\0'if markers else b'no startup markers'
            return original(pin_value,**kwargs)
        sources=copy.deepcopy(self.value['sources'])
        if source_changed:sources[0]['sha256']='0'*64
        with patch.object(n,'source_bindings',return_value=sources), \
             patch.object(probe,'_python_bindings',return_value=self.value['python']), \
             patch.object(self.env,'check_binding',side_effect=check),patch.object(n,'_read_bound',side_effect=read_bound):
            result=n.revalidate_inputs(self.value)
        return result,checked,read_pins

    def test_revalidation_checks_bound_sources_tools_and_markers_without_key_read(self):
        result,checked,read_pins=self.revalidate()
        self.assertIsNone(result)
        expected=self.value['sources']+self.value['tools']+[self.value['source_review']]
        self.assertTrue(all(pin_value in checked for pin_value in expected))
        self.assertTrue(any(p['path']==self.value['adb']['path']for p in read_pins))
        self.assertNotIn(self.value['auth_key'],[p['path']for p in read_pins+checked])

    def test_revalidation_refuses_missing_startup_markers_or_changed_source(self):
        self.refused(lambda:self.revalidate(markers=False))
        self.refused(lambda:self.revalidate(source_changed=True))


@unittest.skipUnless(os.name=='nt','physical D: mocked owner fixtures require Windows')
class OwnerResourceTests(unittest.TestCase):
    def setUp(self):
        from benchmarks import isolated_adb_owner as owner
        from benchmarks import receipt_avd_environment as env
        self.o=owner;self.env=env
        self.base=Path(tempfile.mkdtemp(prefix='locallore-isolated-owner-',dir='D:/Dev/_Temp'))

    def test_runtime_constructor_has_no_native_credential_socket_or_process_io(self):
        with patch.object(self.o.native,'_WindowsApi')as native,patch.object(self.o.AuthKeyGuard,'open')as auth, \
             patch.object(self.o.socket,'socket')as sock,patch.object(self.o.subprocess,'Popen')as process:
            runtime=self.o.WorkerRuntime(dict(validated_admission=admission(),admission=admitted_binding()),admitted_binding(),self.base)
        self.assertIsNone(runtime.api);self.assertIsNone(runtime.child)
        for mocked in(native,auth,sock,process):mocked.assert_not_called()

    def test_failed_process_handle_release_is_never_blindly_retried(self):
        api=SimpleNamespace(open_process=Mock(return_value=901),identity=Mock(return_value=CLIENT),
                            alive=Mock(return_value=True),close_handle=Mock(return_value=False))
        handles=self.o.ProcessHandles(api);handle,_=handles.add(CLIENT['pid'],CLIENT)
        self.assertFalse(handles.release(handle));self.assertFalse(handles.close())
        self.assertEqual(api.close_handle.call_count,1,'uncertain numeric process handle must not be retried')

    def test_failed_auth_handle_close_is_not_retried_and_other_handles_are_attempted(self):
        calls=[]
        def close(handle):calls.append(handle);return 0 if handle==901 else 1
        auth=self.o.AuthKeyGuard();auth.kernel=SimpleNamespace(CloseHandle=close);auth.handles={901,902}
        self.assertFalse(auth._close(901));self.assertFalse(auth.close())
        self.assertEqual(calls.count(901),1,'uncertain key handle must never be blindly retried')
        self.assertIn(902,calls)

    def test_metadata_key_open_denies_write_delete_and_never_reads_contents(self):
        auth=self.o.AuthKeyGuard();create=Mock(return_value=901)
        auth.kernel=SimpleNamespace(CreateFileW=create)
        self.assertEqual(auth._open_read(PureWindowsPath(admission()['auth_key'])),901)
        args=create.call_args.args;self.assertEqual(args[1:4],(0x80000000,1,None))
        self.assertEqual(args[4],3);self.assertIn(901,auth.handles)

    def test_partial_identity_acquisition_keeps_handle_for_final_cleanup(self):
        api=SimpleNamespace(open_process=Mock(return_value=901),identity=Mock(side_effect=self.o.OwnerRefused('identity')),
                            close_handle=Mock(return_value=True))
        handles=self.o.ProcessHandles(api)
        with self.assertRaises(self.o.OwnerRefused):handles.add(CLIENT['pid'],CLIENT)
        self.assertTrue(handles.close());api.close_handle.assert_called_once_with(901)

    def fake_capture(self):
        class Flag:
            def __init__(self):self.value=False
            def set(self):self.value=True
            def is_set(self):return self.value
        return SimpleNamespace(failed=Flag(),overflow=Flag(),close=Mock(),append=Mock(return_value=True))

    def test_reader_start_failure_closes_owned_pipes_and_capture_without_joining_unstarted(self):
        capture=self.fake_capture();thread=SimpleNamespace(start=Mock(side_effect=RuntimeError('synthetic start failure')),
          join=Mock(side_effect=RuntimeError('unstarted join')),is_alive=Mock(return_value=False))
        child=SimpleNamespace(stdout=SimpleNamespace(close=Mock()),stderr=SimpleNamespace(close=Mock()))
        with patch.object(self.o.env,'LiveOutput',return_value=capture),patch.object(self.o.threading,'Thread',return_value=thread):
            output=self.o.ServerCapture(self.base/'output')
            with self.assertRaises(RuntimeError):output.start(child)
            self.assertFalse(output.close())
        thread.join.assert_not_called();child.stdout.close.assert_called_once();child.stderr.close.assert_called_once()
        capture.close.assert_called_once();self.assertTrue(capture.failed.is_set())

    def test_capture_pipe_failure_attempts_remaining_owned_closes(self):
        capture=self.fake_capture();pipes=[SimpleNamespace(close=Mock(side_effect=OSError('synthetic close'))),SimpleNamespace(close=Mock())]
        with patch.object(self.o.env,'LiveOutput',return_value=capture):output=self.o.ServerCapture(self.base/'output')
        output.pipes=pipes;self.assertFalse(output.close())
        for pipe in pipes:pipe.close.assert_called_once()
        capture.close.assert_called_once();self.assertFalse(output.pipes_closed)

    def test_cleanup_preserves_actual_nonzero_server_returncode_and_handle_failure(self):
        handle=SimpleNamespace(closed=False,Close=Mock(side_effect=OSError('synthetic native close')))
        child=SimpleNamespace(poll=Mock(return_value=None),terminate=Mock(),wait=Mock(return_value=7),_handle=handle)
        capture=SimpleNamespace(close=Mock(return_value=True),pipes_closed=True)
        runtime=SimpleNamespace(child=child,capture=capture,clients_closed=True)
        flags,code=self.o._cleanup(runtime)
        self.assertEqual(code,7);self.assertTrue(flags['server_terminate_attempted']);self.assertTrue(flags['server_wait_completed'])
        self.assertFalse(flags['server_process_handle_closed']);self.assertTrue(flags['server_pipes_closed'])
        child.terminate.assert_called_once();child.wait.assert_called_once();capture.close.assert_called_once()

    def test_missing_or_mismatched_started_receipt_never_reaches_auth_port_or_server(self):
        for missing in(False,True):
            root=self.base/('missing'if missing else'mismatch');root.mkdir()
            request=dict(validated_admission=admission(),admission=admitted_binding(),owner=OWNER)
            runtime=self.o.WorkerRuntime(request,admitted_binding(),root);runtime.worker=CLIENT
            runtime.processes=SimpleNamespace(guard=Mock())
            if not missing:self.env.create_json(root/'started-v1.json',dict(worker=dict(CLIENT,creation_filetime=1),request=admitted_binding()))
            ticks=iter((100.0,101.0,106.0))
            with patch.object(self.o.time,'monotonic',side_effect=lambda:next(ticks)),patch.object(self.o.time,'sleep'), \
                 patch.object(self.o.AuthKeyGuard,'open')as auth,patch.object(self.o,'_exclusive_preflight')as port, \
                 patch.object(self.o.subprocess,'Popen')as process:
                with self.assertRaises(self.o.OwnerRefused):runtime.wait_receipt()
            auth.assert_not_called();port.assert_not_called();process.assert_not_called()


if __name__=='__main__':unittest.main()
