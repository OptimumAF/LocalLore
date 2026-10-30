"""Fixed file-only enrollment CLI. It never acquires a roster or a phone.

Capture consistency and a human-choice JSON record cannot authenticate their
own acquisition or human authority. The trusted coordinator supplies both.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).absolute().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from benchmarks import phone_identity_enrollment as contract
from benchmarks import adb_device_roster as roster
from benchmarks import adb_device_roster_probe as roster_cli
from benchmarks import adb_held_socket as held
from benchmarks import receipt_avd_environment as env

need = contract.need
same = roster_cli._same
MAX_JSON = contract.MAX_JSON
_RESULT_PINS = {'admission': ('admission-v1.json', 131072),
    'request': ('roster-v1/request-v1.json', 131072),
    'owner': ('roster-v1/owner-result-v1.json', 4096),
    'worker': ('roster-v1/started-v1.json', 131072),
    'version_report': ('roster-v1/version-report-v1.json', MAX_JSON),
    'version_bytes': ('roster-v1/version-bytes-v1.bin', 13),
    'report': ('roster-v1/report-v1.json', MAX_JSON)}


def _stable(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, value.st_mode, value.st_nlink, getattr(value, 'st_birthtime_ns', None))


def _ordinary(value, cap):
    need(stat.S_ISREG(value.st_mode) and value.st_nlink == 1 and 0 <= value.st_size <= cap
         and type(getattr(value, 'st_birthtime_ns', None)) is int, 'path')


def _expected_pin(value, path, cap):
    contract.pin(value, 'bindings')
    need(value['path'] == str(path) and value['bytes'] <= cap, 'path')


def _read(path, cap, expected=None, sha=None):
    """Bound size and fixed role BEFORE content IO; retain per-API identities."""
    path = Path(path)
    if expected is not None:
        _expected_pin(expected, path, cap)
    if sha is not None:
        contract.digest(sha, 'bindings')
    checked = env.safe_path(path)
    need(checked.drive.upper() == 'D:' and checked == path, 'path')
    before = path.lstat()
    _ordinary(before, cap)
    if expected is not None:
        need(before.st_size == expected['bytes'], 'bindings')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        _ordinary(opened, cap)
        # Windows path/descriptor ctime can differ. Each API must stay stable;
        # join dev/inode/size/mtime and explicit birth, not cross-API ctime.
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_birthtime_ns) ==
             (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_birthtime_ns), 'bindings')
        raw = stream.read(cap+1)
        need(type(raw) is bytes and len(raw) == before.st_size and len(raw) <= cap, 'bindings')
        need(_stable(os.fstat(stream.fileno())) == _stable(opened), 'bindings')
    env.safe_path(path)
    need(_stable(path.lstat()) == _stable(before), 'bindings')
    binding = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    if expected is not None:
        need(same(binding, expected), 'bindings')
    if sha is not None:
        need(binding['sha256'] == sha, 'bindings')
    return binding, raw


def _strict(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'input')
            value[key] = item
        return value
    def constant(_):
        raise contract.EnrollmentRefused('input')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, ValueError, RecursionError):
        raise contract.EnrollmentRefused('input') from None


def _json(path, cap=MAX_JSON, expected=None, sha=None):
    pin, raw = _read(path, cap, expected, sha)
    return pin, _strict(raw)


def _recheck(bindings):
    for binding in bindings:
        # Use the original bounded size, never a new observed unbounded size.
        _read(Path(binding['path']), binding['bytes'], binding)


def _bundle(value):
    path = env.safe_path(value, directory=True)
    need(path.drive.upper() == 'D:' and path.resolve(strict=True) == path and
         not path.is_relative_to(ROOT) and
         all(not os.path.lexists(parent/'.git') for parent in (path, *path.parents)), 'path')
    return path


def _expected_runtime():
    # Fixed code-owned project files and own installed interpreter/DLL only.
    # This can query the current process's DLL location; never a target process.
    return roster_cli._source_bindings(), roster_cli._python_bindings()


def _code_pins():
    return [_read(ROOT/name, MAX_JSON)[0] for name in
            ('benchmarks/phone_identity_enrollment.py', 'benchmarks/phone_identity_enrollment_io.py')]


def _owner(value):
    contract._obj(value, ('status', 'elapsed_ms', 'worker_returncode', 'cleanup_complete',
                         'output_capture_complete', 'stdout_bytes', 'stderr_bytes'), 'owner')
    need(value['status'] == 'child_exited' and type(value['worker_returncode']) is int
         and value['worker_returncode'] == 0 and value['cleanup_complete'] is True
         and value['output_capture_complete'] is True and type(value['elapsed_ms']) is int
         and value['elapsed_ms'] >= 0 and all(type(value[key]) is int and value[key] == 0
             for key in ('stdout_bytes', 'stderr_bytes')), 'owner')


def read_capture(bundle, result_sha):
    root = _bundle(bundle)
    capture = root/'roster-v1'
    result_pin, result = _json(capture/'result-v1.json', sha=result_sha)
    contract._obj(result, roster_cli.RESULT_KEYS, 'capture')
    need(type(result['version']) is int and result['version'] == 1 and result['protocol'] == roster.PROTOCOL
         and result['status'] == 'observed' and result['reason'] is None and result['feature_acceptance'] is False
         and all(result[name] is True for name in
             ('acquisition_completed', 'roster_observed', 'sources_equal', 'python_equal')), 'capture')
    # Validate EVERY embedded input role before following any of them.
    for name, (relative, cap) in _RESULT_PINS.items():
        _expected_pin(result[name], root/relative, cap)
    bindings = [result_pin]
    values = {}
    for name, (relative, cap) in _RESULT_PINS.items():
        actual, raw = _read(root/relative, cap, result[name])
        bindings.append(actual)
        values[name] = raw if name == 'version_bytes' else _strict(raw)
    admission = roster.validate_admission(values['admission'])
    request = values['request']
    contract._obj(request, ('version', 'protocol', 'output', 'admission', 'validated_admission',
                           'owner_seconds', 'parent', 'source_closure', 'python'), 'capture')
    need(type(request['version']) is int and request['version'] == 1 and request['protocol'] == roster.PROTOCOL
         and request['output'] == str(capture) and same(request['admission'], result['admission'])
         and same(request['validated_admission'], admission) and type(request['owner_seconds']) is int
         and request['owner_seconds'] == roster_cli.OWNER_SECONDS, 'capture')
    held._process(request['parent'])
    current_sources, current_python = _expected_runtime()
    need(same(request['source_closure'], current_sources) and same(request['python'], current_python), 'source')
    for prefix, expected in (('source-closure', current_sources), ('python', current_python)):
        for phase in ('before', 'after', 'final'):
            actual, view = _json(capture/(prefix+'-'+phase+'-v1.json'))
            bindings.append(actual)
            contract._obj(view, ('version', 'status', 'reason', 'bindings'), 'source')
            need(type(view['version']) is int and view['version'] == 1 and view['status'] == 'completed'
                 and view['reason'] is None and same(view['bindings'], expected), 'source')
    _owner(values['owner'])
    for name in ('owner-stdout-v1.bin', 'owner-stderr-v1.bin'):
        actual, raw = _read(capture/name, 0)
        bindings.append(actual)
        need(raw == b'', 'owner')
    started = values['worker']
    contract._obj(started, ('worker', 'request'), 'worker')
    held._process(started['worker'])
    need(same(started['request'], result['request']) and
         started['worker']['executable'] == current_python['executable']['path'], 'worker')
    report, version = values['report'], values['version_report']
    need(roster.report_verified(report, admission) and same(report['version_proof'], version)
         and version['response_hex'] == values['version_bytes'].hex(), 'version')
    need(roster_cli._worker_identity(report, started, current_python, result['request']) and
         roster_cli._worker_identity(version, started, current_python, result['request']), 'worker')
    _recheck(bindings)
    need(same(_expected_runtime(), (current_sources, current_python)), 'source')
    return dict(result_pin=result_pin, admission=admission, report=report, bindings=bindings)


def _write(path, raw):
    need(type(raw) is bytes and len(raw) <= MAX_JSON, 'output')
    env.safe_path(path.parent, directory=True)
    with path.open('xb') as stream:
        rest = memoryview(raw)
        while rest:
            written = stream.write(rest)
            need(type(written) is int and written > 0, 'output')
            rest = rest[written:]
        stream.flush(); os.fsync(stream.fileno())
    return _read(path, len(raw), sha=hashlib.sha256(raw).hexdigest())[0]


def _check_capture(value):
    _recheck(value['bindings'])


def prepare(bundle, result_sha):
    root = _bundle(bundle)
    code = _code_pins()
    capture = read_capture(root, result_sha)
    proposal = contract.make_proposal(capture['result_pin'], capture['admission'], capture['report'])
    directory = root/'review-v1'
    need(not os.path.lexists(directory), 'output')
    _check_capture(capture); _recheck(code)
    directory.mkdir()
    proposed = _write(directory/'proposal-v1.json', contract.encoded(proposal))
    review = _write(directory/'review.html', contract.render_review(proposal, proposed['sha256']).encode('utf-8'))
    _check_capture(capture); _recheck(code)
    result = dict(version=1, protocol=contract.PROTOCOL, status=proposal['status'],
        candidate_count=len(proposal['candidates']), feature_acceptance=False, authority_authenticated=False,
        grants_device_actions=False, capture=capture['result_pin'], proposal=proposed, review=review,
        enrollment_sources=code)
    _write(directory/'prepare-result-v1.json', contract.encoded(result))
    _recheck([proposed, review]); _check_capture(capture); _recheck(code)
    return result


def _selection(bundle, proposal_sha, decision_sha):
    root = _bundle(bundle)
    directory = env.safe_path(root/'review-v1', directory=True)
    proposed, proposal = _json(directory/'proposal-v1.json', sha=proposal_sha)
    contract.validate_proposal(proposal)
    _expected_pin(proposal['capture'], root/'roster-v1/result-v1.json', MAX_JSON)
    capture = read_capture(root, proposal['capture']['sha256'])
    expected = contract.make_proposal(capture['result_pin'], capture['admission'], capture['report'])
    need(same(expected, proposal), 'proposal')
    chosen, decision = _json(directory/'human-choice-v1.json', sha=decision_sha)
    identity = contract.select_identity(proposal, proposed, decision, chosen)
    return root, directory, capture, proposed, chosen, identity


def confirm(bundle, proposal_sha, decision_sha):
    code = _code_pins()
    root, directory, capture, proposed, chosen, identity = _selection(bundle, proposal_sha, decision_sha)
    need(not os.path.lexists(directory/'identity-v1.json') and
         not os.path.lexists(directory/'confirm-result-v1.json'), 'output')
    _check_capture(capture); _recheck([proposed, chosen]+code)
    recorded = _write(directory/'identity-v1.json', contract.encoded(identity))
    result = dict(version=1, protocol=contract.PROTOCOL, status='declared_identity',
        feature_acceptance=False, authority_authenticated=False, grants_device_actions=False,
        capture=capture['result_pin'], proposal=proposed, decision=chosen, identity=recorded, enrollment_sources=code)
    _write(directory/'confirm-result-v1.json', contract.encoded(result))
    _check_capture(capture); _recheck([proposed, chosen, recorded]+code)
    return result


def load_identity(bundle, identity_sha):
    root = _bundle(bundle)
    directory = env.safe_path(root/'review-v1', directory=True)
    recorded, identity = _json(directory/'identity-v1.json', sha=identity_sha)
    contract.validate_identity(identity)
    for name, path in (('capture', root/'roster-v1/result-v1.json'),
                       ('proposal', directory/'proposal-v1.json'), ('decision', directory/'human-choice-v1.json')):
        _expected_pin(identity[name], path, MAX_JSON)
    _, _, capture, proposed, chosen, expected = _selection(root, identity['proposal']['sha256'], identity['decision']['sha256'])
    need(same(identity, expected), 'identity')
    result_pin, result = _json(directory/'confirm-result-v1.json')
    expected_result = dict(version=1, protocol=contract.PROTOCOL, status='declared_identity',
        feature_acceptance=False, authority_authenticated=False, grants_device_actions=False,
        capture=capture['result_pin'], proposal=proposed, decision=chosen, identity=recorded, enrollment_sources=_code_pins())
    need(same(result, expected_result), 'identity')
    _check_capture(capture); _recheck([recorded, proposed, chosen, result_pin]+result['enrollment_sources'])
    return identity


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        need(args and args[0] in ('prepare', 'confirm'), 'input')
        operation, rest = args[0], args[1:]
        flags = ('--bundle', '--result-sha256') if operation == 'prepare' else ('--bundle', '--proposal-sha256', '--decision-sha256')
        need(len(rest) == 2*len(flags), 'input')
        options = {}
        for index in range(0, len(rest), 2):
            key, value = rest[index:index+2]
            need(type(key) is str and key in flags and key not in options and type(value) is str and value, 'input')
            options[key] = value
        need(set(options) == set(flags), 'input')
        result = (prepare(options['--bundle'], options['--result-sha256']) if operation == 'prepare' else
                  confirm(options['--bundle'], options['--proposal-sha256'], options['--decision-sha256']))
        print(json.dumps(dict(status=result['status'], candidate_count=result.get('candidate_count'),
                             feature_acceptance=False, authority_authenticated=False, grants_device_actions=False)))
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as error:
        reason = error.reason if type(error) is contract.EnrollmentRefused else 'input'
        print(json.dumps(dict(status='refused', reason=reason, feature_acceptance=False,
                             authority_authenticated=False, grants_device_actions=False)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
