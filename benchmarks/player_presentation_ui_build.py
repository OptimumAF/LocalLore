"""SDK8 launcher admission over the exact, separately frozen B41 product build.

Import performs no file, Git, native, credential or target operation. There is no
caller-selected product path, verifier, source root, protocol conversion or fallback.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import stat
import subprocess

LAUNCH_ROOT = Path(__file__).parents[1]
PRODUCT_ROOT = Path('D:/Worktrees/LocalLore-record-ui-host-v1')
PRODUCT_HEAD = '42ae8f6b7df7373696d35c9a294b6d0517c8886c'
PRODUCT_BUILD_PATH = Path('D:/Dev/Experiments/LocalLore/2026-10-31-player-presentation-v2/record-ui-build-v2.json')
PRODUCT_BUILD_SHA256 = 'a8543cd5c421e69d386f0e4b36f9280e771ae1813e09011eae91e562e5135c60'
FROZEN_VERIFIER_SHA256 = '6aa95e53312b8f371d4150e004eae9450694c5c7d6661fa9abc0a66bbfe43a0b'
PRODUCT_ARTIFACTS = {
    'build': {'path': str(PRODUCT_BUILD_PATH), 'bytes': 16946, 'sha256': PRODUCT_BUILD_SHA256},
    'product_apk': {'path': str(PRODUCT_ROOT / 'apps/android/app/build-archive-verification/outputs/apk/debug/app-debug.apk'),
                    'bytes': 27838412, 'sha256': 'ffa33dca97ec97d1e3f09df96f0a79ff057c2c583c4276add4358c122c8eb92e'},
    'test_apk': {'path': str(PRODUCT_ROOT / 'apps/android/app/build-archive-verification/outputs/apk/androidTest/debug/app-debug-androidTest.apk'),
                 'bytes': 2263192, 'sha256': 'bf7c7b9e50a773dea68a8de3807b176e3b239192a70bbda10fbed77e0464dc53'},
}
# Actual lazy project imports of the frozen whole validator, including their
# project import dependencies. They must execute unchanged bytes in W2.
SHARED_CONSUMERS = (
    ('benchmarks.owned_record_ui_contract', 'benchmarks/owned_record_ui_contract.py'),
    ('benchmarks.owned_ui_contract', 'benchmarks/owned_ui_contract.py'),
    ('benchmarks.owned_target_contract', 'benchmarks/owned_target_contract.py'),
    ('benchmarks.isolated_adb_lease', 'benchmarks/isolated_adb_lease.py'),
    ('benchmarks.receipt_avd_environment', 'benchmarks/receipt_avd_environment.py'),
    ('benchmarks.receipt_avd_storage', 'benchmarks/receipt_avd_storage.py'),
    ('benchmarks.runtime_spike', 'benchmarks/runtime_spike.py'),
    ('benchmarks.host_commit_capacity', 'benchmarks/host_commit_capacity.py'),
    ('benchmarks.android_instrumentation_evidence', 'benchmarks/android_instrumentation_evidence.py'),
    ('scripts.audit_physical_model_apk', 'scripts/audit_physical_model_apk.py'),
    ('audit_apk', 'scripts/audit_apk.py'),
)


class BuildRefused(ValueError):
    """Fixed refusal category, without private artifact data."""


def _need(value, reason='build'):
    if not value:
        raise BuildRefused(reason)


def _ordinary(path, directory=False):
    _need(path.is_absolute() and path.drive.upper() == 'D:', 'path')
    for parent in [path, *path.parents]:
        info = parent.lstat()
        _need(not getattr(info, 'st_file_attributes', 0) & 1024 and not stat.S_ISLNK(info.st_mode), 'path')
        _need(parent == path or stat.S_ISDIR(info.st_mode), 'path')
    _need(path.resolve(strict=True) == path, 'path')
    info = path.lstat()
    _need(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'path')
    return info


def _pin(path, cap=64 * 1024 * 1024):
    before = _ordinary(path)
    _need(0 <= before.st_size <= cap, 'size')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    after = _ordinary(path)
    _need((before.st_size, before.st_mtime_ns, before.st_ino, before.st_nlink) ==
          (after.st_size, after.st_mtime_ns, after.st_ino, after.st_nlink), 'changed')
    return {'path': str(path), 'bytes': after.st_size, 'sha256': digest.hexdigest()}


def _product_head():
    _ordinary(PRODUCT_ROOT, directory=True)
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    answers = [subprocess.run(['git', '-C', str(PRODUCT_ROOT)] + arguments,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15, env=environment)
               for arguments in (['rev-parse', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'])]
    _need(all(answer.returncode == 0 and answer.stderr == b'' for answer in answers), 'source')
    _need(answers[0].stdout.strip().decode('ascii') == PRODUCT_HEAD and answers[1].stdout == b'', 'source')


def _shared_consumers():
    _ordinary(LAUNCH_ROOT, directory=True)
    _need(LAUNCH_ROOT != PRODUCT_ROOT, 'source')
    pins = {}
    for name, relative in SHARED_CONSUMERS:
        product = _pin(PRODUCT_ROOT / relative)
        launch = _pin(LAUNCH_ROOT / relative)
        _need(all(product[key] == launch[key] for key in ('bytes', 'sha256')), 'shared_source')
        module = importlib.import_module(name)
        _need(Path(module.__file__) == LAUNCH_ROOT / relative, 'shared_module')
        pins[relative] = {'product': product, 'launcher': launch}
    for relative in ('benchmarks/__init__.py', 'scripts/__init__.py'):
        first, second = PRODUCT_ROOT / relative, LAUNCH_ROOT / relative
        _need(first.exists() == second.exists(), 'shared_source')
        if first.exists():
            left, right = _pin(first), _pin(second)
            _need(all(left[key] == right[key] for key in ('bytes', 'sha256')), 'shared_source')
            pins[relative] = {'product': left, 'launcher': right}
    return pins


def _load_verified_product():
    """The fixed file's own __file__ supplies W1 ROOT; no module globals change."""
    _product_head()
    path = PRODUCT_ROOT / 'benchmarks/record_ui_build.py'
    before = _pin(path)
    _need(before['sha256'] == FROZEN_VERIFIER_SHA256, 'verifier_source')
    shared = _shared_consumers()
    specification = importlib.util.spec_from_file_location('_locallore_product_42ae_record_ui_build', path)
    _need(specification is not None and specification.loader is not None, 'verifier_source')
    module = importlib.util.module_from_spec(specification)
    with path.open('rb') as stream:
        raw = stream.read(before['bytes'] + 1)
    _need(len(raw) == before['bytes'] and hashlib.sha256(raw).hexdigest() == FROZEN_VERIFIER_SHA256 and
          _pin(path) == before, 'verifier_source')
    # Execute the exact verified source, never a SourceFileLoader-selected pyc.
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    _need(module.ROOT == PRODUCT_ROOT and _pin(path) == before and _shared_consumers() == shared, 'source')
    return module


def _artifact_identity(artifacts):
    _need(type(artifacts) is dict and set(artifacts) == set(PRODUCT_ARTIFACTS), 'artifacts')
    _need(all(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'} and
              type(value['bytes']) is int for value in artifacts.values()), 'artifacts')
    _need(artifacts == PRODUCT_ARTIFACTS, 'product_binding')


def verify_frozen_product(artifacts):
    """Artifacts-only pre-prepare guard; it grants no target or launch authority."""
    try:
        _artifact_identity(artifacts)
        for value in artifacts.values():
            _need(_pin(Path(value['path'])) == value, 'product_binding')
        shared = _shared_consumers()
        frozen = _load_verified_product()
        # This is an artifact-only argument adapter to the unchanged function,
        # which reads only ['artifacts']; it is never presented as an admission.
        value = frozen.verify_current({'artifacts': copy.deepcopy(artifacts)})
        _need(value['head'] == PRODUCT_HEAD and _shared_consumers() == shared, 'source')
        _product_head()
        for artifact in artifacts.values():
            _need(_pin(Path(artifact['path'])) == artifact, 'product_binding')
        return copy.deepcopy(value)
    except BuildRefused:
        raise
    except Exception:
        raise BuildRefused('product') from None


def verify_current(admission):
    from benchmarks import owned_player_presentation_ui_contract as contract
    value = contract.validate_admission(admission)
    _artifact_identity(value['artifacts'])
    # Launcher authority remains the new SDK8 profile and its own source/runtime
    # bindings; an old product head never becomes a new launcher identity.
    contract.revalidate_inputs(value)
    manifest = verify_frozen_product(value['artifacts'])
    contract.revalidate_inputs(value)
    return manifest
