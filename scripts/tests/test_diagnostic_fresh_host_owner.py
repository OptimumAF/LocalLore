"""Real owned Windows host-child checks; no SDK, ADB, guest or model.

Only a generated literal Python fixture process is launched. The actual public
Windows job, identity and bounded capture mechanisms are retained. Its files
remain under this packet. Copyright 2026 LocalLore contributors.
SPDX-License-Identifier: Apache-2.0
"""
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from benchmarks import receipt_avd_environment as env
from scripts import diagnostic_ui_fresh_contract as rules
from scripts import run_diagnostic_ui_fresh as subject


class DiagnosticFreshHostOwnerTests(unittest.TestCase):
    def run_child(self,expiry):
        root=Path(tempfile.mkdtemp(prefix='sdk17-owned-host-'))
        self.assertEqual(root.drive.upper(),'D:')
        live=root/'live';live.mkdir()
        operator=root/'fixture.py'
        body="import sys,time\n"
        body+="assert sys.stdin.buffer.readline()==b'sdk17-fresh-operation-worker-v1\\n'\n"
        body+="request=sys.stdin.buffer.read(131073)\nassert request\n"
        body+=("time.sleep(30)\n" if expiry else "print('owned-host-fixture-complete',flush=True)\n")
        operator.write_text(body)
        request=live/'request.json';request.write_text('{}\n')
        r=SimpleNamespace(LIVE=live,OPERATOR=operator,MAX_SECONDS=1 if expiry else 30,
            need=rules.need,same=rules.same,binding=rules.binding)
        api=SimpleNamespace(env=env)
        began=time.monotonic()
        with patch.object(subject,'_parts',return_value=(r,api)):
            result=subject._supervise(env.binding(request),began)
        (root/'observed-result.json').write_text(json.dumps(result,indent=2))
        self.assertIs(result['cleanup_complete'],True)
        self.assertIs(result['output_capture_complete'],True)
        self.assertEqual(result['worker']['executable'],sys.executable)
        self.assertLess(time.monotonic()-began,15)
        return root,result

    def test_real_owned_host_worker_observes_barrier_and_closes_job_and_capture(self):
        root,result=self.run_child(False)
        self.assertEqual(result['status'],'child_exited')
        self.assertEqual(result['worker_returncode'],0)
        capture=root/'live/outer-owner-v1/owner-stdout-v1.bin'
        self.assertEqual(capture.read_bytes(),b'owned-host-fixture-complete\r\n')

    def test_expired_owned_host_worker_is_killed_without_other_process_actions(self):
        _,result=self.run_child(True)
        self.assertEqual(result['status'],'expired')
        self.assertNotEqual(result['worker_returncode'],0)
