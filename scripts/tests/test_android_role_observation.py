"""Original hostile observation fixtures, with unchanged canonical receipt validation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'benchmarks'))
import android_role_observation as observation
import android_play_probe as play
import android_cache_result as cache
import test_android_play_probe as legacy
from test_android_cache_result import value, raw, UUID


def snapshot(**changes):
    result = dict(version=1, callback_messages=1, buffered_text_bytes=3, callback_error='none',
        benchmark_available=True, sdk_input_tokens=0, sdk_output_tokens=0,
        configuration=dict(schema_requested=True, thinking_disabled_requested=True, template_rendered=True,
            max_tokens=220, prompt_utf8_bytes=123, schema_utf8_bytes=456))
    result.update(changes)
    return result


def packet():
    result = value()
    result['play_result']['first_output_observed'] = True
    turn = result['play_result']['turns'][0]; turn['first_output_observed'] = True
    for generation in turn['generations']:
        generation.update(output_observation='observed', first_output_elapsed_ms=1.5, terminal_observation=snapshot())
    return result


class RoleObservationTests(unittest.TestCase):
    def decode(self, value):
        return cache.parse_result(raw(value), 'gift', UUID, role_observations=True)

    def test_new_observations_survive_without_replacing_canonical_receipt_checks(self):
        v = packet(); decoded = self.decode(v)
        self.assertEqual(decoded['result'], v['play_result'])
        self.assertEqual(decoded['result']['outcome'], 'committed')
        self.assertEqual(decoded['result']['turns'][0]['generations'][0]['terminal_observation']['sdk_output_tokens'], 0)
        v['play_result']['receipts_after'] = 20
        self.assertIsNone(self.decode(v))

    def test_legacy_artifacts_do_not_admit_new_rows_and_new_contract_requires_them(self):
        self.assertIsNone(cache.parse_result(raw(packet()), 'gift', UUID))
        self.assertIsNone(self.decode(value()))
        self.assertIsNotNone(cache.parse_result(raw(value()), 'gift', UUID))
        self.assertIsNone(cache.parse_result(raw(packet()), 'gift', UUID, role_observations=1))

    def test_standalone_play_transport_accepts_both_exact_schemas_but_not_mixed_rows(self):
        self.assertIsNotNone(play.parse_result(legacy.raw(), 'gift'))
        v = packet()['play_result']
        self.assertIsNotNone(play.parse_result(legacy.raw(v), 'gift'))
        for key in observation.GENERATION_EXTRA:
            del v['turns'][0]['generations'][1][key]
        self.assertIsNone(play.parse_result(legacy.raw(v), 'gift'))

    def test_failure_can_have_real_buffered_output_without_an_accepted_event(self):
        v = packet(); turn = v['play_result']['turns'][0]
        turn.update(outcome='failed', error='timeout', roles=1, narrator_calls=0,
            revision_after=0, receipts_after=0, exact_retry=False, canon_unchanged=True)
        turn['generations'] = turn['generations'][:1]
        turn['generations'][0].update(status='error', error='timeout', input_tokens=None, output_tokens=None,
            schema_enforced=False, thinking_disabled=False, template_applied=False)
        v['play_result'] = legacy.value('gift', turn)
        v['metrics'].update(play_roles=1, conversations_opened=1, conversations_closed=1)
        decoded = self.decode(v)
        self.assertEqual(decoded['result']['outcome'], 'failed')
        self.assertTrue(decoded['result']['first_output_observed'])
        self.assertEqual(decoded['result']['receipts_after'], 0)

    def test_unknown_and_known_negative_are_distinct_and_do_not_erase_a_valid_receipt(self):
        for state in ('unknown', 'not_observed'):
            v = packet(); v['play_result']['first_output_observed'] = False
            turn = v['play_result']['turns'][0]; turn['first_output_observed'] = False
            for generation in turn['generations']:
                generation.update(output_observation=state, first_output_elapsed_ms=None, terminal_observation=None)
            self.assertIsNotNone(self.decode(v))

    def test_false_legacy_flag_cannot_hide_new_positive_observation(self):
        for where in ('aggregate', 'turn'):
            v = packet()
            (v['play_result'] if where == 'aggregate' else v['play_result']['turns'][0])['first_output_observed'] = False
            self.assertIsNone(self.decode(v))

    def test_observer_timing_is_finite_nullable_and_never_a_boolean(self):
        for state, elapsed in (('observed', None), ('observed', True), ('observed', float('inf')),
                ('observed', -1), ('observed', 180001), ('unknown', 0), ('not_observed', 1)):
            v = packet(); v['play_result']['turns'][0]['generations'][0].update(
                output_observation=state, first_output_elapsed_ms=elapsed)
            self.assertIsNone(self.decode(v))

    def test_snapshot_cannot_contradict_a_positive_or_negative_buffer_observation(self):
        for state, amount in (('observed', 0), ('unknown', 1), ('not_observed', 1)):
            v = packet(); g = v['play_result']['turns'][0]['generations'][0]
            g.update(output_observation=state, first_output_elapsed_ms=1 if state == 'observed' else None,
                terminal_observation=snapshot(buffered_text_bytes=amount))
            self.assertIsNone(self.decode(v))

    def test_optional_benchmark_failure_keeps_callback_measurements_and_null_counters(self):
        v = packet(); g = v['play_result']['turns'][0]['generations'][0]
        g['terminal_observation'] = snapshot(benchmark_available=False, sdk_input_tokens=None, sdk_output_tokens=None)
        self.assertIsNotNone(self.decode(v))
        g['terminal_observation']['sdk_output_tokens'] = 0
        self.assertIsNone(self.decode(v))

    def test_reported_sdk_counts_are_raw_and_not_gameplay_budget_or_progress_proof(self):
        for count in (0, 4097, 2 ** 31 - 1):
            self.assertTrue(observation.valid_snapshot(snapshot(sdk_input_tokens=count, sdk_output_tokens=count)))
        for count in (-1, 2 ** 31, True, None, 0.0):
            self.assertFalse(observation.valid_snapshot(snapshot(sdk_input_tokens=count)))

    def test_callback_shape_bounds_and_private_prose_are_rejected(self):
        for changes in (dict(callback_messages=65536), dict(callback_messages=0), dict(buffered_text_bytes=16385),
                dict(callback_error='private exception'), dict(callback_messages=True), dict(private='story'), dict(version=True)):
            self.assertFalse(observation.valid_snapshot(snapshot(**changes)))
        self.assertTrue(observation.valid_snapshot(snapshot(callback_messages=65535, buffered_text_bytes=16384)))

    def test_configuration_is_bounded_request_metadata_and_cannot_claim_enforcement(self):
        for key, value in (('schema_requested', 1), ('thinking_disabled_requested', 'true'),
                ('max_tokens', 351), ('prompt_utf8_bytes', 0), ('prompt_utf8_bytes', 32769),
                ('schema_utf8_bytes', 0), ('prompt', 'private story')):
            item = snapshot(); item['configuration'][key] = value
            self.assertFalse(observation.valid_snapshot(item))
        self.assertTrue(observation.valid_snapshot(snapshot(configuration=None)))
        v = packet(); v['play_result']['turns'][0]['generations'][1]['terminal_observation']['configuration']['max_tokens'] = 221
        self.assertIsNone(self.decode(v))

    def test_extra_fields_and_duplicate_json_are_rejected_without_echoing_raw_text(self):
        v = packet(); v['play_result']['turns'][0]['generations'][0]['private'] = 'CANARY'
        self.assertIsNone(self.decode(v))
        packet_bytes = raw(packet()).replace(b'"callback_messages": 1', b'"callback_messages": 1, "callback_messages": 1')
        self.assertIsNone(cache.parse_result(packet_bytes, 'gift', UUID, role_observations=True))


if __name__ == '__main__':
    unittest.main()
