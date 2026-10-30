"""Original byte-bound CLI tests; only OS/backend/supervisor IO is replaced.

Real request, source, started, serialization and pure proof validators run.
Synthetic records confer no host service or device authority.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import adb_device_roster_probe as cli
from scripts.tests import test_adb_device_roster as f
from scripts.tests import test_adb_held_socket as held


class DeviceRosterCliTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-roster-cli-', dir='D:/Dev/_Temp')).resolve()
        self.input = self.base/'admission.json'
        self.input.write_bytes(cli.env.encoded(f.admission()))
        self.input_pin = cli.env.binding(self.input)
        self.python = self.base/'synthetic-python.bin'
        self.python.write_bytes(b'original synthetic interpreter metadata')
        self.python_pin = dict(executable=cli.env.binding(self.python), runtime_dll=None)
        self.parent = dict(pid=9101, creation_filetime=12345, executable=str(self.python))
        self.worker = dict(pid=held.CLIENT_PID, creation_filetime=223456789, executable=str(self.python))
        self.backends = []
        self.outputs = []
        self.supervisor_calls = 0

    def backend(self, kind, version_refused=False):
        value = held.FakeBackend() if kind == 'version' else f.RosterBackend()
        for bracket in value.brackets:
            bracket['client']['executable'] = str(self.python)
        if kind == 'version' and version_refused:
            value.errors[('connect', 0)] = OSError('PRIVATE_VERSION_CANARY')
        self.backends.append((kind, value))
        return value

    def invoke(self, *, receipt=None, owner_changes=None, version_refused=False, after=None):
        output = self.base/('output-%02d' % len(self.outputs))
        self.outputs.append(output)
        self.backends = []
        def identity(pid):
            if pid == self.parent['pid']: return copy.deepcopy(self.parent)
            if pid == self.worker['pid']: return copy.deepcopy(self.worker)
            raise AssertionError('unselected process identity requested')
        def supervise(command, barrier, root, seconds, started):
            self.supervisor_calls += 1
            self.assertEqual((root, seconds, barrier), (output, 30, cli.BARRIER))
            self.assertEqual(command[1:4], ['-I', '-S', '-B'])
            self.assertTrue(started(SimpleNamespace(pid=self.worker['pid'])))
            started_path = root/'started-v1.json'
            if receipt not in (None, 'missing'):
                value = cli.env.read_json(started_path)
                if receipt == 'worker': value['worker']['pid'] += 1
                elif receipt == 'request': value['request'] = self.input_pin
                elif receipt == 'shape': value['private'] = 'PRIVATE_RECEIPT_CANARY'
                else: raise AssertionError('unknown receipt fixture')
                started_path.write_bytes(cli.env.encoded(value))
            request_path = root/'request-v1.json'
            if receipt == 'missing':
                # Do not delete the original receipt: point this attempt at an
                # independently created, unannounced output namespace instead.
                alternate = root/'unannounced'; alternate.mkdir()
                value = cli.env.read_json(request_path); value['output'] = str(alternate)
                request_path = alternate/'request-v1.json'
                cli.env.create_json(request_path, value)
            worker_code = 0
            clock = SimpleNamespace(monotonic=iter((0.0, 6.0)).__next__, sleep=lambda seconds: None)
            with patch.object(cli.os, 'getpid', return_value=self.worker['pid']), \
                 patch.object(cli.os, 'getppid', return_value=self.parent['pid']), \
                 patch.object(cli.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(cli.BARRIER))):
                try:
                    if receipt == 'missing':
                        with patch.object(cli, 'time', clock):
                            worker_code = cli._worker(request_path, cli.env.digest(request_path))
                    else:
                        worker_code = cli._worker(request_path, command[-1])
                except (ValueError, OSError, cli.env.EnvironmentRefused):
                    worker_code = 1
            if after: after(root)
            value = dict(status='child_exited', worker_returncode=worker_code, cleanup_complete=True,
                         output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
            value.update(owner_changes or {})
            return value
        stdout = io.StringIO()
        with patch.object(cli, '_python_bindings', side_effect=lambda: copy.deepcopy(self.python_pin)), \
             patch.object(cli.env, 'process_identity', side_effect=identity), \
             patch.object(cli.os, 'getpid', return_value=self.parent['pid']), \
             patch.object(cli.env, 'supervise', side_effect=supervise), \
             patch.object(cli, '_backend_types', return_value=(
                 lambda: self.backend('version', version_refused), lambda: self.backend('roster'))), \
             redirect_stdout(stdout):
            code = cli.main(['--admission', str(self.input), '--admission-sha256', self.input_pin['sha256'],
                             '--output', str(output)])
        return code, cli.env.read_json(output/'result-v1.json'), stdout.getvalue(), output

    def test_parent_and_worker_replay_real_source_request_started_and_both_proofs(self):
        code, result, stdout, output = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'observed')
        self.assertTrue(result['acquisition_completed'])
        self.assertTrue(result['roster_observed'])
        self.assertFalse(result['feature_acceptance'])
        report = cli.env.read_json(output/'report-v1.json')
        version = cli.env.read_json(output/'version-report-v1.json')
        self.assertEqual(report['version_proof'], version)
        self.assertTrue(f.roster.report_verified(report, f.admission()))
        self.assertEqual([kind for kind, _ in self.backends], ['version', 'roster'])
        self.assertTrue(all(backend.closed for _, backend in self.backends))
        public = json.loads(stdout)
        self.assertEqual(set(public), {'status', 'reason', 'acquisition_completed', 'roster_observed',
                                      'row_count', 'feature_acceptance'})
        self.assertEqual(public['row_count'], 1)
        for private in ('ORIGINAL_USB', 'Original_Model', str(self.base), str(held.SERVER_PID)):
            self.assertNotIn(private, stdout)

    def test_foreign_malformed_or_absent_started_receipt_blocks_backend_construction(self):
        for receipt in ('worker', 'request', 'shape', 'missing'):
            with self.subTest(receipt=receipt):
                code, result, stdout, output = self.invoke(receipt=receipt)
                self.assertEqual(code, 1)
                self.assertFalse(result['roster_observed'])
                self.assertEqual(self.backends, [])
                self.assertFalse((output/'version-report-v1.json').exists())
                self.assertFalse((output/'report-v1.json').exists())

    def test_owner_capture_or_cleanup_failure_cannot_promote_valid_private_reports(self):
        for change in (dict(cleanup_complete=False), dict(output_capture_complete=False),
                       dict(worker_returncode=True), dict(status='expired'),
                       dict(stdout_bytes=1), dict(stderr_bytes=1), dict(stdout_bytes=False)):
            with self.subTest(change=change):
                code, result, stdout, output = self.invoke(owner_changes=change)
                self.assertEqual(code, 1)
                self.assertFalse(result['roster_observed'])
                self.assertIsNone(json.loads(stdout)['row_count'])
                self.assertTrue((output/'report-v1.json').exists())

    def test_refused_version_raw_is_retained_but_no_roster_socket_is_opened(self):
        code, result, stdout, output = self.invoke(version_refused=True)
        self.assertEqual(code, 1)
        self.assertFalse(result['roster_observed'])
        self.assertTrue((output/'version-report-v1.json').exists())
        report = cli.env.read_json(output/'report-v1.json')
        self.assertIsNone(report['version_proof'])
        self.assertIsNone(report['rows'])
        roster_backend = [value for kind, value in self.backends if kind == 'roster'][0]
        self.assertEqual(roster_backend.counts['open'], 0)
        self.assertEqual(roster_backend.sent, [])
        self.assertNotIn('PRIVATE_VERSION_CANARY', stdout)

    def test_mutated_request_or_receipt_after_capture_invalidates_parent_verdict(self):
        for name in ('request-v1.json', 'started-v1.json'):
            def mutate(root):
                value = cli.env.read_json(root/name); value['private'] = 'PRIVATE_MUTATION_CANARY'
                (root/name).write_bytes(cli.env.encoded(value))
            with self.subTest(name=name):
                code, result, stdout, output = self.invoke(after=mutate)
                self.assertEqual(code, 1)
                self.assertFalse(result['roster_observed'])
                self.assertIsNone(json.loads(stdout)['row_count'])
                self.assertNotIn('PRIVATE_MUTATION_CANARY', stdout)
                self.assertTrue((output/'report-v1.json').exists())

    def test_nested_private_report_injection_cannot_be_serialized_as_success(self):
        def mutate(root):
            value = cli.env.read_json(root/'report-v1.json')
            value['stages'][0]['bracket']['unrelated_table'] = 'PRIVATE_TABLE_CANARY'
            (root/'report-v1.json').write_bytes(cli.env.encoded(value))
        code, result, stdout, output = self.invoke(after=mutate)
        self.assertEqual(code, 1)
        self.assertFalse(result['roster_observed'])
        self.assertNotIn('PRIVATE_TABLE_CANARY', stdout)
        self.assertIsNone(json.loads(stdout)['row_count'])

    def test_nonwindows_and_bad_output_refuse_before_any_admission_or_dispatch(self):
        with patch.object(cli, 'os', SimpleNamespace(name='posix')), \
             patch.object(cli, '_load_admission') as load, patch.object(cli, '_dispatch') as dispatch, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main([]), 1)
        load.assert_not_called(); dispatch.assert_not_called()
        for path in ('C:\\Synthetic\\output', 'relative', str(self.base), str(self.base/'NUL')):
            with self.subTest(path=path), patch.object(cli, '_load_admission') as load, \
                 patch.object(cli, '_dispatch') as dispatch, redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(['--admission', str(self.input), '--admission-sha256', self.input_pin['sha256'],
                                           '--output', path]), 1)
                load.assert_not_called(); dispatch.assert_not_called()

    def test_admission_hash_json_and_protocol_are_checked_without_dispatch(self):
        for index, data in enumerate((b'\xff', b'{"version":1,"version":1}', b'{"x":NaN}',
                                      b' '*16385, cli.env.encoded(held.admission()))):
            path = self.base/('bad-%d.json' % index); path.write_bytes(data)
            with self.subTest(index=index), self.assertRaises((ValueError, cli.env.EnvironmentRefused)):
                cli._load_admission(str(path), cli.env.digest(path))
        with self.assertRaises((ValueError, cli.env.EnvironmentRefused)):
            cli._load_admission(str(self.input), '0'*64)


if __name__ == '__main__':
    unittest.main()
