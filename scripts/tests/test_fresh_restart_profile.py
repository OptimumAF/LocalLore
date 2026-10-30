"""Fixed fresh-root metadata checks, not live permission or hash freshness."""
import copy
from contextlib import ExitStack
from pathlib import Path,PureWindowsPath
import socket
import subprocess
import unittest
from unittest.mock import patch

from benchmarks import owned_restart_contract as contract
from scripts.tests import test_owned_restart_contract as fixtures

OLD_ROOT=PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-29-author-restart-controller-v1/avd-v1')
NEW_ROOT=PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-29-restart-after-metadata-v1/avd-v1')


def admission(root):
    value=fixtures.admission();value['guest']['root']=str(root)
    return value


class FreshRestartProfileTests(unittest.TestCase):
    def no_effects(self):
        stack=ExitStack()
        for target,name in((Path,'open'),(Path,'stat'),(Path,'lstat'),(socket,'socket'),(subprocess,'Popen')):
            stack.enter_context(patch.object(target,name,side_effect=AssertionError('pure profile attempted IO or runtime dispatch')))
        return stack

    def test_current_profile_has_one_new_code_fixed_guest_root(self):
        self.assertEqual(contract.GUEST_ROOT,NEW_ROOT)
        self.assertEqual(contract._API.profile.GUEST_ROOT,NEW_ROOT)
        self.assertNotEqual(contract.GUEST_ROOT,OLD_ROOT)

    def test_old_used_root_is_refused_by_current_profile_before_any_runtime(self):
        value=admission(OLD_ROOT);original=copy.deepcopy(value)
        with self.no_effects(),self.assertRaises(contract.TargetRefused):contract.validate_admission(value)
        self.assertEqual(value,original)

    def test_new_root_metadata_is_accepted_and_copied_without_claiming_live_source_freshness(self):
        value=admission(NEW_ROOT);original=copy.deepcopy(value)
        with self.no_effects():accepted=contract.validate_admission(value)
        self.assertEqual(accepted,original);self.assertIsNot(accepted,value)
        accepted['guest']['root']='D:/Synthetic/caller-mutation';self.assertEqual(value,original)
        # These deliberately synthetic hash strings prove only closed metadata
        # shape/coherence. Actual source bytes and human grants have separate
        # mandatory live/closed-reader gates, never this pure predicate.

    def test_json_root_or_module_selectors_cannot_override_the_fixed_profile(self):
        for field in('guest_root','profile','contract_module','owner_module'):
            value=admission(NEW_ROOT);value[field]=str(OLD_ROOT)
            with self.subTest(field=field),self.no_effects(),self.assertRaises(contract.TargetRefused):
                contract.validate_admission(value)
        value=admission(NEW_ROOT);value['guest']['root']=str(NEW_ROOT.parent/'caller-selected-avd')
        with self.no_effects(),self.assertRaises(contract.TargetRefused):contract.validate_admission(value)

    def test_source_roster_and_protocol_remain_closed_metadata_without_a_hash_or_verdict_stub(self):
        value=admission(NEW_ROOT)
        self.assertEqual(contract.PROTOCOL,'owned-emulator-restart-target-v1')
        self.assertEqual(contract.SDK_PROTOCOL,'sdk-owned-restart-v1');self.assertEqual(contract.CLIENT_VERSION,5)
        self.assertEqual(contract.CLAIM_KINDS,('import','author','restart'))
        self.assertEqual(len(contract.SOURCE_NAMES),23)
        self.assertEqual({PureWindowsPath(pin['path']).name for pin in value['sources']},contract.SOURCE_NAMES)
        self.assertIn('owned_restart_contract.py',contract.SOURCE_NAMES)
        with self.no_effects():contract._sources(value['sources'])
        bad=copy.deepcopy(value);bad['server']['sources'][0]['sha256']='f'*64
        with self.no_effects(),self.assertRaisesRegex(contract.TargetRefused,'source'):contract.validate_admission(bad)

    def test_fresh_root_does_not_relax_guest_profile_or_owner_budget(self):
        value=admission(NEW_ROOT)
        self.assertEqual({key:value['guest'][key]for key in('memory_mib','cores','max_seconds','api','abi')},
            dict(memory_mib=8192,cores=4,max_seconds=1800,api=35,abi='x86_64'))
        for field,bad in(('memory_mib',4096),('cores',8),('max_seconds',1801),('api',34),('abi','arm64-v8a')):
            changed=copy.deepcopy(value);changed['guest'][field]=bad
            with self.subTest(field=field),self.no_effects(),self.assertRaises(contract.TargetRefused):contract.validate_admission(changed)
        for seconds in(1199,1701,True):
            changed=copy.deepcopy(value);changed['seconds']=seconds;changed['server']['seconds']=seconds
            with self.subTest(seconds=seconds),self.no_effects(),self.assertRaises(contract.TargetRefused):contract.validate_admission(changed)

    def test_fixed_contract_module_execution_has_no_filesystem_or_runtime_side_effects(self):
        # Read the pinned code before the observation. Executing its already
        # loaded dependency graph must not observe/create a guest or a model.
        code=compile(Path(contract.__file__).read_bytes(),contract.__file__,'exec')
        namespace={'__name__':'benchmarks._fresh_restart_profile_import_fixture','__package__':'benchmarks'}
        with self.no_effects():exec(code,namespace)
        self.assertIn('_API',namespace);self.assertEqual(namespace['SOURCE_NAMES'],contract.SOURCE_NAMES)


if __name__=='__main__':unittest.main()
