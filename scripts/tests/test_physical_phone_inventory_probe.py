"""Original CLI wiring checks with real byte/proof/request validators.

Supervisor and native identity IO are synthetic. No fixture authenticates a
physical device, authorization, or actual service acquisition.
"""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import physical_phone_inventory_probe as cli
from scripts.tests import test_physical_phone_inventory as fixture
from scripts.tests import test_adb_device_roster_probe as prior_cli
from scripts.tests import test_adb_device_roster as roster_fixture
from scripts.tests import test_adb_held_socket as held


class PhoneInventoryCliTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-phone-inventory-', dir='D:/Dev/_Temp')).resolve()
        self.input = self.base/'admission.json'
        self.input.write_bytes(cli.env.encoded(fixture.admission()))
        self.input_pin = cli.env.binding(self.input)
        self.python = self.base/'synthetic-python.bin'; self.python.write_bytes(b'original synthetic runtime')
        self.python_pin = dict(executable=cli.env.binding(self.python), runtime_dll=None)
        self.parent = dict(pid=9101, creation_filetime=12345, executable=str(self.python))
        self.worker = dict(pid=held.CLIENT_PID, creation_filetime=223456789, executable=str(self.python))
        self.backends, self.outputs = [], []

    def backend(self, kind, failed):
        if kind == 'version': value = prior_cli.RecordingVersionBackend()
        elif kind == 'roster': value = roster_fixture.RosterBackend()
        else: value = fixture.InventoryBackend()
        for bracket in value.brackets: bracket['client']['executable'] = str(self.python)
        if failed == kind: value.errors[('connect', 0)] = OSError('PRIVATE_BACKEND_CANARY')
        self.backends.append((kind, value))
        return value

    def invoke(self, *, receipt=None, owner_changes=None, failed=None, after=None, source_changed=False):
        output = self.base/('output-%02d' % len(self.outputs)); self.outputs.append(output)
        self.backends = []; captured = False
        actual_sources = cli._source_bindings()
        def source_bindings():
            value = copy.deepcopy(actual_sources)
            if captured and source_changed: value[0]['sha256'] = 'b'*64
            return value
        def identity(pid):
            if pid == self.parent['pid']: return copy.deepcopy(self.parent)
            if pid == self.worker['pid']: return copy.deepcopy(self.worker)
            raise AssertionError('unselected process lookup')
        def supervise(command, barrier, root, seconds, on_started):
            nonlocal captured
            self.assertEqual((root, seconds, barrier), (output, 45, cli.BARRIER))
            self.assertEqual(command[1:4], ['-I', '-S', '-B'])
            self.assertTrue(on_started(SimpleNamespace(pid=self.worker['pid'])))
            path = output/'request-v1.json'
            if receipt:
                started = cli.env.read_json(output/'started-v1.json')
                if receipt == 'worker': started['worker']['creation_filetime'] += 1
                elif receipt == 'request': started['request'] = self.input_pin
                elif receipt == 'extra': started['private'] = 'PRIVATE_RECEIPT_CANARY'
                elif receipt == 'parent':
                    request = cli.env.read_json(path); request['parent']['pid'] += 1
                    path.write_bytes(cli.env.encoded(request))
                else: raise AssertionError('unknown fixture')
                if receipt != 'parent': (output/'started-v1.json').write_bytes(cli.env.encoded(started))
            code = 0
            with patch.object(cli.os, 'getpid', return_value=self.worker['pid']), \
                 patch.object(cli.os, 'getppid', return_value=self.parent['pid']), \
                 patch.object(cli.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(cli.BARRIER))):
                try: code = cli._worker(path, command[-1])
                except (ValueError, OSError, cli.env.EnvironmentRefused): code = 1
            captured = True
            if after: after(output)
            value = dict(status='child_exited', worker_returncode=code, cleanup_complete=True,
                         output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
            value.update(owner_changes or {})
            return value
        stdout = io.StringIO()
        with patch.object(cli, '_python_bindings', side_effect=lambda: copy.deepcopy(self.python_pin)), \
             patch.object(cli, '_source_bindings', side_effect=source_bindings), \
             patch.object(cli.env, 'process_identity', side_effect=identity), \
             patch.object(cli.os, 'getpid', return_value=self.parent['pid']), \
             patch.object(cli.env, 'supervise', side_effect=supervise), \
             patch.object(cli, '_backend_types', return_value=(lambda: self.backend('version', failed),
                 lambda: self.backend('roster', failed), lambda: self.backend('inventory', failed))), \
             redirect_stdout(stdout):
            code = cli.main(['--admission', str(self.input), '--admission-sha256', self.input_pin['sha256'],
                             '--output', str(output)])
        return code, cli.env.read_json(output/'result-v1.json'), stdout.getvalue(), output

    def test_three_real_proofs_join_actual_started_worker_and_private_measurements_stay_private(self):
        code, result, public, output = self.invoke()
        self.assertEqual(code, 0)
        self.assertTrue(result['inventory_observed']); self.assertTrue(result['acquisition_completed'])
        self.assertEqual(len(result), 17)
        inventory = cli.env.read_json(output/'report-v1.json')
        roster = cli.env.read_json(output/'roster-report-v1.json')
        version = cli.env.read_json(output/'version-report-v1.json')
        self.assertEqual(inventory['roster_proof'], roster)
        self.assertEqual(roster['version_proof'], version)
        self.assertEqual((output/'version-bytes-v1.bin').read_bytes().hex(), version['response_hex'])
        self.assertTrue(fixture.inventory.report_verified(inventory, fixture.admission()))
        self.assertEqual([kind for kind, _ in self.backends], ['version', 'roster', 'inventory'])
        self.assertTrue(all(backend.closed for _, backend in self.backends))
        summary = json.loads(public)
        self.assertEqual(set(summary), {'status', 'reason', 'acquisition_completed',
                                      'inventory_observed', 'feature_acceptance'})
        self.assertFalse(summary['feature_acceptance'])
        for private in (fixture.SERIAL, 'Original Phone', 'Original SoC', str(self.base), str(held.SERVER_PID)):
            self.assertNotIn(private, public)

    def test_started_or_parent_mismatch_prevents_all_backend_constructors(self):
        for receipt in ('worker', 'request', 'extra', 'parent'):
            with self.subTest(receipt=receipt):
                code, result, public, output = self.invoke(receipt=receipt)
                self.assertEqual(code, 1)
                self.assertFalse(result['inventory_observed'])
                self.assertEqual(self.backends, [])
                self.assertFalse((output/'version-report-v1.json').exists())

    def test_strict_owner_counts_and_known_capture_cleanup_are_required(self):
        for change in (dict(worker_returncode=True), dict(stdout_bytes=False), dict(stderr_bytes=False),
                       dict(stdout_bytes=1), dict(stderr_bytes=-1), dict(cleanup_complete=False),
                       dict(output_capture_complete=False), dict(status='expired')):
            with self.subTest(change=change):
                code, result, public, output = self.invoke(owner_changes=change)
                self.assertEqual(code, 1)
                self.assertFalse(result['inventory_observed'])
                self.assertTrue((output/'report-v1.json').exists())

    def test_failed_prior_stage_preserves_raw_reports_and_blocks_inventory_device_send(self):
        for kind in ('version', 'roster'):
            with self.subTest(kind=kind):
                code, result, public, output = self.invoke(failed=kind)
                self.assertEqual(code, 1)
                self.assertFalse(result['inventory_observed'])
                self.assertTrue((output/'version-report-v1.json').exists())
                self.assertTrue((output/'roster-report-v1.json').exists())
                self.assertTrue((output/'report-v1.json').exists())
                backend = [value for name, value in self.backends if name == 'inventory'][0]
                self.assertEqual(backend.counts['open'], 0)
                self.assertEqual(backend.sent, [])
                self.assertNotIn('PRIVATE_BACKEND_CANARY', public)

    def test_bound_report_raw_sidecar_request_and_receipt_mutations_cannot_be_promoted(self):
        for name in ('version-bytes-v1.bin', 'version-report-v1.json', 'roster-report-v1.json',
                     'report-v1.json', 'request-v1.json', 'started-v1.json'):
            def mutate(root):
                path = root/name
                if name.endswith('.bin'): path.write_bytes(b'OKAY0004002a')
                else:
                    value = cli.env.read_json(path); value['private'] = 'PRIVATE_MUTATION_CANARY'
                    path.write_bytes(cli.env.encoded(value))
            with self.subTest(name=name):
                code, result, public, output = self.invoke(after=mutate)
                self.assertEqual(code, 1)
                self.assertFalse(result['inventory_observed'])
                self.assertNotIn('PRIVATE_MUTATION_CANARY', public)

    def test_final_source_change_refuses_and_keeps_completed_private_reports(self):
        code, result, public, output = self.invoke(source_changed=True)
        self.assertEqual(code, 1)
        self.assertFalse(result['inventory_observed']); self.assertFalse(result['sources_equal'])
        self.assertEqual(result['reason'], 'source_changed')
        report = cli.env.read_json(output/'report-v1.json')
        self.assertTrue(fixture.inventory.report_verified(report, fixture.admission()))

    def test_malformed_admission_hash_or_json_cannot_create_output_or_dispatch(self):
        cases = [b'{"version":1,"version":1}', b'\xff',
                 cli.env.encoded({**fixture.admission(), 'authorized_serial': 'emulator-5554'})]
        for index, raw in enumerate(cases):
            path = self.base/('invalid-%d.json' % index); path.write_bytes(raw)
            output = self.base/('invalid-output-%d' % index)
            with self.subTest(index=index), patch.object(cli, '_dispatch') as dispatch, redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(['--admission', str(path), '--admission-sha256', cli.env.digest(path),
                                           '--output', str(output)]), 1)
                dispatch.assert_not_called(); self.assertFalse(output.exists())


if __name__ == '__main__': unittest.main()
