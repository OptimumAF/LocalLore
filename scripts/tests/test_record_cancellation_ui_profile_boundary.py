"""Actual typed input ordering and independent SDK18 origin/command boundaries.

External file/native observations remain explicit synthetic ports. Retargeted
owner roots are real isolated D: temporary parents, never another project.
"""
import copy
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import record_cancellation_ui_controller as controller
from benchmarks import record_cancellation_ui_profile_build as build
from benchmarks import owned_record_cancellation_ui_contract as c
from scripts.tests import test_record_cancellation_ui_profile_fixtures as f


class RecordCancellationUiBoundaryTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'physical D: input-order fixture requires Windows')
    def test_actual_typed_preflight_rejects_before_output_for_retargeted_d_parent(self):
        for stage in ('running', 'sources', 'build'):
            with self.subTest(stage=stage):
                root = Path(tempfile.mkdtemp(prefix='sdk18-preflight-order-'))
                self.assertEqual(root.drive.upper(), 'D:')
                admission = f.admission()
                admission['root'] = str(root)
                admission['server']['root'] = str(root / 'server')
                self.assertEqual(c.validate_admission(admission), admission)
                admission_pin = f.legacy.pin('D:/Synthetic/admission-v1.json')
                running_pin = f.legacy.pin('D:/Synthetic/running-v1.json')
                running = f.running(admission)
                running['admission'] = copy.deepcopy(admission_pin)
                self.assertEqual(c.validate_running(running, admission, admission_pin), running)
                if stage == 'running': running['protocol'] = 'owned-emulator-diagnostic-ui-v1'
                source_check = Mock(side_effect=c.TargetRefused('source') if stage == 'sources' else None)
                verifier = Mock(side_effect=c.TargetRefused('build'))
                def read(pin):
                    self.assertIn(pin, (admission_pin, running_pin))
                    return copy.deepcopy(admission if pin == admission_pin else running)
                with patch.object(controller, '_json', side_effect=read), \
                     patch.object(c, 'revalidate_inputs', source_check), \
                     patch.object(c, 'source_bindings', return_value=admission['sources']), \
                     patch.object(controller, 'verify_current', verifier), \
                     patch.object(controller, '_output', wraps=controller._output) as output, \
                     patch.object(controller, 'LiveOwnedRecordCancellationUiTarget') as live, \
                     patch.object(controller, 'OwnedRecordCancellationUiSdkCapture') as capture:
                    refused = None
                    try: controller.run(admission_pin, running_pin)
                    except c.TargetRefused as error: refused = error
                self.assertEqual(output.call_count, 0)
                self.assertEqual(live.call_count, 0)
                self.assertEqual(capture.call_count, 0)
                self.assertEqual(source_check.call_count, 0 if stage == 'running' else 1)
                self.assertEqual(verifier.call_count, 1 if stage == 'build' else 0)
                self.assertIsInstance(refused, c.TargetRefused)
                self.assertEqual(list(root.iterdir()), [])

    @unittest.skipUnless(os.name == 'nt', 'physical D: checker guard requires Windows')
    def test_cached_bound_shared_reader_alias_cannot_borrow_the_correct_sysmodule(self):
        from benchmarks import archive_ui_build as reader
        fake = SimpleNamespace(__file__='D:/Synthetic/foreign-reader/diagnostic_ui_build.py')
        with patch.object(reader, '_bound') as checked, patch.object(build.build, 'shared', fake):
            refused = None
            try: build.revalidate_checker()
            except c.TargetRefused as error: refused = error
        self.assertIsInstance(refused, c.TargetRefused)
        self.assertEqual(str(refused), 'source')
        self.assertEqual(checked.call_count, 2)
        self.assertTrue(all('foreign-reader' not in call.args[0]['path'] for call in checked.call_args_list))

    def test_old_valid_user_zero_force_stop_command_is_not_sdk18_authority(self):
        value = f.admission()
        for argv in (['am', 'force-stop', '--user', '0', 'org.locallore.app'],
                     ['am', 'force-stop', 'org.locallore.app'], ['pidof', 'org.locallore.app']):
            with self.subTest(argv=argv), self.assertRaises(c.TargetRefused):
                c.validate_operation(dict(argv=argv, stdin=None), value)
