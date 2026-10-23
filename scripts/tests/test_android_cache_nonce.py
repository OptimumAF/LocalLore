"""Explicit private SDK session binding without changing the frozen workload.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import shlex
import unittest
from unittest.mock import Mock, patch

from test_android_cache_control import control, FakeDevice, response, sample, model, decoded, UUID, INSTALLED


class CacheNonceTests(unittest.TestCase):
    def test_traced_artifact_binds_package_and_original_profile_without_replacing_old_pins(self):
        pin = control.TRACED_APK_SHA256
        device = FakeDevice(lambda _, event, __: response((pin+'  '+INSTALLED+'\n').encode()) if event == 'package_hash' else None)
        with patch.object(control.play, 'make_profile', wraps=control.play.make_profile) as profile:
            with patch.object(control.cache_result, 'parse_result', return_value=decoded()):
                result = control.run_control(device, pin, 'gift', UUID,
                    Mock(side_effect=[sample(), sample()]), lambda: model(), lambda _: None, session_nonce='f'*32)
        self.assertTrue(result['check_passed']); profile.assert_called_once_with(pin)
        self.assertEqual(control.SUPPORTED_APKS, {control.APK_SHA256, control.GUARDED_APK_SHA256, pin})

    def test_explicit_nonce_is_dispatched_once_and_never_exported(self):
        nonce = 'e' * 32; device = FakeDevice()
        with patch.object(control.uuid, 'uuid4', side_effect=AssertionError('must not replace nonce')):
            with patch.object(control.cache_result, 'parse_result', return_value=decoded()):
                result = control.run_control(device, control.APK_SHA256, 'gift', UUID,
                    Mock(side_effect=[sample(), sample()]), lambda: model(), lambda _: None, session_nonce=nonce)
        self.assertTrue(result['check_passed']); self.assertEqual(device.launches, 1)
        words = shlex.split(next(args[1] for args, _ in device.calls if shlex.split(args[1])[:2] == ['am', 'instrument']))
        self.assertEqual(words[words.index('session') + 1], nonce)
        self.assertNotIn(nonce, json.dumps(result))

    def test_invalid_nonce_refused_before_measure_model_or_device(self):
        for nonce in ('', 'E'*32, 'a'*31, 'a'*33, True, 'a'*31+';', b'a'*32):
            measure, identity = Mock(), Mock(); device = FakeDevice()
            result = control.run_control(device, control.APK_SHA256, 'gift', UUID, measure, identity, session_nonce=nonce)
            self.assertEqual(result['status'], 'input_refused'); self.assertEqual(device.calls, [])
            measure.assert_not_called(); identity.assert_not_called()


if __name__ == '__main__':
    unittest.main()
