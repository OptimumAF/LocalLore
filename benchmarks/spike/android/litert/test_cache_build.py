"""Independent build isolation/audit failure cases. No build/device/model subprocesses."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import cache_build as target


def manifest(name=target.INSTRUMENTATION, package=target.PACKAGE):
    return ('E: manifest (line=1)\n  E: instrumentation (line=2)\n'
            f'    A: android:name(0x01010003)="{name}" (Raw: "{name}")\n'
            f'    A: android:targetPackage(0x01010021)="{package}" (Raw: "{package}")\n')


class CacheBuildTests(unittest.TestCase):
    def test_permission_or_legacy_package_cannot_pass_new_identity(self):
        for permissions in ('package: org.locallore.runtimebench.litert',
                            'package: ' + target.PACKAGE + '\nuses-permission: android.permission.INTERNET'):
            with self.assertRaisesRegex(ValueError, 'permissions_or_package'):
                target.manifest_audit(permissions, manifest())

    def test_exact_one_explicit_cache_instrumentation_is_required(self):
        target.manifest_audit('package: ' + target.PACKAGE, manifest())
        for tree in (manifest(name='org.locallore.runtimebench.litert.SpikeInstrumentation'),
                     manifest(package='org.locallore.runtimebench.litert'), manifest() + manifest(), ''):
            with self.assertRaisesRegex(ValueError, 'instrumentation'):
                target.manifest_audit('package: ' + target.PACKAGE, tree)

    def test_permission_declaration_is_rejected_even_without_request(self):
        with self.assertRaisesRegex(ValueError, 'permission_declaration'):
            target.manifest_audit('package: ' + target.PACKAGE, manifest() + '  E: permission (line=9)\n')

    def test_host_reserves_do_not_borrow_from_the_other_volume(self):
        output = Path('D:/fresh')
        def usage(system, secondary):
            return lambda path: SimpleNamespace(free=system if str(path).startswith('C:') else secondary)
        with self.assertRaisesRegex(ValueError, 'system_capacity'):
            target.capacity(output, usage(4 * target.GIB, 100 * target.GIB))
        with self.assertRaisesRegex(ValueError, 'output_capacity'):
            target.capacity(output, usage(100 * target.GIB, 16 * target.GIB - 1))
        target.capacity(output, usage(4 * target.GIB + 64 * 1024 ** 2, 16 * target.GIB))

    def test_gradle_uses_only_opt_in_identity_and_explicit_output_offline(self):
        output = Path('D:/new/output')
        with patch.object(target.build.check, 'java_executable', return_value='java17'):
            command = target.gradle_command(Path('java21'), output)
        self.assertIn('-PlocalLoreCacheProbe=true', command)
        self.assertIn('-PlocalLorePlayProbe=false', command)
        self.assertIn('-PlocalLoreCacheOutput=' + str(output / 'app-build'), command)
        self.assertIn('-PlocalLoreCacheNativeDir=' + str(output / 'native/jniLibs'), command)
        self.assertIn('--offline', command)
        self.assertIn('--no-daemon', command)
        self.assertNotIn('clean', command)
        self.assertEqual(command[command.index('--project-cache-dir') + 1], str(output / 'gradle-project'))

    def test_unknown_native_entry_and_duplicate_zip_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / 'fixture.apk'
            with zipfile.ZipFile(apk, 'w') as archive:
                archive.writestr('lib/x86_64/foreign.so', b'not ELF')
            with self.assertRaisesRegex(ValueError, 'native_libraries'):
                target.native_archive_audit(apk)

    def test_native_compression_and_wrong_abi_are_independent_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / 'fixture.apk'
            for compressed in (True, False):
                with zipfile.ZipFile(apk, 'w') as archive:
                    for abi in target.play_build.TARGETS:
                        for library in ('liblitertlm_jni.so', 'liblocallore_android.so'):
                            archive.writestr(f'lib/{abi}/{library}', b'synthetic-invalid-ELF',
                                compress_type=zipfile.ZIP_DEFLATED if compressed else zipfile.ZIP_STORED)
                with self.assertRaises(ValueError):
                    target.native_archive_audit(apk)

    def test_failed_or_unknown_process_cleanup_is_retained_and_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory); (output / 'logs').mkdir()
            for cleanup, status, code in ((False, 'cleanup_failed', 0), (True, 'timeout', -1), (True, 'completed', 1)):
                result = SimpleNamespace(stdout=b'bounded private compiler diagnostic', status=status,
                    returncode=code, elapsed_ms=180000, stderr_bytes=0, cleanup_complete=cleanup)
                with patch.object(target, 'capacity'), patch.object(target.runtime_spike, 'run_process', return_value=result) as run:
                    with self.assertRaisesRegex(ValueError, 'build_stage_failed_test'):
                        target.stage(output, 'test', ['never-run'], output)
                self.assertEqual(run.call_args.kwargs['deadline'], 180)
                self.assertEqual(run.call_args.kwargs['max_output'], 262144)
                self.assertEqual((output / 'logs/test.log').read_bytes(), result.stdout)
                self.assertEqual(target.json.loads((output / 'logs/test.json').read_text())['cleanup_complete'], cleanup)

    def test_output_refuses_existing_directory_and_missing_ancestor(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            self.assertEqual(target.real_directory(parent), parent)
            with self.assertRaises(ValueError):
                target.real_directory(parent / 'missing')
            if target.os.name == 'nt':
                with self.assertRaises(ValueError):
                    target.fresh_output(Path('C:/locallore-cache-output-refused'))
                with self.assertRaises(FileExistsError):
                    target.fresh_output(parent)

    def test_reparse_attribute_refuses_junction_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            with patch.object(Path, 'lstat', return_value=SimpleNamespace(st_file_attributes=0x400)):
                with self.assertRaisesRegex(ValueError, 'linked_or_missing_output'):
                    target.real_directory(parent)
            self.assertEqual(list(parent.iterdir()), [])

    def test_play_probe_exports_are_complete_and_no_unknown_probe_entry_is_accepted(self):
        prefix = 'Java_org_locallore_runtimebench_litert_NativePlayProbe_'
        symbols = ['000123 T ' + prefix + method for method in ('open', 'call', 'poll', 'respond', 'close')]
        target.exports_audit('\n'.join(symbols) + '\n00100 T unrelated_production_entry')
        with self.assertRaisesRegex(ValueError, 'exports'):
            target.exports_audit('\n'.join(symbols[:-1]))
        with self.assertRaisesRegex(ValueError, 'exports'):
            target.exports_audit('\n'.join(symbols) + '\n000234 T ' + prefix + 'unsafe')


if __name__ == '__main__':
    unittest.main()
