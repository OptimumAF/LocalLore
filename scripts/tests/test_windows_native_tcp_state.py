"""Original complete native-control fixtures; no native executable or OS query.

Only raw DWORD bytes are synthesized. Unknown states remain observations and
cannot grant service, SDK or device admission. No private capture is reused.
"""
import copy
import hashlib
import ipaddress
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from contextlib import ExitStack,redirect_stdout
from unittest.mock import patch

from benchmarks import windows_native_tcp_state as n


PROTOCOL='windows-native-owned-tcp-state-v1'
PAYLOAD=b'LL_NTCP_CONTROL1!'
PID=7321
LISTENER_PORT=41001
CLIENT_PORT=41002
PROCESS=dict(pid=PID,creation_filetime=132456789012345678,executable='D:\\Synthetic\\tcp-control.exe')
QUERY_NAMES=('owner_listener','owner_all','basic','owner2')
STAGE_NAMES=('after_listen','connected','exchanged')
STRIDES=dict(owner_listener=24,owner_all=24,basic=20,owner2=28)
SUMMARY_KEYS={'version','protocol','feature_acceptance','acquisition_completed','observation_consistent',
              'listener_states','connection_states','selected_rows','resources_closed'}


def raw_row(query,*,role='listener',state=2,pid=PID,local='127.0.0.1',remote=None,
            local_port=None,remote_port=None,offload=0xfedcba98,high_port_bits=0):
    if role=='listener':lp,rp,ra=LISTENER_PORT,0,'0.0.0.0'
    elif role=='server':lp,rp,ra=LISTENER_PORT,CLIENT_PORT,'127.0.0.1'
    elif role=='client':lp,rp,ra=CLIENT_PORT,LISTENER_PORT,'127.0.0.1'
    else:raise ValueError('synthetic role')
    address=lambda text:int.from_bytes(ipaddress.IPv4Address(text).packed,'little')
    port=lambda value:high_port_bits|int.from_bytes(value.to_bytes(2,'big'),'little')
    values=[state,address(local),port(lp if local_port is None else local_port),
            address(ra if remote is None else remote),port(rp if remote_port is None else remote_port)]
    if query!='basic':values.append(pid)
    if query=='owner2':values.append(offload)
    return struct.pack('<'+'I'*len(values),*values).hex()


def report(*,listener=2,server=5,client=5,listener_remote=None,high_port_bits=0):
    value=dict(version=1,protocol=PROTOCOL,pid=PID,creation_filetime=PROCESS['creation_filetime'],
      abi=dict(owner_pid=dict(row_bytes=24,row_offset=4,field_offsets=[0,4,8,12,16,20]),
               basic=dict(row_bytes=20,row_offset=4,field_offsets=[0,4,8,12,16]),
               owner2=dict(row_bytes=28,row_offset=4,field_offsets=[0,4,8,12,16,20,24])),
      listener_port=LISTENER_PORT,client_port=CLIENT_PORT,stages=[],
      exchange=dict(client_sent=17,server_received=17,server_sent=17,client_received=17,
                    server_hex=PAYLOAD.hex(),client_hex=PAYLOAD.hex()),
      resources=dict(created_mask=7,close_attempted_mask=7,closed_mask=7,winsock_started=True,
                     winsock_cleanup_attempted=True,winsock_cleanup_succeeded=True),
      acquisition_completed=True,reason=None,elapsed_ms=27)
    for phase in STAGE_NAMES:
        stage=dict(stage=phase,acceptconn=1,queries=[])
        for name in QUERY_NAMES:
            rows=[dict(ordinal=1,raw_hex=raw_row(name,state=listener,remote=listener_remote,
                                               high_port_bits=high_port_bits))]
            if phase!='after_listen'and name!='owner_listener':
                rows.extend((dict(ordinal=4,raw_hex=raw_row(name,role='server',state=server,high_port_bits=high_port_bits)),
                             dict(ordinal=8,raw_hex=raw_row(name,role='client',state=client,high_port_bits=high_port_bits))))
            stage['queries'].append(dict(name=name,initial_code=122,final_code=0,
              allocated_bytes=4+12*STRIDES[name]+64,returned_bytes=4+12*STRIDES[name],count=12,rows=rows))
        value['stages'].append(stage)
    return value


def encoded(value):return(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def query(value,stage=1,name='owner_all'):
    return next(q for q in value['stages'][stage]['queries']if q['name']==name)


class NativeAssessorTests(unittest.TestCase):
    def assess(self,value,expected=None):return n.assess_report(encoded(value),copy.deepcopy(PROCESS if expected is None else expected))

    def refused(self,call):
        with self.assertRaises(n.NativeControlRefused)as error:call()
        self.assertNotIn('SYNTHETIC_PRIVATE_CANARY',str(error.exception))

    def test_complete_original_three_by_four_report_has_exact_summary(self):
        result=self.assess(report())
        self.assertEqual(set(result),SUMMARY_KEYS);self.assertEqual(result['version'],1)
        self.assertEqual(result['protocol'],PROTOCOL);self.assertIs(result['feature_acceptance'],False)
        self.assertIs(result['acquisition_completed'],True);self.assertIs(result['observation_consistent'],True)
        self.assertIs(result['resources_closed'],True);self.assertIs(type(result['selected_rows']),int)
        self.assertEqual(result['selected_rows'],24);self.assertEqual(result['listener_states'],[2]*12)
        expected=[dict(stage=stage,query=q,server=5,client=5)for stage in STAGE_NAMES[1:]for q in QUERY_NAMES[1:]]
        self.assertEqual(result['connection_states'],expected)

    def test_unknown_and_future_states_are_acquired_preserved_and_inconsistent(self):
        for state in(0,1,2,5,4294967295):
            with self.subTest(state=state):
                result=self.assess(report(listener=state,server=state,client=state))
                self.assertIs(result['acquisition_completed'],True);self.assertIs(result['observation_consistent'],False)
                self.assertEqual(result['listener_states'],[state]*12)
                self.assertTrue(all(r['server']==r['client']==state for r in result['connection_states']))
                self.assertFalse(result['feature_acceptance'])

    def test_connection_roles_do_not_use_state_two_as_listener_selection(self):
        result=self.assess(report(listener=5,server=2,client=2))
        self.assertEqual(result['listener_states'],[5]*12)
        self.assertTrue(all(r['server']==r['client']==2 for r in result['connection_states']))
        self.assertFalse(result['observation_consistent'])

    def test_listener_remote_fields_are_undefined_and_not_an_ownership_gate(self):
        self.assertTrue(self.assess(report(listener_remote='198.51.100.77'))['observation_consistent'])

    def test_low_sixteen_port_bits_and_opaque_offload_are_preserved(self):
        self.assertTrue(self.assess(report(high_port_bits=0xa5a50000))['observation_consistent'])
        raw=bytes.fromhex(query(report(),name='owner2')['rows'][1]['raw_hex'])
        self.assertEqual(struct.unpack('<7I',raw)[-1],0xfedcba98)

    def test_expected_process_and_native_identity_are_exact(self):
        for field,bad in(('pid',True),('pid',0),('pid',PID+1),('creation_filetime',True),
                         ('creation_filetime',PROCESS['creation_filetime']+1),('executable',True),
                         ('executable','relative.exe'),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            expected=dict(PROCESS);expected[field]=bad
            with self.subTest(field=field):self.refused(lambda:self.assess(report(),expected))
        for field in('pid','creation_filetime'):
            value=report();value[field]+=1
            with self.subTest(native_field=field):self.refused(lambda:self.assess(value))

    def test_native_metadata_does_not_attest_executable_path(self):
        expected=dict(PROCESS,executable='D:\\Synthetic\\other-admitted-binary.exe')
        self.assertTrue(self.assess(report(),expected)['acquisition_completed'])

    def test_top_level_closed_keys_and_scalar_types(self):
        for field,bad in(('version',True),('version',2),('protocol','legacy-SDK2'),('pid',True),
                         ('creation_filetime',0),('elapsed_ms',True),('elapsed_ms',-1),
                         ('acquisition_completed',1),('acquisition_completed',False),
                         ('reason','api'),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            value=report();value[field]=bad
            with self.subTest(field=field,bad=bad):self.refused(lambda:self.assess(value))
        value=report();del value['elapsed_ms'];self.refused(lambda:self.assess(value))

    def test_all_abi_dimensions_offsets_and_closed_keys_are_checked(self):
        for kind in('owner_pid','basic','owner2'):
            for field,bad in(('row_bytes',True),('row_bytes',23),('row_offset',8),
                             ('field_offsets',[0,4]),('private_rows','SYNTHETIC_PRIVATE_CANARY')):
                value=report();value['abi'][kind][field]=bad
                with self.subTest(kind=kind,field=field):self.refused(lambda:self.assess(value))
        value=report();value['abi']['basic']['field_offsets'][1]=True
        self.refused(lambda:self.assess(value))

    def test_ports_are_positive_distinct_and_exclude_existing_adb_endpoint(self):
        for field,bad in(('listener_port',0),('client_port',0),('listener_port',5037),
                         ('client_port',5037),('client_port',LISTENER_PORT),
                         ('client_port',True),('listener_port',65536)):
            value=report();value[field]=bad
            with self.subTest(field=field,bad=bad):self.refused(lambda:self.assess(value))

    def test_stage_and_query_rosters_are_complete_fixed_order_and_unique(self):
        transforms=(lambda v:v['stages'].pop(),lambda v:v['stages'].reverse(),
          lambda v:v['stages'][1].update(stage='after_listen'),
          lambda v:v['stages'][1]['queries'].pop(),lambda v:v['stages'][1]['queries'].reverse(),
          lambda v:v['stages'][1]['queries'][1].update(name='owner_listener'))
        for index,change in enumerate(transforms):
            value=report();change(value)
            with self.subTest(index=index):self.refused(lambda:self.assess(value))

    def test_acceptconn_zero_is_inconsistent_and_exact_type_is_required(self):
        value=report();value['stages'][1]['acceptconn']=0
        self.assertFalse(self.assess(value)['observation_consistent'])
        for bad in(True,-1,2,'1'):
            value=report();value['stages'][1]['acceptconn']=bad
            with self.subTest(bad=bad):self.refused(lambda:self.assess(value))

    def test_api_initial_zero_with_nonzero_valid_allocation_is_allowed(self):
        value=report()
        for stage in value['stages']:
            for q in stage['queries']:q['initial_code']=0
        self.assertTrue(self.assess(value)['observation_consistent'])

    def test_api_codes_and_allocation_count_bounds(self):
        for field,bad in(('initial_code',True),('initial_code',5),('initial_code',-1),
                         ('final_code',1),('final_code',True),('allocated_bytes',0),
                         ('allocated_bytes',1048577),('returned_bytes',0),('returned_bytes',1048577),
                         ('count',True),('count',16385),('count',-1),('count',4294967296)):
            value=report();query(value)[field]=bad
            with self.subTest(field=field,bad=bad):self.refused(lambda:self.assess(value))
        value=report();q=query(value);q['returned_bytes']=q['allocated_bytes']+1
        self.refused(lambda:self.assess(value))
        value=report();q=query(value);q['returned_bytes']=4+q['count']*24-1
        self.refused(lambda:self.assess(value))

    def test_count_delimited_ordinals_are_strict_increasing_unique_and_bounded(self):
        for ordinals in((1,1,8),(4,1,8),(1,4,12),(True,4,8),(-1,4,8)):
            value=report()
            for row,ordinal in zip(query(value)['rows'],ordinals):row['ordinal']=ordinal
            with self.subTest(ordinals=ordinals):self.refused(lambda:self.assess(value))

    def test_raw_hex_is_lowercase_exact_stride_and_closed_row_schema(self):
        for bad in('', '00', 'zz'*24, raw_row('owner_all').upper(),'00'*25,True):
            value=report();query(value)['rows'][0]['raw_hex']=bad
            with self.subTest(bad_type=type(bad).__name__,size=len(bad)if type(bad)is str else None):
                self.refused(lambda:self.assess(value))
        value=report();query(value)['rows'][0]['private_rows']='SYNTHETIC_PRIVATE_CANARY'
        self.refused(lambda:self.assess(value))

    def test_owner_capable_rows_cannot_hide_foreign_pid_by_state_filtering(self):
        for name in('owner_listener','owner_all','owner2'):
            value=report();q=query(value,name=name);q['rows'][0]['raw_hex']=raw_row(name,pid=PID+1,state=0)
            with self.subTest(name=name):self.refused(lambda:self.assess(value))
        value=report();query(value)['rows'][1]['raw_hex']=raw_row('owner_all',role='server',state=0,pid=PID+1)
        self.refused(lambda:self.assess(value))

    def test_basic_has_no_observed_pid_and_cannot_substitute_for_owner_paths(self):
        value=report();q=query(value,name='owner_all');q['rows'][1]['raw_hex']=raw_row('basic',role='server',state=5)
        self.refused(lambda:self.assess(value))

    def test_missing_duplicate_and_swapped_reciprocal_tuples_refuse(self):
        for action in('missing','duplicate','swapped'):
            value=report();q=query(value)
            if action=='missing':q['rows'].pop()
            elif action=='duplicate':q['rows'][2]['raw_hex']=q['rows'][1]['raw_hex']
            else:q['rows'][1]['raw_hex']=raw_row('owner_all',role='server',state=5,remote_port=CLIENT_PORT+1)
            with self.subTest(action=action):self.refused(lambda:self.assess(value))

    def test_unowned_addresses_foreign_selected_ports_and_extra_rows_refuse(self):
        for kwargs in(dict(local='0.0.0.0'),dict(local='127.0.0.2'),dict(local_port=CLIENT_PORT+1)):
            value=report();query(value)['rows'][2]['raw_hex']=raw_row('owner_all',role='client',state=5,**kwargs)
            with self.subTest(kwargs=kwargs):self.refused(lambda:self.assess(value))
        value=report();query(value)['rows'].append(dict(ordinal=9,raw_hex=raw_row('owner_all',role='server',state=0,remote_port=CLIENT_PORT+1)))
        self.refused(lambda:self.assess(value))

    def test_selected_rows_cap_and_unique_listener_requirements(self):
        value=report();q=query(value);q['rows']=[dict(ordinal=i,raw_hex=raw_row('owner_all'))for i in range(9)]
        self.refused(lambda:self.assess(value))
        value=report();query(value,name='owner_listener')['rows']=[];self.refused(lambda:self.assess(value))
        value=report();q=query(value,name='owner_listener');q['rows'].append(dict(ordinal=2,raw_hex=q['rows'][0]['raw_hex']))
        self.refused(lambda:self.assess(value))

    def test_incomplete_wrong_and_nonprefix_exchange_never_qualifies(self):
        for field in('client_sent','server_received','server_sent','client_received'):
            for bad in(16,True,-1,18):
                value=report();value['exchange'][field]=bad
                with self.subTest(field=field,bad=bad):self.refused(lambda:self.assess(value))
        for field in('server_hex','client_hex'):
            for bad in(PAYLOAD[:-1].hex(),(b'X'+PAYLOAD[1:]).hex(),PAYLOAD.hex().upper(),True):
                value=report();value['exchange'][field]=bad
                with self.subTest(field=field):self.refused(lambda:self.assess(value))

    def test_explicit_cleanup_masks_and_winsock_flags_are_required(self):
        for field in('created_mask','close_attempted_mask','closed_mask'):
            for bad in(0,3,True,-1,8):
                value=report();value['resources'][field]=bad
                with self.subTest(field=field,bad=bad):self.refused(lambda:self.assess(value))
        for field in('winsock_started','winsock_cleanup_attempted','winsock_cleanup_succeeded'):
            for bad in(False,1,None):
                value=report();value['resources'][field]=bad
                with self.subTest(field=field,bad=bad):self.refused(lambda:self.assess(value))

    def test_closed_nested_objects_cannot_carry_private_payloads(self):
        changes=(lambda v:v['exchange'].update(private_rows='SYNTHETIC_PRIVATE_CANARY'),
          lambda v:v['resources'].update(private_rows='SYNTHETIC_PRIVATE_CANARY'),
          lambda v:v['stages'][0].update(private_rows='SYNTHETIC_PRIVATE_CANARY'),
          lambda v:v['stages'][0]['queries'][0].update(private_rows='SYNTHETIC_PRIVATE_CANARY'))
        for index,change in enumerate(changes):
            value=report();change(value)
            with self.subTest(index=index):self.refused(lambda:self.assess(value))

    def test_duplicate_json_invalid_utf8_constants_and_wrong_raw_types_refuse(self):
        raw=encoded(report())
        duplicates=(raw.replace(b'"version":1',b'"version":1,"version":1',1),
          raw.replace(b'"acceptconn":1',b'"acceptconn":1,"acceptconn":1',1),
          raw.replace(b'"count":12',b'"count":12,"count":12',1))
        for bad in(*duplicates,b'\xff',b'{"v":NaN}',b'{"v":Infinity}',b'[]',raw+b'{}',bytearray(raw),raw.decode(),None):
            with self.subTest(type=type(bad).__name__):self.refused(lambda:n.assess_report(bad,PROCESS))

    def test_report_size_limit_is_enforced_before_json_acquisition(self):
        raw=encoded(report());limit=512*1024
        padded=raw+b' '*(limit-len(raw));self.assertTrue(n.assess_report(padded,PROCESS)['acquisition_completed'])
        self.refused(lambda:n.assess_report(padded+b' ',PROCESS))

    def test_expected_process_and_returned_summary_do_not_alias_fixture_state(self):
        expected=copy.deepcopy(PROCESS);raw=encoded(report());before=bytes(raw)
        result=n.assess_report(raw,expected);result['listener_states'][0]=999
        self.assertEqual(expected,PROCESS);self.assertEqual(raw,before)
        self.assertEqual(n.assess_report(raw,expected)['listener_states'],[2]*12)

    def test_abi_scalar_coercions_and_equal_valued_float_bounds_refuse(self):
        for offset,bad in((0,False),(1,4.0)):
            value=report();value['abi']['basic']['field_offsets'][offset]=bad
            with self.subTest(offset=offset):self.refused(lambda:self.assess(value))
        for field in('allocated_bytes','returned_bytes','count'):
            value=report();q=query(value);q[field]=float(q[field])
            with self.subTest(field=field):self.refused(lambda:self.assess(value))


@unittest.skipUnless(os.name=='nt','physical D: launcher fixtures require Windows')
class NativeLauncherTests(unittest.TestCase):
    def run_launcher(self,*,value=None,owner_change=None,source_change=False,binary_change=False,
                     missing_started=False,worker_change=None,stderr=b''):
        from benchmarks import receipt_avd_environment as env
        from benchmarks import windows_tcp_control as control
        base=Path(tempfile.mkdtemp(prefix='locallore-native-tcp-launch-',dir='D:/Dev/_Temp'))
        binary=base/'native-control.exe';binary.write_bytes(b'synthetic executable bytes; never run')
        source=base/'source.py';source.write_bytes(b'# synthetic source pin\n')
        py=base/'python.exe';py.write_bytes(b'synthetic installed interpreter pin')
        pin=env.binding(binary);output=base/'output';payload=encoded(report()if value is None else value)
        caller=dict(pid=9001,creation_filetime=900100,executable=str(py))
        worker=dict(PROCESS,executable=str(binary));worker.update(worker_change or {})
        def identity(pid):
            self.assertIn(pid,(9001,PID));return copy.deepcopy(caller if pid==9001 else worker)
        def supervise(argv,barrier,out,seconds,started):
            self.assertEqual(argv,[str(binary)]);self.assertEqual(barrier,b'LL_NATIVE_TCP_STATE_V1\n')
            self.assertEqual(out,output);self.assertEqual(seconds,30)
            if not missing_started:self.assertTrue(started(SimpleNamespace(pid=PID)))
            (output/'owner-stdout-v1.bin').write_bytes(payload);(output/'owner-stderr-v1.bin').write_bytes(stderr)
            if source_change:source.write_bytes(b'# changed synthetic source\n')
            if binary_change:binary.write_bytes(b'changed synthetic binary bytes')
            result=dict(status='child_exited',cleanup_complete=True,elapsed_ms=17,output_capture_complete=True,
                        worker_returncode=0,stdout_bytes=len(payload),stderr_bytes=len(stderr))
            result.update(owner_change or {});return result
        probe=SimpleNamespace(_python_bindings=lambda:dict(executable=env.binding(py),runtime_dll=None))
        fake_control=SimpleNamespace(_prepare_environment=lambda:None,validate_output=control.validate_output)
        with ExitStack()as stack:
            stack.enter_context(patch.object(n,'_runtime',return_value=(env,fake_control,probe)))
            stack.enter_context(patch.object(n,'_source_bindings',side_effect=lambda *_:[env.binding(source)]))
            stack.enter_context(patch.object(env,'process_identity',side_effect=identity))
            stack.enter_context(patch.object(os,'getpid',return_value=9001))
            owner=stack.enter_context(patch.object(n,'_supervise',side_effect=supervise))
            stack.enter_context(redirect_stdout(io.StringIO()))
            code=n.main(['--binary',str(binary),'--binary-sha256',pin['sha256'],'--output',str(output)])
        owner.assert_called_once()
        return code,env.read_json(output/'result-v1.json'),output,payload

    def test_known_owned_consistent_fixture_exits_zero_without_feature_admission(self):
        code,result,out,raw=self.run_launcher()
        self.assertEqual(code,0);self.assertIs(result['qualified_acquisition'],True)
        self.assertIs(result['observation_consistent'],True);self.assertIs(result['feature_acceptance'],False)
        self.assertEqual((out/'owner-stdout-v1.bin').read_bytes(),raw)

    def test_acquired_unknown_native_states_exit_two_and_are_not_promoted(self):
        code,result,_,_=self.run_launcher(value=report(listener=0,server=0,client=0))
        self.assertEqual(code,2);self.assertTrue(result['qualified_acquisition']);self.assertFalse(result['observation_consistent'])
        self.assertEqual(result['assessment']['listener_states'],[0]*12)

    def test_failed_or_uncaptured_owner_never_qualifies(self):
        for change in(dict(status='timeout'),dict(worker_returncode=1),dict(worker_returncode=True),
                      dict(cleanup_complete=False),dict(output_capture_complete=False)):
            with self.subTest(change=change):
                code,result,_,_=self.run_launcher(owner_change=change)
                self.assertEqual(code,1);self.assertFalse(result['qualified_acquisition'])

    def test_owner_capture_counts_require_exact_integer_types(self):
        for bad in(False,0.0):
            with self.subTest(bad=bad):
                code,result,_,_=self.run_launcher(owner_change=dict(stderr_bytes=bad))
                self.assertEqual(code,1);self.assertFalse(result['qualified_acquisition'])

    def test_changed_binary_or_source_pin_refuses_despite_valid_native_bytes(self):
        for changes in(dict(source_change=True),dict(binary_change=True)):
            with self.subTest(changes=changes):
                code,result,_,_=self.run_launcher(**changes)
                self.assertEqual(code,1);self.assertFalse(result['sources_equal']);self.assertIsNone(result['assessment'])

    def test_missing_started_identity_or_wrong_birth_refuses(self):
        for changes in(dict(missing_started=True),dict(worker_change=dict(creation_filetime=PROCESS['creation_filetime']+1))):
            with self.subTest(changes=changes):
                code,result,_,_=self.run_launcher(**changes)
                self.assertEqual(code,1);self.assertFalse(result['qualified_acquisition'])

    def test_stderr_and_malformed_acquisition_are_retained_but_not_qualified(self):
        value=report();value['resources']['closed_mask']=3
        for changes in(dict(stderr=b'original synthetic failure\n'),dict(value=value)):
            with self.subTest(changes=changes):
                code,result,out,raw=self.run_launcher(**changes)
                self.assertEqual(code,1);self.assertFalse(result['qualified_acquisition'])
                self.assertEqual((out/'owner-stdout-v1.bin').read_bytes(),raw)

    def test_wrong_binary_hash_refuses_before_supervisor_or_output_creation(self):
        from benchmarks import receipt_avd_environment as env
        from benchmarks import windows_tcp_control as control
        base=Path(tempfile.mkdtemp(prefix='locallore-native-tcp-preflight-',dir='D:/Dev/_Temp'))
        binary=base/'control.exe';binary.write_bytes(b'synthetic executable; never run');out=base/'output'
        fake_control=SimpleNamespace(_prepare_environment=lambda:None,validate_output=control.validate_output)
        with patch.object(n,'_runtime',return_value=(env,fake_control,SimpleNamespace())),patch.object(n,'_supervise')as owner:
            with self.assertRaises(n.NativeControlRefused):
                n.main(['--binary',str(binary),'--binary-sha256','0'*64,'--output',str(out)])
        owner.assert_not_called();self.assertFalse(out.exists())

    def test_all_owner_counts_and_closed_keys_are_required(self):
        for change in(dict(elapsed_ms=False),dict(elapsed_ms=1.0),dict(private_rows='SYNTHETIC_PRIVATE_CANARY')):
            with self.subTest(change=change):
                code,result,_,_=self.run_launcher(owner_change=change)
                self.assertEqual(code,1);self.assertFalse(result['qualified_acquisition'])


class FakeFlag:
    def __init__(self):self.value=False
    def set(self):self.value=True
    def is_set(self):return self.value


class FakeCapture:
    def __init__(self,events,*,fail=False,overflow=False,close_fail=False):
        self.events=events;self.failed=FakeFlag();self.overflow=FakeFlag();self.sizes=[0,0]
        self.fail,self.limit,self.close_fail=fail,overflow,close_fail
    def append(self,channel,data):
        self.events.append(('capture',channel))
        if self.fail:self.failed.set();return False
        if self.limit:self.overflow.set();return False
        self.sizes[channel]+=len(data);return True
    def close(self):
        self.events.append('capture-close')
        if self.close_fail:raise OSError('synthetic capture close')


class FakeInput:
    def __init__(self,events,*,chunk=None,bad=None):
        self.events=events;self.chunk=chunk;self.bad=bad;self.sent=bytearray();self.closed=False
    def write(self,data):
        self.events.append('stdin-write')
        if self.bad is not None:return self.bad
        count=len(data)if self.chunk is None else min(self.chunk,len(data))
        self.sent.extend(bytes(data[:count]));return count
    def close(self):self.events.append('stdin-close');self.closed=True


class FakeOutput:
    def __init__(self,events,name,data=b'',*,read_fail=False,close_fail=False):
        self.events=events;self.name=name;self.data=data;self.read_fail=read_fail;self.close_fail=close_fail
    def read(self,limit):
        self.events.append(self.name+'-read')
        if self.read_fail:raise OSError('synthetic reader failure')
        data=self.data[:limit];self.data=self.data[limit:];return data
    def close(self):
        self.events.append(self.name+'-close')
        if self.close_fail:raise OSError('synthetic pipe close')


class FakeChild:
    def __init__(self,events,*,chunk=None,bad=None,read_fail=False,stream_close_fail=False,wait_fail=False,hang=False):
        self.pid=PID;self.events=events;self.returncode=None;self.wait_fail=wait_fail;self.hang=hang
        self.stdin=FakeInput(events,chunk=chunk,bad=bad)
        self.stdout=FakeOutput(events,'stdout',b'original synthetic output',read_fail=read_fail,close_fail=stream_close_fail)
        self.stderr=FakeOutput(events,'stderr')
    def poll(self):
        self.events.append('poll')
        if self.stdin.closed and not self.hang:self.returncode=0
        return self.returncode
    def kill(self):self.events.append('kill-own-child');self.returncode=-9
    def wait(self,timeout):
        self.events.append('wait-own-child')
        if self.wait_fail:raise subprocess.TimeoutExpired('synthetic-child',timeout)
        return self.returncode


class FakeJob:
    def __init__(self,events,child,*,closed=True):self.events=events;self.child=child;self.closed=closed
    def close(self):
        self.events.append('job-close')
        if self.child.returncode is None:self.child.returncode=-9
        return self.closed


class FakeReaderThread:
    def __init__(self,*,target,args,daemon):
        self.target=target;self.args=args;self.daemon=daemon;self.stalled=False;self.started=False;self.start_fail=False
    def start(self):
        if self.start_fail:raise RuntimeError('synthetic thread resource exhaustion')
        self.started=True;self.target(*self.args)
    def join(self,timeout):
        if not self.started:raise RuntimeError('cannot join thread before it is started')
    def is_alive(self):return self.stalled


@unittest.skipUnless(os.name=='nt','Windows scoped-supervisor contract')
class NativeSupervisorTests(unittest.TestCase):
    def supervise(self,*,callback='true',chunk=None,bad=None,job_fail=False,job_closed=True,
                  read_fail=False,capture_fail=False,overflow=False,capture_close_fail=False,
                  stream_close_fail=False,wait_fail=False,hang=False,stalled=False,create_capture_fail=False,start_fail=False):
        events=[];child=FakeChild(events,chunk=chunk,bad=bad,read_fail=read_fail,
          stream_close_fail=stream_close_fail,wait_fail=wait_fail,hang=hang)
        capture=FakeCapture(events,fail=capture_fail,overflow=overflow,close_fail=capture_close_fail)
        def create(root):
            events.append('capture-create')
            if create_capture_fail:raise OSError('synthetic create refusal')
            return capture
        def popen(*args,**kwargs):events.append('popen-own-child');return child
        def job(pid):
            self.assertEqual(pid,child.pid);events.append('assign-own-job')
            if job_fail:raise OSError('synthetic job assignment refusal')
            return FakeJob(events,child,closed=job_closed)
        def started(actual):
            self.assertIs(actual,child);self.assertEqual(actual.pid,PID);events.append('identity-recorded')
            if callback=='false':return False
            if callback=='throw':raise ValueError('synthetic identity refusal')
            if callback=='cancel':raise KeyboardInterrupt()
            return True
        def thread(**kwargs):
            value=FakeReaderThread(**kwargs);value.stalled=stalled;value.start_fail=start_fail;return value
        class FakeEnvironmentRefused(RuntimeError):pass
        env=SimpleNamespace(LiveOutput=create,host=SimpleNamespace(WindowsJob=job),EnvironmentRefused=FakeEnvironmentRefused)
        clock=lambda:2.0 if hang and child.stdin.closed else 0.0
        with patch.object(n,'_runtime',return_value=(env,None,None)), \
             patch.object(subprocess,'Popen',side_effect=popen)as process, \
             patch.object(threading,'Thread',side_effect=thread),patch.object(time,'monotonic',side_effect=clock):
            result=n._supervise(['D:\\Synthetic\\never-executed.exe'],n.BARRIER,Path('D:/Synthetic/capture'),1,started)
        if create_capture_fail:process.assert_not_called()
        else:process.assert_called_once()
        return result,events,child,capture

    def test_actual_child_identity_is_recorded_before_any_stdin_release(self):
        result,events,child,_=self.supervise()
        self.assertLess(events.index('assign-own-job'),events.index('identity-recorded'))
        self.assertLess(events.index('identity-recorded'),events.index('stdin-write'))
        self.assertEqual(bytes(child.stdin.sent),n.BARRIER)
        self.assertEqual(result['status'],'child_exited');self.assertTrue(result['cleanup_complete'])
        self.assertTrue(result['output_capture_complete']);self.assertEqual(result['worker_returncode'],0)

    def test_false_throwing_or_cancelled_identity_never_releases_barrier(self):
        for callback in('false','throw','cancel'):
            with self.subTest(callback=callback):
                result,events,child,_=self.supervise(callback=callback)
                self.assertNotIn('stdin-write',events);self.assertEqual(child.stdin.sent,b'')
                self.assertIn('job-close',events);self.assertNotEqual(result['status'],'child_exited')

    def test_partial_writes_release_each_barrier_byte_exactly_once(self):
        result,events,child,_=self.supervise(chunk=3)
        self.assertEqual(bytes(child.stdin.sent),n.BARRIER);self.assertGreater(events.count('stdin-write'),1)
        self.assertEqual(result['status'],'child_exited');self.assertTrue(result['cleanup_complete'])

    def test_zero_boolean_negative_or_oversized_write_refuses(self):
        for bad in(0,True,-1,len(n.BARRIER)+1):
            with self.subTest(bad=bad):
                result,events,child,_=self.supervise(bad=bad)
                self.assertEqual(child.stdin.sent,b'');self.assertEqual(result['status'],'owner_failed')
                self.assertEqual(events.count('stdin-write'),1);self.assertIn('job-close',events)

    def test_failed_job_assignment_kills_only_own_still_blocked_child(self):
        result,events,child,_=self.supervise(job_fail=True)
        self.assertNotIn('stdin-write',events);self.assertNotIn('identity-recorded',events)
        self.assertEqual(events.count('kill-own-child'),1);self.assertIn('wait-own-child',events)
        self.assertEqual(result['status'],'owner_failed');self.assertTrue(result['cleanup_complete'])

    def test_reader_or_capture_failure_never_claims_complete_capture(self):
        for changes in(dict(read_fail=True),dict(capture_fail=True),dict(capture_close_fail=True)):
            with self.subTest(changes=changes):
                result,events,_,_=self.supervise(**changes)
                self.assertEqual(result['status'],'evidence_failed');self.assertFalse(result['output_capture_complete'])
                self.assertIn('job-close',events)

    def test_output_overflow_and_total_budget_expiry_are_failures(self):
        for changes,status in((dict(overflow=True),'output_limit'),(dict(hang=True),'expired')):
            with self.subTest(changes=changes):
                result,events,_,_=self.supervise(**changes)
                self.assertEqual(result['status'],status);self.assertIn('job-close',events)

    def test_uncertain_job_pipe_wait_or_reader_closure_is_not_promoted(self):
        for changes in(dict(job_closed=False),dict(stream_close_fail=True),dict(wait_fail=True),dict(stalled=True)):
            with self.subTest(changes=changes):
                result,events,_,_=self.supervise(**changes)
                self.assertFalse(result['cleanup_complete']);self.assertIn('job-close',events)
                if changes.get('stalled'):
                    self.assertEqual(result['status'],'evidence_failed');self.assertIsNone(result['stdout_bytes'])
                    self.assertFalse(result['output_capture_complete'])

    def test_capture_creation_failure_prevents_process_dispatch(self):
        result,events,_,_=self.supervise(create_capture_fail=True)
        self.assertNotIn('popen-own-child',events);self.assertFalse(result['cleanup_complete'])
        self.assertFalse(result['output_capture_complete']);self.assertEqual(result['status'],'evidence_failed')

    def test_failed_job_close_still_attempts_all_owned_stopped_pipes(self):
        result,events,_,_=self.supervise(job_closed=False)
        self.assertFalse(result['cleanup_complete'])
        for event in('stdin-close','stdout-close','stderr-close','capture-close'):
            self.assertIn(event,events)

    def test_thread_start_resource_failure_never_escapes_or_releases_child(self):
        result,events,child,_=self.supervise(start_fail=True)
        self.assertNotIn('stdin-write',events);self.assertEqual(child.stdin.sent,b'')
        for event in('job-close','wait-own-child','stdin-close','stdout-close','stderr-close','capture-close'):
            self.assertIn(event,events)
        self.assertFalse(result['cleanup_complete']);self.assertFalse(result['output_capture_complete'])
        self.assertNotEqual(result['status'],'child_exited')


if __name__=='__main__':unittest.main()
