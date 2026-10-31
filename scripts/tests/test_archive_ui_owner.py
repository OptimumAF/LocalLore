"""Prelaunch refusal wiring only; injected failure cannot qualify a build or target."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import owned_ui_owner as owner
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as environment
from scripts.tests import test_archive_ui_fixtures as f


@unittest.skipUnless(os.name == 'nt', 'Windows owned-target prelaunch fixtures')
class ArchiveUiPrelaunchTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='locallore-ui-prelaunch-'))
        self.a = f.admission()
        self.path = self.root/'admission-v1.json'
        environment.create_json(self.path,self.a)
        self.binding = environment.binding(self.path)

    def test_parent_build_refusal_happens_before_parent_or_native_dispatch(self):
        output = io.StringIO()
        with patch.object(owner.build,'verify_current',side_effect=ValueError('synthetic rejected build')) as gate, \
             patch.object(mechanisms,'_parent',side_effect=AssertionError('must not launch')) as launch, \
             patch.object(mechanisms,'_ProcessApi',side_effect=AssertionError('must not open native handles')) as handles, \
             contextlib.redirect_stdout(output):
            code = owner.main(['--admission',str(self.path),'--admission-sha256',self.binding['sha256']])
        self.assertEqual(code,1); gate.assert_called_once_with(self.a)
        launch.assert_not_called(); handles.assert_not_called()
        value = json.loads(output.getvalue())
        self.assertFalse(value['qualified_target']); self.assertFalse(value['feature_acceptance'])
        self.assertNotIn('synthetic rejected build',output.getvalue())

    def test_worker_build_refusal_precedes_base_runtime_construction(self):
        request = {'validated_admission':self.a}
        with patch.object(owner.build,'verify_current',side_effect=ValueError('synthetic rejected build')) as gate, \
             patch.object(mechanisms._TargetRuntimeCore,'__init__',side_effect=AssertionError('native runtime must not start')) as base:
            with self.assertRaises(ValueError):
                owner._UiTargetRuntime(request,self.binding,self.root)
        gate.assert_called_once_with(self.a); base.assert_not_called()

    def test_independent_live_observer_build_refusal_precedes_native_base_and_rejects_subclass(self):
        with patch.object(owner.build,'verify_current',side_effect=ValueError('synthetic rejected build')) as gate, \
             patch.object(mechanisms._LiveOwnedTarget,'__init__',side_effect=AssertionError('native observer must not open')) as base:
            with self.assertRaises(ValueError): owner.LiveOwnedUiTarget(self.binding,f.legacy.pin(self.root/'running-v1.json'))
        gate.assert_called_once_with(self.a); base.assert_not_called()
        class Derived(owner.LiveOwnedUiTarget): pass
        with patch.object(owner.build,'verify_current',side_effect=AssertionError('wrong type before build')) as gate:
            with self.assertRaises(owner.OwnerRefused): Derived(self.binding,f.legacy.pin(self.root/'running-v1.json'))
        gate.assert_not_called()
