"""Original controller flow fixtures; target, native, and SDK IO are simulated."""
import copy
from contextlib import ExitStack
import hashlib
import io
import os
from pathlib import Path
import shlex
import tarfile
import tempfile
import unittest
from unittest.mock import Mock,patch

from benchmarks import original_author_restart_controller as c
from benchmarks import android_process_client_v4 as wire
from scripts.tests import test_owned_restart_contract as fixtures
from scripts.tests.test_owned_restart_contract import ClosedRestartGraph
from scripts.tests.test_android_process_client_v4 import FakeSocket,InlineSender,packet
from scripts.tests.test_original_author_restart_proof import RestartFixture


class ControllerFlow:
    """Real fixed classes/readers; only native and bulk-input IO is replaced.

    Synthetic admitted model/APK bytes are metadata, never real model weights.
    Their exact pins alone are whitelisted at the file-input IO boundary.
    """
    def __init__(self,fail=None):
        self.g=g=ClosedRestartGraph();self.output=g.base/'flow-output';self.calls=[];self.streams=[];self.sockets=[];self.fail=fail
        self.installed=False;self.authored=False;self.stopped=False;self.live_closed=False
        g.root=g.base/'flow-owner';g.a['root']=str(g.root);g.a['server']['root']=str(g.root/'server')
        self.manifest=dict(head='a'*40,apks=[dict(package=c.contract.APP,sha256=g.a['artifacts']['product_apk']['sha256']),
            dict(package=c.contract.TEST,sha256=g.a['artifacts']['test_apk']['sha256'])])
        self.build=g.save(g.base/'build-v1.json',self.manifest);g.a['artifacts']['build']=self.build
        g.admission=g.save(g.base/'flow-admission-v1.json',g.a);g.d=fixtures.running(g.a);g.d['admission']=g.admission
        g.running=g.save(g.root/'running-v1.json',g.d)
        baseline=fixtures.author_fixture.fixture(fixtures.author_fixture.CURRENT)
        self.uid=baseline['author']['process']['uid'];self.pid=baseline['author']['process']['pid']
        self.remote={
            'no_backup/original-author-import-proof-v1':{'import-v1.json':baseline['imported']},
            'no_backup/original-author-proof-v1':{'proof-v1.json':fixtures.author_fixture.f.raw(baseline['author']),**baseline['artifacts']},
            'no_backup/original-author-diagnostic-v1':{'diagnostic-v1.json':fixtures.author_fixture.f.raw(baseline['manifest']),**baseline['files']}}
        restart=RestartFixture();self.remote['no_backup/original-author-restart-proof-v1']={
            'proof-v1.json':fixtures.author_fixture.f.raw(restart.proof),**restart.artifacts}
        self.label=None

    def prove(self,live,path,session,context,sock,anchor,after=False):
        self.label=context['label'];value=fixtures.proof(session,after=after)
        value.update(session=wire.environment.binding(Path(session['root'])/'sdk-session-v5.json'),context=copy.deepcopy(context),anchor=copy.deepcopy(anchor))
        queries=path.with_name(path.stem+'-queries-v1.json');self.g.save(queries,fixtures.query_bundle(session));value['queries']=wire.environment.binding(queries)
        return self.g.save(path,value)

    def response(self,argv):
        self.calls.append(list(argv));label=self.label
        if label=='boot':return b'1\n'
        if label=='user':return b'0\n'
        if label=='property':return {'ro.build.version.sdk':b'35\n','ro.product.cpu.abi':b'x86_64\n','ro.kernel.qemu':b'1\n'}[argv[1]]
        if argv[:4]==['cmd','package','list','packages']:
            return (('package:'+c.contract.APP+' uid:'+str(self.uid)+'\npackage:'+c.contract.TEST+' uid:'+str(self.uid+1)+'\n').encode()if self.installed else b'')
        if argv[:3]==['cmd','package','path']:
            kind='product'if argv[-1]==c.contract.APP else'tests';return ('package:/data/app/~~original-'+kind+'/base.apk\n').encode()
        if argv[:2]==['df','-k']:return b'Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/data 60000000 1 50000000 1% /data\n'
        if argv==['cat','/proc/meminfo']:return b'MemAvailable: 6000000 kB\n'
        if argv[0]=='sha256sum':
            path=argv[1];key=('product_apk'if'product'in path else'test_apk'if'test'in path else'process_probe')
            return (self.g.a['artifacts'][key]['sha256']+'  '+path+'\n').encode()
        if argv[:2]==['pm','install']:self.installed=True;return b'Success\n'
        if argv[0]=='chmod':return b''
        if argv[0]==fixtures.PROBE_PATH:
            value=fixtures.process_packet(mode='boot')if argv[1]=='--boot'else fixtures.process_packet(pid=self.pid,uid=self.uid,state='absent'if self.stopped else'alive')
            if self.fail=='probe'and argv[1]=='--snapshot':value.update(state='refused',error='poll',errno=5)
            return self.g.encode(value)
        if argv[:2]==['am','force-stop']:self.stopped=self.authored;return b''
        if argv[:2]==['am','instrument']:
            kind=c.contract.instrumentation_kind(argv)
            if kind=='author':self.authored=True;self.stopped=False
            if self.fail=='junit'and kind=='author':return b'OK (1 test)\n'
            return fixtures.junit_bytes(kind)
        if argv[:4]==['run-as',c.contract.APP,'--user','0']:
            command=argv[4:]
            if command[0]=='mkdir':return b''
            if command[0]=='ls':
                remote=command[1];names=list(self.remote[remote]);dirs=['workspace-v1','archive-staging']if remote.endswith('/original-author-proof-v1')else['archive-staging']if remote.endswith('/original-author-restart-proof-v1')else[]
                return ('\n'.join(names+dirs)+'\n').encode()
            if command[0]=='sha256sum':
                values=[]
                for path in command[1:]:
                    parent,name=path.rsplit('/',1)
                    digest=hashlib.sha256(self.remote[parent][name]).hexdigest()if parent in self.remote else self.g.a['artifacts']['model'if name=='model.litertlm'else'probe']['sha256']
                    values.append(digest+'  '+path+'\n')
                return ''.join(values).encode()
            if command[:3]==['tar','-cf','-']:
                result=io.BytesIO()
                with tarfile.open(fileobj=result,mode='w')as archive:
                    for path in command[3:]:
                        parent,name=path.rsplit('/',1);raw=self.remote[parent][name];item=tarfile.TarInfo(path);item.uid=self.uid;item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
                return result.getvalue()
        raise AssertionError('unplanned synthetic SDK recipe')

    def execute(self):
        g=self.g;flow=self
        original_check=wire.environment.check_binding
        whitelist=[copy.deepcopy(g.a['artifacts'][key])for key in('model','probe','product_apk','test_apk','process_probe')]
        def check(pin):
            if pin in whitelist:return None
            return original_check(pin)
        def initialize(live,admission,running):
            if admission!=g.admission or running!=g.running:raise AssertionError('owner input changed')
            live._admission=copy.deepcopy(g.a);live._descriptor=copy.deepcopy(g.d);live._admission_binding=copy.deepcopy(admission)
            live._running_binding=copy.deepcopy(running);live._caller=copy.deepcopy(g.d['worker'])
        def close(live):flow.live_closed=True;return True
        def stream(cap,argv,pin,label,**kwargs):
            if pin not in whitelist:raise AssertionError('unadmitted synthetic input')
            c.contract.validate_operation(dict(argv=argv,stdin=pin),g.a)
            flow.streams.append((list(argv),copy.deepcopy(pin)));g.sdk=cap.directory.parent;g.s=cap.session;g.session=cap.session_binding
            g.rows=[wire.environment.read_json(cap.directory/('command-%04d.json'%index))for index in range(1,cap.count+1)]
            g.row_pins=[wire.environment.binding(cap.directory/('command-%04d.json'%index))for index in range(1,cap.count+1)]
            g.add(argv,b'',label,stdin=pin);cap.count+=1;return b''
        class Socket(FakeSocket):
            def __init__(self):super().__init__(fragment=65536);self.smart=0;flow.sockets.append(self)
            def send(self,raw):
                raw=bytes(raw);self.sent.extend(raw)
                if self.smart<2:
                    size=int(raw[:4],16);service=raw[4:];
                    if size!=len(service):raise AssertionError('incomplete Smart frame')
                    if self.smart==0:
                        if service!=('host:transport-id:%d'%g.d['transport_id']).encode():raise AssertionError('wrong target selection')
                        self.raw.extend(b'OKAY')
                    else:
                        if not service.startswith(b'shell,v2,raw:'):raise AssertionError('wrong protocol')
                        argv=shlex.split(service[len(b'shell,v2,raw:'):].decode());stdout=flow.response(argv)
                        self.raw.extend(b'OKAY'+packet(1,stdout)+packet(3,b'\0'))
                    self.smart+=1
                return len(raw)
        with ExitStack()as stack:
            for target,name,value in((c,'_verify_inputs',lambda*a:(copy.deepcopy(g.a),copy.deepcopy(self.manifest))),
                (c.LiveOwnedRestartTarget,'__init__',initialize),(c.LiveOwnedRestartTarget,'guard',lambda*a,**kw:None),
                (c.LiveOwnedRestartTarget,'fast_guard',lambda*a:None),(c.LiveOwnedRestartTarget,'prove',lambda live,*a,**kw:self.prove(live,*a,**kw)),
                (c.LiveOwnedRestartTarget,'close',close),(c.OwnedRestartSdkCapture,'stream',stream),
                (wire.environment,'check_binding',check),(wire.socket,'socket',lambda*a:Socket()),(wire.threading,'Thread',InlineSender),
                (wire.time,'time',lambda:1800000010.0)):
                stack.enter_context(patch.object(target,name,value))
            return c.run(g.admission,g.running,self.build,self.output)


@unittest.skipUnless(os.name=='nt','physical D controller fixtures')
class ControllerBoundaryTests(unittest.TestCase):
    def test_package_getter_stderr_stops_before_any_following_sdk_operation(self):
        g=ClosedRestartGraph();rows=g.rows[3:9];calls=[]
        first=rows[0];first['stderr']=g.save(first['stderr']['path'],b'original getter warning\0\x1a')
        g.save(g.row_pins[3]['path'],first)
        class Capture:
            directory=g.sdk/'clients';count=0
            def shell(self,argv,label,**kwargs):
                row=rows[len(calls)];calls.append(list(argv));self.count=row['index']
                if argv!=row['operation']['argv']:raise AssertionError('unexpected SDK recipe')
                return Path(row['stdout']['path']).read_bytes()
        live=Mock();manifest={'apks':[dict(package=c.contract.APP,sha256=g.a['artifacts']['product_apk']['sha256']),
            dict(package=c.contract.TEST,sha256=g.a['artifacts']['test_apk']['sha256'])]}
        with self.assertRaises((ValueError,c.env.EnvironmentRefused)):
            c._installed(Capture(),live,manifest)
        self.assertEqual(len(calls),1)

    def test_output_under_git_refuses_before_creating_evidence_or_input_dispatch(self):
        base=Path(tempfile.mkdtemp(prefix='locallore-restart-controller-git-',dir='D:/Dev/_Temp'))
        (base/'.git').mkdir();output=base/'output';before=list(base.iterdir())
        with patch.object(c,'_verify_inputs',side_effect=ValueError('unexpected input dispatch'))as inputs:
            with self.assertRaises((ValueError,c.env.EnvironmentRefused)):
                c.run({}, {}, {}, output)
        inputs.assert_not_called();self.assertFalse(output.exists());self.assertEqual(list(base.iterdir()),before)

    def test_complete_fixed_class_controller_flow_uses_real_third_claim_and_deep_readers(self):
        flow=ControllerFlow();result=flow.execute()
        self.assertEqual(result['outcome'],'completed');self.assertEqual(result['phase'],'completed');self.assertIsNone(result['reason'])
        self.assertTrue(result['observer_handles_closed']);self.assertFalse(result['feature_acceptance']);self.assertTrue(flow.live_closed)
        instruments=[c.contract.instrumentation_kind(argv)for argv in flow.calls if argv[:2]==['am','instrument']]
        self.assertEqual(instruments,['import','author','restart']);self.assertEqual(len(flow.streams),5)
        claim=c.env.read_json(flow.g.root/'claims-v1/restart-v1.json');self.assertEqual(claim['prerequisite'],result['prerequisite'])
        self.assertTrue(all(sock.closed for sock in flow.sockets));self.assertEqual(result['client_count'],len(flow.calls)+len(flow.streams))

    def test_bad_probe_or_actual_author_junit_stops_without_restart_or_retry(self):
        for failure in('probe','junit'):
            with self.subTest(failure=failure):
                flow=ControllerFlow(fail=failure);result=flow.execute()
                self.assertEqual(result['outcome'],'refused');self.assertTrue(flow.live_closed);self.assertFalse(result['feature_acceptance'])
                methods=[c.contract.instrumentation_kind(argv)for argv in flow.calls if argv[:2]==['am','instrument']]
                self.assertEqual(methods,['import','author']);self.assertIsNone(result['restart_instrumentation'])
                self.assertFalse((flow.g.root/'claims-v1/restart-v1.json').exists())
                self.assertTrue(all(sock.closed for sock in flow.sockets))


if __name__=='__main__':unittest.main()
