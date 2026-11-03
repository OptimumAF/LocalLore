"""Fixed SDK18 parent-operation metadata; validation performs no I/O.

Records represent explicit reviewed local authority, not authentication against
a local administrator. No metadata grants retirement or SDK admission.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path, PureWindowsPath
import re

OUT=Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-fresh-v1')
OPERATOR_ROOT=OUT/'candidate-source-v1'
OPERATOR=OPERATOR_ROOT/'scripts/run_record_cancellation_operation.py'
CONTRACT=OPERATOR_ROOT/'scripts/record_cancellation_operation_contract.py'
AUTHORITY=OUT/'parent-authority-v1.json'
LIVE=OUT/'live-parent-v1'
ATTEMPT=LIVE/'attempt-v1.json'
SOURCE=Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/candidate-source-v1')
FRESH_ROOT=OUT
FRESH_SOURCE=OPERATOR_ROOT
FRESH_HEAD='287b158e72ed5c0811a2e7e433e73ada4f4d6c52'
FRESH_OPERATOR={'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-03-record-cancellation-fresh-v1\\candidate-source-v1\\scripts\\run_record_cancellation_ui_fresh.py', 'bytes': 29984, 'sha256': 'e59270006c263f76dbd51d4393db850776453ca3da206c49b2f44e31a235e108'}
FRESH_CONTRACT={'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-03-record-cancellation-fresh-v1\\candidate-source-v1\\scripts\\record_cancellation_ui_fresh_contract.py', 'bytes': 7683, 'sha256': 'e9fdacf5a04c7a70e897e68fcff5c165b2f1b375f95c5ae76a014557078852f7'}
HANDOFF={'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-03-record-cancellation-fresh-v1\\inspection-v1\\frozen-inputs-v1.json', 'bytes': 9074, 'sha256': '8ee6bd191b3b996c79aae877a125b2b2255ad4e61316ad1baae88cd477b1a40d'}
FRESH_AUTHORITY=FRESH_ROOT/'human-authority-v1.json'
FRESH_LIVE=FRESH_ROOT/'live-operation-v1'
PROPOSAL=FRESH_ROOT/'PROPOSED_OPERATION.md'
REGISTRY=Path('D:/Dev/_Migration/LocalLore-AVD-Storage')
GUEST=Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1/avd-v1')
MAX_SECONDS=2400
AUTHORITY_KEYS=frozenset(('version','scope','profile_source_head','operator','contract','proposal',
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
         value['scope']=='sdk18-record-cancellation-operation-authority-v1' and value['profile_source_head']==FRESH_HEAD,'authority')
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
         value['scope']=='sdk18-record-cancellation-operation-attempt-v1' and value['no_retry'] is True and same(value['authority'],pin),'attempt')
    for role in ('operator','contract','fresh_authority'):need(same(value[role],authority[role]),'attempt')
    return copy.deepcopy(value)
