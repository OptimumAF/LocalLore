"""Actual byte guards, XML rosters and genuine DEX decoding over synthetic D inputs."""
import copy
import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from benchmarks import archive_ui_build as build
from scripts.tests import test_archive_ui_build_fixtures as fixture


@unittest.skipUnless(os.name == 'nt', 'D-only current-build fixtures')
class ArchiveUiBuildTests(unittest.TestCase):
    def setUp(self):
        self.graph = fixture.BuildGraph()
        self.context = self.graph.inputs(build)
        self.context.__enter__(); self.addCleanup(self.context.__exit__,None,None,None)

    def test_complete_byte_graph_with_genuine_junit_dex_accepts_without_tool_execution(self):
        try:
            actual = build.make_manifest(self.graph.public)
        except Exception as error:
            self.fail('Complete genuine-DEX fixture refused: '+type(error).__name__)
        self.assertEqual(actual,self.graph.manifest)
        verified = build.verify_current(self.graph.admission())
        self.assertEqual(verified,actual)
        verified['apks']['product_apk']['package'] = 'changed'
        self.assertEqual(self.graph.manifest['apks']['product_apk']['package'],'org.locallore.app.archiveverify')

    def test_same_named_public_dex_method_without_junit_annotation_is_not_a_selector(self):
        descriptor = next(iter(self.graph.definitions))
        flags,methods = self.graph.definitions[descriptor]
        self.graph.definitions[descriptor] = (flags,[(n,p,f,False) for n,p,f,a in methods])
        self.graph.write_apks(); self.graph.publish()
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())

    def test_missing_or_nonconcrete_selector_definition_refuses_genuine_dex(self):
        original = copy.deepcopy(self.graph.definitions)
        descriptor = next(iter(original))
        for variant in ('absent','abstract','static'):
            self.graph.definitions = copy.deepcopy(original)
            flags,methods = self.graph.definitions[descriptor]
            if variant == 'absent': del self.graph.definitions[descriptor]
            elif variant == 'abstract': self.graph.definitions[descriptor] = (flags|0x400,methods)
            else: self.graph.definitions[descriptor] = (flags,[(n,p,f|8,a) for n,p,f,a in methods])
            self.graph.write_apks(); self.graph.publish()
            with self.subTest(variant=variant), self.assertRaises(build.BuildRefused):
                build.verify_current(self.graph.admission())

    def test_xml_duplicates_skips_and_missing_required_policy_cases_cannot_be_rebound_to_pass(self):
        path = self.graph.reports[1]
        original = path.read_bytes()
        policy = self.graph.reports[0]; original_policy = policy.read_bytes()
        for variant in ('duplicate','skip','wrong_policy','count'):
            path.write_bytes(original); policy.write_bytes(original_policy)
            target = policy if variant == 'wrong_policy' else path
            tree = ET.fromstring(target.read_bytes())
            if variant == 'duplicate': tree[1].attrib.update(tree[0].attrib)
            elif variant == 'skip': ET.SubElement(tree[0],'skipped')
            elif variant == 'wrong_policy': tree[0].set('name','notTheRequiredOriginalCase')
            else: tree.set('tests',str(len(tree)+1))
            target.write_bytes(ET.tostring(tree)); self.graph.publish()
            with self.subTest(variant=variant), self.assertRaises(build.BuildRefused):
                build.verify_current(self.graph.admission())

    def test_lint_error_and_extra_or_moved_report_refuse(self):
        self.graph.lint.write_bytes(b'<issues><issue id="Synthetic" severity="Error"/></issues>')
        self.graph.publish()
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        self.graph.lint.write_bytes(b'<issues/>'); self.graph.publish()
        moved = self.graph.base/'borrowed-report.xml'
        moved.write_bytes(self.graph.reports[0].read_bytes())
        value = copy.deepcopy(self.graph.manifest); value['jvm_reports'][0] = fixture.pin(moved)
        self.graph.write(self.graph.manifest_path,fixture.encoded(value))
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())

    def test_source_head_tool_bytes_and_apk_role_pins_are_current(self):
        accepted = copy.deepcopy(self.graph.manifest)
        self.graph.head = 'b'*40
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        self.graph.head = accepted['head']
        tool = Path(self.graph.tools[0]['path']); original = tool.read_bytes()
        tool.write_bytes(original+b'changed')
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        tool.write_bytes(original)
        source = self.graph.source_paths[0]; raw = source.read_bytes(); source.write_bytes(raw+b'\n// changed\n')
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        source.write_bytes(raw)
        admission = self.graph.admission()
        admission['artifacts']['product_apk'] = copy.deepcopy(admission['artifacts']['test_apk'])
        with self.assertRaises(build.BuildRefused): build.verify_current(admission)

    def test_public_raw_commands_and_pair_package_cannot_be_replaced_by_exit_zero(self):
        commands = self.graph.commands(); commands[0].remove(':app:testDebugUnitTest')
        self.graph.publish(commands=commands)
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())
        self.graph.pair['package'] = 'org.locallore.app'
        self.graph.publish()
        with self.assertRaises(build.BuildRefused): build.verify_current(self.graph.admission())

    def test_public_owner_stream_counters_and_version_require_exact_integers(self):
        # Exercise the actual raw public replay in isolation so DEX adapter errors
        # cannot hide a counter/schema acceptance defect.
        for variant in ('stderr_bool','result_version_bool'):
            self.graph.result['owner']['stderr_bytes'] = False if variant == 'stderr_bool' else 0
            self.graph.result['version'] = True if variant == 'result_version_bool' else 1
            self.graph.publish()
            with self.subTest(variant=variant), self.assertRaises(build.BuildRefused):
                build._public(self.graph.manifest['public'],self.graph.head)
