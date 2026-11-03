"""Fixed SDK18 file-only planning inputs; never prepare, boot or grant authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
from types import SimpleNamespace

OUT = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1')
ROOT = OUT / 'candidate-source-v1'
MODULE = ROOT / 'scripts/record_cancellation_ui_prepare_inputs.py'
OUTPUT = OUT / 'inspection-v1'
SOURCE = OUT / 'frozen-profile-source-v1'
SOURCE_HEAD = 'dbcafb0070734cbccbd420a159f6305bc6f9090d'
SOURCE_TREE = '53c47a25b00f2ca868150f76d408c3789a6fcc3c'
SOURCE_PUBLICATION = {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-03-record-refusal-freeze-v1\\profile-source-publication-v1.json', 'bytes': 755007, 'sha256': 'aa58a83cd42933165f659b454d768b3b6c4cbc4458efabf300704e09fd50de31'}
STATIC = dict(path=str(Path('D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/frozen-inputs-v3/static-installed-inputs-v1.json')),
    bytes=3678, sha256='d2ca3f1ef02ed01169b84bb62090f663aca610db159e8db97606d1e1becccf99')
BUILD = dict(path=str(Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-build-v1/record-cancellation-ui-build-v1.json')),
    bytes=32140, sha256='4d39b74ad5aee455ce9060c01d760204022101e4b6b8ce58d12f666450d2894e')
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-v1/avd-v1')
RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-runtime-v1')
CONTROLS = OUT / 'run-controls-v1'
REGISTRY = Path('D:/Dev/_Migration/LocalLore-AVD-Storage')
SDK = Path('C:/Users/Avery/AppData/Local/Android/Sdk')
JAVA = Path('C:/Program Files/Java/jdk-21')
PROFILE = dict(memory_mib=8192, cores=4, api=35, max_run_seconds=1800)
_SOURCE_FILE_COUNT = 2671
MAX_SOURCE_FILE = 16 * 1024**2
MAX_SOURCE_BYTES = 64 * 1024**2
MAX_INSTALLED_FILES = 2048
MAX_INSTALLED_BYTES = 6 * 1024**3
_MODULES = None


class PrepareInputsRefused(ValueError):
    """Fixed local categories; no private exception text is returned."""


def need(condition, reason):
    if not condition: raise PrepareInputsRefused(reason)


def same(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def _physical(path, *, directory=False):
    need(path.is_absolute() and path.resolve(strict=True) == path, 'path')
    for node in (path, *path.parents):
        need(not node.is_symlink() and not getattr(node.lstat(), 'st_file_attributes', 0) & 1024, 'path')
    need(path.is_dir() if directory else path.is_file() and path.stat().st_nlink == 1, 'path')


def _source_bytes(path, maximum):
    _physical(path)
    before = path.stat()
    need(before.st_size <= maximum, 'budget')
    with path.open('rb') as stream: raw = stream.read(before.st_size + 1)
    _physical(path)
    after = path.stat()
    need(len(raw) == before.st_size and (before.st_size, before.st_mtime_ns, before.st_ino) ==
         (after.st_size, after.st_mtime_ns, after.st_ino), 'changed')
    return raw


def _raw(pin):
    need(type(pin) is dict and set(pin) == {'path', 'bytes', 'sha256'}, 'binding')
    need(type(pin['path']) is str and type(pin['bytes']) is int and 0 < pin['bytes'] <= 2 * 1024**2 and
         type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}', pin['sha256']), 'binding')
    path = Path(pin['path'])
    need(path.drive.upper() == 'D:' and str(path) == pin['path'], 'path')
    raw = _source_bytes(path, 2 * 1024**2)
    need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'binding')
    return raw


def _decode(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'json'); value[key] = item
        return value
    def invalid(_): raise PrepareInputsRefused('json')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid)


def validate_catalog(value):
    need(type(value) is dict and set(value) == {'final_commit', 'final_tree', 'files', 'normal_preserved', 'shared_ledger_sha256'}, 'catalog')
    need(value['final_commit'] == SOURCE_HEAD and value['final_tree'] == SOURCE_TREE and
         type(value['normal_preserved']) is dict and type(value['shared_ledger_sha256']) is str, 'catalog')
    rows = value['files']
    need(type(rows) is list and len(rows) == _SOURCE_FILE_COUNT, 'catalog')
    names = []; total = 0
    for row in rows:
        need(type(row) is dict and set(row) == {'path', 'mode', 'git_blob', 'bytes', 'sha256'}, 'catalog')
        name = row['path']
        need(type(name) is str and name and str(PurePosixPath(name)) == name and
             not PurePosixPath(name).is_absolute() and ':' not in name and '\\' not in name and
             all(part not in ('', '.', '..') for part in PurePosixPath(name).parts) and
             not any(ord(c) < 32 for c in name), 'path')
        need(row['mode'] in ('100644', '100755') and type(row['bytes']) is int and
             0 <= row['bytes'] <= MAX_SOURCE_FILE and type(row['git_blob']) is str and
             re.fullmatch('[0-9a-f]{40}', row['git_blob']) and type(row['sha256']) is str and
             re.fullmatch('[0-9a-f]{64}', row['sha256']), 'catalog')
        names.append(name); total += row['bytes']
    need(names == sorted(names) and len(set(n.casefold() for n in names)) == len(names) and total <= MAX_SOURCE_BYTES, 'catalog')
    return copy.deepcopy(value)


def _verify_catalog(value, root, read, names):
    """Private memory-port seam; public entry points use only fixed sealed data."""
    value = validate_catalog(value)
    need(set(names) == {r['path'] for r in value['files']} and len(names) == len(value['files']), 'source_set')
    for row in value['files']:
        raw = read(root / row['path'], MAX_SOURCE_FILE)
        need(type(raw) is bytes and len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'] and
             hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == row['git_blob'], 'source')
    return value


def _walk(root):
    _physical(root, directory=True)
    files = []; directories = []; pending = [root]; count = 0
    while pending:
        parent = pending.pop()
        with os.scandir(parent) as entries:
            for entry in entries:
                count += 1; need(count <= 4096, 'budget')
                path = Path(entry.path)
                need(not entry.is_symlink() and path.resolve(strict=True) == path and
                     not getattr(path.lstat(), 'st_file_attributes', 0) & 1024, 'path')
                if entry.is_dir(follow_symlinks=False):
                    directories.append(path.relative_to(root).as_posix()); pending.append(path)
                else: files.append(path.relative_to(root).as_posix())
    return files, directories


def source_snapshot():
    raw = _raw(SOURCE_PUBLICATION); catalog = validate_catalog(_decode(raw))
    names, directories = _walk(SOURCE)
    expected_dirs = {p.as_posix() for r in catalog['files'] for p in PurePosixPath(r['path']).parents if p != PurePosixPath('.')}
    need(set(directories) == expected_dirs and len(directories) == len(expected_dirs), 'source_set')
    result = _verify_catalog(catalog, SOURCE, _source_bytes, names)
    need(_raw(SOURCE_PUBLICATION) == raw, 'changed')
    return result


def _parts():
    global _MODULES
    if _MODULES is None:
        need(Path(__file__) == MODULE, 'operator')
        sys.path.insert(0, str(SOURCE))
        from benchmarks import receipt_avd_environment as env
        from benchmarks import receipt_avd_storage as storage
        from benchmarks import owned_record_cancellation_ui_contract as contract
        from benchmarks import record_cancellation_ui_activation as activation
        from benchmarks import record_cancellation_ui_build as build
        from benchmarks import record_cancellation_ui_profile_build as profile_build
        from benchmarks import adb_held_socket_probe as probe
        for name, module in tuple(sys.modules.items()):
            if name == 'benchmarks' or name.startswith('benchmarks.'):
                file = getattr(module, '__file__', None)
                if name == 'benchmarks' and file is None:
                    need(list(module.__path__) == [str(SOURCE / 'benchmarks')], 'source')
                else: need(file is not None and Path(file).resolve().parent == SOURCE / 'benchmarks', 'source')
        need(storage.DEFAULT_REGISTRY == REGISTRY and Path(contract.GUEST_ROOT) == GUEST and
             contract.CLIENT_VERSION == 18 and contract.MODEL_MATERIAL is False and
             activation.SOURCE_ROOT == SOURCE and activation.RUNTIME == RUNTIME and activation.CONTROLS == CONTROLS, 'profile')
        _MODULES = SimpleNamespace(env=env, storage=storage, contract=contract, activation=activation,
            build=build, profile_build=profile_build, probe=probe)
    need(list(sys.modules['benchmarks'].__path__) == [str(SOURCE / 'benchmarks')], 'source')
    for module in vars(_MODULES).values():
        need(Path(module.__file__).resolve().parent == SOURCE / 'benchmarks', 'source')
    original_path = list(sys.path)
    try: _MODULES.activation._source()
    finally: sys.path[:] = original_path
    need(list(sys.modules['benchmarks'].__path__) == [str(SOURCE / 'benchmarks')], 'source')
    return _MODULES


def _installed_files(api):
    files = api.env.installation_files(SDK, JAVA)
    need(type(files) is list and 0 < len(files) <= MAX_INSTALLED_FILES and len(set(files)) == len(files), 'installed')
    total = 0
    for path in files:
        path = api.env.safe_path(path)
        size = path.stat().st_size
        need(type(size) is int and size >= 0, 'installed')
        total += size
        need(total <= MAX_INSTALLED_BYTES, 'budget')
    return files, total


def _static(api, python):
    need(type(python) is dict and set(python) == {'executable', 'runtime_dll'}, 'installed')
    value = _decode(_raw(STATIC))
    need(type(value) is dict and set(value) == {'adb', 'tools', 'python', 'capabilities', 'source_review',
        'compatibility', 'emulator', 'qemu', 'refuser', 'refuser_source', 'auth_key_path'}, 'installed')
    need(type(value['tools']) is list and 0 < len(value['tools']) <= 32 and same(value['python'], python), 'installed')
    key = value['auth_key_path']
    need(type(key) is str and PureWindowsPath(key).is_absolute() and not any(ord(c) < 32 for c in key), 'path')
    # ADB key is path metadata only: never stat/open/hash/copy its contents.
    for role in ('adb', 'capabilities', 'source_review', 'compatibility', 'emulator', 'qemu', 'refuser', 'refuser_source'):
        api.env.check_binding(value[role])
    for pin in value['tools'] + [p for p in python.values() if p is not None]: api.env.check_binding(pin)
    current = api.env.binding(SOURCE / 'benchmarks/native/deny_adb_client.c')
    need(all(current[k] == value['refuser_source'][k] for k in ('bytes', 'sha256')), 'source')


def _inspect(api, catalog, output):
    """Private synthetic-port seam, never a CLI-selected factory or output root."""
    validate_catalog(catalog)
    need(not any(os.path.lexists(p) for p in (GUEST, RUNTIME, CONTROLS, output)), 'exists')
    _physical(output.parent, directory=True); need(output.drive.upper() == 'D:', 'path')
    _physical(GUEST.parent, directory=True)
    ledger_before = api.env.binding(REGISTRY / 'ledger-v1.json')
    sources = api.contract.source_bindings(); need(len(sources) == 28, 'source')
    python = api.probe._python_bindings(); _static(api, python)
    saved = _decode(_raw(BUILD))
    manifest = api.build.verify_frozen_product(dict(saved['artifacts'], build=BUILD))
    need(same(saved, manifest), 'build'); api.profile_build.project_manifest(manifest)
    files, installed_bytes = _installed_files(api)
    capacity = api.storage.preview_prepare(GUEST)
    need(type(capacity) is dict and capacity.get('admission_granted') is False, 'capacity')
    output.mkdir()
    prepare_path = output / 'prepare-proposal-v1.json'
    proposal = api.env.plan_prepare(GUEST, SDK, JAVA, prepare_path, real_candidate=True, four_core_candidate=True)
    api.env.validate_proposal(proposal, 'prepare')
    need(proposal['paths']['root'] == str(GUEST) and type(proposal['memory_mib']) is int and proposal['memory_mib'] == 8192 and
         type(proposal['cores']) is int and proposal['cores'] == 4 and proposal['allow_environment_calls'] is False and proposal['root_go_pending'] is True, 'profile')
    need(len(proposal['bindings']) == len(files) and {p['path'] for p in proposal['bindings']} == {str(p) for p in files} and
         sum(p['bytes'] for p in proposal['bindings']) == installed_bytes, 'installed')
    api.env.verify_installation(proposal); api.env.check_external_state(proposal)
    need(same(capacity, api.storage.preview_prepare(GUEST)) and same(ledger_before, api.env.binding(REGISTRY / 'ledger-v1.json')), 'changed')
    api.env.create_json(output / 'capacity-preview-v1.json', capacity)
    h = dict(version=1, scope='sdk18-fresh-inputs-v1', source_root=str(SOURCE), source_head=SOURCE_HEAD,
        source_tree=SOURCE_TREE, guest=str(GUEST), controls=str(CONTROLS), runtime=str(RUNTIME),
        sources=sources, python=python, artifacts=dict(manifest['artifacts'], build=BUILD),
        prepare_proposal=api.env.binding(prepare_path), capacity_preview=api.env.binding(output / 'capacity-preview-v1.json'),
        profile=PROFILE, execution_authorized=False, model_material=False)
    source_snapshot(); api.activation._source()
    # Later source observations must not hide a changed planning snapshot.
    # This remains an unlocked observation; guarded admission rechecks separately.
    need(same(ledger_before, api.env.binding(REGISTRY / 'ledger-v1.json')) and
         same(capacity, api.storage.preview_prepare(GUEST)), 'changed')
    api.env.create_json(output / 'frozen-inputs-v1.json', h)
    result = dict(version=1, scope='sdk18-prepare-input-inspection-v1',
        handoff=api.env.binding(output / 'frozen-inputs-v1.json'), prepare=h['prepare_proposal'], capacity=h['capacity_preview'],
        source_files=_SOURCE_FILE_COUNT, benchmark_sources=28, installed_files=len(files), installed_bytes_per_pass=installed_bytes,
        installed_hash_passes=2, execution_authorized=False, sdk_dispatched=False, model_material=False)
    api.env.create_json(output / 'inspection-result-v1.json', result)
    return result


def inspect_fixed():
    catalog = source_snapshot()
    return _inspect(_parts(), catalog, OUTPUT)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args != ['inspect']: return 2
    try:
        print(json.dumps(inspect_fixed(), sort_keys=True, allow_nan=False)); return 0
    except Exception:
        print('SDK18 preparation inputs refused', file=sys.stderr); return 1


if __name__ == '__main__': raise SystemExit(main())
