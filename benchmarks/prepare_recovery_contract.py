"""File-only recovery history checks; no process, SDK or import-time I/O.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
from pathlib import Path
from benchmarks import receipt_avd_storage as storage

ACTION = 'recover_failed_root_mkdir_once'
# Reviewed historical reserve -> exclusive mkdir -> SDK order. Not arbitrary code.
LEGACY_MKDIR_SOURCES = frozenset((
    '2b732297aa1915441f3692be9922761957bb3cf5da4037aed1becd44a23aff9b',
    '102ce63378d5468e2a0a311ad5cd073ae643b4db990c42e37f145972c1f860b1',
))
ENTRY_KEYS = {'root','proposal_sha256','state','reserved_bytes','closure','retirement','retirement_receipt'}
PLAN_KEYS = {'version','action','root','registry','prior_entry','failure','prior_proposal',
             'legacy_source','sources','parent_mode','evidence_kind'}
SOURCE_NAMES = frozenset(('receipt_avd_environment.py','receipt_avd_storage.py','runtime_spike.py',
                         'host_commit_capacity.py','prepare_recovery_contract.py',
                         'receipt_avd_prepare_recovery.py','prepare_recovery_windows.py'))


def need(value, reason):
    storage.require(value, 'recovery_' + reason)


def claim_path(registry, root):
    key = hashlib.sha256(str(Path(root)).casefold().encode('utf-8')).hexdigest()
    return Path(registry) / ('prepare-recovery-' + key + '.json')


def old_entry(value):
    need(type(value) is dict and set(value) in (ENTRY_KEYS, ENTRY_KEYS | {'recovery'}), 'entry')
    need(value.get('recovery') is None and value['state'] == 'preparing' and
         type(value['reserved_bytes']) is int and value['reserved_bytes'] == storage.RESERVATION_BYTES and
         all(value[k] is None for k in ('closure','retirement','retirement_receipt')), 'entry')
    return {k: value[k] for k in ENTRY_KEYS}


def validate_plan(value):
    need(type(value) is dict and set(value) == PLAN_KEYS and type(value['version']) is int and
         value['version'] == 1 and value['action'] == ACTION and
         value['evidence_kind'] == 'operator_observed_mkdir_failure_not_process_closure' and
         value['parent_mode'] in ('existing','create_one'), 'plan')
    root = storage.safe_path(value['root'])
    registry = storage.safe_path(value['registry'], exists=True, directory=True)
    need(not storage._contains(root, registry) and not storage._contains(registry, root), 'overlap')
    entry = old_entry(value['prior_entry'])
    need(entry['root'] == str(root), 'entry')
    for role in ('failure','prior_proposal','legacy_source'):
        storage.check_binding(value[role])
        need(not storage._contains(root, Path(value[role]['path'])), 'evidence_inside_guest')
    failure = storage.read_json(value['failure']['path'])
    need(failure.get('version') == 1 and type(failure.get('version')) is int and
         failure.get('scope') == 'sdk14-prepare-observed-failure-v1' and
         failure.get('status') == 'failed-spent-no-retry' and
         failure.get('exception_type') == 'FileNotFoundError' and
         type(failure.get('winerror')) is int and failure['winerror'] == 3 and
         type(failure.get('site')) is str and
         failure['site'].startswith('receipt_avd_environment.prepare:') and
         failure['site'].endswith(' root.mkdir()') and
         failure.get('sdk_worker_reached') is False and failure.get('guest_root_exists') is False and
         failure.get('proposal') == value['prior_proposal'] and
         old_entry(failure.get('entry')) == entry and
         type(failure.get('provenance')) is str and failure['provenance'], 'failure_stage')
    storage.check_binding(failure.get('operator'))
    prior = storage.read_json(value['prior_proposal']['path'])
    need(value['prior_proposal']['sha256'] == entry['proposal_sha256'] and
         prior.get('phase') == 'prepare' and prior.get('paths',{}).get('root') == str(root) and
         type(prior.get('memory_mib')) is int and prior['memory_mib'] == 8192 and
         type(prior.get('cores')) is int and prior['cores'] == 4 and
         type(prior.get('host_available_memory_min')) is int and
         prior['host_available_memory_min'] == 12 * storage.GIB, 'prior_proposal')
    legacy = value['legacy_source']
    need(Path(legacy['path']).name == 'receipt_avd_environment.py' and
         legacy['sha256'] in LEGACY_MKDIR_SOURCES and legacy in prior.get('bindings',[]), 'legacy_source')
    sources = value['sources']
    need(type(sources) is list and len(sources) == len(SOURCE_NAMES) and
         {Path(p['path']).name for p in sources} == SOURCE_NAMES and
         len({str(Path(p['path']).parent) for p in sources}) == 1, 'sources')
    for source in sources:
        storage.check_binding(source)
    return prior


def validate_authorization(value, plan_binding):
    need(value == dict(version=1, action=ACTION, plan_sha256=plan_binding['sha256'],
                       allow_sdk_prepare=True, accept_operator_observation=True) and
         type(value.get('version')) is int and value.get('allow_sdk_prepare') is True and
         value.get('accept_operator_observation') is True, 'authorization')


def validate_history(entry, registry):
    """Required ledger-v2 pointer: deleting a claim cannot make it optional."""
    reference = entry['recovery']
    need(type(reference) is dict and set(reference) == {'intent','completion','outcome'}, 'history')
    storage.check_binding(reference['intent'])
    need(reference['intent']['path'] == str(claim_path(registry, entry['root'])), 'history_path')
    intent = storage.read_json(reference['intent']['path'])
    need(type(intent) is dict and set(intent) == {'version','action','root','plan','authorization','owner'} and
         type(intent['version']) is int and intent['version'] == 1 and
         intent['action'] == ACTION and intent['root'] == entry['root'], 'intent')
    storage.check_binding(intent['plan']); storage.check_binding(intent['authorization'])
    plan = storage.read_json(intent['plan']['path'])
    validate_plan(plan)
    need(plan['root'] == entry['root'] and plan['registry'] == str(registry), 'history_path')
    validate_authorization(storage.read_json(intent['authorization']['path']), intent['plan'])
    owner = intent['owner']
    need(type(owner) is dict and set(owner) == {'pid','creation_filetime','executable'} and
         type(owner['pid']) is int and owner['pid'] > 0 and
         type(owner['creation_filetime']) is int and owner['creation_filetime'] > 0 and
         type(owner['executable']) is str and owner['executable'], 'owner')
    completion = reference['completion']
    if completion is None:
        need(entry['proposal_sha256'] == plan['prior_entry']['proposal_sha256'] and
             entry['state'] == 'preparing' and entry['reserved_bytes'] == storage.RESERVATION_BYTES,
             'incomplete_claim')
    else:
        storage.check_binding(completion)
        complete = storage.read_json(completion['path'])
        need(type(complete) is dict and set(complete) == {'version','intent','proposal','authorization','marker'} and
             type(complete['version']) is int and complete['version'] == 1 and
             complete['intent'] == reference['intent'], 'completion')
        for key in ('proposal','authorization','marker'):
            storage.check_binding(complete[key])
        prepare_auth = storage.read_json(complete['authorization']['path'])
        need(prepare_auth == dict(version=1, phase='prepare', proposal_sha256=complete['proposal']['sha256'],
                                  allow_environment_calls=True, root_go_pending=False) and
             type(prepare_auth.get('version')) is int and prepare_auth.get('allow_environment_calls') is True and
             prepare_auth.get('root_go_pending') is False, 'prepare_authorization')
        proposal = storage.read_json(complete['proposal']['path'])
        need((entry['state'] not in ('preparing','prepared') or
              complete['proposal']['sha256'] == entry['proposal_sha256']) and
             proposal.get('phase') == 'prepare' and
             proposal.get('paths',{}).get('root') == entry['root'] and
             complete['marker']['path'] == str(Path(entry['root']) / 'prepare-recovery-intent-v1.json') and
             storage.read_json(complete['marker']['path']) == {'intent':reference['intent']}, 'completion')
    outcome = reference['outcome']
    if outcome is not None:
        storage.check_binding(outcome)
        terminal = storage.read_json(outcome['path'])
        need(type(terminal) is dict and set(terminal) == {'version','intent','proposal_sha256',
             'prepare_result','status','fence_cleanup_known','sdk_cleanup_known'} and
             type(terminal['version']) is int and terminal['version'] == 1 and
             terminal['intent'] == reference['intent'] and
             terminal['proposal_sha256'] == (complete['proposal']['sha256'] if completion is not None
                                              else entry['proposal_sha256']) and
             terminal['status'] in ('completed','refused') and
             type(terminal['fence_cleanup_known']) is bool and type(terminal['sdk_cleanup_known']) is bool,
             'outcome')
        if terminal['prepare_result'] is not None:
            storage.check_binding(terminal['prepare_result'])
        if terminal['status'] == 'completed':
            need(completion is not None and terminal['fence_cleanup_known'] is True and
                 terminal['sdk_cleanup_known'] is True and terminal['prepare_result'] is not None,
                 'outcome')
    if entry['state'] in ('retained','closed','retired'):
        require_cleanup(entry)


def require_cleanup(entry):
    if entry.get('recovery') is None:
        return
    reference = entry['recovery']
    need(reference['outcome'] is not None, 'cleanup_unknown')
    storage.check_binding(reference['outcome'])
    terminal = storage.read_json(reference['outcome']['path'])
    need(terminal.get('status') == 'completed' and terminal.get('fence_cleanup_known') is True and
         terminal.get('sdk_cleanup_known') is True, 'cleanup_unknown')
    storage.check_binding(terminal['prepare_result'])
    result = storage.read_json(terminal['prepare_result']['path'])
    need(result.get('status') == 'completed' and result.get('prepared_created') is True and
         result.get('closure_verified') is True and result.get('child_cleanup_complete') is True and
         result.get('proposal_sha256') == terminal['proposal_sha256'], 'cleanup_unknown')


def history_paths(entry):
    """Exact required records, never a recursive SDK/source-directory charge."""
    reference = entry.get('recovery')
    if reference is None:
        return []
    intent = storage.read_json(reference['intent']['path'])
    plan = storage.read_json(intent['plan']['path'])
    failure = storage.read_json(plan['failure']['path'])
    pins = [reference['intent'], intent['plan'], intent['authorization'], plan['failure'],
            plan['prior_proposal'], plan['legacy_source'], failure['operator']] + plan['sources']
    if reference['completion'] is not None:
        pins.append(reference['completion'])
        complete = storage.read_json(reference['completion']['path'])
        pins.extend((complete['proposal'], complete['authorization'], complete['marker']))
    if reference['outcome'] is not None:
        pins.append(reference['outcome'])
        terminal = storage.read_json(reference['outcome']['path'])
        if terminal['prepare_result'] is not None:
            pins.append(terminal['prepare_result'])
    return [Path(pin['path']) for pin in pins]
