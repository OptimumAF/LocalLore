"""Fixed live-process witness profile; importing it grants no guest authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import PureWindowsPath
import re

from benchmarks import owned_target_contract as core
from benchmarks import owned_restart_contract as restart

PROTOCOL = 'owned-emulator-live-death-target-v1'
SDK_PROTOCOL = 'sdk-owned-live-death-v1'
PROOF_PROTOCOL = 'owned-live-death-socket-proof-v1'
CLIENT_VERSION = 6
SESSION_FILE = 'sdk-session-v6.json'
OWNER_SCRIPT = 'owned_live_death_owner.py'
BOOT_CLAIM_FILE = 'owned-live-death-boot-claim-v1.json'
# Prospective source-only target. This constant is not preparation/run approval.
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-30-live-death-v1/avd-v1')
CLASS = core.CLASS
METHODS = (core.METHODS[0], 'recordsOneRealAuthorCreationWithLiveDeathCheckpoint')
RESTART_CLASS, RESTART_METHOD = restart.RESTART_CLASS, restart.RESTART_METHOD
INSTRUMENTATIONS = (
    ('import', CLASS, METHODS[0]),
    ('author_live', CLASS, METHODS[1]),
    ('restart', RESTART_CLASS, RESTART_METHOD),
)
CLAIM_KINDS = ('import', 'author_live', 'restart')
ARTIFACT_KEYS = frozenset(restart.ARTIFACT_KEYS)
SOURCE_NAMES = frozenset(restart.SOURCE_NAMES | {
    'owned_live_death_contract.py', 'owned_live_death_owner.py',
    'android_process_client_v6.py', 'android_process_verification_v6.py',
    'android_live_death_witness.py', 'original_author_live_death_controller.py',
})
PROCESS_PROBE = '/data/local/tmp/locallore-author-process-probe-v1'


class _LiveDeathContract(core._Contract):
    """The sole new command is the fixed read-only v2 native snapshot."""

    def validate_operation(self, value, admission):
        argv = value.get('argv') if type(value) is dict else None
        if type(argv) is list and argv == ['run-as', core.APP, '--user', '0', 'ls', 'no_backup']:
            # Poll the existing app-owned parent without issuing a failing ls
            # against a checkpoint child that has not been published yet.
            self.validate_admission(admission)
            core._obj(value, ('argv', 'stdin'), 'command')
            core._need(value['stdin'] is None, 'command')
            return copy.deepcopy(value)
        if type(argv) is list and argv[:2] == [PROCESS_PROBE, '--snapshot-v2']:
            # Validate the same admission, exact record shape, canonical numeric
            # arguments, bounds and absent stdin as the core snapshot command.
            self.validate_admission(admission)
            core._obj(value, ('argv', 'stdin'), 'command')
            core._need(len(argv) == 4 and value['stdin'] is None, 'command')
            for item, minimum in zip(argv[2:], (1, 10000)):
                core._need(type(item) is str and len(item) <= 10 and
                           re.fullmatch('[1-9][0-9]*', item) is not None, 'command')
                core._int(int(item), minimum, 2**31 - 1, 'command')
            return copy.deepcopy(value)
        # SDK6 cannot substitute the weaker v1 native packet in a live witness.
        core._need(not (type(argv) is list and argv[:2] ==
                        [PROCESS_PROBE, '--snapshot']), 'command')
        return super().validate_operation(value, admission)


# Code selects the profile; neither JSON nor public constructors select modules.
_API = _LiveDeathContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
))

for _name in (
    'PORT', 'APP', 'TEST', 'MODEL_BYTES', 'MODEL_SHA256', 'ADMISSION_KEYS',
    'GUEST_KEYS', 'RUNNING_KEYS', 'SESSION_KEYS', 'CONTEXT_KEYS', 'PROOF_KEYS',
    'QUERY_BUNDLE_KEYS', 'QUERY_KEYS', 'BRACKET_KEYS', 'READY_KEYS', 'JOB_KEYS',
    'REQUEST_KEYS', 'WORKER_KEYS', 'CLEANUP_KEYS', 'CLIENT_KEYS', 'TargetRefused',
    '_need', '_obj', '_int', '_same', '_path', '_process',
):
    globals()[_name] = getattr(core, _name)

for _name in (
    'binding', '_sources', 'validate_admission', '_clock', 'validate_running',
    'check_stop', 'validate_session', '_relative', 'validate_operation',
    'operation_digest', '_rows', 'validate_observation', '_guest_observation',
    'validate_guest_observation', 'validate_guest_prefix', 'device_status',
    'device_transport', 'validate_proof', '_brackets', 'validate_query_bundle',
    'validate_guest_job', 'validate_ready', 'validate_claim',
    'validate_client_record', 'source_bindings', 'revalidate_inputs',
    'instrumentation_kind', 'claim_record',
):
    globals()[_name] = getattr(_API, _name)
del _name
