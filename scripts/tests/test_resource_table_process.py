"""Owned local-Python capture checks for the fixed resource-table API.

No AAPT, APK, SDK, model, device, guest or production ledger is accessed.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from benchmarks import runtime_spike as host

PROGRAM=r'''import sys,time
sys.stdin.buffer.read()
mode=sys.argv[1]
if mode=='complete':
    sys.stdout.buffer.write(bytes(range(128))*2400)
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(b'original diagnostic\n'*1234)
    sys.stderr.buffer.flush()
elif mode=='combined-at-limit':
    sys.stderr.buffer.write(b'e'*(3*1024*1024))
    sys.stderr.buffer.flush()
    sys.stdout.buffer.write(b'o'*(1024*1024))
    sys.stdout.buffer.flush()
elif mode=='combined-overflow':
    sys.stderr.buffer.write(b'e'*(3*1024*1024))
    sys.stderr.buffer.flush()
    sys.stdout.buffer.write(b'o'*(1024*1024+1))
    sys.stdout.buffer.flush()
elif mode=='deadline':
    sys.stdout.buffer.write(b'waiting-for-fixed-deadline\n')
    sys.stdout.buffer.flush()
    time.sleep(30)
else:
    raise AssertionError('unknown original producer mode')
'''


class ResourceTableProcessTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-resource-owner-',dir='D:/Dev/_Temp'))
        self.assertEqual(self.base.drive.upper(),'D:')
        self.program=self.base/'original-producer.py'
        self.program.write_bytes(PROGRAM.encode('utf-8'))

    def command(self,mode):
        return [sys.executable,'-I','-S','-B',str(self.program),mode]

    def test_legacy_ceiling_and_new_nonconfigurable_boundary_refuse_before_spawn(self):
        with patch.object(host.subprocess,'Popen')as spawn:
            with self.assertRaisesRegex(ValueError,'^invalid_process_budget$'):
                host.run_process(self.command('complete'),max_output=262145)
            cancelled=threading.Event();cancelled.set()
            result=host.run_process(self.command('complete'),cancel=cancelled,max_output=262144)
            self.assertEqual(result.status,'cancelled');self.assertTrue(result.cleanup_complete)
            for options in ({'deadline':180},{'max_output':8*1024*1024},{'cancel':cancelled},
                            {'request':b'caller-controlled'},{'cancel_at':0}):
                with self.subTest(option=next(iter(options))),self.assertRaises(TypeError):
                    host.run_resource_table(self.command('complete'),**options)
            spawn.assert_not_called()

    def test_resource_capture_above_legacy_ceiling_preserves_binary_stdout_and_stderr_count(self):
        result=host.run_resource_table(self.command('complete'))
        self.assertIsInstance(result,host.ProcessResult)
        self.assertEqual(result.status,'completed');self.assertEqual(result.returncode,0)
        self.assertEqual(result.stdout,bytes(range(128))*2400)
        self.assertGreater(len(result.stdout),262144)
        self.assertEqual(result.stderr_bytes,len(b'original diagnostic\n'*1234))
        self.assertLess(len(result.stdout)+result.stderr_bytes,4*1024*1024)
        self.assertIs(result.cleanup_complete,True)

    def test_stdout_and_stderr_share_one_fixed_limit_and_overflow_is_not_success(self):
        result=host.run_resource_table(self.command('combined-overflow'))
        self.assertEqual(result.status,'output_limit');self.assertIs(result.cleanup_complete,True)
        self.assertGreater(result.stderr_bytes,0);self.assertGreater(len(result.stdout),0)
        self.assertEqual(len(result.stdout)+result.stderr_bytes,4*1024*1024)

    def test_exact_combined_limit_then_eof_is_complete_with_both_counts_preserved(self):
        result=host.run_resource_table(self.command('combined-at-limit'))
        self.assertEqual(result.status,'completed');self.assertEqual(result.returncode,0)
        self.assertIs(result.cleanup_complete,True)
        self.assertEqual(result.stdout,b'o'*(1024*1024))
        self.assertEqual(result.stderr_bytes,3*1024*1024)
        self.assertEqual(len(result.stdout)+result.stderr_bytes,4*1024*1024)

    def test_fixed_deadline_retains_partial_capture_and_reaps_only_owned_producer(self):
        result=host.run_resource_table(self.command('deadline'))
        self.assertEqual(result.status,'timeout');self.assertIs(result.cleanup_complete,True)
        self.assertEqual(result.stdout,b'waiting-for-fixed-deadline\n')
        self.assertEqual(result.stderr_bytes,0)
        # No elapsed-speed threshold or cancellation override: this is an owner
        # deadline outcome from a finite inert producer, not a benchmark.


if __name__=='__main__':unittest.main()
