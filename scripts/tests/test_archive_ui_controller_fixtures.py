"""Full fixed SDK6/closed-reader graph using only synthetic host IO.

The sole byte-authentication exception is an EXACT synthetic adb.exe pin with
the historical fixed ADB hash. Only that pin gets marker bytes/check bypass;
all other source/Python/APK/build/proof/session/claim/JUnit bytes are real and
all corresponding production validators remain active. This is not real ADB,
native ownership, a boot, or Android execution evidence.
"""
import contextlib
import copy
from pathlib import Path
import shlex
from unittest.mock import patch

from benchmarks import archive_ui_build as build
from benchmarks import archive_ui_controller as controller
from benchmarks import adb_held_socket_probe as runtime_probe
from benchmarks import isolated_adb_lease as base
from benchmarks import owned_target_owner as native_owner
from benchmarks import owned_ui_contract as contract
from benchmarks import owned_ui_owner as owner
from benchmarks import android_process_client_v4 as wire
from scripts.tests import test_archive_ui_build_fixtures as builds
from scripts.tests import test_archive_ui_fixtures as f
from scripts.tests import test_android_process_client_v4 as framing
from scripts.tests import test_android_instrumentation_evidence as junit


class ControllerGraph:
    def __init__(self, *, fail=None, boot=None, close=True):
        self.g = builds.BuildGraph()
        self.a = f.admission()
        self.a['root'] = str(self.g.base/'lease')
        Path(self.a['root']).mkdir()
        self.a['server']['root'] = str(Path(self.a['root'])/'server')
        self.a['seconds'] = self.a['server']['seconds'] = 1500
        self.a['artifacts'] = self.g.admission()['artifacts']
        self.a['sources'] = contract.source_bindings()
        self.a['server']['sources'] = base.source_bindings()
        self.python = {}
        for key,name in (('executable','python.exe'),('runtime_dll','python314.dll')):
            path = self.g.base/'python'/name
            self.g.write(path,b'SYNTHETIC own-runtime metadata, never executed')
            self.python[key] = builds.pin(path)
        self.a['python'] = copy.deepcopy(self.python)
        self.a['server']['python'] = copy.deepcopy(self.python)
        for role,relative in (('proposal','guest-proposal.json'),('authorization','guest-authorization.json'),
                              ('emulator','emulator/emulator.exe'),
                              ('qemu','emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe'),
                              ('refuser','deny-adb-client.exe'),('refuser_source','deny_adb_client.c')):
            path = self.g.base/'guest-inputs'/relative
            self.g.write(path,b'SYNTHETIC guest metadata, never executed')
            self.a['guest'][role] = builds.pin(path)
        self.a['guest']['refuser_source'] = wire.environment.binding(
            Path(f.core.__file__).resolve().parents[1]/'benchmarks/native/deny_adb_client.c')
        compat = self.g.base/'compatibility-review.md'; self.g.write(compat,b'SYNTHETIC source compatibility only')
        self.a['compatibility'] = builds.pin(compat)
        tools = []
        self.adb_markers = b'ADB_USB\0ADB_EMU\0ADB_MDNS\0'
        for name in sorted(base.TOOL_NAMES):
            path = self.g.base/'platform-tools'/name
            self.g.write(path,self.adb_markers if name == 'adb.exe' else b'SYNTHETIC tool metadata')
            value = builds.pin(path)
            if name == 'adb.exe': value['sha256'] = base.ADB_SHA256
            tools.append(value)
        self.a['server']['tools'] = tools
        self.adb = copy.deepcopy(next(p for p in tools if Path(p['path']).name == 'adb.exe'))
        self.a['server']['adb'] = copy.deepcopy(self.adb)
        review = self.g.base/'capabilities/source-review.md'; self.g.write(review,b'SYNTHETIC tool source review')
        self.a['server']['source_review'] = builds.pin(review)
        rows = []
        for index,command,raw in ((1,'version',('Android Debug Bridge version 1.0.41\nVersion '+base.SDK_VERSION+'\n').encode()),
                                  (2,'help',b'-L SOCKET\nserver nodaemon\nADB_LOCAL_TRANSPORT_MAX_PORT\nADB_MDNS_AUTO_CONNECT\n')):
            path = review.parent/('command-%02d.stdout.bin'%index); self.g.write(path,raw)
            rows.append(dict(index=index,argv=[self.adb['path'],command],
                owner=dict(status='completed',elapsed_ms=1,returncode=0,cleanup_complete=True,stderr_bytes=0),
                stdout=builds.pin(path)))
        caps = review.parent/'capabilities-v1.json'
        self.g.write(caps,builds.encoded(dict(version=1,passed=True,offline_CLI_calls=2,server_requests=0,
                    device_calls=0,sources_equal=True,rows=rows)))
        self.a['server']['capabilities'] = builds.pin(caps)
        self.ap = self.g.base/'admission-v1.json'; self.g.write(self.ap,builds.encoded(self.a))
        self.admission = builds.pin(self.ap)
        self.d = f.running(self.a); self.d['admission'] = self.admission
        self.rp = Path(self.a['root'])/'running-v1.json'; self.g.write(self.rp,builds.encoded(self.d))
        self.running = builds.pin(self.rp)
        self.caller = copy.deepcopy(self.d['worker'])
        self.clock = 100.0; self.calls = []; self.sockets = []; self.proofs = []
        self.boot = list([b'1\n'] if boot is None else boot)
        self.fail = fail; self.close_result = close; self.close_calls = 0
        self.installed = set(); self.instrumented = []; self.after_queries = 0

    @property
    def output(self):
        return Path(self.a['root'])/'controller-v1'

    def runtime_bindings(self):
        return {key:builds.pin(value['path']) for key,value in self.python.items()}

    def prove(self, live, path, session, context, sock, anchor, after=False):
        value = f.proof(session,after=after)
        value.update(context=copy.deepcopy(context),anchor=copy.deepcopy(anchor),
                     session=wire.environment.binding(Path(session['root'])/'sdk-session-v6.json'))
        queries = path.with_name(path.stem+'-queries-v1.json')
        wire.environment.create_json(queries,f.query_bundle(session))
        value['queries'] = wire.environment.binding(queries)
        wire.environment.create_json(path,value); self.proofs.append((context['index'],context['phase']))
        return wire.environment.binding(path)

    def response(self, argv):
        self.calls.append(list(argv))
        stderr = b''
        if argv == ['getprop','sys.boot_completed']:
            return self.boot.pop(0),stderr
        if argv[:1] == ['getprop']:
            raw = {'ro.build.version.sdk':b'35\n','ro.product.cpu.abi':b'x86_64\n','ro.kernel.qemu':b'1\n'}[argv[1]]
            if self.fail == 'getter_stderr' and argv[1] == 'ro.build.version.sdk': stderr = b'SYNTHETIC unexpected stderr'
            return raw,stderr
        if argv == ['am','get-current-user']: return b'0\n',stderr
        if argv[:4] == ['cmd','package','list','packages']:
            raw = ''.join('package:'+package+' uid:'+str(10001+index)+'\n'
                          for index,package in enumerate((f.APP,f.TEST)) if package in self.installed)
            return raw.encode(),stderr
        if argv[:3] == ['cmd','package','path']:
            package = argv[-1]
            return ('package:/data/app/~~synthetic/'+package+'-opaque==/base.apk\n').encode(),stderr
        if argv[:1] == ['dd']: return b'',b'SYNTHETIC dd copied input bytes\n'
        if argv[:2] == ['pm','install']:
            self.installed.add(f.APP if argv[-1] == controller.STAGED[0] else f.TEST)
            return b'Success\n',stderr
        if argv[:1] == ['sha256sum']:
            role = ('product_apk' if argv[1] == controller.STAGED[0] or
                    (f.APP+'-opaque==') in argv[1] else 'test_apk')
            return (self.a['artifacts'][role]['sha256']+'  '+argv[1]+'\n').encode(),stderr
        if argv[:2] == ['am','instrument']:
            kind = contract.instrumentation_kind(argv)
            self.instrumented.append(kind)
            cls,method = argv[6].split('#')
            if self.fail == 'junit' and kind == f.INSTRUMENTATIONS[2][0]:
                return b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n',stderr
            raw = (junit.bundle(method,1,1,cls=cls,count=1)+
                   junit.bundle(method,1,0,cls=cls,count=1)+junit.ending(1)).encode()
            if self.fail == 'source_after' and kind == f.INSTRUMENTATIONS[-1][0]:
                with Path(self.python['executable']['path']).open('ab') as stream:
                    stream.write(b'changed during cohort')
            return raw,stderr
        raise AssertionError('Unplanned synthetic command: '+repr(argv))

    @contextlib.contextmanager
    def inputs(self):
        original_check = wire.environment.check_binding
        original_read = base._read_bound
        graph = self
        def check(value):
            if value == graph.adb:
                assert Path(value['path']).read_bytes() == graph.adb_markers
                return None
            return original_check(value)
        def read(value, **kwargs):
            if value == graph.adb:
                assert kwargs.get('cap',16*1024*1024) >= len(graph.adb_markers)
                check(value)
                return graph.adb_markers
            return original_read(value,**kwargs)
        def initialize(live, admission, running):
            assert admission == graph.admission and running == graph.running
            live._admission = copy.deepcopy(graph.a); live._descriptor = copy.deepcopy(graph.d)
            live._admission_binding = copy.deepcopy(admission); live._running_binding = copy.deepcopy(running)
            live._caller = copy.deepcopy(graph.caller)
        def guard(live, min_seconds=0):
            # Fake only held native/auth/process observations. Real bound metadata
            # and complete production revalidation run through _inputs before/after.
            original_check(graph.admission); original_check(graph.running)
        def close(live):
            graph.close_calls += 1
            return graph.close_result
        def prove(live, *args, **kwargs):
            return graph.prove(live,*args,**kwargs)
        class Socket(framing.FakeSocket):
            def __init__(self):
                super().__init__(fragment=65536)
                self.pending = bytearray(); self.smart = 0; graph.sockets.append(self)
            def send(self, value):
                raw = bytes(value); self.sent.extend(raw)
                if self.smart < 2:
                    self.pending.extend(raw)
                    while self.smart < 2 and len(self.pending) >= 4:
                        count = int(self.pending[:4],16)
                        if len(self.pending) < count+4: break
                        frame = bytes(self.pending[4:count+4]); del self.pending[:count+4]
                        if self.smart == 0:
                            assert frame == b'host:transport-id:7'
                            self.raw.extend(b'OKAY')
                        else:
                            assert frame.startswith(b'shell,v2,raw:')
                            stdout,stderr = graph.response(shlex.split(frame[len(b'shell,v2,raw:'):].decode()))
                            self.raw.extend(b'OKAY'+framing.packet(1,stdout)+framing.packet(2,stderr)+framing.packet(3,b'\0'))
                        self.smart += 1
                return len(raw)
        with contextlib.ExitStack() as stack:
            stack.enter_context(self.g.inputs(build))
            stack.enter_context(patch.object(wire.environment,'check_binding',side_effect=check))
            stack.enter_context(patch.object(base,'_read_bound',side_effect=read))
            stack.enter_context(patch.object(runtime_probe,'_python_bindings',side_effect=self.runtime_bindings))
            stack.enter_context(patch.object(native_owner._LiveOwnedTarget,'__init__',initialize))
            stack.enter_context(patch.object(native_owner._LiveOwnedTarget,'guard',guard))
            stack.enter_context(patch.object(native_owner._LiveOwnedTarget,'fast_guard',guard))
            stack.enter_context(patch.object(native_owner._LiveOwnedTarget,'prove',prove))
            stack.enter_context(patch.object(native_owner._LiveOwnedTarget,'close',close))
            stack.enter_context(patch.object(wire.time,'monotonic',side_effect=lambda:self.clock))
            stack.enter_context(patch.object(wire.time,'time',return_value=1800000010.0))
            stack.enter_context(patch.object(wire.time,'sleep',side_effect=lambda seconds:setattr(self,'clock',self.clock+seconds)))
            stack.enter_context(patch.object(wire.threading,'Thread',framing.InlineSender))
            stack.enter_context(patch.object(wire.socket,'socket',side_effect=lambda *args:Socket()))
            yield

    def run(self):
        return controller.run(self.admission,self.running)

    def verify(self, caller=None):
        return controller.verify_controller_result(builds.pin(self.output/'controller-result-v1.json'),
                self.admission,self.running,self.caller if caller is None else caller)
