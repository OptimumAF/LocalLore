"""Fixed physical-phone receipt experiment; actual calls require a separate grant.

Private identities and raw diagnostics stay in create-only evidence. No model,
device, filesystem or native operation occurs merely by importing this module.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).absolute().parent))
import physical_model_contract as contract
import receipt_setup_qualification as q
import receipt_avd_environment as environment
import receipt_real_cancellation as cancellation
import litert_worker_trace as worker
import litert_send_trace as send
import litert_callback_trace as callback
import litert_status_trace as status_trace

ROOT = Path(__file__).absolute().parents[1]
SCRIPT = Path(__file__).absolute()
# Resolved only at an explicit entry point; never inspect a user's SDK at import.
ADB = None
POWERSHELL = None
APP, TEST = contract.APP, contract.TEST
SCOPE = 'physical_model_probe_v1'
PROOF_SCOPE = 'physical_model_v1'
REQUEST = b'physical-model-probe-v1\n'
STREAM_REQUEST = b'physical-model-stream-v1\n'
SOURCE_ROOT = 'no_backup/physical-model-source-v1'
PROOF_ROOT = 'no_backup/physical-model-proof-v1'
OWNER_BYTES = b'locallore-physical-source-v1\n'
OWNER_SHA = '6e58105a6f97416ed0727594cfaadac7326bece25e03c4305ab70fc964790b5e'
PROBE_BYTES = 65
PROBE_SHA = '72e34de83e7311b37f7a17361f3d71555209ffbfe4eb9e861cc11c7903e13422'
PROBE_PATH = ROOT / 'benchmarks/fixtures/physical_model_probe_v1.txt'
# Signed pair built from fbef4195 and actually audited at df5669a7.
# These are experiment artifacts, not a production or physical-runtime acceptance.
APK_HASHES = {
    APP: '13f8768e010bf007319748b0b158694ffb6c847d50f87638cf0af42fca60e1a5',
    TEST: '1c3bba2756b5ae6c46842d483cd07dba433b1b3cfa83ee215ae0e1e47af4298c',
}
PRIOR_PAIR = {
    'org.locallore.app.modelverify': '1af7bd97a9c8f40b95387376181a4791d362a9459078036c183695245e39c26e',
    'org.locallore.app.modelverify.test': '8c14c03502faee7661b58a6862c5b35e9fec6e6371e40b9c2718daadd56ad1e5',
}
PHASES = {
    'PRECHECK': ('precheck', 'PhysicalModelPreflightTest', 'verifiesPrivatePhoneSourceBeforeCopy', 30_000,
        frozenset('build_identity_exact phone_profile_exact context_roots_exact same_filesystem source_owner_probe_exact source_whitelist_exact source_model_absent legacy_roots_absent candidate_access_receipt candidate_roots_absent candidate_installed_null_noncreating memory_eligible two_copy_capacity'.split())),
    'IMPORT': ('import', 'PhysicalModelImportTest', 'importsFixedPhoneCandidate', 150_000,
        frozenset('prior_precheck_exact process_identity_changed source_owner_probe_exact source_whitelist_exact source_regular_uid source_fullhash_exact source_verify_closed_once import_offmain_closed_once import_exact_bytes setup_missing_before setup_ready_after candidate_access_receipt preaccept_runtime_refused accepted_full_recheck receipt_owner_exact memory_eligible shared_capacity'.split())),
    'CANCEL': ('cancel', 'PhysicalModelCancellationTest', 'cancelsAndJoinsWithoutCommit', 170_000,
        frozenset('prior_import_exact process_identity_changed accepted_recheck runtime_guard production_transport initial_canon_zero public_inference_sampled cancel_ack_joined terminal_drain known_sdk_close main_responsive no_prepared no_commit no_receipts candidate_owner_retained native_handle_closed model_intact memory_eligible'.split())),
    'GIFT': ('gift', 'PhysicalModelGiftTest', 'commitsGuardedPhoneGift', 170_000,
        frozenset('prior_cancel_exact process_identity_changed prior_story_exact initial_zero fixed_input_once actual_two_roles worker_close_verified canonical_revision_one gift_exact single_receipt zero_repair zero_fallback accepted_post_sdk_full_recheck native_handle_closed memory_eligible'.split())),
    'DIALOGUE': ('dialogue', 'PhysicalModelDialogueTest', 'recordsLiteralPhoneDialogue', 170_000,
        frozenset('prior_gift_exact process_identity_changed prior_story_exact gift_preserved invalid_actions_no_sdk literal_input statement_not_truth known_truth_unchanged canonical_revision_two two_receipts roles_closed zero_repair zero_fallback accepted_post_sdk_full_recheck native_handle_closed memory_eligible'.split())),
    'REOPEN': ('reopen', 'PhysicalModelReopenTest', 'reopensPhoneReceiptsWithoutInference', 120_000,
        frozenset('prior_dialogue_exact process_identity_changed prior_story_exact source_unopened accepted_recheck setup_ready no_sdk no_text canonical_revision_two receipts_exact native_handle_closed memory_eligible retained_transcript'.split())),
}
ORDER = tuple(PHASES)
TRACES = {'PRECHECK': (), 'IMPORT': (),
    'CANCEL': ('cancel-sample-worker-v2.json', 'cancel-worker-v2.json'),
    'GIFT': ('gift-worker-v2.json',),
    'DIALOGUE': ('guards-worker-v2.json', 'dialogue-worker-v2.json'),
    'REOPEN': ('reopen-worker-v2.json',)}
COMMON_KEYS = frozenset(('version scope profile phase pid start uid process model_bytes model_sha256 elapsed_ms shared_free_before shared_free_after memory_total_bytes memory_available_before memory_available_after low_memory_before low_memory_after source_verify_opened source_verify_closed source_verify_bytes source_import_opened source_import_closed source_import_bytes sdk_invoked publication_native_invoked checks').split())
SOURCE_FILES = tuple(dict.fromkeys((*cancellation.SOURCE_FILES,
    'benchmarks/litert_send_trace.py', 'scripts/tests/test_litert_send_trace.py',
    'benchmarks/litert_callback_trace.py', 'scripts/tests/test_litert_callback_trace.py',
    'benchmarks/litert_status_trace.py', 'scripts/tests/test_litert_status_trace.py',
    'benchmarks/physical_model_contract.py', 'scripts/tests/test_physical_model_contract.py',
    'benchmarks/physical_model_probe.py', 'scripts/tests/test_physical_model_probe.py',
    'benchmarks/fixtures/physical_model_probe_v1.txt', 'docs/native/PHYSICAL_MODEL_HOST_PROTOCOL.md',
    'docs/native/PHYSICAL_MODEL_PROFILE.md', 'docs/native/PHYSICAL_MODEL_ANDROID_PROTOCOL.md',
    'apps/android/app/build.gradle.kts', 'apps/android/app/src/physicalModel/AndroidManifest.xml',
    'apps/android/app/src/litert/java/org/locallore/app/AndroidPhysicalModelAccess.kt',
    'apps/android/app/src/litert/java/org/locallore/app/PhysicalModelPolicy.kt',
    'apps/android/app/src/physicalModel/java/org/locallore/app/PhysicalModelProof.kt',
    'apps/android/app/src/physicalModelTest/java/org/locallore/app/PhysicalModelProofTest.kt',
    'apps/android/app/src/physicalModelTest/java/org/locallore/app/PhysicalModelPolicyTest.kt',
    'apps/android/app/src/physicalModelAndroidTest/java/org/locallore/app/PhysicalModelHarness.kt',
    'apps/android/app/src/physicalModelAndroidTest/java/org/locallore/app/PhysicalModelStorageTest.kt',
    'apps/android/app/src/physicalModelAndroidTest/java/org/locallore/app/PhysicalModelCancellationTest.kt',
    'apps/android/app/src/physicalModelAndroidTest/java/org/locallore/app/PhysicalModelPlayTest.kt')))
PROPOSAL_KEYS = frozenset(('version scope phase identity_path identity_sha256 discovery_path discovery_sha256 adb_path powershell_path adb_sha256 powershell_sha256 apk_paths bindings source prior evidence_root').split())
IDENTITY = ('ro.build.fingerprint', 'ro.product.model', 'ro.build.version.sdk', 'ro.soc.model', 'ro.board.platform', 'ro.product.cpu.abilist', 'ro.kernel.qemu')
PROPERTIES = ('sh', '-c', 'for k in ' + ' '.join(IDENTITY) + '; do printf "%s=" "$k"; getprop "$k" || exit 41; done')
PACKAGES = ('cmd', 'package', 'list', 'packages', '-U', '--user', '0', 'org.locallore')
PS = ('ps', '-A', '-o', 'PID,UID,NAME')
MEMORY = ('sh', '-c', "grep -E '^(MemTotal|MemAvailable):' /proc/meminfo")
SPACE = ('stat', '-f', '-c', '%a|%S', '/data')
PAGE = ('getconf', 'PAGESIZE')
POWER = ('dumpsys', 'battery')
THERMAL = ('dumpsys', 'thermalservice')
CURRENT_USER = ('am', 'get-current-user')


def configure_tools():
    """Use explicit SDK/Windows roots and pin one immutable process-local choice."""
    global ADB, POWERSHELL
    configured = [os.environ[k] for k in ('ANDROID_HOME', 'ANDROID_SDK_ROOT') if k in os.environ]
    assert configured and all(type(v) is str and v and Path(v).is_absolute() and '..' not in Path(v).parts for v in configured)
    roots = [plain_path(v, directory=True).resolve(strict=True) for v in configured]
    assert all(root == roots[0] and root.is_dir() for root in roots)
    system = os.environ.get('SystemRoot')
    assert type(system) is str and system and Path(system).is_absolute() and '..' not in Path(system).parts
    system = plain_path(system, directory=True).resolve(strict=True); assert system.is_dir()
    adb = roots[0]/'platform-tools/adb.exe'
    powershell = system/'System32/WindowsPowerShell/v1.0/powershell.exe'
    plain_path(adb, directory=False); plain_path(powershell, directory=False)
    assert ADB is None or ADB == adb
    assert POWERSHELL is None or POWERSHELL == powershell
    ADB, POWERSHELL = adb, powershell
    return adb, powershell


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, low=0, high=2**63-1):
    assert type(value) is int and low <= value <= high
    return value


def digest(value):
    assert type(value) is str and re.fullmatch('[0-9a-f]{64}', value)
    return value


def text(raw, cap=131072):
    return q.normalized(raw, cap)


def load(path):
    return q.contract.strict_json(Path(path).read_bytes())


def write(path, value):
    q.write_json(Path(path), value)


def raw_write(path, raw):
    with Path(path).open('xb') as sink:
        sink.write(raw); sink.flush(); os.fsync(sink.fileno())


def file_hash(path, cap):
    p = Path(path)
    plain_path(p, directory=False)
    before = p.lstat(); assert type(cap) is int and 0 < before.st_size <= cap
    def identity(value):
        return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns
    h = hashlib.sha256()
    with p.open('rb') as source:
        held = os.fstat(source.fileno()); assert stat.S_ISREG(held.st_mode) and identity(held) == identity(before)
        remaining = before.st_size
        while remaining:
            block = source.read(min(1024*1024, remaining)); assert block
            h.update(block); remaining -= len(block)
        assert source.read(1) == b''
        assert identity(os.fstat(source.fileno())) == identity(before)
    plain_path(p, directory=False)
    assert identity(p.lstat()) == identity(before)
    return h.hexdigest()


def plain_path(path, *, directory):
    """Reject links/reparse ancestors without resolving them into trusted paths."""
    p = Path(path)
    assert p.is_absolute() and '..' not in p.parts
    for node in (p, *p.parents):
        value = node.lstat()
        assert not stat.S_ISLNK(value.st_mode) and not (getattr(value, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
        assert (stat.S_ISDIR(value.st_mode) if node != p or directory else stat.S_ISREG(value.st_mode))
    return p


def parse_devices(raw, serial):
    assert type(serial) is str and re.fullmatch('[A-Za-z0-9_-]{4,128}', serial) and not serial.startswith('emulator-')
    lines = text(raw).splitlines()
    assert lines and lines[0] == 'List of devices attached'
    selected = []
    for line in lines[1:]:
        if not line: continue
        parts = line.split(); assert len(parts) >= 2
        if parts[0] != serial: continue
        assert parts[1] == 'device'
        values = {}
        for word in parts[2:]:
            key, sep, value = word.partition(':')
            assert sep and key not in values and key in ('usb', 'product', 'model', 'device', 'transport_id')
            values[key] = value
        assert set(values) == {'usb', 'product', 'model', 'device', 'transport_id'}
        assert re.fullmatch('[1-9][0-9]{0,9}', values['transport_id'])
        assert re.fullmatch('[A-Za-z0-9_.:-]{1,128}', values['usb'])
        assert all(re.fullmatch('[A-Za-z0-9_.-]{1,128}', values[k]) for k in ('product', 'model', 'device'))
        selected.append(dict(values, serial=serial, transport_id=int(values['transport_id'])))
    assert len(selected) <= 1
    return selected[0] if selected else None


def parse_server(raw, adb_sha):
    v = q.contract.strict_json(raw)
    assert type(v) is dict and set(v) == {'pid', 'creation_filetime', 'executable', 'listeners'}
    integer(v['pid'], 1, 2**31-1); integer(v['creation_filetime'], 1)
    assert type(v['executable']) is str and Path(v['executable']).resolve() == ADB.resolve()
    assert type(v['listeners']) is list and 1 <= len(v['listeners']) <= 4
    for row in v['listeners']:
        assert type(row) is dict and set(row) == {'address', 'port', 'pid'}
        assert row['address'] in ('127.0.0.1', '::1') and type(row['port']) is int and row['port'] == 5037
        assert type(row['pid']) is int and row['pid'] == v['pid']
    assert len({(r['address'], r['port'], r['pid']) for r in v['listeners']}) == len(v['listeners'])
    v['listeners'] = sorted(v['listeners'], key=lambda r: (r['address'], r['port'], r['pid']))
    return dict(v, adb_sha256=digest(adb_sha))


def server_command():
    # No server creation/lifecycle command is part of this fixed observation.
    script = "$ErrorActionPreference='Stop'; $l=@(Get-NetTCPConnection -LocalPort 5037 -State Listen -ErrorAction Stop); $ids=@($l.OwningProcess|Select-Object -Unique); if($ids.Count -ne 1){throw 'server_refused'}; $p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$ids[0]); if($null -eq $p){throw 'server_refused'}; [pscustomobject]@{pid=[int]$p.ProcessId;creation_filetime=$p.CreationDate.ToUniversalTime().ToFileTimeUtc();executable=$p.ExecutablePath;listeners=@($l|ForEach-Object{[pscustomobject]@{address=$_.LocalAddress;port=[int]$_.LocalPort;pid=[int]$_.OwningProcess}})}|ConvertTo-Json -Depth 4 -Compress"
    return [str(POWERSHELL), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', script]


class Capture:
    """One monotonic fail-stop client owner, including evidence persistence."""
    def __init__(self, directory, seconds):
        self.directory = Path(directory); self.directory.mkdir(exist_ok=False)
        self.clean = True; self.count = 0; self.until = time.monotonic() + seconds
        self.server = None; self.target = None; self.adb_sha = None

    def capture(self, command, label, seconds=15, cap=131072):
        assert self.clean
        try:
            remaining = self.until-time.monotonic(); assert remaining > 0
            self.count += 1; stem = self.directory / ('command-%04d' % self.count)
            result = q.host.run_process(command, request=b'', deadline=min(seconds, remaining), max_output=cap)
            raw_write(stem.with_suffix('.stdout.bin'), result.stdout)
            write(stem.with_suffix('.json'), {'version': 1, 'index': self.count, 'label': label,
                'status': result.status, 'returncode': result.returncode, 'cleanup_complete': result.cleanup_complete,
                'stdout_bytes': len(result.stdout), 'stdout_sha256': sha(result.stdout), 'stderr_bytes': result.stderr_bytes})
            assert result.cleanup_complete is True and result.status == 'completed'
            assert type(result.returncode) is int and result.returncode == 0 and result.stderr_bytes == 0
            return result.stdout
        except BaseException:
            self.clean = False
            raise

    def check_server(self):
        assert self.clean
        try:
            assert file_hash(ADB, 64*1024**2) == self.adb_sha
            current = parse_server(self.capture(server_command(), 'adb-server', cap=16384), self.adb_sha)
            if self.server is None: self.server = current
            assert current == self.server
        except BaseException:
            self.clean = False; raise

    def adb(self, operation, label, seconds=15, cap=131072):
        assert self.target is not None
        try:
            self.check_server()
            raw = self.capture([str(ADB), '-H', '127.0.0.1', '-P', '5037', '-t', str(self.target['transport_id']), *operation], label, seconds, cap)
            self.check_server()
            return raw
        except BaseException:
            self.clean = False; raise

    def shell(self, op, label, seconds=15, cap=131072):
        return self.adb(['shell', shlex.join(op)], label, seconds, cap)


def packages(raw):
    found = {}
    for line in text(raw).splitlines():
        m = re.fullmatch(r'package:(org\.locallore(?:\.[A-Za-z0-9_]+)+) uid:([1-9][0-9]{0,9})', line)
        assert m and m[1] not in found
        found[m[1]] = integer(int(m[2]), 10000, 2**31-1)
    return found


def installed_hash(owner, package):
    assert re.fullmatch(r'org\.locallore(?:\.[A-Za-z0-9_]+)+', package)
    line = text(owner.shell(('pm', 'path', '--user', '0', package), 'apk-path', cap=4096))
    m = re.fullmatch(r'package:(/data/app/[A-Za-z0-9_~+=./-]+/base\.apk)\n', line)
    assert m and '..' not in m[1].split('/')
    value = text(owner.shell(('sha256sum', m[1]), 'apk-hash', seconds=30, cap=4096))
    assert re.fullmatch('[0-9a-f]{64}  ' + re.escape(m[1]) + '\n', value)
    return value[:64]


def package_snapshot(owner):
    uids = packages(owner.shell(PACKAGES, 'packages'))
    return {name: {'uid': uid, 'sha256': installed_hash(owner, name)} for name, uid in sorted(uids.items())}


def validate_packages(current, baseline, installed):
    assert type(current) is dict and 1 <= len(current) <= 128 and type(baseline) is dict
    assert set(current) == set(baseline) | ({APP, TEST} if installed else set())
    assert APP not in baseline and TEST not in baseline
    for name, row in current.items():
        assert re.fullmatch(r'org\.locallore(?:\.[A-Za-z0-9_]+)+', name)
        assert type(row) is dict and set(row) == {'uid', 'sha256'}
        integer(row['uid'], 10000, 2**31-1); digest(row['sha256'])
    assert all(current.get(k) == row for k, row in baseline.items())
    assert all(current.get(k, {}).get('sha256') == value for k, value in PRIOR_PAIR.items())
    if installed:
        assert all(current[k]['sha256'] == APK_HASHES[k] for k in (APP, TEST))
        assert current[APP]['uid'] != current[TEST]['uid']
        assert not {current[APP]['uid'], current[TEST]['uid']} & {row['uid'] for row in baseline.values()}


def process_rows(raw, uid_map):
    lines = text(raw).splitlines(); assert lines and lines[0].split() == ['PID', 'UID', 'NAME']
    rows = []
    for line in lines[1:]:
        fields = line.split(); assert len(fields) == 3
        pid, uid = integer(int(fields[0]), 1, 2**31-1), integer(int(fields[1]), 0, 2**31-1)
        name = fields[2]
        if name == APP or name.startswith(APP + ':') or name == TEST or name.startswith(TEST + ':') or uid in uid_map.values():
            assert name in (APP, TEST) and name in uid_map and uid == uid_map[name]
            rows.append({'pid': pid, 'uid': uid, 'name': name})
    return rows


def observe(owner, baseline, installed):
    # No payload/model/saves are queried. Existing LocalLore APK/UIDs are immutable.
    owner.check_server()
    target = parse_devices(owner.capture([str(ADB), '-H', '127.0.0.1', '-P', '5037', 'devices', '-l'], 'devices'), owner.target['serial'])
    owner.check_server()
    assert target == owner.target
    assert text(owner.adb(['get-state'], 'state', cap=128)) == 'device\n'
    require_user_zero(owner)
    props = {}
    for line in text(owner.shell(PROPERTIES, 'properties', cap=8192)).splitlines():
        key, sep, value = line.partition('='); assert sep and key in IDENTITY and key not in props
        props[key] = value
    assert set(props) == set(IDENTITY) and props['ro.kernel.qemu'] in ('', '0')
    assert len(props['ro.build.fingerprint']) <= 512 and props['ro.build.fingerprint']
    current = package_snapshot(owner)
    validate_packages(current, baseline, installed)
    rows = process_rows(owner.shell(PS, 'processes'), {k: current[k]['uid'] for k in (APP, TEST) if k in current})
    memory = {}
    for line in text(owner.shell(MEMORY, 'memory', cap=4096)).splitlines():
        m = re.fullmatch(r'(MemTotal|MemAvailable):\s+([0-9]+) kB', line); assert m and m[1] not in memory
        memory[m[1]] = int(m[2])*1024
    assert set(memory) == {'MemTotal', 'MemAvailable'}
    free = re.fullmatch(r'([0-9]+)\|([0-9]+)\n', text(owner.shell(SPACE, 'storage', cap=128)))
    assert free; available = integer(int(free[1]))*integer(int(free[2]), 1)
    integer(available)
    battery = {}
    for line in text(owner.shell(POWER, 'battery')).splitlines():
        key, sep, value = line.strip().partition(': ')
        if sep and key in ('USB powered', 'level', 'scale', 'temperature'):
            assert key not in battery; battery[key] = value
    assert set(battery) == {'USB powered', 'level', 'scale', 'temperature'} and battery['USB powered'] in ('true', 'false')
    thermal = re.findall(r'^Thermal Status: ([0-6])\s*$', text(owner.shell(THERMAL, 'thermal')), re.M)
    assert len(thermal) == 1
    sample = {'version': 1, 'authorized': True, 'physical': True, 'model': props['ro.product.model'],
        'api': int(props['ro.build.version.sdk']), 'soc_model': props['ro.soc.model'], 'board_platform': props['ro.board.platform'],
        'abis': props['ro.product.cpu.abilist'].split(','), 'page_bytes': int(text(owner.shell(PAGE, 'page', cap=128))),
        'memory_total_bytes': memory['MemTotal'], 'memory_available_bytes': memory['MemAvailable'], 'internal_free_bytes': available,
        'battery_level': int(battery['level']), 'battery_scale': int(battery['scale']), 'usb_powered': battery['USB powered'] == 'true',
        'temperature_tenths_celsius': int(battery['temperature']), 'thermal_status': int(thermal[0]),
        'new_app_absent': APP not in current, 'new_test_absent': TEST not in current, 'prior_pair_unchanged': True}
    return {'version': 1, 'target': target, 'current_user': 0, 'properties': props, 'packages': current, 'processes': rows, 'sample': sample}


def require_user_zero(owner):
    assert text(owner.shell(CURRENT_USER, 'current-user', cap=128), 128) == '0\n'


def resources(facts, *, installed, missing, initial=True):
    sample = facts['sample']; report = contract.assess(sample)
    # assess is preinstall-only; installed names are expected, never falsified.
    # The pure contract's storage gate accounts for two still-missing copies.
    # After staging/import only the actual remaining-copy requirement applies.
    allowed = {'namespace_collision', 'storage_capacity'} if installed else set()
    if not initial: allowed.add('memory_capacity')
    assert set(report['reasons']) <= allowed
    assert ('namespace_collision' in report['reasons']) is installed
    assert sample['new_app_absent'] is (not installed) and sample['new_test_absent'] is (not installed)
    assert sample['internal_free_bytes'] >= integer(missing) + contract.SHARED_RESERVE_BYTES


def discover(identity_path, evidence):
    configure_tools()
    root = Path(evidence); plain_path(root.parent, directory=True); root.mkdir(exist_ok=False)
    owner = Capture(root / 'discovery', 165)
    try:
        ident = load(identity_path)
        assert ident['state'] == 'device'; serial = ident['serial']
        owner.adb_sha = file_hash(ADB, 64*1024**2)
        assert file_hash(POWERSHELL, 64*1024**2)
        owner.check_server()
        raw = owner.capture([str(ADB), '-H', '127.0.0.1', '-P', '5037', 'devices', '-l'], 'devices')
        owner.check_server(); owner.target = parse_devices(raw, serial)
        if owner.target is None:
            value = {'version': 1, 'scope': SCOPE, 'status': 'absent', 'target_calls': 0, 'clients_cleaned': owner.clean}
        else:
            require_user_zero(owner)
            baseline = package_snapshot(owner)
            assert APP not in baseline and TEST not in baseline
            facts = observe(owner, baseline, False); resources(facts, installed=False, missing=2*contract.MODEL_BYTES)
            value = {'version': 1, 'scope': SCOPE, 'status': 'observed', 'identity_sha256': file_hash(identity_path, 65536),
                'adb_path': str(ADB), 'powershell_path': str(POWERSHELL), 'server': owner.server, 'target': owner.target, 'facts': facts, 'clients_cleaned': owner.clean}
    except BaseException:
        value = {'version': 1, 'scope': SCOPE, 'status': 'refused', 'clients_cleaned': owner.clean}
    write(root / 'discovery-v1.json', value)
    print(json.dumps({'status': value['status'], 'scope': SCOPE, 'clients_cleaned': owner.clean}))
    return value


def ready_pins():
    assert type(APK_HASHES) is dict and set(APK_HASHES) == {APP, TEST}
    for h in APK_HASHES.values(): digest(h)


def validate_proposal(v):
    configure_tools()
    assert type(v) is dict and set(v) == PROPOSAL_KEYS and type(v['version']) is int and v['version'] == 1
    assert v['scope'] == SCOPE and v['phase'] in ('precheck', 'model')
    ready_pins()
    for name in ('identity_path', 'discovery_path', 'evidence_root'):
        assert type(v[name]) is str and Path(v[name]).is_absolute() and '..' not in Path(v[name]).parts
    destination = Path(v['evidence_root'])
    plain_path(destination if destination.exists() else destination.parent, directory=True)
    for field in ('identity', 'discovery'):
        assert file_hash(v[field+'_path'], 1024**2) == digest(v[field+'_sha256'])
    assert file_hash(ADB, 64*1024**2) == digest(v['adb_sha256'])
    assert file_hash(POWERSHELL, 64*1024**2) == digest(v['powershell_sha256'])
    assert type(v['adb_path']) is str and Path(v['adb_path']).is_absolute() and Path(v['adb_path']).resolve() == ADB
    assert type(v['powershell_path']) is str and Path(v['powershell_path']).is_absolute() and Path(v['powershell_path']).resolve() == POWERSHELL
    d = load(v['discovery_path'])
    assert set(d) == {'version', 'scope', 'status', 'identity_sha256', 'adb_path', 'powershell_path', 'server', 'target', 'facts', 'clients_cleaned'}
    assert type(d['version']) is int and d['version'] == 1 and d['status'] == 'observed' and d['scope'] == SCOPE and d['clients_cleaned'] is True
    assert d['identity_sha256'] == v['identity_sha256'] and d['server']['adb_sha256'] == v['adb_sha256']
    assert parse_server(json.dumps({k: x for k, x in d['server'].items() if k != 'adb_sha256'}).encode(), v['adb_sha256']) == d['server']
    assert d['facts']['target'] == d['target']
    assert (d['adb_path'], d['powershell_path']) == (v['adb_path'], v['powershell_path'])
    assert type(d['facts']['current_user']) is int and d['facts']['current_user'] == 0
    assert d['target']['serial'] == load(v['identity_path'])['serial']
    validate_packages(d['facts']['packages'], d['facts']['packages'], False)
    resources(d['facts'], installed=False, missing=2*contract.MODEL_BYTES)
    assert set(v['apk_paths']) == {APP, TEST}
    for package, path in v['apk_paths'].items():
        assert type(path) is str and Path(path).is_absolute() and '..' not in Path(path).parts
        assert file_hash(path, 1024**3) == APK_HASHES[package]
    assert type(v['bindings']) is dict
    for name in SOURCE_FILES:
        p = str((ROOT/name).resolve()); assert p in v['bindings'] and file_hash(p, 16*1024**2) == digest(v['bindings'][p])
    for p, h in v['bindings'].items(): assert file_hash(p, 16*1024**2) == digest(h)
    source = v['source']; assert type(source) is dict and set(source) == {'path', 'bytes', 'sha256'}
    expected = (PROBE_BYTES, PROBE_SHA) if v['phase'] == 'precheck' else (contract.MODEL_BYTES, contract.MODEL_SHA256)
    assert type(source['bytes']) is int and (source['bytes'], source['sha256']) == expected
    assert type(source['path']) is str and Path(source['path']).is_absolute() and '..' not in Path(source['path']).parts
    p = plain_path(source['path'], directory=False); assert p.stat().st_size == expected[0]
    if v['phase'] == 'precheck':
        assert p.resolve() == PROBE_PATH.resolve() and v['prior'] is None
    else:
        prior = v['prior']; assert type(prior) is dict and set(prior) == {'proof_path', 'proof_sha256', 'facts_path', 'facts_sha256', 'result_path', 'result_sha256'}
        for kind in ('proof', 'facts', 'result'): assert file_hash(prior[kind+'_path'], 1024**2) == digest(prior[kind+'_sha256'])
        result = load(prior['result_path'])
        assert set(result) == {'version', 'scope', 'phase', 'status', 'clients_cleaned', 'stage', 'command_count', 'methods', 'installs', 'result'}
        assert type(result['version']) is int and result['version'] == 1 and result['status'] == 'observed' and result['clients_cleaned'] is True and result['scope'] == SCOPE and result['phase'] == 'precheck'
        assert type(result['methods']) is int and result['methods'] == 1 and type(result['installs']) is int and result['installs'] == 2
        integer(result['command_count'], 1); assert result['stage'] == 'boundary'
        facts = load(prior['facts_path']); proof = parse_proof(Path(prior['proof_path']).read_bytes(), 'PRECHECK', facts['packages'][APP]['uid'])
        validate_packages(facts['packages'], d['facts']['packages'], True)
        assert facts['processes'] == [] and facts['target'] == d['target']
        assert type(facts['current_user']) is int and facts['current_user'] == 0
        assert facts['properties'] == d['facts']['properties']
        resources(facts, installed=True, missing=2*contract.MODEL_BYTES)
        assert facts['packages'][APP]['sha256'] == APK_HASHES[APP] and facts['packages'][TEST]['sha256'] == APK_HASHES[TEST]
        assert proof['process'] == APP
        assert result['result'] == {'proof': proof, 'proof_sha256': prior['proof_sha256']}
    return v


def authorize(proposal_path, authorization_path, evidence):
    raw = Path(proposal_path).read_bytes(); v = q.contract.strict_json(raw); auth = load(authorization_path)
    assert type(auth) is dict and set(auth) == {'version', 'proposal_sha256', 'allow_device_calls', 'allow_new_install', 'allow_model_copy', 'allow_sdk', 'root_go_pending'}
    assert type(auth['version']) is int and auth['version'] == 1 and auth['proposal_sha256'] == sha(raw)
    assert auth['allow_device_calls'] is True and auth['root_go_pending'] is False
    assert auth['allow_new_install'] is (v['phase'] == 'precheck')
    assert auth['allow_model_copy'] is (v['phase'] == 'model') and auth['allow_sdk'] is (v['phase'] == 'model')
    assert Path(v['evidence_root']).resolve() == Path(evidence).resolve()
    return validate_proposal(v)


def selection(phase):
    assert phase in PHASES
    return ('am', 'instrument', '--user', '0', '-w', '-r', '-e', 'class', 'org.locallore.app.'+PHASES[phase][1], TEST+'/androidx.test.runner.AndroidJUnitRunner')


def parse_runner(raw, phase):
    assert phase in PHASES
    return q._parse_selected_instrumentation(raw, 'org.locallore.app.'+PHASES[phase][1], frozenset((PHASES[phase][2],)), phase_budget_ms=PHASES[phase][3])


def parse_proof(raw, phase, uid):
    assert phase in PHASES and type(raw) is bytes and 0 < len(raw) <= 4096
    integer(uid, 10000, 2**31-1); v = q.contract.strict_json(raw)
    extra = set() if phase == 'PRECHECK' else {'prior_pid', 'prior_start', 'prior_proof_sha256'}
    if phase in ('CANCEL', 'GIFT', 'DIALOGUE', 'REOPEN'):
        extra |= {'revision', 'receipt_count', 'receipts_sha256', 'story_sha256', 'worker_trace_sha256'}
    if phase == 'CANCEL': extra |= {'sample_trace_sha256'}
    if phase in ('GIFT', 'DIALOGUE'): extra |= {'repairs', 'fallback'}
    if phase in ('GIFT', 'DIALOGUE', 'REOPEN'): extra |= {'gift_receipt_sha256'}
    if phase in ('DIALOGUE', 'REOPEN'): extra |= {'dialogue_receipt_sha256'}
    if phase == 'DIALOGUE': extra |= {'guards_trace_sha256'}
    assert type(v) is dict and set(v) == COMMON_KEYS | extra
    assert type(v['version']) is int and v['version'] == 1 and v['scope'] == PROOF_SCOPE and v['profile'] == contract.PROFILE and v['phase'] == phase
    integer(v['pid'], 1, 2**31-1); integer(v['start'], 1)
    assert type(v['uid']) is int and v['uid'] == uid and v['process'] == APP
    assert type(v['model_bytes']) is int and v['model_bytes'] == contract.MODEL_BYTES and v['model_sha256'] == contract.MODEL_SHA256
    integer(v['elapsed_ms'], 0, PHASES[phase][3]); total = integer(v['memory_total_bytes'], 10*contract.GIB, 12*contract.GIB)
    integer(v['memory_available_before'], 4*contract.GIB, total); integer(v['memory_available_after'], 0, total)
    assert v['low_memory_before'] is False and v['low_memory_after'] is False
    integer(v['shared_free_before'], contract.REQUIRED_INTERNAL_FREE_BYTES if phase == 'PRECHECK' else contract.SHARED_RESERVE_BYTES)
    integer(v['shared_free_after'], contract.SHARED_RESERVE_BYTES)
    for kind in ('verify', 'import'):
        for suffix in ('opened', 'closed', 'bytes'):
            expected = (contract.MODEL_BYTES if suffix == 'bytes' else 1) if phase == 'IMPORT' else 0
            assert type(v['source_'+kind+'_'+suffix]) is int and v['source_'+kind+'_'+suffix] == expected
    assert v['sdk_invoked'] is (phase in ('CANCEL', 'GIFT', 'DIALOGUE')) and v['publication_native_invoked'] is False
    assert type(v['checks']) is dict and set(v['checks']) == PHASES[phase][4] and all(x is True for x in v['checks'].values())
    for key in extra:
        if key.endswith('_sha256'): digest(v[key])
    if phase != 'PRECHECK': integer(v['prior_pid'], 1, 2**31-1); integer(v['prior_start'], 1)
    if 'revision' in extra:
        rev = 0 if phase == 'CANCEL' else 1 if phase == 'GIFT' else 2
        assert type(v['revision']) is int and type(v['receipt_count']) is int and v['revision'] == v['receipt_count'] == rev
    if phase in ('GIFT', 'DIALOGUE'): assert type(v['repairs']) is int and v['repairs'] == 0 and v['fallback'] is False
    return v


def link_proofs(prior, prior_raw, current):
    index = ORDER.index(current['phase']); assert index > 0
    assert load_bytes(prior_raw) == prior and prior['phase'] == ORDER[index-1]
    assert (current['prior_pid'], current['prior_start'], current['prior_proof_sha256']) == (prior['pid'], prior['start'], sha(prior_raw))
    assert current['uid'] == prior['uid'] and (current['pid'], current['start']) != (prior['pid'], prior['start'])
    if current['phase'] in ('GIFT', 'DIALOGUE', 'REOPEN'): assert current['story_sha256'] == prior['story_sha256']
    if current['phase'] in ('DIALOGUE', 'REOPEN'): assert current['gift_receipt_sha256'] == prior['gift_receipt_sha256']
    if current['phase'] == 'REOPEN':
        assert current['receipts_sha256'] == prior['receipts_sha256'] and current['dialogue_receipt_sha256'] == prior['dialogue_receipt_sha256']


def load_bytes(raw):
    return q.contract.strict_json(raw)


def zero_trace(v):
    assert v['version'] == 2 and v['saturated'] == [] and v['time_saturated'] is False and v['creations_saturated'] is False
    assert v['creations_total'] == 0 and v['creations'] == [] and all(n == 0 for n in v['counts'].values()) and all(n is None for n in v['last_ms'].values())


def trace_predicates(v, phase, prior=None):
    if phase in ('GUARDS', 'REOPEN'): zero_trace(v)
    elif phase == 'CANCEL_SAMPLE': cancellation.trace_predicates(v, 'SAMPLE')
    elif phase == 'CANCEL': cancellation.trace_predicates(v, 'CANCEL', prior)
    else:
        assert phase in ('GIFT', 'DIALOGUE'); cancellation.trace_predicates(v, 'RECOVER')
        if phase == 'DIALOGUE':
            assert prior is not None and v['snapshot_ms'] >= prior['snapshot_ms']
            for event in worker.EVENTS:
                assert v['counts'][event] >= prior['counts'][event]
                if prior['last_ms'][event] is not None: assert v['last_ms'][event] is not None and v['last_ms'][event] >= prior['last_ms'][event]


def source_command(uid, action):
    integer(uid, 10000, 2**31-1); assert action in ('create', 'probe', 'model')
    prefix = 'umask 077; export LC_ALL=C; test $(id -u) -eq '+str(uid)+' && '
    if action == 'create':
        prefix += 'if test -e no_backup || test -L no_backup; then test -d no_backup && test ! -L no_backup && test $(stat -c %u no_backup) -eq '+str(uid)+'; else mkdir no_backup; fi && '
        script = prefix+'test ! -e '+SOURCE_ROOT+' && test ! -L '+SOURCE_ROOT+' && mkdir '+SOURCE_ROOT+' && set -C && printf '+shlex.quote(OWNER_BYTES.decode())+' > '+SOURCE_ROOT+'/source.owner'
    else:
        leaf = 'probe.txt' if action == 'probe' else 'model.litertlm'
        prefix += 'test -d no_backup && test ! -L no_backup && test $(stat -c %u no_backup) -eq '+str(uid)+' && test -d '+SOURCE_ROOT+' && test ! -L '+SOURCE_ROOT+' && test $(stat -c %u '+SOURCE_ROOT+') -eq '+str(uid)+' && '
        marker = SOURCE_ROOT+'/source.owner'
        prefix += 'test -f '+marker+' && test ! -L '+marker+' && test $(stat -c %u '+marker+') -eq '+str(uid)+' && test $(stat -c %h '+marker+') -eq 1 && test $(wc -c < '+marker+') -eq 29 && test "$(sha256sum '+marker+')" = "'+OWNER_SHA+'  '+marker+'" && '
        path = SOURCE_ROOT+'/'+leaf
        script = prefix+'test ! -e '+path+' && test ! -L '+path+' && set -C && cat > '+path
    return ('run-as', APP, '--user', '0', 'sh', '-c', script)


def manifest_command(uid, absent=False):
    integer(uid, 10000, 2**31-1); assert type(absent) is bool
    script = 'test -d no_backup && test ! -L no_backup && test $(stat -c %u no_backup) -eq '+str(uid)+' && '
    if absent: script += 'test ! -e '+PROOF_ROOT+' && test ! -L '+PROOF_ROOT
    else: script += 'test -d '+PROOF_ROOT+' && test ! -L '+PROOF_ROOT+' && test $(stat -c %u '+PROOF_ROOT+') -eq '+str(uid)+' && find '+PROOF_ROOT+' -mindepth 1 -maxdepth 1 -print'
    return ('run-as', APP, '--user', '0', 'sh', '-c', script)


def proof_command(uid, name):
    allowed = {PHASES[p][0]+s for p in PHASES for s in ('-v1.json', '-ready-v1.txt')} | {n for ns in TRACES.values() for n in ns}
    integer(uid, 10000, 2**31-1); assert name in allowed
    path = PROOF_ROOT+'/'+name
    script = 'test -d no_backup && test ! -L no_backup && test $(stat -c %u no_backup) -eq '+str(uid)+' && test -d '+PROOF_ROOT+' && test ! -L '+PROOF_ROOT+' && test $(stat -c %u '+PROOF_ROOT+') -eq '+str(uid)
    script += ' && test -f '+path+' && test ! -L '+path+' && test $(stat -c %u '+path+') -eq '+str(uid)+' && test $(stat -c %h '+path+') -eq 1 && test $(wc -c < '+path+') '+('-eq 0' if name.endswith('-ready-v1.txt') else '-gt 0')+' && test $(wc -c < '+path+') -le 4096 && cat '+path
    return ('run-as', APP, '--user', '0', 'sh', '-c', script)


class Owner(Capture):
    def __init__(self, proposal, evidence):
        configure_tools()
        ready_pins(); self.proposal = proposal; self.root = Path(evidence)
        super().__init__(self.root/'cohort', 165 if proposal['phase'] == 'precheck' else 1170)
        d = load(proposal['discovery_path']); self.server = d['server']; self.target = d['target']; self.adb_sha = proposal['adb_sha256']
        self.baseline = d['facts']['packages']; self.fingerprint = d['facts']['properties']['ro.build.fingerprint']
        self.methods = 0; self.stage = 'admission'; self.installs = 0; self.last_pass = None; self.uids = None

    def adb(self, operation, label, seconds=15, cap=131072):
        assert self.clean
        try:
            op = tuple(shlex.split(operation[1])) if len(operation) == 2 and operation[0] == 'shell' else ()
            if operation[0] == 'install' or op[:2] in (('am', 'instrument'), ('am', 'force-stop')) or op[:1] == ('run-as',):
                # Never target the active user's namespace by default. This
                # check is repeated immediately before each such dispatch.
                raw = super().adb(['shell', shlex.join(CURRENT_USER)], 'mutation-user', cap=128)
                assert text(raw, 128) == '0\n'
            return super().adb(operation, label, seconds, cap)
        except BaseException: self.clean = False; raise

    def facts(self, label, missing=0, *, initial=True):
        assert self.clean
        try:
            installed = self.proposal['phase'] == 'model' or self.installs == 2
            v = observe(self, self.baseline, installed)
            assert v['properties']['ro.build.fingerprint'] == self.fingerprint
            resources(v, installed=installed, missing=missing, initial=initial)
            if installed:
                uids = {p: v['packages'][p]['uid'] for p in (APP, TEST)}
                if self.uids is None: self.uids = uids
                assert self.uids == uids
            assert v['processes'] == []
            write(self.directory/(label+'-facts.json'), v)
            return v
        except BaseException: self.clean = False; raise

    def install(self):
        assert self.clean and self.stage == 'admission' and self.proposal['phase'] == 'precheck' and self.installs == 0
        try:
            sizes = sum(Path(self.proposal['apk_paths'][p]).stat().st_size for p in (APP, TEST))
            self.facts('before-install', 2*contract.MODEL_BYTES+sizes)
            for package in (APP, TEST):
                path = self.proposal['apk_paths'][package]
                assert file_hash(path, 1024**3) == APK_HASHES[package]
                self.installs += 1
                output = self.adb(['install', '--no-streaming', '--user', '0', path], 'install', seconds=60, cap=4096)
                assert text(output, 4096) in ('Success\n', 'Performing Push Install\nSuccess\n')
            self.stage = 'installed'; self.facts('installed', 2*contract.MODEL_BYTES)
        except BaseException: self.clean = False; raise

    def stop_between(self):
        assert self.clean and self.last_pass is not None and self.stage == 'passed'
        try:
            for package in (APP, TEST): assert self.shell(('am', 'force-stop', '--user', '0', package), 'owned-phase-stop', cap=4096) == b''
            rows = process_rows(self.shell(PS, 'owned-phase-absence'), self.uids)
            assert rows == []
            self.stage = 'boundary'
        except BaseException: self.clean = False; raise

    def transfer(self, proposal_path, authorization_path):
        assert self.clean and self.uids and self.stage in ('installed', 'boundary')
        try:
            model = self.proposal['phase'] == 'model'
            self.facts('before-stream', 2*contract.MODEL_BYTES if model else 2*contract.MODEL_BYTES)
            remaining = self.until-time.monotonic(); budget = min(240 if model else 90, int(remaining))
            assert budget >= 6
            parent = {'version': 1, 'parent': environment.process_identity(os.getpid()), 'proposal_sha256': sha(Path(proposal_path).read_bytes()),
                'authorization_sha256': sha(Path(authorization_path).read_bytes()), 'deadline_epoch': time.time()+budget,
                'uid': self.uids[APP], 'facts_sha256': sha((self.directory/'before-stream-facts.json').read_bytes())}
            write(self.directory/'stream-parent-v1.json', parent)
            driver = self.directory/'stream-driver'; driver.mkdir()
            result = environment.supervise([sys.executable, '-B', '-E', str(SCRIPT), '_stream', '--proposal', str(proposal_path), '--authorization', str(authorization_path), '--evidence', str(self.root)], STREAM_REQUEST, driver, budget, lambda child: True)
            write(self.directory/'stream-result-v1.json', result)
            assert result['cleanup_complete'] is True and result['output_capture_complete'] is True and result['status'] == 'child_exited'
            assert type(result['worker_returncode']) is int and result['worker_returncode'] == 0 and result['stderr_bytes'] == 0
            integer(result['stdout_bytes'], 1, 4096)
            raw = (driver/'owner-stdout-v1.bin').read_bytes(); assert len(raw) == result['stdout_bytes']
            v = load_bytes(raw)
            assert set(v) == {'version', 'source_bytes', 'source_verified', 'client_returncode', 'remote_exit_status_known', 'destination_verified'}
            assert type(v['version']) is int and v['version'] == 1 and type(v['source_bytes']) is int and v['source_bytes'] == self.proposal['source']['bytes']
            assert v['source_verified'] is True and type(v['client_returncode']) is int and v['client_returncode'] == 0
            assert v['remote_exit_status_known'] is False and v['destination_verified'] is False
            self.check_server(); return v
        except BaseException: self.clean = False; raise


def read_phase(owner, phase):
    uid = owner.uids[APP]
    names = set()
    for p in ORDER[:ORDER.index(phase)+1]:
        names |= {PHASES[p][0]+'-v1.json', PHASES[p][0]+'-ready-v1.txt', *TRACES[p]}
    raw = owner.shell(manifest_command(uid), 'proof-manifest', cap=8192)
    lines = text(raw, 8192).splitlines(); assert len(lines) == len(names) and set(lines) == {PROOF_ROOT+'/'+n for n in names}
    stem = PHASES[phase][0]
    assert owner.shell(proof_command(uid, stem+'-ready-v1.txt'), 'proof-ready', cap=4096) == b''
    raw = owner.shell(proof_command(uid, stem+'-v1.json'), 'proof-json', cap=4096)
    raw_write(owner.directory/(stem+'-proof.raw.json'), raw); v = parse_proof(raw, phase, uid)
    previous = None
    for index, name in enumerate(TRACES[phase]):
        data = owner.shell(proof_command(uid, name), 'worker-json', cap=4096)
        raw_write(owner.directory/(name+'.raw'), data)
        key = 'sample_trace_sha256' if phase == 'CANCEL' and index == 0 else 'guards_trace_sha256' if phase == 'DIALOGUE' and index == 0 else 'worker_trace_sha256'
        assert sha(data) == v[key]
        trace = worker.parse_worker_trace(data)
        trace_predicates(trace, 'CANCEL_SAMPLE' if phase == 'CANCEL' and index == 0 else 'GUARDS' if phase == 'DIALOGUE' and index == 0 else phase, previous)
        write(owner.directory/name, trace); previous = trace
    write(owner.directory/(stem+'-proof-v1.json'), v)
    return v, raw


def run_selected(owner, phase):
    assert owner.clean and phase in ORDER
    try:
        owner.facts('before-'+PHASES[phase][0], 0)
        owner.stage = 'instrument-'+phase; owner.methods += 1
        raw = owner.shell(selection(phase), 'instrument-'+phase, seconds=180, cap=131072)
        # Passive failure channels cannot grant a passed runner or proof.
        for parser, label in ((status_trace.extract_status_trace, 'status'), (callback.extract_callback_trace, 'callback'), (send.extract_send_trace, 'send'), (worker.extract_worker_trace, 'worker')):
            observation = parser(raw)
            if observation is not None: write(owner.directory/(PHASES[phase][0]+'-failure-'+label+'.json'), observation)
        result = parse_runner(raw, phase); write(owner.directory/(PHASES[phase][0]+'-runner-v1.json'), result)
        value, data = read_phase(owner, phase)
        owner.stage = 'passed'; owner.last_pass = phase
        return value, data
    except BaseException: owner.clean = False; raise


def run_cohort(owner, proposal_path, authorization_path):
    if owner.proposal['phase'] == 'precheck':
        owner.install()
        assert owner.shell(manifest_command(owner.uids[APP], True), 'proof-absent', cap=4096) == b''
        assert owner.shell(source_command(owner.uids[APP], 'create'), 'source-create', cap=4096) == b''
        owner.transfer(proposal_path, authorization_path)
        proof, raw = run_selected(owner, 'PRECHECK')
        owner.stop_between(); owner.facts('final', 2*contract.MODEL_BYTES)
        return {'proof': proof, 'proof_sha256': sha(raw)}
    prior = owner.proposal['prior']; prior_raw = Path(prior['proof_path']).read_bytes()
    previous = parse_proof(prior_raw, 'PRECHECK', load(prior['facts_path'])['packages'][APP]['uid'])
    facts = owner.facts('continued-before', 2*contract.MODEL_BYTES)
    assert facts['packages'] == load(prior['facts_path'])['packages']
    owner.stage = 'boundary'; owner.transfer(proposal_path, authorization_path)
    proofs = {}
    for phase in ORDER[1:]:
        current, raw = run_selected(owner, phase); link_proofs(previous, prior_raw, current)
        owner.stop_between(); owner.facts('after-'+PHASES[phase][0], 0, initial=False)
        proofs[phase] = current; previous, prior_raw = current, raw
    return {'proofs': proofs}


def stream_worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(128) == STREAM_REQUEST
    v = authorize(proposal_path, authorization_path, evidence)
    parent_path = Path(evidence)/'cohort/stream-parent-v1.json'; parent = load(parent_path)
    assert set(parent) == {'version', 'parent', 'proposal_sha256', 'authorization_sha256', 'deadline_epoch', 'uid', 'facts_sha256'}
    assert type(parent['version']) is int and parent['version'] == 1
    assert parent['parent'] == environment.process_identity(os.getppid()) and parent['parent']['executable'].lower() == str(Path(sys.executable)).lower()
    assert parent['proposal_sha256'] == sha(Path(proposal_path).read_bytes()) and parent['authorization_sha256'] == sha(Path(authorization_path).read_bytes())
    assert type(parent['deadline_epoch']) in (int, float) and 0 < parent['deadline_epoch']-time.time() <= (240 if v['phase']=='model' else 90)
    uid = integer(parent['uid'], 10000, 2**31-1)
    facts_path = Path(evidence)/'cohort/before-stream-facts.json'; assert sha(facts_path.read_bytes()) == parent['facts_sha256']
    facts = load(facts_path); assert facts['packages'][APP]['uid'] == uid and facts['processes'] == []
    owner = Capture(Path(evidence)/'cohort/stream-clients', max(1, parent['deadline_epoch']-time.time()))
    d = load(v['discovery_path']); owner.server = d['server']; owner.target = d['target']; owner.adb_sha = v['adb_sha256']
    write(Path(evidence)/'cohort/stream-claimed-v1.json', {'version': 1, 'parent_sha256': sha(parent_path.read_bytes()), 'worker': environment.process_identity(os.getpid())})
    assert owner.target == facts['target']; owner.check_server()
    def recheck():
        owner.check_server()
        current = parse_devices(owner.capture([str(ADB), '-H', '127.0.0.1', '-P', '5037', 'devices', '-l'], 'stream-devices'), owner.target['serial'])
        owner.check_server()
        assert current == owner.target
        assert text(owner.adb(['get-state'], 'stream-state', cap=128)) == 'device\n'
        require_user_zero(owner)
        assert text(owner.shell(PROPERTIES, 'stream-properties', cap=8192)) == ''.join(k+'='+facts['properties'][k]+'\n' for k in IDENTITY)
        assert text(owner.shell(PAGE, 'stream-page', cap=128)) == '4096\n'
    recheck()
    source = Path(v['source']['path'])
    plain_path(source, directory=False)
    path_before = source.lstat(); assert stat.S_ISREG(path_before.st_mode) and not source.is_symlink()
    with source.open('rb', buffering=0) as handle:
        before = os.fstat(handle.fileno()); assert stat.S_ISREG(before.st_mode) and before.st_size == v['source']['bytes']
        assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (path_before.st_dev, path_before.st_ino, path_before.st_size, path_before.st_mtime_ns)
        h = hashlib.sha256()
        remaining_bytes = v['source']['bytes']
        while remaining_bytes:
            block = handle.read(min(1024*1024, remaining_bytes)); assert block
            h.update(block); remaining_bytes -= len(block)
        assert handle.read(1) == b''
        assert h.hexdigest() == v['source']['sha256']; handle.seek(0)
        recheck()
        # The held source is verified, but APP/TEST, UID and resources may have
        # changed during the hash. Reobserve before the first weight byte.
        fresh = observe(owner, d['facts']['packages'], True)
        assert type(fresh['current_user']) is int and fresh['current_user'] == 0
        assert fresh['packages'] == facts['packages'] and fresh['target'] == facts['target'] and fresh['properties'] == facts['properties']
        assert fresh['processes'] == [] and fresh['sample']['memory_total_bytes'] == facts['sample']['memory_total_bytes']
        resources(fresh, installed=True, missing=2*contract.MODEL_BYTES)
        assert parent['parent'] == environment.process_identity(os.getppid())
        timeout = min(150, parent['deadline_epoch']-time.time()-5); assert timeout > 0
        argv = [str(ADB), '-H', '127.0.0.1', '-P', '5037', '-t', str(owner.target['transport_id']), 'exec-in', shlex.join(source_command(uid, 'model' if v['phase']=='model' else 'probe'))]
        result = subprocess.run(argv, stdin=handle, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
        assert type(result.returncode) is int and result.returncode == 0
        after = os.fstat(handle.fileno())
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    plain_path(source, directory=False)
    path_after = source.lstat(); assert stat.S_ISREG(path_after.st_mode) and not source.is_symlink()
    assert (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) == (path_after.st_dev, path_after.st_ino, path_after.st_size, path_after.st_mtime_ns)
    assert type(result.returncode) is int and result.returncode == 0
    assert parent['parent'] == environment.process_identity(os.getppid()); owner.check_server()
    recheck()
    print(json.dumps({'version': 1, 'source_bytes': before.st_size, 'source_verified': True, 'client_returncode': 0, 'remote_exit_status_known': False, 'destination_verified': False}))
    return 0


def worker_main(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(128) == REQUEST
    v = authorize(proposal_path, authorization_path, evidence)
    parent = load(Path(evidence)/'owned-start-v1.json')
    assert set(parent) == {'version', 'seconds', 'parent', 'deadline_epoch', 'proposal_sha256', 'authorization_sha256'}
    assert type(parent['version']) is int and parent['version'] == 1
    assert type(parent['seconds']) is int and parent['seconds'] == (180 if v['phase'] == 'precheck' else 1200)
    assert parent['parent'] == environment.process_identity(os.getppid())
    assert parent['parent']['executable'].lower() == str(Path(sys.executable)).lower()
    assert type(parent['deadline_epoch']) in (int, float) and 0 < parent['deadline_epoch']-time.time() <= parent['seconds']
    assert parent['proposal_sha256'] == sha(Path(proposal_path).read_bytes()) and parent['authorization_sha256'] == sha(Path(authorization_path).read_bytes())
    write(Path(evidence)/'worker-claimed-v1.json', {'version': 1, 'proposal_sha256': sha(Path(proposal_path).read_bytes()), 'worker': environment.process_identity(os.getpid())})
    owner = Owner(v, evidence); result = None
    try: result = run_cohort(owner, proposal_path, authorization_path)
    except BaseException: owner.clean = False
    value = {'version': 1, 'scope': SCOPE, 'phase': v['phase'], 'status': 'observed' if owner.clean else 'stopped',
        'clients_cleaned': owner.clean, 'stage': owner.stage, 'command_count': owner.count, 'methods': owner.methods, 'installs': owner.installs, 'result': result}
    write(owner.directory/'result-v1.json', value)
    print(json.dumps({k: value[k] for k in value if k != 'result'}))
    return 0 if owner.clean else 2


def run_owned(proposal_path, authorization_path, evidence):
    v = authorize(proposal_path, authorization_path, evidence)
    root = Path(evidence); driver = root/'driver'; driver.mkdir(exist_ok=False)
    seconds = 180 if v['phase'] == 'precheck' else 1200
    write(root/'owned-start-v1.json', {'version': 1, 'seconds': seconds, 'parent': environment.process_identity(os.getpid()), 'deadline_epoch': time.time()+seconds,
        'proposal_sha256': sha(Path(proposal_path).read_bytes()), 'authorization_sha256': sha(Path(authorization_path).read_bytes())})
    result = environment.supervise([sys.executable, '-B', '-E', str(SCRIPT), 'worker', '--proposal', str(proposal_path), '--authorization', str(authorization_path), '--evidence', str(evidence)], REQUEST, driver, seconds, lambda child: True)
    write(root/'owned-result-v1.json', result); print(json.dumps(result))
    good = result['status'] == 'child_exited' and type(result['worker_returncode']) is int and result['worker_returncode'] == 0 and result['cleanup_complete'] is True and result['output_capture_complete'] is True
    if not good: return 2
    integer(result['stdout_bytes'], 1, 4096); assert type(result['stderr_bytes']) is int and result['stderr_bytes'] == 0
    raw = (driver/'owner-stdout-v1.bin').read_bytes(); assert len(raw) == result['stdout_bytes']
    validate_completion(v, root, raw)
    return 0


def validate_completion(proposal, root, raw):
    """Closed retained evidence qualifies completion; child0 alone never does."""
    assert type(raw) is bytes and 0 < len(raw) <= 4096
    summary = load_bytes(raw); cohort = Path(root)/'cohort'
    result_path = cohort/'result-v1.json'; assert 0 < result_path.stat().st_size <= 65536
    value = load(result_path)
    keys = {'version', 'scope', 'phase', 'status', 'clients_cleaned', 'stage', 'command_count', 'methods', 'installs'}
    assert type(summary) is dict and set(summary) == keys and type(value) is dict and set(value) == keys | {'result'}
    assert json.dumps(summary, sort_keys=True) == json.dumps({k: value[k] for k in keys}, sort_keys=True)
    assert type(summary['version']) is int and summary['version'] == 1 and summary['scope'] == SCOPE and summary['phase'] == proposal['phase']
    assert summary['status'] == 'observed' and summary['clients_cleaned'] is True and summary['stage'] == 'boundary'
    phases = ('PRECHECK',) if proposal['phase'] == 'precheck' else ORDER[1:]
    assert type(summary['methods']) is int and summary['methods'] == len(phases)
    assert type(summary['installs']) is int and summary['installs'] == (2 if proposal['phase']=='precheck' else 0)
    integer(summary['command_count'], len(phases), 4096)
    records = sorted(cohort.glob('command-*.json')); assert len(records) == summary['command_count']
    results = {}
    for path in records:
        record = load(path); raw_path = path.with_suffix('.stdout.bin'); data = raw_path.read_bytes()
        assert type(record['stdout_bytes']) is int and len(data) == record['stdout_bytes'] and sha(data) == record['stdout_sha256']
        assert record['status'] == 'completed' and record['cleanup_complete'] is True and type(record['returncode']) is int and record['returncode'] == 0
        assert type(record['stderr_bytes']) is int and record['stderr_bytes'] == 0
        if record['label'].startswith('instrument-'):
            phase = record['label'][len('instrument-'):]; assert phase in phases and phase not in results
            results[phase] = parse_runner(data, phase)
    assert set(results) == set(phases)
    facts = load(cohort/('final-facts.json' if proposal['phase']=='precheck' else 'after-reopen-facts.json'))
    d = load(proposal['discovery_path']); validate_packages(facts['packages'], d['facts']['packages'], True)
    assert facts['processes'] == [] and type(facts['current_user']) is int and facts['current_user'] == 0
    uid = facts['packages'][APP]['uid']; prior = prior_raw = None; proofs = {}
    if proposal['phase'] == 'model':
        prior_raw = Path(proposal['prior']['proof_path']).read_bytes(); prior = parse_proof(prior_raw, 'PRECHECK', uid)
    for phase in phases:
        stem = PHASES[phase][0]; proof_raw = (cohort/(stem+'-proof.raw.json')).read_bytes()
        proof = parse_proof(proof_raw, phase, uid)
        if prior is not None: link_proofs(prior, prior_raw, proof)
        trace_prior = None
        for i, name in enumerate(TRACES[phase]):
            data = (cohort/(name+'.raw')).read_bytes()
            key = 'sample_trace_sha256' if phase=='CANCEL' and i==0 else 'guards_trace_sha256' if phase=='DIALOGUE' and i==0 else 'worker_trace_sha256'
            assert sha(data) == proof[key]
            trace = worker.parse_worker_trace(data)
            trace_predicates(trace, 'CANCEL_SAMPLE' if phase=='CANCEL' and i==0 else 'GUARDS' if phase=='DIALOGUE' and i==0 else phase, trace_prior)
            trace_prior = trace
        proofs[phase] = proof; prior, prior_raw = proof, proof_raw
    expected = {'proof': proofs['PRECHECK'], 'proof_sha256': sha(prior_raw)} if proposal['phase']=='precheck' else {'proofs': proofs}
    assert json.dumps(value['result'], sort_keys=True) == json.dumps(expected, sort_keys=True)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('discover', 'run', 'worker', '_stream'))
    parser.add_argument('--identity', type=Path)
    for name in ('proposal', 'authorization', 'evidence'): parser.add_argument('--'+name, type=Path)
    args = parser.parse_args(argv)
    try:
        assert not sys.flags.optimize and args.evidence is not None
        assert not os.environ.get('ADB_SERVER_SOCKET') and not os.environ.get('ANDROID_ADB_SERVER_PORT')
        if args.action == 'discover':
            assert args.identity is not None and args.proposal is None and args.authorization is None
            return 0 if discover(args.identity, args.evidence)['status'] == 'observed' else 2
        assert args.identity is None and args.proposal is not None and args.authorization is not None
        return {'run': run_owned, 'worker': worker_main, '_stream': stream_worker}[args.action](args.proposal, args.authorization, args.evidence)
    except BaseException:
        print(json.dumps({'version': 1, 'scope': SCOPE, 'status': 'refused'})); return 2


if __name__ == '__main__':
    raise SystemExit(main())
