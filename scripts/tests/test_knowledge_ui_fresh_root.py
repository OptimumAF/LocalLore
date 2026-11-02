"""SDK16 fresh-root metadata oracles; no real profile, SDK or owner activity."""
from pathlib import Path, PureWindowsPath
import unittest
from unittest.mock import patch
from benchmarks import owned_knowledge_ui_contract as contract
from benchmarks import owned_knowledge_ui_owner as owner
from benchmarks import knowledge_ui_profile_build as build
from benchmarks import owned_library_ui_contract as sdk15
from benchmarks import owned_record_controls_ui_contract as sdk14
from scripts.tests import test_knowledge_ui_controller_fixtures as data

NEW = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1')
OLD = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1')


class KnowledgeUiFreshRootTests(unittest.TestCase):
    def test_sdk16_has_one_new_literal_and_older_profile_authorities_are_unchanged(self):
        self.assertEqual(contract.GUEST_ROOT,NEW)
        self.assertNotEqual(contract.GUEST_ROOT,OLD)
        self.assertEqual((sdk14.GUEST_ROOT,sdk15.GUEST_ROOT),(OLD,OLD))
        self.assertEqual((contract.CLIENT_VERSION,contract.SESSION_FILE),(16,'sdk-session-v16.json'))
        self.assertEqual(contract.CLAIM_KINDS,('knowledge_labels','knowledge_replaced','knowledge_remount','knowledge_text'))
        self.assertEqual(contract.INSTRUMENTATIONS,data.SELECTORS)

    def test_current_metadata_passes_without_io_but_old_sdk15_guest_cannot_be_adopted(self):
        good=data.admission();good['guest']['root']=str(NEW)
        with patch.object(Path,'open',side_effect=AssertionError('Metadata reader performed IO')), \
             patch.object(Path,'stat',side_effect=AssertionError('Metadata reader performed stat')):
            self.assertEqual(contract.validate_admission(good),good)
            bad=data.admission();bad['guest']['root']=str(OLD)
            with self.assertRaises(contract.TargetRefused):contract.validate_admission(bad)
        # No existence check or mkdir is made against NEW's production parent.

    def test_old_literal_refuses_before_build_freshness_native_owner_or_worker_dispatch(self):
        bad=data.admission();bad['guest']['root']=str(OLD);pin=data.legacy.pin('D:/Synthetic/never-read.json')
        with patch.object(owner.mechanisms,'_read_json',return_value=bad), \
             patch.object(owner,'_verify_build') as product, \
             patch.object(owner.mechanisms._LiveOwnedTarget,'__init__') as native, \
             patch.object(owner.mechanisms._TargetRuntimeCore,'__init__') as worker:
            with self.assertRaises(contract.TargetRefused):owner.LiveOwnedKnowledgeUiTarget(pin,pin)
            with self.assertRaises(contract.TargetRefused):owner._KnowledgeUiTargetRuntime({'validated_admission':bad},pin,None)
            product.assert_not_called();native.assert_not_called();worker.assert_not_called()
        with patch.object(build.contract,'revalidate_inputs') as fresh, \
             patch.object(build.build,'verify_frozen_product') as frozen:
            with self.assertRaises(contract.TargetRefused):build.verify_current(bad)
            fresh.assert_not_called();frozen.assert_not_called()


if __name__=='__main__':unittest.main()
