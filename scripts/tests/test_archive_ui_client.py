"""SDK6 uses actual fixed clients/claims/readers with synthetic byte-backed wire IO."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_client_v6 as client
from benchmarks import android_process_verification_v6 as reader
from benchmarks import owned_ui_contract as contract
from benchmarks import owned_ui_owner as owner
from scripts.tests import test_archive_ui_fixtures as f
from scripts.tests import test_android_process_client_v4 as framing


@unittest.skipUnless(os.name == 'nt', 'Windows owned-target wire fixtures')
class ArchiveUiClientTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-archive-ui-client-'))
        self.a = f.admission()
        self.a['root'] = str(self.base/'lease')
        self.a['server']['root'] = str(self.base/'lease/server')
        for role in ('product_apk','test_apk'):
            path = self.base/(role+'.apk')
            path.write_bytes(b'PK\0\x1a\xff\r\n-SYNTHETIC-'+role.encode())
            self.a['artifacts'][role] = wire.environment.binding(path)
        self.ap = self.base/'admission-v1.json'
        wire.environment.create_json(self.ap,self.a)
        self.admission = wire.environment.binding(self.ap)
        self.d = f.running(self.a); self.d['admission'] = self.admission
        self.rp = self.base/'lease/running-v1.json'; self.rp.parent.mkdir()
        wire.environment.create_json(self.rp,self.d)
        self.running = wire.environment.binding(self.rp)
        # Bypass constructor/native observation only. Fixed properties, real
        # create-only claim_once and all generic SDK proof/client replay remain real.
        self.live = object.__new__(owner.LiveOwnedUiTarget)
        self.live._admission = copy.deepcopy(self.a); self.live._descriptor = copy.deepcopy(self.d)
        self.live._admission_binding = copy.deepcopy(self.admission)
        self.live._running_binding = copy.deepcopy(self.running)
        self.live._caller = copy.deepcopy(self.d['worker'])
        self.live.guard = Mock(); self.live.fast_guard = Mock()
        self.live.prove = Mock(side_effect=self.prove)
        self.clock = 100.0; self.index = 0; self.fail_proof = set(); self.proof_cost = {}
        self.enter(patch.object(wire.time,'monotonic',side_effect=lambda:self.clock))
        self.enter(patch.object(wire.time,'time',return_value=1800000010.0))
        self.enter(patch.object(wire.threading,'Thread',framing.InlineSender))
        self.sock = framing.FakeSocket(self.response())
        self.socket_factory = self.enter(patch.object(wire.socket,'socket',side_effect=lambda *args:self.sock))

    def enter(self, context):
        value = context.__enter__(); self.addCleanup(context.__exit__,None,None,None)
        return value

    def response(self, body=b'original\0\x1a\xff\r\n'):
        return b'OKAYOKAY'+framing.packet(1,body)+framing.packet(3,b'\0')

    def capture(self, seconds=100):
        self.index += 1
        parent = self.base/('session-%02d'%self.index); parent.mkdir()
        return client.OwnedUiSdkCapture(parent/'clients',seconds,self.live)

    def prove(self, path, session, context, sock, anchor, after=False):
        self.clock += self.proof_cost.get(context['phase'],0)
        if context['phase'] in self.fail_proof:
            raise ValueError('synthetic observation refused')
        value = f.proof(session,after=after)
        value.update(context=copy.deepcopy(context),anchor=copy.deepcopy(anchor),
                     session=wire.environment.binding(Path(session['root'])/'sdk-session-v6.json'))
        queries = path.with_name(path.stem+'-queries-v1.json')
        wire.environment.create_json(queries,f.query_bundle(session))
        value['queries'] = wire.environment.binding(queries)
        wire.environment.create_json(path,value)
        return wire.environment.binding(path)

    def record(self, cap):
        return wire.environment.read_json(cap.directory/'command-0001.json')

    def assertPoisoned(self, cap):
        before = self.socket_factory.call_count
        self.assertFalse(cap.clean)
        with self.assertRaises(client.ClientRefused):
            cap.shell(['getprop','sys.boot_completed'],'no-retry')
        self.assertEqual(self.socket_factory.call_count,before)

    def test_original_binary_record_and_actual_full_proof_replay_use_only_sdk6(self):
        cap = self.capture()
        self.assertEqual(cap.shell(['getprop','sys.boot_completed'],'boot'),b'original\0\x1a\xff\r\n')
        row = self.record(cap)
        self.assertEqual(row['version'],6); self.assertEqual(row['protocol'],f.SDK_PROTOCOL)
        self.assertTrue(row['client_qualified'])
        self.assertEqual(Path(row['session']['path']).name,'sdk-session-v6.json')
        self.assertEqual(self.sock.connects,[('127.0.0.1',15937)])
        reader.verify_client_record(wire.environment.binding(cap.directory/'command-0001.json'),cap.session,self.a)
        reader.require_current_clients(cap.directory.parent,1,cap.session_binding,self.a)
        self.live.guard.assert_called(); self.live.fast_guard.assert_called()
        for name in ('_contract','_verification','_expected_lease_class'):
            with self.assertRaises(AttributeError): setattr(cap,name,object())
        self.assertIs(cap._contract,contract); self.assertIs(cap._verification,reader)

    def test_exact_owner_types_prevent_legacy_or_subclass_profile_substitution(self):
        from benchmarks.owned_target_owner import LiveOwnedTarget
        from benchmarks.owned_restart_owner import LiveOwnedRestartTarget
        class Derived(owner.LiveOwnedUiTarget): pass
        for kind in (LiveOwnedTarget,LiveOwnedRestartTarget,Derived):
            wrong = object.__new__(kind); wrong.guard = Mock()
            parent = self.base/kind.__name__; parent.mkdir()
            with self.assertRaises(client.ClientRefused):
                client.OwnedUiSdkCapture(parent/'clients',30,wrong)
            wrong.guard.assert_not_called(); self.assertEqual(list(parent.iterdir()),[])
        with self.assertRaises(wire.ClientRefused):
            wire.OwnedTargetSdkCapture(self.base/'legacy-clients',30,self.live)
        self.socket_factory.assert_not_called()

    def test_all_ten_real_create_only_claims_are_admission_wide_and_cannot_retry(self):
        for triple in f.INSTRUMENTATIONS:
            self.sock = framing.FakeSocket(self.response())
            cap = self.capture(); cap.shell(f.instrument(triple),triple[0])
            path = self.base/'lease/claims-v1'/(triple[0]+'-v1.json')
            claim = wire.environment.read_json(path)
            self.assertEqual(claim['protocol'],f.PROTOCOL)
            self.assertEqual(claim['caller'],self.d['worker'])
            self.assertEqual(claim['operation_sha256'],contract.operation_digest({'argv':f.instrument(triple),'stdin':None}))
            self.assertNotIn('prerequisite',claim)
        self.assertEqual(len(list((self.base/'lease/claims-v1').glob('*.json'))),10)
        self.sock = framing.FakeSocket(self.response()); again = self.capture()
        with self.assertRaises(client.ClientRefused): again.shell(f.instrument(f.INSTRUMENTATIONS[0]),'repeat')
        self.assertEqual(again.count,0); self.assertEqual(self.sock.sent,b'')
        self.assertPoisoned(again)

    def test_forbidden_model_shell_package_and_selector_operations_never_open_socket(self):
        for command in (['run-as',f.APP,'--user','0','ls','files'],['sh','-c','id'],
                        ['df','-k','/data'],['pidof','org.locallore.app'],
                        ['am','instrument','-w','-r','-e','class','foreign.Test#test',f.TEST+'/androidx.test.runner.AndroidJUnitRunner']):
            with self.subTest(command=command):
                cap = self.capture()
                with self.assertRaises(client.ClientRefused): cap.shell(command,'forbidden')
                self.assertEqual(cap.count,0); self.assertPoisoned(cap)
        self.socket_factory.assert_not_called()
        self.assertFalse((self.base/'lease/claims-v1').exists())

    def test_only_bound_apk_bytes_stream_and_are_recorded_without_model_material(self):
        cap = self.capture()
        source = self.a['artifacts']['product_apk']
        command = ['dd','of=/data/local/tmp/locallore-product-v1.apk','bs=65536']
        cap.stream(command,source,'stage-product',seconds=15)
        row = self.record(cap)
        self.assertTrue(row['stdin_complete']); self.assertTrue(row['client_qualified'])
        self.assertEqual(row['stdin_bytes'],source['bytes'])
        self.assertEqual(row['stdin_sha256'],source['sha256'])
        self.assertIn(framing.packet(0,Path(source['path']).read_bytes()),self.sock.sent)
        self.sock = framing.FakeSocket(self.response()); bad = self.capture()
        with self.assertRaises(client.ClientRefused):
            bad.stream(command,self.a['artifacts']['test_apk'],'wrong-role',seconds=15)
        self.assertEqual(bad.count,0); self.assertEqual(self.sock.sent,b'')
        self.assertPoisoned(bad)

    def test_failed_before_proof_closes_socket_and_postproof_keeps_raw_but_not_qualification(self):
        self.fail_proof = {'before'}; cap = self.capture()
        with self.assertRaises(client.ClientRefused): cap.shell(['getprop','sys.boot_completed'],'boot')
        self.assertTrue(self.sock.closed); self.assertEqual(cap.count,0)
        self.assertEqual(self.sock.sent,b''); self.assertPoisoned(cap)
        self.fail_proof = {'after'}; self.sock = framing.FakeSocket(self.response()); cap = self.capture()
        with self.assertRaises(client.ClientRefused): cap.shell(['getprop','sys.boot_completed'],'boot')
        row = self.record(cap)
        self.assertEqual(row['status'],'completed'); self.assertEqual(row['returncode'],0)
        self.assertFalse(row['client_qualified']); self.assertIsNone(row['server_after'])
        self.assertEqual(Path(row['stdout']['path']).read_bytes(),b'original\0\x1a\xff\r\n')
        self.assertPoisoned(cap)

    def test_before_proof_cost_cannot_extend_the_original_full_deadline(self):
        cap = self.capture(seconds=20); self.proof_cost = {'before':6}
        with self.assertRaises(client.ClientRefused):
            cap.shell(['getprop','sys.boot_completed'],'boot',seconds=15,full_budget=True)
        self.assertEqual(cap.count,0); self.assertEqual(self.sock.sent,b'')
        self.assertPoisoned(cap)

    def test_cancelled_partial_raw_and_unknown_socket_close_never_qualify_or_retry(self):
        self.sock = framing.FakeSocket(b'OKAYOKAY'+framing.packet(1,b'partial\0\x1a'))
        self.sock.eof_error = KeyboardInterrupt()
        cap = self.capture()
        with self.assertRaises(client.ClientRefused): cap.shell(['getprop','sys.boot_completed'],'boot')
        row = self.record(cap)
        self.assertEqual(row['status'],'cancelled')
        self.assertEqual(Path(row['stdout']['path']).read_bytes(),b'partial\0\x1a')
        self.assertPoisoned(cap)
        self.sock = framing.FakeSocket(self.response(),close_error=True); cap = self.capture()
        with self.assertRaises(client.ClientRefused): cap.shell(['getprop','sys.boot_completed'],'boot')
        row = self.record(cap)
        self.assertFalse(row['socket_closed']); self.assertFalse(row['client_qualified'])
        self.assertPoisoned(cap)
