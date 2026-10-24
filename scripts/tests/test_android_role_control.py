"""Real strict decoder through a fake transport; no SDK, ADB or model invocation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import unittest
from unittest.mock import Mock, patch

from test_android_cache_control import control, FakeDevice, response, model, sample, INSTALLED, UUID
from test_android_cache_result import raw
from test_android_role_observation import packet
import test_android_sdk_phase_control as phase_fixture

PIN = '9' * 64


class RoleControlTests(unittest.TestCase):
    def test_final_qualified_role_pin_dispatches_reader_without_replacing_the_old_readback_pin(self):
        reader = phase_fixture.reader; pin = control.ROLE_OBSERVATION_APK_SHA256
        self.assertIn(pin, control.SUPPORTED_APKS); self.assertNotEqual(pin, reader.READBACK_APK_SHA256)
        self.assertEqual(reader.READBACK_APK_SHA256, control.TRACED_APK_SHA256)
        with patch.object(phase_fixture, 'PIN', pin):
            result = reader.read_phase(phase_fixture.Device(), pin, phase_fixture.NONCE, Mock())
        self.assertTrue(result['journal_verified']); self.assertTrue(result['process_absent'])

    def invoke(self, value):
        data = raw(value)
        def override(_, event, __):
            if event == 'package_hash':
                return response((PIN+'  '+INSTALLED+'\n').encode())
            if event == 'play':
                return response(data)
            return None
        device = FakeDevice(override); sink = Mock()
        with patch.object(control, 'ROLE_OBSERVATION_APK_SHA256', PIN), patch.object(control, 'SUPPORTED_APKS', control.SUPPORTED_APKS | {PIN}):
            result = control.run_control(device, PIN, 'gift', UUID,
                Mock(side_effect=[sample(), sample()]), lambda: model(), sink, session_nonce='8'*32)
        sink.assert_called_once_with(data)
        return result, device

    def test_new_bound_artifact_keeps_valid_observations_and_primary_receipt(self):
        result, device = self.invoke(packet())
        self.assertTrue(result['check_passed']); self.assertTrue(result['result']['first_output_observed'])
        self.assertEqual((device.launches, device.stops), (1, 3))

    def test_committed_looking_raw_with_malformed_diagnostics_is_unknown_not_failed_gameplay(self):
        value = packet(); value['play_result']['turns'][0]['generations'][0]['terminal_observation']['private'] = 'CANARY'
        result, device = self.invoke(value)
        self.assertEqual(result['status'], 'invalid_terminal'); self.assertIsNone(result['result'])
        self.assertTrue(result['raw_protocol_retained']); self.assertTrue(result['process_absent'])
        self.assertTrue(result['clients_cleaned']); self.assertFalse(result['check_passed'])
        self.assertNotIn('CANARY', json.dumps(result)); self.assertEqual(device.launches, 1)

    def test_late_storage_error_cannot_erase_new_format_accepted_receipt(self):
        value = packet(); value.update(status='error', error='volume_changed'); del value['post_sample']
        result, _ = self.invoke(value)
        self.assertEqual(result['result']['outcome'], 'committed')
        self.assertEqual(result['worker_error'], 'volume_changed'); self.assertFalse(result['check_passed'])


if __name__ == '__main__':
    unittest.main()
