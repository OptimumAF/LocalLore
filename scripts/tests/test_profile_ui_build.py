"""Tiny byte-attestation graphs, not fabricated XML/DEX/ELF qualifications."""
import copy
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import profile_ui_build as b

FIXTURES=Path('D:/Dev/Experiments/LocalLore/2026-11-01-profile-ui-harness-v1/build-fixtures-v1')


def encoded(value):return json.dumps(value,sort_keys=True).encode()
def pin(path):
    raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
    return pin(path)


class Graph:
    """All evidence bytes and identities are real tiny D files; Git IO is simulated.

    Private fixed data is coherently changed only inside tests. No acceptance
    validator is stubbed; opaque payloads deliberately carry no semantic claim.
    """
    def __init__(self):
        FIXTURES.mkdir(parents=True,exist_ok=True)
        self.home=Path(tempfile.mkdtemp(prefix='graph-',dir=FIXTURES))
        self.fixed=copy.deepcopy(b._FIXED)
        self.root,self.out,self.rec=(self.home/name for name in ('product','capture','recovery'))
        self.fixed.update(root=str(self.root),capture=str(self.out),recovery=str(self.rec),manifest=str(self.home/'manifest.json'))
        self.baseline=self.home/'baseline.json';self.refs={};self.r={}
        self.source={}
        for name,raw in (('README.md',b'new readme'),('docs/native/PLAYER_PRESENTATION_V2.md',b'updated native docs'),
                         ('docs/android/PLAYER_SELF_PROFILE_2026-11-01.md',b'new report'),('src/lib.rs',b'source')):
            self.source[name]=put(self.root/name,raw)
        dexrows=[]
        for i,(kind,cls,method) in enumerate(b.ROSTER):
            relative='apps/android/app/src/androidTest/java/'+cls.replace('.','/')+'.kt'
            if relative not in self.source:self.source[relative]=put(self.root/relative,b'opaque source bytes')
            dexrows.append(dict(kind=kind,**{'class':cls},method=method,runtime_junit=True,
                public_concrete_instance_void_noargs=True,code_units=100+i,product_class_family_absent=True,source=self.source[relative]))
        self.fixed.update(source_count=len(self.source),tested_count=len(self.source)-1)
        before=[]
        for name,p in self.source.items():
            if name==b.DOC_DELTA[1]:continue
            raw=(b'old README' if name=='README.md' else b'old native docs') if name in b.DOC_DELTA else (self.root/name).read_bytes()
            before.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        self.r['before']=dict(head=self.fixed['tested_head'],files=before);self.r['after']=copy.deepcopy(self.r['before'])
        for role in ('product_apk','test_apk'):
            self.fixed['apks'][role]=put(self.root/(role+'.apk'),('attested-'+role).encode())
        native=[]
        for target,abi in (('x86_64-linux-android','x86_64'),('aarch64-linux-android','arm64-v8a')):
            base=self.root/'apps/android/app/build';release=base/f'rust-target/{target}/release/liblocallore_android.so'
            alias=release.parent/'deps/liblocallore_android.so'
            put(release,('release-'+abi).encode());alias.parent.mkdir();os.link(release,alias)
            row=dict(abi=abi,release=pin(release),cargo_alias=pin(alias))
            for key,name in (('generated',f'generated/rustJniLibs/{abi}/liblocallore_android.so'),
                             ('merged',f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so'),
                             ('stripped',f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so')):
                row[key]=put(base/name,release.read_bytes() if key!='stripped' else ('stripped-'+abi).encode())
            row['apk_sha256']=row['stripped']['sha256'];native.append(row)
        for key,name,parent in (('tested_archive','host-build-v1/source-tested-v1.zip',self.out),('final_archive','source-final-v1.zip',self.out)):
            self.refs[key]=put(parent/name,('opaque reviewed archive '+key).encode())
        final=dict(head=self.fixed['head'],tested_head=self.fixed['tested_head'],worktree_clean=True,
            files=[dict(path=name,bytes=p['bytes'],sha256=p['sha256']) for name,p in self.source.items()],
            documentation_only_delta=b.DOC_DELTA,source_zip={k:self.refs['final_archive'][k] for k in ('bytes','sha256')})
        self.r['final_source']=final
        original_pairs=[]
        for i in range(85):
            raw=('control-'+str(i)).encode();p=self.out/f'ordinary/{i}.bin';q=self.rec/f'controls/ordinary/{i}.bin'
            a=put(p,raw);put(q,raw)
            original_pairs.append(dict(original=str(p),copy=str(q),bytes=a['bytes'],sha256=a['sha256']))
        self.r['preservation']=dict(head=self.fixed['head'],tested_head=self.fixed['tested_head'],originals_preserved=True,
            full_generated_backup=False,files=original_pairs,files_bytes=sum(p['bytes'] for p in original_pairs))
        self.r['owner']=dict(status='child_exited',worker_returncode=0,cleanup_complete=True,output_capture_complete=True,stdout_bytes=4,stderr_bytes=0)
        self.r['terminal']=dict(owner=self.r['owner'],passed=True,source_equal=True,meter_closed=True,faults=[])
        self.r['public_terminal']=dict(returncode=0)
        reports=[put(self.root/f'apps/android/app/build/test-results/testDebugUnitTest/TEST-{i}.xml',b'closed opaque XML') for i in range(55)]
        lint=put(self.root/'apps/android/app/build/reports/lint-results-debug.xml',b'closed opaque lint')
        artifacts={}
        for role,p in self.fixed['apks'].items():artifacts[role]=dict(original=p,copy=put(self.out/f'apks-v1/{role}.apk',Path(p['path']).read_bytes()))
        self.r['build']=dict(head=self.fixed['tested_head'],source_count=self.fixed['tested_count'],android_runtime_executed=False,
            full_cache_or_TEMP_meter=False,jvm=dict(counts=dict(tests=454,failures=0,errors=0,skipped=0),reports=reports),
            new_ui_methods_compiled=3,terminal=self.r['terminal'],public_terminal=self.r['public_terminal'],
            lint=dict(binding=lint),native=native,artifacts=artifacts,
            stdout=put(self.out/'host-build-v1/owner-stdout-v1.bin',b'pass'),stderr=put(self.out/'host-build-v1/owner-stderr-v1.bin',b''),
            public_audits=[dict(status='passed',permissions=[],libraries=[]),dict(status='passed',package='org.locallore.app',
                test_package='org.locallore.app.test',certificate_sha256=self.fixed['certificate'],test_permissions=[],
                app={k:self.fixed['apks']['product_apk'][k] for k in ('bytes','sha256')},
                test={k:self.fixed['apks']['test_apk'][k] for k in ('bytes','sha256')})])
        self.r['build_review']=dict(blocking_findings=[],source_before_after_current_zip_equal=True,jvm_cases=454,jvm_xml=55,
            jvm_failures=0,jvm_errors=0,jvm_skipped=0,new_annotated_ui_methods=3,runtime_test_execution=False)
        helper=put(self.out/'host-build-v1/run-v1.py',b'reviewed producer source')
        worker=dict(pid=10,creation_filetime=100,executable='C:/Synthetic/python.exe')
        command=[worker['executable'],'-I','-S','-B','scripts/check.py','android','--offline']
        self.r['actual_child']=dict(helper=helper,identity=worker)
        self.r['public_start']=dict(worker=worker,cwd=str(self.root),command=command)
        self.r['public_child']=dict(identity=dict(worker,pid=11),command=command)
        self.r['request']=dict(head=self.fixed['tested_head'],seconds=900,helper=helper)
        dex_inputs={key:put(self.home/f'dex-input/{key}.py',('recorded '+key).encode()) for key in ('contract','reader','dex_parser')}
        self.r['dex']=dict(product_head=self.fixed['head'],tested_head=self.fixed['tested_head'],app=self.fixed['apks']['product_apk'],
            test=self.fixed['apks']['test_apk'],count=14,rows=dexrows,new_and_previous_methods_checked_current_apk=True,
            device_runtime_or_aapt_execution=False,imports_before_external_operation_trap=True,**dex_inputs)
        # These records bind one another; publish in dependency order.
        for key in ('before','after','final_source','preservation'):
            self.record(key)
        self.r['request']['source_map']=self.refs['before']
        self.r['reviews']=dict(head=self.fixed['head'],tested_head=self.fixed['tested_head'],passed=True,pair_original_copy_original_after=True,
            receipt_topology_exact=True,pair_count=85,source_current_raw_and_zip=True,source_count=self.fixed['source_count'],
            documentation_only_delta=b.DOC_DELTA,receipt=self.refs['preservation'])
        for key in self.r:
            if key not in self.refs:self.record(key)
        self.value=dict(version=1,scope=b.MODE,product=self.fixed,refs=self.refs,roster=copy.deepcopy(b.ROSTER),facts=copy.deepcopy(b._FACTS),
            native=native,documentation_only_delta=b.DOC_DELTA,preserved_controls=dict(count=85,bytes=self.r['preservation']['files_bytes']),
            source_encoding=b.SOURCE_ENCODING,dex_inputs=dex_inputs)
        self.seal()

    def paths(self):
        with patch.object(b,'_FIXED',self.fixed):return b._paths()
    def record(self,key):self.refs[key]=put(self.paths()[key],encoded(self.r[key]))
    def seal(self):
        self.baseline.write_bytes(encoded(self.value));self.baseline_pin=pin(self.baseline)
    def git(self,args):
        if args[0]=='rev-parse':return (self.fixed['head']+'\n').encode()
        if args[0]=='status':return b''
        if args==['ls-files','-z']:return ('\0'.join(self.source)+'\0').encode()
        raise AssertionError('unexpected Git query')
    def patches(self):
        return patch.multiple(b,_FIXED=self.fixed,BASELINE_PATH=self.baseline,BASELINE_BYTES=self.baseline_pin['bytes'],
                              BASELINE_SHA256=self.baseline_pin['sha256'],_git=self.git)


@unittest.skipUnless(os.name=='nt','Physical D: byte-backed host fixtures')
class ProfileBuildTests(unittest.TestCase):
    def setUp(self):
        self.g=Graph();self.stack=ExitStack();self.addCleanup(self.stack.close);self.stack.enter_context(self.g.patches())
        for target in ('socket.socket','socket.create_connection','subprocess.run','subprocess.Popen'):
            self.stack.enter_context(patch(target,side_effect=AssertionError('external operation forbidden')))

    def test_complete_current_graph_retains_fourteen_roles_without_publication_or_aliasing(self):
        result=b.create_manifest()
        self.assertEqual(len(result['roster']),14);self.assertEqual(result['roster'],b.ROSTER)
        self.assertEqual(result['validation_mode'],'fixed-b62-byte-attestation-v1')
        self.assertFalse(Path(self.g.fixed['manifest']).exists())
        self.assertFalse(result['recorded_execution']['facts']['deep_semantic_review_repeated'])
        result['roster'][0][0]='other';self.assertNotEqual(result['roster'],b.create_manifest()['roster'])

    def test_manifest_exact_roles_root_and_old_family_retag_refuse(self):
        path=Path(self.g.fixed['manifest']);put(path,encoded(b.create_manifest()))
        artifacts=dict(build=pin(path),**self.g.fixed['apks'])
        self.assertEqual(b.verify_frozen_product(artifacts)['roster'],b.ROSTER)
        for kind in ('role','swap','root','family','extra'):
            changed=copy.deepcopy(artifacts)
            if kind=='role':changed['model']=changed['build']
            elif kind=='swap':changed['product_apk'],changed['test_apk']=changed['test_apk'],changed['product_apk']
            elif kind=='root':changed['build']['path']=str(self.g.home/'foreign.json')
            else:
                value=b.create_manifest()
                if kind=='family':value['scope']='inventory-ui-build-v1'
                else:value['spec']={'root':'D:/unselected'}
                path.write_bytes(encoded(value));changed['build']=pin(path)
            with self.subTest(kind=kind),self.assertRaises(b.BuildRefused):b.verify_frozen_product(changed)

    def test_fixed_evidence_mutations_cannot_be_resealed_by_admission(self):
        for key in ('build','dex','reviews','public_child','owner','final_archive','tested_archive'):
            path=Path(self.g.refs[key]['path']);old=path.read_bytes();path.write_bytes(old+b'changed')
            with self.subTest(key=key),self.assertRaises(b.BuildRefused):b.create_manifest()
            path.write_bytes(old)

    def test_source_raw_newline_changes_and_unlisted_source_bytes_refuse(self):
        for name in ('src/lib.rs','README.md'):
            p=self.g.root/name;raw=p.read_bytes();p.write_bytes(raw+b'\r\n')
            with self.subTest(name=name),self.assertRaises(b.BuildRefused):b.create_manifest()
            p.write_bytes(raw)

    def test_git_dirty_roster_and_fixed_head_drift_refuse(self):
        for kind in ('dirty','roster','head'):
            def git(args):
                if kind=='dirty' and args[0]=='status':return b'?? other\n'
                if kind=='roster' and args[0]=='ls-files':return b'other\0'
                if kind=='head' and args[0]=='rev-parse':return b'0'*40+b'\n'
                return self.g.git(args)
            with self.subTest(kind=kind),patch.object(b,'_git',side_effect=git),self.assertRaises(b.BuildRefused):b.create_manifest()

    def test_baseline_and_json_shapes_reject_duplicate_boolean_and_extra_fields(self):
        for raw in (b'{"key":1,"key":2}',b'{"key":Infinity}'):
            with self.assertRaises(b.BuildRefused):b._json(raw)
        original=self.g.baseline.read_bytes();self.g.baseline.write_bytes(original+b' ')
        with self.assertRaises(b.BuildRefused):b.create_manifest()
        self.g.baseline.write_bytes(original)
        for bad in (dict(self.g.baseline_pin,bytes=True),dict(self.g.baseline_pin,sha256='A'*64),dict(self.g.baseline_pin,extra=True)):
            with self.assertRaises(b.BuildRefused):b._Reader().read(bad)

    def test_cargo_exact_two_names_same_object_and_no_third_alias(self):
        row=self.g.value['native'][0];alias=Path(row['cargo_alias']['path'])
        alias.rename(alias.with_suffix('.retained'));put(alias,Path(row['release']['path']).read_bytes())
        os.link(alias,alias.with_suffix('.foreign'))
        with self.assertRaises(b.BuildRefused):b.create_manifest()
        release=Path(self.g.value['native'][1]['release']['path']);os.link(release,release.with_suffix('.third'))
        with self.assertRaises(b.BuildRefused):b._Reader().native_pair(self.g.value['native'][1]['release'],self.g.value['native'][1]['cargo_alias'])

    def test_apk_source_and_control_hardlinks_never_receive_cargo_exception(self):
        for path in (self.g.root/'src/lib.rs',Path(self.g.fixed['apks']['product_apk']['path']),Path(self.g.refs['owner']['path'])):
            os.link(path,path.with_suffix('.alias'))
            with self.subTest(path=path.name),self.assertRaises(b.BuildRefused):b._Reader().read(pin(path))
        with self.assertRaises(b.BuildRefused):b._Reader().read(self.g.value['native'][0]['release'])

    def test_xml_and_retained_copy_change_cannot_keep_recorded_good_result(self):
        for path in (Path(self.g.r['build']['jvm']['reports'][0]['path']),Path(self.g.r['preservation']['files'][0]['copy'])):
            raw=path.read_bytes();path.write_bytes(raw+b'<failure>hidden</failure>')
            with self.subTest(name=path.name),self.assertRaises(b.BuildRefused):b.create_manifest()
            path.write_bytes(raw)

    def test_held_final_identity_and_deadline_are_not_just_initial_checks(self):
        path=self.g.root/'src/lib.rs';reader=b._Reader();reader.read(pin(path));path.write_bytes(b'late mutation')
        with self.assertRaises(b.BuildRefused):reader.final()
        reader=b._Reader();reader.until=0
        with self.assertRaises(b.BuildRefused):reader.read(pin(path))

    def test_recorded_dex_body_bound_is_exact_8192_not_a_generic_uint16(self):
        record=self.g.r['dex']
        record['rows'][0]['code_units']=8192
        b._dex(b._Reader(),self.g.value,self.g.r)
        record['rows'][0]['code_units']=8193
        with self.assertRaises(b.BuildRefused):b._dex(b._Reader(),self.g.value,self.g.r)

    def test_growing_json_refuses_without_reading_beyond_declared_size_plus_one(self):
        path=self.g.home/'growing.json';original=put(path,b'{}\n');reader=b._Reader()
        real_open=Path.open;consumed=[]
        class Stream:
            def __init__(self,stream):self.stream=stream;self.first=True
            def __enter__(self):return self
            def __exit__(self,*args):return self.stream.__exit__(*args)
            def fileno(self):return self.stream.fileno()
            def read(self,size):
                data=self.stream.read(size);consumed.append(len(data))
                if self.first:
                    self.first=False
                    with real_open(path,'ab') as destination:destination.write(b'x'*4096)
                return data
        def open_stream(p,*args,**kwargs):
            stream=real_open(p,*args,**kwargs)
            return Stream(stream) if p==path and args==('rb',) else stream
        with patch.object(Path,'open',open_stream),self.assertRaises(b.BuildRefused):reader.read(original,data=True)
        self.assertLessEqual(sum(consumed),original['bytes']+1)
        self.assertLessEqual(reader.total,original['bytes']+1)

    def test_source_import_performs_no_filesystem_or_process_io(self):
        source=Path(b.__file__).read_bytes()
        with patch('builtins.open',side_effect=AssertionError('import IO')),patch.object(Path,'open',side_effect=AssertionError('import IO')):
            value={'__file__':b.__file__,'__name__':'import_only'};exec(compile(source,b.__file__,'exec'),value)
        self.assertTrue(callable(value['verify_current']))


if __name__=='__main__':unittest.main()
