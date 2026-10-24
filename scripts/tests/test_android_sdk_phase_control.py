"""Ownership and retention boundaries without ADB, model access or device writes.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
from pathlib import Path
import shlex
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'benchmarks'))
import android_sdk_phase_control as reader
from test_android_cache_control import FakeDevice, response, INSTALLED
from test_android_sdk_phase_result import completed, wire

PIN = 'd' * 64
NONCE = 'c' * 32


class Device(FakeDevice):
    def __init__(self, override=None):
        super().__init__()
        self.running = False
        self.reader_override = override
        self.uid = 10231

    def raw(self, args, **kwargs):
        words = shlex.split(args[1])
        custom = None
        if words[:3] == ['run-as', reader.cache.PACKAGE, 'id']:
            event = 'uid'; custom = response(str(self.uid).encode() + b'\n')
        elif words[0] == 'ps':
            event = 'namespace'; custom = response(b'PID NAME\n1 init\n')
        elif words[0] == 'sha256sum':
            event = 'package_hash'; custom = response((PIN + '  ' + INSTALLED + '\n').encode())
        elif words[:2] == ['am', 'instrument']:
            event = 'read'; custom = response(wire(completed()))
            self.launches += 1; self.running = True
        if custom is None:
            self.override = self.reader_override
            return super().raw(args, **kwargs)
        if not self.clients_cleaned:
            raise AssertionError('dependent transport after unknown client ownership')
        self.calls.append((args, kwargs)); self.events.append(event)
        if self.reader_override:
            changed = self.reader_override(self, event, words)
            if changed is not None:
                custom = changed
        self.clients_cleaned &= custom.cleanup_complete is True
        return custom


class SdkReadControllerTests(unittest.TestCase):
    def test_real_reader_pin_is_new_play_artifact_only(self):
        self.assertEqual(reader.READBACK_APK_SHA256, reader.cache.TRACED_APK_SHA256)
        self.assertNotIn(reader.READBACK_APK_SHA256, (reader.cache.APK_SHA256, reader.cache.GUARDED_APK_SHA256))

    def invoke(self, device=None, sink=None):
        device = device or Device(); sink = sink if sink is not None else Mock()
        with patch.object(reader, 'READBACK_APK_SHA256', PIN):
            result = reader.read_phase(device, PIN, NONCE, sink)
        self.assertNotIn(NONCE, json.dumps(result))
        return result, device, sink

    def test_single_read_has_no_pre_stop_and_stops_verified_reader_before_success(self):
        result, device, sink = self.invoke()
        self.assertTrue(result['journal_verified']); self.assertTrue(result['instance_matched'])
        self.assertTrue(result['process_absent']); self.assertTrue(result['clients_cleaned'])
        self.assertEqual((device.launches, device.stops), (1, 1))
        self.assertLess(device.events.index('read'), device.events.index('stop'))
        sink.assert_called_once_with(wire(completed()))
        command, options = next(call for call in device.calls if shlex.split(call[0][1])[:2] == ['am', 'instrument'])
        self.assertEqual(options['deadline'], 45)
        words = shlex.split(command[1])
        extras = {words[i+1]: words[i+2] for i in range(len(words)-2) if words[i] == '-e'}
        self.assertEqual(extras, {'operation': 'read_phase', 'session': NONCE})

    def test_invalid_inputs_and_old_artifacts_cannot_touch_device(self):
        for pin, nonce, sink in ((reader.cache.APK_SHA256, NONCE, Mock()),
                (reader.cache.GUARDED_APK_SHA256, NONCE, Mock()), (PIN, 'C'*32, Mock()),
                (PIN, True, Mock()), (PIN, NONCE, None)):
            device = Device()
            with patch.object(reader, 'READBACK_APK_SHA256', PIN):
                result = reader.read_phase(device, pin, nonce, sink)
            self.assertEqual(result['status'], 'input_refused'); self.assertEqual(device.calls, [])

    def test_primary_or_child_process_prevents_dispatch_and_is_never_stopped(self):
        for child in (False, True):
            device = Device(lambda _, event, __: response(b'PID NAME\n99 ' + reader.cache.PACKAGE.encode() + b':child\n')
                if child and event == 'namespace' else None)
            device.running = not child
            result, device, _ = self.invoke(device)
            self.assertFalse(result['dispatched']); self.assertEqual(device.stops, 0)
            self.assertFalse(result['journal_verified'])

    def test_large_bounded_process_inventory_is_accepted_but_malformed_is_not(self):
        inventory = b'PID NAME\n' + b'99 com.synthetic.process\n' * 200
        self.assertGreater(len(inventory), 4096)
        result, _, _ = self.invoke(Device(lambda _, event, __: response(inventory) if event == 'namespace' else None))
        self.assertTrue(result['journal_verified'])
        for raw in (b'PID NAME\nbroken\n', b'PID NAME\n'+b'x'*16384, b'PID NAME\n1 \xff\n'):
            result, device, _ = self.invoke(Device(lambda _, event, __: response(raw) if event == 'namespace' else None))
            self.assertFalse(result['dispatched']); self.assertEqual(device.stops, 0)

    def test_raw_precedes_parser_even_for_oversize_or_failed_transport(self):
        for raw, status in ((b'x'*16385, 'completed'), (wire(completed()), 'timeout')):
            order = []
            device = Device(lambda _, event, __: response(raw, status=status) if event == 'read' else None)
            with patch.object(reader.decoder, 'parse_result', side_effect=lambda _: order.append('parse')):
                result, _, _ = self.invoke(device, lambda _: order.append('retain'))
            self.assertEqual(order, ['retain']); self.assertTrue(result['raw_protocol_retained'])
            self.assertTrue(result['process_absent']); self.assertFalse(result['journal_verified'])

    def test_unknown_client_retains_raw_without_parse_or_any_dependent_command(self):
        device = Device(lambda _, event, __: response(wire(completed()), cleaned=False) if event == 'read' else None)
        with patch.object(reader.decoder, 'parse_result') as parser:
            result, device, sink = self.invoke(device)
        parser.assert_not_called(); sink.assert_called_once()
        self.assertEqual(device.events[-1], 'read'); self.assertEqual(device.stops, 0)
        self.assertFalse(result['clients_cleaned']); self.assertFalse(result['journal_verified'])

    def test_sink_failure_stops_reader_without_accepting_unretained_diagnostic(self):
        result, device, _ = self.invoke(sink=Mock(side_effect=OSError('private canary')))
        self.assertEqual(result['failure_stage'], 'raw_retention'); self.assertEqual(device.stops, 1)
        self.assertIsNone(result['result']); self.assertFalse(result['raw_protocol_retained'])
        self.assertNotIn('private canary', json.dumps(result))

    def test_final_uid_or_apk_change_revokes_verification_and_does_not_stop_foreign_owner(self):
        for target in ('uid', 'package_hash'):
            counts = {}
            def override(_, event, __):
                counts[event] = counts.get(event, 0) + 1
                if counts[event] == 2 and event == target:
                    return response(b'10232\n' if event == 'uid' else ('0'*64+'  '+INSTALLED+'\n').encode())
                return None
            result, device, _ = self.invoke(Device(override))
            self.assertIsNotNone(result['result']); self.assertEqual(device.stops, 0)
            self.assertFalse(result['journal_verified']); self.assertFalse(result['process_absent'])

    def test_fixed_reader_error_preserved_independently_of_known_cleanup(self):
        error = dict(version=1, status='error', error='sdk_phase_read_failed', model_execution=False)
        result, device, _ = self.invoke(Device(lambda _, event, __: response(wire(error)) if event == 'read' else None))
        self.assertEqual(result['result'], error); self.assertTrue(result['process_absent'])
        self.assertFalse(result['journal_verified']); self.assertEqual(device.stops, 1)

    def test_preexisting_unknown_client_never_dispatches(self):
        device = Device(); device.clients_cleaned = False
        result, device, _ = self.invoke(device)
        self.assertEqual(device.calls, []); self.assertFalse(result['clients_cleaned'])


if __name__ == '__main__':
    unittest.main()
