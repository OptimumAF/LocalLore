"""Fixed SDK18 fresh-operation metadata. Import/validation perform no I/O.

These records bind explicit reviewed human authority, not authentication
against a local administrator. No validator grants preparation or admission.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path, PureWindowsPath
import re

SOURCE=Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/candidate-source-v1')
SOURCE_HEAD='287b158e72ed5c0811a2e7e433e73ada4f4d6c52'
SOURCE_TREE='81dae478d06f2da8be5f14a693f276318fe0c4ac'
OUT=Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-fresh-v1')
OPERATOR_ROOT=OUT/'candidate-source-v1'
OPERATOR = OPERATOR_ROOT/'scripts/run_record_cancellation_ui_fresh.py'
CONTRACT = OPERATOR_ROOT/'scripts/record_cancellation_ui_fresh_contract.py'
LIVE = OUT/'live-operation-v1'
PROPOSAL = OUT/'PROPOSED_OPERATION.md'
AUTHORITY = OUT/'human-authority-v1.json'
ATTEMPT = LIVE/'attempt-v1.json'
REGISTRY = Path('D:/Dev/_Migration/LocalLore-AVD-Storage')
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1/avd-v1')
RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-runtime-v1')
CONTROLS=Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/run-controls-v1')
RUN_PROPOSAL = LIVE/'run-proposal-v1.json'
RUN_AUTHORIZATION = LIVE/'run-authorization-v1.json'
PREPARE_AUTHORIZATION = LIVE/'prepare-authorization-v1.json'
ADMISSION = RUNTIME/'admission-v1.json'
INPUT = CONTROLS/'run-input-v1.json'
HANDOFF={'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-03-record-cancellation-fresh-v1\\inspection-v1\\frozen-inputs-v1.json', 'bytes': 9074, 'sha256': '8ee6bd191b3b996c79aae877a125b2b2255ad4e61316ad1baae88cd477b1a40d'}
STATIC = dict(path=str(Path('D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/frozen-inputs-v3/static-installed-inputs-v1.json')),
    bytes=3678,sha256='d2ca3f1ef02ed01169b84bb62090f663aca610db159e8db97606d1e1becccf99')
SOURCE_PUBLICATION={'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-03-record-cancellation-profile-v1\\final-source-readback-v1.json', 'bytes': 747334, 'sha256': 'b6202c3a4b06d70845c28cedf52ec68140da3a2dc482b6573221183d2de11db5'}
READY=OUT/'inspection-v1'
PREPARE_PIN={'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-03-record-cancellation-fresh-v1\\inspection-v1\\prepare-proposal-v1.json', 'bytes': 173590, 'sha256': 'ce5b7347c7c2e933f590bf442079d6b9e540529cd31b4e9e4afb71c9c4b89ab0'}
BUILD_PIN={'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-03-record-cancellation-ui-build-v1\\record-cancellation-ui-build-v1.json', 'bytes': 32140, 'sha256': '4d39b74ad5aee455ce9060c01d760204022101e4b6b8ce58d12f666450d2894e'}
PROFILE = dict(memory_mib=8192,cores=4,api=35,max_run_seconds=1800)
MAX_SECONDS = 2400
AUTHORITY_KEYS = frozenset(('version','scope','source_head','proposal','operator','contract',
    'handoff','ledger','allow_sdk_prepare','allow_one_boot','allow_model','allow_retirement',
    'approval_reference','max_operation_seconds'))


class FreshRunRefused(ValueError):
    """Fixed local reason codes, never private record-cancellation text."""


def need(value,reason):
    if not value:
        raise FreshRunRefused(reason)


def same(left,right):
    return json.dumps(left,sort_keys=True,allow_nan=False)==json.dumps(right,sort_keys=True,allow_nan=False)


def binding(value,expected=None,maximum=2*1024**2,*,project=True):
    need(type(value) is dict and set(value)=={'path','bytes','sha256'},'binding')
    need(type(value['path']) is str and type(value['bytes']) is int and 0<value['bytes']<=maximum and
         type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'binding')
    path=PureWindowsPath(value['path'])
    need(path.is_absolute() and (not project or path.drive.upper()=='D:') and
         value['path']==str(path) and not any(ord(c)<32 for c in value['path']),'path')
    if expected is not None:
        need(path==PureWindowsPath(expected),'path')


def validate_authority(value):
    need(type(value) is dict and set(value)==AUTHORITY_KEYS,'authority')
    need(type(value['version']) is int and value['version']==1 and
         value['scope']=='sdk18-fresh-prepare-and-one-record-cancellation-ui-run-v1' and
         value['source_head']==SOURCE_HEAD,'authority')
    need(value['allow_sdk_prepare'] is True and value['allow_one_boot'] is True and
         value['allow_model'] is False and value['allow_retirement'] is False and
         type(value['max_operation_seconds']) is int and value['max_operation_seconds']==MAX_SECONDS,'authority')
    ref=value['approval_reference']
    need(type(ref) is str and 0<len(ref)<=256 and not any(ord(c)<32 for c in ref),'authority')
    for role,path in (('proposal',PROPOSAL),('operator',OPERATOR),('contract',CONTRACT),
                      ('handoff',HANDOFF['path']),('ledger',REGISTRY/'ledger-v1.json')):
        binding(value[role],path)
    need(same(value['handoff'],HANDOFF),'handoff')
    return copy.deepcopy(value)


def validate_attempt(value,authority_pin,authority):
    binding(authority_pin,AUTHORITY)
    authority=validate_authority(authority)
    need(type(value) is dict and set(value)=={'version','scope','authority','handoff','operator','contract','no_retry'} and
         type(value['version']) is int and value['version']==1 and
         value['scope']=='sdk18-fresh-operation-attempt-v1' and value['no_retry'] is True and
         same(value['authority'],authority_pin),'attempt')
    for role in ('handoff','operator','contract'):
        need(same(value[role],authority[role]),'attempt')
    return copy.deepcopy(value)


def validate_handoff(value):
    keys={'version','scope','source_root','source_head','source_tree','guest','controls','runtime',
          'sources','python','artifacts','prepare_proposal','capacity_preview','profile',
          'execution_authorized','model_material'}
    need(type(value) is dict and set(value)==keys and type(value['version']) is int and
         value['version']==1 and value['scope']=='sdk18-fresh-inputs-v1','handoff')
    need(value['source_root']==str(SOURCE) and value['source_head']==SOURCE_HEAD and value['source_tree']==SOURCE_TREE and
         value['guest']==str(GUEST) and value['controls']==str(CONTROLS) and value['runtime']==str(RUNTIME),'handoff')
    need(same(value['profile'],PROFILE) and value['execution_authorized'] is False and value['model_material'] is False,'profile')
    need(type(value['sources']) is list and len(value['sources'])==28,'sources')
    names=set()
    for pin in value['sources']:
        binding(pin)
        path=PureWindowsPath(pin['path'])
        need(path.parent==PureWindowsPath(SOURCE/'benchmarks') and path.name not in names,'sources')
        names.add(path.name)
    need(value['sources']==sorted(value['sources'],key=lambda p:p['path']),'sources')
    need(type(value['python']) is dict and set(value['python'])=={'executable','runtime_dll'},'python')
    binding(value['python']['executable'],maximum=128*1024**2,project=False)
    if value['python']['runtime_dll'] is not None:
        binding(value['python']['runtime_dll'],maximum=128*1024**2,project=False)
    need(type(value['artifacts']) is dict and set(value['artifacts'])=={'build','product_apk','test_apk'},'artifacts')
    for pin in value['artifacts'].values():
        binding(pin,maximum=128*1024**2)
    need(same(value['artifacts']['build'],BUILD_PIN) and same(value['prepare_proposal'],PREPARE_PIN),'handoff')
    binding(value['capacity_preview'],READY/'capacity-preview-v1.json')
    return copy.deepcopy(value)
