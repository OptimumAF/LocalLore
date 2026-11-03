"""Original closed-byte graph oracles. No SDK, Android, model or run authority.

The private seam uses tiny retained D: files and the actual guarded reader.
The public loader tests use only this checkout's public baseline source bytes.
"""
import ast
import builtins
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET
import zipfile
import zlib

from benchmarks import record_cancellation_ui_build as b
from benchmarks import archive_ui_build as archive
from benchmarks import receipt_avd_environment as environment
from scripts import audit_physical_model_apk as dex_audit


PRIVATE = 'PRIVATE-B111-READER /unpublished/path'
METHODS = (
    'cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor',
    'cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens',
    'obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords',
    'oldDetailCancellationAfterBackCannotFinishTheReplacementDetail',
    'disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks',
)
VM_METHODS = ('pageCancellation', 'detailCancellation', 'obsoleteCancellation')
UI_CLASS = 'org.locallore.app.StoryRecordCancellationScreenTest'
VM_CLASS = 'org.locallore.app.StoryRecordCancellationViewModelTest'
REFUSED = (b.BuildRefused, archive.BuildRefused, environment.EnvironmentRefused, dex_audit.AuditError)


def encoded(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()


def git_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def git_tree(rows):
    """Fixture construction independent of the attestor's tree helper."""
    root = {}
    for row in rows:
        node = root
        parts = row['path'].split('/')
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = (row['mode'], row['git_blob'])
    def digest(node):
        data = b''
        for name, value in sorted(node.items(), key=lambda item:
                item[0].encode() + (b'/' if isinstance(item[1], dict) else b'')):
            mode, sha = ('40000', digest(value)) if isinstance(value, dict) else value
            data += mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(sha)
        return hashlib.sha1(b'tree ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    return digest(root)


def uleb(value):
    out = bytearray()
    while value >= 128:
        out.append((value & 127) | 128)
        value >>= 7
    out.append(value)
    return bytes(out)


def dex(names, owner, flags=17, access=17, units=1, annotated=True,
        result=b'V', parameters=0, defined=True):
    """Five same-class definitions; reference strings alone cannot pass.

    No production decoder generates this layout. Code is aligned at fixed
    disjoint offsets; checksums and positive return-void bodies are retained.
    """
    names = tuple(sorted(name.encode() for name in names))
    types = sorted({owner, b'V', b'I', result, b'Lorg/junit/Test;'})
    shorty = result + b'I' * parameters
    strings = sorted(set(types) | set(names) | {shorty})
    so = 112; to = so + 4 * len(strings); po = to + 4 * len(types)
    mo = po + 12; co = mo + 8 * len(names)
    out = bytearray(co + (32 if defined else 0))
    out[:8] = b'dex\n039\0'
    struct.pack_into('<II', out, 36, 112, 0x12345678)
    for header, count, offset in ((56, len(strings), so), (64, len(types), to),
            (72, 1, po), (88, len(names), mo), (96, int(defined), co if defined else 0)):
        struct.pack_into('<II', out, header, count, offset)
    for index, value in enumerate(strings):
        struct.pack_into('<I', out, so + index * 4, len(out))
        out.extend(uleb(len(value)) + value + b'\0')
    for index, value in enumerate(types):
        struct.pack_into('<I', out, to + index * 4, strings.index(value))
    parameter_offset = 0
    if parameters:
        out.extend(bytes((-len(out)) % 4)); parameter_offset = len(out)
        out.extend(struct.pack('<I', parameters) + struct.pack('<' + 'H' * parameters,
            *([types.index(b'I')] * parameters)))
    struct.pack_into('<III', out, po, strings.index(shorty), types.index(result), parameter_offset)
    for index, name in enumerate(names):
        struct.pack_into('<HHI', out, mo + index * 8, types.index(owner), 0, strings.index(name))
    annotation_rows = []
    if annotated and defined:
        for index in range(len(names)):
            item = len(out); out.extend(b'\1' + uleb(types.index(b'Lorg/junit/Test;')) + b'\0')
            out.extend(bytes((-len(out)) % 4)); aset = len(out)
            out.extend(struct.pack('<II', 1, item)); annotation_rows.append((index, aset))
    directory = 0
    if annotation_rows:
        directory = len(out); out.extend(struct.pack('<IIII', 0, 0, len(annotation_rows), 0))
        for row in annotation_rows: out.extend(struct.pack('<II', *row))
    body = 0
    if defined:
        body = len(out)
        out.extend(b'\0\0' + (uleb(len(names)) + b'\0' if access & 8 else b'\0' + uleb(len(names))))
        previous = 0
        for index in range(len(names)):
            out.extend(uleb(index - previous) + uleb(access) + uleb(4096 + index * 128))
            previous = index
        struct.pack_into('<IIIIIIII', out, co, types.index(owner), flags, 0xffffffff,
            0, 0xffffffff, directory, body, 0)
        for index in range(len(names)):
            offset = 4096 + index * 128
            assert len(out) <= offset
            out.extend(bytes(offset - len(out)))
            out.extend(struct.pack('<HHHHII', 4, parameters + 1, 0, 0, 0, units))
            out.extend(b'\x0e\0' * max(1, units))
    struct.pack_into('<I', out, 32, len(out))
    out[12:32] = hashlib.sha1(out[32:]).digest()
    struct.pack_into('<I', out, 8, zlib.adler32(out[12:]) & 0xffffffff)
    return bytes(out)


def apk(raw, duplicate=False):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as z:
        z.writestr('classes.dex', raw)
        if duplicate: z.writestr('classes2.dex', raw)
    return stream.getvalue()


class Graph:
    """All SUT data paths remain under a unique retained D: fixture."""
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix='b111-attestation-'))
        assert self.root.drive.upper() == 'D:'
        self.product = self.root / 'product'; self.product.mkdir()
        self.base = dict(version=1, scope='record-cancellation-ui-build-baseline-v1',
            mode='fixed-b110-byte-attestation-v1', source_encoding=b.ENCODING,
            roots=dict(product=str(self.product), capture=str(self.root), manifest=str(self.root/'manifest.json')),
            product=dict(head='a'*40, tree='b'*40, tested_head='c'*40, tested_tree='d'*40,
                base='e'*40, base_count=1, tested_count=3, source_count=4),
            sources=[], phases=[], apks={}, copies={}, package={}, compiled={}, host_owner={})
        ui = 'package org.locallore.app\nclass StoryRecordCancellationScreenTest {\n' + ''.join(
            ' @Test fun ' + name + '() { check(true) }\n' for name in METHODS) + '}\n'
        vm = 'class StoryRecordCancellationViewModelTest {\n' + ''.join(
            ' @Test fun ' + name + '() { check(true) }\n' for name in VM_METHODS) + '}\n'
        self.source_bodies = {b.PARSER: b'# synthetic historical parser\n', b.UI_SOURCE: ui.encode(),
            b.VM_SOURCE: vm.encode(), b.REPORT: b'# synthetic final report\n'}
        self.sources()
        self.base['host_owner'] = self.put(self.root/'reviewed-owner.py', b'# synthetic checked host owner\n')
        h = self.base['host_owner']
        self.owner = dict(path=h['path'], sha256=h['sha256'], git_blob=git_blob((self.root/'reviewed-owner.py').read_bytes()),
            reviewed_pr361='096c517857c95fc854154bbf60d46cb85b6d6d74')
        self.records = {}
        for name in ('focused-v1', 'validation-v1', 'package-v1'):
            folder = self.root/name; folder.mkdir()
            phase = dict(name=name, junit=[])
            self.base['phases'].append(phase)
            worker = self.put(self.root/(name+'-worker.py'), b'# frozen synthetic worker\n'); phase['worker']=worker
            request = dict(command=b._expected_command(self.base,name), cwd=str(self.product/'apps/android'),
                source_base=self.base['product']['base'], limits=dict(gradle_deadline_seconds=170,
                parent_deadline_seconds=180,capture_bytes=8*1024**2,generated_postrun_planning_bytes=2*1024**3),
                environment=dict(TEMP='D:/Dev/_Temp',TMP='D:/Dev/_Temp',JAVA_HOME='C:/Program Files/Java/jdk-21',
                    ANDROID_HOME='C:/Users/Avery/AppData/Local/Android/Sdk',ANDROID_SDK_ROOT='C:/Users/Avery/AppData/Local/Android/Sdk',
                    GRADLE_USER_HOME='D:/Dev/Tools/Caches/Gradle',CARGO_HOME='D:/Dev/Tools/Caches/Cargo-LocalLore-v1'))
            required = ('buildRustAndroid','compileDebugKotlin','compileDebugUnitTestKotlin','testDebugUnitTest') if name=='focused-v1' else (
                ('testDebugUnitTest',) if name=='validation-v1' else ('compileDebugAndroidTestKotlin','assembleDebug',
                    'assembleDebugAndroidTest','lintAnalyzeDebug','lintReportDebug','lintDebug'))
            for key,value in dict(request=request, result={}, before=[],after=[]).items():
                filename={'before':'sources-before','after':'sources-after'}.get(key,key)+'.json'
                phase[key]=self.put(folder/filename, encoded(value))
            phase['owner']=self.put(self.root/(name+'-owner.json'), encoded(dict(status='completed',returncode=0,
                elapsed_ms=2000,stderr_bytes=0,cleanup_complete=True,owner=self.owner)))
            phase['launch']=self.put(self.root/(name+'-launch.json'), encoded(dict(command=[b._PYTHON,'-I','-S','-B',worker['path'],name],
                worker_bytes=worker['bytes'],worker_sha256=worker['sha256'],owner=self.owner,no_device_or_sdk_management=True)))
            phase['stdout']=self.put(folder/'stdout.txt', ('\n'.join('> Task :app:'+task for task in required)+'\nBUILD SUCCESSFUL in 1s\n').encode())
            phase['stderr']=self.put(folder/'stderr.txt',b'');phase['worker_stderr']=self.put(folder/'worker-stderr.txt',b'')
            if name!='package-v1':
                cases=[(VM_CLASS,VM_METHODS)]
                if name=='validation-v1':
                    cases += [('org.synthetic.Baseline'+str(i),tuple('case'+str(j) for j in range(9 if i<30 else 8))) for i in range(49)]
                for klass,names in cases:
                    root=ET.Element('testsuite',name=klass,tests=str(len(names)),failures='0',errors='0',skipped='0')
                    for method in names:ET.SubElement(root,'testcase',classname=klass,name=method)
                    phase['junit'].append(self.put(folder/'junit'/('TEST-'+klass+'.xml'),ET.tostring(root)))
        self.audit0=dict(status='passed',permissions=['org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'],
            libraries=[dict(entry='lib/'+abi+'/'+name,elf_load_alignment=[16384]*3) for abi in ('arm64-v8a','x86_64')
                for name in ('libandroidx.graphics.path.so','liblocallore_android.so')])
        self.audit1=dict(status='passed',package='org.locallore.app',test_package='org.locallore.app.test',
            test_permissions=['android.permission.REORDER_TASKS'],certificate_sha256=b._CERT,app={},test={})
        self.proof=dict(**{'class':UI_CLASS},class_access_flags=17,
            methods=[dict(name=name,**{'return':'void'},parameters=0,access_flags=17,runtime_junit_test=True) for name in METHODS],
            source_sha256=hashlib.sha256(self.source_bodies[b.UI_SOURCE]).hexdigest(),artifacts=[],
            compiled_junit_eligible_methods=5,instrumentation_executed=0,
            parser_source=dict(path=b.PARSER,sha256=hashlib.sha256(self.source_bodies[b.PARSER]).hexdigest()),qualification='Synthetic recorded definition proof; no Android execution')
        for i in (0,1):
            self.base['package']['audit_'+str(i)]={key:self.put(self.root/'package-v1'/('audit-'+str(i)+'-'+key+('.txt' if key in ('stdout','stderr') else '.json')),
                b'' if key=='stderr' else encoded({})) for key in ('request','result','stdout','stderr')}
        self.base['package']['lint']=self.put(self.root/'package-v1/lint.xml',b'<issues><issue id="GradleDependency" severity="Warning"/><issue id="AutoboxingStateCreation" severity="Hint"/></issues>')
        self.dex_options={};self.rebuild_apks();self.maps()

    def put(self,path,raw):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

    def replace(self,pin,raw):
        value=self.put(Path(pin['path']),raw);pin.clear();pin.update(value)

    def edit(self,pin,change):
        value=json.loads(Path(pin['path']).read_bytes());change(value);self.replace(pin,encoded(value))

    def sources(self):
        rows=[]
        for path,raw in sorted(self.source_bodies.items()):
            pin=self.put(self.product/path,raw)
            rows.append(dict(path=path,mode='100644',git_blob=git_blob(raw),bytes=pin['bytes'],sha256=pin['sha256']))
        self.base['sources']=rows;self.base['product']['tree']=git_tree(rows)
        self.base['product']['tested_tree']=git_tree([r for r in rows if r['path']!=b.REPORT])

    def maps(self):
        for p in self.base['phases']:
            omit={b.REPORT,b.UI_SOURCE} if p['name']=='focused-v1' else {b.REPORT}
            rows=[dict(path=r['path'],size=r['bytes'],sha256=r['sha256']) for r in self.base['sources'] if r['path'] not in omit]
            for key in ('before','after'):self.replace(p[key],encoded(rows))
            result=dict(exit=0,seconds=1.0,source_unchanged=True,source_files=len(rows),android_tree_bytes=1234,
                artifacts=self.artifacts() if p['name']=='package-v1' else [],instrumentation_executed=False)
            self.replace(p['result'],encoded(result))

    def artifacts(self):
        return [dict(path=self.base['apks'][role]['path'],copy=self.base['copies'][role]['path'],size=self.base['apks'][role]['bytes'],
            sha256=self.base['apks'][role]['sha256']) for role in ('product_apk','test_apk')]

    def rebuild_apks(self,product_ui=False,duplicate=False):
        target=('L'+UI_CLASS.replace('.','/')+';').encode()
        app=dex(('control',),b'Lsynthetic/Product;',annotated=False)
        if product_ui:app=dex(METHODS,target)
        test=dex(METHODS,target,**self.dex_options)
        for role,data in [('product_apk',apk(app)),('test_apk',apk(test,duplicate))]:
            self.base['apks'][role]=self.put(self.product/('outputs/'+role+'.apk'),data)
            self.base['copies'][role]=self.put(self.root/'package-v1'/(role+'.apk'),data)
        for i in (0,1):
            record=self.base['package']['audit_'+str(i)]
            command=[b._PYTHON,'-I','-S','-B',str(self.product/('scripts/audit_apk.py' if i==0 else 'scripts/audit_instrumentation_apk.py')),self.base['apks']['product_apk']['path']]
            if i:command.append(self.base['apks']['test_apk']['path'])
            self.replace(record['request'],encoded(dict(command=command)));self.replace(record['result'],encoded(dict(returncode=0)))
        self.audit1['app']={k:self.base['apks']['product_apk'][k] for k in ('bytes','sha256')}
        self.audit1['test']={k:self.base['apks']['test_apk'][k] for k in ('bytes','sha256')}
        self.replace(self.base['package']['audit_0']['stdout'],encoded(self.audit0));self.replace(self.base['package']['audit_1']['stdout'],encoded(self.audit1))
        self.proof['artifacts']=self.artifacts();self.base['compiled']=self.put(self.root/'compiled.json',encoded(self.proof))
        if self.base['phases']:self.maps()

    def attest(self,reader=None):
        return b._attest_impl(self.base,reader if reader is not None else b._Reader())


class PureBuildBoundaryTests(unittest.TestCase):
    def test_import_and_bad_cli_do_not_read_publish_or_dispatch(self):
        source=Path(b.__file__).read_bytes();code=compile(source,b.__file__,'exec')
        with patch.object(Path,'read_bytes',side_effect=AssertionError('read')),patch.object(Path,'open',side_effect=AssertionError('open')),\
             patch.object(builtins,'open',side_effect=AssertionError('open')),patch.object(subprocess,'Popen',side_effect=AssertionError('dispatch')),\
             patch.object(socket,'socket',side_effect=AssertionError('socket')):
            ns={'__file__':b.__file__,'__name__':'_b111_import_only'};exec(code,ns)
        with patch.object(b,'_Reader',side_effect=AssertionError('reader')),patch('sys.stderr',new_callable=io.StringIO):
            self.assertEqual(2,b.main(['create','foreign-path']))

    def test_public_roles_and_none_refuse_before_loading_or_reading(self):
        for value in (None,[],{},dict(build={}),dict(build={},product_apk={},test_apk={},model={})):
            with self.subTest(value=repr(value)),patch.object(b,'_load_baseline',side_effect=AssertionError('loader')),\
                 patch.object(b,'_Reader',side_effect=AssertionError('reader')):
                with self.assertRaises(b.BuildRefused):b.verify_frozen_product(value)

    def test_public_runtime_refusals_are_bounded_build_errors_and_safe_cli_output(self):
        for error in (environment.EnvironmentRefused(PRIVATE),RuntimeError(PRIVATE),OSError(PRIVATE)):
            for boundary in ('reader','loader'):
                with self.subTest(error=type(error).__name__,boundary=boundary),patch.object(b,
                        '_Reader' if boundary=='reader' else '_load_baseline',side_effect=error):
                    try:b.create_manifest()
                    except b.BuildRefused as refused:self.assertNotIn(PRIVATE,str(refused))
                    except Exception:self.fail('Public create leaked a non-BuildRefused exception')
                    else:self.fail('Public create qualified failed input inspection')
            with self.subTest(error=type(error).__name__,boundary='cli'):
                output=io.StringIO()
                with patch.object(b,'create_manifest',side_effect=error),patch('sys.stderr',output):
                    try:status=b.main(['create'])
                    except Exception:self.fail('CLI leaked a reader refusal instead of finite status')
                self.assertEqual(1,status);self.assertNotIn(PRIVATE,output.getvalue())

    @unittest.skipUnless(os.name=='nt','fixed production Windows path policy')
    def test_loader_requests_fixed_golden_and_refuses_retargeted_policy(self):
        frozen=json.loads(Path(b.__file__).with_name('record_cancellation_ui_build_baseline.json').read_bytes())
        port=Mock();port.json.return_value=copy.deepcopy(frozen)
        self.assertEqual(frozen,b._load_baseline(port))
        self.assertEqual(dict(path=str(b.BASELINE_PATH),bytes=b.BASELINE_BYTES,sha256=b.BASELINE_SHA256),port.json.call_args.args[0])
        for field in ('root','head','count','owner','unknown'):
            bad=copy.deepcopy(frozen)
            if field=='root':bad['roots']['product']+='-retargeted'
            elif field=='head':bad['product']['head']='0'*40
            elif field=='count':bad['product']['source_count']=True
            elif field=='owner':bad['host_owner']['sha256']='0'*64
            else:bad['authority']=True
            port.json.return_value=bad
            with self.subTest(field=field),self.assertRaises(b.BuildRefused):b._load_baseline(port)


@unittest.skipUnless(os.name=='nt','actual shared reader requires physical D: paths')
class GuardedGraphTests(unittest.TestCase):
    def refuse(self,g):
        with self.assertRaises(REFUSED):g.attest()

    def test_positive_real_reader_graph_is_detached_and_never_publishes_authority(self):
        g=Graph();before={p:p.read_bytes() for p in g.root.rglob('*') if p.is_file()};r=b._Reader()
        with patch.object(r,'final',wraps=r.final) as final:result=g.attest(r)
        self.assertEqual(1,final.call_count);self.assertEqual(before,{p:p.read_bytes() for p in g.root.rglob('*') if p.is_file()})
        self.assertEqual(425,result['facts']['recorded_jvm_cases']);self.assertEqual(50,result['facts']['recorded_jvm_suites'])
        self.assertEqual(5,len(result['instrumentations']));self.assertEqual(METHODS,tuple(row[2] for row in result['instrumentations']))
        for flag in ('android_runtime_executed','model_material','run_authority','feature_acceptance','native_runtime_executed'):
            self.assertIs(result['facts'][flag],False)
        result['product']['head']='0'*40;self.assertNotEqual(result['product']['head'],g.base['product']['head'])

    def test_json_duplicates_nonfinite_overflow_and_extra_fields_fail_closed(self):
        for kind in ('duplicate_top','duplicate_nested','nan','overflow'):
            g=Graph();phase=g.base['phases'][0]
            if kind=='duplicate_nested':
                pin=phase['owner'];value=json.loads(Path(pin['path']).read_bytes())
                payload=encoded(value).replace(b'"owner": {',b'"owner": {"path": '+json.dumps(value['owner']['path']).encode()+b',',1)
            else:
                pin=phase['result'];payload=Path(pin['path']).read_bytes()
                if kind=='duplicate_top':payload=b'{"exit":0,'+payload[1:]
                else:payload=payload.replace(b'"seconds": 1.0',b'"seconds": '+(b'NaN' if kind=='nan' else b'1e999'))
            g.replace(pin,payload)
            with self.subTest(kind=kind):self.refuse(g)
        g=Graph();g.edit(g.base['phases'][0]['result'],lambda x:x.update(authority=True));self.refuse(g)

    def test_source_raw_git_tree_doc_delta_and_map_joins_are_not_normalized(self):
        for kind in ('raw','blob','tree','duplicate','escape','map','unexpected_report'):
            g=Graph()
            if kind=='raw':(g.product/b.UI_SOURCE).write_bytes(g.source_bodies[b.UI_SOURCE].replace(b'\n',b'\r\n'))
            elif kind=='blob':g.base['sources'][0]['git_blob']='0'*40
            elif kind=='tree':g.base['product']['tested_tree']='0'*40
            elif kind=='duplicate':g.base['sources'][-1]['path']=g.base['sources'][0]['path']
            elif kind=='escape':g.base['sources'][0]['path']='../escaped.py'
            elif kind=='map':g.edit(g.base['phases'][1]['after'],lambda x:x.pop())
            else:g.edit(g.base['phases'][0]['before'],lambda x:x.append(dict(path=b.REPORT,size=1,sha256='0'*64)))
            with self.subTest(kind=kind):self.refuse(g)

    def test_concrete_phase_result_owner_and_budget_types_cannot_alias_truth(self):
        variants=[('result','exit',False),('result','source_unchanged',1),('result','source_files',True),
            ('result','instrumentation_executed',0),('result','seconds',True),('result','android_tree_bytes',True),
            ('owner','returncode',False),('owner','cleanup_complete',1),('owner','elapsed_ms',True),('owner','stderr_bytes',False)]
        for record,key,value in variants:
            g=Graph();g.edit(g.base['phases'][0][record],lambda x:x.update({key:value}))
            with self.subTest(record=record,key=key):self.refuse(g)

    def test_bound_worker_command_task_and_empty_capture_are_all_required(self):
        for kind in ('worker','command','task','stderr','management'):
            g=Graph();p=g.base['phases'][0]
            if kind=='worker':g.edit(p['launch'],lambda x:x.update(worker_sha256='0'*64))
            elif kind=='command':g.edit(p['request'],lambda x:x['command'].remove('--offline'))
            elif kind=='task':g.replace(p['stdout'],b'> Task :app:testDebugUnitTest UP-TO-DATE\nBUILD SUCCESSFUL in 1s\n')
            elif kind=='stderr':g.replace(p['worker_stderr'],b'PRIVATE noise')
            else:g.edit(p['launch'],lambda x:x.update(no_device_or_sdk_management=1))
            with self.subTest(kind=kind):self.refuse(g)

    def test_junit_identity_fail_skip_counts_and_package_recredit_refuse(self):
        for kind in ('failure','skipped','duplicate_case','wrong_count','package_xml'):
            g=Graph();pin=g.base['phases'][1]['junit'][1]
            if kind=='package_xml':g.base['phases'][2]['junit']=[g.base['phases'][0]['junit'][0]]
            else:
                root=ET.fromstring(Path(pin['path']).read_bytes());cases=root.findall('testcase')
                if kind=='failure':ET.SubElement(cases[0],'failure',message='synthetic')
                elif kind=='skipped':ET.SubElement(cases[0],'skipped')
                elif kind=='duplicate_case':cases[1].set('name',cases[0].get('name'))
                else:root.set('tests','425')
                g.replace(pin,ET.tostring(root))
            with self.subTest(kind=kind):self.refuse(g)

    def test_apk_copy_audit_pair_permission_and_lint_must_join(self):
        for kind in ('copy','pair','permission','audit_bool','lint'):
            g=Graph()
            if kind=='copy':g.base['copies']['test_apk']=g.put(g.root/'package-v1/other.apk',b'not the selected APK')
            elif kind=='pair':g.edit(g.base['package']['audit_1']['stdout'],lambda x:x['app'].update(sha256='0'*64))
            elif kind=='permission':g.edit(g.base['package']['audit_0']['stdout'],lambda x:x['permissions'].append('android.permission.INTERNET'))
            elif kind=='audit_bool':g.edit(g.base['package']['audit_1']['result'],lambda x:x.update(returncode=False))
            else:g.replace(g.base['package']['lint'],b'<issues><issue id="Unexpected" severity="Error"/></issues>')
            with self.subTest(kind=kind):self.refuse(g)

    def test_selected_dex_requires_real_eligible_definitions_not_references_or_old_proof(self):
        options=[dict(flags=0),dict(flags=0x201),dict(flags=0x401),dict(access=9),dict(access=0x101),
            dict(access=0x401),dict(access=2),dict(result=b'I'),dict(parameters=1),dict(annotated=False),dict(units=0),dict(defined=False)]
        for option in options:
            g=Graph();g.dex_options=option;g.rebuild_apks()
            with self.subTest(option=option):self.refuse(g)
        for kind in ('product','duplicate','proof_bool','source'):
            g=Graph()
            if kind=='product':g.rebuild_apks(product_ui=True)
            elif kind=='duplicate':g.rebuild_apks(duplicate=True)
            elif kind=='proof_bool':g.edit(g.base['compiled'],lambda x:x.update(instrumentation_executed=False))
            else:
                g.source_bodies[b.UI_SOURCE]=g.source_bodies[b.UI_SOURCE].replace(METHODS[0].encode(),b'foreignCase')
                g.sources();g.maps()
            with self.subTest(kind=kind):self.refuse(g)

    def test_real_reader_rejects_links_changed_end_reads_and_resource_budget(self):
        g=Graph();owner=Path(g.base['host_owner']['path']);os.link(owner,g.root/'second-owner-link.py');self.refuse(g)
        g=Graph();r=b._Reader();original=r.final
        def changed():
            Path(g.base['host_owner']['path']).write_bytes(b'changed after guarded read\n');return original()
        with patch.object(r,'final',side_effect=changed),self.assertRaises(REFUSED):g.attest(r)
        g=Graph()
        with patch.object(b.shared,'MAX_TOTAL',1):self.refuse(g)

    def test_public_verify_binds_fixed_roles_and_rejects_forged_manifest_without_foreign_reads(self):
        g=Graph();expected=g.attest();pin=g.put(Path(g.base['roots']['manifest']),encoded(expected));roles=dict(g.base['apks'],build=pin)
        with patch.object(b,'_load_baseline',return_value=copy.deepcopy(g.base)):
            self.assertEqual(expected,b.verify_frozen_product(roles))
        bad=copy.deepcopy(roles);bad['test_apk']['path']=str(g.root.parent/'never-open-foreign.apk');r=b._Reader()
        with patch.object(b,'_Reader',return_value=r),patch.object(b,'_load_baseline',return_value=copy.deepcopy(g.base)),self.assertRaises(b.BuildRefused):
            b.verify_frozen_product(bad)
        self.assertEqual({},r.files)
        forged=copy.deepcopy(expected);forged['facts']['run_authority']=True;pin=g.put(Path(g.base['roots']['manifest']),encoded(forged))
        with patch.object(b,'_load_baseline',return_value=copy.deepcopy(g.base)),self.assertRaises(b.BuildRefused):
            b.verify_frozen_product(dict(g.base['apks'],build=pin))
