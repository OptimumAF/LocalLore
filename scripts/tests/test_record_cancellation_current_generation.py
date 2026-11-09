"""Original coherent-profile generation oracles. Synthetic records are never consent."""
import copy
import hashlib
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import record_cancellation_ui_fresh_contract as fresh
from scripts import record_cancellation_operation_contract as outer
from scripts import run_record_cancellation_operation as operation
from scripts import run_record_cancellation_ui_fresh as bridge
from scripts import record_cancellation_ui_prepare_inputs as inspection

NEW = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-coherent-v1')
FROZEN = NEW / 'frozen-profile-source-v1'
OLD = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-fresh-v1')
HEAD = 'c89b9e4f73a5481a1ba5afd9808821e023d1cd0c'
TREE = 'd29c520f60c2f21204fef0972d25f7d322ca368a'
OLD_HEAD = '287b158e72ed5c0811a2e7e433e73ada4f4d6c52'
OLD_TREE = '81dae478d06f2da8be5f14a693f276318fe0c4ac'
OLD_HANDOFF = dict(path=str(OLD / 'inspection-v1/frozen-inputs-v1.json'), bytes=9074,
    sha256='8ee6bd191b3b996c79aae877a125b2b2255ad4e61316ad1baae88cd477b1a40d')
OLD_PREPARE = dict(path=str(OLD / 'inspection-v1/prepare-proposal-v1.json'), bytes=173590,
    sha256='ce5b7347c7c2e933f590bf442079d6b9e540529cd31b4e9e4afb71c9c4b89ab0')
OLD_CONTRACT_SHA = 'e9fdacf5a04c7a70e897e68fcff5c165b2f1b375f95c5ae76a014557078852f7'


def pin(path):
    text = str(PureWindowsPath(str(path)))
    return dict(path=text, bytes=101, sha256=hashlib.sha256(('STRUCTURAL ONLY ' + text).encode()).hexdigest())


def inner_authority():
    return dict(version=1, scope='sdk18-fresh-prepare-and-one-record-cancellation-ui-run-v1',
        source_head=HEAD, proposal=pin(NEW / 'PROPOSED_OPERATION.md'),
        operator=copy.deepcopy(outer.FRESH_OPERATOR), contract=copy.deepcopy(outer.FRESH_CONTRACT),
        handoff=copy.deepcopy(fresh.HANDOFF), ledger=pin('D:/Dev/_Migration/LocalLore-AVD-Storage/ledger-v1.json'),
        allow_sdk_prepare=True, allow_one_boot=True, allow_model=False, allow_retirement=False,
        approval_reference='SYNTHETIC GENERATION TEST; NOT APPROVAL', max_operation_seconds=2400)


def parent_authority():
    return dict(version=1, scope='sdk18-record-cancellation-operation-authority-v1',
        profile_source_head=HEAD, operator=pin(NEW / 'candidate-source-v1/scripts/run_record_cancellation_operation.py'),
        contract=pin(NEW / 'candidate-source-v1/scripts/record_cancellation_operation_contract.py'),
        proposal=pin(NEW / 'PROPOSED_OPERATION.md'), fresh_authority=pin(NEW / 'human-authority-v1.json'),
        allow_one_operation=True, allow_model=False, allow_retirement=False,
        max_operation_seconds=2400, approval_reference='SYNTHETIC GENERATION TEST; NOT APPROVAL')


def handoff():
    return dict(version=1, scope='sdk18-fresh-inputs-v1', source_root=str(fresh.SOURCE),
        source_head=HEAD, source_tree=TREE,
        guest=str(fresh.GUEST), controls=str(fresh.CONTROLS), runtime=str(fresh.RUNTIME),
        sources=[pin(PureWindowsPath(str(fresh.SOURCE)) / 'benchmarks' / ('source-%02d.py' % n)) for n in range(28)],
        python=dict(executable=pin('C:/Synthetic/python.exe'), runtime_dll=None),
        artifacts=dict(build=copy.deepcopy(fresh.BUILD_PIN), product_apk=pin('D:/Synthetic/product.apk'),
            test_apk=pin('D:/Synthetic/test.apk')), prepare_proposal=copy.deepcopy(fresh.PREPARE_PIN),
        capacity_preview=pin(NEW / 'inspection-v1/capacity-preview-v1.json'),
        profile=dict(memory_mib=8192, cores=4, api=35, max_run_seconds=1800),
        execution_authorized=False, model_material=False)


class RecordCancellationCurrentGenerationTests(unittest.TestCase):
    def test_generation_slots_rotate_but_profile_and_build_remain_the_same(self):
        self.assertEqual(PureWindowsPath(str(fresh.OUT)), NEW)
        self.assertEqual(PureWindowsPath(str(outer.OUT)), NEW)
        self.assertEqual(PureWindowsPath(fresh.HANDOFF['path']), NEW / 'inspection-v1/frozen-inputs-v1.json')
        self.assertEqual(PureWindowsPath(fresh.PREPARE_PIN['path']), NEW / 'inspection-v1/prepare-proposal-v1.json')
        self.assertEqual(outer.HANDOFF, fresh.HANDOFF)
        self.assertNotEqual(fresh.HANDOFF['sha256'], OLD_HANDOFF['sha256'])
        self.assertNotEqual(outer.FRESH_CONTRACT['sha256'], OLD_CONTRACT_SHA)
        self.assertEqual(fresh.SOURCE_HEAD, HEAD)
        self.assertEqual(fresh.SOURCE_TREE, TREE)
        self.assertEqual(outer.FRESH_HEAD, HEAD)
        self.assertEqual(PureWindowsPath(str(fresh.SOURCE)), FROZEN)
        self.assertEqual(PureWindowsPath(str(outer.SOURCE)), FROZEN)
        self.assertEqual(inspection._SOURCE_FILE_COUNT, 2664)
        self.assertEqual(bridge._SOURCE_FILE_COUNT, 2664)
        self.assertEqual(PureWindowsPath(fresh.SOURCE_PUBLICATION['path']), NEW / 'profile-source-publication-v1.json')
        self.assertEqual(fresh.SOURCE_PUBLICATION['bytes'], 753002)
        self.assertEqual(fresh.SOURCE_PUBLICATION['sha256'], 'cab63a069e95ecc2fed25e4064bc67030d06cf4b744df39a1441100de659870d')
        self.assertEqual(fresh.BUILD_PIN['bytes'], 32140)
        self.assertEqual(fresh.BUILD_PIN['sha256'], '4d39b74ad5aee455ce9060c01d760204022101e4b6b8ce58d12f666450d2894e')
        for rules, value in ((fresh, inner_authority()), (outer, parent_authority())):
            original = copy.deepcopy(value)
            detached = rules.validate_authority(value)
            self.assertEqual(detached, original)
            detached['operator']['sha256'] = '0' * 64
            self.assertEqual(value, original)

    def test_old_inner_authority_and_retagged_handoff_pin_cannot_be_refreshed_by_path_only(self):
        valid = inner_authority()
        self.assertEqual(fresh.validate_authority(valid), valid)
        for kind in ('untouched-old', 'retagged-old-handoff', 'current-path-wrong-bytes'):
            stale = copy.deepcopy(valid)
            if kind == 'untouched-old':
                for role in ('proposal', 'operator', 'contract'):
                    stale[role]['path'] = str(OLD / PureWindowsPath(stale[role]['path']).relative_to(NEW))
                stale['source_head'] = OLD_HEAD
                stale['handoff'] = copy.deepcopy(OLD_HANDOFF)
            elif kind == 'retagged-old-handoff':
                stale['handoff'] = dict(OLD_HANDOFF, path=fresh.HANDOFF['path'])
            else:
                stale['handoff']['bytes'] += 1
            with self.subTest(kind=kind), self.assertRaises(fresh.FreshRunRefused):
                fresh.validate_authority(stale)

    def test_old_prepare_and_capacity_bindings_cannot_form_current_handoff(self):
        current = handoff()
        self.assertEqual(fresh.validate_handoff(current), current)
        for kind in ('old-prepare', 'wrong-prepare-bytes', 'old-capacity', 'old-source-role', 'old-profile-head', 'old-profile-tree'):
            stale = copy.deepcopy(current)
            if kind == 'old-prepare': stale['prepare_proposal'] = copy.deepcopy(OLD_PREPARE)
            elif kind == 'wrong-prepare-bytes': stale['prepare_proposal']['bytes'] += 1
            elif kind == 'old-capacity': stale['capacity_preview']['path'] = str(OLD / 'inspection-v1/capacity-preview-v1.json')
            elif kind == 'old-source-role': stale['source_root'] = str(Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/candidate-source-v1'))
            elif kind == 'old-profile-head': stale['source_head'] = OLD_HEAD
            else: stale['source_tree'] = OLD_TREE
            with self.subTest(kind=kind), self.assertRaises(fresh.FreshRunRefused):
                fresh.validate_handoff(stale)
        # Output generation does not change the prepare body by itself. If the
        # installed inputs made the old and current bodies identical, the exact
        # current binding is a valid data control, not borrowed authority.
        retagged = copy.deepcopy(current)
        retagged['prepare_proposal'] = dict(OLD_PREPARE, path=fresh.PREPARE_PIN['path'])
        if retagged['prepare_proposal'] == current['prepare_proposal']:
            self.assertEqual(fresh.validate_handoff(retagged), current)
        else:
            with self.assertRaises(fresh.FreshRunRefused): fresh.validate_handoff(retagged)
        self.assertIs(current['execution_authorized'], False)

    def test_parent_rejects_old_slot_and_old_nested_contract_even_after_retag(self):
        authority = parent_authority(); child = inner_authority(); authority_pin = pin(NEW / 'parent-authority-v1.json')
        api = SimpleNamespace(env=SimpleNamespace(check_binding=Mock()),
            probe=SimpleNamespace(_python_bindings=Mock(return_value={'fixture': 'python'})), fresh_rules=fresh)
        dispatched = Mock(side_effect=AssertionError('unexpected operation'))
        with patch.object(operation, '_parts', return_value=(outer, api)), \
             patch.object(operation, '_bootstrap', return_value={'python': {'fixture': 'python'}}), \
             patch.object(operation, '_invoke_fresh', dispatched):
            observed = Mock(side_effect=[authority, child])
            with patch.object(operation, 'read', observed):
                self.assertEqual(operation.read_authority(authority_pin), authority)
            self.assertEqual(observed.call_count, 2)
            for kind in ('old-parent-slot', 'retagged-contract', 'borrowed-approval', 'old-inner-source'):
                bad_parent, bad_child = copy.deepcopy(authority), copy.deepcopy(child)
                if kind == 'old-parent-slot': bad_parent['fresh_authority']['path'] = str(OLD / 'human-authority-v1.json')
                elif kind == 'retagged-contract': bad_child['contract']['sha256'] = OLD_CONTRACT_SHA
                elif kind == 'borrowed-approval': bad_child['approval_reference'] = 'UNRELATED SYNTHETIC REVIEW'
                else: bad_child['source_head'] = OLD_HEAD
                reads = Mock(side_effect=[bad_parent, bad_child])
                with self.subTest(kind=kind), patch.object(operation, 'read', reads):
                    with self.assertRaises((outer.OperationRefused, fresh.FreshRunRefused)):
                        operation.read_authority(authority_pin)
                self.assertEqual(reads.call_count, 1 if kind == 'old-parent-slot' else 2)
        self.assertEqual(dispatched.call_count, 0)
