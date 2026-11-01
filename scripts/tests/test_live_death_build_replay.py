"""Original byte-backed SDK6 build metadata, never compiler/device evidence.

The only seam redirects source ROOT lookups to real tiny D fixture files. Real
closed readers, native ELF parser, XML parser and hash bindings are not replaced.
"""
from contextlib import ExitStack
import copy
import hashlib
import os
from pathlib import Path, PureWindowsPath
import struct
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from benchmarks import original_author_live_death_controller as live
from benchmarks import original_author_restart_controller as legacy
from benchmarks import owned_live_death_contract as c
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_owned_live_death_contract as profile


class ClosedLiveBuild:
    """Fresh synthetic source/tool/ELF/XML bytes; no installed SDK is consulted."""
    def __init__(self, *, tests=600, reports=59, scope='owned_live_death_android_build_admission_v1'):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-live-build-', dir='D:/Dev/_Temp')).resolve()
        self.root, self.output = self.base/'source', self.base/'build'
        self.a = profile.admission()
        for name in c.SOURCE_NAMES:
            self.save(self.root/'benchmarks'/name, ('# Synthetic source bytes: '+name+'\n').encode())
        self.save(self.root/'benchmarks/native/android_author_process_probe.c', b'/* Synthetic source, never compiled. */\n')
        self.save(self.root/'scripts/build_android_author_process_probe.py', b'# Synthetic builder bytes, never executed.\n')
        self.save(self.root/'README.md', b'Synthetic closed-build metadata only.\n')
        self.a['sources'] = [env.binding(self.root/'benchmarks'/name) for name in sorted(c.SOURCE_NAMES)]
        by_name = {PureWindowsPath(pin['path']).name: pin for pin in self.a['sources']}
        self.a['server']['sources'] = [copy.deepcopy(by_name[PureWindowsPath(pin['path']).name])
                                      for pin in self.a['server']['sources']]
        self.a['artifacts']['process_probe_source'] = env.binding(self.root/'benchmarks/native/android_author_process_probe.c')
        self.mapping = {p.relative_to(self.root).as_posix(): env.digest(p)
                        for p in sorted(self.root.rglob('*')) if p.is_file()}
        self.native_root = self.base/'native'
        native_pin = self.native()
        self.summary, self.suites, files = [], {}, {}
        remaining = tests
        for index in range(reports):
            count = remaining if index == reports-1 else min(10, remaining)
            remaining -= count
            classname = 'org.locallore.synthetic.BuildCase%02d' % index
            name = 'TEST-'+classname+'.xml'
            suite = ET.Element('testsuite', name=classname, tests=str(count), failures='0', errors='0', skipped='0')
            for method in range(count):
                ET.SubElement(suite, 'testcase', classname=classname, name='originalCase%03d' % method)
            self.suites[name] = suite
            self.summary.append(dict(name=name, tests=count, failures=0, errors=0, skipped=0))
            files['reports/'+name] = self.save(self.output/'reports'/name, ET.tostring(suite))
        sources = self.save(self.output/'sources.json', self.mapping)
        compiled = self.save(self.output/'compiled.json', legacy._compiled_sources(self.mapping))
        files.update({
            'request-v1.json': self.save(self.output/'request-v1.json', dict(sources=self.mapping)),
            'sources-before-v1.json': self.save(self.output/'sources-before-v1.json', self.mapping),
            'sources-after-v1.json': self.save(self.output/'sources-after-v1.json', self.mapping),
            'result-v1.json': self.save(self.output/'result-v1.json', dict(passed=True, sources_equal=True,
                status='child_exited', worker_returncode=0, cleanup_complete=True, output_capture_complete=True,
                synthetic_only=True)),
            'test-summary-v1.json': self.save(self.output/'test-summary-v1.json', self.summary),
        })
        lint = {name: files[name] for name in ('request-v1.json', 'sources-after-v1.json', 'result-v1.json')}
        lint['litert-analyzer-audit.json'] = self.save(self.output/'litert-analyzer-audit.json',
                                                    dict(analysis_did_work=True, synthetic_only=True))
        lint['lint-results-debug.xml'] = self.save(self.output/'lint-results-debug.xml', b'<issues/>')
        apks = []
        for key, package in (('product_apk', c.APP), ('test_apk', c.TEST)):
            pin = self.save(self.output/(key+'.apk'), ('Synthetic APK binding only: '+package).encode())
            self.a['artifacts'][key] = pin; apks.append(dict(package=package, **pin))
        self.value = dict(version=1, scope=scope, head='a'*40, sources=sources, compiled=compiled,
            build_files=files, fresh_lint_files=lint, apks=apks,
            counts=dict(tracked=len(self.mapping), compiled=len(legacy._compiled_sources(self.mapping)), jvm=tests, reports=reports),
            independent_build=self.save(self.output/'independent-build.json', dict(passed=True, synthetic_only=True)),
            independent_lint=self.save(self.output/'independent-lint.json', dict(passed=True, synthetic_only=True)),
            process_probe_build=native_pin)
        self.publish()

    def save(self, path, value):
        path = Path(path).resolve(strict=False)
        if path.drive.upper() != 'D:' or not path.is_relative_to(self.base):
            raise AssertionError('synthetic build write escaped retained D fixture')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if type(value) is bytes else env.encoded(value))
        return env.binding(path)

    def native(self):
        ndk = self.base/'ndk/29.0.14206865'; llvm = ndk/'toolchains/llvm/prebuilt/windows-x86_64'
        paths = [ndk/'source.properties', llvm/'bin/clang.exe', llvm/'bin/ld.lld.exe',
                 llvm/'sysroot/usr/include/x86_64-linux-android/asm/unistd_64.h',
                 llvm/'sysroot/usr/include/asm-generic/unistd.h']
        tools = [self.save(path, b'Pkg.Revision = 29.0.14206865\n' if path.name == 'source.properties'
                           else b'Original synthetic tool/header bytes; never executed.\n') for path in sorted(paths)]
        raw = bytearray(512); raw[:7] = b'\x7fELF\x02\x01\x01'
        struct.pack_into('<HH', raw, 16, 3, 62); struct.pack_into('<Q', raw, 32, 64)
        struct.pack_into('<HH', raw, 54, 56, 3)
        interp = b'/system/bin/linker64\0'; raw[256:256+len(interp)] = interp
        strings = b'\0libc.so\0'; raw[400:400+len(strings)] = strings
        segments = ((1,4,0,4096,0,512,512,4096), (3,4,256,4352,0,len(interp),len(interp),1),
                    (2,4,288,4384,0,64,64,8))
        for index, segment in enumerate(segments):
            struct.pack_into('<IIQQQQQQ', raw, 64+index*56, *segment)
        for index, entry in enumerate(((5,4496), (10,len(strings)), (1,1), (0,0))):
            struct.pack_into('<QQ', raw, 288+index*16, *entry)
        binary = self.save(self.native_root/'android-author-process-probe-v1', bytes(raw))
        self.a['artifacts']['process_probe'] = binary
        source = self.a['artifacts']['process_probe_source']
        builder = env.binding(self.root/'scripts/build_android_author_process_probe.py')
        command = [str(llvm/'bin/clang.exe'), '--no-default-config', '--target=x86_64-linux-android35',
            '--sysroot='+str(llvm/'sysroot'), '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-fPIE', '-pie',
            '-Wl,-z,relro,-z,now', '-Wl,-z,max-page-size=16384', source['path'], '-o', binary['path']]
        self.native_request = dict(version=1, scope='android_author_process_probe_build_v1', ndk_revision='29.0.14206865',
            target='x86_64-linux-android35', source=source, builder=builder, tools=tools, command=command,
            environment={key:'D:\\Dev\\_Temp' for key in ('TEMP','TMP','TMPDIR')}, ndk=str(ndk), output=str(self.native_root))
        request = self.save(self.native_root/'request-v1.json', self.native_request)
        self.started = dict(request=request, worker=dict(pid=7210, creation_filetime=1007210,
                                                        executable=self.a['python']['executable']['path']))
        self.native_value = {key: copy.deepcopy(value) for key, value in self.native_request.items() if key not in ('ndk','output')}
        self.native_value.update(request=request, started=self.save(self.native_root/'started-v1.json', self.started),
            owner=self.save(self.native_root/'owner-result-v1.json', dict(status='child_exited', worker_returncode=0,
                cleanup_complete=True, output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)),
            compile=self.save(self.native_root/'compile.json', dict(returncode=0, capture_complete=True,
                timed_out=False, output_limit=False, stdout=self.save(self.native_root/'compile.stdout.raw', b''),
                stderr=self.save(self.native_root/'compile.stderr.raw', b''))),
            binary=binary, elf=legacy._probe_elf(bytes(raw)), passed=True, feature_acceptance=False)
        for stream in ('stdout', 'stderr'):
            self.save(self.native_root/('owner-'+stream+'-v1.bin'), b'')
        return self.save(self.native_root/'result-v1.json', self.native_value)

    def publish(self):
        self.pin = self.save(self.output/'build-admission-v1.json', self.value)

    def suite_changed(self, name):
        self.value['build_files']['reports/'+name] = self.save(self.output/'reports'/name, ET.tostring(self.suites[name]))
        self.value['build_files']['test-summary-v1.json'] = self.save(self.output/'test-summary-v1.json', self.summary)
        self.publish()

    def started_changed(self):
        self.native_value['started'] = self.save(self.native_root/'started-v1.json', self.started)
        self.value['process_probe_build'] = self.save(self.native_root/'result-v1.json', self.native_value)
        self.publish()

    def validate(self):
        with ExitStack() as stack:
            # Physical source lookup is the only seam. No reader, parser, hash
            # binding or native-build validation result is replaced.
            stack.enter_context(patch.object(live, 'ROOT', self.root))
            stack.enter_context(patch.object(legacy, 'ROOT', self.root))
            return live._verify_build_closed(self.pin, self.a)


@unittest.skipUnless(os.name == 'nt', 'retained physical D build metadata fixtures')
class LiveDeathBuildReplayTests(unittest.TestCase):
    def refused(self, action):
        with self.assertRaises((ValueError, OSError, env.EnvironmentRefused)):
            action()

    def test_complete_exact_600_cases_and_59_reports_replay_real_pinned_files(self):
        graph = ClosedLiveBuild(); before = copy.deepcopy(graph.value)
        self.assertEqual(graph.validate(), before)
        self.assertEqual(sum(len(suite.findall('testcase')) for suite in graph.suites.values()), 600)
        self.assertEqual(len(graph.suites), 59)
        self.assertEqual(graph.value, before)

    def test_legacy_scope_or_old_588_58_counts_cannot_be_promoted_to_sdk6(self):
        for arguments in (dict(scope='owned_restart_android_build_admission_v1'), dict(tests=588, reports=58)):
            with self.subTest(arguments=arguments):
                graph = ClosedLiveBuild(**arguments); self.refused(graph.validate)

    def test_duplicate_case_identity_is_not_600_distinct_executed_cases(self):
        graph = ClosedLiveBuild(); name = graph.summary[0]['name']; cases = graph.suites[name].findall('testcase')
        cases[1].set('name', cases[0].attrib['name']); graph.suite_changed(name)
        self.refused(graph.validate)

    def test_xml_suite_name_cannot_disagree_with_the_pinned_report_identity(self):
        graph = ClosedLiveBuild(); name = graph.summary[0]['name']
        graph.suites[name].set('name', 'org.locallore.synthetic.UnrelatedSuite')
        graph.suite_changed(name)
        self.refused(graph.validate)

    def test_matching_summary_totals_cannot_hide_per_report_case_miscounts(self):
        graph = ClosedLiveBuild()
        for index, change in ((0,1), (1,-1)):
            item = graph.summary[index]; item['tests'] += change
            graph.suites[item['name']].set('tests', str(item['tests'])); graph.suite_changed(item['name'])
        self.assertEqual(sum(item['tests'] for item in graph.summary), 600)
        self.refused(graph.validate)

    def test_zero_summary_counters_cannot_hide_failure_error_or_skipped_descendants(self):
        for tag in ('failure', 'error', 'skipped'):
            with self.subTest(tag=tag):
                graph = ClosedLiveBuild(); name = graph.summary[0]['name']
                ET.SubElement(graph.suites[name].find('testcase'), tag)
                graph.suite_changed(name); self.refused(graph.validate)

    def test_nested_failure_error_or_skipped_descendants_are_not_success(self):
        for tag in ('failure', 'error', 'skipped'):
            with self.subTest(tag=tag):
                graph = ClosedLiveBuild(); name = graph.summary[0]['name']
                container = ET.SubElement(graph.suites[name].find('testcase'), 'system-out')
                ET.SubElement(container, tag)
                graph.suite_changed(name); self.refused(graph.validate)

    def test_native_owner_cannot_outlive_its_fixed_300_second_parent_budget(self):
        graph = ClosedLiveBuild()
        owner = env.read_json(graph.native_value['owner']['path']); owner['elapsed_ms'] = 312001
        graph.native_value['owner'] = graph.save(graph.native_root/'owner-result-v1.json', owner)
        graph.value['process_probe_build'] = graph.save(graph.native_root/'result-v1.json', graph.native_value)
        graph.publish(); self.refused(graph.validate)

    def test_native_started_request_and_python_worker_are_bound_to_the_same_build(self):
        for change in ('request', 'legacy_without_request', 'worker_executable', 'worker_pid_bool'):
            with self.subTest(change=change):
                graph = ClosedLiveBuild()
                if change == 'request':
                    graph.started['request'] = graph.save(graph.base/'another-request-v1.json', graph.native_request)
                elif change == 'legacy_without_request':
                    del graph.started['request']
                elif change == 'worker_executable':
                    graph.started['worker']['executable'] = graph.native_request['tools'][0]['path']
                else:
                    graph.started['worker']['pid'] = True
                graph.started_changed(); self.refused(graph.validate)


if __name__ == '__main__':
    unittest.main()
