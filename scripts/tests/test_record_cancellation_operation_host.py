"""Actual owned literal Python children; no SDK/ADB/model/service/guest action.

Run this module only in Root's separately declared host-process cohort. The
ordinary fake-observation suite must continue denying all process dispatch.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_environment as env
from scripts import record_cancellation_operation_contract as rules
from scripts import run_record_cancellation_operation as subject

HOST_SCRIPT = '''MODE = __MODE__
import json,os,sys,time
from pathlib import Path
assert sys.argv[1:] == ["_worker"]
barrier = b"sdk18-record-cancellation-operation-worker-v1\\n"
assert sys.stdin.buffer.readline(len(barrier)+1) == barrier
request = json.loads(sys.stdin.buffer.read(131073))
live = Path(__file__).resolve().parent / "live"
started = json.loads((live / "worker-started-v1.json").read_bytes())
assert started["request"] == request
assert started["worker"]["pid"] == os.getpid()
assert started["worker"]["executable"] == sys.executable
(live / "literal-preflight-v1.json").write_text(json.dumps(dict(scope="sdk18-host-preflight-fixture-v1",execution_authorized=False)),encoding="utf-8")
if MODE == "blocked": time.sleep(5)
(live / "literal-stage-v1.json").write_text(json.dumps(dict(scope="sdk18-host-stage-fixture-v1",sdk_dispatched=False,model_material=False)),encoding="utf-8")
print("sdk18-literal-host-complete",flush=True)
'''


def host_body(mode):
    assert mode in ('complete', 'blocked')
    return HOST_SCRIPT.replace('__MODE__', repr(mode)).encode('utf-8')


@unittest.skipUnless(os.name == 'nt', 'actual checked Windows Job ownership')
class RecordCancellationOperationHostTests(unittest.TestCase):
    def run_literal(self, mode, *, original_clock_debt=0.0, close_false=False, assign_failure=False):
        base = Path(tempfile.mkdtemp(prefix='sdk18-parent-literal-host-'))
        self.assertEqual(base.drive.upper(), 'D:')
        live = base / 'live'; live.mkdir()
        operator = base / 'literal-worker.py'; operator.write_bytes(host_body(mode))
        request = live / 'literal-request-v1.json'
        env.create_json(request, dict(version=1, scope='sdk18-host-request-fixture-v1', execution_authorized=False))
        r = SimpleNamespace(LIVE=live, OPERATOR=operator, MAX_SECONDS=6 if mode == 'blocked' else 20,
            binding=rules.binding, need=rules.need, same=rules.same)
        real_job = env.host.WindowsJob
        native_close_results = []
        class CloseObservation:
            def __init__(self, pid): self.job = real_job(pid)
            def close(self):
                observed = self.job.close(); native_close_results.append(observed)
                self_test.assertIs(observed, True)
                return False
        self_test = self
        def cannot_assign(pid): raise RuntimeError('PRIVATE_ASSIGNMENT_FAILURE')
        started = time.monotonic(); begin = started - original_clock_debt
        with patch.object(subject, '_parts', return_value=(r, SimpleNamespace(env=env))), \
             patch.object(subject, '_RULES', r), \
             patch.object(env.host, 'WindowsJob', cannot_assign if assign_failure else CloseObservation if close_false else real_job):
            result = subject._supervise(env.binding(request), begin)
        wall = time.monotonic() - started
        env.create_json(base / 'observed-result-v1.json', dict(result=result, wall_seconds=wall,
            original_clock_debt=original_clock_debt, native_close_results=native_close_results))
        self.assertLess(wall, 20)
        return base, live, result, native_close_results

    def test_original_parent_clock_expires_real_preflight_before_a_literal_stage(self):
        # The child would finish its literal preflight after5s. The original
        # parent clock has already spent2.5s of its6s budget, so resetting the
        # clock at child spawn would incorrectly allow its stage to execute.
        _, live, result, _ = self.run_literal('blocked', original_clock_debt=2.5)
        self.assertTrue((live / 'literal-preflight-v1.json').is_file())
        self.assertFalse((live / 'literal-stage-v1.json').exists())
        self.assertEqual(result['status'], 'expired')
        self.assertIs(type(result['worker_returncode']), int)
        self.assertNotEqual(result['worker_returncode'], 0)
        self.assertIs(result['cleanup_complete'], True)
        self.assertIs(result['output_capture_complete'], True)
        self.assertGreaterEqual(result['elapsed_ms'], 6000)

    def test_started_receipt_precedes_real_child_and_uncertain_close_cannot_borrow_zero_exit(self):
        for unknown_close in (False, True):
            with self.subTest(unknown_close=unknown_close):
                _, live, result, closes = self.run_literal('complete', close_false=unknown_close)
                self.assertEqual(result['status'], 'child_exited')
                self.assertEqual(result['worker_returncode'], 0)
                self.assertIs(result['cleanup_complete'], not unknown_close)
                self.assertIs(result['output_capture_complete'], True)
                self.assertEqual(result['worker']['executable'], sys.executable)
                self.assertTrue((live / 'worker-started-v1.json').is_file())
                self.assertTrue((live / 'literal-preflight-v1.json').is_file())
                self.assertTrue((live / 'literal-stage-v1.json').is_file())
                self.assertEqual((live / 'outer-owner-v1/owner-stdout-v1.bin').read_bytes(), b'sdk18-literal-host-complete\r\n')
                self.assertEqual(closes, [True] if unknown_close else [])

    def test_assignment_failure_never_releases_barrier_and_keeps_cleanup_unknown(self):
        _, live, result, _ = self.run_literal('complete', assign_failure=True)
        self.assertEqual(result['status'], 'owner_failed')
        self.assertIs(type(result['worker_returncode']), int)
        self.assertIs(result['cleanup_complete'], False)
        self.assertIs(result['output_capture_complete'], False)
        self.assertIsNone(result['worker'])
        self.assertFalse((live / 'worker-started-v1.json').exists())
        self.assertFalse((live / 'literal-preflight-v1.json').exists())
        self.assertFalse((live / 'literal-stage-v1.json').exists())
        self.assertNotIn('PRIVATE_ASSIGNMENT_FAILURE', json.dumps(result))
