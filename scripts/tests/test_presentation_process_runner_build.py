"""Independent admission adversaries over actual files and real Git metadata.

Only _SPEC is patched; no source/build/report/audit/signer verdict is replaced.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from benchmarks import presentation_process_build as build
from benchmarks import owned_presentation_process_owner as owner
from scripts.tests import test_presentation_process_runner_build_fixtures as f


@unittest.skipUnless(os.name == 'nt', 'Isolated physical D source/capture fixtures')
class PresentationProcessRunnerBuildTests(unittest.TestCase):
    def refused(self, graph):
        with patch.object(build, '_SPEC', graph.spec), self.assertRaises(build.BuildRefused):
            build.create_manifest()
        self.assertFalse(graph.spec['manifest_path'].exists())

    def test_complete_byte_backed_three_apk_graph_creates_one_manifest_and_replays_without_tools(self):
        graph = f.BuildGraph(build)
        with patch.object(build, '_SPEC', graph.spec):
            binding = build.create_manifest()
            actual = build.verify_frozen_product(graph.artifacts(build))
            self.assertEqual(binding, f.pin(graph.spec['manifest_path']))
            self.assertEqual(set(actual), {'version', 'scope', 'product_source', 'public_execution', 'apks'})
            self.assertEqual(actual['scope'], 'presentation-process-build-v1')
            self.assertEqual(actual['product_source']['head'], graph.spec['head'])
            self.assertEqual(set(actual['apks']), {'product_apk', 'test_apk', 'controller_apk'})
            self.assertEqual({row['certificate_sha256'] for row in actual['apks'].values()}, {f.SIGNER})
            original = graph.spec['manifest_path'].read_bytes()
            with self.assertRaises(build.BuildRefused):
                build.create_manifest()
            self.assertEqual(graph.spec['manifest_path'].read_bytes(), original)
            for missing in graph.artifacts(build):
                bad = graph.artifacts(build)
                del bad[missing]
                with self.subTest(missing=missing), self.assertRaises(build.BuildRefused):
                    build.verify_frozen_product(bad)
        self.assertEqual(len(graph.roster), 417)
        self.assertEqual(len(list(graph.reports.glob('TEST-*.xml'))), 48)

    def test_stale_tracked_sources_tool_bytes_and_original_capture_pins_refuse(self):
        for mutation in ('source', 'tool', 'capture', 'head'):
            graph = f.BuildGraph(build)
            if mutation == 'source':
                graph.proof_source.write_bytes(graph.proof_source.read_bytes() + b'// stale source\n')
            elif mutation == 'tool':
                graph.tool_paths[0].write_bytes(b'changed pinned tool')
            elif mutation == 'capture':
                (graph.capture / 'owner-stdout-v1.bin').write_bytes(b'substituted original stdout')
            else:
                graph.spec['head'] = '0' * 40
            with self.subTest(mutation=mutation):
                self.refused(graph)

    def test_wrong_profile_command_missing_or_cached_tasks_and_absent_fourth_gate_refuse(self):
        for mutation in ('old_package', 'missing_task', 'cached_task', 'missing_gate'):
            graph = f.BuildGraph(build)
            if mutation == 'old_package':
                graph.commands[1][-1] = '--archive-verification'
            elif mutation == 'missing_task':
                graph.gradle_lines.remove('> Task :app:testDebugUnitTest')
            elif mutation == 'cached_task':
                index = graph.gradle_lines.index('> Task :app:compileDebugAndroidTestKotlin')
                graph.gradle_lines[index] += ' UP-TO-DATE'
            else:
                graph.commands.pop()
                graph.audits.pop()
            graph.publish()
            with self.subTest(mutation=mutation):
                self.refused(graph)

    def test_three_signatures_cannot_be_disagreed_missing_or_multiple_even_with_current_pins(self):
        for role in ('product_apk', 'test_apk', 'controller_apk'):
            for outcome in ('different', 'missing', 'multiple'):
                graph = f.BuildGraph(build)
                if outcome == 'different':
                    graph.signer_outputs[role] = graph.signer_outputs[role].replace(f.SIGNER, 'b' * 64)
                elif outcome == 'missing':
                    graph.signer_outputs[role] = 'Number of signers: 1\n'
                else:
                    graph.signer_outputs[role] = graph.signer_outputs[role].replace('signers: 1', 'signers: 2')
                graph.publish()
                with self.subTest(role=role, outcome=outcome):
                    self.refused(graph)

    def test_xml_actual_outcomes_duplicates_and_missing_new_policy_methods_cannot_hide_in_totals(self):
        for mutation in ('failure', 'error', 'skipped', 'duplicate', 'renamed_policy', 'missing_report'):
            graph = f.BuildGraph(build)
            path = graph.reports / 'TEST-org.locallore.app.PresentationProcessProofTest.xml'
            tree = ET.fromstring(path.read_bytes())
            if mutation in ('failure', 'error', 'skipped'):
                ET.SubElement(tree.find('testcase'), mutation)
            elif mutation == 'duplicate':
                tree.findall('testcase')[1].set('name', tree.find('testcase').get('name'))
            elif mutation == 'renamed_policy':
                tree.find('testcase').set('name', 'unrelatedReplacementWithSameGlobalCount')
                graph.roster[0]['name'] = 'unrelatedReplacementWithSameGlobalCount'
                graph.publish()
            else:
                path.rename(graph.base / 'retained-missing-report.xml')
            if mutation != 'missing_report':
                path.write_bytes(ET.tostring(tree))
            with self.subTest(mutation=mutation):
                self.refused(graph)

    def test_nested_testcase_outcomes_are_refusals_even_when_headers_and_roster_claim_zero(self):
        for outcome in ('failure', 'error', 'skipped'):
            graph = f.BuildGraph(build)
            path = graph.reports / 'TEST-org.locallore.app.PresentationProcessProofTest.xml'
            tree = ET.fromstring(path.read_bytes())
            ET.SubElement(ET.SubElement(tree.find('testcase'), 'wrapper'), outcome)
            path.write_bytes(ET.tostring(tree))
            with self.subTest(outcome=outcome):
                self.refused(graph)

    def test_owner_join_cleanup_and_nested_independent_review_cannot_be_passed_label_only(self):
        for mutation in ('unknown_cleanup', 'wrong_child', 'review_loss', 'review_owner', 'review_keys', 'alignment'):
            graph = f.BuildGraph(build)
            if mutation == 'unknown_cleanup':
                graph.owner['cleanup_complete'] = False
            elif mutation == 'wrong_child':
                graph.actual_child['executable'] = 'D:/Synthetic/other-python.exe'
            elif mutation == 'review_loss':
                graph.closed['summary']['failures'] = 1
            elif mutation == 'review_owner':
                graph.closed['summary']['owner_elapsed_ms'] += 1
            elif mutation == 'review_keys':
                graph.closed['summary']['unexpected'] = True
            else:
                graph.audits[0]['libraries'][0]['elf_load_alignment'] = []
            graph.publish()
            with self.subTest(mutation=mutation):
                self.refused(graph)


if __name__ == '__main__':
    unittest.main()
