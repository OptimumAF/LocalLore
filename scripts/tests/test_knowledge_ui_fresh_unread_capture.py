"""Original supplemental SDK16 unread-pipe capture adversaries.

Extends only the original fake ports: no process/thread/native/file execution.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import unittest

from scripts.tests.test_knowledge_ui_fresh_supervisor import SupervisorPorts


class SecondReaderNeverStarts(SupervisorPorts):
    def make_thread(self, target, args, daemon):
        reader=super().make_thread(target,args,daemon)
        if len(self.threads)==2:
            def refuse_start():
                self.events.append('second_reader_start_refused')
                raise RuntimeError('Synthetic second reader never started')
            reader.start=refuse_start
        return reader


class FreshSupervisorUnreadCaptureTests(unittest.TestCase):
    def test_no_successful_reader_start_cannot_publish_capture_complete(self):
        for fault in ('job','thread_start'):
            with self.subTest(fault=fault),SupervisorPorts(fault) as graph:
                result=graph.run()
            self.assertEqual(result['status'],'owner_failed')
            self.assertEqual(graph.stdin,b'','Failed admission must not release the worker')
            self.assertEqual(graph.child.stdout.data.tell(),0)
            self.assertEqual(graph.child.stderr.data.tell(),0)
            self.assertEqual([bytes(value) for value in graph.raw],[b'',b''])
            self.assertFalse(result['output_capture_complete'],
                'An unread stdout/stderr pair is not a complete capture even when closing empty capture files succeeds')

    def test_one_drained_reader_cannot_qualify_the_other_unstarted_reader(self):
        with SecondReaderNeverStarts() as graph:
            result=graph.run()
        self.assertEqual(result['status'],'owner_failed')
        self.assertEqual(graph.stdin,b'')
        self.assertEqual(bytes(graph.raw[0]),graph.stdout)
        self.assertEqual(bytes(graph.raw[1]),b'')
        self.assertEqual(graph.child.stderr.data.tell(),0)
        self.assertEqual(graph.job_close_calls,1)
        self.assertFalse(result['output_capture_complete'],
            'Draining stdout does not supply missing stderr capture when its reader failed to start')


if __name__=='__main__':unittest.main()