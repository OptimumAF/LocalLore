"""Hostile stopped-SDK diagnostics; these results never establish canonical state.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'benchmarks'))
import android_sdk_phase_result as decoder


def completed(**changes):
    value = dict(version=1, status='completed', error='none', model_execution=False,
        journal_valid=True, checkpoint_count=3, last_phase='model_initialize_before',
        last_role='director', fresh_reader_process=True, exit_history_available=True,
        exit_records_examined=16, exit_instance_matches=1, exit_instance_matched=True,
        exit_reason=4, exit_status=11)
    value.update(changes)
    return value


def wire(value):
    return (b'INSTRUMENTATION_RESULT: sdk_phase_result=' + json.dumps(value).encode()
        + b'\nINSTRUMENTATION_CODE: -1\n')


class SdkPhaseResultTests(unittest.TestCase):
    def test_all_sdk_phases_require_matching_roles(self):
        for phase in decoder.PHASES:
            generation = phase.startswith(('role_', 'model_create_', 'model_initialize_', 'native_respond_'))
            for role in ('none', 'director', 'narrator'):
                value = completed(last_phase=phase, last_role=role)
                self.assertEqual(decoder.valid(value), generation == (role != 'none'), (phase, role))

    def test_exact_bounded_result_and_uniform_line_endings(self):
        for count in (1, 96):
            value = completed(checkpoint_count=count, **({'last_phase': 'instrumentation_start', 'last_role': 'none'} if count == 1 else {}))
            self.assertEqual(decoder.parse_result(wire(value)), value)
            self.assertEqual(decoder.parse_result(wire(value).replace(b'\n', b'\r\n')), value)
        for count in (0, 97, True, 1.0):
            self.assertIsNone(decoder.parse_result(wire(completed(checkpoint_count=count))))

    def test_single_row_requires_the_mandatory_initial_checkpoint(self):
        self.assertIsNone(decoder.parse_result(wire(completed(checkpoint_count=1))))
        self.assertIsNone(decoder.parse_result(wire(completed(checkpoint_count=1, last_phase='terminal', last_role='none'))))

    def test_exit_identity_is_not_inferred_from_a_recent_unmatched_record(self):
        for matches in (0, 2, 16):
            value = completed(exit_instance_matches=matches, exit_instance_matched=False, exit_reason=-1, exit_status=-1)
            self.assertTrue(decoder.journal_verified(value))
            self.assertFalse(decoder.instance_matched(value))
            self.assertFalse(decoder.valid(dict(value, exit_reason=4)))
        for changes in (dict(exit_records_examined=0), dict(exit_records_examined=17),
                dict(exit_history_available=False), dict(exit_instance_matched=False),
                dict(exit_reason=-1), dict(exit_status=-1), dict(exit_instance_matches=True)):
            self.assertFalse(decoder.valid(completed(**changes)))

    def test_unavailable_history_and_same_process_never_gain_instance_proof(self):
        value = completed(exit_history_available=False, exit_records_examined=0,
            exit_instance_matches=0, exit_instance_matched=False, exit_reason=-1, exit_status=-1)
        self.assertTrue(decoder.journal_verified(value))
        self.assertFalse(decoder.instance_matched(value))
        value = completed(fresh_reader_process=False)
        self.assertTrue(decoder.valid(value))
        self.assertFalse(decoder.journal_verified(value))
        self.assertFalse(decoder.instance_matched(value))

    def test_fixed_error_is_observed_but_never_verified(self):
        value = dict(version=1, status='error', error='sdk_phase_read_failed', model_execution=False)
        self.assertEqual(decoder.parse_result(wire(value)), value)
        self.assertFalse(decoder.journal_verified(value))
        for extra in ({'last_phase': 'terminal'}, {'error': 'private diagnostics'}, {'model_execution': True}):
            self.assertFalse(decoder.valid(dict(value, **extra)))

    def test_foreign_wrapper_probe_vocabulary_and_raw_noise_are_rejected(self):
        valid = wire(completed())
        cases = [b'noise\n' + valid, valid + b'noise', valid.replace(b'sdk_phase_result', b'phase_result'),
            valid.replace(b'-1\n', b'0\n'), valid.replace(b'\n', b'\r\n', 1), b'x' * (decoder.MAX_RAW + 1),
            wire(completed(last_phase='probe_kill', last_role='none')),
            wire(completed(last_phase='probe_ready', last_role='none'))]
        for raw in cases:
            self.assertIsNone(decoder.parse_result(raw))

    def test_duplicate_keys_nonfinite_extra_fields_and_invalid_types_rejected(self):
        raw = wire(completed())
        for hostile in (raw.replace(b'"version": 1', b'"version": 1, "version": 1'),
                raw.replace(b'"exit_status": 11', b'"exit_status": NaN'),
                raw.replace(b'"exit_status": 11', b'"exit_status": true'),
                wire(completed(secret='private-save')), wire(completed(fresh_reader_process=1)),
                wire(completed(model_execution=0)), b'\xff', None):
            self.assertIsNone(decoder.parse_result(hostile))


if __name__ == '__main__':
    unittest.main()
