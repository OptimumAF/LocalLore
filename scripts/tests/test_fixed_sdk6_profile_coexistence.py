"""Distinct fixed SDK6 profiles over fresh D files and simulated wire only.

Equal version/session numbers cannot grant another profile's owner, admission
or recorded bytes. No SDK, device, native owner, model or shared ledger is used.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_client_v6 as ui_client
from benchmarks import android_process_verification_v6 as ui_reader
from benchmarks import android_process_live_death_client as live_client
from benchmarks import android_process_live_death_verification as live_reader
from benchmarks import owned_ui_contract as ui_contract
from benchmarks import owned_ui_owner as ui_owner
from benchmarks import owned_live_death_contract as live_contract
from benchmarks import owned_live_death_owner as live_owner
from scripts.tests import test_archive_ui_client as ui_wire_fixture
from scripts.tests import test_archive_ui_fixtures as ui_fixture
from scripts.tests import test_live_death_closed_replay as live_fixture
from scripts.tests import test_owned_live_death_contract as live_metadata


class FixedSdk6AdmissionIsolationTests(unittest.TestCase):
    def test_equal_versions_and_session_names_keep_distinct_valid_admissions(self):
        self.assertEqual(ui_contract.CLIENT_VERSION, 6)
        self.assertEqual(live_contract.CLIENT_VERSION, 6)
        self.assertEqual(ui_contract.SESSION_FILE, 'sdk-session-v6.json')
        self.assertEqual(live_contract.SESSION_FILE, ui_contract.SESSION_FILE)
        self.assertNotEqual(ui_contract.PROTOCOL, live_contract.PROTOCOL)
        self.assertNotEqual(ui_contract.SDK_PROTOCOL, live_contract.SDK_PROTOCOL)
        self.assertNotEqual(ui_contract.PROOF_PROTOCOL, live_contract.PROOF_PROTOCOL)
        ui, live = ui_fixture.admission(), live_metadata.admission()
        before = copy.deepcopy((ui, live))
        # Both positive controls use the unchanged production validators.
        self.assertEqual(ui_contract.validate_admission(ui), ui)
        self.assertEqual(live_contract.validate_admission(live), live)
        with self.assertRaises(ui_contract.TargetRefused):
            ui_contract.validate_admission(live)
        with self.assertRaises(live_contract.TargetRefused):
            live_contract.validate_admission(ui)
        self.assertEqual((ui, live), before)

    def test_each_fixed_client_rejects_the_other_exact_owner_before_guard_or_io(self):
        cases = (
            (ui_client.OwnedUiSdkCapture, live_owner.LiveOwnedLiveDeathTarget),
            (live_client.OwnedLiveDeathSdkCapture, ui_owner.LiveOwnedUiTarget),
        )
        for client, wrong_type in cases:
            with self.subTest(client=client.__name__, owner=wrong_type.__name__):
                wrong = object.__new__(wrong_type)
                wrong.guard = Mock(side_effect=AssertionError('foreign owner guard reached'))
                with patch.object(Path, 'open', side_effect=AssertionError('foreign owner file IO')) as opened, \
                     patch.object(Path, 'mkdir', side_effect=AssertionError('foreign owner mkdir')) as mkdir, \
                     patch.object(wire.socket, 'socket', side_effect=AssertionError('foreign owner socket')) as socket, \
                     patch.object(wire.environment, 'check_binding', side_effect=AssertionError('foreign owner binding IO')) as binding:
                    with self.assertRaises(wire.ClientRefused):
                        client(Path('D:/Dev/_Temp/uncreated-sdk6-cross-profile/clients'), 30, wrong)
                wrong.guard.assert_not_called()
                opened.assert_not_called()
                mkdir.assert_not_called()
                socket.assert_not_called()
                binding.assert_not_called()


@unittest.skipUnless(os.name == 'nt', 'fresh physical D Windows record fixtures')
class FixedSdk6RecordedByteIsolationTests(unittest.TestCase):
    def test_valid_closed_records_cannot_cross_profiles_despite_equal_version_six(self):
        self.assertEqual(Path(tempfile.gettempdir()).drive.upper(), 'D:')
        graph = live_fixture.ClosedLiveGraph()
        live_pin = graph.add(graph.s, ['getprop', 'sys.boot_completed'], b'1\n', 'profile-control')
        live_row = wire.environment.read_json(live_pin['path'])
        # Replay every actual session/query/proof/stdout binding for the positive
        # control. Only existing fixture producers supply synthetic bytes.
        self.assertEqual(live_reader.verify_client_record(live_pin, graph.s, graph.a), live_row)

        fixture = ui_wire_fixture.ArchiveUiClientTests(methodName='runTest')
        try:
            fixture.setUp()
            cap = fixture.capture()
            self.assertEqual(cap.shell(['getprop', 'sys.boot_completed'], 'profile-control'),
                             b'original\0\x1a\xff\r\n')
            ui_pin = wire.environment.binding(cap.directory / 'command-0001.json')
            ui_row = fixture.record(cap)
            self.assertEqual(ui_reader.verify_client_record(ui_pin, cap.session, fixture.a), ui_row)
            self.assertEqual(live_row['version'], ui_row['version'])
            self.assertEqual(ui_row['version'], 6)
            self.assertEqual(Path(live_row['session']['path']).name, Path(ui_row['session']['path']).name)
            self.assertEqual(live_row['operation'], ui_row['operation'])

            # Give each reader its OWN valid admission/session so refusal is
            # exercised on the foreign record bytes, not an invalid outer input.
            with self.assertRaises(ui_contract.TargetRefused):
                ui_reader.verify_client_record(live_pin, cap.session, fixture.a)
            with self.assertRaises(live_contract.TargetRefused):
                live_reader.verify_client_record(ui_pin, graph.s, graph.a)
            # A rejected cross-read must not mutate either original proof graph.
            self.assertEqual(ui_reader.verify_client_record(ui_pin, cap.session, fixture.a), ui_row)
            self.assertEqual(live_reader.verify_client_record(live_pin, graph.s, graph.a), live_row)
            self.assertTrue(all(path.drive.upper() == 'D:' and path.is_relative_to(graph.base)
                                for path in graph.writes))
            self.assertEqual(fixture.base.drive.upper(), 'D:')
        finally:
            fixture.doCleanups()


if __name__ == '__main__':
    unittest.main()
