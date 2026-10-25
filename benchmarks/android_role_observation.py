"""Strict optional SDK observations; they cannot validate output or establish canon.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy

import android_play_probe as play

GENERATION_EXTRA = {'output_observation', 'first_output_elapsed_ms', 'terminal_observation'}
SNAPSHOT = {'version', 'callback_messages', 'buffered_text_bytes', 'callback_error', 'benchmark_available',
            'sdk_input_tokens', 'sdk_output_tokens', 'configuration'}
CONFIG = {'schema_requested', 'thinking_disabled_requested', 'template_rendered', 'max_tokens',
          'prompt_utf8_bytes', 'schema_utf8_bytes'}


def integer(value, cap, minimum=0):
    return type(value) is int and minimum <= value <= cap


def valid_snapshot(value):
    if value is None:
        return True
    if (type(value) is not dict or set(value) != SNAPSHOT or type(value['version']) is not int
            or value['version'] != 1 or not integer(value['callback_messages'], 65535)
            or not integer(value['buffered_text_bytes'], 16384)
            or value['buffered_text_bytes'] > 0 and value['callback_messages'] == 0
            or type(value['callback_error']) is not str or value['callback_error'] not in
                {'none', 'unsupported_output', 'output_too_large', 'generation_failed'}
            or type(value['benchmark_available']) is not bool):
        return False
    counts = [value[k] for k in ('sdk_input_tokens', 'sdk_output_tokens')]
    if value['benchmark_available']:
        if not all(integer(count, 2 ** 31 - 1) for count in counts):
            return False
    elif counts != [None, None]:
        return False
    config = value['configuration']
    return config is None or (type(config) is dict and set(config) == CONFIG
        and all(type(config[k]) is bool for k in ('schema_requested', 'thinking_disabled_requested', 'template_rendered'))
        and integer(config['max_tokens'], 350, 1) and integer(config['prompt_utf8_bytes'], 32768, 1)
        and integer(config['schema_utf8_bytes'], 32768)
        and config['schema_requested'] == (config['schema_utf8_bytes'] > 0))


def valid_generation(value):
    if type(value) is not dict or set(value) != play.GENERATION_KEYS | GENERATION_EXTRA:
        return False
    state = value['output_observation']
    if type(state) is not str or state not in {'unknown', 'not_observed', 'observed'}:
        return False
    elapsed = value['first_output_elapsed_ms']
    if (not play.number(elapsed, 180000) if state == 'observed' else elapsed is not None):
        return False
    snapshot = value['terminal_observation']
    if not valid_snapshot(snapshot):
        return False
    if snapshot is not None:
        if (snapshot['buffered_text_bytes'] > 0) != (state == 'observed'):
            return False
        config = snapshot['configuration']
        if config is not None and config['max_tokens'] > (350 if value['role'] == 'director' else 220):
            return False
    return play.valid_generation({key: value[key] for key in play.GENERATION_KEYS})


def validate_play_result(value, metrics, case):
    """Use the original canonical receipt checks after validating diagnostics separately."""
    try:
        if type(value) is not dict or type(value.get('turns')) is not list or not 1 <= len(value['turns']) <= 2:
            return None
        stripped = copy.deepcopy(value)
        for turn in stripped['turns']:
            if type(turn) is not dict or type(turn.get('generations')) is not list or len(turn['generations']) > 3:
                return None
            if not all(valid_generation(generation) for generation in turn['generations']):
                return None
            if turn.get('first_output_observed') != any(g['output_observation'] == 'observed' for g in turn['generations']):
                return None
            for generation in turn['generations']:
                for key in GENERATION_EXTRA:
                    del generation[key]
        if play.validate_play_result(stripped, metrics, case) is None:
            return None
        return value, metrics
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
        return None
