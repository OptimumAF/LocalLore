"""Explicit exact-image retirement under the shared receipt admission lock.

The execution flag is a trusted operator assertion, not human authorization.
No import performs file, native, process, SDK or device operations.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import copy
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import time

ROOT = Path(__file__).parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from benchmarks import receipt_avd_storage as storage
from benchmarks import receipt_avd_retirement_windows as windows

SECONDS = 900
SCOPE = 'receipt-avd-retirement-v1'
REQUEST_SCOPE = 'receipt-avd-retirement-request-v1'
PLAN_KEYS = frozenset(('version', 'action', 'root', 'proposal_sha256',
                       'evidence_manifest', 'closure', 'remove', 'preserve'))
RESULT_KEYS = frozenset(('version', 'scope', 'outcome', 'phase', 'reason', 'plan',
                         'request', 'marked_count', 'attempted_count', 'cleanup_known',
                         'retirement_recorded', 'elapsed_ms'))
CLEANUP_KEYS = frozenset((
    'auth_handle_closed', 'client_sockets_closed', 'guest_output_capture_complete',
    'guest_pipes_closed', 'guest_preflight_sockets_closed', 'guest_process_handle_closed',
    'guest_terminate_attempted', 'guest_wait_completed', 'preflight_sockets_closed',
    'process_handles_closed', 'server_output_capture_complete', 'server_pipes_closed',
    'server_process_handle_closed', 'server_terminate_attempted', 'server_wait_completed'))
PROTOCOLS = frozenset(('owned-emulator-target-v1', 'owned-emulator-restart-target-v1',
                       'owned-emulator-archive-ui-v1'))


class RetirementRefused(ValueError):
    """A stable reason without private capture text."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _need(condition, reason):
    if not condition:
        raise RetirementRefused(reason)


def _same(left, right):
    return storage.encoded(left) == storage.encoded(right)


def _binding_shape(pin, limit):
    _need(type(pin) is dict and set(pin) == {'path', 'bytes', 'sha256'}, 'binding')
    _need(type(pin['path']) is str and type(pin['bytes']) is int and
          0 <= pin['bytes'] <= limit and type(pin['sha256']) is str and
          re.fullmatch('[0-9a-f]{64}', pin['sha256']) is not None, 'binding')
    _need(str(storage.safe_path(pin['path'])) == pin['path'], 'path')


def _pin(pin, limit=16 * 1024**2):
    _binding_shape(pin, limit)
    storage.check_binding(pin)
    return copy.deepcopy(pin)


def _json(pin):
    _pin(pin)
    value = storage.read_json(pin['path'])
    _pin(pin)
    return value


def _source_bindings():
    return [storage.binding(path) for path in (
        Path(__file__).resolve(), ROOT / 'benchmarks/receipt_avd_storage.py',
        ROOT / 'benchmarks/receipt_avd_retirement_windows.py')]


def _identity(value):
    _need(type(value) is dict and set(value) == {'pid', 'creation_filetime', 'executable'}, 'identity')
    _need(type(value['pid']) is int and 1 <= value['pid'] <= 0xffffffff and
          type(value['creation_filetime']) is int and 1 <= value['creation_filetime'] <= 0xffffffffffffffff and
          type(value['executable']) is str and PureWindowsPath(value['executable']).is_absolute() and
          re.fullmatch('[A-Za-z]:', PureWindowsPath(value['executable']).drive) is not None and
          '\x00' not in value['executable'], 'identity')
    return copy.deepcopy(value)


def _closure(entry):
    closure = _json(entry['closure'])
    _need(closure.get('proposal_sha256') == entry['proposal_sha256'] and
          closure.get('closure_verified') is True and closure.get('cleanup_complete') is True and
          all(key in closure for key in storage.ADAPTER_PROOFS), 'closure')
    proofs = {key: _json(closure[key]) for key in storage.ADAPTER_PROOFS}
    worker, after, owner = proofs['worker_result'], proofs['after'], proofs['owner_result']
    _need(type(owner) is dict and owner.get('status') == 'child_exited' and
          owner.get('cleanup_complete') is True and owner.get('output_capture_complete') is True and
          type(owner.get('worker_returncode')) is int, 'closure')
    _need(type(after) is dict and after.get('process_handles_closed') is True and
          type(worker) is dict and worker.get('protocol') in PROTOCOLS, 'closure')
    admission = proofs['admission']
    _need(type(admission) is dict and admission.get('protocol') == worker['protocol'] and
          _same(worker.get('admission'), closure['admission']) and
          _same(after.get('admission'), closure['admission']), 'closure')
    guest = admission.get('guest')
    _need(type(guest) is dict and guest.get('root') == entry['root'] and
          type(guest.get('proposal')) is dict and
          guest['proposal'].get('sha256') == entry['proposal_sha256'], 'closure')
    cleanup = worker.get('cleanup')
    _need(type(cleanup) is dict and set(cleanup) == CLEANUP_KEYS and
          all(value is True for value in cleanup.values()), 'closure')
    _need(type(worker.get('guest_ancestry')) is list and
          1 <= len(worker['guest_ancestry']) <= 32, 'identity')
    identities = [after.get('owner'), worker.get('worker'), worker.get('server'),
                  *worker['guest_ancestry'], worker.get('guest')]
    unique = {}
    for value in identities:
        value = _identity(value)
        previous = unique.setdefault(value['pid'], value)
        _need(_same(previous, value), 'identity')
    return list(unique.values())


def _records(root, plan, entry):
    identities = _closure(entry)
    _need(_same(plan['closure'], entry['closure']), 'closure')
    preserved = {}
    for pin in plan['preserve']:
        _pin(pin)
        path = Path(pin['path'])
        _need(path.is_relative_to(root), 'preserved_files')
        name = path.relative_to(root).as_posix()
        _need(name not in storage.DISPOSABLE and name not in preserved, 'preserved_files')
        preserved[name] = path
    manifest = storage._evidence(root, plan['evidence_manifest']['path'], preserved, entry['closure'])
    _need(_same(manifest, plan['evidence_manifest']), 'evidence')
    return identities


def _preflight(plan, entry):
    _need(type(plan) is dict and set(plan) == PLAN_KEYS and type(plan['version']) is int and
          plan['version'] == 1 and plan['action'] == 'retire_disposable_images_only', 'plan')
    _need(type(plan['root']) is str and plan['root'] == entry['root'] and entry['state'] == 'closed' and
          _same(plan, entry['retirement']) and plan['proposal_sha256'] == entry['proposal_sha256'], 'plan')
    root = storage.safe_path(plan['root'], exists=True, directory=True)
    _need(type(plan['remove']) is list and 1 <= len(plan['remove']) <= len(storage.DISPOSABLE) and
          type(plan['preserve']) is list and 1 <= len(plan['preserve']) <= 20000, 'plan')
    _pin(plan['evidence_manifest'])
    files = storage._files(root)
    images = {name: path for name, path in files.items() if name in storage.DISPOSABLE}
    _need(images and len(plan['remove']) == len(images), 'image_roster')
    for item, path in zip(plan['remove'], (images[name] for name in sorted(images))):
        _binding_shape(item, storage.BUDGET_BYTES)
        _need(item['path'] == str(path) and path.stat().st_size == item['bytes'], 'image_roster')
    _need(sum(item['bytes'] for item in plan['remove']) <= storage.BUDGET_BYTES, 'image_size')
    current_records = [storage.binding(files[name]) for name in sorted(files) if name not in storage.DISPOSABLE]
    _need(_same(current_records, plan['preserve']), 'preserved_files')
    return root, _records(root, plan, entry)


def _output(path, root, registry):
    path = storage.safe_path(path)
    _need(not storage._contains(root, path) and not storage._contains(registry, path), 'output')
    _need(not path.exists(), 'output')
    storage.safe_path(path.parent, exists=True, directory=True)
    path.mkdir()
    return path, (path.stat().st_dev, path.stat().st_ino)


def _write(output, identity, name, value):
    storage.safe_path(output, exists=True, directory=True)
    _need((output.stat().st_dev, output.stat().st_ino) == identity, 'output')
    path = output / name
    with path.open('xb') as stream:
        stream.write(storage.encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    _need((output.stat().st_dev, output.stat().st_ino) == identity, 'output')
    return storage.binding(path)


def _reason(error):
    if isinstance(error, (KeyboardInterrupt, SystemExit)):
        return 'interrupted'
    value = getattr(error, 'reason', error.args[0] if error.args else '')
    return value if type(value) is str and re.fullmatch('[a-z_]{1,64}', value) else 'checks_failed'


def execute(plan_binding, output_root, *, execute_reviewed_plan=False):
    """Execute only after external owner approval of this exact pinned plan.

    Production callers cannot select another registry or native implementation.
    The flag cannot authenticate a person or supply the missing approval itself.
    """
    return _execute(plan_binding, output_root, storage.DEFAULT_REGISTRY,
                    execute_reviewed_plan=execute_reviewed_plan)


def _execute(plan_binding, output_root, registry, *, execute_reviewed_plan=False):
    """Internal synthetic-registry seam; absent consent refuses before any I/O."""
    _need(execute_reviewed_plan is True, 'not_authorized')
    start = time.monotonic()
    deadline = start + SECONDS
    plan = _json(plan_binding)
    _need(type(plan) is dict and type(plan.get('root')) is str, 'plan')
    root = storage.safe_path(plan['root'], exists=True, directory=True)
    registry = storage.safe_path(registry, exists=True, directory=True)
    storage.safe_path(registry / 'ledger-v1.json', exists=True)
    output, output_identity = _output(Path(output_root), root, registry)
    sources = _source_bindings()
    request = _write(output, output_identity, 'request-v1.json', dict(
        version=1, scope=REQUEST_SCOPE, plan=copy.deepcopy(plan_binding), registry=str(registry),
        root=str(root), sources=sources, seconds=SECONDS, execute_reviewed_plan=True))
    result = dict(version=1, scope=SCOPE, outcome='refused', phase='admission', reason='checks_failed',
                  plan=copy.deepcopy(plan_binding), request=request, marked_count=0, attempted_count=0,
                  cleanup_known=True, retirement_recorded=False, elapsed_ms=0)
    failures = []
    recording = False
    images = None

    def tick():
        _need(time.monotonic() < deadline, 'deadline')

    def conserved(entry, ledger_pin, lock_pin):
        tick()
        _need(_same(_source_bindings(), sources), 'source')
        _pin(plan_binding)
        _pin(ledger_pin)
        _pin(lock_pin)
        _need(_same(entry['retirement'], plan), 'plan')
        return _records(root, plan, entry)

    try:
        with storage._locked(registry) as ledger:
            ledger_pin = storage.binding(registry / 'ledger-v1.json')
            lock_pin = storage.binding(registry / 'admission.lock')
            entry = storage._entry(ledger, root)
            checked_root, identities = _preflight(plan, entry)
            _need(checked_root == root, 'root')
            conserved(entry, ledger_pin, lock_pin)
            result['phase'] = 'ownership'
            images = windows.WindowsImageSet(plan['remove'], deadline)
            result['cleanup_known'] = False
            try:
                result['phase'] = 'closure'
                process_rows = windows.closed_processes(identities, deadline)
                _need(type(process_rows) is list and len(process_rows) == len(identities) and
                      all(type(row) is dict and set(row) == {'identity', 'status'} and
                          _same(row['identity'], identity) and row['status'] in ('pid_absent', 'pid_reused', 'exited')
                          for row, identity in zip(process_rows, identities)), 'process')
                _need(_same(conserved(entry, ledger_pin, lock_pin), identities), 'identity')
                snapshots = images.snapshots
                _need(type(snapshots) is list and len(snapshots) == len(plan['remove']) and
                      all(type(row) is dict and set(row) == {'binding', 'identity'} and type(row['identity']) is dict
                          for row in snapshots) and
                      _same([row['binding'] for row in snapshots], plan['remove']), 'image_binding')
                images.verify()
                _write(output, output_identity, 'before-v1.json', dict(
                    version=1, scope='receipt-avd-retirement-before-v1', request=request,
                    processes=process_rows, images=snapshots, sources=sources))
                result['phase'] = 'mark'
                for index, item in enumerate(plan['remove'], 1):
                    conserved(entry, ledger_pin, lock_pin)
                    progress = dict(version=1, scope='receipt-avd-retirement-progress-v1', request=request,
                                    index=index, planned=item, phase='before_mark')
                    _write(output, output_identity, 'attempt-%02d-v1.json' % index, progress)
                    result['attempted_count'] = index
                    images.mark_delete(index - 1)
                    result['marked_count'] = index
                    _write(output, output_identity, 'marked-%02d-v1.json' % index,
                           dict(progress, phase='marked'))
            except BaseException as error:
                failures.append(dict(phase=result['phase'], reason=_reason(error), type=type(error).__name__))
                raise
            finally:
                closing_from_phase = result['phase']
                result['phase'] = 'cleanup'
                images.close()
                _need(images.closed is True, 'cleanup_unknown')
                result['cleanup_known'] = True
                result['phase'] = closing_from_phase
            conserved(entry, ledger_pin, lock_pin)
            _need(result['marked_count'] == len(plan['remove']), 'partial')
            _need(all(not Path(item['path']).exists() for item in plan['remove']), 'images_remain')
            result['phase'] = 'finalization'
            recording = True
            storage._record_retired_locked(root, plan, registry, ledger, entry)
            result['retirement_recorded'] = True
            result['phase'] = 'unlock'
        result.update(outcome='completed', phase='completed', reason='completed')
    except BaseException as error:
        if recording and result['retirement_recorded'] is not True:
            result['retirement_recorded'] = None
        if getattr(error, 'cleanup_known', True) is not True:
            result['cleanup_known'] = False
        failures.append(dict(phase=result['phase'], reason=_reason(error), type=type(error).__name__))
        result['reason'] = _reason(error)
    result['elapsed_ms'] = round((time.monotonic() - start) * 1000)
    if failures:
        _write(output, output_identity, 'failures-v1.json', dict(version=1, scope=SCOPE, failures=failures))
    _write(output, output_identity, 'result-v1.json', result)
    return copy.deepcopy(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--execute-reviewed-plan', action='store_true')
    args = parser.parse_args(argv)
    try:
        # No path binding, file or native access is allowed before explicit opt-in.
        _need(args.execute_reviewed_plan is True, 'not_authorized')
        binding = storage.binding(storage.safe_path(args.plan, exists=True))
        _need(binding['sha256'] == args.plan_sha256, 'binding')
        result = execute(binding, args.output, execute_reviewed_plan=True)
        print(storage.encoded(result).decode(), end='')
        return 0 if result['outcome'] == 'completed' else 1
    except (RetirementRefused, storage.StorageRefused, windows.RetirementWindowsError,
            OSError, ValueError, TypeError, KeyError):
        print('Retirement refused', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
