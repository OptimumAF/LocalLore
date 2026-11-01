# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""FIRST SDK8 oracles. Exact module absence selects SDK7 for feature-absence evidence ONLY."""
import copy
import importlib
from pathlib import Path, PureWindowsPath
import socket
import unittest
from unittest.mock import patch

from benchmarks import owned_record_ui_contract as sdk7
from benchmarks import owned_target_contract as core
from scripts.tests import test_record_ui_fixtures as old


def selected(name, baseline):
    full = 'benchmarks.' + name
    try:
        return importlib.import_module(full)
    except ModuleNotFoundError as error:
        if error.name != full:
            raise
        return importlib.import_module('benchmarks.' + baseline)


c = selected('owned_player_presentation_ui_contract', 'owned_record_ui_contract')
client = selected('android_process_player_presentation_ui_client', 'android_process_record_ui_client')
owner = selected('owned_player_presentation_ui_owner', 'owned_record_ui_owner')
controller = selected('player_presentation_ui_controller', 'record_ui_controller')
build = selected('player_presentation_ui_build', 'record_ui_build')
PROTOCOL = 'owned-emulator-player-presentation-ui-v1'
SDK = 'sdk-player-presentation-ui-v1'
PROOF = 'player-presentation-ui-socket-proof-v1'
GUEST = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-31-player-presentation-ui-v1/avd-v1')
NEW_SOURCES = {'owned_player_presentation_ui_contract.py', 'owned_player_presentation_ui_owner.py',
               'android_process_player_presentation_ui_client.py', 'android_process_player_presentation_ui_verification.py',
               'player_presentation_ui_controller.py', 'player_presentation_ui_build.py'}


def admission():
    value = old.admission()
    value['protocol'] = PROTOCOL
    value['guest']['root'] = str(GUEST)
    value['sources'] = sorted([old.legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
                               for name in old.SOURCE_NAMES | NEW_SOURCES], key=lambda row: row['path'])
    return value


def session(value):
    result = old.legacy.session(value)
    descriptor = old.legacy.running(value); descriptor['protocol'] = PROTOCOL
    result.update(protocol=SDK, descriptor=descriptor)
    return result


class PlayerPresentationUiProfileTests(unittest.TestCase):
    def test_sdk8_is_fixed_to_new_root_and_distinct_tags_with_unchanged_ten_cases(self):
        self.assertEqual((c.PROTOCOL, c.SDK_PROTOCOL, c.PROOF_PROTOCOL), (PROTOCOL, SDK, PROOF))
        self.assertEqual((c.CLIENT_VERSION, c.SESSION_FILE), (8, 'sdk-session-v8.json'))
        self.assertEqual(c.GUEST_ROOT, GUEST)
        self.assertEqual(c.OWNER_SCRIPT, 'owned_player_presentation_ui_owner.py')
        self.assertEqual(c.BOOT_CLAIM_FILE, 'owned-player-presentation-ui-boot-claim-v1.json')
        self.assertEqual(tuple(c.INSTRUMENTATIONS), tuple(old.INSTRUMENTATIONS))
        self.assertEqual(c.SOURCE_NAMES, old.SOURCE_NAMES | NEW_SOURCES)
        self.assertEqual((c.APP, c.TEST, c.MODEL_MATERIAL), (old.APP, old.TEST, False))

    def test_new_admission_is_pure_and_does_not_mutate_the_caller(self):
        value = admission(); original = copy.deepcopy(value)
        with patch.object(Path, 'open', side_effect=AssertionError('file IO')), patch.object(socket, 'socket', side_effect=AssertionError('socket IO')):
            actual = c.validate_admission(value)
        self.assertEqual(actual, original)
        actual['sources'].clear(); self.assertEqual(value, original)

    def test_old_root_and_all_protocol_retags_are_refused_both_directions(self):
        value = admission()
        self.assertEqual(c.validate_admission(value), value)  # Establish the positive first.
        for wrong in (str(old.GUEST_ROOT), str(GUEST.parent / 'different.avd')):
            bad = copy.deepcopy(value); bad['guest']['root'] = wrong
            with self.assertRaises(core.TargetRefused): c.validate_admission(bad)
        with self.assertRaises(core.TargetRefused): c.validate_admission(old.admission())
        with self.assertRaises(core.TargetRefused): sdk7.validate_admission(value)
        bad = old.admission(); bad['protocol'] = PROTOCOL; bad['guest']['root'] = str(GUEST)
        with self.assertRaises(core.TargetRefused): c.validate_admission(bad)  # Missing new source closure.

    def test_no_model_material_arbitrary_profile_or_missing_launcher_source_is_admitted(self):
        value = admission(); c.validate_admission(value)
        for key in ('model', 'probe', 'process_probe'):
            bad = copy.deepcopy(value); bad['artifacts'][key] = old.legacy.pin('D:/Synthetic/' + key)
            with self.assertRaises(core.TargetRefused): c.validate_admission(bad)
        for key in ('profile', 'verifier', 'product_root', 'selectors'):
            bad = copy.deepcopy(value); bad[key] = 'caller-selected'
            with self.assertRaises(core.TargetRefused): c.validate_admission(bad)
        bad = copy.deepcopy(value); bad['sources'] = [row for row in bad['sources'] if PureWindowsPath(row['path']).name != 'player_presentation_ui_build.py']
        with self.assertRaises(core.TargetRefused): c.validate_admission(bad)

    def test_ten_instrumentations_and_scoped_claims_keep_the_original_closed_commands(self):
        value = admission(); c.validate_admission(value)
        for triple in old.INSTRUMENTATIONS:
            operation = {'argv': old.instrument(triple), 'stdin': None}
            self.assertEqual(c.instrumentation_kind(operation['argv']), triple[0])
            self.assertEqual(c.validate_operation(operation, value), operation)
        for argv in (['sh', '-c', 'id'], ['run-as', c.APP, 'ls'], ['getprop', 'ro.serialno']):
            with self.assertRaises(core.TargetRefused): c.validate_operation({'argv': argv, 'stdin': None}, value)

    def test_sdk8_session_and_proof_reject_old_versions_and_stale_descriptor(self):
        value = admission(); c.validate_admission(value)
        record = session(value); self.assertEqual(c.validate_session(record, value), record)
        proof = old.legacy.proof(record)
        proof.update(protocol=PROOF, session=old.legacy.pin(PureWindowsPath(record['root']) / 'sdk-session-v8.json'))
        c.validate_proof(proof, record, proof['context'])
        bad = copy.deepcopy(record); bad['protocol'] = old.SDK_PROTOCOL
        with self.assertRaises(core.TargetRefused): c.validate_session(bad, value)
        bad = copy.deepcopy(proof); bad['protocol'] = old.PROOF_PROTOCOL
        with self.assertRaises(core.TargetRefused): c.validate_proof(bad, record, proof['context'])
        bad = copy.deepcopy(record); bad['descriptor']['run_id'] = 'f' * 32
        with self.assertRaises(core.TargetRefused): c.validate_session(bad, value)

    def test_exact_new_client_and_owner_types_cannot_accept_legacy_lease_or_subclasses(self):
        self.assertTrue(hasattr(client, 'OwnedPlayerPresentationUiSdkCapture'))
        self.assertTrue(hasattr(owner, 'LiveOwnedPlayerPresentationUiTarget'))
        from benchmarks.owned_record_ui_owner import LiveOwnedRecordUiTarget
        wrong = object.__new__(LiveOwnedRecordUiTarget)
        with patch.object(socket, 'socket', side_effect=AssertionError('socket dispatch')):
            with self.assertRaises(client.ClientRefused): client.OwnedPlayerPresentationUiSdkCapture(Path('D:/Synthetic/unused'), 10, wrong)
            class Derived(client.OwnedPlayerPresentationUiSdkCapture): pass
            with self.assertRaises(client.ClientRefused): Derived(Path('D:/Synthetic/unused'), 10, wrong)

    def test_controller_uses_only_new_concrete_types_and_fixed_result_tags(self):
        self.assertEqual(controller.SCOPE, 'player-presentation-ui-controller-v1')
        self.assertEqual(controller.REQUEST_SCOPE, 'player-presentation-ui-controller-request-v1')
        self.assertIs(controller.LiveOwnedPlayerPresentationUiTarget, owner.LiveOwnedPlayerPresentationUiTarget)
        self.assertIs(controller.OwnedPlayerPresentationUiSdkCapture, client.OwnedPlayerPresentationUiSdkCapture)
        self.assertEqual(controller.SECONDS, 1200)

    def test_product_source_is_fixed_and_distinct_from_the_launcher_source(self):
        self.assertEqual(getattr(build, 'PRODUCT_HEAD', None), '42ae8f6b7df7373696d35c9a294b6d0517c8886c')
        self.assertEqual(getattr(build, 'PRODUCT_ROOT', None), Path('D:/Worktrees/LocalLore-record-ui-host-v1'))
        self.assertEqual(getattr(build, 'PRODUCT_BUILD_SHA256', None), 'a8543cd5c421e69d386f0e4b36f9280e771ae1813e09011eae91e562e5135c60')
        self.assertEqual(getattr(build, 'FROZEN_VERIFIER_SHA256', None), '6aa95e53312b8f371d4150e004eae9450694c5c7d6661fa9abc0a66bbfe43a0b')

    def test_product_drift_and_legacy_admission_refuse_before_frozen_verifier_dispatch(self):
        self.assertTrue(hasattr(build, '_load_verified_product'))
        with patch.object(build, '_load_verified_product', side_effect=AssertionError('product verifier must not dispatch')):
            with self.assertRaises((build.BuildRefused, core.TargetRefused)): build.verify_current(old.admission())
            bad = admission(); bad['artifacts']['build']['sha256'] = 'f' * 64
            with self.assertRaises((build.BuildRefused, core.TargetRefused)): build.verify_current(bad)
