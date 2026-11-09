"""Original tiny B66-shaped byte graphs, not XML/DEX/ELF or Android qualifications.

All artifact bytes are real D: files. Only Git observation and private fixed
baseline authority are coherently substituted; no validation verdict is stubbed.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from benchmarks import record_controls_ui_build as b

FIXTURES=Path('D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-harness-v1/build-fixtures-v1')

def encoded(value): return json.dumps(value,sort_keys=True).encode()
def pin(path):
    raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream: stream.write(raw)
    return pin(path)


class Graph:
    """Opaque synthetic payloads prove byte/identity joins only, never test results."""
    def __init__(self):
        FIXTURES.mkdir(parents=True,exist_ok=True)
        self.home=Path(tempfile.mkdtemp(prefix='record-graph-',dir=FIXTURES))
        self.fixed=copy.deepcopy(b._FIXED)
        self.root,self.out,self.rec=(self.home/name for name in ('product','capture','recovery'))
        self.fixed.update(root=str(self.root),capture=str(self.out),recovery=str(self.rec),manifest=str(self.home/'manifest.json'))
        self.baseline=self.home/'baseline.json'; self.refs={}; self.r={}; self.source={}
        for name,raw in [('src/lib.rs',b'actual synthetic source'),(b.NATIVE_FIXTURE,b'formatted native fixture')]+[(n,('current '+n).encode()) for n in b.DOC_DELTA]:
            self.source[name]=put(self.root/name,raw)
        dexrows=[]
        for i,(kind,klass,method) in enumerate(b.ROSTER):
            name='apps/android/app/src/androidTest/java/'+klass.replace('.','/')+'.kt'
            if name not in self.source: self.source[name]=put(self.root/name,b'opaque reviewed source bytes')
            dexrows.append(dict(kind=kind,**{'class':klass},method=method,runtime_junit=True,
                public_concrete_instance_void_noargs=True,code_units=100+i,
                product_class_family_absent=True,source=self.source[name]))
        self.fixed.update(source_count=len(self.source),tested_count=len(self.source)-1)
        before=[]
        for name,p in self.source.items():
            if name==b.DOC_DELTA[1]: continue
            raw=(b'unformatted native fixture' if name==b.NATIVE_FIXTURE else
                 b'previous documentation' if name in b.DOC_DELTA else (self.root/name).read_bytes())
            before.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        native=copy.deepcopy(before)
        for row in native:
            if row['path']==b.NATIVE_FIXTURE: row.update({k:self.source[b.NATIVE_FIXTURE][k] for k in ('bytes','sha256')})
        self.r['before']=dict(head=self.fixed['tested_head'],files=before)
        self.r['after']=copy.deepcopy(self.r['before'])
        self.r['native_before']=dict(head=self.fixed['native_tested_head'],files=native)
        self.r['native_after']=copy.deepcopy(self.r['native_before'])
        for role,name in [('product_apk','app-debug.apk'),('test_apk','app-debug-androidTest.apk')]:
            self.fixed['apks'][role]=put(self.root/name,('attested synthetic '+role).encode())
        for key in ('tested_archive','native_archive','helper','stdout','stderr'):
            self.refs[key]=put(self.paths()[key],('opaque reviewed '+key).encode())
        overlays=[]
        for name in b.DOC_DELTA:
            q=put(self.out/'final-docs-v2'/name,(self.root/name).read_bytes())
            overlays.append(dict(path=name,copy=q['path'],bytes=q['bytes'],sha256=q['sha256']))
        self.r['final_source']=dict(head=self.fixed['head'],previous_final_head=self.fixed['previous_head'],
            files=[dict(path=n,bytes=p['bytes'],sha256=p['sha256']) for n,p in self.source.items()],
            source_count=len(self.source),tested_source_zip=self.refs['native_archive'],
            documentation_only_delta=overlays,production_unchanged=True,prior_snapshot_retained=True)
        self.r['previous_source']=dict(head=self.fixed['previous_head'],files=[])
        self.native=[]
        for target,abi in [('x86_64-linux-android','x86_64'),('aarch64-linux-android','arm64-v8a')]:
            base=self.root/'apps/android/app/build'; release=base/f'rust-target/{target}/release/liblocallore_android.so'
            alias=release.parent/'deps/liblocallore_android.so'
            put(release,('release '+abi).encode()); alias.parent.mkdir(); os.link(release,alias)
            row=dict(abi=abi,release=pin(release),cargo_alias=pin(alias))
            for key,name in [('generated',f'generated/rustJniLibs/{abi}/liblocallore_android.so'),
                ('merged',f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so'),
                ('stripped',f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so')]:
                row[key]=put(base/name,release.read_bytes() if key!='stripped' else ('stripped '+abi).encode())
            row['apk_sha256']=row['stripped']['sha256']; self.native.append(row)
        pairs={}
        for kind,subdir,count in [('controls','controls',109),('addendum','addendum-v1',8)]:
            rows=[]
            for i in range(count):
                p=self.out/f'{kind}/{i}.bin'; q=self.rec/subdir/f'{kind}/{i}.bin'
                a=put(p,('control '+kind+str(i)).encode());put(q,p.read_bytes())
                rows.append(dict(original=str(p),copy=str(q),bytes=a['bytes'],sha256=a['sha256']))
            pairs[kind]=rows
        artifacts={}
        for role,p in self.fixed['apks'].items():
            key='app' if role=='product_apk' else 'test'
            artifacts[key]=dict(original=p,copy=put(self.rec/'apks-v1'/Path(p['path']).name,Path(p['path']).read_bytes()))
        self.r['preservation']=dict(head=self.fixed['previous_head'],source_count=len(self.source),files=pairs['controls'],
            pair_count=109,control_bytes=sum(p['bytes'] for p in pairs['controls']),artifacts=artifacts,
            full_generated_cache_or_TEMP_backup=False)
        self.r['addendum']=dict(head=self.fixed['head'],prior_final_head=self.fixed['previous_head'],
            files=pairs['addendum'],pair_count=8,copied_bytes=sum(p['bytes'] for p in pairs['addendum']),
            previous_109_pairs_and_apks_unchanged=True,source_count=len(self.source))
        self.r['owner']=dict(status='child_exited',worker_returncode=0,cleanup_complete=True,output_capture_complete=True,
            stdout_bytes=self.refs['stdout']['bytes'],stderr_bytes=self.refs['stderr']['bytes'])
        self.r['terminal']=dict(passed=True,source_equal=True,faults=[],owner=self.r['owner'])
        self.r['command_terminal']=dict(returncode=0)
        worker=dict(pid=10,creation_filetime=100,executable='C:/Synthetic/python.exe')
        command=[worker['executable'],'-I','-S','-B','scripts/check.py','android','--offline']
        helper={k:self.refs['helper'][k] for k in ('bytes','sha256')}
        self.r['request']=dict(head=self.fixed['tested_head'],cwd=str(self.root),seconds=900,helper=helper,
            owner=dict(worker,pid=9),command=command)
        self.r['actual_child']=dict(identity=worker,helper=helper)
        self.r['command_child']=dict(identity=dict(worker,pid=11),command=command)
        reports=[]
        for i in range(58):
            p=self.root/f'apps/android/app/build/test-results/testDebugUnitTest/TEST-{i}.xml'
            original=put(p,b'opaque recorded report, not a synthetic JUnit qualification')
            reports.append(dict(original=original,copy=put(self.out/'reports-v1'/p.name,p.read_bytes())))
        lint=self.root/'apps/android/app/build/reports/lint-results-debug.xml'
        original=put(lint,b'opaque recorded lint')
        cases=[['org.locallore.app.PromiseStatusBrowseTest',f'new{i}'] for i in range(12)]+[['synthetic.Recorded',f'old{i}'] for i in range(467)]
        self.r['build']=dict(head=self.fixed['native_tested_head'],jvm_methods=479,jvm_reports=58,jvm_failures_errors_skips=[0,0,0],
            new_compose_executed=False,new_dependency_or_device_operation=False,cases=cases,reports=reports,
            lint=dict(original=original,copy=put(self.out/'reports-v1'/lint.name,lint.read_bytes())),
            lint_severities={'Warning':1,'Hint':1},artifacts=artifacts,
            public_audits=[dict(status='passed',permissions=[],libraries=[{}]*4),
                dict(status='passed',package='org.locallore.app',test_package='org.locallore.app.test',
                    certificate_sha256=self.fixed['certificate'],test_permissions=[],
                    app={k:self.fixed['apks']['product_apk'][k] for k in ('bytes','sha256')},
                    test={k:self.fixed['apks']['test_apk'][k] for k in ('bytes','sha256')})])
        self.r['build_review']=dict(findings=[],jvm_unique_methods=479,jvm_xml_reports=58,failures_errors_skips=[0,0,0],
            report_original_copy_pairs_checked=58,android_production_source_unchanged=True,android_ui_executed=False,
            captured_signer_audit_matches_artifact_hashes=True,certificate_sha256=self.fixed['certificate'])
        self.dex_inputs={k:put(self.home/f'dex-input/{k}.py',('recorded '+k).encode()) for k in ('contract','reader','dex_parser')}
        self.r['current']=dict(scope='record-controls-ui-current-artifact-readback-v2',product_head=self.fixed['head'],
            tested_head=self.fixed['tested_head'],native_tested_head=self.fixed['native_tested_head'],apks=self.fixed['apks'],
            count=19,roster=b.ROSTER,rows=dexrows,runtime_execution=False,
            build_or_semantic_apk_ELF_signer_audit_repeated=False,**self.dex_inputs,
            native=[dict(row,release_alias_links=2) for row in self.native])
        self.r['prior_limitation']=dict(prior_packet='B65',prior_xml_count=57,regenerated_xml_count=57,
            historical_capture_or_receipt_rewritten=False)
        for key in ('before','after','native_before','native_after','final_source','previous_source','preservation','addendum','terminal'):
            self.record(key)
        self.r['build']['phases']={'android-v1':dict(head=self.fixed['tested_head'],source_count=self.fixed['tested_count'],
            owner=self.r['owner'],terminal=self.refs['terminal'],command=command)}
        self.r['reviews']=dict(head=self.fixed['previous_head'],findings=[],controls_verified=109,
            control_bytes=self.r['preservation']['control_bytes'],artifacts_verified=2,source_files_verified=len(self.source),
            receipt=self.refs['preservation'])
        self.record('reviews')
        self.r['addendum_review']=dict(head=self.fixed['head'],findings=[],new_original_copy_original_after_pairs=8,
            new_copied_bytes=self.r['addendum']['copied_bytes'],all_2570_current_raw_source_and_zip_overlay_reconstruction_verified=True,
            same_native_v2_zip_crc_and_roster_verified=True,addendum=self.refs['addendum'],
            prior_109_pair_receipt_unchanged={k:self.refs['preservation'][k] for k in ('bytes','sha256')},
            prior_independent_reader_unchanged={k:self.refs['reviews'][k] for k in ('bytes','sha256')},
            report_explicitly_records_B65_final_57_XML_not_archived_or_recoverable=True)
        for key in self.r:
            if key not in self.refs:self.record(key)
        self.value=dict(version=1,scope=b.MODE,product=self.fixed,refs=self.refs,roster=copy.deepcopy(b.ROSTER),facts=copy.deepcopy(b._FACTS),
            native=self.native,documentation_only_delta=b.DOC_DELTA,
            preserved_controls={name:dict(count=len(rows),bytes=sum(r['bytes'] for r in rows)) for name,rows in pairs.items()},
            source_encoding=b.SOURCE_ENCODING,dex_inputs=self.dex_inputs)
        self.seal()

    def paths(self):
        with patch.object(b,'_FIXED',self.fixed): return b._paths()
    def record(self,key): self.refs[key]=put(self.paths()[key],encoded(self.r[key]))
    def seal(self):
        self.baseline.write_bytes(encoded(self.value)); self.baseline_pin=pin(self.baseline)
    def git(self,args):
        if args[0]=='rev-parse': return (self.fixed['head']+'\n').encode()
        if args[0]=='status': return b''
        if args==['ls-files','-z']: return ('\0'.join(self.source)+'\0').encode()
        raise AssertionError('unexpected Git query')
    def patches(self):
        return patch.multiple(b,_FIXED=self.fixed,BASELINE_PATH=self.baseline,BASELINE_BYTES=self.baseline_pin['bytes'],
            BASELINE_SHA256=self.baseline_pin['sha256'],_git=self.git)


@unittest.skipUnless(os.name=='nt','Physical D: byte-backed host fixtures')
class RecordControlsBuildTests(unittest.TestCase):
    def setUp(self):
        self.g=Graph();self.stack=ExitStack();self.addCleanup(self.stack.close);self.stack.enter_context(self.g.patches())
        for target in ('socket.socket','socket.create_connection','subprocess.run','subprocess.Popen'):
            self.stack.enter_context(patch(target,side_effect=AssertionError('external operation forbidden')))

    def test_complete_b66_graph_preserves_nineteen_scoped_roles_without_publishing(self):
        result=b.create_manifest()
        self.assertEqual(result['roster'],b.ROSTER);self.assertEqual(len(result['roster']),19)
        self.assertEqual(result['validation_mode'],'fixed-b66-byte-attestation-v1')
        self.assertFalse(Path(self.g.fixed['manifest']).exists())
        self.assertFalse(result['recorded_execution']['facts']['deep_semantic_review_repeated'])
        self.assertEqual(result['recorded_execution']['facts']['prior_exact_generated_xml_unrecoverable'],57)
        result['roster'][0][0]='other';self.assertEqual(b.create_manifest()['roster'],b.ROSTER)

    def test_manifest_retag_extra_roles_swapped_apks_and_foreign_root_refuse(self):
        path=Path(self.g.fixed['manifest']);put(path,encoded(b.create_manifest()))
        artifacts=dict(build=pin(path),**self.g.fixed['apks'])
        self.assertEqual(b.verify_frozen_product(artifacts)['roster'],b.ROSTER)
        for kind in ('model','swap','root','sdk13','extra'):
            changed=copy.deepcopy(artifacts)
            if kind=='model':changed['model']=changed['build']
            elif kind=='swap':changed['product_apk'],changed['test_apk']=changed['test_apk'],changed['product_apk']
            elif kind=='root':changed['build']['path']=str(self.g.home/'foreign.json')
            else:
                value=b.create_manifest()
                if kind=='sdk13':value['scope']='profile-ui-build-v1'
                else:value['spec']={'root':'D:/unselected'}
                path.write_bytes(encoded(value));changed['build']=pin(path)
            with self.subTest(kind=kind),self.assertRaises(b.BuildRefused):b.verify_frozen_product(changed)

    def test_evidence_hash_tampering_is_not_resealed_by_admission(self):
        for key in ('build','current','reviews','addendum_review','command_child','owner','native_archive','tested_archive','helper'):
            path=Path(self.g.refs[key]['path']);raw=path.read_bytes();path.write_bytes(raw+b'changed')
            with self.subTest(key=key),self.assertRaises(b.BuildRefused):b.create_manifest()
            path.write_bytes(raw)

    def test_current_source_oracle_overlay_and_raw_newline_changes_refuse(self):
        names=['src/lib.rs',b.DOC_DELTA[1],b.NATIVE_FIXTURE]+[n for n in self.g.source if n.endswith('PromiseStatusScreenTest.kt')]
        for name in names:
            path=self.g.root/name;raw=path.read_bytes();path.write_bytes(raw+b'\r\n')
            with self.subTest(name=name),self.assertRaises(b.BuildRefused):b.create_manifest()
            path.write_bytes(raw)
        overlay=Path(self.g.r['final_source']['documentation_only_delta'][0]['copy'])
        overlay.write_bytes(b'replaced overlay')
        with self.assertRaises(b.BuildRefused):b.create_manifest()

    def test_git_head_dirty_and_roster_drift_refuse(self):
        for kind in ('head','dirty','roster'):
            def git(args):
                if kind=='head' and args[0]=='rev-parse':return b'0'*40+b'\n'
                if kind=='dirty' and args[0]=='status':return b'?? unreviewed\n'
                if kind=='roster' and args[0]=='ls-files':return b'other\0'
                return self.g.git(args)
            with self.subTest(kind=kind),patch.object(b,'_git',side_effect=git),self.assertRaises(b.BuildRefused):b.create_manifest()

    def test_baseline_json_duplicate_nonfinite_boolean_and_extra_fields_refuse(self):
        for raw in (b'{"key":1,"key":2}',b'{"key":Infinity}'):
            with self.assertRaises(b.BuildRefused):b._json(raw)
        path=self.g.baseline;raw=path.read_bytes();path.write_bytes(raw+b' ')
        with self.assertRaises(b.BuildRefused):b.create_manifest()
        path.write_bytes(raw)
        for bad in (dict(self.g.baseline_pin,bytes=True),dict(self.g.baseline_pin,sha256='A'*64),dict(self.g.baseline_pin,extra=True)):
            with self.assertRaises(b.BuildRefused):b._Reader().read(bad)

    def test_cargo_alias_must_be_the_exact_two_names_of_one_object(self):
        row=self.g.value['native'][0];alias=Path(row['cargo_alias']['path'])
        alias.rename(alias.with_suffix('.retained'));put(alias,Path(row['release']['path']).read_bytes())
        os.link(alias,alias.with_suffix('.foreign'))
        with self.assertRaises(b.BuildRefused):b.create_manifest()
        row=self.g.value['native'][1];release=Path(row['release']['path']);os.link(release,release.with_suffix('.third'))
        with self.assertRaises(b.BuildRefused):b._Reader().native_pair(row['release'],row['cargo_alias'])

    def test_source_apk_controls_and_stripped_native_never_gain_cargo_exception(self):
        paths=[self.g.root/'src/lib.rs',Path(self.g.fixed['apks']['product_apk']['path']),
            Path(self.g.refs['owner']['path']),Path(self.g.native[0]['stripped']['path'])]
        for path in paths:
            os.link(path,path.with_suffix('.alias'))
            with self.subTest(name=path.name),self.assertRaises(b.BuildRefused):b._Reader().read(pin(path))

    def test_report_lint_and_both_recovery_generations_are_fresh_byte_checks(self):
        paths=[Path(self.g.r['build']['reports'][0]['original']['path']),Path(self.g.r['build']['reports'][0]['copy']['path']),
            Path(self.g.r['build']['lint']['copy']['path']),Path(self.g.r['preservation']['files'][0]['copy']),
            Path(self.g.r['addendum']['files'][0]['copy'])]
        for path in paths:
            raw=path.read_bytes();path.write_bytes(raw+b'mutated')
            with self.subTest(path=str(path)),self.assertRaises(b.BuildRefused):b.create_manifest()
            path.write_bytes(raw)

    def test_recorded_selector_bodies_flags_and_sources_are_not_name_only(self):
        for index in (0,14,18):
            for key,value in [('code_units',0),('code_units',8193),('code_units',True),('runtime_junit',False),
                              ('product_class_family_absent',False),('public_concrete_instance_void_noargs',False)]:
                record=copy.deepcopy(self.g.r);record['current']['rows'][index][key]=value
                with self.subTest(index=index,key=key),self.assertRaises(b.BuildRefused):b._dex(b._Reader(),self.g.value,record)
        record=copy.deepcopy(self.g.r);record['current']['rows'][-1]['code_units']=8192
        b._dex(b._Reader(),self.g.value,record)
        record['current']['rows'][-1]['source']=self.g.source['src/lib.rs']
        with self.assertRaises(b.BuildRefused):b._dex(b._Reader(),self.g.value,record)

    def test_actual_producer_identity_command_and_cleanup_joins_refuse_drift(self):
        for kind in ('pid','helper','command','cleanup','result'):
            record=copy.deepcopy(self.g.r)
            if kind=='pid':record['command_child']['identity']=record['actual_child']['identity']
            elif kind=='helper':record['request']['helper']['sha256']='0'*64
            elif kind=='command':record['command_child']['command'][-1]='--online'
            elif kind=='cleanup':record['owner']['cleanup_complete']=False
            else:record['command_terminal']['returncode']=True
            with self.subTest(kind=kind),self.assertRaises(b.BuildRefused):b._execution(b._Reader(),self.g.value,record)

    def test_retention_late_generation_cannot_erase_prior_missing_xml_limit(self):
        for kind in ('missing','copy','review','limit'):
            record=copy.deepcopy(self.g.r)
            if kind=='missing':record['addendum']['files'].pop()
            elif kind=='copy':record['addendum']['files'][0]['copy']=record['preservation']['files'][0]['copy']
            elif kind=='review':record['addendum_review']['findings']=['not closed']
            else:record['prior_limitation']['regenerated_xml_count']=0
            with self.subTest(kind=kind),self.assertRaises(b.BuildRefused):b._retention(b._Reader(),self.g.value,record)

    def test_held_final_identity_deadline_and_declared_size_bound_survive_late_changes(self):
        path=self.g.root/'src/lib.rs';reader=b._Reader();reader.read(pin(path));path.write_bytes(b'late mutation')
        with self.assertRaises(b.BuildRefused):reader.final()
        reader=b._Reader();reader.until=0
        with self.assertRaises(b.BuildRefused):reader.read(pin(path))
        growing=self.g.home/'growing.json';original=put(growing,b'{}\n');reader=b._Reader();real=Path.open;consumed=[]
        class Stream:
            def __init__(self,stream):self.stream=stream;self.first=True
            def __enter__(self):return self
            def __exit__(self,*args):return self.stream.__exit__(*args)
            def fileno(self):return self.stream.fileno()
            def read(self,size):
                raw=self.stream.read(size);consumed.append(len(raw))
                if self.first:
                    self.first=False
                    with real(growing,'ab') as destination:destination.write(b'x'*4096)
                return raw
        def opened(p,*args,**kwargs):
            stream=real(p,*args,**kwargs)
            return Stream(stream) if p==growing and args==('rb',) else stream
        with patch.object(Path,'open',opened),self.assertRaises(b.BuildRefused):reader.read(original,data=True)
        self.assertLessEqual(sum(consumed),original['bytes']+1)

    def test_source_import_performs_no_file_process_or_target_io(self):
        source=Path(b.__file__).read_bytes()
        with patch('builtins.open',side_effect=AssertionError('import IO')),patch.object(Path,'open',side_effect=AssertionError('import IO')):
            value={'__file__':b.__file__,'__name__':'import_only'};exec(compile(source,b.__file__,'exec'),value)
        self.assertTrue(callable(value['verify_current']))

    def test_fixed_contract_entry_revalidates_inputs_around_real_byte_validation(self):
        path=Path(self.g.fixed['manifest']);put(path,encoded(b.create_manifest()))
        admission={'artifacts':dict(build=pin(path),**self.g.fixed['apks'])}
        module=types.ModuleType('benchmarks.owned_record_controls_ui_contract');seen=[]
        def validate(value):
            seen.append('validate');return copy.deepcopy(value)
        module.validate_admission=validate
        module.revalidate_inputs=lambda value:seen.append('revalidate')
        with patch.dict('sys.modules',{'benchmarks.owned_record_controls_ui_contract':module}), \
             patch.object(__import__('benchmarks'),'owned_record_controls_ui_contract',module,create=True):
            result=b.verify_current(admission)
        self.assertEqual(seen,['validate','revalidate','revalidate'])
        self.assertEqual(result['roster'],b.ROSTER)


if __name__=='__main__': unittest.main()
