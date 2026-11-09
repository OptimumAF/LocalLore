"""Fixed SDK15 operation metadata. Import and validation perform no I/O.

Operator metadata records applicable human approval; it is not authentication
against a local administrator. Runtime owners retain their independent gates.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path, PureWindowsPath
import re

SOURCE = Path('D:/Worktrees/locallore-record-actions-tests-v1')
SOURCE_HEAD = '18809566af72530408e2e25007ee4d501e6bf12a'
OPERATOR_ROOT = Path('D:/Worktrees/LocalLore-record-query2-tests-v1')
OPERATOR = OPERATOR_ROOT/'scripts/run_library_ui_recovery.py'
BUILDER = OPERATOR_ROOT/'scripts/library_ui_run_inputs.py'
CONTRACT = OPERATOR_ROOT/'scripts/library_ui_recovery_contract.py'
OUT = Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-operator-v1')
LIVE = OUT/'live-operation-v1'
EXECUTION = OUT/'recovery-execution-v1'
AUTHORITY = OUT/'human-authority-v1.json'
PROPOSAL = OUT/'PROPOSED_OPERATION.md'
REGISTRY = Path('D:/Dev/_Migration/LocalLore-AVD-Storage')
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1')
RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-02-current-library-ui-run-v1')
CONTROLS = Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-ui-harness-v1/run-controls-v1')
RUN_PROPOSAL = LIVE/'run-proposal-v1.json'
RUN_AUTHORIZATION = LIVE/'run-authorization-v1.json'
RECOVERY_AUTHORIZATION = LIVE/'recovery-authorization-v1.json'
RECOVERY_RESULT = EXECUTION/'recovery-result-v1.json'
ATTEMPT = LIVE/'attempt-v1.json'
ADMISSION = RUNTIME/'admission-v1.json'
INPUT = CONTROLS/'run-input-v1.json'
HANDOFF = dict(path=str(Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-readiness-v1/frozen-inputs-v1/handoff-inputs-v1.json')),
    bytes=8214,sha256='b94367b9a70e194138a03528e6971c8be1e66d25551021f9140f1fb115a03475')
PLAN = dict(path=str(Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-readiness-v1/frozen-inputs-v1/recovery-plan-v1.json')),
    bytes=2609,sha256='0b4de12259218f1eb735eb366a4ff955b0f2cf6c6481c3143d90f96544a0afd2')
INITIAL_LEDGER_SHA256 = '4917ec696f7c9f9de5917838aafbd9c2d11184e17c8cbecd71f4eb66ae6a58c5'
AUTHORITY_SCOPE = 'sdk15-recovery-and-one-library-ui-run-v1'
MAX_SECONDS = 2400
AUTHORITY_KEYS = frozenset(('version','scope','source_head','operator_head','proposal','operator','builder',
    'contract','handoff','recovery_plan','allow_ledger_v2','allow_sdk_prepare','allow_one_boot',
    'accept_operator_observation','allow_model','approval_reference','max_operation_seconds'))
ATTEMPT_KEYS = frozenset(('version','scope','authority','handoff','recovery_plan','operator','builder','contract','no_retry'))


class OperationRefused(ValueError):
    """Fixed reason codes only; arbitrary diagnostics never become authority."""


def need(value, reason):
    if not value:
        raise OperationRefused(reason)


def same(left, right):
    return json.dumps(left,sort_keys=True,allow_nan=False) == json.dumps(right,sort_keys=True,allow_nan=False)


def binding(value, expected=None, maximum=2*1024**2):
    need(type(value) is dict and set(value)=={'path','bytes','sha256'}, 'binding')
    need(type(value['path']) is str and type(value['bytes']) is int and 0<value['bytes']<=maximum and
         type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None, 'binding')
    path = PureWindowsPath(value['path'])
    need(path.is_absolute() and path.drive.upper()=='D:' and value['path']==str(path), 'path')
    if expected is not None:
        need(path==PureWindowsPath(expected), 'path')


def validate_authority(value):
    need(type(value) is dict and set(value)==AUTHORITY_KEYS, 'authority')
    need(type(value['version']) is int and value['version']==1 and value['scope']==AUTHORITY_SCOPE and
         value['source_head']==SOURCE_HEAD and type(value['operator_head']) is str and
         re.fullmatch('[0-9a-f]{40}',value['operator_head']) is not None, 'authority')
    for flag in ('allow_ledger_v2','allow_sdk_prepare','allow_one_boot','accept_operator_observation'):
        need(value[flag] is True, 'authority')
    need(value['allow_model'] is False and type(value['max_operation_seconds']) is int and
         value['max_operation_seconds']==MAX_SECONDS, 'authority')
    reference=value['approval_reference']
    need(type(reference) is str and 0<len(reference)<=256 and not any(ord(c)<32 for c in reference), 'authority')
    for role,path in (('proposal',PROPOSAL),('operator',OPERATOR),('builder',BUILDER),('contract',CONTRACT),
                      ('handoff',HANDOFF['path']),('recovery_plan',PLAN['path'])):
        binding(value[role],path)
    need(same(value['handoff'],HANDOFF) and same(value['recovery_plan'],PLAN), 'authority')
    return copy.deepcopy(value)


def validate_attempt(value, authority_pin, authority):
    binding(authority_pin,AUTHORITY)
    authority=validate_authority(authority)
    need(type(value) is dict and set(value)==ATTEMPT_KEYS and type(value['version']) is int and
         value['version']==1 and value['scope']=='sdk15-recovery-operation-attempt-v1' and
         value['no_retry'] is True and same(value['authority'],authority_pin), 'attempt')
    for role in ('handoff','recovery_plan','operator','builder','contract'):
        need(same(value[role],authority[role]), 'attempt')
    return copy.deepcopy(value)
