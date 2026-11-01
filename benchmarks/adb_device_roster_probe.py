"""Explicit source/worker-bound held device-roster CLI; never device admission.

Two fixed exchanges use separate required sockets: legacy version, then roster.
No SDK executable is launched and no backend is selected by JSON. Reports and
all untrusted roster metadata remain private. Installed Python/stdlib is a
trusted tool boundary, not exhaustive runtime attestation. Backend close flags
cover its own resources; external owner capture/termination is additional.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import importlib
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from benchmarks import adb_held_socket as old
from benchmarks import adb_held_socket_probe as helpers
from benchmarks import receipt_avd_environment as env
from benchmarks import windows_tcp_control as output_control

PROTOCOL = 'adb-held-device-roster-v1'
BARRIER = b'LL_ADB_HELD_DEVICE_ROSTER_V1\n'
OWNER_SECONDS = 30
MAX_ADMISSION = helpers.MAX_ADMISSION
MAX_REQUEST = helpers.MAX_REQUEST
MAX_REPORT = 2 * 1024 * 1024
PUBLIC_SOURCES = (*helpers.PUBLIC_SOURCES, 'benchmarks/adb_device_roster.py',
                  'benchmarks/adb_device_roster_windows.py', 'benchmarks/adb_device_roster_probe.py',
                  'benchmarks/receipt_avd_storage.py')
RESULT_KEYS = {'version', 'protocol', 'status', 'reason', 'acquisition_completed',
               'roster_observed', 'feature_acceptance', 'sources_equal', 'python_equal',
               'admission', 'request', 'owner', 'version_report', 'report', 'worker', 'version_bytes'}
CliRefused = helpers.CliRefused
_need = helpers._need
_same = helpers._same
_read_bound = helpers._read_bound
_existing_D_file = helpers._existing_D_file
_python_bindings = helpers._python_bindings
_set_temporary = helpers._set_temporary
_write_bytes = helpers._write_bytes
_snapshot_after = helpers._snapshot_after
_arguments = helpers._arguments


def _contract():
    return importlib.import_module('benchmarks.adb_device_roster')


def _backend_types():
    # Fixed code imports, never a module/class supplied by a request or caller.
    legacy = importlib.import_module('benchmarks.adb_device_roster_windows').WindowsVersionRecordingBackend
    roster = importlib.import_module('benchmarks.adb_device_roster_windows').WindowsRosterBackend
    return legacy, roster


def _load_admission(value, expected):
    try:
        path = _existing_D_file(value, 'admission')
        binding, raw = _read_bound(path, expected, MAX_ADMISSION, 'admission')
        admitted = _contract().validate_admission(raw)
        env.check_binding(binding)
        return binding, admitted
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError, env.EnvironmentRefused):
        raise CliRefused('admission') from None


def _source_bindings():
    try:
        _need(ROOT.drive.upper() == 'D:' and ROOT.resolve(strict=True) == ROOT, 'source')
        names = list(PUBLIC_SOURCES)
        if os.path.lexists(ROOT/'benchmarks/__init__.py'):
            names.append('benchmarks/__init__.py')
        return [env.binding(ROOT/name) for name in sorted(names)]
    except (OSError, ValueError, TypeError, env.EnvironmentRefused):
        raise CliRefused('source') from None


def _check_bindings(sources, python):
    _need(_same(sources, _source_bindings()), 'source')
    _need(_same(python, _python_bindings()), 'python')
    for row in sources+[python['executable']]+([python['runtime_dll']] if python['runtime_dll'] is not None else []):
        env.check_binding(row)


def _worker(path, sha):
    _need(sys.stdin.buffer.read(len(BARRIER)+1) == BARRIER, 'request')
    path = _existing_D_file(str(path), 'request')
    request_pin, request = _read_bound(path, sha, MAX_REQUEST, 'request')
    _need(type(request) is dict and set(request) == {'version', 'protocol', 'output', 'admission',
          'validated_admission', 'owner_seconds', 'parent', 'source_closure', 'python'}, 'request')
    _need(type(request['version']) is int and request['version'] == 1 and request['protocol'] == PROTOCOL and
          type(request['owner_seconds']) is int and request['owner_seconds'] == OWNER_SECONDS, 'request')
    output = env.safe_path(request['output'], directory=True)
    _need(output.drive.upper() == 'D:' and output.resolve(strict=True) == output and
          not output.is_relative_to(ROOT) and path == output/'request-v1.json', 'request')
    cwd = Path.cwd()
    _need(cwd.drive.upper() == 'D:' and cwd.resolve(strict=True) == cwd and
          all(not os.path.lexists(parent/'.git') for parent in (output, *output.parents)), 'request')
    old._process(request['parent'])
    _need(_same(env.process_identity(os.getppid()), request['parent']), 'request')
    _check_bindings(request['source_closure'], request['python'])
    bound, admitted = _load_admission(request['admission']['path'], request['admission']['sha256'])
    _need(_same(bound, request['admission']) and _same(admitted, request['validated_admission']), 'admission')
    until = time.monotonic()+5
    started_path = output/'started-v1.json'
    while not os.path.lexists(started_path):
        _need(time.monotonic() < until, 'request')
        time.sleep(.01)
    started_pin = env.binding(started_path)
    _, started = _read_bound(started_path, started_pin['sha256'], MAX_ADMISSION, 'request')
    _need(type(started) is dict and set(started) == {'worker', 'request'} and
          _same(started['request'], request_pin), 'request')
    old._process(started['worker'])
    _need(_same(started['worker'], env.process_identity(os.getpid())) and
          started['worker']['executable'] == request['python']['executable']['path'], 'request')
    env.check_binding(request_pin); env.check_binding(started_pin)
    _set_temporary()
    legacy_type, roster_type = _backend_types()
    translated = _contract().backend_admission(admitted)
    version_backend = legacy_type()
    version = old.probe(version_backend, translated)
    version_bytes = version_backend.received_bytes
    _need(type(version_bytes) is bytes and len(version_bytes) <= 13, 'report')
    _write_bytes(output/'version-bytes-v1.bin', version_bytes)
    version_bytes_pin = env.binding(output/'version-bytes-v1.bin')
    # Raw bounded report publication precedes verdict; no successful roster is
    # fabricated from a refused version. The new pure probe owns this gate.
    _write_bytes(output/'version-report-v1.json', helpers._report_bytes(version, translated))
    version_pin = env.binding(output/'version-report-v1.json')
    report = _contract().probe(roster_type(), admitted, version)
    _write_bytes(output/'report-v1.json', _contract().report_bytes(report, admitted))
    report_pin = env.binding(output/'report-v1.json')
    _check_bindings(request['source_closure'], request['python'])
    for pin in (bound, request_pin, started_pin, version_pin, version_bytes_pin, report_pin):
        env.check_binding(pin)
    return 0


def _read_version_bytes(binding, output):
    _need(type(binding) is dict and set(binding) == {'path', 'bytes', 'sha256'} and
          binding['path'] == str(output/'version-bytes-v1.bin') and
          type(binding['bytes']) is int and 0 <= binding['bytes'] <= 13, 'report')
    env.check_binding(binding)
    with env.safe_path(binding['path']).open('rb') as source:
        raw = source.read(14)
    _need(len(raw) == binding['bytes'] and hashlib.sha256(raw).hexdigest() == binding['sha256'], 'report')
    env.check_binding(binding)
    return raw


def _worker_identity(report, started, python, request):
    try:
        _need(type(started) is dict and set(started) == {'worker', 'request'} and
              _same(started['request'], request), 'report')
        return helpers._worker_identity(report, {'worker': started['worker']}, python)
    except (CliRefused, KeyError, TypeError, IndexError):
        return False


def _dispatch(output, admission, admitted):
    _set_temporary()
    sources, python = _source_bindings(), _python_bindings()
    parent = env.process_identity(os.getpid())
    output = output_control.validate_output(str(output))
    env.check_binding(admission); _check_bindings(sources, python)
    output.mkdir()
    env.create_json(output/'source-closure-before-v1.json', dict(version=1, status='completed', reason=None, bindings=sources))
    env.create_json(output/'python-before-v1.json', dict(version=1, status='completed', reason=None, bindings=python))
    request = dict(version=1, protocol=PROTOCOL, output=str(output), admission=admission, validated_admission=admitted,
                   owner_seconds=OWNER_SECONDS, parent=parent, source_closure=sources, python=python)
    env.create_json(output/'request-v1.json', request)
    request_pin = env.binding(output/'request-v1.json')
    started_pin = None
    def started(child):
        nonlocal started_pin
        env.check_binding(request_pin)
        worker = env.process_identity(child.pid)
        old._process(worker)
        _need(worker['executable'] == python['executable']['path'], 'request')
        staged = output/'started.pending-v1.json'
        env.create_json(staged, dict(worker=worker, request=request_pin))
        staged.rename(output/'started-v1.json')
        started_pin = env.binding(output/'started-v1.json')
        return True
    owner = env.supervise([sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()), '_worker',
        str(output/'request-v1.json'), request_pin['sha256']], BARRIER, output, OWNER_SECONDS, started)
    env.create_json(output/'owner-result-v1.json', owner)
    after = _snapshot_after(output/'source-closure-after-v1.json', _source_bindings, 'source')
    python_after = _snapshot_after(output/'python-after-v1.json', _python_bindings, 'python')
    source_equal, python_equal = _same(sources, after), _same(python, python_after)
    known = (owner['status'] == 'child_exited' and type(owner['worker_returncode']) is int and owner['worker_returncode'] == 0
        and owner['cleanup_complete'] is True and owner['output_capture_complete'] is True and
        all(type(owner[key]) is int and owner[key] >= 0 for key in ('stdout_bytes', 'stderr_bytes')) and
        owner['stderr_bytes'] == owner['stdout_bytes'] == 0)
    acquired = observed = False
    reason, report_pin, version_pin, version_bytes_pin = 'owner_failed', None, None, None
    row_count = None
    try:
        _need(known, 'report')
        if not source_equal:
            reason = 'source_changed'; raise CliRefused('source')
        if not python_equal:
            reason = 'python_changed'; raise CliRefused('python')
        reason = 'request_changed'; env.check_binding(request_pin)
        reason = 'admission_changed'; env.check_binding(admission)
        reason = 'report_missing'
        report_pin, version_pin = env.binding(output/'report-v1.json'), env.binding(output/'version-report-v1.json')
        version_bytes_pin = env.binding(output/'version-bytes-v1.bin')
        version_bytes = _read_version_bytes(version_bytes_pin, output)
        reason = 'report_invalid'
        _, report = _read_bound(output/'report-v1.json', report_pin['sha256'], MAX_REPORT, 'report')
        _, version = _read_bound(output/'version-report-v1.json', version_pin['sha256'], helpers.MAX_REPORT, 'report')
        _contract().report_bytes(report, admitted)
        helpers._report_bytes(version, _contract().backend_admission(admitted))
        acquired = True; reason = 'proof_refused'
        if _contract().report_verified(report, admitted) is True:
            reason = 'version_report'
            _need(_same(report['version_proof'], version) and
                  version['response_hex'] == version_bytes.hex(), 'report')
            reason = 'worker_identity'
            _need(started_pin is not None, 'report')
            _, actual_started = _read_bound(output/'started-v1.json', started_pin['sha256'], MAX_ADMISSION, 'report')
            observed = (_worker_identity(report, actual_started, python, request_pin) and
                        _worker_identity(version, actual_started, python, request_pin))
            row_count = len(report['rows']) if observed else None
        _check_bindings(sources, python)
        for pin in (admission, request_pin, report_pin, version_pin, version_bytes_pin): env.check_binding(pin)
        if observed: reason = None
    except (CliRefused, env.EnvironmentRefused, OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError):
        observed = False; row_count = None
    final_sources = _snapshot_after(output/'source-closure-final-v1.json', _source_bindings, 'source')
    final_python = _snapshot_after(output/'python-final-v1.json', _python_bindings, 'python')
    source_equal = source_equal and _same(sources, final_sources)
    python_equal = python_equal and _same(python, final_python)
    if not source_equal:
        acquired = observed = False; row_count = None; reason = 'source_changed'
    elif not python_equal:
        acquired = observed = False; row_count = None; reason = 'python_changed'
    else:
        for pin, failure in ((admission, 'admission_changed'), (request_pin, 'request_changed'),
                             (report_pin, 'report_invalid'), (version_pin, 'version_report'),
                             (version_bytes_pin, 'version_report'), (started_pin, 'worker_identity')):
            if pin is None: continue
            try: env.check_binding(pin)
            except (env.EnvironmentRefused, OSError, ValueError, TypeError, KeyError, OverflowError):
                acquired = observed = False; row_count = None; reason = failure
    status = 'observed' if observed else 'refused'
    value = dict(version=1, protocol=PROTOCOL, status=status, reason=reason,
        acquisition_completed=acquired, roster_observed=observed, feature_acceptance=False,
        sources_equal=source_equal, python_equal=python_equal, admission=admission,
        request=request_pin, owner=env.binding(output/'owner-result-v1.json'),
        version_report=version_pin, report=report_pin, worker=started_pin, version_bytes=version_bytes_pin)
    _need(set(value) == RESULT_KEYS, 'report')
    env.create_json(output/'result-v1.json', value)
    print(json.dumps(dict(status=status, reason=reason, acquisition_completed=acquired,
        roster_observed=observed, row_count=row_count, feature_acceptance=False)), flush=True)
    return 0 if observed else 1


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if os.name != 'nt': raise CliRefused('platform')
        if type(args) is list and len(args) == 3 and args[0] == '_worker':
            return _worker(Path(args[1]), args[2])
        if args == ['--help']:
            print('python -B -m benchmarks.adb_device_roster_probe --admission <D: JSON> --admission-sha256 <sha256> --output <missing physical D: directory>')
            return 0
        options = _arguments(args)
        output = output_control.validate_output(options['--output'])
        binding, admitted = _load_admission(options['--admission'], options['--admission-sha256'])
        return _dispatch(output, binding, admitted)
    except (CliRefused, output_control.ControlRefused, env.EnvironmentRefused, OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
        reason = error.reason if type(error) in (CliRefused, output_control.ControlRefused) else 'request'
        print(json.dumps(dict(status='refused', reason=reason, acquisition_completed=False,
            roster_observed=False, row_count=None, feature_acceptance=False)), flush=True)
        return 1


if __name__ == '__main__': raise SystemExit(main())