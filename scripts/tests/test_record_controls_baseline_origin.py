"""Frozen B66 record identity must survive relocation of its validating reader.

These definition-only executions read no record and perform no attestation; the
existing build graph tests retain the byte, path and negative binding checks.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import builtins
from contextlib import ExitStack
import os
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch

from benchmarks import record_controls_ui_build as build

ORIGIN = Path('D:/Worktrees/locallore-record-controls-ui-core-v1/benchmarks')
RECORDED_BASELINE = ORIGIN / 'record_controls_ui_build_baseline.json'
BASELINE_SHA256 = '2bcfa9dee3e8314e8fc24a10b9adec0481a31c165073c9bed9d6e54f138dc5fa'


class RecordControlsBaselineOriginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(build.__file__).read_bytes()

    def definitions(self, reader_path):
        namespace = {'__name__': 'benchmarks._frozen_baseline_origin_probe',
            '__package__': 'benchmarks', '__file__': str(reader_path)}
        with ExitStack() as stack:
            traps = [stack.enter_context(patch.object(target, name,
                side_effect=AssertionError('Definitions must not observe or operate the host')))
                for target, name in ((builtins, 'open'), (Path, 'open'), (Path, 'stat'),
                    (os, 'open'), (socket, 'socket'), (subprocess, 'run'), (subprocess, 'Popen'))]
            exec(compile(self.source, str(reader_path), 'exec'), namespace)
            for trap in traps: trap.assert_not_called()
        self.assertEqual(namespace['BASELINE_BYTES'], 16380)
        self.assertEqual(namespace['BASELINE_SHA256'], BASELINE_SHA256)
        return namespace

    def test_original_reader_keeps_the_literal_frozen_baseline_record(self):
        value = self.definitions(ORIGIN / 'record_controls_ui_build.py')
        self.assertEqual(value['BASELINE_PATH'], RECORDED_BASELINE)

    def test_relocated_reader_does_not_retarget_the_recorded_manifest_baseline(self):
        for folder in ('D:/Worktrees/locallore-record-actions-flow-v1/benchmarks',
                       'D:/Synthetic/ForeignReader/benchmarks'):
            with self.subTest(reader=folder):
                value = self.definitions(Path(folder) / 'record_controls_ui_build.py')
                self.assertEqual(value['BASELINE_PATH'], RECORDED_BASELINE,
                    'Moving a validator cannot rewrite the immutable manifest baseline.path')


if __name__ == '__main__':
    unittest.main()
