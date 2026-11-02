"""Bounded B83 fixture: real isolated recovery/storage history, mocked SDK/native ports.

All authority/authorization records are synthetic test data at unique paths.
They cannot be used by the fixed operational scripts without test-only patches.
"""
import copy
from contextlib import ExitStack
from dataclasses import replace
import os
from pathlib import Path, PureWindowsPath
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from benchmarks import isolated_adb_lease as base
from benchmarks import owned_library_ui_contract as profile
from benchmarks import prepare_recovery_contract as history
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_prepare_recovery as recovery
from benchmarks import receipt_avd_storage as storage
from scripts import library_ui_recovery_contract as rules
from scripts import library_ui_run_inputs as builder
from scripts import run_library_ui_recovery as operator
from scripts.tests import test_library_ui_controller_fixtures as wire_data
from scripts.tests import test_prepare_recovery_adversaries as recovery_data
from scripts.tests.test_library_ui_recovery_operator import synthetic_attempt, synthetic_authority

BASE = Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-operator-v1/test-agent-v1')
SOURCE = Path(__file__).resolve().parents[2]


def budget(extra=0):
    total = wire_data.meter(BASE)
    if total + extra > 128 * 1024 * 1024: raise RuntimeError('fixture_budget_refused')


class OwnedFiles:
    def __init__(self):
        budget(8 * 1024 * 1024)
        parent = BASE / 'controller'; parent.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix='metadata-', dir=parent))
    def write(self, path, raw):
        path = Path(path)
        if not path.is_relative_to(self.base): raise AssertionError('Foreign synthetic file')
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)


class BuilderFixture:
    """Readiness/proof boundaries are synthetic; journal, schemas and byte joins remain real."""
    def __init__(self, *, known=True, execute_recovery=True):
        self.known = known; self.execute_recovery = execute_recovery
        self.stack = ExitStack(); self.forbidden = []
    def __enter__(self):
        try: return self._open()
        except BaseException:
            self.stack.close()
            raise
    def _open(self):
        budget(8 * 1024 * 1024)
        parent = BASE / 'recovery'; parent.mkdir(parents=True, exist_ok=True)
        self.fixture = recovery_data.PrepareRecoveryAdversaries(methodName='runTest')
        self.stack.callback(self.fixture.doCleanups)
        original_temp = recovery_data.tempfile.TemporaryDirectory
        def isolated_temp(*args, **kwargs):
            kwargs['dir'] = parent; return original_temp(*args, **kwargs)
        with patch.object(recovery_data.tempfile, 'TemporaryDirectory', side_effect=isolated_temp):
            self.fixture.setUp()
        self.stack.enter_context(patch.object(wire_data, 'SyntheticFiles', OwnedFiles))
        self.stack.enter_context(patch.object(wire_data, 'FIXTURE_ROOT', BASE))
        self.stack.enter_context(patch.object(wire_data, 'OWN_FOLDERS', ('controller', 'recovery')))
        self.wire = wire_data.ControllerGraph()
        self.stack.enter_context(self.wire.inputs())
        f = self.fixture; self.root = f.base
        operator = self.root / 'operator'; (operator / 'scripts').mkdir(parents=True)
        execution = self.root / 'run-1'; runtime = self.root / 'runtime'; controls = self.root / 'controls'
        for name, value in dict(SOURCE=SOURCE, OPERATOR_ROOT=operator,
            OPERATOR=operator / 'scripts/run_library_ui_recovery.py', BUILDER=operator / 'scripts/library_ui_run_inputs.py',
            CONTRACT=operator / 'scripts/library_ui_recovery_contract.py', OUT=self.root, LIVE=self.root,
            EXECUTION=execution, AUTHORITY=self.root / 'synthetic-human-authority.json',
            PROPOSAL=self.root / 'SYNTHETIC_PROPOSAL.md', REGISTRY=f.registry, GUEST=f.root,
            RUNTIME=runtime, CONTROLS=controls, RUN_PROPOSAL=self.root / 'run-proposal-v1.json',
            RUN_AUTHORIZATION=self.root / 'run-authorization-v1.json',
            RECOVERY_AUTHORIZATION=self.root / 'recovery-authorization.json',
            RECOVERY_RESULT=execution / 'recovery-result-v1.json', ATTEMPT=self.root / 'attempt-v1.json',
            ADMISSION=runtime / 'admission-v1.json', INPUT=controls / 'run-input-v1.json').items():
            self.stack.enter_context(patch.object(rules, name, value))
        for path in (rules.OPERATOR, rules.BUILDER, rules.CONTRACT, rules.PROPOSAL):
            path.write_bytes(b'SYNTHETIC metadata marker; never executed or approved')
        self.stack.enter_context(patch.object(profile._API, 'profile', replace(profile._API.profile, GUEST_ROOT=PureWindowsPath(f.root))))
        sdk = f.sdk / 'emulator'
        sdk.mkdir(exist_ok=True); (sdk / 'emulator.exe').write_bytes(b'synthetic SDK marker; never executable')
        qemu = sdk / 'qemu/windows-x86_64/qemu-system-x86_64-headless.exe'
        qemu.parent.mkdir(parents=True); qemu.write_bytes(b'SYNTHETIC qemu metadata')
        guest = self.wire.a['guest']; server = self.wire.a['server']
        self.installed = {key: copy.deepcopy(server[key]) for key in ('adb', 'tools', 'python', 'capabilities', 'source_review')}
        self.installed.update(compatibility=copy.deepcopy(self.wire.a['compatibility']),
            emulator=env.binding(sdk / 'emulator.exe'), qemu=env.binding(qemu), refuser=copy.deepcopy(guest['refuser']),
            refuser_source=copy.deepcopy(guest['refuser_source']), auth_key_path=server['auth_key'])
        self.static_pin = self.store(self.root / 'synthetic-static-inputs.json', self.installed)
        self.plan_path, self.recovery_auth_path, _ = f.make_plan()
        self.stack.enter_context(patch.object(rules, 'PLAN', env.binding(self.plan_path)))
        self.handoff = dict(version=1, scope='sdk15-recovery-inspection-inputs-v1', source_root=str(SOURCE), head=rules.SOURCE_HEAD,
            ready_for_execution=False, approval_inferred=False, method_count=4,
            fixed_roster=[list(row) for row in wire_data.SELECTORS], recovery_plan=copy.deepcopy(rules.PLAN),
            guest=str(f.root), controls=str(controls), runtime=str(runtime), sources=profile.source_bindings(),
            helper=env.binding(SOURCE / 'scripts/freeze_library_ui_recovery_inputs.py'),
            activation=env.binding(SOURCE / 'benchmarks/library_ui_activation.py'),
            static_inputs=self.static_pin, artifacts=copy.deepcopy(self.wire.a['artifacts']))
        handoff_pin = self.store(self.root / 'synthetic-handoff.json', self.handoff)
        self.stack.enter_context(patch.object(rules, 'HANDOFF', handoff_pin))
        self.authority = synthetic_authority()
        for role in ('operator', 'builder', 'contract', 'proposal'): self.authority[role] = env.binding(getattr(rules, role.upper()))
        self.authority_pin = self.store(rules.AUTHORITY, self.authority)
        self.store(rules.ATTEMPT, synthetic_attempt(self.authority_pin, self.authority))
        def prepared(proposal, proposal_path, authorization_path, digest):
            f.synthetic_worker(proposal); return dict(proposal_sha256=digest, synthetic_prepared=True)
        f.worker.side_effect = prepared; f.close_known = self.known
        if not self.execute_recovery: pass
        elif self.known: f.execute(self.plan_path, self.recovery_auth_path)
        else:
            try: f.execute(self.plan_path, self.recovery_auth_path)
            except storage.StorageRefused as error:
                if 'cleanup_unknown' not in str(error): raise
            else: raise AssertionError('Synthetic unknown fence cleanup unexpectedly completed')
        self.recovery_authorization = env.binding(rules.RECOVERY_AUTHORIZATION)
        self.recovery_result = env.binding(rules.RECOVERY_RESULT) if self.execute_recovery else None
        self.before_ledger = f.ledger_bytes()
        self.api = SimpleNamespace(env=env, storage=storage, recovery=recovery, history=history, contract=profile,
            activation=SimpleNamespace(SOURCE_ROOT=SOURCE, RUNTIME=runtime, CONTROLS=controls,
                HELPER=SOURCE / 'benchmarks/library_ui_activation.py'), base=base,
            build=SimpleNamespace(verify_frozen_product=Mock(side_effect=self.verify_artifacts),
                verify_current=Mock(side_effect=self.wire.verified_build)))
        self.git = self.stack.enter_context(patch.object(builder, '_git'))
        self.stack.enter_context(patch.object(builder, '_rules', return_value=rules))
        self.stack.enter_context(patch.object(builder, '_api', return_value=self.api))
        self.readiness = self.stack.enter_context(patch.object(env, 'verify_prepared'))
        self.planner = self.stack.enter_context(patch.object(env, 'plan_run', wraps=env.plan_run))
        for target, name in ((recovery, 'execute'), (storage, 'record_state'), (storage, 'record_closed'),
            (storage, 'reserve_prepare'), (env, 'resource_facts'), (env, 'process_identity'), (env, 'supervise')):
            self.forbidden.append(self.stack.enter_context(patch.object(target, name,
                side_effect=AssertionError('Input construction dispatched a forbidden runtime operation'))))
        return self
    def __exit__(self, kind, error, trace):
        try:
            for forbidden in self.forbidden: forbidden.assert_not_called()
        finally:
            self.stack.close(); budget()
        return False
    @staticmethod
    def store(path, value):
        env.create_json(path, value); return env.binding(path)
    def verify_artifacts(self, artifacts):
        if artifacts != self.handoff['artifacts']: raise AssertionError('Wrong synthetic APK/build pair')
        for pin in artifacts.values(): env.check_binding(pin)
        return dict(roster=[list(row) for row in wire_data.SELECTORS], synthetic_product=True)
    def create(self):
        return builder.create_inputs(self.authority_pin, self.recovery_authorization, self.recovery_result)


class OperatorFixture:
    """Actual initial ledger/attempt/final file gates; simulated owned worker stage outcome."""
    def __init__(self):
        self.stack = ExitStack(); self.fault = None
    def __enter__(self):
        try: return self._open()
        except BaseException:
            self.stack.close(); raise
    def _open(self):
        self.graph = self.stack.enter_context(BuilderFixture(execute_recovery=False))
        self.root = self.graph.root; self.authority_pin = self.graph.authority_pin; self.authority = self.graph.authority
        self.api = self.graph.api
        live = self.root / 'operator-live'
        for name, value in dict(LIVE=live, ATTEMPT=live / 'attempt-v1.json',
            RECOVERY_AUTHORIZATION=live / 'recovery-authorization-v1.json',
            RUN_PROPOSAL=live / 'run-proposal-v1.json', RUN_AUTHORIZATION=live / 'run-authorization-v1.json').items():
            self.stack.enter_context(patch.object(rules, name, value))
        ledger = self.graph.fixture.registry / 'ledger-v1.json'; raw = ledger.read_bytes()
        ledger.write_bytes(raw + b' ' * (41230 - len(raw)))
        self.before_ledger = ledger.read_bytes()
        self.stack.enter_context(patch.object(rules, 'INITIAL_LEDGER_SHA256', env.binding(ledger)['sha256']))
        self.stack.enter_context(patch.object(operator, '_parts', return_value=(rules, builder, self.api)))
        self.stack.enter_context(patch.object(Path, 'cwd', return_value=rules.SOURCE))
        self.stack.enter_context(patch.dict(os.environ, {key: 'D:/Dev/_Temp' for key in ('TEMP', 'TMP', 'TMPDIR')}))
        self.worker = dict(pid=7717, creation_filetime=123456, executable=sys.executable)
        self.stack.enter_context(patch.object(env, 'process_identity',
            side_effect=lambda pid: dict(pid=pid, creation_filetime=100000 + pid, executable=sys.executable)))
        self.supervisor = self.stack.enter_context(patch.object(operator, '_supervise', side_effect=self.terminal))
        return self
    def __exit__(self, *args):
        self.stack.close(); budget(); return False
    def terminal(self, request, begin):
        value = env.read_json(request['path'])
        started = dict(request=request, worker=self.worker)
        claim = dict(version=1, authority=self.authority_pin, attempt=value['attempt'], request=request, worker=self.worker)
        if self.fault == 'started': started['worker'] = dict(self.worker, creation_filetime=1)
        if self.fault == 'claim': claim['request'] = dict(request, sha256='0' * 64)
        builder.save(rules.LIVE / 'worker-started-v1.json', started)
        builder.save(rules.LIVE / 'worker-claim-v1.json', claim)
        stages = dict(version=1, scope='sdk15-recovery-operation-stages-v1', passed=True, phase='completed',
            authority=self.authority_pin, attempt=value['attempt'], feature_acceptance=False, synthetic_outcome=True)
        if self.fault == 'stages': stages['attempt'] = dict(value['attempt'], sha256='0' * 64)
        builder.save(rules.LIVE / 'stage-result-v1.json', stages)
        result = dict(status='child_exited', worker_returncode=0, cleanup_complete=True,
            output_capture_complete=True, worker=self.worker, stdout_bytes=0, stderr_bytes=0, elapsed_ms=1)
        if self.fault == 'boolean_code': result['worker_returncode'] = False
        elif self.fault == 'expired': result['status'] = 'expired'
        elif self.fault == 'capture': result['output_capture_complete'] = False
        elif self.fault == 'cleanup': result['cleanup_complete'] = False
        return result
