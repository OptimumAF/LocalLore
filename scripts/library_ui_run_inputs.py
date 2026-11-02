"""Create fixed SDK15 run inputs only after verified, authorized recovery.

No import performs I/O. No server/guest/SDK dispatch or ledger transition is
implemented here. Normal planning retains its Windows profile-path lookup and
console-token/default-AVD metadata checks. Credential bytes are never copied.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from types import SimpleNamespace
import uuid

ROOT = Path(__file__).parents[1]
_MODULES = None


def _rules():
    sys.path.insert(0,str(ROOT))
    from scripts import library_ui_recovery_contract as rules
    rules.need(Path(rules.__file__).resolve()==ROOT/'scripts/library_ui_recovery_contract.py', 'contract_source')
    return rules


def _git(root, head):
    r = _rules()
    r.need(root.drive.upper()=='D:' and root.resolve(strict=True)==root, 'source_path')
    for args,wanted in ((['rev-parse','HEAD'],(head+'\n').encode()),
                        (['status','--porcelain','--untracked-files=all'],b'')):
        reply=subprocess.run(['git','--no-optional-locks','-C',str(root),*args],stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=15,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
        r.need(reply.returncode==0 and reply.stderr==b'' and reply.stdout.replace(b'\r\n',b'\n')==wanted, 'source')


def _api():
    global _MODULES
    if _MODULES is None:
        r=_rules();_git(r.SOURCE,r.SOURCE_HEAD);sys.path.insert(0,str(r.SOURCE))
        from benchmarks import receipt_avd_environment as env
        from benchmarks import receipt_avd_storage as storage
        from benchmarks import receipt_avd_prepare_recovery as recovery
        from benchmarks import prepare_recovery_contract as history
        from benchmarks import owned_library_ui_contract as contract
        from benchmarks import library_ui_activation as activation
        from benchmarks import library_ui_build as build
        from benchmarks import isolated_adb_lease as base
        modules=dict(env=env,storage=storage,recovery=recovery,history=history,contract=contract,
                     activation=activation,build=build,base=base)
        for module in modules.values():
            r.need(Path(module.__file__).resolve().parent==r.SOURCE/'benchmarks', 'module_source')
        r.need(storage.DEFAULT_REGISTRY==r.REGISTRY and activation.SOURCE_ROOT==r.SOURCE and
               activation.RUNTIME==r.RUNTIME and activation.CONTROLS==r.CONTROLS and
               Path(contract.GUEST_ROOT)==r.GUEST and contract.CLIENT_VERSION==15 and
               contract.MODEL_MATERIAL is False, 'profile')
        _MODULES=SimpleNamespace(**modules)
    return _MODULES


def read(pin, expected=None, maximum=2*1024**2):
    r=_rules();r.binding(pin,expected,maximum);api=_api();api.env.check_binding(pin)
    result=api.env.read_json(pin['path'],maximum);api.env.check_binding(pin)
    return result


def save(path, value):
    api=_api();api.env.create_json(path,value);pin=api.env.binding(path)
    _rules().need(_rules().same(read(pin,path),value), 'publication')
    return pin


def read_authority(pin):
    r=_rules();authority=r.validate_authority(read(pin,r.AUTHORITY,16384));api=_api()
    _git(r.SOURCE,r.SOURCE_HEAD);_git(r.OPERATOR_ROOT,authority['operator_head'])
    for role in ('proposal','operator','builder','contract','handoff','recovery_plan'):
        api.env.check_binding(authority[role])
    return authority


def frozen_inputs(authority_pin):
    r=_rules();api=_api();authority=read_authority(authority_pin)
    h=read(r.HANDOFF);plan=read(r.PLAN)
    r.need(type(h['version']) is int and h['version']==1 and h['scope']=='sdk15-recovery-inspection-inputs-v1' and
           h['source_root']==str(r.SOURCE) and h['head']==r.SOURCE_HEAD and h['ready_for_execution'] is False and
           h['approval_inferred'] is False and h['method_count']==4 and
           r.same(h['fixed_roster'],[list(row) for row in api.contract.INSTRUMENTATIONS]) and
           r.same(h['recovery_plan'],r.PLAN) and h['guest']==str(r.GUEST) and
           h['controls']==str(r.CONTROLS) and h['runtime']==str(r.RUNTIME), 'handoff')
    r.need(r.same(h['sources'],api.contract.source_bindings()) and len(h['sources'])==25 and
           any(Path(p['path']).name=='prepare_recovery_contract.py' for p in h['sources']), 'source_closure')
    api.history.validate_plan(plan)
    r.need(r.same(plan['sources'],api.recovery._sources()) and len(plan['sources'])==7 and
           plan['root']==str(r.GUEST) and plan['registry']==str(r.REGISTRY), 'plan')
    for pin in h['sources']+[h['helper'],h['activation']]:api.env.check_binding(pin)
    r.need(r.same(h['activation'],api.env.binding(api.activation.HELPER)) and
           any(r.same(h['activation'],pin) for pin in h['sources']), 'activation_source')
    installed=read(h['static_inputs'])
    for key in ('adb','capabilities','source_review','compatibility','emulator','qemu','refuser','refuser_source'):
        api.env.check_binding(installed[key])
    for pin in installed['tools']+[p for p in installed['python'].values() if p is not None]:api.env.check_binding(pin)
    r.need(type(installed['auth_key_path']) is str, 'key_path')
    r.need(r.same(installed['refuser_source'],api.env.binding(r.SOURCE/'benchmarks/native/deny_adb_client.c')), 'refuser_source')
    api.build.verify_frozen_product(h['artifacts'])
    return authority,h,installed


def recovered(authority_pin, recovery_authorization, recovery_result):
    r=_rules();api=_api();authority=read_authority(authority_pin)
    attempt=read(api.env.binding(r.ATTEMPT),r.ATTEMPT)
    r.validate_attempt(attempt,authority_pin,authority)
    auth=read(recovery_authorization,r.RECOVERY_AUTHORIZATION,4096)
    api.history.validate_authorization(auth,r.PLAN)
    terminal=read(recovery_result,r.RECOVERY_RESULT)
    before=api.env.binding(r.REGISTRY/'ledger-v1.json');ledger=read(before)
    api.storage._validate(ledger,r.REGISTRY)
    entry=api.storage._entry(ledger,r.GUEST)
    r.need(type(ledger['version']) is int and ledger['version']==2 and entry['state']=='prepared' and
           entry['reserved_bytes']==40*1024**3 and entry['closure'] is None and entry['recovery'] is not None, 'recovered_state')
    reference=entry['recovery']
    r.need(r.same(reference['outcome'],recovery_result) and reference['completion'] is not None and
           terminal['status']=='completed' and terminal['fence_cleanup_known'] is True and
           terminal['sdk_cleanup_known'] is True and r.same(terminal['intent'],reference['intent']), 'recovery_cleanup')
    api.history.validate_history(entry,r.REGISTRY);api.history.require_cleanup(entry)
    intent=read(reference['intent']);complete=read(reference['completion'],r.EXECUTION/'recovery-rebind-v1.json')
    r.need(r.same(intent['plan'],r.PLAN) and r.same(intent['authorization'],recovery_authorization) and
           r.same(complete['intent'],reference['intent']) and
           complete['proposal']['path']==str(r.EXECUTION/'prepare-proposal-v1.json') and
           complete['authorization']['path']==str(r.EXECUTION/'prepare-authorization-v1.json') and
           complete['marker']['path']==str(r.GUEST/'prepare-recovery-intent-v1.json') and
           terminal['prepare_result']['path']==str(r.GUEST/'prepare-result-v1.json') and
           terminal['proposal_sha256']==entry['proposal_sha256']==complete['proposal']['sha256'], 'recovery_join')
    api.env.check_binding(before)
    return before,complete


def create_inputs(authority_pin, recovery_authorization, recovery_result):
    """One post-recovery metadata transaction; never retains or boots the guest."""
    r=_rules();api=_api();authority,h,installed=frozen_inputs(authority_pin)
    ledger,complete=recovered(authority_pin,recovery_authorization,recovery_result)
    for path in (r.RUNTIME,r.CONTROLS,r.RUN_PROPOSAL,r.RUN_AUTHORIZATION):
        r.need(not os.path.lexists(path), 'already_used')
    r.need(not os.path.lexists(r.GUEST/api.contract.BOOT_CLAIM_FILE), 'already_used')
    # The public planner retains all existing profile/console-token/default-AVD,
    # source and prepared-image checks. It never transitions the shared ledger.
    proposal=api.env.plan_run(complete['proposal']['path'],r.GUEST/'prepared-v1.json',r.RUN_PROPOSAL,max_seconds=1800)
    proposal_pin=api.env.binding(r.RUN_PROPOSAL)
    r.need(r.same(read(proposal_pin),proposal), 'run_proposal')
    run_auth=dict(version=1,phase='run',proposal_sha256=proposal_pin['sha256'],
                  allow_environment_calls=True,root_go_pending=False)
    run_auth_pin=save(r.RUN_AUTHORIZATION,run_auth)
    r.need(r.same(api.env.authorize(r.RUN_PROPOSAL,r.RUN_AUTHORIZATION,'run'),proposal), 'run_authorization')
    run_id=uuid.uuid4().hex
    server=dict(version=1,protocol=api.base.PROTOCOL,run_id=run_id,root=str(r.RUNTIME/'owned-v1/server'),
        port=15937,seconds=1700,adb=installed['adb'],tools=installed['tools'],sdk_version=api.base.SDK_VERSION,
        expected_version='0029',sources=[p for p in h['sources'] if PureWindowsPath(p['path']).name in api.base.SOURCE_NAMES|{'__init__.py'}],
        python=installed['python'],auth_key=installed['auth_key_path'],capabilities=installed['capabilities'],source_review=installed['source_review'])
    guest=dict(root=str(r.GUEST),proposal=proposal_pin,authorization=run_auth_pin,emulator=installed['emulator'],
        qemu=installed['qemu'],refuser=installed['refuser'],refuser_source=installed['refuser_source'],
        console_port=5592,adb_port=5593,serial='emulator-5592',memory_mib=8192,cores=4,max_seconds=1800,api=35,abi='x86_64')
    admission=dict(version=1,protocol=api.contract.PROTOCOL,run_id=run_id,root=str(r.RUNTIME/'owned-v1'),seconds=1700,
        server=server,guest=guest,artifacts=copy.deepcopy(h['artifacts']),sources=copy.deepcopy(h['sources']),
        python=copy.deepcopy(installed['python']),compatibility=installed['compatibility'])
    api.contract.validate_admission(admission);api.contract.revalidate_inputs(admission);api.build.verify_current(admission)
    for folder in (r.RUNTIME,r.CONTROLS):
        api.env.safe_path(folder,exists=False);folder.mkdir()
    admission_pin=save(r.ADMISSION,admission)
    # Activation input is published last, after complete run/admission validation.
    input_pin=save(r.INPUT,dict(version=1,scope='library-ui-run-input-v1',admission=admission_pin,helper=h['activation']))
    again,_=recovered(authority_pin,recovery_authorization,recovery_result)
    r.need(r.same(ledger,again), 'ledger_changed')
    frozen_inputs(authority_pin)
    for pin in (authority_pin,recovery_authorization,recovery_result,proposal_pin,run_auth_pin,admission_pin,input_pin):api.env.check_binding(pin)
    return dict(version=1,scope='sdk15-post-recovery-inputs-v1',authority=authority_pin,
        recovery_authorization=recovery_authorization,recovery_result=recovery_result,ledger_before=ledger,
        run_proposal=proposal_pin,run_authorization=run_auth_pin,admission=admission_pin,input=input_pin)
