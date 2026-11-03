"""Original SDK17 parsed/read-byte binding controls; no actual files or targets.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0

Quiet before/after binding observations model an ABA read window. The bytes
actually consumed must match the expected digest, not just length. JSON helper
controls retain the real existing env.read_bound_json implementation, which
already hashes its consumed bytes: no fabricated JSON-helper RED.
"""
import contextlib
import hashlib
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import diagnostic_ui_activation as activation
from benchmarks import diagnostic_ui_controller as controller


GOOD = b'{"value":1}'
WRONG = b'{"value":2}'
PIN = {'path': r'D:\synthetic-diagnostic-bound\record.json',
       'bytes': len(GOOD), 'sha256': hashlib.sha256(GOOD).hexdigest()}


class _ReadWindow:
    def __init__(self, payload):
        self.payload = payload
        self.reads = 0
        self.streams = []

    def stat(self):
        return SimpleNamespace(st_size=len(self.payload))

    def read_bytes(self):
        self.reads += 1
        return self.payload

    def open(self, path, mode='r', *args, **kwargs):
        if Path(path) != Path(PIN['path']) or mode != 'rb':
            raise AssertionError('Unexpected file access outside bounded fake read')
        self.reads += 1
        stream = io.BytesIO(self.payload)
        self.streams.append(stream)
        return stream


class DiagnosticUiBoundReadTests(unittest.TestCase):
    @contextlib.contextmanager
    def window(self, payload):
        self.assertEqual(len(GOOD), len(payload))
        observed = _ReadWindow(payload)
        env = controller.env
        # Keep actual syntax/type validation and actual JSON hash/decode helpers.
        # Only filesystem and repeated path observations are controlled ports.
        decode = env.decode_json
        api = SimpleNamespace(env=env, contract=controller.contract)
        with patch.object(activation, '_api', return_value=api), \
                patch.object(env, 'check_binding', return_value=None) as checks, \
                patch.object(env, 'safe_path', return_value=observed), \
                patch.object(env, 'decode_json', wraps=decode) as decoder, \
                patch.object(Path, 'open', lambda path, mode='r', *a, **kw:
                             observed.open(path, mode, *a, **kw)):
            try:
                yield observed, checks, decoder
            finally:
                # No background task or real descriptor exists, even on RED.
                for stream in observed.streams:
                    stream.close()

    def test_activation_bound_matching_bytes_preserves_json_and_observation_controls(self):
        with self.window(GOOD) as (observed, checks, decoder):
            self.assertEqual({'value': 1}, activation._bound(dict(PIN)))
            self.assertEqual(1, observed.reads)
            self.assertEqual(2, checks.call_count)
            decoder.assert_called_once_with(GOOD)
            self.assertTrue(all(stream.closed for stream in observed.streams))

    def test_activation_bound_rejects_wrong_equal_length_bytes_before_decode(self):
        with self.window(WRONG) as (observed, checks, decoder):
            with self.assertRaises((activation.ActivationRefused, controller.env.EnvironmentRefused)):
                activation._bound(dict(PIN))
            self.assertEqual(1, observed.reads)
            self.assertGreaterEqual(checks.call_count, 1)
            decoder.assert_not_called()

    def test_controller_raw_matching_bytes_preserves_the_exact_payload(self):
        with self.window(GOOD) as (observed, checks, decoder):
            self.assertEqual(GOOD, controller._raw(dict(PIN)))
            self.assertEqual(1, observed.reads)
            self.assertEqual(2, checks.call_count)
            decoder.assert_not_called()

    def test_controller_raw_rejects_wrong_equal_length_bytes_before_return(self):
        with self.window(WRONG) as (observed, checks, decoder):
            with self.assertRaises(controller.env.EnvironmentRefused):
                controller._raw(dict(PIN))
            self.assertEqual(1, observed.reads)
            self.assertGreaterEqual(checks.call_count, 1)
            decoder.assert_not_called()

    def test_controller_json_real_existing_helper_accepts_matching_bytes(self):
        with self.window(GOOD) as (observed, checks, decoder):
            self.assertEqual({'value': 1}, controller._json(dict(PIN)))
            self.assertEqual(1, observed.reads)
            self.assertGreaterEqual(checks.call_count, 1)
            decoder.assert_called_once_with(GOOD)

    def test_controller_json_real_existing_helper_already_rejects_unbound_bytes(self):
        with self.window(WRONG) as (observed, checks, decoder):
            with self.assertRaises(controller.env.EnvironmentRefused):
                controller._json(dict(PIN))
            self.assertEqual(1, observed.reads)
            self.assertGreaterEqual(checks.call_count, 1)
            decoder.assert_not_called()
