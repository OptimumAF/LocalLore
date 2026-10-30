"""Closed SDK6 replay for a held AUTHOR and an observed live-process fault.

No target, process, socket, credential or model runtime operation is performed.
Shell completion of the deliberately interrupted runner is never JUnit success.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
from pathlib import Path, PureWindowsPath
import re
import sys
import tarfile

from benchmarks import android_process_verification_v4 as shared
from benchmarks import android_process_verification_v5 as passive
from benchmarks import android_live_death_witness as witness
from benchmarks import original_author_model_proof as author
from benchmarks import original_author_restart_proof as restart
from benchmarks import owned_live_death_contract as c
from benchmarks import receipt_avd_environment as env
from benchmarks.android_instrumentation_evidence import validate_instrumentation

_IO = shared._Verifier(c)
CHECKPOINT_ROOT = 'no_backup/original-author-live-checkpoint-v1'
CHECKPOINT_FILES = ('ready-v1.json', 'catalog-v1.json', 'snapshot-v1.json')
PREREQUISITE_KEYS = frozenset((
    'version', 'protocol', 'admission', 'running', 'build', 'control_session',
    'author_session', 'pending', 'ready', 'ready_client', 'preflight_client',
    'preflight_artifacts', 'checkpoint_artifacts',
    'boot_initial', 'probe_before', 'force_stop', 'probe_after', 'import_proof',
    'author_proof', 'author_artifacts', 'import_instrumentation', 'package_checks',
))


def _same(a, b, reason='binding'):
    c._need(c._same(a, b), reason)


def _current_sources(a):
    _same(a['sources'], c.source_bindings(), 'source')
    _same(a['python']['executable'], env.binding(Path(sys.executable)), 'source')
    _same(a['artifacts']['process_probe_source'], env.binding(
        Path(__file__).resolve().parents[1]/'benchmarks/native/android_author_process_probe.c'), 'source')
    for pin in a['sources'] + [x for x in a['python'].values() if x is not None]:
        env.check_binding(pin)


def _raw(pin, cap=4*1024*1024):
    return _IO._raw(pin, cap)


def _json(pin):
    return _IO._json(pin)


def _stdout(row):
    c._need(_raw(row['stderr']) == b'', 'capability')
    return _raw(row['stdout'])


def _client(pin, session, admission, argv):
    peek = c.validate_client_record(_json(pin), session)
    _same(peek['operation'], dict(argv=argv, stdin=None), 'command')
    row = _IO.verify_client_record(pin, session, admission)
    c._need(row['returncode'] == 0, 'capability')
    _stdout(row)
    return row


def instrument_argv(kind):
    selected = next((row for row in c.INSTRUMENTATIONS if row[0] == kind), None)
    c._need(selected is not None, 'command')
    return ['am', 'instrument', '-w', '-r', '-e', 'class', selected[1]+'#'+selected[2],
            c.TEST+'/androidx.test.runner.AndroidJUnitRunner']


def preflight_paths():
    return (['no_backup/original-author-proof-v1/'+name for name in
             ('proof-v1.json', *author.RECORDS, *author.TRACES)] +
            [CHECKPOINT_ROOT+'/'+name for name in CHECKPOINT_FILES])


def unpack_preflight(raw, uid):
    """A single fixed read authenticates the completed proof while it is held."""
    paths = preflight_paths()
    c._need(type(raw) is bytes and 0 < len(raw) <= 4*1024*1024, 'binding')
    result = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as packed:
            members = packed.getmembers()
            c._need(len(members) == len(paths) and {m.name for m in members} == set(paths), 'binding')
            for item in members:
                c._need(item.isfile() and not item.islnk() and not item.issym() and item.uid == uid and
                        0 < item.size <= author.MAX_ARTIFACT, 'binding')
                with packed.extractfile(item) as stream:
                    data = stream.read(author.MAX_ARTIFACT+1)
                c._need(len(data) == item.size, 'binding')
                result[item.name] = data
    except (tarfile.TarError, OSError, ValueError, TypeError):
        raise c.TargetRefused('binding') from None
    return result


def validate_live_baseline(raw_ready, authored, imported, artifacts, checkpoint_files, uid):
    baseline = author.validate_author(authored, artifacts, imported, expected_prompt_version='initial-world-v1.1')
    c._need(baseline['process']['uid'] == uid and checkpoint_files['ready-v1.json'] == raw_ready, 'identity')
    catalog, snapshot = checkpoint_files['catalog-v1.json'], checkpoint_files['snapshot-v1.json']
    selected = witness.validate_checkpoint(raw_ready, author_proof_sha256=hashlib.sha256(authored).hexdigest(),
        import_proof_sha256=hashlib.sha256(imported).hexdigest(), expected_process=baseline['process'],
        catalog_sha256=hashlib.sha256(catalog).hexdigest(), snapshot_sha256=hashlib.sha256(snapshot).hexdigest())
    for new, old, fields in ((catalog, artifacts['workspace-created-v1.json'],
            ('persistent', 'location', 'schema_version', 'database_schema_version', 'stories')),
            (snapshot, artifacts['snapshot-created-v1.json'], ('scope', 'revision', 'rules', 'player', 'inventory', 'receipts'))):
        _same(author._reply(author._json(new), fields), author._reply(author._json(old), fields), 'canonical')
    return selected


def validate_interrupted_instrumentation(raw):
    """Recognize the pinned raw crash report, without declaring a test passed."""
    c._need(type(raw) is bytes and 0 < len(raw) <= 262144 and b'\0' not in raw, 'capability')
    try:
        lines = [line.strip() for line in raw.decode('utf-8', errors='strict').splitlines() if line.strip()]
    except UnicodeError:
        raise c.TargetRefused('capability') from None
    c._need(len(lines) <= 4096 and
            lines.count('INSTRUMENTATION_RESULT: shortMsg=Process crashed.') == 1 and
            len([line for line in lines if line.startswith('INSTRUMENTATION_CODE:')]) == 1 and
            lines[-1] == 'INSTRUMENTATION_CODE: 0' and
            not any(line.startswith(('OK (', 'FAILURES!!!', 'INSTRUMENTATION_FAILED:')) or
                    line == 'INSTRUMENTATION_STATUS_CODE: 0' for line in lines), 'capability')
    return dict(report='interrupted', junit_success=False)


def _instrument(pin, session, admission, kind):
    row = _client(pin, session, admission, instrument_argv(kind))
    selected = next(item for item in c.INSTRUMENTATIONS if item[0] == kind)
    if kind == 'author_live':
        validate_interrupted_instrumentation(_stdout(row))
    else:
        validate_instrumentation(_stdout(row), selected[1], [selected[2]])
    return row


def _counts(rows, expected):
    observed = {kind: 0 for kind in c.CLAIM_KINDS}
    for row in rows:
        if row['operation']['argv'][:2] == ['am', 'instrument']:
            observed[c.instrumentation_kind(row['operation']['argv'])] += 1
    _same(observed, expected, 'spent')


def _prefix(session, a, count):
    c._int(count, 1, 10000, 'binding')
    rows = []
    for index in range(1, count+1):
        pin = _IO._pin(Path(session['root'])/'clients'/('command-%04d.json' % index))
        peek = c.validate_client_record(_json(pin), session)
        argv = peek['operation']['argv']
        c._need(argv[:2] != ['am', 'instrument'] or c.instrumentation_kind(argv) != 'restart', 'command')
        rows.append(_IO.verify_client_record(pin, session, a))
        c._need(rows[-1]['index'] == index and rows[-1]['returncode'] == 0, 'capability')
    return rows


def _collection(rows, session, remote, local, pins, uid, lower, upper):
    """Bind exact copied bytes to qualified ls/hash/tar/hash calls and tar UID."""
    names = tuple(pins)
    paths = [remote+'/'+name for name in names]
    prefix = ['run-as', c.APP, '--user', '0']
    recipes = [prefix+['ls', remote], prefix+['sha256sum', *paths],
               prefix+['tar', '-cf', '-', *paths], prefix+['sha256sum', *paths]]
    candidates = [row for row in rows if lower < row['index'] < upper]
    selected = []
    for position, argv in enumerate(recipes):
        matches = [row for row in candidates if row['operation'] == dict(argv=argv, stdin=None)]
        c._need(len(matches) == (2 if position in (1, 3) else 1), 'binding')
        selected.append(matches[-1] if position == 3 else matches[0])
    order = [row['index'] for row in selected]
    c._need(order == sorted(set(order)), 'clock')
    directories = {'workspace-v1', 'archive-staging'} if remote == 'no_backup/original-author-proof-v1' else (
        {'archive-staging'} if remote == 'no_backup/original-author-restart-proof-v1' else set())
    listed = _stdout(selected[0]).decode('ascii').splitlines()
    c._need(len(listed) == len(set(listed)) and set(listed) == set(names)|directories, 'binding')
    values = {}
    for name in names:
        c._need(PureWindowsPath(pins[name]['path']) == PureWindowsPath(session['root'])/local/name, 'binding')
        values[name] = _raw(pins[name], author.MAX_ARTIFACT)
    expected = {remote+'/'+name: hashlib.sha256(raw).hexdigest() for name, raw in values.items()}
    for row in (selected[1], selected[3]):
        observed = {}
        for line in _stdout(row).decode('ascii').splitlines():
            match = re.fullmatch(r'([0-9a-f]{64})  (no_backup/[A-Za-z0-9_./-]+)', line)
            c._need(match is not None and match[2] not in observed, 'binding')
            observed[match[2]] = match[1]
        _same(observed, expected)
    try:
        with tarfile.open(fileobj=io.BytesIO(_stdout(selected[2])), mode='r:') as packed:
            members = packed.getmembers()
            c._need(len(members) == len(paths) and {item.name for item in members} == set(paths), 'binding')
            for item in members:
                c._need(item.isfile() and not item.islnk() and not item.issym() and item.uid == uid and
                        0 < item.size <= author.MAX_ARTIFACT, 'binding')
                with packed.extractfile(item) as stream:
                    raw = stream.read(author.MAX_ARTIFACT+1)
                c._need(raw == values[item.name.rsplit('/', 1)[1]] and len(raw) == item.size, 'binding')
    except (tarfile.TarError, OSError, ValueError, TypeError):
        raise c.TargetRefused('binding') from None
    return values


def _packages(checks, session, a):
    c._obj(checks, ('product', 'tests'), 'binding')
    uids, indices = {}, []
    for key, package, artifact in (('product', c.APP, 'product_apk'), ('tests', c.TEST, 'test_apk')):
        row = checks[key]
        c._obj(row, ('uid', 'path', 'sha256'), 'binding')
        uid = _client(row['uid'], session, a, ['cmd', 'package', 'list', 'packages', '-U', '--user', '0', package])
        path = _client(row['path'], session, a, ['cmd', 'package', 'path', '--user', '0', package])
        uids[package] = passive._uid(_stdout(uid), package)
        location = _stdout(path).decode('ascii').strip()
        c._need(re.fullmatch(r'package:/data/app/[A-Za-z0-9_~=/.-]+/base\.apk', location) is not None, 'identity')
        location = location[len('package:'):]
        hashed = _client(row['sha256'], session, a, ['sha256sum', location])
        c._need(_stdout(hashed) == (a['artifacts'][artifact]['sha256']+'  '+location+'\n').encode('ascii'), 'binding')
        indices += [uid['index'], path['index'], hashed['index']]
    c._need(indices == sorted(set(indices)) and uids[c.APP] != uids[c.TEST], 'identity')
    return uids, indices


def verify_pending_author(pin, admission, admission_binding, running_binding, control_session):
    """Authenticate the distinct process/session and known terminal capture."""
    a = c.validate_admission(admission)
    value = _json(pin)
    c._obj(value, ('version', 'protocol', 'request', 'started', 'worker', 'owner', 'after'), 'binding')
    c._need(type(value['version']) is int and value['version'] == 1 and
            value['protocol'] == 'owned-live-author-result-v1', 'binding')
    request = _json(value['request'])
    c._obj(request, ('version', 'protocol', 'admission', 'running', 'control_session', 'root',
                     'sources', 'python', 'controller', 'seconds', 'owner_seconds'), 'binding')
    c._need(type(request['version']) is int and request['version'] == 1 and
            request['protocol'] == 'owned-live-author-request-v1' and
            type(request['seconds']) is int and request['seconds'] == 240 and
            type(request['owner_seconds']) is int and request['owner_seconds'] == 270, 'budget')
    _same(request['admission'], admission_binding); _same(request['running'], running_binding)
    _same(request['control_session'], control_session)
    _same(request['sources'], a['sources']); _same(request['python'], a['python'])
    _same(request['controller'], next(p for p in a['sources'] if PureWindowsPath(p['path']).name == 'original_author_live_death_controller.py'))
    root = Path(request['root'])
    for key, name in (('request', 'request-v1.json'), ('started', 'started-v1.json'),
                      ('worker', 'worker-result-v1.json'), ('owner', 'owner-result-v1.json'),
                      ('after', 'after-v1.json')):
        c._need(PureWindowsPath(value[key]['path']) == PureWindowsPath(str(root/name)), 'binding')
    c._need(PureWindowsPath(pin['path']) == PureWindowsPath(str(root/'result-v1.json')), 'binding')
    started = _json(value['started'])
    c._obj(started, ('request', 'worker'), 'binding'); _same(started['request'], value['request'])
    c._process(started['worker'])
    parent_session = c.validate_session(_json(control_session), a)
    c._need(started['worker']['pid'] != parent_session['caller']['pid'], 'identity')
    owner = _json(value['owner'])
    c._obj(owner, ('status', 'cleanup_complete', 'elapsed_ms', 'worker_returncode',
                  'stdout_bytes', 'stderr_bytes', 'output_capture_complete'), 'cleanup')
    c._int(owner['elapsed_ms'], 0, 282000, 'budget')
    c._int(owner['stdout_bytes'], 0, 0, 'cleanup'); c._int(owner['stderr_bytes'], 0, 0, 'cleanup')
    c._need(owner['status'] == 'child_exited' and type(owner['worker_returncode']) is int and
            owner['worker_returncode'] == 0 and owner['cleanup_complete'] is True and
            owner['output_capture_complete'] is True and owner['stdout_bytes'] == owner['stderr_bytes'] == 0, 'cleanup')
    for channel in ('stdout', 'stderr'):
        c._need(env.safe_path(root/'worker-output-v1'/('owner-'+channel+'-v1.bin')).read_bytes() == b'', 'cleanup')
    worker = _json(value['worker'])
    c._obj(worker, ('version', 'protocol', 'request', 'session', 'client', 'client_count', 'outcome', 'observer_handles_closed'), 'binding')
    c._need(type(worker['version']) is int and worker['version'] == 1 and
            worker['protocol'] == 'owned-live-author-worker-v1' and worker['outcome'] == 'captured' and
            type(worker['client_count']) is int and worker['client_count'] == 1 and
            worker['observer_handles_closed'] is True, 'capability')
    _same(worker['request'], value['request'])
    session = c.validate_session(_json(worker['session']), a)
    _same(session['admission'], admission_binding); _same(session['running'], running_binding)
    _same(session['caller'], started['worker'], 'identity')
    c._need(PureWindowsPath(session['root']) == PureWindowsPath(str(root/'capture-v1')) and
            session['seconds'] == 240 and session['deadline_epoch'] <= parent_session['deadline_epoch'], 'budget')
    rows = _IO.require_current_clients(session['root'], 1, worker['session'], a)
    _counts(rows, {'import': 0, 'author_live': 1, 'restart': 0})
    instrument = _instrument(worker['client'], session, a, 'author_live')
    c._need(instrument['index'] == 1, 'binding')
    after = _json(value['after'])
    _same(after, dict(request=value['request'], worker=started['worker'], sources=a['sources'],
                      python=a['python'], process_handles_closed=True))
    return copy.deepcopy(worker)


def verify_restart_prerequisite(pin, admission, admission_binding, running_binding, caller):
    a = c.validate_admission(admission); _current_sources(a)
    value = _IO._at(pin, Path(a['root'])/'restart-prerequisite-v1.json')
    c._obj(value, PREREQUISITE_KEYS)
    c._need(type(value['version']) is int and value['version'] == 1 and
            value['protocol'] == 'original-author-live-death-prerequisite-v1', 'binding')
    _same(value['admission'], admission_binding); _same(value['running'], running_binding)
    _same(value['build'], a['artifacts']['build'])
    session = c.validate_session(_json(value['control_session']), a)
    _same(session['caller'], caller, 'identity'); _same(session['admission'], admission_binding)
    _same(session['running'], running_binding)
    pending = verify_pending_author(value['pending'], a, admission_binding, running_binding, value['control_session'])
    _same(pending['session'], value['author_session'])
    imported = _raw(value['import_proof']); authored = _raw(value['author_proof'])
    c._obj(value['author_artifacts'], author.RECORDS+author.TRACES)
    artifacts = {name: _raw(p) for name, p in value['author_artifacts'].items()}
    baseline = author.validate_author(authored, artifacts, imported, expected_prompt_version='initial-world-v1.1')
    uids, package_indices = _packages(value['package_checks'], session, a)
    c._need(uids[c.APP] == baseline['process']['uid'], 'identity')
    boot_row = _client(value['boot_initial'], session, a, [c.PROCESS_PROBE, '--boot'])
    boot = passive.parse_probe(_stdout(boot_row), 'boot')['boot_id']
    ready_row = _client(value['ready_client'], session, a,
                        ['run-as', c.APP, '--user', '0', 'cat', CHECKPOINT_ROOT+'/ready-v1.json'])
    raw_ready = _raw(value['ready'], 8192); c._need(raw_ready == _stdout(ready_row), 'binding')
    c._obj(value['checkpoint_artifacts'], CHECKPOINT_FILES)
    ready = _raw(value['checkpoint_artifacts']['ready-v1.json'], 8192)
    c._need(ready == raw_ready, 'binding')
    catalog = _raw(value['checkpoint_artifacts']['catalog-v1.json'])
    snapshot = _raw(value['checkpoint_artifacts']['snapshot-v1.json'])
    selected = validate_live_baseline(raw_ready, authored, imported, artifacts,
        {name: _raw(value['checkpoint_artifacts'][name]) for name in CHECKPOINT_FILES}, uids[c.APP])
    preflight = _client(value['preflight_client'], session, a,
        ['run-as', c.APP, '--user', '0', 'tar', '-cf', '-', *preflight_paths()])
    preflight_files = unpack_preflight(_stdout(preflight), uids[c.APP])
    c._obj(value['preflight_artifacts'], ('author', 'checkpoint'))
    c._obj(value['preflight_artifacts']['author'], ('proof-v1.json', *author.RECORDS, *author.TRACES))
    c._obj(value['preflight_artifacts']['checkpoint'], CHECKPOINT_FILES)
    for group, remote in (('author', 'no_backup/original-author-proof-v1'), ('checkpoint', CHECKPOINT_ROOT)):
        for name, pin in value['preflight_artifacts'][group].items():
            c._need(PureWindowsPath(pin['path']) == PureWindowsPath(session['root'])/'live-preflight'/group/name, 'binding')
            expected = authored if group == 'author' and name == 'proof-v1.json' else (
                artifacts[name] if group == 'author' else _raw(value['checkpoint_artifacts'][name]))
            c._need(_raw(pin) == preflight_files[remote+'/'+name] == expected, 'binding')
    args = [c.PROCESS_PROBE, '--snapshot-v2', str(selected['process']['pid']), str(selected['process']['uid'])]
    before = _client(value['probe_before'], session, a, args)
    stop = _client(value['force_stop'], session, a, ['am', 'force-stop', '--user', '0', c.APP])
    after = _client(value['probe_after'], session, a, args)
    c._need(_stdout(stop) == b'', 'capability')
    first = witness.validate_before(selected, _stdout(before), boot)
    witness.validate_after(selected, first, _stdout(after))
    imported_call = _instrument(value['import_instrumentation'], session, a, 'import')
    order = [boot_row['index'], imported_call['index'], *package_indices, ready_row['index'], preflight['index'],
             before['index'], stop['index'], after['index']]
    c._need(order == sorted(set(order)), 'clock')
    # All post-fault copies must be collected before the restart claim exists.
    upper = max(c.validate_client_record(_json(_IO._pin(Path(session['root'])/'clients'/name)), session)['index']
                for name in (p.name for p in (Path(session['root'])/'clients').glob('command-*.json'))
                if name)
    claim = Path(a['root'])/'claims-v1/restart-v1.json'
    if claim.exists():
        # Do not replay the restart client from its own prerequisite.
        selected_claim = c.validate_claim(_json(_IO._pin(claim)), admission_binding, caller, 'restart',
                                        c.operation_digest(dict(argv=instrument_argv('restart'), stdin=None)))
        _same(selected_claim['prerequisite'], pin)
        candidates = [c.validate_client_record(_json(_IO._pin(p)), session) for p in
                      (Path(session['root'])/'clients').glob('command-*.json')]
        restart_indices = [r['index'] for r in candidates if r['operation']['argv'] == instrument_argv('restart')]
        if restart_indices:
            upper = min(restart_indices)-1
    rows = _prefix(session, a, upper)
    _counts(rows, {'import': 1, 'author_live': 0, 'restart': 0})
    _collection(rows, session, 'no_backup/original-author-import-proof-v1', 'import-proof',
                {'import-v1.json': value['import_proof']}, uids[c.APP], imported_call['index'], ready_row['index'])
    _collection(rows, session, CHECKPOINT_ROOT, 'checkpoint-proof', value['checkpoint_artifacts'],
                uids[c.APP], after['index'], upper+1)
    _collection(rows, session, 'no_backup/original-author-proof-v1', 'author-proof',
                {'proof-v1.json': value['author_proof'], **value['author_artifacts']}, uids[c.APP], after['index'], upper+1)
    _current_sources(a)
    return copy.deepcopy(value)


def verify_proof(*args, **kwargs):
    return _IO.verify_proof(*args, **kwargs)


def verify_client_record(binding, session, admission):
    value = _IO.verify_client_record(binding, session, admission)
    if value['operation']['argv'] == instrument_argv('restart'):
        claim = _json(_IO._pin(Path(admission['root'])/'claims-v1/restart-v1.json'))
        verify_restart_prerequisite(claim['prerequisite'], admission, session['admission'], session['running'], session['caller'])
    return value


def require_current_clients(root, count, session_binding, admission):
    rows = _IO.require_current_clients(root, count, session_binding, admission)
    observed = {kind: 0 for kind in c.CLAIM_KINDS}
    for row in rows:
        if row['operation']['argv'][:2] == ['am', 'instrument']:
            observed[c.instrumentation_kind(row['operation']['argv'])] += 1
        if row['operation']['argv'] == instrument_argv('restart'):
            verify_client_record(_IO._pin(Path(root)/'clients'/('command-%04d.json' % row['index'])),
                                 c.validate_session(_json(session_binding), admission), admission)
    c._need(all(number <= 1 for number in observed.values()), 'spent')
    return rows


def verify_owned_target_result(*args, **kwargs):
    return _IO.verify_owned_target_result(*args, **kwargs)


def verify_guest_inputs(*args, **kwargs):
    return _IO.verify_guest_inputs(*args, **kwargs)


def verify_controller_result(binding, admission, admission_binding, running_binding, expected_caller):
    """Full current-profile replay; a legacy passive result cannot enter here."""
    a = c.validate_admission(admission); _current_sources(a)
    value = _json(binding)
    c._obj(value, ('version', 'protocol', 'request', 'session', 'prerequisite',
        'restart_instrumentation', 'boot_final', 'restart_proof', 'restart_artifacts',
        'client_count', 'outcome', 'phase', 'reason', 'observer_handles_closed',
        'pending_handles_closed', 'feature_acceptance', 'elapsed_ms'))
    c._need(type(value['version']) is int and value['version'] == 1 and
        value['protocol'] == 'original-author-live-death-controller-v1' and
        value['outcome'] == value['phase'] == 'completed' and value['reason'] is None and
        value['observer_handles_closed'] is True and value['pending_handles_closed'] is True and
        value['feature_acceptance'] is False, 'capability')
    c._int(value['elapsed_ms'], 0, 1300000, 'budget')
    request = _json(value['request'])
    c._obj(request, ('version', 'protocol', 'admission', 'running', 'build', 'root', 'head',
        'sources', 'python', 'controller', 'seconds', 'started_epoch', 'deadline_epoch'))
    c._need(type(request['version']) is int and request['version'] == 1 and
            request['protocol'] == 'original-author-live-death-controller-request-v1' and
            type(request['seconds']) is int and request['seconds'] == 1200, 'binding')
    c._clock(request['started_epoch'], request['deadline_epoch'], 1200)
    _same(request['admission'], admission_binding); _same(request['running'], running_binding)
    _same(request['sources'], a['sources']); _same(request['python'], a['python'])
    _same(request['build'], a['artifacts']['build'])
    _same(request['controller'], next(p for p in a['sources'] if PureWindowsPath(p['path']).name == 'original_author_live_death_controller.py'))
    from benchmarks.original_author_restart_controller import _verify_build_closed
    manifest = _verify_build_closed(request['build'], a)
    _same(request['head'], manifest['head'], 'source')
    root = c._path(request['root'], project=True)
    c._need(PureWindowsPath(binding['path']) == root/'controller-result-v1.json' and
            PureWindowsPath(value['request']['path']) == root/'request-v1.json', 'binding')
    session = c.validate_session(_json(value['session']), a)
    c._process(expected_caller); _same(session['caller'], expected_caller, 'identity')
    _same(session['admission'], admission_binding); _same(session['running'], running_binding)
    c._need(PureWindowsPath(session['root']) == root and
            request['started_epoch'] <= session['started_epoch'] < session['deadline_epoch'] <= request['deadline_epoch'], 'budget')
    prior = verify_restart_prerequisite(value['prerequisite'], a, admission_binding, running_binding, expected_caller)
    _same(prior['control_session'], value['session'])
    rows = require_current_clients(request['root'], value['client_count'], value['session'], a)
    _counts(rows, {'import': 1, 'author_live': 0, 'restart': 1})
    selected = _instrument(value['restart_instrumentation'], session, a, 'restart')
    final_boot = _client(value['boot_final'], session, a, [c.PROCESS_PROBE, '--boot'])
    initial_boot = _client(prior['boot_initial'], session, a, [c.PROCESS_PROBE, '--boot'])
    c._need(passive.parse_probe(_stdout(final_boot), 'boot')['boot_id'] ==
            passive.parse_probe(_stdout(initial_boot), 'boot')['boot_id'], 'identity')
    after = c.validate_client_record(_json(prior['probe_after']), session)
    c._need(after['index'] < selected['index'] < final_boot['index'] <= len(rows), 'clock')
    c._obj(value['restart_artifacts'], restart.RECORDS)
    newer = {name: _raw(pin, restart.MAX_ARTIFACT) for name, pin in value['restart_artifacts'].items()}
    baseline = {name: _raw(pin, author.MAX_ARTIFACT) for name, pin in prior['author_artifacts'].items()}
    uid = author.validate_import(_raw(prior['import_proof']))['process']['uid']
    _collection(rows, session, 'no_backup/original-author-restart-proof-v1', 'restart-proof',
        {'proof-v1.json': value['restart_proof'], **value['restart_artifacts']}, uid,
        selected['index'], final_boot['index'])
    restart.validate_restart(_raw(value['restart_proof'], restart.MAX_PROOF), newer,
        _raw(prior['author_proof']), baseline, _raw(prior['import_proof']), expected_prompt_version='initial-world-v1.1')
    _current_sources(a)
    return copy.deepcopy(value)
