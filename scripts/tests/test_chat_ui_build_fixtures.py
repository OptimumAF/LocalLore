"""Original tiny B55-shaped graph. Every successful validator consumes real bytes.

Synthetic DEX/ELF are inert packaging fixtures; no Android tools or Git are run.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from scripts.tests.test_audit_physical_model_apk import dex
from scripts.tests.test_audit_apk import library

FIXTURES = Path('D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-host-fixtures-v1/build')


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()


def pin(path):
    raw = Path(path).read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class BuildGraph:
    """Data-only _SPEC seam; validators and actual source/artifact parsers stay real."""
    def __init__(self, build):
        FIXTURES.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix='graph-', dir=FIXTURES))
        self.root = self.base/'product'
        self.capture = self.base/'capture'
        self.recovery = self.base/'recovery'
        self.spec = copy.deepcopy(build._SPEC)
        self.spec.update(root=str(self.root), head='2'*40, tested_head='1'*40,
                         capture=str(self.capture), recovery=str(self.recovery),
                         manifest=str(self.base/'chat-ui-build-v1.json'))
        self.build = build
        self.source_names = ['README.md']
        self.write(self.root/'README.md', b'Tested synthetic product\n')
        for name in ('scripts/audit_physical_model_apk.py','scripts/audit_apk.py',
                     'benchmarks/android_instrumentation_evidence.py'):
            self.write(self.root/name, (build.ROOT/name).read_bytes())
            self.source_names.append(name)
        groups = {}
        for _, klass, method in build.SELECTORS:
            groups.setdefault(klass, []).append(method)
        for klass, methods in groups.items():
            name = 'apps/android/app/src/androidTest/java/'+klass.replace('.','/')+'.kt'
            self.write(self.root/name, ('package '+klass.rsplit('.',1)[0]+'\nclass '+klass.rsplit('.',1)[1]+' {\n'+
                ''.join('@Test fun '+method+'() {}\n' for method in methods)+'}\n').encode())
            self.source_names.append(name)
        tested = self.map()
        self.spec['tested_source_count'] = len(tested)
        self.spec['tested_archive'] = self.zip_sources(self.capture/'source-fcf92fa3.zip', tested, self.spec['tested_head'])
        self.before = dict(head=self.spec['tested_head'], files=[dict(path=n,**p) for n,p in tested.items()],
                           eolOnlyDifferences=[], canonicalSourceZip=self.spec['tested_archive'])
        self.write(self.root/'README.md', b'Final synthetic docs only\n')
        self.source_names.append(self.spec['docs_changed'][1])
        self.write(self.root/self.spec['docs_changed'][1], b'Synthetic verification document\n')
        current = self.map()
        self.spec['source_count'] = len(current)
        self.spec['canonical_archive'] = self.zip_sources(self.recovery/'source-canonical-v1.zip', current, self.spec['head'])
        self.spec['raw_archive'] = self.zip_sources(self.recovery/'source-raw-v1.zip', current)
        self.final = dict(head=self.spec['head'], testedHead=self.spec['tested_head'], trackedFiles=len(current),
            canonical=self.spec['canonical_archive'], raw=self.spec['raw_archive'], eolOnlyDifferences=[],
            admissionManifest=False, androidRuntimeExecuted=False)
        self.write(self.recovery/'raw-source-pins-v1.json',
                   [dict(relative=n,path=str(self.root/n),**p) for n,p in current.items()])
        self.write(self.recovery/'publication-readback-v1.json', dict(head=self.spec['head'],
            testedHead=self.spec['tested_head'], limitations=dict(androidRuntimeExecuted=False,
                admissionManifest=False, innerRawAuditTools=False, sibling317Included=False, fullSupervisedPipeline=False)))
        self.apks = {
            'product_apk':self.root/'apps/android/app/build/outputs/apk/debug/app-debug.apk',
            'test_apk':self.root/'apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'}
        self.class_definitions = {('L'+k.replace('.','/')+';').encode():
            (1, [(m.encode(), (b'V',0), 1, True) for m in methods]) for k,methods in groups.items()}
        self.apk(self.apks['product_apk'], {b'Lsynthetic/Product;':(1,[])}, product=True)
        self.apk(self.apks['test_apk'], self.class_definitions)
        self.spec['apks'] = {role:pin(path) for role,path in self.apks.items()}
        self.pair = dict(status='passed', package=build.APP, test_package=build.APP+'.test',
            test_permissions=['android.permission.REORDER_TASKS'], certificate_sha256=self.spec['certificate'],
            app={k:self.spec['apks']['product_apk'][k] for k in ('bytes','sha256')},
            test={k:self.spec['apks']['test_apk'][k] for k in ('bytes','sha256')})
        self.product = dict(status='passed', permissions=[build.APP+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'],
            libraries=[dict(entry='lib/'+abi+'/'+name,elf_load_alignment=[16384])
                for abi in ('arm64-v8a','x86_64') for name in ('liblocallore_android.so','libandroidx.graphics.path.so')])
        native = []
        stage_root = self.root/'apps/android/app/build'
        for target,abi,machine in (('x86_64-linux-android','x86_64',62),('aarch64-linux-android','arm64-v8a',183)):
            stripped = bytes(library(machine))
            stages = {'release':stage_root/f'rust-target/{target}/release/liblocallore_android.so',
                'generated':stage_root/f'generated/rustJniLibs/{abi}/liblocallore_android.so',
                'merged':stage_root/f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so',
                'stripped':stage_root/f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so'}
            for stage,path in stages.items():
                self.write(path, stripped if stage=='stripped' else stripped+b'UNSTRIPPED FIXTURE')
            native.append(dict(abi=abi, **{k:pin(p) for k,p in stages.items()},
                apkEntry=f'lib/{abi}/liblocallore_android.so',apkBytes=len(stripped),
                apkSHA256=hashlib.sha256(stripped).hexdigest(),stripStageHasDifferentBytes=True))
        self.reports = []
        for i in range(50):
            klass = 'synthetic.Suite%02d'%i
            count = 9 if i<28 else 8
            root = ET.Element('testsuite',name=klass,tests=str(count),failures='0',errors='0',skipped='0')
            for j in range(count): ET.SubElement(root,'testcase',classname=klass,name='case%02d'%j)
            p = stage_root/'test-results/testDebugUnitTest'/('TEST-'+klass+'.xml')
            self.write(p,ET.tostring(root)); copied=self.capture/'reports-v1'/p.name
            self.write(copied,p.read_bytes());self.reports.append(dict(original=pin(p),copy=pin(copied)))
        lint = ET.Element('issues')
        self.issues = [dict(id='GradleDependency',severity='Warning'),dict(id='AutoboxingStateCreation',severity='Hint')]
        for issue in self.issues: ET.SubElement(lint,'issue',**issue)
        p=stage_root/'reports/lint-results-debug.xml';self.write(p,ET.tostring(lint))
        self.write(self.capture/'reports-v1'/p.name,p.read_bytes())
        for path in self.apks.values():self.write(self.capture/'apks-v1'/path.name,path.read_bytes())
        definitions = [dict(selector=k+'#'+m,public=True,static=False,abstract=False,native=False,
                            voidZeroArgs=True,junitAnnotation=True) for _,k,m in build.SELECTORS]
        self.terminal=dict(androidRuntimeExecuted=False,elapsedSeconds=117.2967263,nativeIncluded=True,exit=0)
        self.evidence=dict(version=1,head=self.spec['tested_head'],trackedSourcesUnchanged=len(tested),
            buildTerminal=self.terminal,buildLog={},productAudit=self.product,pairAudit=self.pair,
            apkCopies=[pin(self.capture/'apks-v1'/p.name) for p in self.apks.values()],
            junit=dict(counts=dict(tests=428,failures=0,errors=0,skipped=0),uniqueCases=428,suites=50,reports=self.reports),
            lint=self.issues,nativeJoins=native,dexReader=pin(self.root/'scripts/audit_physical_model_apk.py'),
            definedUiMethods=definitions,dexReaderProcessCalls=0,dexReaderSocketCalls=0,
            generatedBuildBytes=1,controlsBytesBeforeReceipt=1,androidRuntimeExecuted=False,admissionManifest=False)
        self.write(self.capture/'build-start-v1.json',dict(deviceOperations=False,ordinaryProfile=True,
            offline=True,nativeIncluded=True,head=self.spec['tested_head'],started='2026-11-01T17:02:24Z'))
        self.write(self.capture/'build-terminal-v1.json',self.terminal)
        self.write(self.capture/'source-before-v1.json',self.before)
        self.write(self.capture/'final-source-verification-v1.json',self.final)
        self.write(self.capture/'collect-closed-build-v1.py',b'# inert synthetic capture source\n')
        self.write(self.capture/'tools-identity-v1.json',dict(tools=[],newDependencySelection=False))
        self.publish()

    def write(self,path,value):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(encoded(value) if not isinstance(value,bytes) else value)

    def map(self):
        return {n:{k:pin(self.root/n)[k] for k in ('bytes','sha256')} for n in sorted(self.source_names)}

    def zip_sources(self,path,rows,head=''):
        path.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.comment=head.encode()
            for name in rows:z.writestr(name,(self.root/name).read_bytes())
        return pin(path)

    def apk(self,path,definitions,product=False):
        path.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('AndroidManifest.xml',b'INERT SYNTHETIC MANIFEST')
            z.writestr('classes.dex',dex(definitions))
            if product:
                for abi,machine in (('arm64-v8a',183),('x86_64',62)):
                    for name in ('liblocallore_android.so','libandroidx.graphics.path.so'):
                        entry=zipfile.ZipInfo('lib/'+abi+'/'+name)
                        offset=z.fp.tell()+30+len(entry.filename.encode())
                        padding=(16384-(offset+4)%16384)%16384
                        entry.extra=struct.pack('<HH',0xCAFE,padding)+bytes(padding)
                        z.writestr(entry,library(machine))

    def git(self,args):
        return {('rev-parse','HEAD'):(self.spec['head']+'\n').encode(),
                ('status','--porcelain','--untracked-files=all'):b'',
                ('ls-files','-z'):('\0'.join(sorted(self.source_names))+'\0').encode()}[tuple(args)]

    def publish(self):
        """Reseal coherent fixture metadata after an intentional semantic mutation."""
        python=r'C:\SyntheticInstalledPython\python.exe'
        commands=[[r'C:\Program Files\Java\jdk-21\bin\java.exe','-classpath',
            str(self.root/'apps/android/gradle/wrapper/gradle-wrapper.jar'),'org.gradle.wrapper.GradleWrapperMain',
            ':app:assembleDebug',':app:assembleDebugAndroidTest',':app:testDebugUnitTest',':app:lintDebug',
            '--no-daemon','--console=plain','-Pandroid.builder.sdkDownload=false','--offline'],
            [python,str(self.root/'scripts/audit_apk.py'),str(self.apks['product_apk'])],
            [python,str(self.root/'scripts/audit_instrumentation_apk.py'),str(self.apks['product_apk']),str(self.apks['test_apk'])]]
        log='+ '+repr(commands[0])+'\n'+''.join('> Task :app:'+t+'\n' for t in
            ('buildRustAndroid','compileDebugAndroidTestKotlin','testDebugUnitTest','lintDebug','assembleDebug','assembleDebugAndroidTest'))
        log+='Building LocalLore Rust JNI: x86_64-linux-android -> x86_64\nBuilding LocalLore Rust JNI: aarch64-linux-android -> arm64-v8a\n'
        log+='BUILD SUCCESSFUL in 1m 55s\n81 actionable tasks: 81 executed\n'
        log+='+ '+repr(commands[1])+'\n'+json.dumps(self.product,indent=2)+'\n'
        log+='+ '+repr(commands[2])+'\n'+json.dumps(self.pair)+'\n'
        self.write(self.capture/'build-check-v1.log',log.encode())
        self.evidence['buildLog']=pin(self.capture/'build-check-v1.log')
        self.write(self.capture/'closed-build-evidence-v1.json',self.evidence)
        self.spec['records']={n:pin(self.capture/n) for n in self.spec['records']}
        files=sorted(p for p in self.capture.rglob('*') if p.is_file())
        # 50 XML +lint+two APKs+8 records+archive+two inert controls =64.
        while len(files)<64:
            p=self.capture/('inert-control-%02d.txt'%len(files));self.write(p,b'SYNTHETIC CONTROL');files.append(p)
        assert len(files)==64,len(files)
        copies=[]
        for p in sorted(files):
            copied=self.recovery/'controls-v1'/p.relative_to(self.capture)
            self.write(copied,p.read_bytes());copies.append(dict(original=pin(p),copy=pin(copied)))
        self.write(self.recovery/'preservation-receipt-v1.json',dict(head=self.spec['head'],source=self.final,
            controlsBytes=sum(row['original']['bytes'] for row in copies),controls=copies))
        self.spec['recovery_records']={n:pin(self.recovery/n) for n in self.spec['recovery_records']}

    def artifacts(self):
        return dict(build=pin(Path(self.spec['manifest'])),**copy.deepcopy(self.spec['apks']))
