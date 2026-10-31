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

    def test_nested_failure_error_or_skip_inside_a_testcase_wrapper_cannot_hide_behind_zero_totals(self):
        path = self.graph.reports[1]
        original = path.read_bytes()
        for outcome in ('failure','error','skipped'):
            tree = ET.fromstring(original)
            wrapper = ET.SubElement(tree[0],'synthetic-wrapper')
            ET.SubElement(wrapper,outcome,message='SYNTHETIC outcome must not be hidden')
            path.write_bytes(ET.tostring(tree)); self.graph.publish()
            with self.subTest(outcome=outcome), self.assertRaises(build.BuildRefused):
                build._reports(self.graph.manifest['jvm_reports'],self.graph.manifest['lint'])

    def test_report_filename_suite_name_and_testcase_classname_must_identify_the_same_suite(self):
        for mismatch in ('suite_name','case_classname','filename'):
            graph = fixture.BuildGraph()
            path = graph.reports[1]
            tree = ET.fromstring(path.read_bytes())
            if mismatch == 'suite_name': tree.set('name','synthetic.Unrelated')
            elif mismatch == 'case_classname': tree[0].set('classname','synthetic.Unrelated')
            else:
                moved = path.with_name('TEST-synthetic.Unrelated.xml')
                path.rename(moved); graph.reports[1] = moved; path = moved
            path.write_bytes(ET.tostring(tree)); graph.publish()
            with graph.inputs(build), self.subTest(mismatch=mismatch), self.assertRaises(build.BuildRefused):
                build._reports(graph.manifest['jvm_reports'],graph.manifest['lint'])

    def test_missing_or_up_to_date_critical_gradle_tasks_cannot_be_replaced_by_success_text(self):
        for task in ('buildRustAndroid','testDebugUnitTest','lintAnalyzeDebug','compileDebugAndroidTestKotlin'):
            for state in ('missing','UP-TO-DATE'):
                tasks = [name for name in fixture.EXECUTED_TASKS if name != task]
                if state != 'missing': tasks.append(task+' '+state)
                self.graph.publish(tasks=tasks)
                with self.subTest(task=task,state=state), self.assertRaises(build.BuildRefused):
                    build._public(self.graph.manifest['public'],self.graph.head)

    def test_repeated_bare_compile_heading_around_warning_is_valid_fresh_task_output(self):
        # Real successful captures repeat this bare heading around the compiler warning:
        # B23 stdout SHA256 727a0bf253255f2295257d9cb4f002749a0847fac0cf9b6d238edee26bc0a976, lines175/184;
        # B24 stdout SHA256 98242afb94a3307e2e66f6aba72aa7ba3c8f52b32e2c54d9246264aa2e6ed6af, lines178/184.
        self.graph.publish(tasks=fixture.EXECUTED_TASKS+('compileDebugAndroidTestKotlin',))
        path = self.graph.public/'owner-stdout-v1.bin'
        raw = path.read_bytes()
        heading = b'> Task :app:compileDebugAndroidTestKotlin\n'
        self.assertEqual(raw.count(heading),2)
        before, after = raw.rsplit(heading,1)
        warning = (b'w: file:///D:/Synthetic/LocalLore/apps/android/app/src/androidTest/java/'
                   b'org/locallore/app/FrameworkInterruptionTest.kt:128:50 This call may have inconsistent results '
                   b"because 'AtomicReference' uses identity equality and 'Boolean?' does not have a consistent identity. "
                   b"Consider using 'AtomicBoolean' instead.\n")
        raw = before+heading+warning+after
        path.write_bytes(raw)
        self.graph.result['owner']['stdout_bytes'] = len(raw)
        result_path = self.graph.public/'result-v1.json'
        result_path.write_bytes(fixture.encoded(self.graph.result))
        self.graph.manifest['public']['stdout'] = fixture.pin(path)
        self.graph.manifest['public']['result'] = fixture.pin(result_path)
        try:
            accepted = build._public(self.graph.manifest['public'],self.graph.head)
        except build.BuildRefused as error:
            self.fail('Repeated bare executed heading refused: '+str(error))
        self.assertEqual(accepted,self.graph.pair)
