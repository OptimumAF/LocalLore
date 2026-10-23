#!/usr/bin/env python3
"""Synthetic license/cached-source policy checks; no builds, extraction or model execution."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('desktop_license_package', Path(__file__).with_name('desktop-package.py'))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)
REAL_ROOT, REAL_WORKER = package.ROOT, package.WORKER_SHA


class LicenseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='license fixture with spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.worker = b'MZ synthetic worker, never executed'
        self.root_patch = patch.object(package, 'ROOT', self.root)
        self.worker_patch = patch.object(package, 'WORKER_SHA', package.sha(self.worker))
        self.root_patch.start(); self.worker_patch.start()
        self.addCleanup(self.root_patch.stop); self.addCleanup(self.worker_patch.stop)
        self.write('LICENSE', b'synthetic first-party Apache license')
        self.write('apps/desktop/package-lock.json', b'{}')
        self.write('licenses/desktop/texts/MPL.txt', b'synthetic MPL terms')
        self.archive = b'\x1f\x8b\0synthetic pinned source archive; never extracted'
        self.crates = self.root / 'registry/src/index.fixture'
        self.records = []
        self.meta = {'workspace_root': str(self.root), 'packages': [],
                     'resolve': {'root': 'desktop', 'nodes': []}}
        self.record('desktop', 'locallore-desktop-spike', None, 'Apache-2.0', [
            self.notice('project', 'LICENSE', 'LICENSE', (self.root / 'LICENSE').read_bytes())])
        self.record('combined', 'combined', 'registry+https://example.invalid/index', 'Apache-2.0 AND MIT', [
            self.notice('crate', 'LICENSE-APACHE', 'NOTICES/rust/combined-1.0.0/LICENSE-APACHE', b'Apache fixture', ['Apache-2.0']),
            self.notice('crate', 'LICENSE-MIT', 'NOTICES/rust/combined-1.0.0/LICENSE-MIT', b'MIT fixture', ['MIT'])])
        self.record('mpl', 'mpl', 'registry+https://example.invalid/index', 'MPL-2.0', [
            self.notice('resource', 'texts/MPL.txt', 'NOTICES/MPL-2.0.txt', b'synthetic MPL terms')], package.sha(self.archive))
        self.meta['resolve']['nodes'] = [{'id': 'desktop', 'deps': [{'pkg': 'combined'}, {'pkg': 'mpl'}]},
                                         {'id': 'combined', 'deps': []}, {'id': 'mpl', 'deps': []}]
        self.write('registry/cache/index.fixture/mpl-1.0.0.crate', self.archive)
        self.write('registry/src/index.fixture/combined-1.0.0/native.lib', b'\0synthetic native source')
        self.catalog = {'schema': 'locallore-desktop-license-catalog-v1', 'scope': package.LICENSE_SCOPE,
                        'target': 'x86_64-pc-windows-msvc', 'worker_sha256': package.WORKER_SHA,
                        'runtime_commit': package.RUNTIME_COMMIT,
                        'runtime_profile_sha256': package.sha(package.encode({'runtime_commit': package.RUNTIME_COMMIT, 'downloads': False})),
                        'review_complete': False,
                        'distribution_approved': False, 'packages': sorted(self.records, key=lambda p: (p['name'], p['version'])),
                        'registry_count': 2, 'local_count': 1, 'frontend': [], 'additional_notices': [],
                        'verified_cached_inputs': [{'name': 'combined', 'version': '1.0.0', 'path': 'native.lib',
                                                   'bytes': 24, 'sha256': package.sha(b'\0synthetic native source')}],
                        'frontend_lock_sha256': package.sha(b'{}'), 'source_archives_byte_cap': 262144,
                        'source_archives_each_byte_cap': 131072, 'remaining_gaps': ['Independent review pending'],
                        'mpl_sources': [{'name': 'mpl', 'version': '1.0.0', 'output': 'SOURCES/MPL/mpl-1.0.0.crate',
                                         'sha256': package.sha(self.archive), 'bytes': len(self.archive)}]}
        self.catalog['verified_cached_inputs'][0]['bytes'] = len(b'\0synthetic native source')
        self.catalog['selected_graph_sha256'] = package.sha(package.encode([
            package.package_identity(p, p['checksum']) for p in self.catalog['packages']]))
        self.save_catalog()
        blocks = []
        for record in self.catalog['packages']:
            block = f'[[package]]\nname = "{record["name"]}"\nversion = "1.0.0"\n'
            if record['source']:
                block += f'source = "{record["source"]}"\nchecksum = "{record["checksum"]}"\n'
            blocks.append(block)
        self.write('Cargo.lock', ('version = 4\n' + '\n'.join(blocks)).encode())

    def write(self, relative, data):
        p = self.root / relative; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)

    def notice(self, origin, path, output, data, terms=None):
        result = {'origin': origin, 'path': path, 'output': output, 'sha256': package.sha(data), 'bytes': len(data)}
        if terms: result['license_terms'] = terms
        return result

    def record(self, identity, name, source, license, notices, checksum=None):
        directory = self.crates / f'{name}-1.0.0' if source else self.root
        directory.mkdir(parents=True, exist_ok=True)
        for n in notices:
            if n['origin'] == 'crate':
                data = b'Apache fixture' if n['path'] == 'LICENSE-APACHE' else b'MIT fixture'
                (directory / n['path']).write_bytes(data)
        self.records.append({'name': name, 'version': '1.0.0', 'source': source,
                             'checksum': (checksum or '1' * 64) if source else None,
                             'license': license, 'notices': notices})
        self.meta['packages'].append({'id': identity, 'name': name, 'version': '1.0.0', 'source': source,
                                      'license': license, 'manifest_path': str(directory / 'Cargo.toml')})

    def save_catalog(self):
        self.write(package.CATALOG_PATH, package.encode(self.catalog))

    def collected(self):
        return package.collect_license_materials(self.meta)

    def packet(self):
        notices, _, report = self.collected()
        files = {'LocalLore Desktop.exe': b'MZ synthetic application, never executed',
                 'runtime/locallore-llama-worker.exe': self.worker,
                 'runtime/profile-v1.json': package.encode({'runtime_commit': package.RUNTIME_COMMIT, 'downloads': False}),
                 'README.txt': b'synthetic readme', **notices}
        manifest = {'kind': 'unsigned-windows-x64-developer-folder-v1', 'source_commit': 'synthetic',
                    'model_weights_included': False, 'dev_harness': False, 'license_audit_complete': False,
                    'license_scope_audit': report}
        return self.seal(files, manifest)

    def seal(self, files, manifest=None):
        manifest = manifest or json.loads(files['build-manifest.json'])
        manifest['files'] = {n: {'sha256': package.sha(b), 'bytes': len(b)} for n, b in files.items() if n != 'build-manifest.json'}
        files['build-manifest.json'] = package.encode(manifest)
        return files

    def test_closed_materials_root_alias_and_binary_sources_round_trip(self):
        files, inventory, report = self.collected()
        self.assertEqual(len(inventory), 3)
        self.assertTrue(report['coverage_complete'])
        self.assertFalse(report['review_complete'])
        self.assertFalse(report['distribution_approved'])
        self.assertEqual(files['LICENSE'], (self.root / 'LICENSE').read_bytes())
        self.assertEqual(files['SOURCES/MPL/mpl-1.0.0.crate'], self.archive)
        package.validate_files(self.packet(), require_license_audit=True)

    def test_unselected_manifest_is_never_read_and_unknown_selected_fails(self):
        self.meta['packages'].append({'id': 'unselected', 'manifest_path': str(self.root / 'must-not-read/private/Cargo.toml')})
        self.collected()
        self.meta['resolve']['nodes'][0]['deps'].append({'pkg': 'unselected'})
        self.meta['resolve']['nodes'].append({'id': 'unselected', 'deps': []})
        with self.assertRaises(ValueError):
            self.collected()

    def test_version_license_source_checksum_and_lock_owner_drift_fail(self):
        for field, value in [('version', '2.0.0'), ('license', 'Unreviewed'), ('source', 'registry+https://foreign.invalid')]:
            with self.subTest(field=field):
                meta = copy.deepcopy(self.meta); meta['packages'][1][field] = value
                with self.assertRaisesRegex(ValueError, 'graph/version/checksum/expression'):
                    package.collect_license_materials(meta)
        lock = self.root / 'Cargo.lock'; before = lock.read_bytes(); lock.write_bytes(before.replace(b'1' * 64, b'2' * 64))
        with self.assertRaisesRegex(ValueError, 'graph/version/checksum/expression'): self.collected()
        lock.write_bytes(before)
        meta = copy.deepcopy(self.meta); meta['workspace_root'] = str(self.root.parent)
        with self.assertRaisesRegex(ValueError, 'lock owner'): package.collect_license_materials(meta)

    def test_missing_and_modified_required_text_and_root_license_fail(self):
        for p in [self.root / 'LICENSE', self.crates / 'combined-1.0.0/LICENSE-MIT', self.root / 'licenses/desktop/texts/MPL.txt']:
            with self.subTest(path=p.name):
                original = p.read_bytes(); p.write_bytes(original + b'changed')
                with self.assertRaisesRegex(ValueError, 'required license material'): self.collected()
                p.write_bytes(original); p.unlink()
                with self.assertRaises(OSError): self.collected()
                p.write_bytes(original)

    def test_and_operands_cannot_be_dropped_from_catalog_or_packet(self):
        combined = next(p for p in self.catalog['packages'] if p['name'] == 'combined')
        removed = combined['notices'].pop()
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'AND license coverage'): self.collected()
        combined['notices'].append(removed); self.save_catalog()
        files = self.packet(); del files[removed['output']]; self.seal(files)
        with self.assertRaisesRegex(ValueError, 'audited license material'): package.validate_files(files)

    def test_resource_origin_and_path_cannot_escape(self):
        mpl = next(p for p in self.catalog['packages'] if p['name'] == 'mpl')['notices'][0]
        for key, value in [('path', '../private.txt'), ('origin', 'shell'), ('output', 'NOTICES/../private.txt')]:
            original = mpl[key]; mpl[key] = value; self.save_catalog()
            with self.assertRaises(ValueError): self.collected()
            mpl[key] = original
        self.save_catalog()

    def test_native_cache_and_frontend_lock_mutation_fail(self):
        native = self.crates / 'combined-1.0.0/native.lib'; native.write_bytes(b'different')
        with self.assertRaisesRegex(ValueError, 'embedded native input'): self.collected()
        native.write_bytes(b'\0synthetic native source')
        self.write('apps/desktop/package-lock.json', b'changed')
        with self.assertRaisesRegex(ValueError, 'frontend dependency lock'): self.collected()

    def test_frontend_version_license_and_text_are_checked(self):
        b = b'frontend MIT fixture'
        self.catalog['frontend'] = [{'name': 'react', 'version': '1.0.0', 'license': 'MIT', 'output': 'NOTICES/frontend/react-LICENSE.txt', 'sha256': package.sha(b), 'bytes': len(b)}]
        self.save_catalog(); self.write('apps/desktop/node_modules/react/LICENSE', b)
        path = self.root / 'apps/desktop/node_modules/react/package.json'
        for version, license in [('2.0.0', 'MIT'), ('1.0.0', 'other')]:
            path.write_bytes(package.encode({'name': 'react', 'version': version, 'license': license}))
            with self.assertRaisesRegex(ValueError, 'frontend license identity'): self.collected()
        path.write_bytes(package.encode({'name': 'react', 'version': '1.0.0', 'license': 'MIT'})); self.collected()
        self.write('apps/desktop/node_modules/react/LICENSE', b'tampered')
        with self.assertRaisesRegex(ValueError, 'required license material'): self.collected()

    def test_source_archive_hash_missing_count_and_budgets_fail(self):
        archive = self.root / 'registry/cache/index.fixture/mpl-1.0.0.crate'; archive.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'required license material'): self.collected()
        archive.unlink()
        with self.assertRaises(OSError): self.collected()
        archive.write_bytes(self.archive)
        self.catalog['mpl_sources'] = []; self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'MPL source coverage'): self.collected()

    def test_resealed_packets_cannot_forge_coverage_or_materials(self):
        for operation in ['scope', 'inventory', 'source', 'extra', 'approval', 'profile']:
            with self.subTest(operation=operation):
                files = self.packet(); manifest = json.loads(files['build-manifest.json'])
                if operation == 'scope': manifest['license_scope_audit']['catalog_sha256'] = '0' * 64
                elif operation == 'inventory': files['NOTICES/rust-inventory.json'] = b'[]'
                elif operation == 'source': files['SOURCES/MPL/mpl-1.0.0.crate'] += b'changed'
                elif operation == 'extra': files['NOTICES/private-story.txt'] = b'unreviewed material'
                elif operation == 'approval': manifest['license_audit_complete'] = True
                elif operation == 'profile':
                    files['runtime/profile-v1.json'] = package.encode({'runtime_commit': package.RUNTIME_COMMIT, 'downloads': False, 'model': 'foreign'})
                self.seal(files, manifest)
                with self.assertRaises(ValueError): package.validate_files(files)

    def test_source_binary_exception_is_closed_and_capped(self):
        for name, data in [('SOURCES/other.crate', b'\0'), ('SOURCES/MPL/mpl-1.0.0.crate', b'\0' * 131073), ('NOTICES/binary.txt', b'\0')]:
            files = self.packet(); files[name] = data; self.seal(files)
            with self.assertRaises(ValueError): package.validate_files(files)

    def test_catalog_duplicates_reserved_outputs_and_aggregate_caps_fail(self):
        original = copy.deepcopy(self.catalog)
        self.catalog['packages'].append(copy.deepcopy(self.catalog['packages'][0])); self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'Duplicate'): self.collected()
        self.catalog = copy.deepcopy(original)
        self.catalog['additional_notices'] = [self.notice('resource', 'texts/MPL.txt', 'NOTICES/license-audit.json', b'synthetic MPL terms')]
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'Reserved'): self.collected()
        self.catalog = copy.deepcopy(original)
        self.catalog['additional_notices'] = [
            {'origin': 'resource', 'path': f'texts/large-{index}.txt', 'output': f'NOTICES/large-{index}.txt',
             'sha256': '1' * 64, 'bytes': 1024 * 1024} for index in range(17)]
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'aggregate budget'): self.collected()

    def test_scope_identity_and_source_license_reference_are_not_self_declared(self):
        for key, value in [('scope', 'foreign'), ('worker_sha256', '0' * 64),
                           ('target', 'other'), ('distribution_approved', True)]:
            original = self.catalog[key]; self.catalog[key] = value; self.save_catalog()
            with self.assertRaisesRegex(ValueError, 'Unsupported'): self.collected()
            self.catalog[key] = original
        mpl = next(p for p in self.catalog['packages'] if p['name'] == 'mpl')['notices'][0]
        mpl['output'] = 'NOTICES/broken-license-reference.txt'; self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'MPL source license text'): self.collected()

    def test_legacy_packet_downgrade_is_never_reported_as_audited(self):
        files = self.packet(); manifest = json.loads(files['build-manifest.json']); del manifest['license_scope_audit']
        del files['NOTICES/license-audit.json']; del files['SOURCES/MPL/mpl-1.0.0.crate']; self.seal(files, manifest)
        self.assertEqual(package.validate_scope_audit(files, manifest), 'legacy_unreviewed')
        with self.assertRaisesRegex(ValueError, 'Missing scoped'): package.validate_files(files, require_license_audit=True)

    def test_actual_public_catalog_is_exact_and_all_resource_hashes_match(self):
        with patch.object(package, 'ROOT', REAL_ROOT), patch.object(package, 'WORKER_SHA', REAL_WORKER):
            c, _ = package.license_catalog()
            self.assertEqual(len(c['packages']), 256)
            self.assertEqual((c['registry_count'], c['local_count']), (250, 6))
            self.assertEqual(len(c['mpl_sources']), 5)
            self.assertEqual(sum(p['bytes'] for p in c['mpl_sources']), 150290)
            self.assertIn('licenses/desktop', package.SOURCE_PATHS)
            for item in [n for p in c['packages'] for n in p['notices']] + c['additional_notices']:
                if item['origin'] == 'resource':
                    data = (REAL_ROOT / 'licenses/desktop' / item['path']).read_bytes()
                    self.assertEqual((package.sha(data), len(data)), (item['sha256'], item['bytes']))

    def test_msvc_additional_materials_are_required_after_packet_resealing(self):
        names = ['MSVC-STL-LICENSE.txt', 'MSVC-STL-NOTICE.txt', 'MSVC-runtime-provenance.json']
        for name in names:
            data = (b'{"review_complete":false}' if name.endswith('.json') else b'synthetic MSVC notice ' + name.encode())
            self.write('licenses/desktop/texts/' + name, data)
            self.catalog['additional_notices'].append(
                self.notice('resource', 'texts/' + name, 'NOTICES/native/' + name, data))
        self.save_catalog()
        package.validate_files(self.packet(), require_license_audit=True)
        for name in names:
            with self.subTest(name=name):
                path = self.root / 'licenses/desktop/texts' / name
                original = path.read_bytes(); path.write_bytes(original + b'changed')
                with self.assertRaisesRegex(ValueError, 'required license material'): self.collected()
                path.write_bytes(original)
                for operation in ['change', 'remove']:
                    files = self.packet(); output = 'NOTICES/native/' + name
                    if operation == 'change': files[output] += b'changed'
                    else: del files[output]
                    self.seal(files)
                    with self.assertRaisesRegex(ValueError, 'audited license material'):
                        package.validate_files(files)

    def test_actual_msvc_record_separates_embedded_startup_and_external_dlls(self):
        with patch.object(package, 'ROOT', REAL_ROOT), patch.object(package, 'WORKER_SHA', REAL_WORKER):
            c, _ = package.license_catalog()
            required = package.expected_license_materials(c)
            for name in ['MSVC-STL-LICENSE.txt', 'MSVC-STL-NOTICE.txt', 'MSVC-runtime-provenance.json']:
                self.assertIn('NOTICES/native/' + name, required)
            notices = {n['output']: n for n in c['additional_notices']}
            for name in ['MSVC-STL-LICENSE.txt', 'MSVC-STL-NOTICE.txt']:
                self.assertEqual(notices['NOTICES/native/' + name]['provenance']['revision'],
                                 'af8adfa73b7433d4f902584bc1994c897297e492')
            p = json.loads((REAL_ROOT / 'licenses/desktop/texts/MSVC-runtime-provenance.json').read_bytes())
            self.assertEqual(p['schema'], 'locallore-msvc-runtime-provenance-v1')
            self.assertFalse(p['review_complete']); self.assertFalse(p['distribution_approved'])
            self.assertFalse(p['new_build']); self.assertFalse(p['app_worker_model_executed'])
            families = {row['family']: row for row in p['components']}
            startup = families['MSVC native CRT startup and import glue']
            self.assertTrue(startup['embedded_object_family'])
            self.assertTrue(startup['stl_license_does_not_relicense_this_family'])
            self.assertEqual(startup['license_reference'], 'LicenseRef-Microsoft-Visual-Studio-Community-2022')
            dlls = families['MSVC STL, VCRuntime and OpenMP DLLs']
            self.assertFalse(dlls['redistributed'])
            self.assertEqual(set(dlls['required_worker_imports']),
                             {'MSVCP140.dll', 'VCOMP140.DLL', 'VCRUNTIME140.dll', 'VCRUNTIME140_1.dll'})
            self.assertEqual(p['retained_binary_evidence']['worker']['sha256'], REAL_WORKER)

    def test_actual_embedded_json_notices_bind_all_distinct_header_authors(self):
        with patch.object(package, 'ROOT', REAL_ROOT), patch.object(package, 'WORKER_SHA', REAL_WORKER):
            c, _ = package.license_catalog()
            notices = {n['output']: n for n in c['additional_notices']}
            name = 'NOTICES/native/nlohmann-json-header-notices.txt'
            self.assertIn(name, package.expected_license_materials(c))
            n = notices[name]; provenance = n['provenance']
            self.assertEqual(provenance['path'], 'vendor/nlohmann/json.hpp')
            self.assertEqual(provenance['source_file_sha256'],
                             'f9ce5c0a1ac99e20ef92daeb60eb571e2146988daa553ac0269755348843efd7')
            text = (REAL_ROOT / 'licenses/desktop' / n['path']).read_text(encoding='utf-8')
            for author in ['Niels Lohmann', 'Evan Nemerson', 'The Abseil Authors',
                           'Bj\u00f6rn Hoehrmann', 'Florian Loitsch']:
                self.assertIn(author, text)
            self.assertIn('#else of JSON_HAS_CPP_14', provenance['conditional_applicability'])
            self.assertIn('not proof', provenance['conditional_applicability'])
            for reference in provenance['license_members']:
                self.assertIn(reference, package.expected_license_materials(c))


if __name__ == '__main__':
    unittest.main()
