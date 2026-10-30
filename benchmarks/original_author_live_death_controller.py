"""Explicit SDK6 AUTHOR hold/fault/recovery workflow; importing activates nothing.

The pending AUTHOR has its own process, observer and capture session. No capture
object or command index is shared concurrently. The aggregate controller budget
stays 1200 seconds; the held shell command stays 210 seconds.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))

from benchmarks import android_live_death_witness as witness
from benchmarks import android_process_verification_v6 as reader
from benchmarks import owned_live_death_contract as c6
from benchmarks import owned_live_death_owner as owner
from benchmarks import owned_target_owner as held
from benchmarks import isolated_adb_owner as primitives
from benchmarks import receipt_avd_environment as env
from benchmarks import original_author_restart_controller as original
from benchmarks import original_author_model_proof as author
from benchmarks import original_author_diagnostic as diagnostic
from benchmarks import original_author_restart_proof as restart
from benchmarks.android_process_client_v6 import OwnedLiveDeathSdkCapture
from benchmarks import windows_tcp_control as output_control

SECONDS = 1200
AUTHOR_SECONDS = 240
AUTHOR_OWNER_SECONDS = 270
BARRIER = b'LL_OWNED_LIVE_AUTHOR_V1\n'
CHECKPOINT_ROOT = reader.CHECKPOINT_ROOT
_shell = original._shell


def _need(value, reason='checks_failed'):
    env.require(value, reason)


def _bound(pin):
    env.check_binding(pin)
    return env.read_bound_json(pin['path'], pin['sha256'])


def _fault_window(cap, live, pending, checkpoint, expected_boot_id):
    """Finite private plumbing; public run constructs the fixed owned SDK6 types."""
    pending.require_pending()
    process = checkpoint['process']
    argv = [c6.PROCESS_PROBE, '--snapshot-v2', str(process['pid']), str(process['uid'])]
    raw, before_pin = _shell(cap, live, argv, 'live-process-before', seconds=20, limit=4096)
    before = witness.validate_before(checkpoint, raw, expected_boot_id)
    # Completing JUnit or losing ownership before fault is a refusal, not a kill.
    pending.require_pending()
    raw, stop_pin = _shell(cap, live, ['am', 'force-stop', '--user', '0', c6.APP],
                           'live-force-stop', seconds=20, limit=4096)
    _need(raw == b'', 'stop_output')
    raw, after_pin = _shell(cap, live, argv, 'live-process-after', seconds=20, limit=4096)
    after = witness.validate_after(checkpoint, before, raw)
    return dict(before=before, after=after, probe_before=before_pin, force_stop=stop_pin, probe_after=after_pin)


def _worker(request_pin):
    """One fixed pending operation; completed shell framing is not JUnit success."""
    request = _bound(request_pin)
    c6._obj(request, ('version', 'protocol', 'admission', 'running', 'control_session', 'root',
                     'sources', 'python', 'controller', 'seconds', 'owner_seconds'))
    _need(type(request['version']) is int and request['version'] == 1 and
          request['protocol'] == 'owned-live-author-request-v1' and
          type(request['seconds']) is int and request['seconds'] == AUTHOR_SECONDS and
          type(request['owner_seconds']) is int and request['owner_seconds'] == AUTHOR_OWNER_SECONDS)
    root = env.safe_path(request['root'], directory=True)
    _need(root.drive.upper() == 'D:' and root.resolve(strict=True) == root and
          not root.is_relative_to(ROOT) and
          all(not os.path.lexists(p/'.git') for p in (root, *root.parents)), 'output')
    _need(request_pin == env.binding(root/'request-v1.json'))
    until = time.monotonic()+5
    while not os.path.lexists(root/'started-v1.json'):
        _need(time.monotonic() < until, 'started_deadline'); time.sleep(.01)
    started_pin = env.binding(root/'started-v1.json'); started = _bound(started_pin)
    c6._obj(started, ('request', 'worker'))
    _need(started['request'] == request_pin and started['worker'] == env.process_identity(os.getpid()), 'identity')
    a = c6.validate_admission(_bound(request['admission']))
    c6.revalidate_inputs(a)
    _need(request['sources'] == a['sources'] == c6.source_bindings() and request['python'] == a['python'], 'source')
    _need(request['controller'] == env.binding(Path(__file__).resolve()), 'source')
    control = c6.validate_session(_bound(request['control_session']), a)
    _need(control['admission'] == request['admission'] and control['running'] == request['running'] and
          control['caller']['pid'] == os.getppid() and root == Path(control['root'])/'pending-author-v1', 'identity')
    live = cap = None
    outcome, closed, client_pin, session_pin = 'refused', None, None, None
    try:
        live = owner.LiveOwnedLiveDeathTarget(request['admission'], request['running'])
        live.guard(min_seconds=AUTHOR_SECONDS+10)
        (root/'capture-v1').mkdir()
        cap = OwnedLiveDeathSdkCapture(root/'capture-v1/clients', AUTHOR_SECONDS, live)
        session_pin = cap.session_binding
        _need(cap.session['deadline_epoch'] <= control['deadline_epoch'], 'aggregate_budget')
        ready_pending = root/'worker-ready.pending-v1.json'
        env.create_json(ready_pending, dict(version=1, protocol='owned-live-author-ready-v1',
            request=request_pin, session=session_pin, worker=started['worker']))
        ready_pending.rename(root/'worker-ready-v1.json')
        raw = cap.shell(reader.instrument_argv('author_live'), 'instrument-author-live',
                        seconds=210, cap=262144, full_budget=True)
        client_pin = original._record(cap)
        reader.validate_interrupted_instrumentation(raw)
        reader.require_current_clients(str(root/'capture-v1'), cap.count, session_pin, a)
        _need(cap.clean is True and cap.count == 1, 'capture')
        outcome = 'captured'
    except BaseException:
        outcome = 'refused'
    finally:
        if cap is not None:
            cap.close()
        if live is not None:
            try:
                closed = live.close()
            except BaseException:
                closed = None
        if closed is not True:
            outcome = 'refused'
        for pin in (request_pin, started_pin, request['controller']):
            try:
                env.check_binding(pin)
            except (OSError, ValueError, env.EnvironmentRefused):
                outcome = 'refused'
        env.create_json(root/'worker-result-v1.json', dict(version=1, protocol='owned-live-author-worker-v1',
            request=request_pin, session=session_pin, client=client_pin,
            client_count=0 if cap is None else cap.count, outcome=outcome, observer_handles_closed=closed))
    return 0 if outcome == 'captured' else 1


class PendingAuthor:
    """Own one finite Python worker; no SDK capture or index is shared by threads."""
    def __init__(self, root, admission_pin, running_pin, control_session):
        self.root = output_control.validate_output(str(root))
        self.admission_pin, self.running_pin = copy.deepcopy(admission_pin), copy.deepcopy(running_pin)
        self.admission = c6.validate_admission(_bound(admission_pin))
        self.control = c6.validate_session(_bound(control_session), self.admission)
        _need(self.control['admission'] == admission_pin and self.control['running'] == running_pin)
        _need(self.root == Path(self.control['root'])/'pending-author-v1', 'output')
        _need(self.control['deadline_epoch']-time.time() >= 300, 'aggregate_budget')
        self.root.mkdir()
        self.request = dict(version=1, protocol='owned-live-author-request-v1', admission=admission_pin,
            running=running_pin, control_session=control_session, root=str(self.root), sources=self.admission['sources'],
            python=self.admission['python'], controller=env.binding(Path(__file__).resolve()),
            seconds=AUTHOR_SECONDS, owner_seconds=AUTHOR_OWNER_SECONDS)
        env.create_json(self.root/'request-v1.json', self.request)
        self.request_pin = env.binding(self.root/'request-v1.json')
        self.handles = primitives.ProcessHandles(held._ProcessApi())
        self.lock = threading.Lock()
        self.expected = self.started_pin = self.owner_result = self.ready_pin = None
        self.failed = False
        self.thread = None
        self.until = time.monotonic()+AUTHOR_OWNER_SECONDS+12

    def _supervise(self):
        def started(child):
            with self.lock:
                self.handles.guard()
                _, self.expected = self.handles.add(child.pid)
                _need(self.expected['executable'] == self.admission['python']['executable']['path'], 'identity')
                env.check_binding(self.request_pin)
                _need(self.request['sources'] == c6.source_bindings(), 'source')
                pending = self.root/'started.pending-v1.json'
                env.create_json(pending, dict(request=self.request_pin, worker=copy.deepcopy(self.expected)))
                pending.rename(self.root/'started-v1.json')
                self.started_pin = env.binding(self.root/'started-v1.json')
            return True
        try:
            output = self.root/'worker-output-v1'; output.mkdir()
            self.owner_result = env.supervise([sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()), '_author_worker'],
                BARRIER+env.encoded(dict(request=self.request_pin)), output, AUTHOR_OWNER_SECONDS, started,
                stop_proposal_sha256=self.request_pin['sha256'])
            env.create_json(self.root/'owner-result-v1.json', self.owner_result)
        except BaseException:
            self.failed = True

    def start(self):
        _need(self.thread is None, 'spent')
        self.thread = threading.Thread(target=self._supervise, daemon=False)
        self.thread.start()
        until = min(self.until, time.monotonic()+35)
        while not os.path.lexists(self.root/'worker-ready-v1.json'):
            _need(not self.failed and self.thread.is_alive() and time.monotonic() < until, 'pending_start')
            time.sleep(.02)
        ready = env.read_json(self.root/'worker-ready-v1.json')
        c6._obj(ready, ('version', 'protocol', 'request', 'session', 'worker'))
        _need(type(ready['version']) is int and ready['version'] == 1 and
              ready['protocol'] == 'owned-live-author-ready-v1' and ready['request'] == self.request_pin and
              ready['worker'] == self.expected, 'identity')
        self.ready_pin = env.binding(self.root/'worker-ready-v1.json')
        session = c6.validate_session(_bound(ready['session']), self.admission)
        _need(ready['session'] == env.binding(self.root/'capture-v1'/c6.SESSION_FILE) and
              session['caller'] == self.expected and session['admission'] == self.admission_pin and
              session['running'] == self.running_pin and session['seconds'] == AUTHOR_SECONDS and
              Path(session['root']) == self.root/'capture-v1' and
              session['deadline_epoch'] <= self.control['deadline_epoch'], 'pending_session')
        self.require_pending()
        return self

    def require_pending(self):
        _need(self.thread is not None and self.thread.is_alive() and not self.failed and
              time.monotonic() < self.until, 'pending_terminal')
        with self.lock:
            _need(self.expected is not None and self.started_pin is not None, 'identity')
            self.handles.guard()
            env.check_binding(self.started_pin); env.check_binding(self.request_pin)
            _need(self.ready_pin is not None, 'pending_session')
            env.check_binding(self.ready_pin)
        _need(not os.path.lexists(self.root/'worker-result-v1.json') and
              not os.path.lexists(self.root/'capture-v1/clients/command-0001.json'), 'pending_terminal')

    def _join(self):
        if self.thread is not None:
            self.thread.join(max(0, self.until-time.monotonic()))
            _need(not self.thread.is_alive() and not self.failed, 'pending_cleanup')

    def finish(self):
        self._join()
        with self.lock:
            closed = self.handles.close()
        _need(closed is True and self.expected is not None, 'pending_handles')
        result = self.owner_result
        _need(result is not None and result['status'] == 'child_exited' and
              type(result['worker_returncode']) is int and result['worker_returncode'] == 0 and
              result['cleanup_complete'] is True and result['output_capture_complete'] is True and
              result['stdout_bytes'] == result['stderr_bytes'] == 0, 'pending_capture')
        env.create_json(self.root/'after-v1.json', dict(request=self.request_pin, worker=self.expected,
            sources=c6.source_bindings(), python=self.admission['python'], process_handles_closed=True))
        value = dict(version=1, protocol='owned-live-author-result-v1', request=self.request_pin,
            started=env.binding(self.root/'started-v1.json'), worker=env.binding(self.root/'worker-result-v1.json'),
            owner=env.binding(self.root/'owner-result-v1.json'), after=env.binding(self.root/'after-v1.json'))
        env.create_json(self.root/'result-v1.json', value)
        pin = env.binding(self.root/'result-v1.json')
        reader.verify_pending_author(pin, self.admission, self.admission_pin, self.running_pin,
                                     self.request['control_session'])
        return pin

    def cancel(self):
        """Only the owned host worker is stopped; no target fault is dispatched."""
        if self.thread is not None and self.thread.is_alive():
            path = self.root/'worker-output-v1/stop-v1.json'
            # A missing supervisor output is not repaired or adopted.
            if path.parent.is_dir() and not os.path.lexists(path):
                staged = path.with_name('stop.pending-v1.json')
                env.create_json(staged, dict(version=1, proposal_sha256=self.request_pin['sha256'], action='stop'))
                staged.rename(path)
        try:
            self._join()
        finally:
            # A failed terminal verdict must still release retained local
            # handles once the supervisor thread has stopped using them.
            if self.thread is None or not self.thread.is_alive():
                with self.lock:
                    closed = self.handles.close() is True
            else:
                closed = False
        return closed


def _ready(cap, live, pending, output):
    """Poll absence only; a present malformed/terminal checkpoint refuses once."""
    for _ in range(20):
        pending.require_pending()
        raw, _ = _shell(cap, live, ['run-as', c6.APP, '--user', '0', 'ls', 'no_backup'], 'checkpoint-parent', limit=16384)
        parents = raw.decode('ascii').splitlines()
        if 'original-author-live-checkpoint-v1' not in parents:
            time.sleep(1); continue
        raw, _ = original._run_as(cap, live, ['ls', CHECKPOINT_ROOT], 'checkpoint-list', limit=16384)
        names = raw.decode('ascii').splitlines()
        _need(len(names) == len(set(names)) and set(names) <= set(reader.CHECKPOINT_FILES), 'checkpoint_terminal')
        if 'ready-v1.json' not in names:
            time.sleep(1); continue
        raw, pin = _shell(cap, live, ['run-as', c6.APP, '--user', '0', 'cat', CHECKPOINT_ROOT+'/ready-v1.json'],
                          'checkpoint-ready', limit=8192)
        original._write(output/'ready-captured-v1.json', raw)
        return raw, pin
    raise env.EnvironmentRefused('checkpoint_deadline')


def run(admission_binding, running_binding, build_binding, output_root):
    """One explicitly admitted new-profile run; no boot, server or grant creation."""
    begin, started_epoch = time.monotonic(), time.time()
    until = begin+SECONDS
    a = c6.validate_admission(_bound(admission_binding))
    c6.revalidate_inputs(a)
    _need(c6.source_bindings() == a['sources'])
    c6.validate_running(_bound(running_binding), a, admission_binding)
    _need(a['artifacts']['build'] == build_binding)
    manifest = original._verify_build(build_binding, a)
    output = output_control.validate_output(str(output_root)); output.mkdir()
    request = dict(version=1, protocol='original-author-live-death-controller-request-v1',
        admission=admission_binding, running=running_binding, build=build_binding, root=str(output),
        head=manifest['head'], sources=a['sources'], python=a['python'], controller=env.binding(Path(__file__).resolve()),
        seconds=SECONDS, started_epoch=started_epoch, deadline_epoch=started_epoch+SECONDS)
    env.create_json(output/'request-v1.json', request)
    request_pin = env.binding(output/'request-v1.json')
    live = cap = pending = None
    prerequisite = restart_pin = restart_call = boot_final = None
    restart_artifacts = {name: None for name in restart.RECORDS}
    outcome, phase, reason = 'refused', 'admission', 'checks_failed'
    observer_closed = pending_closed = None
    try:
        live = owner.LiveOwnedLiveDeathTarget(admission_binding, running_binding)
        live.guard(min_seconds=1400)
        left = int(until-time.monotonic()); _need(left > 0, 'aggregate_budget')
        cap = OwnedLiveDeathSdkCapture(output/'clients', left, live)
        _need(cap.session['deadline_epoch'] <= request['deadline_epoch'], 'aggregate_budget')
        raw, _ = _shell(cap, live, ['getprop', 'sys.boot_completed'], 'boot')
        _need(raw.strip() == b'1')
        raw, _ = _shell(cap, live, ['am', 'get-current-user'], 'user'); _need(raw.strip() == b'0')
        for key, expected in (('ro.build.version.sdk', b'35'), ('ro.product.cpu.abi', b'x86_64'), ('ro.kernel.qemu', b'1')):
            raw, _ = _shell(cap, live, ['getprop', key], 'property'); _need(raw.strip() == expected)
        for package in (c6.APP, c6.TEST):
            _need(original._package(cap, live, package)[0] is None)
        original._resources(cap, live)
        phase = 'install'
        for key, path in (('product_apk', '/data/local/tmp/locallore-product-v1.apk'),
                          ('test_apk', '/data/local/tmp/locallore-test-v1.apk'), ('process_probe', c6.PROCESS_PROBE)):
            pin = a['artifacts'][key]
            cap.stream(['dd', 'of='+path, 'bs=65536'], pin, 'process-stage' if key == 'process_probe' else 'apk-stage', seconds=120)
            raw, _ = _shell(cap, live, ['sha256sum', path], 'staged-hash')
            _need(raw.decode('ascii').strip() == pin['sha256']+'  '+path)
            if key == 'process_probe':
                raw, _ = _shell(cap, live, ['chmod', '700', path], 'process-mode'); _need(raw == b'')
            else:
                raw, _ = _shell(cap, live, ['pm', 'install', '-r', '-t', '--user', '0', path], 'install', seconds=120)
                _need(raw.strip() == b'Success')
        uids, _ = original._installed(cap, live, manifest)
        uid = uids[c6.APP]
        # The native observer can only run after its bound binary is installed.
        boot, boot_initial = original._probe(cap, live, 'boot')
        original._run_as(cap, live, ['mkdir', '-p', 'no_backup/original-author-source-v1'], 'source-directory')
        phase = 'binary_probe'
        probe_path = 'no_backup/original-author-transfer-probe-v1.bin'
        cap.stream(['run-as', c6.APP, '--user', '0', 'dd', 'of='+probe_path, 'bs=65536'], a['artifacts']['probe'], 'binary-probe')
        _need(original._hashes(cap, live, [probe_path], 'probe-hash')[probe_path] == a['artifacts']['probe']['sha256'])
        phase = 'model_transfer'
        model_path = 'no_backup/original-author-source-v1/model.litertlm'
        cap.stream(['run-as', c6.APP, '--user', '0', 'dd', 'of='+model_path, 'bs=65536'], a['artifacts']['model'], 'model-transfer', seconds=240)
        _need(original._hashes(cap, live, [model_path], 'model-hash')[model_path] == c6.MODEL_SHA256)
        phase = 'import'
        imported_call = original._instrument(cap, live, 0)
        imported_files = original._collect(output/'import-proof', cap, live, uid,
            'no_backup/original-author-import-proof-v1', ('import-v1.json',))
        author.validate_import(imported_files['import-v1.json'])
        raw, _ = _shell(cap, live, ['am', 'force-stop', '--user', '0', c6.APP], 'import-force-stop'); _need(raw == b'')
        _, package_checks = original._installed(cap, live, manifest, uids)
        phase = 'author_live'
        pending = PendingAuthor(output/'pending-author-v1', admission_binding, running_binding, cap.session_binding)
        pending.start()
        raw_ready, ready_client = _ready(cap, live, pending, output)
        pending.require_pending()
        packed, preflight_client = _shell(cap, live,
            ['run-as', c6.APP, '--user', '0', 'tar', '-cf', '-', *reader.preflight_paths()],
            'live-preflight', limit=4*1024*1024)
        preflight_files = reader.unpack_preflight(packed, uid)
        preflight_pins = {'author': {}, 'checkpoint': {}}
        for group, remote, names in (('author', 'no_backup/original-author-proof-v1',
                ('proof-v1.json', *author.RECORDS, *author.TRACES)),
                ('checkpoint', CHECKPOINT_ROOT, reader.CHECKPOINT_FILES)):
            folder = output/'live-preflight'/group; folder.mkdir(parents=True)
            for name in names:
                original._write(folder/name, preflight_files[remote+'/'+name])
                preflight_pins[group][name] = env.binding(folder/name)
        checkpoint = reader.validate_live_baseline(raw_ready,
            preflight_files['no_backup/original-author-proof-v1/proof-v1.json'], imported_files['import-v1.json'],
            {name: preflight_files['no_backup/original-author-proof-v1/'+name] for name in author.RECORDS+author.TRACES},
            {name: preflight_files[CHECKPOINT_ROOT+'/'+name] for name in reader.CHECKPOINT_FILES}, uid)
        phase = 'fault'
        fault = _fault_window(cap, live, pending, checkpoint, boot['boot_id'])
        pending_pin = pending.finish(); pending_closed = True
        phase = 'collect'
        checkpoint_files = original._collect(output/'checkpoint-proof', cap, live, uid, CHECKPOINT_ROOT, reader.CHECKPOINT_FILES)
        names = ('proof-v1.json', *author.RECORDS, *author.TRACES)
        authored_files = original._collect(output/'author-proof', cap, live, uid, 'no_backup/original-author-proof-v1', names)
        diagnostics = original._collect(output/'diagnostic-proof', cap, live, uid, 'no_backup/original-author-diagnostic-v1',
                                       ('diagnostic-v1.json', *diagnostic.FILES))
        artifacts = {name: authored_files[name] for name in author.RECORDS+author.TRACES}
        authored = author.validate_author(authored_files['proof-v1.json'], artifacts, imported_files['import-v1.json'],
                                          expected_prompt_version='initial-world-v1.1')
        diagnostic.validate_diagnostic(diagnostics['diagnostic-v1.json'], {name: diagnostics[name] for name in diagnostic.FILES},
            authored_files['proof-v1.json'], artifacts, imported_files['import-v1.json'], expected_prompt_version='initial-world-v1.1')
        witness.validate_checkpoint(checkpoint_files['ready-v1.json'], author_proof_sha256=hashlib.sha256(authored_files['proof-v1.json']).hexdigest(),
            import_proof_sha256=hashlib.sha256(imported_files['import-v1.json']).hexdigest(), expected_process=authored['process'],
            catalog_sha256=hashlib.sha256(checkpoint_files['catalog-v1.json']).hexdigest(),
            snapshot_sha256=hashlib.sha256(checkpoint_files['snapshot-v1.json']).hexdigest())
        pending_value = _bound(pending_pin); worker = _bound(pending_value['worker'])
        prior = dict(version=1, protocol='original-author-live-death-prerequisite-v1', admission=admission_binding,
            running=running_binding, build=build_binding, control_session=cap.session_binding, author_session=worker['session'],
            pending=pending_pin, ready=env.binding(output/'ready-captured-v1.json'), ready_client=ready_client,
            preflight_client=preflight_client, preflight_artifacts=preflight_pins,
            checkpoint_artifacts={name: env.binding(output/'checkpoint-proof'/name) for name in reader.CHECKPOINT_FILES},
            boot_initial=boot_initial, **{key: fault[key] for key in ('probe_before', 'force_stop', 'probe_after')},
            import_proof=env.binding(output/'import-proof/import-v1.json'), author_proof=env.binding(output/'author-proof/proof-v1.json'),
            author_artifacts={name: env.binding(output/'author-proof'/name) for name in author.RECORDS+author.TRACES},
            import_instrumentation=imported_call, package_checks=package_checks)
        destination = Path(a['root'])/'restart-prerequisite-v1.json'
        pending_path = destination.with_name('restart-prerequisite.pending-v1.json')
        env.create_json(pending_path, prior); pending_path.rename(destination)
        prerequisite = env.binding(destination)
        reader.verify_restart_prerequisite(prerequisite, a, admission_binding, running_binding, live.caller)
        phase = 'restart'
        restart_call = original._instrument(cap, live, 2)
        files = original._collect(output/'restart-proof', cap, live, uid, 'no_backup/original-author-restart-proof-v1',
                                  ('proof-v1.json', *restart.RECORDS))
        restart_pin = env.binding(output/'restart-proof/proof-v1.json')
        restart_artifacts = {name: env.binding(output/'restart-proof'/name) for name in restart.RECORDS}
        restart.validate_restart(files['proof-v1.json'], {name: files[name] for name in restart.RECORDS},
            authored_files['proof-v1.json'], artifacts, imported_files['import-v1.json'], expected_prompt_version='initial-world-v1.1')
        final, boot_final = original._probe(cap, live, 'boot')
        _need(final['boot_id'] == boot['boot_id'] and time.monotonic() < until, 'aggregate_budget')
        phase, reason, outcome = 'completed', None, 'completed'
    except BaseException as error:
        reason = 'deadline' if isinstance(error, TimeoutError) or str(error) in ('deadline', 'expired') else 'checks_failed'
        outcome = 'refused'
    finally:
        if pending is not None and pending_closed is not True:
            try:
                pending_closed = pending.cancel()
            except BaseException:
                pending_closed = None
        if pending is not None and pending_closed is not True:
            outcome, reason = 'refused', 'resource_uncertain'
        if cap is not None:
            try:
                _need(cap.clean is True)
                reader.require_current_clients(str(output), cap.count, cap.session_binding, a)
            except BaseException:
                outcome, reason = 'refused', 'checks_failed'
            cap.close()
        if live is not None:
            try:
                observer_closed = live.close()
            except BaseException:
                observer_closed = None
            if observer_closed is not True:
                outcome, reason = 'refused', 'resource_uncertain'
        try:
            _need(c6.source_bindings() == request['sources'])
            for pin in (request_pin, request['controller'], admission_binding, running_binding, build_binding):
                env.check_binding(pin)
        except (OSError, ValueError, env.EnvironmentRefused):
            outcome, reason = 'refused', 'source_changed'
        result = dict(version=1, protocol='original-author-live-death-controller-v1', request=request_pin,
            session=None if cap is None else cap.session_binding, prerequisite=prerequisite,
            restart_instrumentation=restart_call, boot_final=boot_final, restart_proof=restart_pin,
            restart_artifacts=restart_artifacts, client_count=0 if cap is None else cap.count,
            outcome=outcome, phase=phase, reason=reason, observer_handles_closed=observer_closed,
            pending_handles_closed=pending_closed, feature_acceptance=False,
            elapsed_ms=round(max(0, time.monotonic()-begin)*1000))
        env.create_json(output/'controller-result-v1.json', result)
    return copy.deepcopy(result)


def main():
    _need(sys.argv[1:] == ['_author_worker'], 'explicit_phase')
    _need(sys.stdin.buffer.read(len(BARRIER)) == BARRIER, 'barrier')
    message = env.decode_json(sys.stdin.buffer.read(131073))
    c6._obj(message, ('request',))
    return _worker(message['request'])


if __name__ == '__main__':
    raise SystemExit(main())
