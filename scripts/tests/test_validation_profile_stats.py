"""Original profiling semantics/ownership tests; no speed acceptance threshold."""
import copy
import json
from pathlib import Path
import sys
import unittest

from benchmarks.validation_profile_stats import ProfileCapture


TOP={'version','scope','wall_ns','cpu_ns','total_calls','primitive_calls','entries'}
ENTRY={'filename','line','function','primitive_calls','calls','self_ns','cumulative_ns'}


def _leaf():
    total=0
    for value in range(17):total+=value
    return total


def _recursive(depth):
    return _leaf()+(_recursive(depth-1)if depth else 0)


def _nested():
    return _leaf()+_leaf()


def _profiler_state():
    monitoring=getattr(sys,'monitoring',None)
    if monitoring is None:return sys.getprofile(),None,None
    tool=monitoring.PROFILER_ID
    return sys.getprofile(),monitoring.get_tool(tool),monitoring.get_events(tool)


class ValidationProfileStatsTests(unittest.TestCase):
    def setUp(self):
        self.original=sys.getprofile()
        self.assertIsNone(self.original,'finite test worker must start without an external profiler')
        self.assertIsNone(_profiler_state()[1],'finite test worker must start without a monitoring profiler')
        self.addCleanup(self.restore_test_owned_profilers)

    def restore_test_owned_profilers(self):
        # This finite worker starts with no profiler. Any tool installed by
        # these tests is test-owned; release it even after a failing assertion
        # so one observed leak cannot manufacture later independent failures.
        monitoring=getattr(sys,'monitoring',None)
        if monitoring is not None and monitoring.get_tool(monitoring.PROFILER_ID)is not None:
            monitoring.free_tool_id(monitoring.PROFILER_ID)
        sys.setprofile(self.original)

    def shape(self,value):
        self.assertIsNone(_profiler_state()[1],'owned monitoring profiler must be released before snapshot')
        self.assertIs(type(value),dict);self.assertEqual(set(value),TOP)
        self.assertIs(type(value['version']),int);self.assertEqual(value['version'],1)
        self.assertEqual(value['scope'],'python-cprofile-cost-v1')
        for name in('wall_ns','cpu_ns','total_calls','primitive_calls'):
            self.assertIs(type(value[name]),int);self.assertGreaterEqual(value[name],0)
        self.assertIs(type(value['entries']),list);self.assertTrue(value['entries'])
        keys=[]
        for entry in value['entries']:
            self.assertIs(type(entry),dict);self.assertEqual(set(entry),ENTRY)
            for name in('filename','function'):self.assertIs(type(entry[name]),str);self.assertTrue(entry[name])
            for name in('line','primitive_calls','calls','self_ns','cumulative_ns'):
                self.assertIs(type(entry[name]),int);self.assertGreaterEqual(entry[name],0)
            self.assertLessEqual(entry['primitive_calls'],entry['calls'])
            self.assertLessEqual(entry['self_ns'],entry['cumulative_ns'])
            keys.append((entry['filename'],entry['line'],entry['function']))
        self.assertEqual(keys,sorted(set(keys)))
        self.assertEqual(value['total_calls'],sum(entry['calls']for entry in value['entries']))
        self.assertEqual(value['primitive_calls'],sum(entry['primitive_calls']for entry in value['entries']))

    def entry(self,value,function):
        matches=[item for item in value['entries']if item['function']==function.__name__ and
                 Path(item['filename']).name==Path(__file__).name]
        self.assertEqual(len(matches),1)
        self.assertEqual(matches[0]['line'],function.__code__.co_firstlineno)
        return matches[0]

    def test_one_action_closed_snapshot_has_integer_counters_and_closed_sorted_schema(self):
        events=[]
        with ProfileCapture()as capture:
            events.append(_leaf())
        self.assertEqual(events,[136]);self.assertIsNone(sys.getprofile())
        value=capture.snapshot();self.shape(value)
        self.assertEqual((self.entry(value,_leaf)['primitive_calls'],self.entry(value,_leaf)['calls']),(1,1))

    def test_recursive_total_calls_and_primitive_calls_keep_pstats_meaning(self):
        with ProfileCapture()as capture:result=_recursive(4)
        self.assertEqual(result,680);value=capture.snapshot();self.shape(value)
        recursive=self.entry(value,_recursive);leaf=self.entry(value,_leaf)
        self.assertEqual((recursive['primitive_calls'],recursive['calls']),(1,5))
        self.assertEqual((leaf['primitive_calls'],leaf['calls']),(5,5))

    def test_nested_cumulative_cost_is_inclusive_without_becoming_a_wall_time_sum(self):
        with ProfileCapture()as capture:self.assertEqual(_nested(),272)
        value=capture.snapshot();self.shape(value)
        parent=self.entry(value,_nested);leaf=self.entry(value,_leaf)
        self.assertEqual((parent['primitive_calls'],parent['calls']),(1,1));self.assertEqual(leaf['calls'],2)
        self.assertGreaterEqual(parent['cumulative_ns'],leaf['cumulative_ns'])
        # Inclusive cumulative entries overlap. Deliberately do not compare
        # their sum to either wall_ns or cpu_ns or impose a speed threshold.

    def test_original_action_exception_identity_propagates_and_clean_stats_remain_observable(self):
        error=LookupError('SYNTHETIC_ACTION_PRIVATE_CANARY');capture=ProfileCapture();seen=[]
        try:
            with capture:
                seen.append(_leaf());raise error
        except BaseException as observed:self.assertIs(observed,error)
        else:self.fail('action exception suppressed')
        self.assertEqual(seen,[136]);self.assertIsNone(sys.getprofile());value=capture.snapshot();self.shape(value)
        self.assertNotIn('SYNTHETIC_ACTION_PRIVATE_CANARY',json.dumps(value))

    def test_keyboard_interrupt_identity_propagates_and_profiler_is_disabled_finally(self):
        error=KeyboardInterrupt();capture=ProfileCapture()
        try:
            with capture:_leaf();raise error
        except BaseException as observed:self.assertIs(observed,error)
        else:self.fail('cancellation suppressed')
        self.assertIsNone(sys.getprofile());self.shape(capture.snapshot())

    def test_repeated_closed_snapshots_are_frozen_independent_deep_copies(self):
        with ProfileCapture()as capture:_recursive(2)
        first=capture.snapshot();expected=copy.deepcopy(first);second=capture.snapshot()
        self.assertEqual(second,expected);self.assertIsNot(first,second);self.assertIsNot(first['entries'],second['entries'])
        first['entries'][0]['calls']=999999;first['entries'].append({'private':'not profile data'});first['wall_ns']=-1
        _recursive(3)  # Later work must not extend this closed observation.
        self.assertEqual(capture.snapshot(),expected);self.assertIsNone(sys.getprofile())

    def test_unstarted_or_active_snapshot_and_unstarted_exit_refuse_without_replacing_profiler(self):
        with self.assertRaises(ValueError):ProfileCapture().snapshot()
        with self.assertRaises(ValueError):ProfileCapture().__exit__(None,None,None)
        with ProfileCapture()as capture:
            active=_profiler_state();self.assertTrue(active[0]is not None or active[1]is not None)
            with self.assertRaises(ValueError):capture.snapshot()
            self.assertEqual(_profiler_state(),active)
        self.assertIsNone(sys.getprofile())
        self.assertIsNone(_profiler_state()[1])

    def test_existing_external_profiler_is_never_disabled_or_replaced_by_refused_entry(self):
        def external(frame,event,arg):return None
        sys.setprofile(external);capture=ProfileCapture()
        with self.assertRaises(ValueError):capture.__enter__()
        self.assertIs(sys.getprofile(),external)
        sys.setprofile(None)
        with self.assertRaises(ValueError):capture.__enter__()
        self.assertIsNone(sys.getprofile())
        monitoring=getattr(sys,'monitoring',None)
        if monitoring is not None:
            calls=[];tool=monitoring.PROFILER_ID;events=monitoring.events.PY_START
            monitoring.use_tool_id(tool,'original-synthetic-external-profiler')
            monitoring.register_callback(tool,events,lambda *args:calls.append('observed'))
            monitoring.set_events(tool,events);state=_profiler_state()
            with self.assertRaises(ValueError):ProfileCapture().__enter__()
            self.assertEqual(_profiler_state(),state);before=len(calls);_leaf();self.assertGreater(len(calls),before)
            monitoring.free_tool_id(tool)

    def test_nested_capture_refuses_while_retaining_outer_profiler_and_outer_statistics(self):
        with ProfileCapture()as outer:
            active=_profiler_state()
            with self.assertRaises(ValueError):ProfileCapture().__enter__()
            self.assertEqual(_profiler_state(),active);_leaf()
        self.assertIsNone(sys.getprofile());self.assertEqual(self.entry(outer.snapshot(),_leaf)['calls'],1)

    def test_context_cannot_be_reused_after_successful_or_exceptional_action(self):
        for fail in(False,True):
            capture=ProfileCapture()
            try:
                with capture:
                    _leaf()
                    if fail:raise LookupError('original synthetic failure')
            except LookupError:pass
            with self.assertRaises(ValueError):capture.__enter__()
            self.assertIsNone(sys.getprofile())

    def test_reentrant_entry_does_not_disable_its_active_owned_profiler(self):
        with ProfileCapture()as capture:
            active=_profiler_state()
            with self.assertRaises(ValueError):capture.__enter__()
            self.assertEqual(_profiler_state(),active)
        self.assertIsNone(sys.getprofile())

    def test_action_installed_external_profiler_is_preserved_and_incomplete_capture_refuses(self):
        def external(frame,event,arg):return None
        capture=ProfileCapture()
        with self.assertRaises(ValueError):
            with capture:_leaf();sys.setprofile(external)
        self.assertIs(sys.getprofile(),external)
        self.assertIsNone(_profiler_state()[1])
        with self.assertRaises(ValueError):capture.snapshot()
        self.assertIs(sys.getprofile(),external)

    def test_action_error_identity_wins_if_profiler_ownership_is_lost(self):
        def external(frame,event,arg):return None
        error=KeyboardInterrupt();capture=ProfileCapture()
        try:
            with capture:sys.setprofile(external);raise error
        except BaseException as observed:self.assertIs(observed,error)
        else:self.fail('action error suppressed')
        self.assertIs(sys.getprofile(),external)
        self.assertIsNone(_profiler_state()[1])
        with self.assertRaises(ValueError):capture.snapshot()
        self.assertIs(sys.getprofile(),external)

    def test_duplicate_exit_cannot_clear_a_later_external_profiler(self):
        with ProfileCapture()as capture:_leaf()
        def external(frame,event,arg):return None
        sys.setprofile(external)
        with self.assertRaises(ValueError):capture.__exit__(None,None,None)
        self.assertIs(sys.getprofile(),external)


if __name__=='__main__':unittest.main()
