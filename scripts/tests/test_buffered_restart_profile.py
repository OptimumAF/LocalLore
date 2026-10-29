"""Fixed buffered-run metadata, never live authority or source-byte freshness."""
import copy
from contextlib import ExitStack
import os
from pathlib import Path, PureWindowsPath
import socket
import subprocess
import unittest
from unittest.mock import patch

from benchmarks import owned_restart_contract as restart
from benchmarks import owned_target_contract as original
from scripts.tests import test_owned_restart_contract as fixtures

NEW=PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-v1/avd-v1')
SPENT=(PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-29-restart-after-metadata-v1/avd-v1'),
       PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-29-author-restart-controller-v1/avd-v1'))


def admission(root):
    value=fixtures.admission();value['guest']['root']=str(root);return value


class BufferedRestartProfileTests(unittest.TestCase):
    def no_effects(self):
        stack=ExitStack()
        for target,name in ((Path,'open'),(Path,'stat'),(Path,'lstat'),(Path,'mkdir'),
                            (os,'open'),(os,'listdir'),(os,'scandir'),
                            (socket,'socket'),(subprocess,'Popen')):
            stack.enter_context(patch.object(target,name,side_effect=AssertionError('pure metadata attempted an external operation')))
        return stack

    def test_one_code_fixed_buffered_root_replaces_both_spent_names(self):
        self.assertEqual(restart.GUEST_ROOT,NEW)
        self.assertEqual(restart._API.profile.GUEST_ROOT,NEW)
        self.assertNotIn(restart.GUEST_ROOT,SPENT)

    def test_each_spent_root_refuses_without_observing_or_repairing_it(self):
        for root in SPENT:
            value=admission(root);before=copy.deepcopy(value)
            with self.subTest(root=root.name),self.no_effects():
                with self.assertRaises(restart.TargetRefused):restart.validate_admission(value)
            self.assertEqual(value,before)

    def test_new_root_synthetic_metadata_is_accepted_and_deep_copied(self):
        value=admission(NEW);before=copy.deepcopy(value)
        with self.no_effects():
            try:accepted=restart.validate_admission(value)
            except restart.TargetRefused as error:self.fail('new fixed root metadata was refused: '+str(error))
        self.assertEqual(accepted,before);self.assertIsNot(accepted,value)
        accepted['guest']['root']='D:/Synthetic/caller-mutated-root'
        accepted['sources'][0]['sha256']='f'*64
        self.assertEqual(value,before)
        # Synthetic pins establish shape and internal coherence only. Actual
        # source bytes, storage admission and human grants remain separate gates.

    def test_json_cannot_select_a_root_implementation_or_another_registry(self):
        for field in ('guest_root','profile','owner_module','contract_module','registry'):
            value=admission(NEW);value[field]=str(SPENT[0])
            with self.subTest(field=field),self.no_effects(),self.assertRaises(restart.TargetRefused):
                restart.validate_admission(value)
        value=admission(NEW.parent/'caller-selected')
        with self.no_effects(),self.assertRaises(restart.TargetRefused):restart.validate_admission(value)

    def test_wire_rosters_storage_source_and_profile_limits_do_not_change(self):
        value=admission(restart.GUEST_ROOT)
        self.assertEqual((restart.PROTOCOL,restart.SDK_PROTOCOL,restart.CLIENT_VERSION),
            ('owned-emulator-restart-target-v1','sdk-owned-restart-v1',5))
        self.assertEqual(restart.CLAIM_KINDS,('import','author','restart'))
        self.assertEqual((len(original.SOURCE_NAMES),len(restart.SOURCE_NAMES)),(15,24))
        self.assertIn('receipt_avd_storage.py',original.SOURCE_NAMES)
        self.assertTrue(original.SOURCE_NAMES<=restart.SOURCE_NAMES)
        self.assertEqual({PureWindowsPath(pin['path']).name for pin in value['sources']},restart.SOURCE_NAMES)
        self.assertEqual({key:value['guest'][key]for key in ('memory_mib','cores','max_seconds','api','abi')},
            dict(memory_mib=8192,cores=4,max_seconds=1800,api=35,abi='x86_64'))
        changed=copy.deepcopy(value);changed['server']['sources'][0]['sha256']='f'*64
        with self.no_effects(),self.assertRaisesRegex(restart.TargetRefused,'source'):
            restart.validate_admission(changed)

    def test_fixed_module_execution_has_no_path_socket_process_or_ledger_effect(self):
        code=compile(Path(restart.__file__).read_bytes(),restart.__file__,'exec')
        namespace={'__name__':'benchmarks._buffered_restart_import_fixture','__package__':'benchmarks'}
        with self.no_effects():exec(code,namespace)
        self.assertEqual(namespace['SOURCE_NAMES'],restart.SOURCE_NAMES)
        self.assertEqual(namespace['SDK_PROTOCOL'],'sdk-owned-restart-v1')


if __name__=='__main__':unittest.main()
