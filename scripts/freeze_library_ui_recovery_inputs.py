"""Fixed SDK15 file-only recovery inspection, never an execution authority.

No import performs I/O. This tool writes inspection records only. Preparation,
ledger migration, resource/process observations, ADB and boot are separate.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from types import SimpleNamespace

SOURCE = Path('D:/Worktrees/locallore-record-actions-tests-v1')
SOURCE_HEAD = '18809566af72530408e2e25007ee4d501e6bf12a'
OUT = Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-readiness-v1')
OUTPUT = OUT / 'frozen-inputs-v1'
REGISTRY = Path('D:/Dev/_Migration/LocalLore-AVD-Storage')
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1')
LEDGER_SHA256 = '4917ec696f7c9f9de5917838aafbd9c2d11184e17c8cbecd71f4eb66ae6a58c5'
FAILURE = dict(path='D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-capacity-v1/approved-operation-v1/prepare-observed-failure-v1.json',
    bytes=2171,sha256='e21cf804358ba01c8f10c5b9a426da749b32cbc9c6c4920751e93ca8a1571505')
STATIC = dict(path='D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/frozen-inputs-v3/static-installed-inputs-v1.json',
    bytes=3678,sha256='d2ca3f1ef02ed01169b84bb62090f663aca610db159e8db97606d1e1becccf99')
BUILD = dict(path='D:/Dev/Experiments/LocalLore/2026-11-02-library-ui-harness-v1/library-ui-build-v1.json',
    bytes=30730,sha256='496f6358a860c2f5ff8809610d0d2f83e93dd867fbfdfe5e6c4c551871058ad3')
FILES = frozenset(('b80-byte-attestation-v1.json','recovery-plan-v1.json',
    'static-installed-inputs-v1.json','handoff-inputs-v1.json','result-v1.json'))
PENDING = ('human_exact_scope_authority','actual_recovery_and_known_cleanup',
    'fresh_prepare_and_run_proposal_bindings','fresh_run_authorization',
    'fresh_admission_and_activation_input','fresh_storage_resources_ports_and_native_ownership')
_MODULES = None


class InspectionRefused(ValueError):
    """Only fixed reason codes escape; no private diagnostic or key payload."""


def _need(value, reason):
    if not value:
        raise InspectionRefused(reason)


def _git():
    # Check the exact operational checkout before importing its code. Git's
    # optional lock/index refresh is disabled; these are file-only queries.
    _need(SOURCE.drive.upper() == 'D:' and SOURCE.resolve(strict=True) == SOURCE, 'source_path')
    for path in (SOURCE, *SOURCE.parents):
        _need(path.is_dir() and not path.is_symlink() and
              not getattr(path.lstat(),'st_file_attributes',0) & 1024, 'source_path')
    answers = []
    for args in (['rev-parse','HEAD'],['status','--porcelain','--untracked-files=all']):
        result = subprocess.run(['git','--no-optional-locks','-C',str(SOURCE),*args],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,
            env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
        _need(result.returncode == 0 and result.stderr == b'' and len(result.stdout) <= 131072, 'git')
        answers.append(result.stdout.replace(b'\r\n',b'\n'))
    _need(answers == [(SOURCE_HEAD+'\n').encode('ascii'),b''], 'source')


def _api():
    global _MODULES
    if _MODULES is None:
        sys.path.insert(0,str(SOURCE))
        from benchmarks import receipt_avd_environment as env
        from benchmarks import receipt_avd_storage as storage
        from benchmarks import receipt_avd_prepare_recovery as recovery
        from benchmarks import owned_library_ui_contract as contract
        from benchmarks import library_ui_activation as activation
        from benchmarks import library_ui_build as build
        modules = dict(env=env,storage=storage,recovery=recovery,contract=contract,activation=activation,build=build)
        for module in modules.values():
            _need(Path(module.__file__).resolve().parent == SOURCE/'benchmarks', 'module_source')
        _MODULES = SimpleNamespace(**modules)
    return _MODULES


def _same(left, right):
    return _api().env.encoded(left) == _api().env.encoded(right)


def _read(pin):
    api = _api()
    api.env.check_binding(pin)
    value = api.env.read_json(pin['path'])
    api.env.check_binding(pin)
    return value


def _static():
    api = _api()
    value = _read(STATIC)
    _need(type(value) is dict and set(value) == {'adb','tools','python','capabilities','source_review',
        'compatibility','emulator','qemu','refuser','refuser_source','auth_key_path'}, 'installed_inputs')
    _need(type(value['tools']) is list and 0 < len(value['tools']) <= 32 and type(value['python']) is dict,
          'installed_inputs')
    key = value['auth_key_path']
    _need(type(key) is str and PureWindowsPath(key).is_absolute() and
          not any(c in key for c in ('\0','\n','\r')), 'key_path')
    # A credential PATH is metadata only: never stat/open/hash/copy its bytes.
    pins = [value[k] for k in ('adb','capabilities','source_review','compatibility','emulator',
                              'qemu','refuser','refuser_source')]
    pins += value['tools'] + [p for p in value['python'].values() if p is not None]
    for pin in pins:
        api.env.check_binding(pin)
    value = copy.deepcopy(value)
    value['refuser_source'] = api.env.binding(SOURCE/'benchmarks/native/deny_adb_client.c')
    api.env.check_binding(value['refuser_source'])
    return value, pins


def _inputs():
    api = _api()
    _need(api.storage.DEFAULT_REGISTRY == REGISTRY and api.activation.SOURCE_ROOT == SOURCE and
          Path(api.contract.GUEST_ROOT) == GUEST, 'fixed_paths')
    _need(api.contract.CLIENT_VERSION == 15 and api.contract.MODEL_MATERIAL is False and
          len(api.contract.INSTRUMENTATIONS) == 4 and api.contract.ARTIFACT_KEYS == {'build','product_apk','test_apk'},
          'profile')
    sources = api.contract.source_bindings()
    _need(len(sources) == 25 and len({Path(p['path']).name for p in sources}) == 25 and
          all(Path(p['path']).parent == SOURCE/'benchmarks' for p in sources) and
          'prepare_recovery_contract.py' in {Path(p['path']).name for p in sources}, 'source_closure')
    for pin in sources:
        api.env.check_binding(pin)
    ledger = api.env.binding(REGISTRY/'ledger-v1.json')
    _need(ledger['bytes'] == 41230 and ledger['sha256'] == LEDGER_SHA256, 'ledger')
    _need(not os.path.lexists(GUEST) and not os.path.lexists(GUEST.parent), 'guest_exists')
    _need(not os.path.lexists(api.activation.CONTROLS) and not os.path.lexists(api.activation.RUNTIME), 'run_exists')
    _read(FAILURE)
    return sources, ledger


def inspect():
    """Create only a fixed five-file inspection set; no authorization or dispatch."""
    _need(Path.cwd() == SOURCE and all(Path(os.environ.get(k,'')) == Path('D:/Dev/_Temp')
          for k in ('TEMP','TMP','TMPDIR')), 'environment')
    _git()
    api = _api()
    sources, ledger = _inputs()
    helper = api.env.binding(Path(__file__))
    installed, installed_pins = _static()
    artifacts = dict(build=copy.deepcopy(BUILD), **copy.deepcopy(api.build._FIXED['apks']))
    manifest = api.build.verify_frozen_product(artifacts)
    _need(_same(manifest['roster'],[list(row) for row in api.contract.INSTRUMENTATIONS]), 'roster')
    api.env.safe_path(OUT,exists=True,directory=True)
    _need(OUTPUT == OUT/'frozen-inputs-v1' and not os.path.lexists(OUTPUT), 'output_exists')
    api.env.safe_path(OUTPUT,exists=False)
    OUTPUT.mkdir()
    api.env.create_json(OUTPUT/'b80-byte-attestation-v1.json',manifest)
    plan = api.recovery.plan(GUEST,Path(FAILURE['path']),OUTPUT/'recovery-plan-v1.json')
    _need(_same(plan['sources'],api.recovery._sources()) and len(plan['sources']) == 7 and
          all(Path(p['path']).parent == SOURCE/'benchmarks' for p in plan['sources']), 'recovery_sources')
    for pin in plan['sources']:
        api.env.check_binding(pin)
    api.env.create_json(OUTPUT/'static-installed-inputs-v1.json',installed)
    blueprint = dict(version=1,scope='sdk15-recovery-inspection-inputs-v1',source_root=str(SOURCE),head=SOURCE_HEAD,
        helper=helper,sources=sources,activation=api.env.binding(api.activation.HELPER),
        controls=str(api.activation.CONTROLS),runtime=str(api.activation.RUNTIME),guest=str(GUEST),
        artifacts=artifacts,static_inputs=api.env.binding(OUTPUT/'static-installed-inputs-v1.json'),
        recovery_plan=api.env.binding(OUTPUT/'recovery-plan-v1.json'),fixed_roster=[list(row) for row in api.contract.INSTRUMENTATIONS],
        method_count=4,ready_for_execution=False,approval_inferred=False,pending=list(PENDING),
        original_observation_acceptance_required=True,no_historical_process_closure_claim=True,
        limits=dict(memory_mib=8192,cores=4,guest_seconds=1800,owner_seconds=1700,parent_seconds=1730,
            controller_seconds=1200,caller_seconds=1230,ready_seconds=400,private_adb_port=15937,console_port=5592,guest_adb_port=5593))
    api.env.create_json(OUTPUT/'handoff-inputs-v1.json',blueprint)
    # Planning does not reserve a state snapshot. Revalidate before claiming a
    # completed inspection; partial files are retained and never auto-retried.
    _git()
    after_sources, after_ledger = _inputs()
    _need(_same(sources,after_sources) and _same(ledger,after_ledger), 'inputs_changed')
    for pin in installed_pins + list(artifacts.values()) + [helper,blueprint['activation']]:
        api.env.check_binding(pin)
    _need(_same(api.env.binding(SOURCE/'benchmarks/native/deny_adb_client.c'),installed['refuser_source']), 'inputs_changed')
    _need({p.name for p in OUTPUT.iterdir()} == FILES-{'result-v1.json'}, 'output_roster')
    result = dict(version=1,scope='sdk15-recovery-inspection-result-v1',status='completed-file-only',
        head=SOURCE_HEAD,helper=helper,source_count=25,recovery_source_count=7,method_count=4,
        ledger_before=ledger,ledger_after=after_ledger,ledger_unchanged=True,
        handoff=api.env.binding(OUTPUT/'handoff-inputs-v1.json'),recovery_plan=blueprint['recovery_plan'],
        ready_for_execution=False,approval_inferred=False,recovery_executed=False,authority_created=False,
        guest_parent_created=False,admission_created=False,activation_input_created=False,
        resource_or_process_observation=False,sdk_or_adb_executed=False)
    api.env.create_json(OUTPUT/'result-v1.json',result)
    _need({p.name for p in OUTPUT.iterdir()} == FILES, 'output_roster')
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args != ['inspect']:
        return 1
    try:
        value = inspect()
    except Exception as error:
        # Keep a useful fixed refusal without exposing arbitrary exception text.
        # Partial records remain unready; never retry into their directory.
        print(json.dumps(dict(scope='sdk15-recovery-inspection-result-v1',status='refused',
            ready_for_execution=False,failure_type=type(error).__name__,
            reason=str(error) if type(error) is InspectionRefused else 'inspection_failed')))
        return 1
    print(_api().env.encoded(value).decode('utf-8'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
