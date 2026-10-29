"""Original diagnostic observations; all native and target IO is replaced.

These counters are not target, latency, cleanup or performance acceptance.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import copy
import itertools
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_target_owner as owner
from benchmarks import owned_restart_owner as restart
from scripts.tests import test_owned_target_contract as original
from scripts.tests import test_owned_restart_contract as restarted

PHASES=('total','budget_before','inputs','metadata','observation','validation','budget_after')
TOP={'version','scope','valid','reason','observer_closed','open_phases','complete',
     'feature_acceptance','instrumentation_overhead_included','rows'}
FIELDS={'phase','calls','completed','raised','wall_ns','max_ns'}
MAX_NS=(1<<63)-1


class CollectorTests(unittest.TestCase):
    def collector(self):
        self.assertTrue(hasattr(owner,'_GuardPhases'),'the diagnostic collector must exist')
        return owner._GuardPhases()

    def valid(self,value,closed=True):
        self.assertEqual(set(value),TOP)
        self.assertEqual((value['version'],value['scope']),(1,'owned-target-guard-phases-v1'))
        self.assertIs(value['valid'],True);self.assertIsNone(value['reason'])
        self.assertIs(value['observer_closed'],closed)
        self.assertIs(value['feature_acceptance'],False)
        self.assertIs(value['instrumentation_overhead_included'],True)
        self.assertEqual([row['phase']for row in value['rows']],list(PHASES))
        for row in value['rows']:
            self.assertEqual(set(row),FIELDS)
            for key in FIELDS-{'phase'}:
                self.assertIs(type(row[key]),int);self.assertGreaterEqual(row[key],0)
            self.assertEqual(row['completed']+row['raised'],row['calls'])
            self.assertLessEqual(row['max_ns'],row['wall_ns'])

    def test_nested_spans_count_real_calls_without_adding_total_to_children(self):
        stats=self.collector()
        with patch.object(owner.time,'perf_counter_ns',side_effect=[10,20,35,50]):
            with stats.phase('total'):
                with stats.phase('inputs'):pass
        value=stats.snapshot(True);self.valid(value)
        rows={row['phase']:row for row in value['rows']}
        self.assertEqual((rows['total']['calls'],rows['total']['wall_ns'],rows['total']['max_ns']),(1,40,40))
        self.assertEqual((rows['inputs']['calls'],rows['inputs']['wall_ns']),(1,15))
        self.assertEqual(value['open_phases'],0);self.assertIs(value['complete'],True)
        self.assertEqual(sum(row['calls']for row in value['rows']),2)

    def test_original_exception_and_cancellation_identity_survives_observation(self):
        for failure in (RuntimeError('private-body-canary'),KeyboardInterrupt(),SystemExit(7)):
            with self.subTest(type=type(failure).__name__):
                stats=self.collector()
                with patch.object(owner.time,'perf_counter_ns',side_effect=[1,3]):
                    try:
                        with stats.phase('validation'):raise failure
                    except BaseException as error:self.assertIs(error,failure)
                    else:self.fail('primary failure was swallowed')
                row=stats.snapshot(True)['rows'][5]
                self.assertEqual((row['calls'],row['raised'],row['completed']),(1,1,0))
                self.assertNotIn('private-body-canary',json.dumps(stats.snapshot(True)))

    def test_clock_invalid_types_bounds_and_regression_invalidate_without_skipping_body(self):
        for clock in (True,1.5,-1,MAX_NS+1,'private-clock-canary'):
            with self.subTest(clock_type=type(clock).__name__):
                stats=self.collector();body=[]
                with patch.object(owner.time,'perf_counter_ns',return_value=clock):
                    with stats.phase('inputs'):body.append('once')
                value=stats.snapshot(True)
                self.assertEqual(body,['once']);self.assertIs(value['valid'],False)
                self.assertEqual(value['reason'],'clock');self.assertIs(value['complete'],False)
                self.assertNotIn('private-clock-canary',json.dumps(value))
        stats=self.collector()
        with patch.object(owner.time,'perf_counter_ns',side_effect=[20,19]):
            with stats.phase('inputs'):pass
        self.assertEqual(stats.snapshot(True)['reason'],'clock')

    def test_observer_clock_exceptions_preserve_primary_and_do_not_swallow_interrupt(self):
        stats=self.collector();body=[]
        with patch.object(owner.time,'perf_counter_ns',side_effect=OSError('private-clock-error')):
            with stats.phase('inputs'):body.append('once')
        self.assertEqual(body,['once']);self.assertEqual(stats.snapshot(True)['reason'],'clock')
        for primary in (None,RuntimeError('primary')):
            stats=self.collector();interrupt=KeyboardInterrupt()
            with patch.object(owner.time,'perf_counter_ns',side_effect=[1,interrupt]):
                try:
                    with stats.phase('inputs'):
                        if primary is not None:raise primary
                except BaseException as error:self.assertIs(error,primary if primary is not None else interrupt)
                else:self.fail('primary failure or user interrupt was swallowed')

    def test_counter_and_nanosecond_saturation_do_not_wrap_or_claim_validity(self):
        for field in ('calls','wall_ns'):
            stats=self.collector()
            if field=='calls':stats._rows['inputs'].update(calls=1_000_000,completed=1_000_000)
            else:stats._rows['inputs'].update(calls=1,completed=1,wall_ns=MAX_NS,max_ns=MAX_NS)
            with patch.object(owner.time,'perf_counter_ns',side_effect=[1,2]):
                with stats.phase('inputs'):pass
            value=stats.snapshot(True);self.assertIs(value['valid'],False)
            self.assertEqual(value['reason'],'overflow');self.assertIs(value['complete'],False)

    def test_malformed_state_is_sanitized_and_snapshots_are_independent(self):
        stats=self.collector();value=stats.snapshot(True);self.valid(value)
        value['rows'][0]['calls']=999;value['rows'].append({'private':'path-canary'})
        self.assertEqual(stats.snapshot(True)['rows'][0]['calls'],0)
        for bad in (None,{'inputs':{}},{name:{'private':'path-canary'}for name in PHASES}):
            stats=self.collector();stats._rows=copy.deepcopy(bad)
            value=stats.snapshot(True)
            self.assertIs(value['valid'],False);self.assertEqual(value['reason'],'state')
            self.assertEqual(value['rows'],[]);self.assertNotIn('path-canary',json.dumps(value))

    def test_open_spans_and_open_observer_never_claim_complete(self):
        stats=self.collector()
        with patch.object(owner.time,'perf_counter_ns',side_effect=[1,2]):
            with stats.phase('observation'):
                value=stats.snapshot(True);self.valid(value)
                self.assertEqual(value['open_phases'],1);self.assertIs(value['complete'],False)
        value=stats.snapshot(False);self.valid(value,False);self.assertIs(value['complete'],False)
        self.assertIs(stats.snapshot(True)['complete'],True)

    def test_concurrent_phase_body_does_not_hold_the_aggregate_lock(self):
        stats=self.collector();entered=threading.Event();release=threading.Event();second_done=threading.Event();errors=[]
        def first():
            try:
                with stats.phase('inputs'):entered.set();release.wait(3)
            except BaseException as error:errors.append(error)
        def second():
            try:
                with stats.phase('inputs'):pass
            except BaseException as error:errors.append(error)
            finally:second_done.set()
        with patch.object(owner.time,'perf_counter_ns',side_effect=itertools.count()):
            one=threading.Thread(target=first);two=threading.Thread(target=second)
            one.start();self.assertTrue(entered.wait(1));two.start()
            try:self.assertTrue(second_done.wait(1),'second body must finish while first body remains held')
            finally:release.set();one.join(2);two.join(2)
        self.assertFalse(one.is_alive());self.assertFalse(two.is_alive());self.assertEqual(errors,[])
        value=stats.snapshot(True);self.valid(value);self.assertEqual(value['rows'][2]['calls'],2)

    def test_counter_lock_contention_is_nonblocking_and_invalidates_observation(self):
        stats=self.collector();done=threading.Event();body=[]
        def action():
            try:
                with stats.phase('metadata'):body.append('once')
            finally:done.set()
        stats._lock.acquire();thread=threading.Thread(target=action);thread.start()
        try:self.assertTrue(done.wait(1),'diagnostics cannot block an authoritative body on its counter lock')
        finally:stats._lock.release();thread.join(2)
        self.assertEqual(body,['once']);value=stats.snapshot(True)
        self.assertIs(value['valid'],False);self.assertEqual(value['reason'],'busy')


class GuardFixture:
    """Construct actual concrete lease types; replace only native/input boundaries."""
    def __init__(self,restart_profile=False,failure=None):
        self.events=[];self.failure=failure;self.primary=RuntimeError('original-phase-refusal')
        self.selected=restart.contract if restart_profile else owner.contract
        self.kind=restart.LiveOwnedRestartTarget if restart_profile else owner.LiveOwnedTarget
        self.a=restarted.admission()if restart_profile else original.admission()
        self.d=restarted.running(self.a)if restart_profile else original.running(self.a)
        self.a['root']='D:/Dev/_Temp/guard-phases-synthetic-no-IO'
        self.live=self.kind.__new__(self.kind);live=self.live
        live._closed=False;live._guard_close_known=False;live._api=object()
        live._last_time=None;live._clock_lock=threading.Lock();live._deadline=1000
        live._admission=self.a;live._descriptor=self.d
        live._admission_binding={'slot':'admission','sha256':'a'*64};live._running_binding={'slot':'running'}
        live._guard_phases=owner._GuardPhases()if hasattr(owner,'_GuardPhases')else None
        self.close=Mock(return_value=True);self.held_calls=0
        def held():
            self.held_calls+=1;self.event('held')
            if failure==('budget_before'if self.held_calls==1 else'budget_after'):raise self.primary
        live._handles=SimpleNamespace(guard=held,close=self.close)
        observation=original.ready(self.a,self.d)['guest_observation']
        self.capture=(observation,original.table_metadata(observation));self.stack=ExitStack()
    def event(self,label):self.events.append(label)
    def operation(self,label,phase,value=None):
        def call(*args,**kwargs):
            self.event(label)
            if phase is not None and self.failure==phase:raise self.primary
            return value
        return call
    def __enter__(self):
        selected=self.selected
        self.stack.enter_context(patch.object(owner.time,'monotonic',return_value=100))
        self.stack.enter_context(patch.object(owner.time,'time',return_value=1800000010.0))
        self.stack.enter_context(patch.object(owner.os.path,'lexists',return_value=False))
        self.stack.enter_context(patch.object(owner,'_check_ancestry',side_effect=self.operation('ancestry',None)))
        self.stack.enter_context(patch.object(selected,'revalidate_inputs',side_effect=self.operation('inputs','inputs')))
        def metadata(pin,**kwargs):return self.operation(pin['slot'],'metadata',self.a if pin['slot']=='admission'else self.d)()
        self.stack.enter_context(patch.object(owner,'_read_json',side_effect=metadata))
        self.stack.enter_context(patch.object(owner,'_observe',side_effect=self.operation('observation','observation',self.capture)))
        actual_validate=selected.validate_guest_observation;actual_tables=owner.server_contract._tables
        def validate(*args):
            self.operation('validation','validation')();return actual_validate(*args)
        def tables(*args):self.event('tables');return actual_tables(*args)
        self.stack.enter_context(patch.object(selected,'validate_guest_observation',side_effect=validate))
        self.stack.enter_context(patch.object(owner.server_contract,'_tables',side_effect=tables))
        for target,name in ((owner,'_ProcessApi'),(owner.socket,'socket'),(owner.subprocess,'Popen')):
            self.stack.enter_context(patch.object(target,name,side_effect=AssertionError('unmocked native operation')))
        return self
    def __exit__(self,*args):return self.stack.__exit__(*args)


class GuardIntegrationTests(unittest.TestCase):
    def test_actual_profiles_preserve_guard_order_and_expose_closed_observations(self):
        for profile in (False,True):
            with self.subTest(restart=profile),GuardFixture(profile)as f:
                f.live.guard()
                self.assertEqual(f.events,['held','ancestry','inputs','admission','running','observation','validation','tables','held','ancestry'])
                self.assertIs(f.live.close(),True)
                getter=getattr(f.live,'guard_phase_snapshot',None)
                self.assertTrue(callable(getter),'actual SDK4/5 leases must expose post-close guard phase observations')
                value=getter();self.assertIs(value['complete'],True)
                self.assertEqual([row['phase']for row in value['rows']],list(PHASES))
                self.assertTrue(all(row['calls']==row['completed']==1 and row['raised']==0 for row in value['rows']))

    def test_each_original_guard_refusal_keeps_identity_and_stops_later_phases(self):
        for profile in (False,True):
            for failure in PHASES[1:]:
                with self.subTest(restart=profile,phase=failure),GuardFixture(profile,failure)as f:
                    try:f.live.guard()
                    except BaseException as error:self.assertIs(error,f.primary)
                    else:self.fail('original guard refusal swallowed')
                    f.live.close();value=f.live.guard_phase_snapshot()
                    rows={row['phase']:row for row in value['rows']}
                    self.assertEqual((rows['total']['calls'],rows['total']['raised']),(1,1))
                    self.assertEqual((rows[failure]['calls'],rows[failure]['raised']),(1,1))
                    for later in PHASES[PHASES.index(failure)+1:]:self.assertEqual(rows[later]['calls'],0)

    def test_closed_flag_does_not_replace_known_close_and_getter_is_pure(self):
        for result in (None,False,1,True):
            with self.subTest(close_result=result),GuardFixture()as f:
                f.live.guard();f.close.return_value=result
                self.assertIs(f.live.close(),result);self.assertTrue(f.live._closed)
                f.events.clear()
                with patch.object(owner.environment,'binding',side_effect=AssertionError('snapshot IO')):
                    value=f.live.guard_phase_snapshot()
                self.assertIs(value['observer_closed'],result is True)
                self.assertIs(value['complete'],result is True);self.assertEqual(f.events,[])
                self.assertEqual(f.close.call_count,1)


if __name__=='__main__':unittest.main()
