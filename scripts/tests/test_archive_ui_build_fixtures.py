"""Tiny, explicitly synthetic closed-build graph; no compiler/tool execution."""
import contextlib
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

from scripts.tests import test_archive_ui_fixtures as f
from scripts.tests import test_audit_physical_model_apk as dex_fixture

POLICY_METHODS = (
    'initialLoadUnresolvedAndChangedScopesNeverScheduleNavigation',
    'strictAppendFollowsOnlyTheExactPreviouslyReadSnapshotAndStillRemainsUnread',
    'historyReaderKeepsUnreadUntilAnExactCurrentTailReadWithoutAnotherScroll',
    'rewrittenReorderedTruncatedOrReplacedHistoriesAreNotAppends',
    'callerMutationsCannotRewriteFrozenHistoryOrRetroactivelyAuthorizeAppend',
    'latestRequestsRejectStaleScopesHistoriesAndForgedTargetsEvenWithReusedIds',
    'aReadWitnessForAnotherStoryOrOlderHistoryCannotClearCurrentUnread',
    'tailGeometryRequiresTheBottomOrAnActualLaterItemAndDoesNotOverflow',
)
EXECUTED_TASKS = (
    'buildRustAndroid','stripDebugDebugSymbols','compileDebugKotlin','compileDebugJavaWithJavac',
    'compileDebugAndroidTestKotlin','compileDebugAndroidTestJavaWithJavac','compileDebugUnitTestKotlin',
    'testDebugUnitTest','lintAnalyzeDebug','lintAnalyzeDebugAndroidTest','lintAnalyzeDebugUnitTest',
    'lintReportDebug','lintDebug','assembleDebug','assembleDebugAndroidTest',
)

def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()

def pin(path):
    raw = Path(path).read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

class BuildGraph:
    """All byte guards/rosters/DEX parsing are real; only current Git discovery is synthetic."""
    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-ui-build-'))
        self.root = self.base/'source'; self.root.mkdir()
        self.build = self.root/'apps/android/app/build-archive-verification'
        self.public = self.base/'public-run'; self.public.mkdir()
        self.head = 'a'*40
        self.source_paths = []
        self.definitions = {}
        grouped = {}
        for _,cls,method in f.INSTRUMENTATIONS:
            grouped.setdefault(cls,[]).append(method)
        for cls,methods in grouped.items():
            path = self.root/'apps/android/app/src/androidTest/java'/(cls.replace('.','/')+'.kt')
            self.write(path, 'package org.locallore.app\nclass '+cls.rsplit('.',1)[-1]+' {\n'+
                       ''.join('@Test fun '+name+'() {}\n' for name in methods)+'}\n')
            self.source_paths.append(path)
            self.definitions[('L'+cls.replace('.','/')+';').encode()] = (
                17, [(name.encode(),(b'V',0),1,True) for name in methods])
        policy = self.root/'apps/android/app/src/test/java/org/locallore/app/TranscriptFollowTest.kt'
        self.write(policy, 'package org.locallore.app\nclass TranscriptFollowTest {\n'+
                   ''.join('@Test fun '+name+'() {}\n' for name in POLICY_METHODS)+'}\n')
        self.source_paths.append(policy)
        for name in ('scripts/check.py','apps/android/gradle/wrapper/gradle-wrapper.jar'):
            path = self.root/name; self.write(path,b'synthetic non-executable source input\n')
            self.source_paths.append(path)
        self.apks = {'product_apk':self.build/'outputs/apk/debug/app-debug.apk',
                     'test_apk':self.build/'outputs/apk/androidTest/debug/app-debug-androidTest.apk'}
        self.write_apks()
        self.reports = []
        cases = [('org.locallore.app.TranscriptFollowTest',name) for name in POLICY_METHODS]
        self.report('TEST-org.locallore.app.TranscriptFollowTest.xml',cases)
        remaining = 337
        for index in range(40):
            count = 9 if index < 17 else 8
            self.report('TEST-synthetic.Unit%d.xml'%index,
                        [('synthetic.Unit%d'%index,'case%d'%n) for n in range(count)])
            remaining -= count
        assert remaining == 0
        self.lint = self.build/'reports/lint-results-debug.xml'
        self.write(self.lint,b'<issues><issue id="GradleDependency" severity="Warning"/>'
                             b'<issue id="AutoboxingStateCreation" severity="Hint"/></issues>')
        self.tools = []
        for name in ('run-public-v1.py','python.exe','java.exe','jvm.dll','aapt2.exe',
                     'apksigner.jar','signing-compatibility-v1.json'):
            path = self.base/'tools'/name
            self.write(path,('SYNTHETIC tool bytes, never executed: '+name).encode())
            self.tools.append(pin(path))
        self.source_map = self.current_sources()
        self.write(self.public/'sources-before-v1.json',encoded(self.source_map))
        self.write(self.public/'sources-after-v1.json',encoded(self.source_map))
        self.request = dict(version=1,head=self.head,command=[sys.executable,'-I','-S','-B',
            str(self.root/'scripts/check.py'),'android','--archive-verification','--offline'],
            owner_seconds=900,sources=pin(self.public/'sources-before-v1.json'),tools=self.tools,
            signing_property_names=sorted('android.injected.signing.'+x for x in
                ('store.file','store.password','key.alias','key.password')),signing_values_logged=False)
        self.result = dict(version=1,passed=True,sources_equal=True,tools_equal=True,feature_acceptance=False,
            owner=dict(status='child_exited',worker_returncode=0,cleanup_complete=True,
                       output_capture_complete=True,elapsed_ms=1000,stderr_bytes=0,stdout_bytes=0))
        self.pair = dict(status='passed',package=f.APP,test_package=f.TEST,
                         test_permissions=['android.permission.REORDER_TASKS'],certificate_sha256='c'*64)
        self.product = {'status':'passed','permissions':[f.APP+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'],
                        'libraries':[]}
        self.write(self.public/'public-result-v1.json',encoded({'returncode':0,'elapsed_ms':900}))
        self.write(self.public/'owner-stderr-v1.bin',b'')
        self.manifest_path = self.base/'build-manifest-v1.json'
        self.publish()

    def write(self,path,raw):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(raw.encode() if isinstance(raw,str) else raw)

    def write_apks(self):
        for role,path in self.apks.items():
            path.parent.mkdir(parents=True,exist_ok=True)
            definitions = self.definitions if role == 'test_apk' else {b'Lsynthetic/Product;':(17,[])}
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('classes.dex',dex_fixture.dex(definitions))

    def report(self,name,cases):
        suite = ET.Element('testsuite',name=cases[0][0],tests=str(len(cases)),failures='0',errors='0',skipped='0')
        for cls,method in cases:
            ET.SubElement(suite,'testcase',classname=cls,name=method)
        path = self.build/'test-results/testDebugUnitTest'/name
        self.write(path,ET.tostring(suite))
        self.reports.append(path)

    def current_sources(self):
        return {p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.source_paths}

    def commands(self):
        java = next(p['path'] for p in self.tools if Path(p['path']).name == 'java.exe')
        return [[java,'-classpath',str(self.root/'apps/android/gradle/wrapper/gradle-wrapper.jar'),
                 'org.gradle.wrapper.GradleWrapperMain',':app:assembleDebug',':app:assembleDebugAndroidTest',
                 ':app:testDebugUnitTest',':app:lintDebug','--no-daemon','--console=plain',
                 '-Pandroid.builder.sdkDownload=false','-PlocalLoreArchiveVerification=true','--offline'],
                [sys.executable,str(self.root/'scripts/audit_apk.py'),str(self.apks['product_apk']),'--archive-verification'],
                [sys.executable,str(self.root/'scripts/audit_instrumentation_apk.py'),
                 str(self.apks['product_apk']),str(self.apks['test_apk']),'--archive-verification']]

    def publish(self, *, commands=None, tasks=None):
        self.pair.update(app={k:v for k,v in pin(self.apks['product_apk']).items() if k != 'path'},
                         test={k:v for k,v in pin(self.apks['test_apk']).items() if k != 'path'})
        commands = self.commands() if commands is None else commands
        tasks = EXECUTED_TASKS if tasks is None else tasks
        task_log = ''.join('> Task :app:'+name+'\n' for name in tasks)
        stdout = ('+ '+repr(commands[0])+'\n'+task_log+'BUILD SUCCESSFUL\n+ '+repr(commands[1])+'\n'+
                  json.dumps(self.product)+'\n+ '+repr(commands[2])+'\n'+json.dumps(self.pair)+'\n').encode()
        self.write(self.public/'owner-stdout-v1.bin',stdout)
        self.result['owner']['stdout_bytes'] = len(stdout)
        self.write(self.public/'request-v1.json',encoded(self.request))
        self.write(self.public/'result-v1.json',encoded(self.result))
        self.manifest = dict(version=1,scope='archive-ui-build-v1',head=self.head,
            public={role:pin(self.public/name) for role,name in {
                'request':'request-v1.json','result':'result-v1.json','public_result':'public-result-v1.json',
                'stdout':'owner-stdout-v1.bin','stderr':'owner-stderr-v1.bin',
                'sources_before':'sources-before-v1.json','sources_after':'sources-after-v1.json'}.items()},
            apks={role:dict(binding=pin(path),package=f.APP if role == 'product_apk' else f.TEST,
                           certificate_sha256=self.pair['certificate_sha256']) for role,path in self.apks.items()},
            jvm_reports=[pin(p) for p in sorted(self.reports)],lint=pin(self.lint),
            roster=[list(row) for row in f.INSTRUMENTATIONS])
        self.write(self.manifest_path,encoded(self.manifest))

    @contextlib.contextmanager
    def inputs(self, module):
        with contextlib.ExitStack() as stack:
            for name,value in (('ROOT',self.root),('BUILD',self.build),('APK_PATHS',self.apks)):
                stack.enter_context(patch.object(module,name,value))
            stack.enter_context(patch.object(module,'_current_head',side_effect=lambda:self.head))
            stack.enter_context(patch.object(module,'_current_sources',side_effect=self.current_sources))
            yield

    def admission(self):
        value = f.admission()
        value['artifacts'] = {'build':pin(self.manifest_path),
                             **{role:pin(path) for role,path in self.apks.items()}}
        return value
