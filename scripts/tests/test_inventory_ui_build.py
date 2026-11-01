"""Byte-backed attestation plumbing, not synthetic DEX/ELF qualification."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import inventory_ui_build as build


HERE = Path('D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-host-fixtures-v1/build')


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class Fixture:
    """Tiny complete fixed graph; only fixed data and Git I/O are substituted."""
    def __init__(self):
        HERE.mkdir(parents=True, exist_ok=True)
        self.home = Path(tempfile.mkdtemp(prefix='case-', dir=HERE))
        self.root, self.out, self.rec = (self.home/name for name in ('product', 'out', 'recovery'))
        self.fixed = copy.deepcopy(build._FIXED)
        self.fixed.update(root=str(self.root), capture=str(self.out), recovery=str(self.rec),
                          manifest=str(self.home/'manifest.json'), source_count=3, tested_count=2)
        self.baseline = self.home/'baseline.json'
        self.records = {}
        self.refs = {}
        self.native = []
        for target, abi in (('x86_64-linux-android','x86_64'), ('aarch64-linux-android','arm64-v8a')):
            base = self.root/'apps/android/app/build'
            release = base/f'rust-target/{target}/release/liblocallore_android.so'
            alias = base/f'rust-target/{target}/release/deps/liblocallore_android.so'
            self.write(release, ('native-'+abi).encode())
            alias.parent.mkdir(parents=True, exist_ok=True)
            os.link(release, alias)
            row = dict(abi=abi, release=pin(release), cargo_alias=pin(alias), release_alias_links=2)
            for key, name in (
                ('generated',f'generated/rustJniLibs/{abi}/liblocallore_android.so'),
                ('merged',f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so'),
                ('stripped',f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so')):
                self.write(base/name, release.read_bytes() if key!='stripped' else b'stripped-'+abi.encode())
                row[key] = pin(base/name)
            row.update(apk_sha256=row['stripped']['sha256'])
            self.native.append(row)
        for role in ('product_apk','test_apk'):
            path = self.root/(role+'.apk')
            self.write(path, ('inert-attested-'+role).encode())
            self.fixed['apks'][role] = pin(path)
        self.source = {}
        for name, raw in (('README.md',b'new readme'), ('src/lib.rs',b'canonical source'),
                          ('docs/android/PLAYER_INVENTORY_APKS_2026-11-01.md',b'report')):
            self.write(self.root/name, raw)
            self.source[name] = pin(self.root/name)
        before = dict(head=self.fixed['tested_head'], files=[
            dict(path='README.md',bytes=3,sha256=hashlib.sha256(b'old').hexdigest()),
            dict(path='src/lib.rs', **{k:self.source['src/lib.rs'][k] for k in ('bytes','sha256')})])
        pairs = []
        for i in range(89):
            original, saved = self.out/f'ordinary/{i}.bin', self.rec/f'controls-v1/ordinary/{i}.bin'
            raw = ('ordinary-'+str(i)).encode()
            self.write(original, raw); self.write(saved, raw)
            pairs.append(dict(original=pin(original),copy=pin(saved)))
        paths = dict(build='closed-build-evidence-v1.json', producer='producer-closure-v1.json',
                     final_source='final-source-verification-v1.json',before='source-before-v1.json',after='source-after-v1.json')
        paths.update(preservation='preservation-receipt-v1.json',reviews='independent-readback-v1.json',raw_pins='raw-source-pins-v1.json')
        for key, name in (('tested_archive','source-b8dbbcbb-v1.zip'),
                          ('canonical_archive','source-canonical-v1.zip'),('raw_archive','source-raw-v1.zip')):
            path = (self.out if key=='tested_archive' else self.rec)/name
            self.write(path, ('sealed-byte-archive-'+key).encode());self.refs[key]=pin(path)
        final = dict(head=self.fixed['head'],testedHead=self.fixed['tested_head'],trackedFiles=3,
            documentationOnlyDelta=['README.md','docs/android/PLAYER_INVENTORY_APKS_2026-11-01.md'],
            eolOnlyDifferences=['documented-eol.txt'],canonical=self.refs['canonical_archive'],raw=self.refs['raw_archive'])
        self.records = dict(before=before,after=copy.deepcopy(before),raw_pins=self.source,final_source=final,
            producer=dict(head=self.fixed['tested_head'],closed_before_independent_review=True,
                build_runs=1,build_retries=0,runtime_or_device_execution=False,files=[p['original'] for p in pairs[:76]]),
            preservation=dict(controls=pairs,controlsBytes=sum(p['original']['bytes'] for p in pairs),source=final),
            reviews=dict(sourceHead=self.fixed['head'],testedHead=self.fixed['tested_head'],
                rolesClosed=['native_build_policy','closed_apk_dex','final_preservation'],
                artifactReader=dict(definedJUnitMethodsWithBodies=11),elevenAndroidMethodsUnrun=True),
            build=dict(head=self.fixed['tested_head'],source_count=2,
                junit=dict(counts=dict(tests=439,failures=0,errors=0,skipped=0),unique_cases=439,xml_suites=52),
                android_runtime_executed=False,inner_aapt_raw_capture_claimed=False,full_tool_binary_provenance_claimed=False,
                native=self.native, artifacts=pairs[:55],
                pair_audit=dict(package='org.locallore.app',test_package='org.locallore.app.test',status='passed',
                    certificate_sha256=self.fixed['certificate'],
                    app={k:self.fixed['apks']['product_apk'][k] for k in ('bytes','sha256')},
                    test={k:self.fixed['apks']['test_apk'][k] for k in ('bytes','sha256')})))
        for key,name in paths.items():
            path = (self.rec if key in ('preservation','reviews','raw_pins') else self.out)/name
            self.write(path, self.encode(self.records[key]));self.refs[key]=pin(path)
        self.value = dict(version=1,scope=build.MODE,product=self.fixed,refs=self.refs,
            roster=copy.deepcopy(build.ROSTER),facts=copy.deepcopy(build._FACTS),native=self.native,
            documentation_only_delta=final['documentationOnlyDelta'],raw_canonical_eol_paths=final['eolOnlyDifferences'],
            preserved_controls=dict(count=89,bytes=self.records['preservation']['controlsBytes']),producer_files=76)
        self.seal()

    @staticmethod
    def encode(value):
        return json.dumps(value,sort_keys=True).encode()

    @staticmethod
    def write(path,raw):
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)

    def seal(self):
        self.baseline.write_bytes(self.encode(self.value))
        self.baseline_pin = pin(self.baseline)

    def git(self,args):
        if args==['rev-parse','HEAD']:return (self.fixed['head']+'\n').encode()
        if args==['status','--porcelain','--untracked-files=all']:return b''
        if args==['ls-files','-z']:return ('\0'.join(self.source)+'\0').encode()
        raise AssertionError('unexpected Git operation')

    def patches(self):
        return patch.multiple(build,_FIXED=self.fixed,BASELINE_PATH=self.baseline,
            BASELINE_BYTES=self.baseline_pin['bytes'],BASELINE_SHA256=self.baseline_pin['sha256'],_git=self.git)

    def artifacts(self):
        return dict(build=pin(Path(self.fixed['manifest'])),**copy.deepcopy(self.fixed['apks']))


class InventoryBuildTests(unittest.TestCase):
    def setUp(self):
        self.f=Fixture()
        self.p=self.f.patches();self.p.start();self.addCleanup(self.p.stop)
        self.traps=[]
        for target in ('subprocess.run','subprocess.Popen','socket.socket','socket.create_connection'):
            p=patch(target,side_effect=AssertionError('forbidden process/network call'))
            p.start();self.traps.append(p);self.addCleanup(p.stop)

    def test_complete_byte_graph_returns_detached_eleven_roster_without_publication(self):
        result=build.create_manifest()
        self.assertFalse(Path(self.f.fixed['manifest']).exists())
        self.assertEqual(build.MODE,result['validation_mode'])
        self.assertEqual(build.ROSTER,result['roster'])
        self.assertEqual(11,len(result['roster']))
        self.assertFalse(result['recorded_execution']['facts']['deep_semantic_review_repeated'])
        result['roster'][0][0]='mutated'
        self.assertNotEqual(result['roster'],build.create_manifest()['roster'])

    def test_manifest_and_exact_three_artifacts_are_replayed(self):
        self.f.write(Path(self.f.fixed['manifest']),self.f.encode(build.create_manifest()))
        self.assertEqual(build.ROSTER,build.verify_frozen_product(self.f.artifacts())['roster'])
        for change in ('extra','swap','root','retag'):
            with self.subTest(change=change):
                artifacts=self.f.artifacts()
                if change=='extra':artifacts['model']=artifacts['product_apk']
                if change=='swap':artifacts['product_apk'],artifacts['test_apk']=artifacts['test_apk'],artifacts['product_apk']
                if change=='root':artifacts['build']['path']=str(self.f.home/'foreign.json')
                if change=='retag':
                    value=build.create_manifest();value['scope']='chat-ui-build-v1'
                    Path(self.f.fixed['manifest']).write_bytes(self.f.encode(value));artifacts=self.f.artifacts()
                with self.assertRaises(build.BuildRefused):build.verify_frozen_product(artifacts)

    def test_source_byte_drift_refuses_even_when_git_head_matches(self):
        (self.f.root/'src/lib.rs').write_bytes(b'changed source')
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_source_roster_or_dirty_worktree_refuses(self):
        for dirty in (True,False):
            def git(args):
                if args[0]=='status' and dirty:return b'?? foreign\n'
                if args[0]=='ls-files' and not dirty:return b'foreign\0'
                return self.f.git(args)
            with self.subTest(dirty=dirty),patch.object(build,'_git',side_effect=git),self.assertRaises(build.BuildRefused):
                build.create_manifest()

    def test_recorded_xml_failure_or_audit_mutation_cannot_retain_closed_seal(self):
        path=Path(self.f.refs['build']['path']);old=path.read_bytes()
        for key,value in (('junit',dict(counts=dict(tests=439,failures=1,errors=0,skipped=0))),
                          ('pair_audit',dict(status='passed',certificate_sha256='0'*64))):
            changed=copy.deepcopy(self.f.records['build']);changed[key]=value;path.write_bytes(self.f.encode(changed))
            with self.subTest(key=key),self.assertRaises(build.BuildRefused):build.create_manifest()
            path.write_bytes(old)

    def test_closed_source_archive_or_control_copy_drift_refuses(self):
        for path in (Path(self.f.refs['raw_archive']['path']),
                     Path(self.f.records['preservation']['controls'][-1]['copy']['path'])):
            old=path.read_bytes();path.write_bytes(old+b'drift')
            with self.subTest(role=path.name),self.assertRaises(build.BuildRefused):build.create_manifest()
            path.write_bytes(old)

    def test_unsealed_baseline_and_duplicate_json_refuse(self):
        self.f.baseline.write_bytes(self.f.baseline.read_bytes()+b' ')
        with self.assertRaises(build.BuildRefused):build.create_manifest()
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}'):
            with self.subTest(raw=raw),self.assertRaises(build.BuildRefused):build._json(raw)

    def test_resealed_wrong_documentation_delta_refuses(self):
        self.f.value['documentation_only_delta']=['src/lib.rs'];self.f.seal()
        with patch.object(build,'BASELINE_BYTES',self.f.baseline_pin['bytes']),patch.object(build,'BASELINE_SHA256',self.f.baseline_pin['sha256']),self.assertRaises(build.BuildRefused):
            build.create_manifest()

    def test_exact_two_cargo_names_must_be_the_same_object(self):
        row=self.f.native[0];alias=Path(row['cargo_alias']['path'])
        # Retain original alias; a foreign same-byte nlink2 object cannot replace it.
        alias.rename(alias.with_suffix('.original'))
        self.f.write(alias,Path(row['release']['path']).read_bytes())
        os.link(alias,alias.with_suffix('.foreign'))
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_third_cargo_alias_refuses_without_generic_exception(self):
        release=Path(self.f.native[0]['release']['path'])
        os.link(release,release.with_suffix('.third'))
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_missing_cargo_alias_refuses(self):
        alias=Path(self.f.native[0]['cargo_alias']['path'])
        alias.rename(alias.with_suffix('.retained'))
        with self.assertRaises(build.BuildRefused):build.create_manifest()

    def test_source_apk_and_ordinary_control_hardlinks_always_refuse(self):
        for path in (self.f.root/'src/lib.rs',Path(self.f.fixed['apks']['product_apk']['path']),
                     Path(self.f.records['producer']['files'][0]['path'])):
            os.link(path,path.with_suffix('.extra'))
            with self.subTest(role=path.name),self.assertRaises(build.BuildRefused):build._Reader().read(pin(path))
        release=Path(self.f.native[0]['release']['path'])
        with self.assertRaises(build.BuildRefused):build._Reader().read(pin(release))

    def test_final_check_refuses_late_drift_and_expired_budget(self):
        path=self.f.root/'src/lib.rs';reader=build._Reader();reader.read(pin(path));path.write_bytes(b'late drift')
        with self.assertRaises(build.BuildRefused):reader.final()
        reader=build._Reader();reader.until=0
        with self.assertRaises(build.BuildRefused):reader.read(pin(path))

    def test_import_has_no_filesystem_process_or_network_activity(self):
        source=Path(build.__file__).read_bytes()
        with patch('builtins.open',side_effect=AssertionError('import IO')),patch.object(Path,'open',side_effect=AssertionError('import IO')):
            namespace={'__file__':build.__file__,'__name__':'import_only'}
            exec(compile(source,build.__file__,'exec'),namespace)
        self.assertTrue(callable(namespace['create_manifest']))


if __name__=='__main__':
    unittest.main()
