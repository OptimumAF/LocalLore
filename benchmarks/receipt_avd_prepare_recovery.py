"""Explicit, one-use recovery of an observed pre-SDK exclusive-mkdir failure.

No import performs I/O. Planning is a snapshot, never process closure. Execution
retains the same root/count/40 GiB and has no boot, deletion or retry operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path

from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import prepare_recovery_contract as contract
from benchmarks.prepare_recovery_windows import DirectoryFence


def _sources():
    folder = Path(__file__).resolve().parent
    return [storage.binding(folder / name) for name in sorted(contract.SOURCE_NAMES)]


def _absent(root):
    storage.safe_path(root)
    contract.need(not os.path.lexists(str(root)), 'root_exists')


def _entry_snapshot(registry, root):
    # Planning does not initialize the registry or create its lock. Execution
    # rechecks the exact entry under the shared lock before any recovery intent.
    pin = storage.binding(registry / 'ledger-v1.json')
    ledger = storage.read_json(pin['path'])
    storage._validate(ledger, registry)
    entry = copy.deepcopy(storage._entry(ledger, root))
    storage.check_binding(pin)
    return entry


def plan(root, failure_path, output, registry=storage.DEFAULT_REGISTRY):
    root = storage.safe_path(root)
    registry = storage.safe_path(registry, exists=True, directory=True)
    output = storage.safe_path(output)
    contract.need(not storage._contains(root, output) and
                  not storage._contains(registry, output), 'output_overlap')
    _absent(root)
    entry = _entry_snapshot(registry, root)
    contract.old_entry(entry)
    contract.need(not contract.claim_path(registry, root).exists(), 'spent')
    parent_exists = root.parent.exists()
    storage.safe_path(root.parent if parent_exists else root.parent.parent, exists=True, directory=True)
    failure = storage.read_json(failure_path)
    prior_pin = failure.get('proposal')
    storage.check_binding(prior_pin)
    prior = storage.read_json(prior_pin['path'])
    candidates = [p for p in prior.get('bindings',[]) if
                  Path(p.get('path','')).name == 'receipt_avd_environment.py']
    contract.need(len(candidates) == 1, 'legacy_source')
    value = dict(version=1, action=contract.ACTION, root=str(root), registry=str(registry),
                 prior_entry=entry, failure=storage.binding(failure_path), prior_proposal=prior_pin,
                 legacy_source=candidates[0], sources=_sources(),
                 parent_mode='existing' if parent_exists else 'create_one',
                 evidence_kind='operator_observed_mkdir_failure_not_process_closure')
    contract.validate_plan(value)
    # Recheck after evidence hashing; never present this as fresh SDK readiness.
    contract.need(_entry_snapshot(registry, root) == entry, 'entry_changed')
    _absent(root)
    env.create_json(output, value)
    return value


def _publish_intent(ledger, registry, entry, plan_pin, auth_pin, owner):
    intent = dict(version=1, action=contract.ACTION, root=entry['root'],
                  plan=plan_pin, authorization=auth_pin, owner=owner)
    path = contract.claim_path(registry, entry['root'])
    # This deterministic, create-only record remains spent even if the guest is
    # removed or publication of its ledger link fails. Never rollback/delete it.
    env.create_json(path, intent)
    if ledger['version'] == 1:
        ledger['version'] = 2
        for item in ledger['entries']:
            item['recovery'] = None
    reference = dict(intent=storage.binding(path), completion=None, outcome=None)
    entry['recovery'] = reference
    storage._validate(ledger, registry)
    storage._atomic_write(registry / 'ledger-v1.json', ledger)
    return reference


def _rebind(registry, root, reference, proposal_pin, authorization_pin, marker_pin, output):
    completion_path = output / 'recovery-rebind-v1.json'
    env.create_json(completion_path, dict(version=1, intent=reference['intent'],
                                         proposal=proposal_pin, authorization=authorization_pin, marker=marker_pin))
    with storage._locked(registry) as ledger:
        entry = storage._entry(ledger, root)
        contract.need(entry['recovery'] == reference and entry['state'] == 'preparing', 'entry_changed')
        entry['proposal_sha256'] = proposal_pin['sha256']
        entry['recovery']['completion'] = storage.binding(completion_path)
        storage._validate(ledger, registry)
        storage._atomic_write(registry / 'ledger-v1.json', ledger)


def _record_outcome(registry, root, intent_pin, terminal, terminal_path):
    with storage._locked(registry) as ledger:
        entry = storage._entry(ledger, root)
        contract.need(entry.get('recovery',{}).get('intent') == intent_pin and
                      entry['recovery']['outcome'] is None, 'entry_changed')
        # A proposal may have been generated before rebind failed. History owns
        # which digest was actually installed, never the caller's pending value.
        completion = entry['recovery']['completion']
        terminal['proposal_sha256'] = (storage.read_json(completion['path'])['proposal']['sha256']
                                      if completion is not None else entry['proposal_sha256'])
        env.create_json(terminal_path, terminal)
        entry['recovery']['outcome'] = storage.binding(terminal_path)
        storage._validate(ledger, registry)
        storage._atomic_write(registry / 'ledger-v1.json', ledger)
        return terminal


def execute(plan_path, authorization_path, output, registry=storage.DEFAULT_REGISTRY):
    """Perform one explicitly authorized preparation, never a guest boot.

    A refusal before intent leaves the ledger unchanged. Once intent is forced,
    every interruption is spent and charged; no cleanup deletes records or roots.
    """
    registry = storage.safe_path(registry, exists=True, directory=True)
    plan_pin, auth_pin = storage.binding(plan_path), storage.binding(authorization_path)
    value = storage.read_json(plan_path)
    prior = contract.validate_plan(value)
    contract.validate_authorization(storage.read_json(authorization_path), plan_pin)
    contract.need(value['registry'] == str(registry) and value['sources'] == _sources(), 'sources')
    root = storage.safe_path(value['root'])
    _absent(root)
    output = storage.safe_path(output)
    contract.need(not output.exists() and not storage._contains(root, output) and
                  not storage._contains(output, root) and not storage._contains(registry, output) and
                  not storage._contains(output, registry), 'output_overlap')
    storage.safe_path(output.parent, exists=True, directory=True)
    facts = env.resource_facts(prior)
    owner = env.process_identity(os.getpid())
    fence = DirectoryFence()
    reference = None
    proposal_pin = None
    failure = None
    fence_known = False
    sdk_known = False
    try:
        # Protect the existing path chain before creating any parent or guest.
        fence.hold(root.parent if value['parent_mode'] == 'existing' else root.parent.parent)
        with storage._locked(registry) as ledger:
            entry = storage._entry(ledger, root)
            contract.need(entry == value['prior_entry'], 'entry_changed')
            contract.old_entry(entry)
            contract.validate_plan(value)
            storage.check_binding(plan_pin); storage.check_binding(auth_pin)
            _absent(root)
            contract.need(root.parent.exists() == (value['parent_mode'] == 'existing'), 'parent_changed')
            contract.need(not contract.claim_path(registry, root).exists(), 'spent')
            # Reobserve resources at the dispatch boundary, without changing any floor.
            facts = env.resource_facts(prior)
            output.mkdir()
            reference = _publish_intent(ledger, registry, entry, plan_pin, auth_pin, owner)
            if value['parent_mode'] == 'create_one':
                fence.create(root.parent)
            fence.create(root)  # Atomic no-overwrite creation AND held native handle.
            env.create_json(root / 'prepare-recovery-intent-v1.json', {'intent':reference['intent']})
        fence.verify()
        proposal_path = output / 'prepare-proposal-v1.json'
        proposal = env._prepare_proposal_value(root, prior['sdk'], prior['java_home'],
                                               real_candidate=True, four_core_candidate=True)
        env.validate_proposal(proposal, 'prepare')
        env.create_json(proposal_path, proposal)
        proposal_pin = storage.binding(proposal_path)
        auth_path = output / 'prepare-authorization-v1.json'
        env.create_json(auth_path, dict(version=1, phase='prepare', proposal_sha256=proposal_pin['sha256'],
                                       allow_environment_calls=True, root_go_pending=False))
        actual = env.authorize(proposal_path, auth_path, 'prepare')
        contract.need(actual == proposal, 'proposal_changed')
        fence.verify()
        _rebind(registry, root, reference, proposal_pin, storage.binding(auth_path),
                storage.binding(root / 'prepare-recovery-intent-v1.json'), output)
        env._prepare_admitted(proposal, proposal_path, auth_path, proposal_pin['sha256'], facts,
                               registry=registry)
        fence.verify()
        contract.validate_plan(value)
        result = env.read_json(root / 'prepare-result-v1.json')
        sdk_known = (result.get('status') == 'completed' and result.get('prepared_created') is True and
                     result.get('closure_verified') is True and result.get('child_cleanup_complete') is True)
        contract.need(sdk_known, 'sdk_cleanup_unknown')
    except BaseException as error:
        failure = error
    finally:
        try:
            fence_known = fence.close() is True
        except BaseException as error:
            if failure is None:
                failure = error
        if not fence_known and failure is None:
            failure = storage.StorageRefused('recovery_fence_cleanup_unknown')
    if reference is not None:
        result_path = root / 'prepare-result-v1.json'
        terminal = dict(version=1, intent=reference['intent'],
                        proposal_sha256=proposal_pin['sha256'] if proposal_pin is not None
                        else value['prior_entry']['proposal_sha256'],
                        prepare_result=storage.binding(result_path) if result_path.is_file() else None,
                        status='completed' if failure is None else 'refused',
                        fence_cleanup_known=fence_known, sdk_cleanup_known=sdk_known)
        terminal_path = output / 'recovery-result-v1.json'
        terminal = _record_outcome(registry, root, reference['intent'], terminal, terminal_path)
    if failure is not None:
        raise failure
    return terminal
