"""Original outer execute success-edge cancellation oracle; metadata ports only."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import record_cancellation_ui_activation as a
from scripts.tests import test_record_cancellation_ui_profile_fixtures as f


class RecordCancellationUiActivationEdgeTests(unittest.TestCase):
    def test_execute_cancellation_after_success_update_is_terminal_false_not_repaired(self):
        for interrupt in (False, True):
            with self.subTest(interrupt=interrupt):
                events, published = [], []
                class Result(dict):
                    def update(self, *args, **kwargs):
                        super().update(*args, **kwargs)
                        if kwargs.get('passed') is True and 'runtime' in kwargs:
                            events.append('success_flag_written')
                            if interrupt: raise KeyboardInterrupt('PRIVATE_SUCCESS_EDGE_PAYLOAD')

                input_pin = f.legacy.pin(a.INPUT)
                request_pin = f.legacy.pin(a.CONTROL / 'worker-request-v1.json')
                runtime_pin = f.legacy.pin(a.CONTROL / 'runtime-result-v1.json')
                parent = dict(pid=900, created_filetime=1000, executable=a.sys.executable)
                worker = dict(pid=901, created_filetime=1001, executable=a.sys.executable)
                admission = f.admitted()
                admission['python']['executable']['path'] = a.sys.executable
                value = f.input_value()
                owner_result = Result(status='child_exited', worker_returncode=0,
                    cleanup_complete=True, output_capture_complete=True)

                def save(path, value):
                    published.append((str(path), copy.deepcopy(dict(value))))
                    return f.legacy.pin(path)

                def bound(pin):
                    if Path(pin['path']) == a.CONTROL / 'worker-started-v1.json':
                        return dict(request=request_pin, worker=worker)
                    self.assertEqual(pin, runtime_pin)
                    return dict(passed=True, input=input_pin, request=request_pin, worker=worker)

                def supervise(command, envelope, capture, seconds, started):
                    self.assertEqual(seconds, 1800)
                    self.assertTrue(envelope.startswith(b'record-cancellation-ui-activation-worker-v1\n'))
                    self.assertIs(started(SimpleNamespace(pid=901)), True)
                    events.append('owned_worker_terminal')
                    return owner_result

                api = SimpleNamespace(env=SimpleNamespace(safe_path=Mock(), binding=f.legacy.pin,
                    encoded=f.env.encoded, supervise=Mock(side_effect=supervise)))
                with patch.object(a, '_api', return_value=api), \
                     patch.object(a, 'dict', Result, create=True), \
                     patch.object(a, '_inputs', return_value=(value, admission)) as inputs, \
                     patch.object(a, '_identity', return_value=parent), \
                     patch.object(a, '_started', return_value=worker) as started, \
                     patch.object(a, '_bound', side_effect=bound) as reads, \
                     patch.object(a, '_save', side_effect=save), \
                     patch.object(Path, 'cwd', return_value=a.SOURCE_ROOT), \
                     patch.object(Path, 'mkdir') as mkdir, \
                     patch.object(a.os.path, 'lexists', return_value=False), \
                     patch.dict(a.os.environ, {key: 'D:/Dev/_Temp' for key in ('TEMP', 'TMP', 'TMPDIR')}):
                    returned = a.execute(input_pin)

                # The identical owner/runtime graph must qualify without the
                # injected interrupt. With interruption, success was reached
                # and written before the catch: a metadata refusal is not the
                # tested failure. No authority, process or file was opened.
                self.assertEqual(events, ['owned_worker_terminal', 'success_flag_written'])
                self.assertIs(returned['passed'], not interrupt)
                self.assertIs(returned['feature_acceptance'], False)
                self.assertEqual(returned['runtime'], runtime_pin)
                self.assertEqual(api.env.supervise.call_count, 1)
                self.assertEqual(started.call_count, 1)
                self.assertEqual(reads.call_count, 2)
                self.assertEqual(mkdir.call_count, 2)
                self.assertEqual([(row.args, row.kwargs) for row in inputs.call_args_list],
                    [((input_pin,), {'fresh': True}), ((input_pin,), {})])
                self.assertEqual(len(published), 3)
                self.assertEqual(published[-1][0], str(a.CONTROL / 'final-result-v1.json'))
                self.assertIs(published[-1][1]['passed'], not interrupt)
                if interrupt: self.assertEqual(returned['reason'], 'KeyboardInterrupt')
                else: self.assertNotIn('reason', returned)
                self.assertNotIn('PRIVATE_SUCCESS_EDGE_PAYLOAD', json.dumps(returned))
                self.assertNotIn('PRIVATE_SUCCESS_EDGE_PAYLOAD', json.dumps(published))
