"""Fixed source/worker-bound read-only physical inventory CLI.

No import IO, ordinary ADB executable, service lifecycle, arbitrary command,
implementation selector or target fallback. Raw reports stay private. A declared
serial is not human authorization; actual use needs separately retained scope.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import importlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from benchmarks import adb_held_socket as old
from benchmarks import adb_device_roster as roster
from benchmarks import adb_device_roster_probe as shared
from benchmarks import adb_held_socket_probe as files
from benchmarks import receipt_avd_environment as env
from benchmarks import windows_tcp_control as output_control

PROTOCOL = 'physical-phone-inventory-v1'
BARRIER = b'LL_PHYSICAL_PHONE_INVENTORY_V1\n'
OWNER_SECONDS = 45
MAX_ADMISSION = files.MAX_ADMISSION
MAX_REQUEST = files.MAX_REQUEST
MAX_REPORT = 2 * 1024 * 1024
PUBLIC_SOURCES = (*shared.PUBLIC_SOURCES, 'benchmarks/physical_phone_inventory.py',
                  'benchmarks/physical_phone_inventory_windows.py', 'benchmarks/physical_phone_inventory_probe.py')
RESULT_KEYS = {'version', 'protocol', 'status', 'reason', 'acquisition_completed', 'inventory_observed',
               'feature_acceptance', 'sources_equal', 'python_equal', 'admission', 'request', 'owner',
               'version_report', 'version_bytes', 'roster_report', 'report', 'worker'}
CliRefused = files.CliRefused
_need, _same = files._need, files._same
_read_bound, _existing_D_file = files._read_bound, files._existing_D_file
_python_bindings, _set_temporary = files._python_bindings, files._set_temporary
_write_bytes, _snapshot_after = files._write_bytes, files._snapshot_after
_arguments, _read_version_bytes = files._arguments, shared._read_version_bytes
_worker_identity = shared._worker_identity


def _contract():
    return importlib.import_module('benchmarks.physical_phone_inventory')


def _backend_types():
    known = importlib.import_module('benchmarks.adb_device_roster_windows')
    inventory = importlib.import_module('benchmarks.physical_phone_inventory_windows')
    return known.WindowsVersionRecordingBackend, known.WindowsRosterBackend, inventory.WindowsPhoneInventoryBackend


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
        _need(time.monotonic() < until, 'request'); time.sleep(.01)
    started_pin = env.binding(started_path)
    _, started = _read_bound(started_path, started_pin['sha256'], MAX_ADMISSION, 'request')
    _need(type(started) is dict and set(started) == {'worker', 'request'} and
          _same(started['request'], request_pin), 'request')
    old._process(started['worker'])
    _need(_same(started['worker'], env.process_identity(os.getpid())) and
          started['worker']['executable'] == request['python']['executable']['path'], 'request')
    env.check_binding(request_pin); env.check_binding(started_pin)
    _set_temporary()
    version_type, roster_type, inventory_type = _backend_types()
    version_backend = version_type()
    version = old.probe(version_backend, _contract().backend_admission(admitted))
    raw = version_backend.received_bytes
    _need(type(raw) is bytes and len(raw) <= 13, 'report')
    _write_bytes(output/'version-bytes-v1.bin', raw)
    _write_bytes(output/'version-report-v1.json', files._report_bytes(version, _contract().backend_admission(admitted)))
    roster_report = roster.probe(roster_type(), _contract().roster_admission(admitted), version)
    _write_bytes(output/'roster-report-v1.json', roster.report_bytes(roster_report, _contract().roster_admission(admitted)))
    report = _contract().probe(inventory_type(), admitted, roster_report)
    _write_bytes(output/'report-v1.json', _contract().report_bytes(report, admitted))
    _check_bindings(request['source_closure'], request['python'])
    for pin in (bound, request_pin, started_pin): env.check_binding(pin)
    for name in ('version-bytes-v1.bin', 'version-report-v1.json', 'roster-report-v1.json', 'report-v1.json'):
        env.check_binding(env.binding(output/name))
    return 0


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
        worker = env.process_identity(child.pid); old._process(worker)
        _need(worker['executable'] == python['executable']['path'], 'request')
        staged = output/'started.pending-v1.json'
        env.create_json(staged, dict(worker=worker, request=request_pin)); staged.rename(output/'started-v1.json')
        started_pin = env.binding(output/'started-v1.json')
        return True
    owner = env.supervise([sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()), '_worker',
        str(output/'request-v1.json'), request_pin['sha256']], BARRIER, output, OWNER_SECONDS, started)
    env.create_json(output/'owner-result-v1.json', owner)
    after = _snapshot_after(output/'source-closure-after-v1.json', _source_bindings, 'source')
    python_after = _snapshot_after(output/'python-after-v1.json', _python_bindings, 'python')
    source_equal, python_equal = _same(sources, after), _same(python, python_after)
    known = (owner['status'] == 'child_exited' and type(owner['worker_returncode']) is int and owner['worker_returncode'] == 0
        and owner['cleanup_complete'] is True and owner['output_capture_complete'] is True
        and all(type(owner[k]) is int and owner[k] >= 0 for k in ('stdout_bytes', 'stderr_bytes'))
        and owner['stderr_bytes'] == owner['stdout_bytes'] == 0)
    acquired = observed = False
    reason = 'owner_failed'
    reports = dict(version_report=None, version_bytes=None, roster_report=None, report=None)
    try:
        _need(known, 'report')
        if not source_equal: reason = 'source_changed'; raise CliRefused('source')
        if not python_equal: reason = 'python_changed'; raise CliRefused('python')
        reason = 'request_changed'; env.check_binding(request_pin)
        reason = 'admission_changed'; env.check_binding(admission)
        reason = 'report_missing'
        for key, name in (('version_report', 'version-report-v1.json'), ('version_bytes', 'version-bytes-v1.bin'),
                          ('roster_report', 'roster-report-v1.json'), ('report', 'report-v1.json')):
            reports[key] = env.binding(output/name)
        reason = 'report_invalid'
        _, version = _read_bound(reports['version_report']['path'], reports['version_report']['sha256'], files.MAX_REPORT, 'report')
        _, prior = _read_bound(reports['roster_report']['path'], reports['roster_report']['sha256'], MAX_REPORT, 'report')
        _, report = _read_bound(reports['report']['path'], reports['report']['sha256'], MAX_REPORT, 'report')
        raw_version = _read_version_bytes(reports['version_bytes'], output)
        files._report_bytes(version, _contract().backend_admission(admitted))
        roster.report_bytes(prior, _contract().roster_admission(admitted))
        _contract().report_bytes(report, admitted)
        acquired = True; reason = 'proof_refused'
        if _contract().report_verified(report, admitted) is True:
            reason = 'prior_reports'
            _need(_same(report['roster_proof'], prior) and _same(prior['version_proof'], version) and
                  version['response_hex'] == raw_version.hex(), 'report')
            reason = 'worker_identity'; _need(started_pin is not None, 'report')
            _, actual_started = _read_bound(output/'started-v1.json', started_pin['sha256'], MAX_ADMISSION, 'report')
            observed = all(_worker_identity(value, actual_started, python, request_pin) for value in (version, prior, report))
        _check_bindings(sources, python)
        for pin in (admission, request_pin, *reports.values()): env.check_binding(pin)
        if observed: reason = None
    except (CliRefused, env.EnvironmentRefused, OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError):
        observed = False
    final_sources = _snapshot_after(output/'source-closure-final-v1.json', _source_bindings, 'source')
    final_python = _snapshot_after(output/'python-final-v1.json', _python_bindings, 'python')
    source_equal = source_equal and _same(sources, final_sources)
    python_equal = python_equal and _same(python, final_python)
    if not source_equal: acquired = observed = False; reason = 'source_changed'
    elif not python_equal: acquired = observed = False; reason = 'python_changed'
    else:
        for pin, failure in ((admission, 'admission_changed'), (request_pin, 'request_changed'),
                             (started_pin, 'worker_identity'), *((pin, 'report_invalid') for pin in reports.values())):
            if pin is None: continue
            try: env.check_binding(pin)
            except (env.EnvironmentRefused, OSError, ValueError, TypeError, KeyError, OverflowError):
                acquired = observed = False; reason = failure
    status = 'observed' if observed else 'refused'
    value = dict(version=1, protocol=PROTOCOL, status=status, reason=reason, acquisition_completed=acquired,
        inventory_observed=observed, feature_acceptance=False, sources_equal=source_equal, python_equal=python_equal,
        admission=admission, request=request_pin, owner=env.binding(output/'owner-result-v1.json'), worker=started_pin, **reports)
    _need(set(value) == RESULT_KEYS, 'report'); env.create_json(output/'result-v1.json', value)
    print(json.dumps(dict(status=status, reason=reason, acquisition_completed=acquired,
        inventory_observed=observed, feature_acceptance=False)), flush=True)
    return 0 if observed else 1


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if os.name != 'nt': raise CliRefused('platform')
        if type(args) is list and len(args) == 3 and args[0] == '_worker': return _worker(Path(args[1]), args[2])
        if args == ['--help']:
            print('python -B -m benchmarks.physical_phone_inventory_probe --admission <D: JSON> --admission-sha256 <sha256> --output <missing physical D: directory>')
            return 0
        options = _arguments(args)
        output = output_control.validate_output(options['--output'])
        binding, admitted = _load_admission(options['--admission'], options['--admission-sha256'])
        return _dispatch(output, binding, admitted)
    except (CliRefused, output_control.ControlRefused, env.EnvironmentRefused, OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
        reason = error.reason if type(error) in (CliRefused, output_control.ControlRefused) else 'request'
        print(json.dumps(dict(status='refused', reason=reason, acquisition_completed=False,
            inventory_observed=False, feature_acceptance=False)), flush=True)
        return 1


if __name__ == '__main__': raise SystemExit(main())