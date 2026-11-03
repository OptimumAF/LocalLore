"""Closed SDK17 operator entry refuses missing input without leaking errors."""
from contextlib import redirect_stderr, redirect_stdout
import io
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from benchmarks import diagnostic_ui_activation as activation
from benchmarks import receipt_avd_environment as env


class DiagnosticUiCliTests(unittest.TestCase):
    def test_unknown_action_never_observes_files_or_dispatches(self):
        with patch.object(activation, '_api', side_effect=AssertionError('observation')):
            self.assertEqual(activation.main(['prepare']), 1)

    def test_environment_refusal_is_a_fixed_nonzero_exit_before_execute(self):
        binding = Mock(side_effect=env.EnvironmentRefused('PRIVATE_INPUT_CANARY'))
        api = SimpleNamespace(env=SimpleNamespace(binding=binding))
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(activation, '_api', return_value=api), \
             patch.object(activation, 'execute', side_effect=AssertionError('dispatch')) as execute, \
             redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = activation.main(['--input-sha256', '0' * 64])
            except env.EnvironmentRefused:
                self.fail('Environment refusal escaped the closed operator entry')
        self.assertEqual(code, 1)
        binding.assert_called_once_with(activation.INPUT)
        execute.assert_not_called()
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')
