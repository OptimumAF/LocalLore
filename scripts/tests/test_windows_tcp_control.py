"""Original synthetic owned-socket controls; never native or network execution.

Assessment consistency does not authenticate a process, service, SDK or device.
The CLI preflight tests replace the dispatch seam before attempting bad outputs.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
import ipaddress
import os
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stdout

from benchmarks import windows_tcp_control as t

PID, LISTENER, CLIENT = 808, 41001, 41002


def encode_row(kind, ordinal=0, *, state=2, local_port=LISTENER,
               remote_address='0.0.0.0', remote_port=0, pid=PID, offload_state=0):
    address = lambda value: int.from_bytes(ipaddress.IPv4Address(value).packed, 'little')
    port = lambda value: int.from_bytes(value.to_bytes(2, 'big'), 'little')
    words = [state, address('127.0.0.1'), port(local_port), address(remote_address), port(remote_port)]
    if kind != 'GetTcpTable':
        words.append(pid)
    if kind == 'GetTcpTable2':
        words.append(offload_state)
    raw = struct.pack('<'+'I'*len(words), *words)
    value = dict(ordinal=ordinal, original_offset=4+ordinal*len(raw), row_bytes=len(raw),
                 raw_hex=raw.hex(), raw_sha256=hashlib.sha256(raw).hexdigest(), family=2,
                 local_address='127.0.0.1', local_port=local_port, remote_address=remote_address,
                 remote_port=remote_port, state=state, pid=None if kind=='GetTcpTable' else pid,
                 has_listen_state=state==2)
    if kind in ('GetTcpTable', 'GetTcpTable2'):
        value.update(selection_owner_pid=PID,
                     offload_state=offload_state if kind=='GetTcpTable2' else None)
    else:
        value.update(local_scope_id=0, remote_scope_id=0)
    return value


def native_table(kind, connected=False, bound=False):
    stride = 20 if kind=='GetTcpTable' else 28 if kind=='GetTcpTable2' else 24
    rows = [] if bound else [encode_row(kind)]
    if connected and kind != 3:
        rows.extend((encode_row(kind, 1, state=5, remote_address='127.0.0.1', remote_port=CLIENT),
                     encode_row(kind, 2, state=5, local_port=CLIENT,
                                remote_address='127.0.0.1', remote_port=LISTENER)))
    count = len(rows)
    value = dict(family=2, initial_return=122, final_return=0, returned_bytes=4+count*stride,
                 allocated_bytes=4+count*stride, count=count,
                 count_header_hex=struct.pack('<I', count).hex(), table_rows_offset=4,
                 row_stride=stride, selected_rows=rows)
    if kind in ('GetTcpTable', 'GetTcpTable2'):
        value.update(api=kind, captured_scope='selected_owned_loopback_ports_PID_when_API_supplies_PID')
    else:
        value.update(table_class=kind, captured_scope='exact_owned_PID_and_owned_ports_only')
    return value


def fixture():
    offsets = dict(state=0, local=4, port=8, remote=12, remote_port=16)
    shapes = {'2':dict(offsets,pid=20),
              '23':dict(local=0,local_scope_id=16,port=20,remote=24,remote_scope_id=40,
                        remote_port=44,state=48,pid=52),
              'GetTcpTable':offsets, 'GetTcpTable2':dict(offsets,pid=20,offload_state=24)}
    sizes = {'2':24,'23':56,'GetTcpTable':20,'GetTcpTable2':28}
    abi = {key:dict(row_bytes=sizes[key],row_alignment=4,table_rows_offset=4,field_offsets=value)
           for key,value in shapes.items()}
    stages = []
    for i,name in enumerate(('bound_not_listening','after_listen','after_own_connect_and_accept')):
        stages.append(dict(stage=name,socket_acceptconn=0 if i==0 else 1,
                           owned_ports=[LISTENER] if i<2 else [LISTENER,CLIENT],
                           native=[native_table(kind,connected=i==2,bound=i==0) for kind in (3,5)],
                           native_alternatives=[native_table(kind,connected=i==2,bound=i==0)
                                                for kind in ('GetTcpTable','GetTcpTable2')]))
    actions = [dict(action='bind_owned_loopback',address='127.0.0.1',port=LISTENER),
               dict(action='listen_owned_loopback',address='127.0.0.1',port=LISTENER),
               dict(action='connect_only_owned_listener',address='127.0.0.1',port=LISTENER,client_port=CLIENT),
               dict(action='accept_only_owned_client',peer_address='127.0.0.1',peer_port=CLIENT),
               dict(action='one_fixed_owned_loopback_exchange',bytes=17),
               dict(action='owned_socket_contexts_closed',count=3,all_fileno_minus_one=True)]
    for i,action in enumerate(actions):
        action.update(ordinal=i,elapsed_ns=i*1000)
    return dict(version=1,scope='owned_loopback_controls_not_ADB_or_device_qualification',
                feature_acceptance=False,acquisition_completed=True,
                own_process=dict(pid=PID,creation_filetime=123456789,executable='D:/Synthetic/python.exe'),
                ABI=abi,actions=actions,stages=stages,owned_socket_objects_closed=True,
                required_native_LISTEN_state=2,IPv6_attempted=False,sdk_calls=0,device_calls=0,
                existing_service_connections=0,existing_process_controls=0,host_setting_changes=0,
                server_lifecycle_operations=0,references=list(t.REFERENCES))


def tables(report, stage=1):
    return report['stages'][stage]['native']+report['stages'][stage]['native_alternatives']


def change_listener(table, **changes):
    kind = table.get('api',table.get('table_class'))
    table['selected_rows'][0] = encode_row(kind, **changes)


class WindowsTcpControlAssessmentTests(unittest.TestCase):
    def test_complete_synthetic_consistent_controls_are_readonly(self):
        value = fixture()
        before = copy.deepcopy(value)
        self.assertIs(t.assess_controls(value), True)
        self.assertIs(value['feature_acceptance'], False)
        self.assertEqual(value,before)

    def test_acquisition_and_closure_do_not_promote_unknown_listener_state(self):
        value = fixture()
        for index in (1,2):
            for table in tables(value,index):
                change_listener(table,state=0)
        self.assertIs(value['acquisition_completed'], True)
        self.assertIs(value['owned_socket_objects_closed'], True)
        self.assertIs(t.assess_controls(value), False)

    def test_each_observation_path_must_independently_observe_listen(self):
        for stage in (1,2):
            for index in range(4):
                for state in (0,1,5,12,4294967295):
                    value = fixture()
                    change_listener(tables(value,stage)[index],state=state)
                    with self.subTest(stage=stage,path=index,state=state):
                        self.assertIs(t.assess_controls(value), False)

    def test_claimed_has_listen_flag_cannot_override_raw_state(self):
        for index in range(4):
            value = fixture()
            table = tables(value)[index]
            change_listener(table,state=0)
            table['selected_rows'][0]['has_listen_state'] = True
            with self.subTest(path=index):
                self.assertIs(t.assess_controls(value), False)

    def test_listen_remote_endpoint_is_not_given_meaning_by_the_assessor(self):
        value = fixture()
        for stage in (1,2):
            for table in tables(value,stage):
                change_listener(table,remote_address='192.0.2.19',remote_port=65535)
        self.assertIs(t.assess_controls(value), True)

    def test_missing_duplicate_foreign_and_reordered_stages_refuse(self):
        for mode in ('missing','duplicate','foreign','reordered'):
            value = fixture()
            if mode=='missing': value['stages'].pop()
            elif mode=='duplicate': value['stages'][1]=copy.deepcopy(value['stages'][0])
            elif mode=='foreign': value['stages'][1]['stage']='after_external_connect'
            else: value['stages'].reverse()
            with self.subTest(mode=mode):
                self.assertIs(t.assess_controls(value),False)

    def test_all_four_api_paths_are_required_exactly_once(self):
        for group in ('native','native_alternatives'):
            for mode in ('missing','duplicate','foreign'):
                value = fixture()
                rows = value['stages'][1][group]
                if mode=='missing': rows.pop()
                elif mode=='duplicate': rows[1]=copy.deepcopy(rows[0])
                elif group=='native': rows[1]['table_class']=4
                else: rows[1]['api']='GetTcp6Table'
                with self.subTest(group=group,mode=mode):
                    self.assertIs(t.assess_controls(value),False)

    def test_acceptconn_is_an_exact_ordered_integer_observation(self):
        for stage,values in ((0,(True,1,2,None)),(1,(True,False,0,2,None)),(2,(True,False,0,2,None))):
            for observed in values:
                value = fixture()
                value['stages'][stage]['socket_acceptconn']=observed
                with self.subTest(stage=stage,observed=observed):
                    self.assertIs(t.assess_controls(value),False)

    def test_incomplete_closed_or_boolean_counter_claims_refuse(self):
        for field,replacement in (('version',True),('feature_acceptance',True),
                                  ('acquisition_completed',False),('owned_socket_objects_closed',False),
                                  ('owned_socket_objects_closed',1),('required_native_LISTEN_state',0),
                                  ('required_native_LISTEN_state',True),('IPv6_attempted',True),
                                  ('sdk_calls',False),('device_calls',1),('existing_service_connections',1),
                                  ('existing_process_controls',True),('host_setting_changes',1),
                                  ('server_lifecycle_operations',1)):
            value = fixture()
            value[field]=replacement
            with self.subTest(field=field,replacement=replacement):
                self.assertIs(t.assess_controls(value),False)

    def test_bad_report_types_missing_fields_and_extra_claims_never_raise(self):
        for value in (None,True,1,[],(),'',b'{}'):
            with self.subTest(kind=type(value).__name__):
                self.assertIs(t.assess_controls(value),False)
        for field in fixture():
            value = fixture()
            del value[field]
            with self.subTest(missing=field):
                self.assertIs(t.assess_controls(value),False)
        value = fixture()
        value['ADB_qualified']=True
        self.assertIs(t.assess_controls(value),False)

    def test_nested_malformed_values_refuse_without_exception(self):
        for field in ('own_process','ABI','actions','stages','references'):
            for replacement in (None,True,1,'not-a-roster',{},()):
                value = fixture()
                value[field]=replacement
                with self.subTest(field=field,kind=type(replacement).__name__):
                    self.assertIs(t.assess_controls(value),False)
        for field in ('native','native_alternatives','owned_ports'):
            value = fixture()
            value['stages'][1][field]=None
            with self.subTest(field=field):
                self.assertIs(t.assess_controls(value),False)

    def test_owned_process_metadata_is_positive_exact_and_scoped(self):
        for field,replacement in (('pid',0),('pid',True),('creation_filetime',0),
                                  ('creation_filetime',True),('executable',''),
                                  ('executable','relative-python.exe')):
            value = fixture()
            value['own_process'][field]=replacement
            with self.subTest(field=field,replacement=replacement):
                self.assertIs(t.assess_controls(value),False)

    def test_raw_byte_hash_length_and_claimed_fields_must_agree(self):
        for field,replacement in (('raw_hex','00'),('raw_hex','not-hex'),('raw_sha256','0'*64),
                                  ('row_bytes',0),('state',0),('has_listen_state',1),
                                  ('local_address','192.0.2.1'),('local_port',5037),
                                  ('pid',PID+1),('ordinal',True),('original_offset',5)):
            value = fixture()
            tables(value)[0]['selected_rows'][0][field]=replacement
            with self.subTest(field=field):
                self.assertIs(t.assess_controls(value),False)

    def test_basic_api_pid_is_unknown_rather_than_fabricated(self):
        value = fixture()
        row = value['stages'][1]['native_alternatives'][0]['selected_rows'][0]
        self.assertIsNone(row['pid'])
        self.assertIsNone(row['offload_state'])
        row['pid']=PID
        self.assertIs(t.assess_controls(value),False)
        value = fixture()
        value['stages'][1]['native_alternatives'][0]['selected_rows'][0]['selection_owner_pid']=PID+1
        self.assertIs(t.assess_controls(value),False)

    def test_table_returns_capacity_count_and_original_offsets_are_bounded(self):
        for field,replacement in (('initial_return',1),('final_return',1),('family',23),
                                  ('allocated_bytes',1048577),('returned_bytes',3),('count',True),
                                  ('count',16385),('count_header_hex','00000000'),
                                  ('table_rows_offset',8),('row_stride',56),('captured_scope','unfiltered')):
            value = fixture()
            tables(value)[0][field]=replacement
            with self.subTest(field=field):
                self.assertIs(t.assess_controls(value),False)

    def test_listener_must_belong_to_control_port_and_owner(self):
        for kind in ('foreign_pid','client_port'):
            value = fixture()
            table = value['stages'][2]['native'][1]
            change_listener(table,pid=PID+1) if kind=='foreign_pid' else change_listener(table,local_port=CLIENT)
            with self.subTest(kind=kind):
                self.assertIs(t.assess_controls(value),False)

    def test_port_roster_excludes_service_port_duplicates_and_boolean_ports(self):
        for stage,replacement in ((0,[5037]),(1,[True]),(1,[0]),(1,[65536]),
                                  (2,[LISTENER,LISTENER]),(2,[CLIENT,LISTENER]),(2,[LISTENER,5037])):
            value = fixture()
            value['stages'][stage]['owned_ports']=replacement
            with self.subTest(stage=stage,replacement=replacement):
                self.assertIs(t.assess_controls(value),False)

    def test_abi_offsets_and_official_reference_roster_are_closed(self):
        value = fixture()
        value['ABI']['2']['field_offsets']['state']=16
        self.assertIs(t.assess_controls(value),False)
        value = fixture()
        value['references'].append('https://example.invalid/not-an-official-contract')
        self.assertIs(t.assess_controls(value),False)

    def test_action_order_owned_endpoints_exchange_and_closure_are_bound(self):
        for index,field,replacement in ((0,'port',5037),(1,'action','skip_listen'),
                                        (2,'client_port',LISTENER),(3,'peer_address','192.0.2.1'),
                                        (4,'bytes',16),(4,'ordinal',False),
                                        (5,'count',2),(5,'all_fileno_minus_one',1)):
            value = fixture()
            value['actions'][index][field]=replacement
            with self.subTest(index=index,field=field):
                self.assertIs(t.assess_controls(value),False)


class WindowsTcpControlPreflightTests(unittest.TestCase):
    def test_non_windows_refuses_before_path_or_dispatch(self):
        with patch.object(t,'os',SimpleNamespace(name='posix')), \
             patch.object(t,'Path',side_effect=AssertionError('path dispatch must not run')), \
             patch.object(t,'_dispatch',side_effect=AssertionError('native dispatch must not run')) as dispatch:
            with self.assertRaises(t.ControlRefused) as caught:
                t.validate_output('D:/Dev/synthetic-new-output')
            self.assertEqual(str(caught.exception),'platform')
            dispatch.assert_not_called()

    def test_bad_output_arguments_never_dispatch(self):
        for value in (None,1,True,Path('D:/Dev/synthetic-output'),'', 'relative-output',
                      'C:/project-output','E:/project-output'):
            with self.subTest(value=repr(value)), patch.object(t,'_dispatch') as dispatch:
                with self.assertRaises(t.ControlRefused):
                    t.validate_output(value)
                dispatch.assert_not_called()

    @unittest.skipUnless(os.name=='nt','physical D: fixture requires Windows')
    def test_existing_output_directory_is_rejected_and_preserved(self):
        folder = Path(tempfile.mkdtemp(prefix='listener-control-existing-',dir='D:/Dev/_Temp'))
        with patch.object(t,'_dispatch') as dispatch, redirect_stdout(io.StringIO()):
            self.assertEqual(t.main(['--output',str(folder)]),1)
            dispatch.assert_not_called()
        self.assertTrue(folder.is_dir())

    @unittest.skipUnless(os.name=='nt','physical D: fixture requires Windows')
    def test_existing_output_file_is_rejected_without_overwrite(self):
        parent = Path(tempfile.mkdtemp(prefix='listener-control-file-',dir='D:/Dev/_Temp'))
        output = parent/'existing-control'
        original = b'original synthetic sentinel\n'
        with output.open('xb') as sink:
            sink.write(original)
        with patch.object(t,'_dispatch') as dispatch, redirect_stdout(io.StringIO()):
            self.assertEqual(t.main(['--output',str(output)]),1)
            dispatch.assert_not_called()
        self.assertEqual(output.read_bytes(),original)

    @unittest.skipUnless(os.name=='nt','physical D: fixture requires Windows')
    def test_physical_D_preflight_returns_missing_path_without_creating_it(self):
        parent = Path(tempfile.mkdtemp(prefix='listener-control-parent-',dir='D:/Dev/_Temp'))
        output = parent/'new-control'
        with patch.object(t,'_dispatch') as dispatch:
            self.assertEqual(t.validate_output(str(output)),output)
            dispatch.assert_not_called()
        self.assertFalse(output.exists())

    @unittest.skipUnless(os.name=='nt','physical D: fixture requires Windows')
    def test_nonphysical_D_resolution_refuses_before_dispatch(self):
        parent = Path(tempfile.mkdtemp(prefix='listener-control-resolve-',dir='D:/Dev/_Temp'))
        output = parent/'new-control'
        with patch.object(t.Path,'resolve',return_value=Path('C:/compatibility-target')), \
             patch.object(t,'_dispatch') as dispatch, redirect_stdout(io.StringIO()):
            self.assertEqual(t.main(['--output',str(output)]),1)
            dispatch.assert_not_called()
        self.assertFalse(output.exists())


if __name__=='__main__':
    unittest.main()
