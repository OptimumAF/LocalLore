"""Fixed file-only SDK16 preparation inspection; never execution authority.

Imports perform no I/O. Planning fingerprints installed tools and may use the
existing Windows profile lookup; it never launches SDK/ADB, prepares or boots a
guest, changes the shared ledger, retires images or creates an authorization.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
from types import SimpleNamespace

SOURCE = Path('D:/Worktrees/LocalLore-original-input-compose-review-v1')
SOURCE_HEAD = '80f2c10cceb7fb061bb0ab9ddfa50c7e17fd99f2'
OPERATOR = Path('D:/Worktrees/LocalLore-theme-archive-review-v1')
HELPER = OPERATOR / 'scripts/freeze_knowledge_ui_prepare_inputs.py'
OUT = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-prepare-inputs-v1')
OUTPUT = OUT / 'frozen-inputs-v1'
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1')
REGISTRY = Path('D:/Dev/_Migration/LocalLore-AVD-Storage')
SDK = Path('C:/Users/Avery/AppData/Local/Android/Sdk')
JAVA = Path('C:/Program Files/Java/jdk-21')
BUILD = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-build-v1/knowledge-ui-build-v1.json')
BUILD_PIN = dict(path=str(BUILD), bytes=8656,
                 sha256='97037d90a3b738a09054a07d03caf659cb2276774935d0b46535712b31d6f55c')
FILES = frozenset(('knowledge-build-v1.json', 'prepare-proposal-v1.json',
                   'capacity-preview-v1.json', 'handoff-inputs-v1.json', 'result-v1.json'))
MISSING = ('exact_retirement_prepare_and_boot_approval', 'pinned_storage_retirement',
           'fresh_prepare_authorization', 'guarded_prepare_result',
           'fresh_run_proposal_authorization_and_admission', 'fresh_ownership_resources_ports')
PROFILE = dict(memory_mib=8192, cores=4, api=35, max_run_seconds=1800)
_MODULES = None


class InspectionRefused(ValueError):
    """Fixed local reason code, never raw private diagnostic data."""


def _need(value, reason):
    if not value:
        raise InspectionRefused(reason)


def _git(root, head=None):
    _need(root.drive.upper() == 'D:' and root.resolve(strict=True) == root, 'source_path')
    for path in (root, *root.parents):
        _need(path.is_dir() and not path.is_symlink() and
              not getattr(path.lstat(), 'st_file_attributes', 0) & 1024, 'source_path')
    answers = []
    for args in (['rev-parse', 'HEAD'], ['status', '--porcelain', '--untracked-files=all']):
        result = subprocess.run(['git', '--no-optional-locks', '-C', str(root), *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
        _need(result.returncode == 0 and result.stderr == b'' and len(result.stdout) <= 131072, 'git')
        answers.append(result.stdout.replace(b'\r\n', b'\n'))
    _need(re.fullmatch(rb'[0-9a-f]{40}\n', answers[0]) is not None and answers[1] == b'', 'source')
    actual = answers[0].decode('ascii').strip()
    _need(head is None or actual == head, 'source')
    return actual


def _api():
    global _MODULES
    if _MODULES is None:
        sys.path.insert(0, str(SOURCE))
        from benchmarks import receipt_avd_environment as env
        from benchmarks import receipt_avd_storage as storage
        from benchmarks import owned_knowledge_ui_contract as contract
        from benchmarks import knowledge_ui_activation as activation
        from benchmarks import knowledge_ui_build as build
        from benchmarks import adb_held_socket_probe as probe
        # A cached transitive module from another checkout is not this frozen API.
        for name, module in tuple(sys.modules.items()):
            if name == 'benchmarks' or name.startswith('benchmarks.'):
                file = getattr(module, '__file__', None)
                if name == 'benchmarks' and file is None:
                    locations = list(getattr(module, '__path__', ()))
                    _need(locations == [str(SOURCE / 'benchmarks')] and
                          Path(locations[0]).resolve(strict=True) == SOURCE / 'benchmarks', 'module_source')
                else:
                    _need(file is not None and Path(file).resolve().parent == SOURCE / 'benchmarks', 'module_source')
        _MODULES = SimpleNamespace(env=env, storage=storage, contract=contract,
                                   activation=activation, build=build, probe=probe)
    return _MODULES


def _same(left, right):
    return _api().env.encoded(left) == _api().env.encoded(right)


def _read(pin):
    api = _api()
    api.env.check_binding(pin)
    value = api.env.read_json(pin['path'])
    api.env.check_binding(pin)
    return value


def _paths(fresh):
    api = _api()
    _need(Path.cwd() == SOURCE and Path(__file__) == HELPER and os.name == 'nt' and
          all(Path(os.environ.get(key, '')) == Path('D:/Dev/_Temp')
              for key in ('TEMP', 'TMP', 'TMPDIR')), 'environment')
    _need(api.storage.DEFAULT_REGISTRY == REGISTRY and api.activation.SOURCE_ROOT == SOURCE and
          Path(api.contract.GUEST_ROOT) == GUEST, 'fixed_paths')
    api.storage.safe_path(HELPER, exists=True)
    api.storage.safe_path(GUEST.parent, exists=True, directory=True)
    api.storage.safe_path(OUT, exists=True, directory=True)
    api.storage.safe_path(OUTPUT)
    _need(not os.path.lexists(GUEST), 'guest_exists')
    _need(not fresh or not os.path.lexists(OUTPUT), 'output_exists')
    _need(OUTPUT == OUT / 'frozen-inputs-v1' and GUEST not in OUTPUT.parents and
          OUTPUT not in GUEST.parents and REGISTRY not in OUTPUT.parents and
          OUTPUT not in REGISTRY.parents, 'output_path')


def _source_rows(rows):
    api = _api()
    _need(type(rows) is list, 'sources')
    names = set()
    for pin in rows:
        api.contract.binding(pin)
        path = PureWindowsPath(pin['path'])
        _need(path.parent == PureWindowsPath(SOURCE / 'benchmarks') and path.name not in names, 'sources')
        names.add(path.name)
    _need(names in (api.contract.SOURCE_NAMES, api.contract.SOURCE_NAMES | {'__init__.py'}), 'sources')
    _need(rows == sorted(rows, key=lambda p: p['path']), 'sources')


def _python(value):
    api = _api()
    _need(type(value) is dict and set(value) == {'executable', 'runtime_dll'}, 'python')
    api.contract.binding(value['executable'], project=False)
    if value['runtime_dll'] is not None:
        api.contract.binding(value['runtime_dll'], project=False)


def _capacity(value):
    api = _api()
    keys = {'version', 'scope', 'root', 'ledger', 'max_guests', 'budget_bytes', 'reservation_bytes',
            'active_count', 'charged_bytes', 'projected_bytes', 'root_limit_exceeded',
            'byte_limit_exceeded', 'would_fit', 'admission_granted'}
    _need(type(value) is dict and set(value) == keys, 'capacity')
    for key in ('version', 'max_guests', 'budget_bytes', 'reservation_bytes', 'active_count', 'charged_bytes', 'projected_bytes'):
        _need(type(value[key]) is int and value[key] >= 0, 'capacity')
    _need(value['version'] == 1 and value['scope'] == 'receipt-avd-prepare-capacity-preview-v1' and
          value['root'] == str(GUEST) and value['max_guests'] == 2 and
          value['budget_bytes'] == 64 * 1024**3 and value['reservation_bytes'] == 40 * 1024**3 and
          value['active_count'] <= 2 and value['projected_bytes'] == value['charged_bytes'] + value['reservation_bytes'], 'capacity')
    api.contract.binding(value['ledger'])
    _need(Path(value['ledger']['path']) == REGISTRY / 'ledger-v1.json', 'capacity')
    root_limit = value['active_count'] + 1 > value['max_guests']
    byte_limit = value['projected_bytes'] > value['budget_bytes']
    _need(value['root_limit_exceeded'] is root_limit and value['byte_limit_exceeded'] is byte_limit and
          value['would_fit'] is (not root_limit and not byte_limit) and value['admission_granted'] is False, 'capacity')


def validate_handoff(value):
    api = _api()
    keys = {'version', 'scope', 'source_root', 'source_head', 'operator_root', 'operator_head',
            'helper', 'guest', 'controls', 'runtime', 'sources', 'python', 'artifacts', 'build_copy',
            'prepare_proposal', 'capacity_preview', 'profile', 'execution_authorized',
            'model_material', 'missing_requirements'}
    _need(type(value) is dict and set(value) == keys and type(value['version']) is int and
          value['version'] == 1 and value['scope'] == 'sdk16-fresh-prepare-inspection-v1', 'handoff')
    _need(value['source_root'] == str(SOURCE) and value['source_head'] == SOURCE_HEAD and
          value['operator_root'] == str(OPERATOR) and type(value['operator_head']) is str and
          re.fullmatch(r'[0-9a-f]{40}', value['operator_head']) is not None and
          value['guest'] == str(GUEST) and value['controls'] == str(api.activation.CONTROLS) and
          value['runtime'] == str(api.activation.RUNTIME), 'handoff')
    _need(_same(value['profile'], PROFILE) and value['execution_authorized'] is False and
          value['model_material'] is False and type(value['missing_requirements']) is list and
          value['missing_requirements'] == list(MISSING), 'handoff')
    _source_rows(value['sources']); _python(value['python'])
    for key, path in (('helper', HELPER), ('build_copy', OUTPUT / 'knowledge-build-v1.json'),
                      ('prepare_proposal', OUTPUT / 'prepare-proposal-v1.json'),
                      ('capacity_preview', OUTPUT / 'capacity-preview-v1.json')):
        api.contract.binding(value[key])
        _need(Path(value[key]['path']) == path, 'handoff_path')
    _need(type(value['artifacts']) is dict and set(value['artifacts']) == {'build', 'product_apk', 'test_apk'}, 'artifacts')
    for pin in value['artifacts'].values():
        api.contract.binding(pin)
    _need(_same(value['artifacts']['build'], BUILD_PIN), 'artifacts')
    return value


def _plan(value):
    api = _api()
    api.env.validate_proposal(value, 'prepare')
    _need(value['paths']['root'] == str(GUEST) and value['sdk'] == str(SDK) and
          value['java_home'] == str(JAVA) and type(value['memory_mib']) is int and value['memory_mib'] == 8192 and
          type(value['cores']) is int and value['cores'] == 4 and
          value['allow_environment_calls'] is False and value['root_go_pending'] is True, 'profile')


def inspect():
    # Establish frozen source identity before importing any operational API.
    _git(SOURCE, SOURCE_HEAD)
    operator_head = _git(OPERATOR)
    api = _api()
    _paths(True)
    helper = api.env.binding(HELPER)
    sources = api.contract.source_bindings(); _source_rows(sources)
    python = api.probe._python_bindings(); _python(python)
    for pin in sources + [p for p in python.values() if p is not None]:
        api.env.check_binding(pin)
    api.env.check_binding(BUILD_PIN)
    manifest = api.build.create_manifest()
    artifacts = dict(build=copy.deepcopy(BUILD_PIN), **copy.deepcopy(manifest['artifacts']))
    _need(_same(api.build.verify_frozen_product(artifacts), manifest) and
          _same(manifest['instrumentations'], [list(row) for row in api.contract.INSTRUMENTATIONS]), 'build')
    before = api.storage.binding(REGISTRY / 'ledger-v1.json')
    capacity = api.storage.preview_prepare(GUEST); _capacity(capacity)
    _need(_same(capacity['ledger'], before), 'ledger')
    _paths(True)
    OUTPUT.mkdir()
    api.env.create_json(OUTPUT / 'knowledge-build-v1.json', manifest)
    proposal = api.env.plan_prepare(GUEST, SDK, JAVA, OUTPUT / 'prepare-proposal-v1.json',
                                    real_candidate=True, four_core_candidate=True)
    _plan(proposal)
    api.env.verify_installation(proposal)
    api.env.check_external_state(proposal)
    api.env.create_json(OUTPUT / 'capacity-preview-v1.json', capacity)
    value = dict(version=1, scope='sdk16-fresh-prepare-inspection-v1', source_root=str(SOURCE),
        source_head=SOURCE_HEAD, operator_root=str(OPERATOR), operator_head=operator_head,
        helper=helper, guest=str(GUEST), controls=str(api.activation.CONTROLS), runtime=str(api.activation.RUNTIME),
        sources=sources, python=python, artifacts=artifacts,
        build_copy=api.env.binding(OUTPUT / 'knowledge-build-v1.json'),
        prepare_proposal=api.env.binding(OUTPUT / 'prepare-proposal-v1.json'),
        capacity_preview=api.env.binding(OUTPUT / 'capacity-preview-v1.json'),
        profile=copy.deepcopy(PROFILE), execution_authorized=False, model_material=False,
        missing_requirements=list(MISSING))
    validate_handoff(value)
    api.env.create_json(OUTPUT / 'handoff-inputs-v1.json', value)
    handoff_pin = api.env.binding(OUTPUT / 'handoff-inputs-v1.json')
    _need({p.name for p in OUTPUT.iterdir()} == FILES - {'result-v1.json'}, 'output_roster')
    for pin in sources + [helper, before] + [p for p in python.values() if p is not None]:
        api.env.check_binding(pin)
    _need(_git(SOURCE, SOURCE_HEAD) == SOURCE_HEAD and _git(OPERATOR) == operator_head, 'source_changed')
    _need(_same(api.probe._python_bindings(), python) and
          _same(api.build.verify_frozen_product(artifacts), manifest), 'inputs_changed')
    _need(_same(_read(value['build_copy']), manifest) and _same(_read(value['prepare_proposal']), proposal) and
          _same(_read(value['capacity_preview']), capacity), 'output_changed')
    _need(_same(_read(handoff_pin), value), 'output_changed')
    _paths(False)
    result = dict(version=1, scope='sdk16-prepare-inspection-result-v1', passed=True,
        source_head=SOURCE_HEAD, operator_head=operator_head, helper=helper,
        handoff=handoff_pin, source_count=len(sources), method_count=4,
        capacity_would_fit=capacity['would_fit'], capacity_blocked=not capacity['would_fit'],
        execution_authorized=False, preparation_performed=False, guest_created=False,
        ledger_written=False, admission_created=False, target_executed=False,
        missing_requirements=list(MISSING))
    api.env.create_json(OUTPUT / 'result-v1.json', result)
    _need({p.name for p in OUTPUT.iterdir()} == FILES and
          _same(_read(api.env.binding(OUTPUT / 'result-v1.json')), result), 'result_copy')
    for pin in sources + [helper, before, BUILD_PIN, handoff_pin, value['build_copy'],
                         value['prepare_proposal'], value['capacity_preview']] + [p for p in python.values() if p is not None]:
        api.env.check_binding(pin)
    api.env.verify_installation(proposal)
    api.env.check_external_state(proposal)
    _need(_git(SOURCE, SOURCE_HEAD) == SOURCE_HEAD and _git(OPERATOR) == operator_head, 'source_changed')
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ['--help']:
        print('Fixed SDK16 file-only preparation inspection. No execution authority; no path/profile overrides.')
        return 0
    if argv:
        print(json.dumps(dict(passed=False, reason='arguments')))
        return 1
    try:
        result = inspect()
    except InspectionRefused as error:
        print(json.dumps(dict(passed=False, reason=str(error))))
        return 1
    except Exception:
        print(json.dumps(dict(passed=False, reason='inspection_refused')))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
