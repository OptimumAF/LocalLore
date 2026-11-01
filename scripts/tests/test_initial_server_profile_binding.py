"""Fixed pre-guest adapter profile, with no process, socket or file operations."""
import copy
from unittest.mock import patch
import unittest

from benchmarks import owned_target_owner as target
from scripts.tests import test_initial_server_exchange_guards as fixture


class InitialServerProfileBindingTests(unittest.TestCase):
    def test_adapter_names_its_fixed_isolated_profile_without_mutating_outer_admission(self):
        runtime = fixture.Runtime()
        before = copy.deepcopy(runtime.admission)
        view = target._InitialServerView(runtime, runtime.server_binding)
        self.assertEqual(view.admission['protocol'], target.server_contract.PROTOCOL)
        self.assertEqual(runtime.admission, before)
        self.assertEqual(runtime.full_calls, 0)
        self.assertEqual(runtime.fast_calls, 0)
        self.assertEqual(runtime.auth_calls, 0)
        self.assertEqual(runtime.events, [])

    def test_explicit_phone_unknown_or_malformed_profile_is_never_retagged(self):
        for protocol in (target.server_contract.PHONE_PROTOCOL, 'unrecognized-profile', None, 1):
            runtime = fixture.Runtime()
            runtime.admission['server']['protocol'] = protocol
            before = copy.deepcopy(runtime.admission)
            with self.subTest(protocol=protocol), \
                 patch.object(target.primitives.socket, 'socket', side_effect=AssertionError('socket reached')) as socket, \
                 patch.object(target.environment, 'check_binding', side_effect=AssertionError('binding IO reached')) as binding:
                with self.assertRaises(target.OwnerRefused):
                    target._InitialServerView(runtime, runtime.server_binding)
            self.assertEqual(runtime.admission, before)
            socket.assert_not_called()
            binding.assert_not_called()
            self.assertEqual(runtime.full_calls, 0)
            self.assertEqual(runtime.fast_calls, 0)
            self.assertEqual(runtime.auth_calls, 0)


if __name__ == '__main__':
    unittest.main()
