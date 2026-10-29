"""Fixed restart-profile closed replay and native observation consistency.

No process, socket, device, model or credential operation is performed here.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import re
from pathlib import Path, PureWindowsPath

from benchmarks import android_process_verification_v4 as shared
from benchmarks import original_author_model_proof as author
from benchmarks import owned_restart_contract as c
from benchmarks import original_author_restart_proof as restart
from benchmarks import receipt_avd_environment as env
from benchmarks.android_instrumentation_evidence import validate_instrumentation

PROBE_PROTOCOL = 'android-author-process-probe-v1'
PROBE_KEYS = frozenset((
    'version', 'protocol', 'mode', 'boot_id', 'pid', 'expected_uid',
    'observed_uid', 'start_ticks', 'state', 'pidfd_opened', 'poll_revents',
    'pidfd_closed', 'proc_opened', 'proc_closed', 'error', 'errno',
))
PROBE_ERRORS = frozenset((
    'pidfd_unsupported', 'pidfd_permission', 'proc_permission', 'proc_race',
    'uid_mismatch', 'io', 'close', 'malformed',
))


def validate_probe_packet(raw):
    """Retain a complete refused packet as data; never promote it to absence."""
    try:
        value = author._json(raw, 4096)
        c._obj(value, PROBE_KEYS)
        c._int(value['version'], 1, 1)
        c._need(value['protocol'] == PROBE_PROTOCOL, 'probe')
        c._need(value['mode'] in ('boot', 'snapshot') and
                value['state'] in ('boot', 'alive', 'exited', 'absent', 'refused'), 'probe')
        if value['boot_id'] is not None:
            c._need(type(value['boot_id']) is str and re.fullmatch(
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', value['boot_id']) is not None, 'probe')
        if value['mode'] == 'boot':
            c._need(all(value[k] is None for k in ('pid', 'expected_uid', 'observed_uid', 'start_ticks')), 'probe')
        else:
            c._int(value['pid'], 1, 2**31-1, 'probe')
            c._int(value['expected_uid'], 10000, 2**31-1, 'probe')
        if value['observed_uid'] is not None:
            c._int(value['observed_uid'], 0, 2**31-1, 'probe')
        if value['start_ticks'] is not None:
            c._int(value['start_ticks'], 1, 2**63-1, 'probe')
        c._int(value['errno'], 0, 4095, 'probe')
        for opened, closed in (('pidfd_opened', 'pidfd_closed'), ('proc_opened', 'proc_closed')):
            c._need(type(value[opened]) is bool and
                    (value[closed] is None or type(value[closed]) is bool), 'probe')
            c._need(value[opened] or value[closed] is None, 'probe')
        if value['poll_revents'] is not None:
            c._int(value['poll_revents'], 0, 65535, 'probe')
        c._need(value['pidfd_opened'] or value['poll_revents'] is None, 'probe')
        if value['state'] == 'refused':
            c._need(value['error'] in PROBE_ERRORS, 'probe')
        else:
            c._need(value['boot_id'] is not None and value['error'] is None, 'probe')
            if value['state'] == 'boot':
                c._need(value['mode'] == 'boot' and value['errno'] == 0 and
                        value['pidfd_opened'] is value['proc_opened'] is False and
                        value['poll_revents'] is value['pidfd_closed'] is value['proc_closed'] is None, 'probe')
            elif value['state'] == 'absent':
                c._need(value['mode'] == 'snapshot' and value['errno'] == 3 and
                        value['observed_uid'] is value['start_ticks'] is None and
                        value['pidfd_opened'] is False and value['poll_revents'] is value['pidfd_closed'] is None and
                        (value['proc_opened'] is False and value['proc_closed'] is None or
                         value['proc_opened'] is True and value['proc_closed'] is True), 'probe')
            else:
                c._need(value['mode'] == 'snapshot' and value['errno'] == 0 and
                        value['observed_uid'] == value['expected_uid'] and value['start_ticks'] is not None and
                        value['pidfd_opened'] is value['pidfd_closed'] is value['proc_opened'] is value['proc_closed'] is True,
                        'probe')
                c._need(value['poll_revents'] == 0 if value['state'] == 'alive' else
                        value['poll_revents'] in (1, 16, 17), 'probe')
        return copy.deepcopy(value)
    except c.TargetRefused:
        raise
    except (author.ProofRefused, ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        raise c.TargetRefused('probe') from None


def parse_probe(raw, mode, pid=None, uid=None):
    value = validate_probe_packet(raw)
    c._need(value['state'] != 'refused' and value['mode'] == mode, 'probe')
    c._need((mode == 'boot' and pid is uid is None) or
            (mode == 'snapshot' and type(pid) is type(uid) is int and
             value['pid'] == pid and value['expected_uid'] == uid), 'probe')
    return value


PREREQUISITE_KEYS = frozenset((
    'version', 'protocol', 'admission', 'running', 'session', 'caller',
    'import_proof', 'author_proof', 'author_artifacts', 'import_instrumentation',
    'author_instrumentation', 'boot_initial', 'probe_before', 'force_stop',
    'probe_after', 'package_checks',
))
REQUEST_KEYS = frozenset((
    'version', 'protocol', 'admission', 'running', 'build', 'root', 'head',
    'sources', 'python', 'controller', 'seconds',
))
RESULT_KEYS = frozenset((
    'version', 'protocol', 'request', 'session', 'prerequisite',
    'restart_instrumentation', 'boot_final', 'restart_proof',
    'restart_artifacts', 'client_count', 'outcome', 'phase', 'reason',
    'observer_handles_closed', 'feature_acceptance', 'elapsed_ms',
))
HELPER = '/data/local/tmp/locallore-author-process-probe-v1'
_IO = shared._Verifier(c)


def _same(left, right, reason='binding'):
    c._need(c._same(left, right), reason)


def _raw(pin, cap=2*1024*1024):
    return _IO._raw(pin, cap)


def _json(pin):
    return _IO._json(pin)


def _at(pin, path):
    return _IO._at(pin, path)


def _client(pin, session, admission, argv):
    # Check the witness's recipe before invoking the complete generic replay.
    # A restart instrument can never recursively witness its own prerequisite.
    peek = c.validate_client_record(_json(pin), session)
    _same(peek['operation'], dict(argv=argv, stdin=None), 'command')
    value = _IO.verify_client_record(pin, session, admission)
    c._need(value['returncode'] == 0, 'capability')
    return value


def _stdout(record):
    return _raw(record['stdout'], 2*1024*1024)


def _empty_stderr(record):
    c._need(_raw(record['stderr']) == b'', 'capability')


def _instrument(pin, session, admission, kind):
    selected = next((row for row in c.INSTRUMENTATIONS if row[0] == kind), None)
    c._need(selected is not None, 'command')
    _, cl, method = selected
    argv = ['am', 'instrument', '-w', '-r', '-e', 'class', cl+'#'+method,
            c.TEST+'/androidx.test.runner.AndroidJUnitRunner']
    value = _client(pin, session, admission, argv)
    _empty_stderr(value)
    validate_instrumentation(_stdout(value), cl, [method])
    return value


def _uid(raw, selected):
    try:
        lines = raw.decode('ascii').splitlines()
    except UnicodeError:
        raise c.TargetRefused('identity') from None
    c._need(1 <= len(lines) <= 2, 'identity')
    result = {}
    for line in lines:
        match = re.fullmatch(r'package:([^\s]+) uid:([1-9][0-9]*)', line)
        c._need(match is not None and match[1] in (c.APP, c.TEST) and match[1] not in result, 'identity')
        result[match[1]] = c._int(int(match[2]), 10000, 2**31-1, 'identity')
    c._need(selected in result, 'identity')
    return result[selected]


def _packages(checks, session, admission):
    c._obj(checks, ('product', 'tests'), 'binding')
    indices = []
    uids = {}
    for key, package, artifact in (('product', c.APP, 'product_apk'), ('tests', c.TEST, 'test_apk')):
        row = c._obj(checks[key], ('uid', 'path', 'sha256'), 'binding')
        uid = _client(row['uid'], session, admission,
                      ['cmd', 'package', 'list', 'packages', '-U', '--user', '0', package])
        path = _client(row['path'], session, admission,
                       ['cmd', 'package', 'path', '--user', '0', package])
        for item in (uid, path):
            _empty_stderr(item)
        uids[package] = _uid(_stdout(uid), package)
        raw_path = _stdout(path).decode('ascii').strip()
        c._need(re.fullmatch(r'package:/data/app/[A-Za-z0-9_~=/.-]+/base\.apk', raw_path) is not None, 'identity')
        location = raw_path[len('package:'):]
        digest = _client(row['sha256'], session, admission, ['sha256sum', location])
        _empty_stderr(digest)
        expected = admission['artifacts'][artifact]['sha256']+'  '+location+'\n'
        c._need(_stdout(digest) == expected.encode('ascii'), 'binding')
        current = [uid['index'], path['index'], digest['index']]
        c._need(current == sorted(set(current)) and (not indices or indices[-1] < current[0]), 'clock')
        indices += current
    c._need(uids[c.APP] != uids[c.TEST], 'identity')
    return uids, indices


def verify_restart_prerequisite(pin, admission, admission_binding, running_binding, caller):
    """Replay bound witness bytes; never query a process or select another target."""
    a = c.validate_admission(admission)
    _same(c.validate_admission(_json(admission_binding)), a)
    root = Path(a['root'])
    value = _at(pin, root/'restart-prerequisite-v1.json')
    c._obj(value, PREREQUISITE_KEYS)
    c._int(value['version'], 1, 1)
    c._need(value['protocol'] == 'original-author-restart-prerequisite-v1', 'binding')
    for key, expected in (('admission', admission_binding), ('running', running_binding), ('caller', caller)):
        _same(value[key], expected)
    session = c.validate_session(_json(value['session']), a)
    _same(session['admission'], admission_binding)
    _same(session['running'], running_binding)
    _same(session['caller'], caller)
    _same(c.validate_running(_json(running_binding), a, admission_binding), session['descriptor'])
    imported = _raw(value['import_proof'], author.MAX_ARTIFACT)
    authored = _raw(value['author_proof'], author.MAX_ARTIFACT)
    c._obj(value['author_artifacts'], author.RECORDS+author.TRACES, 'binding')
    artifacts = {name: _raw(value['author_artifacts'][name], author.MAX_ARTIFACT)
                 for name in author.RECORDS+author.TRACES}
    baseline = author.validate_author(authored, artifacts, imported, expected_prompt_version='initial-world-v1.1')
    import_record = _instrument(value['import_instrumentation'], session, a, 'import')
    author_record = _instrument(value['author_instrumentation'], session, a, 'author')
    initial = _client(value['boot_initial'], session, a, [HELPER, '--boot'])
    _empty_stderr(initial)
    boot = parse_probe(_stdout(initial), 'boot')['boot_id']
    uids, package_indices = _packages(value['package_checks'], session, a)
    identity = baseline['process']
    c._need(uids[c.APP] == identity['uid'], 'identity')
    argv = [HELPER, '--snapshot', str(identity['pid']), str(identity['uid'])]
    before = _client(value['probe_before'], session, a, argv)
    stop = _client(value['force_stop'], session, a, ['am', 'force-stop', '--user', '0', c.APP])
    after = _client(value['probe_after'], session, a, argv)
    for item in (before, stop, after):
        _empty_stderr(item)
    c._need(_stdout(stop) == b'', 'capability')
    first = parse_probe(_stdout(before), 'snapshot', identity['pid'], identity['uid'])
    last = parse_probe(_stdout(after), 'snapshot', identity['pid'], identity['uid'])
    c._need(first['boot_id'] == last['boot_id'] == boot and last['state'] in ('absent', 'exited'), 'identity')
    if last['state'] == 'exited' and first['start_ticks'] is not None:
        c._need(last['start_ticks'] == first['start_ticks'], 'identity')
    order = [initial['index'], import_record['index'], author_record['index'], *package_indices,
             before['index'], stop['index'], after['index']]
    c._need(order == sorted(set(order)), 'clock')
    return copy.deepcopy(value)


class _RestartVerifier(shared._Verifier):
    def __init__(self):
        super().__init__(c)

    def verify_client_record(self, binding, session, admission):
        value = super().verify_client_record(binding, session, admission)
        if value['operation']['argv'][:2] == ['am', 'instrument'] and c.instrumentation_kind(value['operation']['argv']) == 'restart':
            path = Path(admission['root'])/'claims-v1/restart-v1.json'
            claim = self._json(self._pin(path))
            verify_restart_prerequisite(claim['prerequisite'], admission,
                                        session['admission'], session['running'], session['caller'])
        return value


_REPLAY = _RestartVerifier()


def verify_proof(pin, session, context):
    return _REPLAY.verify_proof(pin, session, context)


def verify_client_record(binding, session, admission):
    return _REPLAY.verify_client_record(binding, session, admission)


def require_current_clients(root, count, session_binding, admission):
    return _REPLAY.require_current_clients(root, count, session_binding, admission)


def verify_owned_target_result(*args, **kwargs):
    return _REPLAY.verify_owned_target_result(*args, **kwargs)


def verify_guest_inputs(*args, **kwargs):
    return _REPLAY.verify_guest_inputs(*args, **kwargs)


def verify_controller_result(binding, admission, admission_binding, running_binding):
    value = _json(binding)
    c._obj(value, RESULT_KEYS)
    c._int(value['version'], 1, 1)
    c._need(value['protocol'] == 'original-author-restart-controller-v1' and
            value['outcome'] == 'completed' and value['phase'] == 'completed' and
            value['reason'] is None and value['observer_handles_closed'] is True and
            value['feature_acceptance'] is False, 'capability')
    c._int(value['elapsed_ms'], 0, 1350000, 'budget')
    request = _json(value['request'])
    c._obj(request, REQUEST_KEYS)
    c._int(request['version'], 1, 1)
    c._need(request['protocol'] == 'original-author-restart-controller-request-v1', 'binding')
    _same(request['admission'], admission_binding)
    _same(request['running'], running_binding)
    _same(request['build'], admission['artifacts']['build'])
    _same(request['sources'], admission['sources'])
    _same(request['python'], admission['python'])
    expected_source = next(p for p in admission['sources'] if PureWindowsPath(p['path']).name == 'original_author_restart_controller.py')
    _same(request['controller'], expected_source)
    c._need(type(request['head']) is str and re.fullmatch('[0-9a-f]{40}', request['head']) is not None, 'source')
    c._int(request['seconds'], 1200, 1200, 'budget')
    root = c._path(request['root'], project=True)
    c._need(PureWindowsPath(binding['path']) == root/'controller-result-v1.json' and
            PureWindowsPath(value['request']['path']) == root/'request-v1.json', 'binding')
    session = c.validate_session(_json(value['session']), admission)
    _same(session['root'], request['root'])
    verify_restart_prerequisite(value['prerequisite'], admission, admission_binding, running_binding, session['caller'])
    prior = _json(value['prerequisite'])
    _same(prior['session'], value['session'])
    records = require_current_clients(request['root'], value['client_count'], value['session'], admission)
    selected = _instrument(value['restart_instrumentation'], session, admission, 'restart')
    final_boot = _client(value['boot_final'], session, admission, [HELPER, '--boot'])
    _empty_stderr(final_boot)
    initial_boot = _client(prior['boot_initial'], session, admission, [HELPER, '--boot'])
    c._need(parse_probe(_stdout(final_boot), 'boot')['boot_id'] ==
            parse_probe(_stdout(initial_boot), 'boot')['boot_id'], 'identity')
    after = c.validate_client_record(_json(prior['probe_after']), session)
    c._need(after['index'] < selected['index'] < final_boot['index'] <= len(records), 'clock')
    c._obj(value['restart_artifacts'], restart.RECORDS, 'binding')
    newer = {name: _raw(value['restart_artifacts'][name], restart.MAX_ARTIFACT) for name in restart.RECORDS}
    baseline = {name: _raw(prior['author_artifacts'][name], author.MAX_ARTIFACT) for name in author.RECORDS+author.TRACES}
    restart.validate_restart(_raw(value['restart_proof'], restart.MAX_PROOF), newer,
                             _raw(prior['author_proof']), baseline, _raw(prior['import_proof']))
    return copy.deepcopy(value)
