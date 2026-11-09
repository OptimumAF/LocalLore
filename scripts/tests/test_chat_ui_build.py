"""Byte-backed host adversaries for the fixed B55 guard; no target operations.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from benchmarks import chat_ui_build as build
from scripts.tests.test_chat_ui_build_fixtures import BuildGraph, encoded, pin


class ChatUiBuildTests(unittest.TestCase):
    def setUp(self):
        self.graph = BuildGraph(build)
        self.stack = []
        for target, name, replacement in ((build, '_SPEC', self.graph.spec),
                (build, '_git', self.graph.git),
                (subprocess, 'run', self.forbidden), (subprocess, 'Popen', self.forbidden),
                (socket, 'socket', self.forbidden)):
            item=patch.object(target,name,replacement);item.start();self.stack.append(item)
        self.addCleanup(lambda:[item.stop() for item in reversed(self.stack)])

    @staticmethod
    def forbidden(*args, **kwargs):
        raise AssertionError('No process, SDK or socket operation in synthetic build replay')

    def test_complete_graph_replays_real_source_zip_xml_dex_elf_and_manifest(self):
        value=build.create_manifest()
        self.assertEqual((428,50),(value['jvm']['cases'],value['jvm']['suites']))
        self.assertEqual([list(row) for row in build.SELECTORS],value['roster'])
        self.assertFalse(value['recorded_execution']['historical_supervised_pipeline'])
        self.assertFalse(value['recorded_execution']['historical_inner_raw_aapt'])
        self.assertTrue(value['recorded_execution']['historical_full_raw_source_map'])
        path=Path(self.graph.spec['manifest'])
        self.assertFalse(path.exists(), 'Pure builder must not publish')
        self.graph.write(path,value)
        verified=build.verify_frozen_product(self.graph.artifacts())
        self.assertEqual(value,verified)
        verified['apks']['product_apk']['package']='caller mutation'
        self.assertEqual(build.APP,value['apks']['product_apk']['package'])

    def test_current_source_drift_refuses_even_when_git_metadata_is_unchanged(self):
        self.graph.write(self.graph.root/'README.md',b'Changed current raw source\n')
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_undocumented_code_delta_cannot_borrow_docs_only_attribution(self):
        name='scripts/audit_apk.py'
        row=next(v for v in self.graph.before['files'] if v['path']==name)
        row['sha256']='a'*64
        self.graph.write(self.graph.capture/'source-before-v1.json',self.graph.before)
        self.graph.publish()
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_source_roster_count_and_bool_head_count_are_not_metadata_overrides(self):
        self.graph.final['trackedFiles']=True
        self.graph.write(self.graph.capture/'final-source-verification-v1.json',self.graph.final)
        self.graph.publish()
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_canonical_archive_wrong_member_bytes_refuses_after_resealing(self):
        import zipfile
        path=Path(self.graph.spec['tested_archive']['path'])
        with zipfile.ZipFile(path,'w') as z:
            z.comment=self.graph.spec['tested_head'].encode()
            z.writestr('README.md',b'Wrong canonical content')
        self.graph.spec['tested_archive']=pin(path)
        self.graph.before['canonicalSourceZip']=pin(path)
        self.graph.write(self.graph.capture/'source-before-v1.json',self.graph.before)
        self.graph.publish()
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_all_xml_descendant_failure_error_skip_outcomes_refuse_zero_headers(self):
        path=Path(self.graph.reports[0]['original']['path'])
        baseline=path.read_bytes()
        for tag in ('failure','error','skipped'):
            # Each invalid XML is an independently retained file as well as the
            # current coherent copied report used by the real full validator.
            root=ET.fromstring(baseline)
            wrapper=ET.SubElement(root,'unexpected-wrapper')
            ET.SubElement(wrapper,tag)
            raw=ET.tostring(root)
            self.graph.write(self.graph.base/('negative-'+tag+'.xml'),raw)
            self.graph.write(path,raw)
            copied=Path(self.graph.reports[0]['copy']['path']);self.graph.write(copied,raw)
            self.graph.reports[0]=dict(original=pin(path),copy=pin(copied))
            self.graph.publish()
            with self.subTest(tag=tag),self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_nested_suite_and_duplicate_test_identity_are_refused_by_real_xml_parser(self):
        good=b'<testsuite name="X" tests="1" failures="0" errors="0" skipped="0"><testcase classname="X" name="a"/></testsuite>'
        self.assertEqual([('X','a')],build._cases(good))
        for raw in (good.replace(b'</testsuite>',b'<testsuite name="hidden"/></testsuite>'),
                    good.replace(b'tests="1"',b'tests="2"').replace(b'</testsuite>',b'<testcase classname="X" name="a"/></testsuite>')):
            with self.assertRaises(build.BuildRefused):build._cases(raw)

    def test_pair_audit_wrong_certificate_refuses_even_when_raw_log_and_receipt_agree(self):
        self.graph.pair['certificate_sha256']='a'*64
        self.graph.publish()
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_archive_package_retag_cannot_turn_an_ordinary_pair_into_another_profile(self):
        self.graph.pair['package']=build.APP+'.archiveverify'
        self.graph.pair['test_package']=build.APP+'.archiveverify.test'
        self.graph.publish()
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def refresh_test(self):
        path=self.graph.apks['test_apk']
        self.graph.apk(path,self.graph.class_definitions)
        self.graph.spec['apks']['test_apk']=pin(path)
        self.graph.pair['test']={k:pin(path)[k] for k in ('bytes','sha256')}
        copied=self.graph.capture/'apks-v1'/path.name
        self.graph.write(copied,path.read_bytes())
        self.graph.evidence['apkCopies'][1]=pin(copied)
        self.graph.publish()

    def test_missing_junit_definition_cannot_be_replaced_by_receipt_claims(self):
        first=next(iter(self.graph.class_definitions))
        flags,methods=self.graph.class_definitions[first]
        self.graph.class_definitions[first]=(flags,methods[1:])
        self.refresh_test()
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_swapped_method_definition_and_unannotated_method_are_not_string_evidence(self):
        first=next(iter(self.graph.class_definitions))
        flags,methods=self.graph.class_definitions[first]
        methods=list(methods)
        name,proto,access,_=methods[0]
        methods[0]=(name,proto,access,False)
        self.graph.class_definitions[first]=(flags,methods)
        self.refresh_test()
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_native_strip_chain_mismatch_is_not_excused_by_matching_release_copies(self):
        row=self.graph.evidence['nativeJoins'][0]
        path=Path(row['stripped']['path'])
        self.graph.write(path,b'Different stripped bytes')
        row['stripped']=pin(path)
        row['apkBytes']=pin(path)['bytes'];row['apkSHA256']=pin(path)['sha256']
        self.graph.publish()
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_old_sdk10_manifest_retag_and_extra_artifact_roles_refuse(self):
        value=build.create_manifest()
        path=Path(self.graph.spec['manifest'])
        for scope in ('transcript-ui-build-v1',build.SCOPE):
            old=copy.deepcopy(value);old['scope']=scope
            if scope==build.SCOPE:old['roster'][0][0]='transcript_history'
            self.graph.write(path,old)
            with self.subTest(scope=scope),self.assertRaises(build.BuildRefused):
                build.verify_frozen_product(self.graph.artifacts())
        self.graph.write(path,value)
        artifacts=self.graph.artifacts();artifacts['model']=copy.deepcopy(artifacts['test_apk'])
        with self.assertRaises(build.BuildRefused):build.verify_frozen_product(artifacts)

    def test_reader_rejects_bound_file_drift_duplicate_json_and_hardlink(self):
        path=self.graph.base/'bound.json';self.graph.write(path,dict(version=1))
        reader=build._Reader();reader.pin(path)
        self.graph.write(path,dict(version=2))
        with self.assertRaises(build.BuildRefused):reader.final()
        with self.assertRaises(build.BuildRefused):build._json(b'{"v":1,"v":2}')
        import os
        link=self.graph.base/'alias.json';os.link(path,link)
        with self.assertRaises(build.BuildRefused):build._Reader().raw(link)

    def test_only_fixed_cargo_release_aliases_admit_stable_read_only_hardlinks(self):
        import os
        release=Path(self.graph.evidence['nativeJoins'][0]['release']['path'])
        self.assertEqual(2,release.stat().st_nlink)
        with self.assertRaises(build.BuildRefused):build._Reader().bound(pin(release))
        self.assertEqual(2,len(build.create_manifest()['native_chains']))
        generated=Path(self.graph.evidence['nativeJoins'][0]['generated']['path'])
        os.link(generated,self.graph.base/'unapproved-generated-alias.so')
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_third_cargo_alias_refuses_even_when_the_fixed_two_names_still_match(self):
        import os
        release=Path(self.graph.evidence['nativeJoins'][0]['release']['path'])
        os.link(release,self.graph.base/'third-retained-cargo-alias.so')
        self.assertEqual(3,release.stat().st_nlink)
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_foreign_two_link_alias_with_equal_bytes_is_not_cargo_object_identity(self):
        import os
        release=Path(self.graph.evidence['nativeJoins'][0]['release']['path'])
        alias=release.parent/'deps/liblocallore_android.so'
        alias.rename(self.graph.base/'retained-original-deps-alias.so')
        alias.write_bytes(release.read_bytes())
        os.link(alias,self.graph.base/'foreign-equal-bytes-alias.so')
        self.assertEqual(2,alias.stat().st_nlink)
        self.assertNotEqual(release.stat().st_ino,alias.stat().st_ino)
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_cargo_alias_disappearance_after_initial_read_refuses_final_check(self):
        release=Path(self.graph.evidence['nativeJoins'][0]['release']['path'])
        reader=build._Reader();reader.cargo_release(pin(release))
        (release.parent/'deps/liblocallore_android.so').rename(self.graph.base/'retained-late-alias.so')
        with self.assertRaises((build.BuildRefused,OSError)):reader.final()

    def test_source_apk_and_control_hardlinks_keep_generic_single_link_rule(self):
        import os
        paths=(self.graph.root/'README.md',self.graph.apks['product_apk'],self.graph.capture/'build-start-v1.json')
        for i,path in enumerate(paths):
            binding=pin(path);os.link(path,self.graph.base/('retained-generic-alias-%d'%i))
            with self.subTest(path=path.name),self.assertRaises(build.BuildRefused):build._Reader().bound(binding)

    def test_resealed_bad_terminal_and_unavailable_outcomes_never_become_pass(self):
        self.graph.terminal['exit']=True
        self.graph.write(self.graph.capture/'build-terminal-v1.json',self.graph.terminal)
        self.graph.publish()
        with self.assertRaises(build.BuildRefused):build.create_manifest()


if __name__ == '__main__':
    unittest.main()
