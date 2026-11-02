"""Fixed SDK16 fresh-operation metadata; import/validation perform no I/O.

Approval records describe reviewed human authority, not authentication against
a local administrator. No validator grants storage, preparation or boot.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path, PureWindowsPath
import re

SOURCE = Path('D:/Worktrees/LocalLore-original-input-compose-review-v1')
SOURCE_HEAD = '80f2c10cceb7fb061bb0ab9ddfa50c7e17fd99f2'
INSPECTOR_ROOT = Path('D:/Worktrees/LocalLore-theme-archive-review-v1')
INSPECTOR_HEAD = 'e7328a966a81720d5b0731fd33cd0f4acf8bf9a7'
OPERATOR_ROOT = Path('D:/Dev/Repositories/LocalLore')
OPERATOR = OPERATOR_ROOT/'scripts/run_knowledge_ui_fresh.py'
CONTRACT = OPERATOR_ROOT/'scripts/knowledge_ui_fresh_contract.py'
OUT = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-bridge-v1')
LIVE = OUT/'live-operation-v1'
PROPOSAL = OUT/'PROPOSED_OPERATION.md'
AUTHORITY = OUT/'human-authority-v1.json'
ATTEMPT = LIVE/'attempt-v1.json'
REGISTRY = Path('D:/Dev/_Migration/LocalLore-AVD-Storage')
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1')
RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-02-current-knowledge-ui-run-v1')
CONTROLS = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-harness-v1/run-controls-v1')
RUN_PROPOSAL = LIVE/'run-proposal-v1.json'
RUN_AUTHORIZATION = LIVE/'run-authorization-v1.json'
PREPARE_AUTHORIZATION = LIVE/'prepare-authorization-v1.json'
ADMISSION = RUNTIME/'admission-v1.json'
INPUT = CONTROLS/'run-input-v1.json'
HANDOFF = dict(path=str(Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-prepare-inputs-v1/frozen-inputs-v1/handoff-inputs-v1.json')),
    bytes=8520, sha256='079badce9a2ee44695f91fd99b7c5d700e638e6ee776d584450bf2a35e4983a2')
STATIC = dict(path=str(Path('D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/frozen-inputs-v3/static-installed-inputs-v1.json')),
    bytes=3678, sha256='d2ca3f1ef02ed01169b84bb62090f663aca610db159e8db97606d1e1becccf99')
MAX_SECONDS = 2400
AUTHORITY_KEYS = frozenset(('version','scope','source_head','operator_head','proposal','operator','contract',
    'handoff','ledger','allow_sdk_prepare','allow_one_boot','allow_model','allow_retirement',
    'approval_reference','max_operation_seconds'))


class FreshRunRefused(ValueError):
    """Only fixed reason codes; never raw private diagnostic data."""


def need(value, reason):
    if not value:
        raise FreshRunRefused(reason)


def same(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def binding(value, expected=None, maximum=2*1024**2):
    need(type(value) is dict and set(value)=={'path','bytes','sha256'}, 'binding')
    need(type(value['path']) is str and type(value['bytes']) is int and 0<value['bytes']<=maximum and
         type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None, 'binding')
    path=PureWindowsPath(value['path'])
    need(path.is_absolute() and path.drive.upper()=='D:' and value['path']==str(path), 'path')
    if expected is not None:
        need(path==PureWindowsPath(expected), 'path')


def validate_authority(value):
    need(type(value) is dict and set(value)==AUTHORITY_KEYS, 'authority')
    need(type(value['version']) is int and value['version']==1 and
         value['scope']=='sdk16-fresh-prepare-and-one-knowledge-ui-run-v1' and
         value['source_head']==SOURCE_HEAD and type(value['operator_head']) is str and
         re.fullmatch('[0-9a-f]{40}',value['operator_head']) is not None, 'authority')
    need(value['allow_sdk_prepare'] is True and value['allow_one_boot'] is True and
         value['allow_model'] is False and value['allow_retirement'] is False and
         type(value['max_operation_seconds']) is int and value['max_operation_seconds']==MAX_SECONDS, 'authority')
    ref=value['approval_reference']
    need(type(ref) is str and 0<len(ref)<=256 and not any(ord(c)<32 for c in ref), 'authority')
    for role,path in (('proposal',PROPOSAL),('operator',OPERATOR),('contract',CONTRACT),
                      ('handoff',HANDOFF['path']),('ledger',REGISTRY/'ledger-v1.json')):
        binding(value[role],path)
    need(same(value['handoff'],HANDOFF), 'handoff')
    return copy.deepcopy(value)


def validate_attempt(value, authority_pin, authority):
    binding(authority_pin,AUTHORITY)
    authority=validate_authority(authority)
    need(type(value) is dict and set(value)=={'version','scope','authority','handoff','operator','contract','no_retry'} and
         type(value['version']) is int and value['version']==1 and
         value['scope']=='sdk16-fresh-operation-attempt-v1' and value['no_retry'] is True and
         same(value['authority'],authority_pin), 'attempt')
    for role in ('handoff','operator','contract'):
        need(same(value[role],authority[role]), 'attempt')
    return copy.deepcopy(value)
