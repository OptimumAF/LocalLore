# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""FIRST record UI build guards over genuine synthetic DEX and bound raw files."""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

from benchmarks import record_ui_build as build
from benchmarks import archive_ui_build as old_build
from benchmarks import owned_record_ui_owner as owner
from benchmarks import owned_target_owner as native
from scripts.tests import test_audit_physical_model_apk as dex
from scripts.tests import test_record_ui_fixtures as f


@unittest.skipUnless(os.name == 'nt', 'Physical-D byte graph fixtures')
class RecordUiBuildTests(unittest.TestCase):
    def setUp(self):
        self.graph = f.BuildGraph()
        self.context = self.graph.inputs(build)
        self.context.__enter__(); self.addCleanup(self.context.__exit__, None, None, None)

    def test_complete_380_case_43_report_graph_accepts_real_dex_without_any_tool_execution(self):
        with patch('subprocess.Popen', side_effect=AssertionError('tool execution')):
            actual = build.make_manifest(self.graph.public)
            self.assertEqual(actual, self.graph.manifest)
            self.assertEqual(build.verify_current(self.graph.admission()), actual)
            output = self.graph.base / 'create-only-build.json'
            written = build.write_manifest(self.graph.public, output)
            self.assertEqual(written, f.pin(output))
            with self.assertRaises(FileExistsError): build.write_manifest(self.graph.public, output)
        self.assertEqual(actual['scope'], 'record-ui-build-v1')
        self.assertEqual(len(actual['jvm_reports']), 43)
        self.assertEqual(sum(len(ET.fromstring(Path(row['path']).read_bytes())) for row in actual['jvm_reports']), 380)
        self.assertEqual(actual['roster'], [list(row) for row in f.INSTRUMENTATIONS])
        self.assertEqual(tuple(build.QUERY2_POLICY_METHODS), f.QUERY_METHODS)

    def test_selector_must_be_a_public_concrete_nonstatic_junit_definition_and_absent_product(self):
        original = copy.deepcopy(self.graph.definitions)
        descriptor = next(iter(original))
        for fault in ('missing', 'annotation', 'abstract', 'static', 'product'):
            self.graph.definitions = copy.deepcopy(original)
            flags, methods = self.graph.definitions[descriptor]
            if fault == 'missing': del self.graph.definitions[descriptor]
            elif fault == 'annotation': self.graph.definitions[descriptor] = (flags, [(n, p, m, False) for n, p, m, _ in methods])
            elif fault == 'abstract': self.graph.definitions[descriptor] = (flags | 0x400, methods)
            elif fault == 'static': self.graph.definitions[descriptor] = (flags, [(n, p, m | 8, a) for n, p, m, a in methods])
            self.graph.write_apks()
            if fault == 'product':
                with zipfile.ZipFile(self.graph.apks['product_apk'], 'w') as stream:
                    stream.writestr('classes.dex', dex.dex(original))
            self.graph.publish()
            with self.subTest(fault=fault), self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())

    def test_xml_nested_outcomes_duplicate_ids_and_missing_exact_query2_policy_cannot_hide(self):
        path = next(path for path in self.graph.reports if 'Query2StoryRecordTest' in path.name)
        original = path.read_bytes()
        for fault in ('failure', 'error', 'skipped', 'duplicate', 'missing-policy', 'suite'):
            tree = ET.fromstring(original)
            if fault in ('failure', 'error', 'skipped'): ET.SubElement(ET.SubElement(tree[0], 'wrapper'), fault)
            elif fault == 'duplicate': tree[1].attrib.update(tree[0].attrib)
            elif fault == 'missing-policy': tree[0].set('name', 'notTheFrozenQuery2Case')
            else: tree[0].set('classname', 'unrelated.Class')
            path.write_bytes(ET.tostring(tree)); self.graph.publish()
            with self.subTest(fault=fault), self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        path.write_bytes(original)

    def test_fresh_task_rows_are_required_while_repeated_bare_headings_are_legitimate(self):
        tasks = f.previous_builds.EXECUTED_TASKS
        for fault in ('missing', 'up-to-date', 'cache'):
            changed = tuple(row for row in tasks if row != 'testDebugUnitTest')
            if fault != 'missing': changed += ('testDebugUnitTest ' + ('UP-TO-DATE' if fault == 'up-to-date' else 'FROM-CACHE'),)
            self.graph.publish(tasks=changed)
            with self.subTest(fault=fault), self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        self.graph.publish(tasks=tasks + ('compileDebugAndroidTestKotlin',))
        self.assertEqual(build.verify_current(self.graph.admission()), self.graph.manifest)
        commands = self.graph.commands(); commands[0].remove(':app:testDebugUnitTest')
        self.graph.publish(commands=commands)
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())

    def test_current_source_head_tool_bytes_and_apk_roles_cannot_be_borrowed_or_rebound(self):
        self.graph.head = 'b' * 40
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        self.graph.head = 'a' * 40
        source = self.graph.source_paths[0]; raw = source.read_bytes(); source.write_bytes(raw + b'// changed\n')
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        source.write_bytes(raw)
        tool = Path(self.graph.tools[0]['path']); raw = tool.read_bytes(); tool.write_bytes(raw + b'changed')
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        tool.write_bytes(raw)
        admission = self.graph.admission(); admission['artifacts']['product_apk'] = copy.deepcopy(admission['artifacts']['test_apk'])
        with self.assertRaises(build.BuildRefused): build.verify_current(admission)

    def test_archive_scope_lint_errors_and_exit_zero_counters_do_not_qualify_a_record_build(self):
        with self.assertRaises(old_build.BuildRefused): old_build._verify_manifest(self.graph.manifest)
        value = copy.deepcopy(self.graph.manifest); value['scope'] = 'archive-ui-build-v1'
        self.graph.write(self.graph.manifest_path, f.encoded(value))
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        self.graph.publish()
        self.graph.lint.write_bytes(b'<issues><issue severity="Error" id="Synthetic"/></issues>'); self.graph.publish()
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        self.graph.lint.write_bytes(b'<issues/>')
        for field, value in (('worker_returncode', False), ('stderr_bytes', False), ('stderr_bytes', 0.0), ('cleanup_complete', False)):
            original = copy.deepcopy(self.graph.result)
            self.graph.result['owner'][field] = value; self.graph.publish()
            with self.subTest(field=field, value=value), self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
            self.graph.result = original

    def test_stale_build_refuses_before_any_native_observer_constructor(self):
        path = self.graph.base / 'admission.json'; self.graph.write(path, f.encoded(self.graph.admission()))
        self.graph.head = 'b' * 40
        with patch.object(native._LiveOwnedTarget, '__init__', side_effect=AssertionError('native constructor')) as constructor:
            with self.assertRaises(build.BuildRefused): owner.LiveOwnedRecordUiTarget(f.pin(path), f.legacy.pin('D:/Synthetic/running.json'))
            constructor.assert_not_called()
