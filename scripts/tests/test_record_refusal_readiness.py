"""Original readiness oracles over explicit observation/socket fakes; never approval."""
import copy
import json
from pathlib import PureWindowsPath
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import inspect_record_refusal_readiness as subject


GIB = 1024**3
PRIVATE = 'B122_PRIVATE_PAYLOAD_MUST_NOT_BE_RENDERED'
FORMATTED = []
B121 = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1')
GUEST = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-v1/avd-v1')
EVENTS = ['verify.before', 'resources', 'commit.snapshot', 'commit.check', 'ports', 'storage', 'verify.after']


class PrivateError(Exception):
    def __str__(self):
        FORMATTED.append('error_str')
        return PRIVATE

    def __repr__(self):
        FORMATTED.append('error_repr')
        return PRIVATE


class EnvironmentRefused(PrivateError):
    pass


class HostCommitRefused(PrivateError):
    pass


class StorageRefused(PrivateError):
    pass


class ObjectPayload:
    def __str__(self):
        FORMATTED.append('object_str')
        return PRIVATE

    def __repr__(self):
        FORMATTED.append('object_repr')
        return PRIVATE


class StringPayload(str):
    def __hash__(self):
        FORMATTED.append('string_hash')
        return super().__hash__()

    def __eq__(self, other):
        FORMATTED.append('string_equal')
        return super().__eq__(other)


def binding(path, size, digest):
    return dict(path=str(PureWindowsPath(path)), bytes=size, sha256=digest)


def stamp():
    return dict(profile_head='dbcafb0070734cbccbd420a159f6305bc6f9090d',
        source_catalog=binding(B121/'profile-source-publication-v1.json',755007,
            'aa58a83cd42933165f659b454d768b3b6c4cbc4458efabf300704e09fd50de31'),
        handoff=binding(B121/'inspection-v1/frozen-inputs-v1.json',9021,
            '23e13dc8ef2a9a7dc169dc88bb3ef013767c6e223a126f75ba8d2423c151e041'),
        prepare=binding(B121/'inspection-v1/prepare-proposal-v1.json',173555,
            '4dc63f47db5ab969402f9bac170641c8b6e4a37c494974e047b2369d5f3691aa'),
        ledger=binding('D:/Dev/_Migration/LocalLore-AVD-Storage/ledger-v1.json',52151,'c'*64))


def snapshot(total_gib):
    return dict(version=1,commit_total_bytes=total_gib*GIB,commit_limit_bytes=80*GIB,
                available_commit_bytes=(80-total_gib)*GIB)


def extended(value):
    return dict(value, guest_memory_bytes=8*GIB, required_commit_bytes=10*GIB, reserve_bytes=2*GIB)


class Observations:
    """No path is opened, no real memory/port/ledger is observed by this fixture."""
    EnvironmentRefused = EnvironmentRefused
    HostCommitRefused = HostCommitRefused
    StorageRefused = StorageRefused

    def __init__(self):
        self.plan = dict(memory_mib=8192,cores=4,host_available_memory_min=12*GIB,
                         host_free_min={'C:':16*GIB,'D:':40*GIB},opaque_plan_note=PRIVATE)
        self.stamp = stamp()
        self.after_plan = self.after_stamp = None
        self.events, self.errors, self.verifications = [], {}, 0
        self.resources = dict(free_bytes={'C:':32*GIB,'D:':80*GIB},available_memory=24*GIB,
                              logical_cpus=16,commit_capacity=extended(snapshot(60)))
        # A later sequential reading may differ and still pass independently.
        self.commit = snapshot(68)
        self.commit_facts = extended(self.commit)
        self.ports_result = None
        self.storage = dict(version=1,scope='receipt-avd-prepare-capacity-preview-v1',
            root=str(GUEST),ledger=copy.deepcopy(self.stamp['ledger']),
            active_count=1,max_guests=2,budget_bytes=64*GIB,charged_bytes=20*GIB,
            projected_bytes=60*GIB,reservation_bytes=40*GIB,
            root_limit_exceeded=False,byte_limit_exceeded=False,would_fit=True,admission_granted=False)
        self.forbidden = {name: Mock(side_effect=AssertionError('unexpected operation'))
                          for name in ('prepare','authorize','reserve_prepare','execute','create_authority')}
        for name, call in self.forbidden.items():
            setattr(self,name,call)

    def hit(self, name):
        self.events.append(name)
        if name in self.errors:
            raise self.errors[name]

    def verify(self):
        self.verifications += 1
        after = self.verifications == 2
        self.hit('verify.after' if after else 'verify.before')
        return (self.after_plan if after and self.after_plan is not None else self.plan), \
            (self.after_stamp if after and self.after_stamp is not None else self.stamp)

    def resource_facts(self, plan):
        self.hit('resources')
        assert plan == self.plan
        return self.resources

    def commit_snapshot(self):
        self.hit('commit.snapshot')
        return self.commit

    def commit_check(self, value, memory_mib):
        self.hit('commit.check')
        assert value == self.commit and type(memory_mib) is int and memory_mib == 8192
        return self.commit_facts

    def check_ports(self):
        self.hit('ports')
        return self.ports_result

    def preview_prepare(self):
        self.hit('storage')
        return self.storage


class FakeSocket:
    def __init__(self, family, events, *, bind_error=None, close_error=None):
        self.family, self.events = family, events
        self.bind_error, self.close_error = bind_error, close_error
        self.options, self.addresses, self.close_calls = [], [], 0
        self.forbidden_calls = []

    def setsockopt(self, level, option, value):
        self.options.append((level,option,value))

    def bind(self, address):
        self.events.append(('bind',self.family))
        self.addresses.append(address)
        if self.bind_error is not None:
            raise self.bind_error

    def close(self):
        self.close_calls += 1
        self.events.append(('close',self.family))
        if self.close_error is not None:
            raise self.close_error

    def connect(self, *args):
        self.forbidden_calls.append('connect')
        raise AssertionError('connect forbidden')

    def connect_ex(self, *args):
        self.forbidden_calls.append('connect_ex')
        raise AssertionError('connect forbidden')

    def listen(self, *args):
        self.forbidden_calls.append('listen')
        raise AssertionError('listen forbidden')

    def send(self, *args):
        self.forbidden_calls.append('send')
        raise AssertionError('send forbidden')

    def sendall(self, *args):
        self.forbidden_calls.append('sendall')
        raise AssertionError('send forbidden')


class RecordRefusalReadinessTests(unittest.TestCase):
    def setUp(self):
        FORMATTED.clear()

    def finite(self, api, report):
        self.assertEqual(set(report), {'version','scope','ready','execution_authorized','feature_acceptance',
            'inputs_stable','phase','reason','checks','bindings','sequential_observations','observed_unix_ns','elapsed_ms'})
        self.assertIs(type(report['version']),int)
        self.assertEqual(report['version'],1)
        self.assertIs(type(report['ready']),bool)
        self.assertIs(type(report['inputs_stable']),bool)
        self.assertEqual(report['scope'],'sdk18-record-refusal-readiness-v1')
        self.assertIs(report['execution_authorized'],False)
        self.assertIs(report['feature_acceptance'],False)
        self.assertIs(report['sequential_observations'],True)
        self.assertEqual(set(report['checks']),{'resources','commit','ports','storage'})
        for check in report['checks'].values():
            self.assertEqual(set(check),{'passed','reason','facts'})
            self.assertIs(type(check['passed']),bool)
            self.assertIs(type(check['reason']),str)
        for key in ('observed_unix_ns','elapsed_ms'):
            self.assertIs(type(report[key]),int)
            self.assertGreaterEqual(report[key],0)
            self.assertLessEqual(report[key],2**64-1)
        self.assertNotIn(PRIVATE,json.dumps(report,allow_nan=False))
        self.assertEqual(FORMATTED,[])
        for call in api.forbidden.values():
            self.assertEqual(call.call_count,0)

    def test_positive_is_detached_closed_and_accepts_distinct_sequential_commit_readings(self):
        api = Observations(); before = copy.deepcopy((api.plan,api.stamp,api.resources,api.commit,api.commit_facts,api.storage))
        report = subject._probe(api); self.finite(api,report)
        self.assertIs(report['ready'],True)
        self.assertIs(report['inputs_stable'],True)
        self.assertEqual((report['phase'],report['reason']),('completed','ready'))
        self.assertEqual(api.events,EVENTS)
        self.assertTrue(all(v['passed'] and v['reason']=='ok' for v in report['checks'].values()))
        self.assertEqual(report['checks']['resources']['facts'],api.resources)
        self.assertEqual(report['checks']['commit']['facts'],api.commit_facts)
        self.assertNotEqual(report['checks']['resources']['facts']['commit_capacity'],report['checks']['commit']['facts'])
        self.assertEqual(report['checks']['ports']['facts'],{'guest_ports':[5592,5593],'private_adb_port':15937})
        self.assertEqual(set(report['checks']['storage']['facts']),{'active_count','max_guests','budget_bytes','charged_bytes',
                         'projected_bytes','reservation_bytes','would_fit','admission_granted'})
        self.assertEqual(report['bindings'],api.stamp)
        report['bindings']['ledger']['sha256'] = '0'*64
        report['checks']['resources']['facts']['free_bytes']['D:'] = 0
        report['checks']['commit']['facts']['reserve_bytes'] = 0
        report['checks']['storage']['facts']['active_count'] = 0
        self.assertEqual((api.plan,api.stamp,api.resources,api.commit,api.commit_facts,api.storage),before)

    def test_ordinary_refusals_and_storage_blocking_still_finish_other_checks_and_reverify(self):
        for variant in ('resource','several','storage-blocked'):
            api = Observations()
            if variant != 'storage-blocked': api.errors['resources'] = EnvironmentRefused('host_capacity')
            if variant == 'several':
                api.commit = snapshot(74)
                api.commit_facts = extended(api.commit)
                api.errors.update({'commit.check':HostCommitRefused('commit_capacity'),
                    'ports':subject.ReadinessRefused('ports_unavailable'),'storage':StorageRefused('registry_locked')})
            if variant == 'storage-blocked':
                api.storage.update(active_count=2,root_limit_exceeded=True,would_fit=False)
            with self.subTest(variant=variant):
                report = subject._probe(api); self.finite(api,report)
                self.assertIs(report['ready'],False)
                self.assertIs(report['inputs_stable'],True)
                self.assertEqual(report['phase'],'completed')
                self.assertEqual(api.events,EVENTS)
                if variant == 'storage-blocked':
                    self.assertIs(report['checks']['storage']['passed'],False)
                    self.assertIs(report['checks']['storage']['facts']['admission_granted'],False)
                else:
                    self.assertEqual(report['checks']['resources']['reason'],'host_capacity')
                    self.assertIsNone(report['checks']['resources']['facts'])
                if variant == 'several':
                    self.assertEqual([report['checks'][k]['reason'] for k in ('commit','ports','storage')],
                                     ['commit_capacity','ports_unavailable','registry_locked'])
                    self.assertIs(report['checks']['commit']['passed'],False)
                    self.assertEqual(report['checks']['commit']['facts'],extended(api.commit))
                    self.assertLess(report['checks']['commit']['facts']['available_commit_bytes'],10*GIB)

    def test_initial_verification_failure_or_malformed_stamp_never_observes_resources(self):
        for variant in ('exception','extra','foreign-ledger','wrong-head','boolean-size','wrong-handoff'):
            api = Observations()
            if variant == 'exception': api.errors['verify.before'] = PrivateError(PRIVATE)
            elif variant == 'extra': api.stamp['private'] = PRIVATE
            elif variant == 'foreign-ledger': api.stamp['ledger']['path'] = str(PureWindowsPath('D:/Other/ledger.json'))
            elif variant == 'wrong-head': api.stamp['profile_head'] = 'c89b9e4f73a5481a1ba5afd9808821e023d1cd0c'
            elif variant == 'boolean-size': api.stamp['ledger']['bytes'] = True
            else: api.stamp['handoff']['sha256'] = '0'*64
            with self.subTest(variant=variant):
                report = subject._probe(api); self.finite(api,report)
                self.assertIs(report['ready'],False)
                self.assertEqual((report['phase'],report['reason']),('verification_failed','verification_failed'))
                self.assertEqual(api.events,['verify.before'])
                self.assertIsNone(report['bindings'])
                self.assertTrue(all(v==dict(passed=False,reason='not_observed',facts=None) for v in report['checks'].values()))
        attempted = Mock(side_effect=AssertionError('CLI observation before argument refusal'))
        with patch.object(subject,'_api',attempted), patch.object(subject,'_probe',attempted), \
             patch.object(subject,'_physical',attempted):
            for argv in ([], ['inspect','--factory','caller'], ['--root','D:/Foreign'], ['inspect','--profile','other']):
                with self.subTest(argv=argv): self.assertEqual(subject.main(argv),2)
        self.assertEqual(attempted.call_count,0)

    def test_late_stamp_or_plan_change_and_reverification_exception_cannot_qualify(self):
        for variant in ('ledger','plan','ordinary-exception','own-exception'):
            api = Observations()
            if variant == 'ledger':
                api.after_stamp = copy.deepcopy(api.stamp); api.after_stamp['ledger']['sha256'] = 'd'*64
            elif variant == 'plan':
                api.after_plan = copy.deepcopy(api.plan); api.after_plan['opaque_plan_note'] = 'different-valid-plan-data'
            else:
                api.errors['verify.after'] = PrivateError(PRIVATE) if variant == 'ordinary-exception' else subject.ReadinessRefused('input_invalid')
            with self.subTest(variant=variant):
                report = subject._probe(api); self.finite(api,report)
                self.assertEqual(api.events,EVENTS)
                self.assertIs(report['ready'],False)
                self.assertIs(report['inputs_stable'],False)
                self.assertEqual(report['reason'],'inputs_changed' if variant in ('ledger','plan') else 'revalidation_failed')

    def test_keyboard_interrupt_stops_at_each_boundary_without_later_observation(self):
        for index,event in enumerate(EVENTS):
            api = Observations(); api.errors[event] = KeyboardInterrupt(PRIVATE)
            with self.subTest(event=event):
                report = subject._probe(api); self.finite(api,report)
                self.assertEqual(api.events,EVENTS[:index+1])
                self.assertEqual((report['phase'],report['reason']),('cancelled','cancelled'))
                self.assertIs(report['ready'],False)
                if event != 'verify.after': self.assertNotIn('verify.after',api.events)
                remaining = {'resources':'resources','commit.snapshot':'commit','commit.check':'commit','ports':'ports','storage':'storage'}
                for later in EVENTS[index+1:]:
                    key = remaining.get(later)
                    if key is not None and later != 'commit.check':
                        self.assertEqual(report['checks'][key],dict(passed=False,reason='not_observed',facts=None))

    def test_malformed_numeric_facts_private_fields_and_error_spoofs_never_become_ready(self):
        for variant in ('boolean-memory','negative-free','overflow','resource-extra','commit-extra',
                        'commit-boolean','storage-extra','storage-admission','storage-flags','ports-false'):
            api = Observations(); check,reason = 'resources','resources_invalid'
            if variant == 'boolean-memory': api.resources['available_memory'] = True
            elif variant == 'negative-free': api.resources['free_bytes']['D:'] = -1
            elif variant == 'overflow': api.resources['available_memory'] = 2**200
            elif variant == 'resource-extra': api.resources['private'] = PRIVATE
            elif variant == 'commit-extra': api.commit_facts['private'] = PRIVATE; check,reason = 'commit','commit_invalid'
            elif variant == 'commit-boolean': api.commit_facts['reserve_bytes'] = True; check,reason = 'commit','commit_invalid'
            elif variant == 'storage-extra': api.storage['entries'] = [PRIVATE]; check,reason = 'storage','storage_invalid'
            elif variant == 'storage-admission': api.storage['admission_granted'] = True; check,reason = 'storage','storage_invalid'
            elif variant == 'storage-flags': api.storage['byte_limit_exceeded'] = True; check,reason = 'storage','storage_invalid'
            else: api.ports_result = False; check,reason = 'ports','ports_invalid'
            with self.subTest(variant=variant):
                report = subject._probe(api); self.finite(api,report)
                self.assertIs(report['ready'],False)
                self.assertEqual(report['checks'][check]['reason'],reason)
                self.assertIsNone(report['checks'][check]['facts'])
                self.assertEqual(api.verifications,2)
        errors = [EnvironmentRefused(PRIVATE),EnvironmentRefused('host_capacity',PRIVATE),
                  EnvironmentRefused(ObjectPayload()),EnvironmentRefused(StringPayload('host_capacity')),
                  type('EnvironmentRefused',(Exception,),{})('host_capacity'),
                  type('EnvironmentRefused',(EnvironmentRefused,),{})('host_capacity'),PrivateError(PRIVATE)]
        for index,error in enumerate(errors):
            error.__cause__ = PrivateError(PRIVATE); error.__context__ = PrivateError(PRIVATE)
            api = Observations(); api.errors['resources'] = error
            with self.subTest(error_variant=index):
                report = subject._probe(api); self.finite(api,report)
                self.assertIs(report['ready'],False)
                self.assertEqual(report['checks']['resources']['reason'],'observation_failed')

    def test_ports_check_guest_guard_first_and_only_exclusive_loopback_binds_then_close(self):
        events,opened = [],[]
        env = SimpleNamespace(ports_free=Mock(side_effect=lambda: events.append('guest-ports')))
        def factory(family,kind):
            self.assertEqual(kind,subject.socket.SOCK_STREAM)
            self.assertIn(family,(subject.socket.AF_INET,subject.socket.AF_INET6))
            s = FakeSocket(family,events); opened.append(s); events.append(('create',family)); return s
        with patch.object(subject.socket,'socket',side_effect=factory), \
             patch.object(subject.socket,'SO_EXCLUSIVEADDRUSE',31337,create=True):
            self.assertIsNone(subject._ports(env))
        self.assertEqual(events[0],'guest-ports')
        self.assertEqual(env.ports_free.call_count,1)
        self.assertEqual([s.family for s in opened],[subject.socket.AF_INET,subject.socket.AF_INET6])
        self.assertEqual([s.close_calls for s in opened],[1,1])
        self.assertTrue(all(s.forbidden_calls==[] for s in opened))
        for s,address in zip(opened,('127.0.0.1','::1')):
            self.assertEqual(s.addresses,[(address,15937)])
            self.assertIn((subject.socket.SOL_SOCKET,31337,1),s.options)
        self.assertIn((subject.socket.IPPROTO_IPV6,subject.socket.IPV6_V6ONLY,1),opened[1].options)
        self.assertEqual([row[0] for row in events if isinstance(row,tuple)],['create','bind','create','bind','close','close'])
        self.assertEqual(FORMATTED,[])

    def test_ports_failures_attempt_all_acquired_closes_before_refusal_or_cancellation(self):
        for variant in ('guest','second-create','second-bind','ordinary-close','interrupt-bind','interrupt-close','exit-close'):
            events,opened = [],[]
            env = SimpleNamespace(ports_free=Mock(side_effect=EnvironmentRefused('ports_unavailable') if variant=='guest' else None))
            def factory(family,kind):
                if variant=='second-create' and opened: raise OSError(PRIVATE)
                s = FakeSocket(family,events,
                    bind_error=(KeyboardInterrupt(PRIVATE) if variant=='interrupt-bind' else OSError(PRIVATE))
                        if family==subject.socket.AF_INET6 and variant in ('second-bind','interrupt-bind','interrupt-close') else None,
                    close_error=(KeyboardInterrupt(PRIVATE) if variant=='interrupt-close' else SystemExit(PRIVATE)
                        if variant=='exit-close' else RuntimeError(PRIVATE))
                        if not opened and variant in ('ordinary-close','interrupt-close','exit-close') else None)
                opened.append(s); return s
            with self.subTest(variant=variant), patch.object(subject.socket,'socket',side_effect=factory) as create, \
                 patch.object(subject.socket,'SO_EXCLUSIVEADDRUSE',31337,create=True):
                if variant=='guest':
                    with self.assertRaises(EnvironmentRefused): subject._ports(env)
                elif variant.startswith('interrupt'):
                    with self.assertRaises(KeyboardInterrupt): subject._ports(env)
                elif variant=='exit-close':
                    with self.assertRaises(SystemExit): subject._ports(env)
                else:
                    with self.assertRaises(subject.ReadinessRefused) as caught: subject._ports(env)
                    self.assertEqual(caught.exception.args,('ports_unavailable',))
                self.assertEqual(env.ports_free.call_count,1)
                self.assertEqual([s.close_calls for s in opened],[1]*len(opened))
                self.assertEqual(len(opened),0 if variant=='guest' else 1 if variant=='second-create' else 2)
                self.assertEqual(create.call_count,0 if variant=='guest' else 2)
                self.assertTrue(all(s.forbidden_calls==[] for s in opened))
                self.assertEqual(FORMATTED,[])
