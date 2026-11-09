"""Actual owned Python preflight-expiry checks; no SDK/ADB/guest/model.

Only generated literal host processes and new D: fixture files are used.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
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
from scripts import diagnostic_operation_contract as rules
from scripts import run_diagnostic_operation as subject


@unittest.skipUnless(os.name=='nt','owned Windows job and real host identity')
class DiagnosticOperationHostTests(unittest.TestCase):
    def run_host(self,blocked):
        root=Path(tempfile.mkdtemp(prefix='sdk17-parent-host-'))
        self.assertEqual(root.drive.upper(),'D:')
        live=root/'live';live.mkdir()
        operator=root/'literal.py';entered=root/'preflight-entered';stage=root/'stage-entered'
        text='import sys,time\nfrom pathlib import Path\n'
        text+=f'assert sys.stdin.buffer.readline()=={subject.BARRIER!r}\n'
        text+='assert sys.stdin.buffer.read(131073)\n'
        text+=f'Path({str(entered)!r}).write_text("literal preflight only")\n'
        text+=('time.sleep(30)\n' if blocked else '')
        text+=f'Path({str(stage)!r}).write_text("literal stage only; no SDK")\n'
        text+='print("literal-host-complete",flush=True)\n'
        operator.write_text(text)
        request=live/'request.json';request.write_text('{}\n')
        r=SimpleNamespace(LIVE=live,OPERATOR=operator,MAX_SECONDS=3 if blocked else 30,
            binding=rules.binding,need=rules.need,same=rules.same)
        began=time.monotonic()
        with patch.object(subject,'_parts',return_value=(r,SimpleNamespace(env=env))),patch.object(subject,'_RULES',r):
            result=subject._supervise(env.binding(request),began)
        (root/'result.json').write_text(json.dumps(result,indent=2))
        self.assertTrue(entered.is_file())
        self.assertIs(result['cleanup_complete'],True)
        self.assertIs(result['output_capture_complete'],True)
        self.assertIs(type(result['worker_returncode']),int)
        self.assertEqual(result['worker']['executable'],sys.executable)
        self.assertLess(time.monotonic()-began,15)
        return root,stage,result

    def test_parent_job_expires_a_real_child_blocked_before_literal_stage(self):
        _,stage,result=self.run_host(True)
        self.assertEqual(result['status'],'expired')
        self.assertNotEqual(result['worker_returncode'],0)
        self.assertFalse(stage.exists())

    def test_parent_positive_child_passes_barrier_and_captures_known_exit(self):
        root,stage,result=self.run_host(False)
        self.assertEqual(result['status'],'child_exited')
        self.assertEqual(result['worker_returncode'],0)
        self.assertTrue(stage.is_file())
        self.assertEqual((root/'live/outer-owner-v1/owner-stdout-v1.bin').read_bytes(),b'literal-host-complete\r\n')
