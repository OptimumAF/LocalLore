"""Model-free checks for the held narration process observer."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import narration_process_observer as observer
from benchmarks import receipt_avd_environment as env

GATE = 60
DIRECT = 61
WORKER = 62
OTHER = 63
JOB = 64
DIRECT_IMAGE = r"D:\Synthetic\play-scene-probe.exe"
WORKER_IMAGE = r"D:\Synthetic\locallore-llama-worker.exe"
BARRIER = b"locallore-narration-observer-synthetic-v1\n"


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.members = {GATE, DIRECT, WORKER}
        self.images = {DIRECT: DIRECT_IMAGE, WORKER: WORKER_IMAGE}
        self.waits = {DIRECT: observer.WAIT_TIMEOUT, WORKER: observer.WAIT_TIMEOUT}
        self.exits = {DIRECT: 1, WORKER: 0}
        self.api = Mock()
        self.api.members.side_effect = lambda job: set(self.members)
        self.api.open.side_effect = lambda pid: pid
        self.api.member.return_value = True
        self.api.creation.side_effect = lambda handle, pid: 10_000 + pid
        self.api.image.side_effect = self.image
        self.api.wait.side_effect = lambda handle, timeout: self.waits[handle]
        self.api.exit_code.side_effect = lambda handle: self.exits[handle]
        self.api.close.return_value = True
        self.watch = observer.NarrationProcessObserver(
            self.api, JOB, DIRECT, DIRECT_IMAGE, WORKER_IMAGE, gate_pid=GATE)

    def image(self, handle):
        value = self.images[handle]
        if isinstance(value, Exception):
            raise value
        return value

    def third(self, image, *, wait=observer.WAIT_OBJECT_0, code=0, pid=OTHER):
        self.members.add(pid)
        self.images[pid] = image
        self.waits[pid] = wait
        self.exits[pid] = code

    def close_roles(self):
        self.waits[DIRECT] = self.waits[WORKER] = observer.WAIT_OBJECT_0

    def test_positive_roles_hold_exact_image_and_creation_identity(self):
        self.assertTrue(self.watch.poll())
        self.api.open.assert_any_call(DIRECT)
        self.api.open.assert_any_call(WORKER)
        self.assertNotIn(GATE, [call.args[0] for call in self.api.open.call_args_list])
        self.api.close.assert_not_called()
        self.close_roles()
        proof = self.watch.finish()
        self.assertEqual(proof["direct"], dict(pid=DIRECT, creation_filetime=10_000 + DIRECT,
                                              executable=DIRECT_IMAGE, exit=1))
        self.assertEqual(proof["worker"]["executable"], WORKER_IMAGE)
        self.assertEqual(proof["worker"]["exit"], 0)
        self.assertTrue(proof["handles_closed"])
        self.assertTrue(self.watch.close())
        self.assertEqual([call.args[0] for call in self.api.close.call_args_list], [DIRECT, WORKER])

    def test_signaled_distinct_image_failure_never_acquires_role_credit(self):
        self.assertTrue(self.watch.poll())
        self.third(observer.ImageUnavailable(31), code=8)
        self.assertTrue(self.watch.poll())
        self.api.wait.assert_called_with(OTHER, observer.EXIT_GRACE_MS)
        self.api.close.assert_called_once_with(OTHER)
        self.members.remove(OTHER)
        self.close_roles()
        proof = self.watch.finish()
        self.assertEqual(proof["unclassified_exits"], [dict(pid=OTHER, creation_filetime=10_000 + OTHER,
                                                           image_error=31, exit=8)])
        self.assertEqual(proof["worker"]["pid"], WORKER)

    def test_live_or_unknown_wait_for_failed_image_refuses_and_latches(self):
        for wait in (observer.WAIT_TIMEOUT, 0xFFFFFFFF):
            with self.subTest(wait=wait):
                watch = observer.NarrationProcessObserver(self.api, JOB, DIRECT, DIRECT_IMAGE,
                                                           WORKER_IMAGE, gate_pid=GATE)
                self.members.discard(OTHER)
                self.assertTrue(watch.poll())
                self.third(observer.ImageUnavailable(31), wait=wait)
                with self.assertRaisesRegex(observer.ObservationRefused, "^image$"):
                    watch.poll()
                with self.assertRaisesRegex(observer.ObservationRefused, "^observer_state$"):
                    watch.poll()
                self.assertTrue(watch.close())

    def test_direct_image_failure_remains_fatal_even_when_signaled(self):
        self.images[DIRECT] = observer.ImageUnavailable(31)
        self.waits[DIRECT] = observer.WAIT_OBJECT_0
        with self.assertRaisesRegex(observer.ImageUnavailable, "^image$") as failure:
            self.watch.poll()
        self.assertEqual((failure.exception.pid, failure.exception.creation_filetime, failure.exception.code),
                         (DIRECT, 10_000 + DIRECT, 31))
        self.api.wait.assert_not_called()
        self.api.close.assert_called_once_with(DIRECT)

    def test_unidentified_exit_cannot_substitute_for_worker(self):
        self.images[WORKER] = observer.ImageUnavailable(31)
        self.waits[WORKER] = observer.WAIT_OBJECT_0
        with self.assertRaisesRegex(observer.ObservationRefused, "^image$"):
            self.watch.poll()
        self.assertEqual(self.watch.transients, {})
        self.assertTrue(self.watch.close())

    def test_wrong_job_membership_refuses_even_after_required_roles(self):
        self.assertTrue(self.watch.poll())
        self.third(observer.ImageUnavailable(31))
        self.api.member.return_value = False
        with self.assertRaisesRegex(observer.ObservationRefused, "^job_member$"):
            self.watch.poll()
        self.assertEqual(self.watch.transients, {})
        self.api.close.assert_called_once_with(OTHER)
        self.assertTrue(self.watch.close())

    def test_same_worker_basename_in_wrong_directory_refuses(self):
        self.images[WORKER] = r"D:\Other\locallore-llama-worker.exe"
        with self.assertRaisesRegex(observer.ObservationRefused, "^worker_image$"):
            self.watch.poll()
        self.assertTrue(self.watch.close())

    def test_second_positive_worker_refuses_without_replacing_held_identity(self):
        self.assertTrue(self.watch.poll())
        self.third(WORKER_IMAGE, wait=observer.WAIT_TIMEOUT)
        with self.assertRaisesRegex(observer.ObservationRefused, "^required_identity$"):
            self.watch.poll()
        self.assertEqual(self.watch.held["worker"][1]["pid"], WORKER)
        self.assertTrue(self.watch.close())

    def test_missing_direct_pid_refuses_before_open(self):
        self.members.remove(DIRECT)
        with self.assertRaisesRegex(observer.ObservationRefused, "^direct_missing$"):
            self.watch.poll()
        self.api.open.assert_not_called()

    def test_failed_open_of_disappeared_nonrequired_pid_never_earns_credit(self):
        self.assertTrue(self.watch.poll())
        self.third(observer.ImageUnavailable(31))
        def open_member(pid):
            self.members.remove(pid)
            return None
        self.api.open.side_effect = open_member
        self.assertTrue(self.watch.poll())
        self.assertEqual(self.watch.transients, {})
        self.assertTrue(self.watch.close())

    def test_failed_open_of_member_that_stays_in_job_refuses(self):
        self.assertTrue(self.watch.poll())
        self.third(observer.ImageUnavailable(31))
        self.api.open.side_effect = lambda pid: None
        with self.assertRaisesRegex(observer.ObservationRefused, "^process_open$"):
            self.watch.poll()
        self.assertTrue(self.watch.close())

    def test_transient_evidence_has_a_hard_bound_and_same_pid_can_reappear(self):
        self.assertTrue(self.watch.poll())
        for sequence in range(observer.MAX_TRANSIENTS):
            self.third(observer.ImageUnavailable(31))
            self.api.creation.side_effect = lambda handle, pid, offset=sequence: 10_000 + pid + offset
            self.assertTrue(self.watch.poll())
            self.members.remove(OTHER)
        self.third(observer.ImageUnavailable(31))
        self.api.creation.side_effect = lambda handle, pid: 99_999
        with self.assertRaisesRegex(observer.ObservationRefused, "^transient_roster$"):
            self.watch.poll()
        self.assertEqual(len(self.watch.transients), observer.MAX_TRANSIENTS)
        self.assertTrue(self.watch.close())

    def test_unknown_terminal_still_closes_both_retained_handles(self):
        self.assertTrue(self.watch.poll())
        self.close_roles()
        self.waits[WORKER] = observer.WAIT_TIMEOUT
        with self.assertRaisesRegex(observer.ObservationRefused, "^process_exit$"):
            self.watch.finish()
        self.assertEqual([call.args[0] for call in self.api.close.call_args_list], [DIRECT, WORKER])

    def test_failed_handle_close_is_sticky_and_all_handles_are_offered_once(self):
        self.assertTrue(self.watch.poll())
        self.close_roles()
        self.api.close.side_effect = [OSError("synthetic close"), True]
        with self.assertRaisesRegex(observer.ObservationRefused, "^handle_close$"):
            self.watch.finish()
        self.assertFalse(self.watch.close())
        self.assertEqual([call.args[0] for call in self.api.close.call_args_list], [DIRECT, WORKER])


PYTHON = Path(sys.executable).resolve()
PYTHONW = PYTHON.with_name("pythonw.exe")


@unittest.skipUnless(os.name == "nt" and PYTHONW.is_file(), "Windows and installed windowless interpreter")
class WindowsJobTest(unittest.TestCase):
    def test_actual_owned_job_holds_exact_python_images_and_closes(self):
        temporary = env.safe_path(Path("D:/Dev/_Temp"), directory=True)
        self.assertEqual(temporary.resolve(strict=True), temporary)
        root = Path(tempfile.mkdtemp(prefix="locallore-narration-observer-v1-", dir=temporary))
        print(f"Retained synthetic Job capture: {root}", flush=True)
        jobs = []
        watch = None
        qualified_polls = 0
        api = observer.WindowsProcessApi()
        create = env.host.WindowsJob

        def create_job(pid):
            job = create(pid)
            jobs.append(job)
            return job

        def sample(child):
            nonlocal watch, qualified_polls
            self.assertEqual(len(jobs), 1)
            if watch is None:
                watch = observer.NarrationProcessObserver(api, jobs[0].handle, child.pid, PYTHON, PYTHONW)
            qualified_polls += int(watch.poll())
            # The shared supervisor continues sampling only while this is false.
            return False

        with patch.object(env.host, "WindowsJob", side_effect=create_job):
            try:
                value = env.supervise([str(PYTHON), "-I", "-S", "-B", str(Path(__file__).resolve()), "--fixture"],
                                      BARRIER, root, 8, sample)
                env.create_json(root / "job-terminal-v1.json", value)
                self.assertEqual(value["status"], "child_exited")
                self.assertEqual(value["worker_returncode"], 0)
                self.assertTrue(value["cleanup_complete"])
                self.assertTrue(value["output_capture_complete"])
                self.assertEqual((value["stdout_bytes"], value["stderr_bytes"]), (0, 0))
                self.assertIsNotNone(watch)
                self.assertGreaterEqual(qualified_polls, 2)
                proof = watch.finish()
                env.create_json(root / "observer-proof-v1.json", proof)
                self.assertTrue(proof["handles_closed"])
                self.assertEqual(proof["unclassified_exits"], [])
                self.assertEqual([Path(proof[role]["executable"]) for role in ("direct", "worker")],
                                 [PYTHON, PYTHONW])
                self.assertEqual([proof[role]["exit"] for role in ("direct", "worker")], [0, 0])
            finally:
                if watch is not None:
                    self.assertTrue(watch.close())


def fixture():
    if os.name != "nt" or sys.stdin.buffer.read(len(BARRIER) + 1) != BARRIER:
        return 1
    child = subprocess.Popen([str(PYTHONW), "-I", "-S", "-B", "-c", "import time; time.sleep(0.7)"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
    return child.wait(timeout=4)


if __name__ == "__main__":
    if sys.argv[1:] == ["--fixture"]:
        raise SystemExit(fixture())
    unittest.main()
