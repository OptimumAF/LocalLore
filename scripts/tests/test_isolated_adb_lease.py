"""Original isolated-lease metadata and raw-row adversaries. Never start ADB.

Pins below describe synthetic values, not an authenticated build or live lease.
No profile key, service, device, emulator, model or private capture is opened.
"""
import copy
import hashlib
import ipaddress
import math
from pathlib import Path,PureWindowsPath
import struct
import unittest
from unittest.mock import patch

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
      source_review=pin('D:\\Synthetic\\packet\\source-review-v1.json'))


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


if __name__=='__main__':unittest.main()
