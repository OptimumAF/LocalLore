"""SDK16 graph using established SDK4 binary framing fixtures and fresh four-method oracles.

Native/process/socket observations and the B88 build-proof boundary are mocks.
The payload files are deliberately NOT APKs; separate build tests and the real
artifact guard validate that boundary. Other source/runtime/capture/claim/JUnit
bindings use actual tiny owned D: files. The exact synthetic adb pin is the sole
fixed-hash exception, as in the existing bounded-wire fixture. No SDK executes.
Successful and failed fixture roots remain for this bounded host cohort.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import copy
from pathlib import Path, PureWindowsPath
import shlex
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import patch

from benchmarks import knowledge_ui_profile_build as build
from benchmarks import knowledge_ui_controller as controller
from benchmarks import adb_held_socket_probe as runtime_probe
from benchmarks import isolated_adb_lease as base
from benchmarks import owned_target_owner as native_owner
from benchmarks import owned_knowledge_ui_contract as contract
from benchmarks import owned_knowledge_ui_owner as owner
from benchmarks import android_process_client_v4 as wire
from scripts.tests import test_archive_ui_build_fixtures as builds
from scripts.tests import test_owned_target_contract as legacy
from benchmarks import owned_target_contract as core
from scripts.tests import test_archive_ui_fixtures as raw_fixture
from scripts.tests import test_android_process_client_v4 as framing
from scripts.tests import test_android_instrumentation_evidence as junit


CREATED_ROOTS = []
FIXTURE_ROOT = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-harness-v1/test-agent-v1/fixtures')
OWN_FOLDERS = ('controller', 'activation')
BUDGET_OBSERVATIONS = []
_SHARED = None

# Literal SDK16 roster; none of the nineteen SDK14 methods grants this authority.
SELECTORS = (
    ('knowledge_labels', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'exactlyFiveKnowledgeFacetsExposeLiteralLabelsSelectionAndFortyEightDpTargetsOnlyInKnowledge'),
    ('knowledge_replaced', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'retainedRealFacetAndCloseActionsCannotRetargetDifferentOrEqualDistinctSuppliedViews'),
    ('knowledge_remount', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'removedAndRemountedSameStateCannotReviveOldFacetOrCloseButFreshActionsStillWork'),
    ('knowledge_text', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'doubledFontKeepsEveryFacetAndUnchangedOriginSourceAndCloseReachableInTheActualDialog'),
)


def raw_manifest(admission):
    """Synthetic B88 DATA shape, not an attestation and never live authority.

    Payload bytes are opaque fixture files; the B88 artifact validator is the
    explicitly replaced boundary. No public compatibility roster/apks exists.
    """
    return dict(version=1, scope='knowledge-ui-build-v1',
        mode='fixed-b88-byte-attestation-v1',
        product={'synthetic_boundary': True},
        artifacts={role: copy.deepcopy(admission['artifacts'][role])
                   for role in ('product_apk', 'test_apk')},
        current_native_bindings={}, evidence={},
        facts={'package_audit': dict(status='passed', package='org.locallore.app',
                    test_package='org.locallore.app.test', certificate_sha256='e' * 64),
               'android_runtime_executed': False, 'model_material': False},
        instrumentations=[list(row) for row in SELECTORS])


def meter(root):
    import os
    total = 0
    if not root.exists():
        return total
    assert not getattr(root.lstat(), 'st_file_attributes', 0) & 0x400
    for here, dirs, files in os.walk(root, followlinks=False,
                                   onerror=lambda error: (_ for _ in ()).throw(error)):
        for name in dirs:
            assert not getattr((Path(here) / name).lstat(), 'st_file_attributes', 0) & 0x400
        for name in files:
            entry = (Path(here) / name).lstat()
            assert not getattr(entry, 'st_file_attributes', 0) & 0x400
            total += entry.st_size
    return total


def ensure_budget(extra=0):
    own = sum(meter(FIXTURE_ROOT / name) for name in OWN_FOLDERS)
    shared = meter(FIXTURE_ROOT)
    BUDGET_OBSERVATIONS.append(dict(own_bytes=own, shared_bytes=shared, reserved_extra=extra))
    if own + extra > 128 * 1024 * 1024 or shared + extra > 256 * 1024 * 1024:
        raise RuntimeError('fixture_budget_refused')
    return own, shared


def admission():
    """Structural SDK16 metadata, for isolated coordinator fault tests only."""
    value = legacy.admission()
    value['protocol'] = contract.PROTOCOL
    value['guest']['root'] = str(contract.GUEST_ROOT)
    value['artifacts'] = {role: value['artifacts'][role]
                          for role in ('build', 'product_apk', 'test_apk')}
    value['sources'] = sorted([
        legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
        for name in contract.SOURCE_NAMES], key=lambda row: row['path'])
    names = {PureWindowsPath(pin['path']).name: pin for pin in value['sources']}
    value['server']['sources'] = [copy.deepcopy(names[PureWindowsPath(pin['path']).name])
                                  for pin in value['server']['sources']]
    return value


def running(value):
    result = legacy.running(value)
    result['protocol'] = contract.PROTOCOL
    return result


class SyntheticFiles:
    def __init__(self):
        ensure_budget(8 * 1024 * 1024)
        parent = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-harness-v1/test-agent-v1/fixtures/controller')
        parent.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix='case-', dir=parent))
        assert self.base.is_absolute() and self.base.drive.upper() == 'D:'
        CREATED_ROOTS.append(self.base)

    def write(self, path, raw):
        path = Path(path)
        assert path.is_relative_to(self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


class ControllerGraph:
    def __init__(self, *, fail=None, boot=None, close=True):
        self.g = SyntheticFiles()
        self.a = legacy.admission()
        self.a['protocol'] = contract.PROTOCOL
        self.a['guest']['root'] = str(contract.GUEST_ROOT)
        self.a['artifacts'] = {role: self.a['artifacts'][role]
                               for role in ('build', 'product_apk', 'test_apk')}
        self.a['root'] = str(self.g.base/'owned-v1')
        Path(self.a['root']).mkdir()
        self.a['server']['root'] = str(Path(self.a['root'])/'server')
        self.a['seconds'] = self.a['server']['seconds'] = 1700
        self.a['artifacts'] = self.artifacts()
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
            Path(core.__file__).resolve().parents[1]/'benchmarks/native/deny_adb_client.c')
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
        self.d = legacy.running(self.a); self.d['protocol'] = contract.PROTOCOL
        self.d['admission'] = self.admission
        self.rp = Path(self.a['root'])/'running-v1.json'; self.g.write(self.rp,builds.encoded(self.d))
        self.running = builds.pin(self.rp)
        self.caller = copy.deepcopy(self.d['worker'])
        self.clock = 100.0; self.calls = []; self.sockets = []; self.proofs = []
        self.boot = list([b'1\n'] if boot is None else boot)
        self.fail = fail; self.close_result = close; self.close_calls = 0
        self.installed = set(); self.instrumented = []; self.after_queries = 0

    def artifacts(self):
        result = {}
        for role in ('build', 'product_apk', 'test_apk'):
            path = self.g.base / ('synthetic-' + role + '.bin')
            self.g.write(path, ('SYNTHETIC controller payload, not an APK: ' + role).encode() + b'\x00\x1a\r\n\xff')
            result[role] = builds.pin(path)
        return result

    def verified_build(self, admission):
        # Only the build-proof boundary is replaced. Actual metadata validation,
        # bindings, one-shot claims and binary closed replay stay active.
        contract.validate_admission(admission)
        if self.fail == 'build':
            raise build.BuildRefused('synthetic_build_refused')
        assert admission['artifacts'] == self.a['artifacts']
        for value in admission['artifacts'].values():
            wire.environment.check_binding(value)
        roster = [list(row) for row in contract.INSTRUMENTATIONS]
        if self.fail == 'roster': roster[-1] = list(contract.INSTRUMENTATIONS[0])
        result = raw_manifest(self.a)
        result['instrumentations'] = roster
        return result

    @property
    def output(self):
        return Path(self.a['root'])/'controller-v1'

    def runtime_bindings(self):
        return {key:builds.pin(value['path']) for key,value in self.python.items()}

    def prove(self, live, path, session, context, sock, anchor, after=False):
        value = raw_fixture.proof(session,after=after)
        value['protocol'] = contract.PROOF_PROTOCOL
        value.update(context=copy.deepcopy(context),anchor=copy.deepcopy(anchor),
                     session=wire.environment.binding(Path(session['root'])/contract.SESSION_FILE))
        queries = path.with_name(path.stem+'-queries-v1.json')
        bundle = raw_fixture.query_bundle(session)
        bundle['protocol'] = contract.PROOF_PROTOCOL
        wire.environment.create_json(queries,bundle)
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
            if self.fail == 'wrong_filter' and argv[-1] == contract.TEST:
                return ('package:' + contract.APP + ' uid:10001\n').encode(), stderr
            raw = ''.join('package:'+package+' uid:'+str(10001+index)+'\n'
                          for index,package in enumerate((contract.APP,contract.TEST))
                          if package in self.installed and argv[-1] in package)
            return raw.encode(),stderr
        if argv[:3] == ['cmd','package','path']:
            package = argv[-1]
            return ('package:/data/app/~~synthetic/'+package+'-opaque==/base.apk\n').encode(),stderr
        if argv[:1] == ['dd']: return b'',b'SYNTHETIC dd copied input bytes\n'
        if argv[:2] == ['pm','install']:
            self.installed.add(contract.APP if argv[-1] == controller.STAGED[0] else contract.TEST)
            return b'Success\n',stderr
        if argv[:1] == ['sha256sum']:
            role = ('product_apk' if argv[1] == controller.STAGED[0] or
                    (contract.APP+'-opaque==') in argv[1] else 'test_apk')
            return (self.a['artifacts'][role]['sha256']+'  '+argv[1]+'\n').encode(),stderr
        if argv[:2] == ['am','instrument']:
            kind = contract.instrumentation_kind(argv)
            self.instrumented.append(kind)
            cls,method = argv[6].split('#')
            if self.fail == 'skip:' + kind:
                return (junit.bundle(method,1,1,cls=cls,count=1) +
                        junit.bundle(method,1,-3,cls=cls,count=1) + junit.ending(1)).encode(),stderr
            if self.fail == 'junit' and kind == contract.INSTRUMENTATIONS[2][0]:
                return b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n',stderr
            raw = (junit.bundle(method,1,1,cls=cls,count=1)+
                   junit.bundle(method,1,0,cls=cls,count=1)+junit.ending(1)).encode()
            if self.fail == 'junit_late' and kind == contract.INSTRUMENTATIONS[0][0]:
                raw += (junit.bundle(method, 1, -2, cls=cls, count=1)).encode()
            if self.fail == 'source_after' and kind == contract.INSTRUMENTATIONS[-1][0]:
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
                            response = b'OKAY'+framing.packet(1,stdout)+framing.packet(2,stderr)
                            if graph.fail != 'missing_exit' or not frame.startswith(b'shell,v2,raw:am instrument '):
                                response += framing.packet(3,b'\0')
                            self.raw.extend(response)
                        self.smart += 1
                return len(raw)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(build,'verify_current',side_effect=self.verified_build))
            stack.enter_context(patch.object(controller,'verify_current',side_effect=self.verified_build))
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
            # A private wire namespace keeps this fake sender out of subprocess/Git.
            stack.enter_context(patch.object(wire,'threading',SimpleNamespace(
                Lock=threading.Lock, Thread=framing.InlineSender)))
            stack.enter_context(patch.object(wire.socket,'socket',side_effect=lambda *args:Socket()))
            yield

    def run(self):
        return controller.run(self.admission,self.running)

    def verify(self, caller=None):
        return controller.verify_controller_result(builds.pin(self.output/'controller-result-v1.json'),
                self.admission,self.running,self.caller if caller is None else caller)


def shared_graph():
    """Emit one successful graph per process; all further checks replay its bytes."""
    global _SHARED
    if _SHARED is None:
        graph = ControllerGraph()
        with graph.inputs():
            result = graph.run()
            assert result['outcome'] == 'completed', result
            assert result['client_count'] == 29
            assert graph.verify() == result
        graph.baseline_result = copy.deepcopy(result)
        graph.baseline_files = {p: p.read_bytes() for p in graph.g.base.rglob('*') if p.is_file()}
        graph.successful_graphs = 1
        ensure_budget()
        _SHARED = graph
    return _SHARED


class Mutation:
    """Retain only changed/missing/new files; restore the same baseline afterward."""
    def __init__(self, graph, name):
        self.graph = graph
        self.root = graph.g.base / 'preserved-deltas' / name

    def __enter__(self):
        ensure_budget(1024 * 1024)
        self.root.mkdir(parents=True)
        return self

    def __exit__(self, kind, error, trace):
        graph = self.graph
        changes = []
        for path, original in graph.baseline_files.items():
            current = path.read_bytes() if path.exists() else None
            if current != original:
                rel = path.relative_to(graph.g.base)
                row = dict(path=str(path), absent=current is None)
                if current is not None:
                    dest = self.root / 'changed' / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with dest.open('xb') as stream: stream.write(current)
                    row['changed'] = builds.pin(dest)
                changes.append(row)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original)
        extras = [p for p in graph.g.base.rglob('*') if p.is_file() and p not in graph.baseline_files
                  and not p.is_relative_to(graph.g.base / 'preserved-deltas')]
        for path in extras:
            dest = self.root / 'extra' / path.relative_to(graph.g.base)
            dest.parent.mkdir(parents=True, exist_ok=True)
            path.rename(dest)
            changes.append(dict(extra=builds.pin(dest)))
        builds_raw = builds.encoded(dict(changes=changes, exception=None if kind is None else kind.__name__))
        with (self.root / 'delta-v1.json').open('xb') as stream: stream.write(builds_raw)
        ensure_budget()
        return False
