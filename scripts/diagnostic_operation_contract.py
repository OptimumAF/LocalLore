"""Fixed SDK17 parent-operation metadata; validation performs no I/O.

Records represent explicit reviewed local authority, not authentication against
a local administrator. No metadata grants retirement or SDK admission.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path, PureWindowsPath
import re

OUT=Path('D:/Dev/Experiments/LocalLore/2026-11-03-diagnostic-operation-v1')
OPERATOR_ROOT=OUT/'candidate-source-v1'
OPERATOR=OPERATOR_ROOT/'scripts/run_diagnostic_operation.py'
CONTRACT=OPERATOR_ROOT/'scripts/diagnostic_operation_contract.py'
AUTHORITY=OUT/'human-authority-v1.json'
LIVE=OUT/'live-parent-v1'
ATTEMPT=LIVE/'attempt-v1.json'
SOURCE=Path('D:/Dev/Experiments/LocalLore/2026-11-02-diagnostic-ui-profile-v1/candidate-source-v1')
FRESH_ROOT=Path('D:/Dev/Experiments/LocalLore/2026-11-03-diagnostic-fresh-handoff-v1')
FRESH_SOURCE=FRESH_ROOT/'candidate-source-v1'
FRESH_HEAD='62ffccfef23e737bd4a6049faf3edb0e558df093'
FRESH_OPERATOR=dict(path=str(FRESH_SOURCE/'scripts/run_diagnostic_ui_fresh.py'),bytes=27471,
    sha256='2bd8a8fed7d15ebe25151442f8f1190ccfbe69b2b28785b4450641fb91bf9232')
FRESH_CONTRACT=dict(path=str(FRESH_SOURCE/'scripts/diagnostic_ui_fresh_contract.py'),bytes=7465,
    sha256='65ddc833a83158d53bf1cb9ad0c87cf956bdbf776d9a7c6b26f6040fe2255fcf')
HANDOFF=dict(path=str(FRESH_ROOT/'frozen-inputs-v1.json'),bytes=9664,
    sha256='8bc25238ca542c30837bcbeda75aaaf82ef256afb27eafe2e6547c88313816cc')
FRESH_AUTHORITY=FRESH_ROOT/'human-authority-v1.json'
FRESH_LIVE=FRESH_ROOT/'live-operation-v1'
PROPOSAL=FRESH_ROOT/'PROPOSED_OPERATION.md'
REGISTRY=Path('D:/Dev/_Migration/LocalLore-AVD-Storage')
GUEST=Path('D:/Dev/Experiments/LocalLore/2026-11-03-diagnostic-ui-v1/avd-v1')
MAX_SECONDS=2400
AUTHORITY_KEYS=frozenset(('version','scope','fresh_head','operator','contract','proposal',
    'fresh_authority','allow_one_operation','allow_model','allow_retirement','max_operation_seconds','approval_reference'))


class OperationRefused(ValueError):
    """Fixed local categories; never private exception payload."""


def need(value,reason):
    if not value:raise OperationRefused(reason)


def same(a,b):
    return json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False)


def binding(pin,expected=None,maximum=2*1024**2):
    need(type(pin) is dict and set(pin)=={'path','bytes','sha256'},'binding')
    need(type(pin['path']) is str and type(pin['bytes']) is int and 0<pin['bytes']<=maximum and
         type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None,'binding')
    path=PureWindowsPath(pin['path'])
    need(path.is_absolute() and path.drive.upper()=='D:' and str(path)==pin['path'] and
         not any(ord(c)<32 for c in pin['path']),'path')
    if expected is not None:need(path==PureWindowsPath(expected),'path')


def validate_authority(value):
    need(type(value) is dict and set(value)==AUTHORITY_KEYS,'authority')
    need(type(value['version']) is int and value['version']==1 and
         value['scope']=='sdk17-diagnostic-operation-authority-v1' and value['fresh_head']==FRESH_HEAD,'authority')
    need(value['allow_one_operation'] is True and value['allow_model'] is False and value['allow_retirement'] is False and
         type(value['max_operation_seconds']) is int and value['max_operation_seconds']==MAX_SECONDS,'authority')
    for role,path in (('operator',OPERATOR),('contract',CONTRACT),('proposal',PROPOSAL),('fresh_authority',FRESH_AUTHORITY)):
        binding(value[role],path)
    ref=value['approval_reference']
    need(type(ref) is str and 0<len(ref)<=256 and not any(ord(c)<32 for c in ref),'authority')
    return copy.deepcopy(value)


def validate_attempt(value,pin,authority):
    binding(pin,AUTHORITY);authority=validate_authority(authority)
    need(type(value) is dict and set(value)=={'version','scope','authority','operator','contract','fresh_authority','no_retry'} and
         type(value['version']) is int and value['version']==1 and
         value['scope']=='sdk17-diagnostic-operation-attempt-v1' and value['no_retry'] is True and same(value['authority'],pin),'attempt')
    for role in ('operator','contract','fresh_authority'):need(same(value[role],authority[role]),'attempt')
    return copy.deepcopy(value)
