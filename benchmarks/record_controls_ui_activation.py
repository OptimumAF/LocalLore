"""Fixed SDK14 activation glue; importing performs no I/O or target operation.

No preparation, retirement, input, admission or authorization is created here.
Current public owners retain every SDK/storage/process mechanism and deadline.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace

SOURCE_ROOT = Path("D:/Worktrees/locallore-record-controls-ui-core-v1")
HELPER = SOURCE_ROOT / 'benchmarks/record_controls_ui_activation.py'
CONTROLS = Path('D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-harness-v1/run-controls-v1')
RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-01-current-record-controls-ui-run-v1')
CONTROL = RUNTIME / 'control-v1'
INPUT = CONTROLS / 'run-input-v1.json'
BARRIER = b'record-controls-ui-activation-worker-v1\n'
OUTER_SECONDS, OWNER_SECONDS, PARENT_SECONDS = 1800, 1700, 1730
CONTROLLER_SECONDS, CALLER_SECONDS = 1200, 1230
_MODULES = None


class ActivationRefused(ValueError):
    """Fixed reason only; raw private failure material remains in owned captures."""


def _need(condition, reason):
    if not condition:
        raise ActivationRefused(reason)


def _api():
    global _MODULES
    if _MODULES is None:
        sys.path.insert(0, str(SOURCE_ROOT))
        from benchmarks import receipt_avd_environment as env
        from benchmarks import owned_record_controls_ui_contract as contract
        from benchmarks import owned_record_controls_ui_owner as owner
        from benchmarks import owned_target_owner as shared
        from benchmarks import isolated_adb_owner as process
        from benchmarks import record_controls_ui_build as build
        from benchmarks import record_controls_ui_controller as controller
        from benchmarks import android_process_record_controls_ui_verification as verification
        modules = dict(env=env, contract=contract, owner=owner, shared=shared, process=process,
                       build=build, controller=controller, verification=verification)
        for module in modules.values():
            _need(Path(module.__file__).resolve().parent == SOURCE_ROOT / 'benchmarks', 'api_source')
        _MODULES = SimpleNamespace(**modules)
    return _MODULES


def _same(left, right):
    return _api().env.encoded(left) == _api().env.encoded(right)


def _save(path, value):
    api = _api()
    api.env.create_json(path, value)
    return api.env.binding(path)


def _bound(pin, cap=131072):
    api = _api()
    api.contract.binding(pin, max_bytes=cap)
    api.env.check_binding(pin)
    _need(type(pin['bytes']) is int and 0 < pin['bytes'] <= cap, 'binding')
    with Path(pin['path']).open('rb') as stream:
        raw = stream.read(pin['bytes'] + 1)
    _need(len(raw) == pin['bytes'], 'binding')
    result = api.env.decode_json(raw)
    api.env.check_binding(pin)
    return result


def _validate_input(value):
    api = _api()
    _need(type(value) is dict and set(value) == {'version','scope','admission','helper'} and
          type(value['version']) is int and value['version'] == 1 and
          value['scope'] == 'record-controls-ui-run-input-v1', 'input')
    for role in ('admission','helper'):
        api.contract.binding(value[role])
    _need(Path(value['admission']['path']) == RUNTIME / 'admission-v1.json' and
          Path(value['helper']['path']) == HELPER, 'input_path')


def _validate_metadata(value, admission, proposal, authorization):
    api = _api()
    _validate_input(value)
    admitted = api.contract.validate_admission(admission)
    _need(Path(admitted['root']) == RUNTIME / 'owned-v1' and
          admitted['seconds'] == admitted['server']['seconds'] == OWNER_SECONDS and
          set(admitted['artifacts']) == {'build','product_apk','test_apk'}, 'owner_scope')
    _need(type(proposal) is dict and proposal.get('phase') == 'run' and
          proposal.get('paths',{}).get('root') == admitted['guest']['root'] and
          all(type(proposal.get(key)) is int and proposal[key] == expected for key,expected in
              (('memory_mib',8192),('cores',4),('max_seconds',1800))), 'proposal')
    api.env.check_authorization(authorization, 'run', admitted['guest']['proposal']['sha256'])
    return admitted


def _source():
    api = _api()
    api.env.safe_path(SOURCE_ROOT, exists=True, directory=True)
    # The helper is itself part of the admitted source set. Embedding its own
    # future commit would be self-referential; exact source bytes own authority.
    for args in (['rev-parse', 'HEAD'], ['status', '--porcelain', '--untracked-files=all']):
        answer = subprocess.run(['git', '--no-optional-locks', '-C', str(SOURCE_ROOT)] + args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
        _need(answer.returncode == 0 and answer.stderr == b'', 'source')
        raw = answer.stdout.replace(b'\r\n', b'\n')
        if args[0] == 'rev-parse':
            _need(re.fullmatch(rb'[0-9a-f]{40}\n', raw) is not None, 'source')
        else:
            _need(raw == b'', 'source')


def _inputs(binding, *, fresh=False):
    api = _api()
    _need(Path(binding['path']) == INPUT and Path(__file__) == HELPER, 'input_path')
    value = _bound(binding)
    _validate_input(value)
    admission = api.contract.validate_admission(_bound(value['admission']))
    proposal = _bound(admission['guest']['proposal'], 16*1024**2)
    authorization = _bound(admission['guest']['authorization'], 4096)
    admission = _validate_metadata(value, admission, proposal, authorization)
    _need(_same(value['helper'], api.env.binding(HELPER)) and
          any(_same(value['helper'], pin) for pin in admission['sources']), 'helper')
    _source()
    api.build.verify_current(admission)
    actual = api.env.authorize(admission['guest']['proposal']['path'],
                               admission['guest']['authorization']['path'], 'run')
    _need(_same(actual, proposal), 'proposal')
    api.env.verify_prepared(proposal, initial=fresh)
    if fresh:
        _need(not os.path.lexists(admission['root']), 'owner_exists')
    api.env.check_binding(binding)
    return value, admission


def _identity(pid, expected=None):
    api = _api()
    handles = api.process.ProcessHandles(api.shared._ProcessApi())
    try:
        _, value = handles.add(pid, expected)
    finally:
        _need(handles.close() is True, 'identity_close')
    return value


def _started(path, request, child, executable):
    actual = _identity(child.pid)
    _need(actual['executable'] == executable, 'worker_executable')
    pending = path.with_name(path.stem+'.pending.json')
    _save(pending, dict(request=request,worker=actual))
    pending.rename(path)
    _api().env.check_binding(request)
    return actual


def _enter(kind):
    api = _api()
    _need(kind in ('worker','controller'), 'worker_kind')
    raw = sys.stdin.buffer.read(131073)
    _need(len(raw) <= 131072 and raw.startswith(BARRIER), 'barrier')
    envelope = api.env.decode_json(raw[len(BARRIER):])
    _need(type(envelope) is dict and set(envelope) == {'request'} and
          Path(envelope['request']['path']) == CONTROL/(kind+'-request-v1.json'), 'request')
    request = _bound(envelope['request'])
    _need(type(request) is dict and set(request) == {'version','scope','input','parent','running'} and
          type(request['version']) is int and request['version'] == 1 and
          request['scope'] == 'record-controls-ui-'+kind+'-request-v1', 'request')
    path = CONTROL/(kind+'-started-v1.json')
    until = time.monotonic()+5
    while not path.exists():
        _need(time.monotonic() < until, 'started_timeout')
        time.sleep(.02)
    started = _bound(api.env.binding(path))
    _need(type(started) is dict and set(started) == {'request','worker'} and
          _same(started['request'],envelope['request']), 'started')
    actual = _identity(os.getpid(),started['worker'])
    _need(_same(actual,started['worker']) and os.getppid() == request['parent']['pid'] and
          _same(_identity(os.getppid(),request['parent']),request['parent']), 'parent')
    _inputs(request['input'])
    return request, actual


def _known_terminal(value):
    return (type(value) is dict and value.get('status') == 'child_exited' and
            type(value.get('worker_returncode')) is int and value.get('cleanup_complete') is True and
            value.get('output_capture_complete') is True)


def _publish_stop(observer, admission):
    api = _api()
    stop = dict(version=1,protocol=api.contract.PROTOCOL,admission_sha256=admission['sha256'],action='stop')
    api.contract.check_stop(stop,admission['sha256'])
    observer.guard(min_seconds=5)
    pending = RUNTIME/'owned-v1/stop.pending-v1.json'
    _save(pending,stop)
    observer.guard(min_seconds=5)
    pending.rename(pending.with_name('stop-v1.json'))
    # The stop is now spent. Never guard or retry after its atomic publication.


def _controller_worker():
    request,_ = _enter('controller')
    _need(request['running'] is not None, 'running')
    value,_ = _inputs(request['input'])
    result = _api().controller.run(value['admission'],request['running'])
    return 0 if result['outcome'] == 'completed' else 1


class _Runtime:
    def __init__(self, request, identity, value, admission):
        self.request,self.identity,self.value,self.admission = request,identity,value,admission
        self.begin = time.monotonic()
        self.until = self.begin+1750
        self.child = self.capture = self.observer = self.original_owner = None
        self.caller = self.controller_owner = self.controller_result = self.running = None
        self.stop_attempted = self.stop_published = False
        self.result = dict(passed=False,controller_passed=False,owner_qualified=False,
                           storage_closed=False,source_equal=False,cleanup_known=True)

    def dispatch(self):
        api = _api()
        self.capture = api.process.ServerCapture(CONTROL/'owner-console-v1')
        self.child = subprocess.Popen([sys.executable,'-I','-S','-B',str(SOURCE_ROOT/'benchmarks'/api.contract.OWNER_SCRIPT),
            '--admission',self.value['admission']['path'],'--admission-sha256',self.value['admission']['sha256']],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            bufsize=0,creationflags=subprocess.CREATE_NO_WINDOW)
        self.capture.start(self.child)
        self.original_owner = _identity(self.child.pid)
        _need(self.original_owner['executable'] == self.admission['python']['executable']['path'], 'owner_executable')
        _save(CONTROL/'original-owner-started-v1.json',dict(input=self.request['input'],owner=self.original_owner,parent=self.identity))
        path = Path(self.admission['root'])/'running-v1.json'
        until = min(self.until,self.begin+400)
        while not path.exists():
            _need(self.child.poll() is None and time.monotonic()<until, 'owner_not_ready')
            self.capture.guard()
            time.sleep(.1)
        self.capture.guard()
        self.running = api.env.binding(path)
        running = api.contract.validate_running(_bound(self.running),self.admission,self.value['admission'])
        _need(_same(running['owner'],self.original_owner), 'running_owner')
        self.observer = api.owner.LiveOwnedRecordControlsUiTarget(self.value['admission'],self.running)
        self.observer.guard(min_seconds=CALLER_SECONDS)
        request = _save(CONTROL/'controller-request-v1.json',dict(version=1,scope='record-controls-ui-controller-request-v1',
            input=self.request['input'],parent=self.identity,running=self.running))
        capture = CONTROL/'controller-owner-v1';capture.mkdir()
        def started(child):
            self.caller = _started(CONTROL/'controller-started-v1.json',request,child,
                                   self.admission['python']['executable']['path'])
            return True
        self.controller_owner = api.env.supervise([sys.executable,'-I','-S','-B',str(HELPER),'_controller'],
            BARRIER+api.env.encoded(dict(request=request)),capture,CALLER_SECONDS,started)
        _save(CONTROL/'controller-owner-result-v1.json',self.controller_owner)
        _need(_known_terminal(self.controller_owner) and self.caller is not None, 'caller_terminal')
        _need(_same(_bound(api.env.binding(CONTROL/'controller-started-v1.json')),
                    dict(request=request,worker=self.caller)), 'caller_join')
        self.controller_result = api.env.binding(Path(self.admission['root'])/'controller-v1/controller-result-v1.json')
        verified = api.controller.verify_controller_result(self.controller_result,self.value['admission'],self.running,self.caller)
        _need(self.controller_owner['worker_returncode'] == 0 and verified['outcome'] == 'completed', 'cohort_refused')
        self.result['controller_passed'] = True

    def cleanup(self):
        # Each failure is sticky. Later observations cannot repair an unknown wait.
        result = self.result
        result.update(owner_wait_known=False,original_owner_returncode=None,observer_closed=self.observer is None,
            capture_complete=False,capture_evidence_known=False,owner_terminal_published=False)
        if (not self.stop_attempted and self.observer is not None and self.caller is not None and
                _known_terminal(self.controller_owner)):
            self.stop_attempted = True
            try:
                _publish_stop(self.observer,self.value['admission'])
                self.stop_published = True
            except BaseException:
                result.update(stop_failed=True,cleanup_known=False)
        if self.observer is not None:
            try: result['observer_closed'] = self.observer.close() is True
            except BaseException: result['observer_close_error'] = True
            if not result['observer_closed']: result['cleanup_known'] = False
        if self.child is not None:
            try:
                code = self.child.poll()
                while code is None and time.monotonic()<self.until:
                    time.sleep(.1);code = self.child.poll()
                if type(code) is int:
                    result.update(owner_wait_known=True,original_owner_returncode=code)
                else: result['cleanup_known'] = False
            except BaseException: result.update(owner_wait_error=True,cleanup_known=False)
        else: result['cleanup_known'] = False
        if self.capture is not None:
            try: result['capture_complete'] = self.capture.close() is True
            except BaseException: result['capture_close_error'] = True
        if not result['capture_complete']: result['cleanup_known'] = False
        terminal = dict(owner=self.original_owner,returncode=result['original_owner_returncode'],
            wait_known=result['owner_wait_known'],capture_complete=result['capture_complete'],stdout=None,stderr=None)
        if result['capture_complete']:
            try:
                terminal['stdout'] = _api().env.binding(CONTROL/'owner-console-v1/owner-stdout-v1.bin')
                terminal['stderr'] = _api().env.binding(CONTROL/'owner-console-v1/owner-stderr-v1.bin')
                result['capture_evidence_known'] = True
            except BaseException: result.update(capture_evidence_error=True,cleanup_known=False)
        terminal.update(cleanup_known=result['cleanup_known'],capture_evidence_known=result['capture_evidence_known'])
        try:
            _save(CONTROL/'original-owner-terminal-v1.json',terminal)
            result['owner_terminal_published'] = True
        except BaseException: result.update(owner_terminal_publication_error=True,cleanup_known=False)

    def qualify(self):
        api = _api();r = self.result;a = self.admission
        _need(r['cleanup_known'] and r['owner_wait_known'] and r['original_owner_returncode'] == 0 and
              r['capture_complete'] and r['capture_evidence_known'] and r['owner_terminal_published'], 'owner_terminal')
        public = _bound(api.env.binding(Path(a['root'])/'result-v1.json'))
        _need(public['qualified_target'] is True and public['reason'] == 'stop_requested' and
              _same(public['admission'],self.value['admission']), 'owner_qualification')
        _need(_same(_bound(public['request'])['owner'],self.original_owner), 'owner_join')
        record = api.verification.verify_owned_target_result(public['worker_result'],a,self.value['admission'],
            public['request'],_bound(public['started'])['worker'])
        _need(record['reason'] == 'stop_requested' and set(record['cleanup']) == set(api.contract.CLEANUP_KEYS) and
              all(flag is True for flag in record['cleanup'].values()), 'cleanup')
        closure_path = Path(a['guest']['root'])/'guest-storage-closure-v1.json'
        closure_pin = api.env.binding(closure_path);closure = _bound(closure_pin)
        _need(closure['closure_verified'] is True and closure['cleanup_complete'] is True and
              all(_same(closure[k],v) for k,v in [('admission',self.value['admission']),('worker_result',public['worker_result']),
                  ('owner_result',public['owner']),('after',public['after'])]) and
              closure['proposal_sha256'] == a['guest']['proposal']['sha256'], 'closure')
        ledger_pin = api.env.binding(api.env.guest_storage.DEFAULT_REGISTRY/'ledger-v1.json')
        ledger = _bound(ledger_pin,16*1024**2)
        entries = [entry for entry in ledger['entries'] if Path(entry['root']) == Path(a['guest']['root'])]
        _need(len(entries)==1 and entries[0]['state']=='closed' and _same(entries[0]['closure'],closure_pin) and
              entries[0]['proposal_sha256']==a['guest']['proposal']['sha256'], 'storage_closed')
        _inputs(self.request['input'])
        # Final file-only replay binds the SAME initial proof after owner cleanup.
        _need(self.controller_result is not None and self.caller is not None, 'controller_evidence')
        verified = api.controller.verify_controller_result(self.controller_result,
            self.value['admission'], self.running, self.caller)
        _need(verified['outcome'] == 'completed', 'controller_replay')
        api.env.check_binding(self.controller_result)
        api.env.check_binding(ledger_pin)
        r.update(owner_qualified=True,storage_closed=True,source_equal=True,ledger=ledger_pin)
        r['passed'] = (r['controller_passed'] is True and self.stop_published and r['observer_closed'] is True)

    def publish(self):
        r = self.result
        request_pin = None
        try: request_pin = _api().env.binding(CONTROL/'worker-request-v1.json')
        except BaseException: r.update(request_evidence_error=True,cleanup_known=False,passed=False)
        try: elapsed = round((time.monotonic()-self.begin)*1000)
        except BaseException:
            elapsed=None;r.update(clock_error=True,cleanup_known=False,passed=False)
        r.update(version=1,scope='record-controls-ui-activation-runtime-v1',input=self.request['input'],request=request_pin,
            worker=self.identity,controller_result=self.controller_result,stop_attempted=self.stop_attempted,
            stop_published=self.stop_published,elapsed_ms=elapsed,feature_acceptance=False)
        try: _save(CONTROL/'runtime-result-v1.json',r)
        except BaseException:
            r.update(runtime_publication_error=True,cleanup_known=False,passed=False)
            try:
                sys.stderr.write('{"scope":"record-controls-ui-activation-runtime-v1","passed":false,"publication_error":true}\n')
                sys.stderr.flush()
            except BaseException: pass
            return 1
        return 0 if r['passed'] else 1

    def run(self):
        try: self.dispatch()
        except BaseException as error: self.result['dispatch_error'] = type(error).__name__
        finally: self.cleanup()
        try: self.qualify()
        except BaseException as error: self.result['qualification_error'] = type(error).__name__
        return self.publish()


def _runtime_worker():
    request,identity = _enter('worker')
    _need(request['running'] is None, 'request')
    value,admission = _inputs(request['input'],fresh=True)
    return _Runtime(request,identity,value,admission).run()


def execute(input_binding):
    api = _api()
    _need(Path.cwd()==SOURCE_ROOT and all(Path(os.environ.get(key,'')) == Path('D:/Dev/_Temp')
          for key in ('TEMP','TMP','TMPDIR')), 'environment')
    value,admission = _inputs(input_binding,fresh=True)
    api.env.safe_path(RUNTIME,exists=True,directory=True)
    _need(not os.path.lexists(CONTROL), 'control_exists')
    CONTROL.mkdir()
    parent = _identity(os.getpid())
    _need(parent['executable']==admission['python']['executable']['path']==sys.executable, 'parent')
    request = _save(CONTROL/'worker-request-v1.json',dict(version=1,scope='record-controls-ui-worker-request-v1',
        input=input_binding,parent=parent,running=None))
    capture = CONTROL/'outer-owner-v1';capture.mkdir()
    worker = None
    def started(child):
        nonlocal worker
        worker = _started(CONTROL/'worker-started-v1.json',request,child,admission['python']['executable']['path'])
        return True
    result = dict(version=1,scope='record-controls-ui-activation-final-v1',passed=False,input=input_binding,
                  worker=None,owner=None,feature_acceptance=False)
    try:
        returned = api.env.supervise([sys.executable,'-I','-S','-B',str(HELPER),'_worker'],
            BARRIER+api.env.encoded(dict(request=request)),capture,OUTER_SECONDS,started)
        result['owner'] = _save(CONTROL/'outer-owner-result-v1.json',returned)
        _need(_known_terminal(returned) and returned['worker_returncode']==0 and worker is not None, 'outer_terminal')
        _need(_same(_bound(api.env.binding(CONTROL/'worker-started-v1.json')),dict(request=request,worker=worker)), 'worker_join')
        pin = api.env.binding(CONTROL/'runtime-result-v1.json');record = _bound(pin)
        _need(record['passed'] is True and _same(record['input'],input_binding) and
              _same(record['request'],request) and _same(record['worker'],worker), 'runtime')
        _inputs(input_binding)
        result.update(passed=True,runtime=pin)
    except BaseException as error: result['reason'] = type(error).__name__
    result['worker'] = worker
    try: _save(CONTROL/'final-result-v1.json',result)
    except BaseException:
        result.update(passed=False,publication_error=True)
        try: sys.stderr.write('{"scope":"record-controls-ui-activation-final-v1","passed":false,"publication_error":true}\n')
        except BaseException: pass
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args == ['_worker']: return _runtime_worker()
    if args == ['_controller']: return _controller_worker()
    if len(args)!=2 or args[0]!='--input-sha256' or re.fullmatch('[0-9a-f]{64}',args[1]) is None: return 1
    try:
        binding = _api().env.binding(INPUT)
        _need(binding['sha256']==args[1], 'input_hash')
        return 0 if execute(binding)['passed'] else 1
    except (ActivationRefused,OSError,ValueError,KeyError,TypeError): return 1


if __name__ == '__main__':
    raise SystemExit(main())
