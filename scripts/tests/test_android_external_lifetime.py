"""Original synthetic lifetime-admission tests; no SDK or owner is observed.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
from contextlib import ExitStack, contextmanager
import copy
import inspect
from pathlib import Path
from types import SimpleNamespace
import textwrap
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_external_controller as external


NOW = 2_000_000_000.0
SESSION_BUDGET = 1100


@contextmanager
def synthetic_session(remaining, *, forbid_capture=False):
    """Mock existing external boundaries, never Session or its admission code."""
    sdk = Path("synthetic-sdk-not-an-installation")
    request = dict(sdk=str(sdk), powershell="synthetic-powershell-not-an-executable",
                   sources={"path": "synthetic-source-map"}, running="synthetic-running",
                   proposal="synthetic-proposal", server="synthetic-server")
    sources = {"original-synthetic-source": "a" * 64}
    server = {"original-synthetic-server": True}
    descriptor = dict(adb_path=str(sdk / "platform-tools/adb.exe"),
                      avd_name=external.environment.NAME, serial="emulator-5592",
                      console_port=5592, guest_boot_verified=False,
                      launcher={"pid": 101, "creation_filetime": 202,
                                "executable": "synthetic-launcher"},
                      started_epoch=NOW - 10, deadline_epoch=NOW + remaining)
    original = copy.deepcopy(descriptor)
    events, clock = [], [NOW]
    live = SimpleNamespace(descriptor=descriptor,
                           check=Mock(side_effect=lambda: events.append("live-check")))
    capture = SimpleNamespace(target=None, clean=True)
    capture.check_server = Mock(side_effect=lambda: events.append("server-observation"))
    capture.capture = Mock(return_value=b"List of devices attached\n"
                               b"emulator-5592 device transport_id:7\n")
    responses = {"boot": b"1\n", "user": b"0\n"}

    def sdk_reply(operation, label, seconds, cap):
        events.append("sdk-" + label)
        if label == "profile":
            return b"35\n" if "ro.build.version.sdk" in operation[1] else b"x86_64\n"
        return responses[label]

    capture.adb = Mock(side_effect=sdk_reply)

    def construct(*args):
        events.append("capture-construction")
        if forbid_capture:
            raise AssertionError("insufficient_lifetime_reached_capture_construction")
        return capture

    def read_json(path):
        events.append("read-" + str(path))
        if str(path) == request["sources"]["path"]:
            return sources
        if str(path) == request["server"]:
            return server
        raise AssertionError("unexpected_synthetic_read")

    with ExitStack() as stack:
        reader = stack.enter_context(patch.object(external.environment, "read_json", side_effect=read_json))
        digest = stack.enter_context(patch.object(external.environment, "digest", return_value="b" * 64))
        opener = stack.enter_context(patch.object(external.environment, "open_live_owner", return_value=live))
        admission = stack.enter_context(patch.object(external, "admit", side_effect=lambda _: events.append("admission")))
        source_map = stack.enter_context(patch.object(external.driver, "source_map", return_value=sources))
        constructor = stack.enter_context(patch.object(external, "SdkCapture", side_effect=construct))
        stack.enter_context(patch.object(external.time, "time", side_effect=lambda: clock[0]))
        sleeper = stack.enter_context(patch.object(external.time, "sleep", side_effect=AssertionError("unexpected_poll")))
        yield SimpleNamespace(request=request, out=Path("synthetic-evidence-not-created"),
                              sdk=sdk, descriptor=descriptor, original=original, live=live,
                              capture=capture, constructor=constructor, reader=reader,
                              digest=digest, opener=opener, admission=admission,
                              source_map=source_map, sleeper=sleeper, server=server,
                              clock=clock, events=events)


class OwnedSessionLifetimeTests(unittest.TestCase):
    def assert_no_capture(self, fixture):
        fixture.constructor.assert_not_called()
        fixture.capture.check_server.assert_not_called()
        fixture.capture.capture.assert_not_called()
        fixture.capture.adb.assert_not_called()
        self.assertNotIn("read-" + fixture.request["server"], fixture.events)
        self.assertEqual(fixture.descriptor, fixture.original)

    def test_short_remaining_lifetime_refuses_before_capture_or_server_observation(self):
        # The old constructor reaches our sentinel: a concrete unsafe ordering,
        # rather than a test failure caused only by a missing new helper symbol.
        for remaining in (1099.999, 100, 1):
            with self.subTest(remaining=remaining), synthetic_session(remaining, forbid_capture=True) as f:
                with self.assertRaises(external.ExternalRefused):
                    external.Session(f.request, f.out)
                self.assert_no_capture(f)
                f.live.check.assert_called_once_with()
                f.admission.assert_called_once_with(f.request)
                f.source_map.assert_called_once_with()

    def test_time_used_by_live_admission_is_not_counted_as_available_for_sdk(self):
        with synthetic_session(1101, forbid_capture=True) as f:
            def live_check():
                f.events.append("live-check")
                f.clock[0] += 2
            f.live.check.side_effect = live_check
            with self.assertRaises(external.ExternalRefused):
                external.Session(f.request, f.out)
            self.assert_no_capture(f)
            f.admission.assert_called_once_with(f.request)

    def test_exact_remaining_budget_admits_real_session_without_extending_lease(self):
        with synthetic_session(SESSION_BUDGET) as f:
            session = external.Session(f.request, f.out)
            self.assertIs(session.live, f.live)
            self.assertIs(session.lease, f.descriptor)
            self.assertIs(session.capture, f.capture)
            f.constructor.assert_called_once_with(f.out / "clients", SESSION_BUDGET,
                f.sdk / "platform-tools/adb.exe", Path(f.request["powershell"]),
                f.server, f.descriptor["launcher"])
            self.assertEqual(f.capture.target, {"transport_id": 7})
            self.assertEqual(f.capture.adb.call_count, 4)
            f.capture.check_server.assert_called()
            self.assertLess(f.events.index("live-check"), f.events.index("capture-construction"))
            self.assertLess(f.events.index("admission"), f.events.index("capture-construction"))
            self.assertEqual(f.descriptor, f.original)
            f.sleeper.assert_not_called()

    def test_extra_owned_time_does_not_increase_the_existing_sdk_budget(self):
        with synthetic_session(1180) as f:
            external.Session(f.request, f.out)
            self.assertEqual(f.constructor.call_args.args[1], SESSION_BUDGET)
            self.assertEqual(f.descriptor, f.original)
            self.assertEqual(f.clock[0], NOW)

    def test_expired_live_owner_stops_before_capture_without_replacing_lease(self):
        for remaining in (0, -1):
            with self.subTest(remaining=remaining), synthetic_session(remaining, forbid_capture=True) as f:
                # Expiration is already an existing live-owner boundary. Keep
                # that check real in Session, while its native identity is fake.
                f.live.check.side_effect = external.environment.EnvironmentRefused("owner_expired")
                with self.assertRaises(external.ExternalRefused):
                    external.Session(f.request, f.out)
                self.assert_no_capture(f)
                f.admission.assert_not_called()
                f.opener.assert_called_once_with(f.request["proposal"], f.request["running"], "b" * 64)

    def test_existing_live_admission_and_source_guards_still_precede_capture(self):
        for boundary in ("live", "admission", "source"):
            with self.subTest(boundary=boundary), synthetic_session(1180, forbid_capture=True) as f:
                if boundary == "live":
                    f.live.check.side_effect = RuntimeError("synthetic_owner_lost")
                elif boundary == "admission":
                    f.admission.side_effect = external.ExternalRefused("synthetic_admission")
                else:
                    f.source_map.return_value = {"changed-synthetic-source": "c" * 64}
                with self.assertRaises(external.ExternalRefused):
                    external.Session(f.request, f.out)
                self.assert_no_capture(f)

    def test_admitted_session_keeps_sticky_owner_failure_without_another_sdk_call(self):
        with synthetic_session(1180) as f:
            session = external.Session(f.request, f.out)
            previous_calls = f.capture.adb.call_count
            f.live.check.side_effect = RuntimeError("synthetic_owner_lost")
            with self.assertRaises(external.ExternalRefused):
                session.adb(["get-state"], "later")
            f.live.check.side_effect = None
            previous_checks = f.live.check.call_count
            with self.assertRaises(external.ExternalRefused):
                session.adb(["get-state"], "still-later")
            self.assertEqual(f.capture.adb.call_count, previous_calls)
            self.assertEqual(f.live.check.call_count, previous_checks)
            self.assertTrue(session.failed)
            self.assertFalse(f.capture.clean)
            self.assertEqual(f.descriptor, f.original)

    def test_session_wires_fixed_budget_guard_before_capture_not_after_sdk(self):
        tree = ast.parse(textwrap.dedent(inspect.getsource(external.Session.__init__)))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        guards = [node for node in calls if isinstance(node.func, ast.Name)
                  and node.func.id == "_require_session_lifetime"]
        constructors = [node for node in calls if isinstance(node.func, ast.Name)
                        and node.func.id == "SdkCapture"]
        self.assertEqual(len(guards), 1, "real_session_requires_owned_lifetime_guard")
        self.assertEqual(len(constructors), 1)
        self.assertEqual(ast.dump(guards[0].args[0]), ast.dump(ast.parse("self.lease", mode="eval").body))
        self.assertLess(guards[0].lineno, constructors[0].lineno)
        self.assertIsInstance(constructors[0].args[1], ast.Name)
        self.assertEqual(constructors[0].args[1].id, "SESSION_SECONDS")
        self.assertEqual(getattr(external, "SESSION_SECONDS", None), SESSION_BUDGET)


if __name__ == "__main__":
    unittest.main()
