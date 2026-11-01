"""Synthetic metadata only; these fixtures grant no target or process authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import PureWindowsPath

from scripts.tests import test_owned_target_contract as legacy

PROTOCOL = 'owned-emulator-presentation-process-v1'
SDK_PROTOCOL = 'sdk-presentation-process-v1'
PROOF_PROTOCOL = 'presentation-process-socket-proof-v1'
APP = 'org.locallore.app.presentationprocessverify'
TEST = APP + '.test'
CONTROL = 'org.locallore.app.presentationprocesscontroller'
COMPONENT = CONTROL + '/org.locallore.presentationprocessverify.PresentationProcessRestoreInstrumentation'
CASE = 'restore_player_presentation'
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-01-presentation-process-target-v1/avd-v1')
STAGED = {
    'product_apk': '/data/local/tmp/locallore-product-v1.apk',
    'test_apk': '/data/local/tmp/locallore-test-v1.apk',
    'controller_apk': '/data/local/tmp/locallore-presentation-controller-v1.apk',
}


def admission(contract):
    value = legacy.admission()
    value['protocol'] = PROTOCOL
    value['guest']['root'] = str(GUEST_ROOT)
    value['artifacts'] = {role: value['artifacts'][role] for role in ('build', 'product_apk', 'test_apk')}
    value['artifacts']['controller_apk'] = legacy.pin('D:/Synthetic/controller-debug.apk')
    value['sources'] = sorted([
        legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
        for name in contract.SOURCE_NAMES
    ], key=lambda row: row['path'])
    sources = {PureWindowsPath(row['path']).name: row for row in value['sources']}
    value['server']['sources'] = [copy.deepcopy(sources[PureWindowsPath(row['path']).name])
                                  for row in value['server']['sources']]
    return value


def session(contract, value=None):
    value = admission(contract) if value is None else value
    result = legacy.session(value)
    result['protocol'] = SDK_PROTOCOL
    result['descriptor']['protocol'] = PROTOCOL
    result['root'] = 'D:/Synthetic/sdk-v9'
    return result


def instrument(value):
    return ['am', 'instrument', '-w', '-r', '-e', 'case', CASE, '-e', 'run_id',
            value['run_id'][:16], '-e', 'product_sha256',
            value['artifacts']['product_apk']['sha256'], COMPONENT]


def running(value):
    result = legacy.running(value)
    result['protocol'] = PROTOCOL
    return result


def proof(session_value, *, after=False):
    result = legacy.proof(session_value, after=after)
    result['protocol'] = PROOF_PROTOCOL
    result['session'] = legacy.pin(PureWindowsPath(session_value['root']) / 'sdk-session-v9.json')
    return result


def query_bundle(session_value):
    result = legacy.query_bundle(session_value)
    result['protocol'] = PROOF_PROTOCOL
    return result
