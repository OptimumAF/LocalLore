"""Independent fixed model-free profile adversaries; no filesystem/native/device IO."""
import copy
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from benchmarks import owned_target_contract as legacy
from benchmarks import owned_ui_contract as c
from scripts.tests import test_archive_ui_fixtures as f


class ArchiveUiContractTests(unittest.TestCase):
    def refused(self, call):
        with self.assertRaises(c.TargetRefused):
            call()

    def test_fixed_profile_and_legacy_defaults_have_distinct_authority(self):
        self.assertEqual(c.PROTOCOL, f.PROTOCOL)
        self.assertEqual(c.SDK_PROTOCOL, f.SDK_PROTOCOL)
        self.assertEqual(c.PROOF_PROTOCOL, f.PROOF_PROTOCOL)
        self.assertEqual(c.CLIENT_VERSION, 6)
        self.assertEqual(c.SESSION_FILE, 'sdk-session-v6.json')
        self.assertEqual(c.APP, f.APP); self.assertEqual(c.TEST, f.TEST)
        self.assertEqual(c.GUEST_ROOT, f.GUEST_ROOT)
        self.assertEqual(set(c.ARTIFACT_KEYS), {'build','product_apk','test_apk'})
        self.assertEqual(c.SOURCE_NAMES, f.SOURCE_NAMES)
        self.assertEqual(tuple(c.INSTRUMENTATIONS), f.INSTRUMENTATIONS)
        self.assertEqual(tuple(c.CLAIM_KINDS), tuple(t[0] for t in f.INSTRUMENTATIONS))
        old = legacy._legacy_spec()
        self.assertTrue(old.MODEL_MATERIAL)
        self.assertEqual(old.APP, 'org.locallore.app.litertverify')
        self.assertEqual(old.TEST, old.APP+'.test')
        self.assertEqual(legacy.validate_admission(f.legacy.admission()), f.legacy.admission())

    def test_complete_model_free_admission_is_pure_and_returns_independent_data(self):
        value = f.admission(); original = copy.deepcopy(value)
        with patch.object(Path,'open',side_effect=AssertionError('unexpected file read')), \
             patch.object(Path,'stat',side_effect=AssertionError('unexpected file metadata')), \
             patch.object(socket,'socket',side_effect=AssertionError('unexpected socket')):
            result = c.validate_admission(value)
        self.assertEqual(result, original)
        result['artifacts']['product_apk']['bytes'] = 0
        result['sources'].clear()
        self.assertEqual(value, original)

    def test_no_legacy_retag_or_extra_model_material_can_supply_ui_authority(self):
        self.refused(lambda:c.validate_admission(f.legacy.admission()))
        self.refused(lambda:legacy.validate_admission(f.admission()))
        for role in ('model','probe','process_probe'):
            value = f.admission(); value['artifacts'][role] = f.legacy.pin('D:/Synthetic/'+role)
            with self.subTest(extra=role): self.refused(lambda:c.validate_admission(value))
        for role in ('model','probe'):
            old = f.legacy.admission(); del old['artifacts'][role]
            with self.subTest(legacy_missing=role): self.refused(lambda:legacy.validate_admission(old))
        value = f.admission(); value['protocol'] = legacy.PROTOCOL
        value['guest']['root'] = str(legacy.GUEST_ROOT)
        value['sources'] = f.legacy.admission()['sources']
        self.refused(lambda:legacy.validate_admission(value))

    def test_exact_ten_method_selectors_and_their_claim_names_are_closed(self):
        value = f.admission()
        for triple in f.INSTRUMENTATIONS:
            command = f.instrument(triple)
            self.assertEqual(c.instrumentation_kind(command), triple[0])
            self.assertEqual(c.validate_operation({'argv':command,'stdin':None}, value)['argv'], command)
            for position, replacement in ((6,triple[1]+'#unknownMethod'),
                                          (7,'org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner')):
                bad = list(command); bad[position] = replacement
                with self.subTest(kind=triple[0],position=position):
                    self.refused(lambda:c.validate_operation({'argv':bad,'stdin':None},value))
            self.refused(lambda:c.instrumentation_kind(command+['--user','0']))

    def test_package_checks_and_only_admitted_apk_streams_are_allowed(self):
        value = f.admission()
        for package in (f.APP,f.TEST):
            for command in (['cmd','package','list','packages','-U','--user','0',package],
                            ['cmd','package','path','--user','0',package],
                            ['am','force-stop','--user','0',package],['pidof',package]):
                self.assertEqual(c.validate_operation({'argv':command,'stdin':None},value)['argv'],command)
        for role, remote in (('product_apk','/data/local/tmp/locallore-product-v1.apk'),
                             ('test_apk','/data/local/tmp/locallore-test-v1.apk')):
            command = ['dd','of='+remote,'bs=65536']
            source = value['artifacts'][role]
            self.assertEqual(c.validate_operation({'argv':command,'stdin':source},value)['stdin'],source)
            for bad in (None,value['artifacts']['build'],dict(source,sha256='0'*64)):
                with self.subTest(role=role,source=bad):
                    self.refused(lambda:c.validate_operation({'argv':command,'stdin':bad},value))
            self.refused(lambda:c.validate_operation({'argv':['dd','of='+remote+'/../escape','bs=65536'],'stdin':source},value))

    def test_model_run_as_general_shell_and_non_ui_queries_refuse(self):
        value = f.admission()
        commands = [
            ['run-as',f.APP,'--user','0','ls','files'],
            ['run-as',f.APP,'--user','0','dd','of=no_backup/model.litertlm','bs=65536'],
            ['df','-k','/data'],['cat','/proc/meminfo'],['screencap','-p'],['sh','-c','id'],
            ['getprop','ro.serialno'],['getprop','sys.boot_completed;id'],
            ['am','force-stop','--user','0',legacy.APP],['pidof','other.app'],
            ['sha256sum','/data/app/../escape/base.apk'],
            ['/data/local/tmp/locallore-author-process-probe-v1','--boot'],
        ]
        for command in commands:
            with self.subTest(command=command):
                self.refused(lambda:c.validate_operation({'argv':command,'stdin':None},value))
        old = f.legacy.admission()
        self.assertEqual(legacy.validate_operation({'argv':['df','-k','/data'],'stdin':None},old)['argv'],['df','-k','/data'])

    def test_source_roster_root_and_resource_metadata_cannot_be_relaxed(self):
        for path, bad in ((('guest','root'),str(legacy.GUEST_ROOT)),(('guest','memory_mib'),4096),
                          (('guest','cores'),True),(('guest','api'),34),(('seconds',),True),
                          (('protocol',),'owned-emulator-restart-v1')):
            value = f.admission(); target = value
            for key in path[:-1]: target = target[key]
            target[path[-1]] = bad
            with self.subTest(path=path,bad=bad): self.refused(lambda:c.validate_admission(value))
        value = f.admission(); value['sources'] = value['sources'][:-1]
        self.refused(lambda:c.validate_admission(value))

    def test_session_join_refuses_other_callers_sources_and_rebound_deadlines(self):
        value = f.admission(); session = f.session(value)
        self.assertEqual(c.validate_session(session,value), session)
        for mutate in (lambda x:x.update(protocol='sdk-owned-target-v1'),
                       lambda x:x['descriptor'].update(protocol=legacy.PROTOCOL),
                       lambda x:x['caller'].update(pid=x['descriptor']['guest']['pid']),
                       lambda x:x['sources'][0].update(sha256='0'*64),
                       lambda x:x.update(seconds=True),
                       lambda x:x.update(deadline_epoch=x['deadline_epoch']+1)):
            bad = copy.deepcopy(session); mutate(bad)
            self.refused(lambda:c.validate_session(bad,value))

    def test_claims_bind_exact_kind_operation_admission_and_caller_without_prerequisite(self):
        session = f.session(); binding = session['admission']; caller = session['caller']
        for triple in f.INSTRUMENTATIONS:
            operation = {'argv':f.instrument(triple),'stdin':None}
            digest = c.operation_digest(operation)
            record = c.claim_record(binding,caller,triple[0],digest)
            self.assertEqual(c.validate_claim(record,binding,caller,triple[0],digest),record)
            self.assertNotIn('prerequisite',record)
            for mutate in (lambda x:x.update(kind='author'),lambda x:x.update(protocol=legacy.PROTOCOL),
                           lambda x:x.update(admission_sha256='0'*64),
                           lambda x:x['caller'].update(creation_filetime=x['caller']['creation_filetime']+1),
                           lambda x:x.update(operation_sha256='0'*64),lambda x:x.update(version=True)):
                bad = copy.deepcopy(record); mutate(bad)
                self.refused(lambda:c.validate_claim(bad,binding,caller,triple[0],digest))
            self.refused(lambda:c.claim_record(binding,caller,triple[0],digest,f.legacy.pin('D:/Synthetic/not-a-grant.json')))
