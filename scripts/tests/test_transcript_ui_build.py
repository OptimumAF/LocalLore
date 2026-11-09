"""B49 data-only guard regressions; tiny retained D fixtures, no SDK or target.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from benchmarks import transcript_ui_build as build


class TranscriptUiBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = Path(tempfile.mkdtemp(prefix='locallore-b49-build-', dir='D:/Dev/_Temp'))

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='case-', dir=self.directory))

    def file(self, name, raw=b'fixture'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    @staticmethod
    def pin(path):
        raw = path.read_bytes()
        return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    @staticmethod
    def xml(rows='<testcase classname="Fixture" name="case"/>', tests=1, failures=0):
        return (f'<testsuite name="Fixture" tests="{tests}" failures="{failures}" errors="0" skipped="0">'
                + rows + '</testsuite>').encode()

    def test_reader_accepts_small_ordinary_executable_suffix_and_rechecks_it(self):
        path = self.file('inert.exe', b'not executable code')
        reader = build._Reader()
        self.assertEqual(b'not executable code', reader.raw(path))
        reader.final()

    def test_reader_rejects_content_drift_after_initial_pin(self):
        path = self.file('value.json', b'old')
        reader = build._Reader(); reader.pin(path)
        path.write_bytes(b'new')
        with self.assertRaises(build.BuildRefused): reader.final()

    def test_reader_refuses_hardlink_before_open_and_expired_deadline(self):
        original = self.file('ordinary.txt')
        link = self.root / 'linked.txt'; os.link(original, link)
        with self.assertRaises(build.BuildRefused): build._Reader().raw(link)
        reader = build._Reader(); reader.deadline = 0
        with self.assertRaises(build.BuildRefused): reader.raw(self.file('other.txt'))

    def test_binding_rejects_bool_integer_unknown_fields_and_wrong_digest(self):
        path = self.file('data'); valid = self.pin(path)
        for bad in [dict(valid, bytes=True), dict(valid, bytes=-1), dict(valid, sha256='0'*64),
                    dict(valid, callback='ignored'), dict(valid, path=3)]:
            with self.subTest(bad=bad), self.assertRaises(build.BuildRefused): build._Reader().bound(bad)

    def test_closed_json_refuses_duplicate_keys_nonfinite_and_bool_equivalence(self):
        for raw in [b'{"a":1,"a":2}', b'{"a":NaN}']:
            with self.assertRaises(build.BuildRefused): build._json(raw)
        self.assertFalse(build._same({'version':1}, {'version':True}))

    def test_relative_source_names_cannot_escape_or_hide_normalization(self):
        for name in ['../other', '/absolute', 'C:/project', 'a\\b', 'a//b', 'a/./b', 'a/../b', '']:
            with self.subTest(name=name), self.assertRaises(build.BuildRefused): build._relative(name)

    def test_git_uses_only_fixed_read_queries_and_product_root(self):
        answer = subprocess.CompletedProcess([], 0, b'head', b'')
        with patch.object(build.subprocess, 'run', return_value=answer) as run, patch.object(build, 'PRODUCT_ROOT', self.root):
            self.assertEqual(b'head', build._git(['rev-parse','HEAD']))
            argv = run.call_args.args[0]
            self.assertEqual(['git','--no-optional-locks','-C',str(self.root),'rev-parse','HEAD'], argv)
            with self.assertRaises(build.BuildRefused): build._git(['checkout','main'])
            self.assertEqual(1, run.call_count)

    def test_source_queries_bind_head_clean_status_and_current_raw_roster(self):
        path = self.file('source.kt', b'raw source\r\n')
        replies = {('rev-parse','HEAD'):b'head\n', ('status','--porcelain','--untracked-files=all'):b'',
                   ('ls-files','-z'):b'source.kt\0'}
        with patch.object(build,'PRODUCT_ROOT',self.root), patch.object(build,'PRODUCT_HEAD','head'), \
             patch.object(build,'_git',side_effect=lambda args:replies[tuple(args)]):
            self.assertEqual({'source.kt':self.pin(path)['sha256']}, build._source(build._Reader()))
            replies[('status','--porcelain','--untracked-files=all')] = b' M source.kt\n'
            with self.assertRaises(build.BuildRefused): build._source(build._Reader())

    def test_canonical_archive_checks_comment_roster_critical_bytes_and_duplicates(self):
        def archive(name, comment=b'head', members=None):
            path = self.root / name
            with zipfile.ZipFile(path,'w') as z:
                z.comment=comment
                for n,raw in members or [('source.kt',b'canonical')]: z.writestr(n,raw)
            return path
        good=archive('good.zip'); digest=hashlib.sha256(b'canonical').hexdigest()
        with patch.object(build,'PRODUCT_HEAD','head'), patch.object(build,'CRITICAL_SOURCES',{'source.kt':digest}):
            with patch.object(build,'ARCHIVE',self.pin(good)):
                self.assertEqual(1,build._archive(build._Reader(),{'source.kt':digest})['files'])
            for p in [archive('head.zip',b'wrong'), archive('path.zip',members=[('../source.kt',b'canonical')]),
                      archive('bytes.zip',members=[('source.kt',b'wrong')])]:
                with patch.object(build,'ARCHIVE',self.pin(p)), self.assertRaises(build.BuildRefused):
                    build._archive(build._Reader(),{'source.kt':digest})

    def test_xml_zero_headers_cannot_hide_outcomes_nested_cases_or_duplicates(self):
        bad = [self.xml('<testcase classname="Fixture" name="x"><failure/></testcase>'),
               self.xml('<testcase classname="Fixture" name="x"><skipped/></testcase>'),
               self.xml('<testcase classname="Fixture" name="x"/><testcase classname="Fixture" name="x"/>',2),
               self.xml('<testsuite name="hidden"><testcase classname="Fixture" name="x"/></testsuite>',0),
               self.xml('<testcase classname="Other" name="x"/>')]
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(build.BuildRefused): build._cases(raw)
        self.assertEqual([('Fixture','case')], build._cases(self.xml()))

    def test_xml_refuses_entities_and_first_failure_count_is_preserved(self):
        with self.assertRaises(build.BuildRefused): build._xml(b'<!DOCTYPE testsuite><testsuite/>')
        failed=self.xml('<testcase classname="Fixture" name="x"><failure/></testcase>',1,1)
        self.assertEqual([('Fixture','x')],build._cases(failed,1,1))
        with self.assertRaises(build.BuildRefused): build._cases(failed,1,0)

    def test_phase_freshness_allows_repeated_bare_headings_but_rejects_cached(self):
        raw=b'> Task :app:testDebugUnitTest\n> Task :app:testDebugUnitTest\nBUILD SUCCESSFUL\n'
        build._tasks(raw,('testDebugUnitTest',),'BUILD SUCCESSFUL')
        for bad in [raw.replace(b'UnitTest\n',b'UnitTest UP-TO-DATE\n',1), b'BUILD SUCCESSFUL\n',
                    raw.replace(b'UnitTest\n',b'UnitTest FROM-CACHE\n',1)]:
            with self.assertRaises(build.BuildRefused): build._tasks(bad,('testDebugUnitTest',),'BUILD SUCCESSFUL')

    def test_phases_keep_host_compile_and_apk_packaging_as_separate_evidence(self):
        def log(tasks,ending): return ('\n'.join('> Task :app:'+n for n in tasks)+'\n'+ending).encode()
        records={'full-android-host-v1.log':log(['testDebugUnitTest','compileDebugAndroidTestKotlin','lintAnalyzeDebug','lintReportDebug','lintDebug'],'BUILD SUCCESSFUL in 53s'),
                 'focused-green-v1.log':log(['compileDebugKotlin','testDebugUnitTest'],'BUILD SUCCESSFUL in 33s'),
                 'apk-build-v1.log':log(['buildRustAndroid','compileDebugKotlin UP-TO-DATE','compileDebugAndroidTestKotlin UP-TO-DATE','packageDebug','assembleDebug','packageDebugAndroidTest','assembleDebugAndroidTest'],'BUILD SUCCESSFUL in 2m 50s'),
                 'first-jvm-v1.log':b'9 tests completed, 6 failed\nBUILD FAILED in 47s'}
        build._phases(records)
        records['full-android-host-v1.log']=records['full-android-host-v1.log'].replace(b'UnitTest\n',b'UnitTest UP-TO-DATE\n')
        with self.assertRaises(build.BuildRefused): build._phases(records)

    def test_artifacts_are_exact_fixed_roles_paths_and_original_apk_pins(self):
        good=dict(build=dict(path=str(build.MANIFEST_PATH),bytes=1,sha256='a'*64),**copy.deepcopy(build.APK_BINDINGS))
        build._artifacts(good)
        bad=[]
        bad.append(dict(good,controller_apk=good['test_apk']))
        bad.append(dict(good,model=good['test_apk']))
        bad.append(dict(good,build=dict(good['build'],path=str(self.root/'elsewhere.json'))))
        bad.append(dict(good,product_apk=dict(good['product_apk'],sha256='b'*64)))
        bad.append(dict(good,test_apk=dict(good['test_apk'],bytes=True)))
        for value in bad:
            with self.assertRaises(build.BuildRefused): build._artifacts(value)

    def test_manifest_verifier_compares_whole_graph_and_keeps_return_detached(self):
        path=self.file('build.json',b'{"version":1,"scope":"fixture","apks":{}}')
        expected={'version':1,'scope':'fixture','apks':{}}
        artifacts=dict(build=self.pin(path),**copy.deepcopy(build.APK_BINDINGS))
        # File/graph equality is real; only the expensive fixed product replay and
        # two already-bound APK reads are IO seams in this small host test.
        real=build._Reader.bound
        def bound(reader,pin,cap=64*1024**2):
            return real(reader,pin,cap) if pin['path']==str(path) else b''
        with patch.object(build,'MANIFEST_PATH',path), patch.object(build,'create_manifest',return_value=expected), \
             patch.object(build._Reader,'bound',bound):
            actual=build.verify_frozen_product(artifacts);actual['apks']['caller']='changed'
            self.assertEqual({},expected['apks'])
            expected['version']=True
            with self.assertRaises(build.BuildRefused): build.verify_frozen_product(artifacts)

    def test_selector_roster_is_fixed_two_plus_four_and_distinct_claims(self):
        self.assertEqual(6,len(build.SELECTORS))
        self.assertEqual(6,len({r[0] for r in build.SELECTORS}))
        self.assertEqual(4,sum(r[1]=='org.locallore.app.TranscriptFollowScreenTest' for r in build.SELECTORS))
        self.assertEqual(2,sum(r[1]=='org.locallore.app.ui.TranscriptRolloverUiTest' for r in build.SELECTORS))
        self.assertEqual({'product_apk','test_apk'},set(build.APK_BINDINGS))

    def test_packaging_requires_real_public_instance_junit_definition_not_string_reference(self):
        from scripts import audit_physical_model_apk as physical
        descriptor=b'Lorg/locallore/app/ui/TranscriptRolloverUiTest;'
        name='realCase';path=self.file('apps/android/app/src/androidTest/java/org/locallore/app/ui/TranscriptRolloverUiTest.kt',
            b'package org.locallore.app.ui\nclass TranscriptRolloverUiTest { @Test fun realCase() {} }')
        valid={descriptor:(1,[(name.encode(),(b'V',0),1,True)])}
        choices=[{}, {descriptor:(1,[])}, {descriptor:(1,[(name.encode(),(b'V',0),9,True)])},
                 {descriptor:(1,[(name.encode(),(b'V',0),1,False)])},
                 {descriptor:(1,[(name.encode(),(b'V',1),1,True)])},
                 {descriptor:(1,valid[descriptor][1]*2)}]
        with patch.object(build,'PRODUCT_ROOT',self.root), patch.object(build,'SELECTORS',(('claim','org.locallore.app.ui.TranscriptRolloverUiTest',name),)):
            with patch.object(physical,'dex_classes',side_effect=[{},valid]): build._selectors(build._Reader())
            for invalid in choices:
                with patch.object(physical,'dex_classes',side_effect=[{},invalid]),self.assertRaises(build.BuildRefused):
                    build._selectors(build._Reader())
            with patch.object(physical,'dex_classes',side_effect=[valid,valid]),self.assertRaises(build.BuildRefused):
                build._selectors(build._Reader())

    def audit_fixture(self):
        apk_bindings={}
        preserved=[]
        for role,name in [('product_apk','app-debug.apk'),('test_apk','app-debug-androidTest.apk')]:
            original=self.file('original/'+name,b'inert '+role.encode())
            copied=self.file('recovery/apks/'+name,original.read_bytes())
            binding=self.pin(original);apk_bindings[role]=binding
            preserved.append(dict(source=str(original),copy=str(copied),bytes=binding['bytes'],sha256=binding['sha256']))
        pair=dict(status='passed',package=build.APP,test_package=build.APP+'.test',
            test_permissions=['android.permission.REORDER_TASKS'],certificate_sha256=build.CERTIFICATE,
            app={k:apk_bindings['product_apk'][k] for k in ['bytes','sha256']},
            test={k:apk_bindings['test_apk'][k] for k in ['bytes','sha256']})
        product=dict(status='passed',permissions=[build.APP+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'],
            libraries=[dict(entry=f'lib/{abi}/{name}',elf_load_alignment=[16384]*3)
                for abi in ['arm64-v8a','x86_64'] for name in ['liblocallore_android.so','libandroidx.graphics.path.so']])
        return apk_bindings,preserved,pair,product

    def test_ordinary_audit_positive_binds_both_copies_packages_certificate_and_four_libraries(self):
        bindings,preserved,pair,product=self.audit_fixture()
        records={'pair-audit-v1.json':json.dumps(pair).encode(),'product-audit-v1.json':json.dumps(product).encode()}
        with patch.object(build,'APK_BINDINGS',bindings),patch.object(build,'RECOVERY',self.root/'recovery'):
            value=build._audits(build._Reader(),records,dict(copied_files=preserved))
        self.assertEqual({'product_apk','test_apk'},set(value))
        self.assertEqual(build.APP,value['product_apk']['package'])
        self.assertEqual(build.CERTIFICATE,value['test_apk']['certificate_sha256'])

    def test_success_category_cannot_hide_wrong_package_signer_apk_or_permissions(self):
        bindings,preserved,pair,product=self.audit_fixture()
        bad_pairs=[dict(pair,package='org.locallore.app.archiveverify'),dict(pair,certificate_sha256='0'*64),
            dict(pair,test_permissions=[]),dict(pair,app=dict(pair['app'],bytes=True)),
            dict(pair,test=dict(pair['test'],sha256='0'*64)),dict(pair,callback='ignored')]
        with patch.object(build,'APK_BINDINGS',bindings),patch.object(build,'RECOVERY',self.root/'recovery'):
            for bad in bad_pairs:
                records={'pair-audit-v1.json':json.dumps(bad).encode(),'product-audit-v1.json':json.dumps(product).encode()}
                with self.subTest(bad=bad),self.assertRaises(build.BuildRefused):
                    build._audits(build._Reader(),records,dict(copied_files=preserved))
            product['libraries'][0]['elf_load_alignment']=[4096]
            with self.assertRaises(build.BuildRefused):
                build._audits(build._Reader(),{'pair-audit-v1.json':json.dumps(pair).encode(),
                    'product-audit-v1.json':json.dumps(product).encode()},dict(copied_files=preserved))

    def test_parser_body_compatibility_allows_unrelated_profile_text_but_rejects_changed_decoder(self):
        product=self.root/'product';launcher=self.root/'launcher'
        for parent,extra in [(product,''),(launcher,'\nNEW_UNRELATED_PROFILE=True\n')]:
            for name,raw in [('scripts/audit_physical_model_apk.py','class Dex: pass\ndef dex_classes(path): return {}\n'+extra),
                             ('scripts/audit_apk.py','def require(condition, reason):\n if not condition: raise ValueError(reason)\n'+extra),
                             ('benchmarks/android_instrumentation_evidence.py','def test_roster(path): return []\n')]:
                p=parent/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(raw)
        with patch.object(build,'PRODUCT_ROOT',product),patch.object(build,'ROOT',launcher):
            self.assertEqual(3,len(build._helpers(build._Reader())))
            (launcher/'scripts/audit_physical_model_apk.py').write_text('class Dex: pass\ndef dex_classes(path): return {"forged":1}\n')
            with self.assertRaises(build.BuildRefused):build._helpers(build._Reader())

    def report_fixture(self):
        product=self.root/'product';capture=self.root/'capture';rows=[];reports={}
        classes=[('org.locallore.app.TranscriptRolloverTest',[f'rollover{i}' for i in range(9)]),
                 ('org.locallore.app.TranscriptFollowTest',[f'follow{i}' for i in range(8)])]
        classes +=[(f'Other{i}',[f'case{j}' for j in range(9 if i<35 else 8)]) for i in range(46)]
        for klass,methods in classes:
            raw=('<testsuite name="'+klass+'" tests="'+str(len(methods))+'" failures="0" errors="0" skipped="0">'+
                ''.join(f'<testcase classname="{klass}" name="{m}"/>' for m in methods)+'</testsuite>').encode()
            path=product/'apps/android/app/build/test-results/testDebugUnitTest'/('TEST-'+klass+'.xml')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);reports[klass]=raw
            target=capture/'host-reports-v1'/path.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            pin=self.pin(path);rows.append(dict(source=str(path),copy=str(target),bytes=pin['bytes'],sha256=pin['sha256']))
            if klass.startswith('org.locallore.app.'):
                name=klass.rsplit('.',1)[1];source=product/'apps/android/app/src/test/java/org/locallore/app'/(name+'.kt')
                source.parent.mkdir(parents=True,exist_ok=True)
                source.write_text('class '+name+' {\n'+'\n'.join('@Test fun '+m+'() {}' for m in methods)+'\n}')
        for rel,raw in [('reports/lint-results-debug.xml',b'<issues><issue id="GradleDependency" severity="Warning"/><issue id="AutoboxingStateCreation" severity="Hint"/></issues>'),
                        ('tmp/kotlin-classes/debugAndroidTest/org/locallore/app/ui/TranscriptRolloverUiTest.class',b'\xca\xfe\xba\xbeinert')]:
            path=product/'apps/android/app/build'/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            target=capture/'host-reports-v1'/path.name;target.write_bytes(raw);pin=self.pin(path)
            rows.append(dict(source=str(path),copy=str(target),bytes=pin['bytes'],sha256=pin['sha256']))
        first=reports['org.locallore.app.TranscriptRolloverTest'].replace(b'failures="0"',b'failures="6"')
        first=first.replace(b'/>',b'><failure/></testcase>',6)
        records={'FIRST-TranscriptRolloverTest-v1.xml':first,
            'GREEN-TranscriptRolloverTest-v1.xml':reports['org.locallore.app.TranscriptRolloverTest'],
            'GREEN-TranscriptFollowTest-v1.xml':reports['org.locallore.app.TranscriptFollowTest']}
        return product,capture,rows,records

    def test_complete_ordinary_report_graph_recounts_420_cases_and_exact_48_suites(self):
        product,capture,rows,records=self.report_fixture()
        with patch.object(build,'PRODUCT_ROOT',product),patch.object(build,'CAPTURE',capture):
            actual=build._reports(build._Reader(),rows,records)
            self.assertEqual((420,48),(actual['cases'],actual['suites']))
            self.assertEqual(50,len(actual['reports']))
            with self.assertRaises(build.BuildRefused):build._reports(build._Reader(),rows[:-1],records)

    def test_report_graph_refuses_hidden_failure_even_with_rebound_matching_copies(self):
        product,capture,rows,records=self.report_fixture()
        row=next(r for r in rows if Path(r['source']).name=='TEST-Other0.xml')
        changed=Path(row['source']).read_bytes().replace(b'/>',b'><failure/></testcase>',1)
        for field in ['source','copy']:Path(row[field]).write_bytes(changed)
        row.update(bytes=len(changed),sha256=hashlib.sha256(changed).hexdigest())
        with patch.object(build,'PRODUCT_ROOT',product),patch.object(build,'CAPTURE',capture),self.assertRaises(build.BuildRefused):
            build._reports(build._Reader(),rows,records)


if __name__ == '__main__':
    unittest.main()
