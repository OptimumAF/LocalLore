"""Host-only output evidence tests; fake Python workers never invoke Android tools.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import io
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from benchmarks import receipt_avd_environment as env


class FaultFile:
    def __init__(self, wrapped, failure):
        self.wrapped, self.failure, self.close_calls = wrapped, failure, 0

    def write(self, data):
        if self.failure == "write":
            raise OSError("synthetic write failure")
        if self.failure == "short":
            return self.wrapped.write(data[:-1])
        return self.wrapped.write(data)

    def flush(self):
        if self.failure == "flush":
            raise OSError("synthetic flush failure")
        self.wrapped.flush()

    def fileno(self):
        return self.wrapped.fileno()

    def close(self):
        self.close_calls += 1
        self.wrapped.close()
        if self.failure == "close":
            raise OSError("synthetic close failure")


class DeferredPipe(io.BytesIO):
    def __init__(self, gate, data=b"", error=False):
        super().__init__(data)
        self.gate, self.error = gate, error

    def read(self, count=-1):
        if not self.gate.wait(3):
            raise RuntimeError("Test did not release fake reader")
        if self.error:
            raise RuntimeError("Synthetic reader failure")
        return super().read(count)


@unittest.skipUnless(os.name == "nt", "Windows supervisor ownership")
class ReceiptSupervisorEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def test_empty_files_created_and_forced_before_spawn_then_job_before_barrier(self):
        order = []
        real_force = env.os.fsync

        def force(fd):
            real_force(fd)
            order.append("force")

        child = mock.Mock(pid=123, returncode=0)
        child.stdout, child.stderr = io.BytesIO(b""), io.BytesIO(b"")
        child.stdin = mock.Mock()
        child.stdin.write.side_effect = lambda data: order.append("barrier")
        child.poll.return_value = 0

        def spawn(*args, **kwargs):
            self.assertEqual(order, ["force", "force"])
            self.assertEqual([p.read_bytes() for p in map(self.root.__truediv__, env.LiveOutput.names)], [b"", b""])
            order.append("spawn")
            return child

        def job(pid):
            self.assertEqual(pid, 123)
            order.append("job")
            return mock.Mock(close=mock.Mock(return_value=True))

        with mock.patch.object(env.os, "fsync", side_effect=force), mock.patch.object(
                env.subprocess, "Popen", side_effect=spawn), mock.patch.object(env.host, "WindowsJob", side_effect=job):
            result = env.supervise(["fake-python"], b"barrier", self.root, 5, lambda _: True)
        self.assertEqual(order[:5], ["force", "force", "spawn", "job", "barrier"])
        self.assertEqual(result["status"], "child_exited")
        self.assertTrue(result["cleanup_complete"] and result["output_capture_complete"])

    def test_existing_evidence_refuses_without_spawn_or_overwrite(self):
        for name in env.LiveOutput.names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                (root / name).write_bytes(b"prior evidence")
                with mock.patch.object(env.subprocess, "Popen") as spawn:
                    result = env.supervise(["must-not-spawn"], b"x", root, 5, lambda _: True)
                spawn.assert_not_called()
                self.assertEqual(result["status"], "evidence_failed")
                self.assertFalse(result["output_capture_complete"])
                self.assertEqual((root / name).read_bytes(), b"prior evidence")
                self.assertEqual(list(root.iterdir()), [root / name])

    def test_second_create_failure_preserves_forced_first_and_prevents_spawn(self):
        original = Path.open

        def opened(path, *args, **kwargs):
            if path.name == env.LiveOutput.names[1]:
                raise OSError("Synthetic second create failure")
            return original(path, *args, **kwargs)

        with mock.patch.object(Path, "open", new=opened), mock.patch.object(env.subprocess, "Popen") as spawn:
            result = env.supervise(["must-not-spawn"], b"x", self.root, 5, lambda _: True)
        spawn.assert_not_called()
        self.assertEqual(result["status"], "evidence_failed")
        self.assertEqual((self.root / env.LiveOutput.names[0]).read_bytes(), b"")
        self.assertFalse((self.root / env.LiveOutput.names[1]).exists())

    def test_initial_force_failure_preserves_partial_files_without_spawn(self):
        with mock.patch.object(env.os, "fsync", side_effect=OSError("Synthetic initial force")), mock.patch.object(
                env.subprocess, "Popen") as spawn:
            result = env.supervise(["must-not-spawn"], b"x", self.root, 5, lambda _: True)
        spawn.assert_not_called()
        self.assertEqual(result["status"], "evidence_failed")
        self.assertFalse(result["output_capture_complete"])
        self.assertEqual((self.root / env.LiveOutput.names[0]).read_bytes(), b"")

    def test_append_forces_before_count_visibility_and_sizes_is_copy(self):
        capture = env.LiveOutput(self.root)
        self.addCleanup(capture.close)
        real_force = env.os.fsync
        events = []

        def force(fd):
            events.append((os.fstat(fd).st_size, list(capture._sizes)))
            real_force(fd)

        with mock.patch.object(env.os, "fsync", side_effect=force):
            self.assertTrue(capture.append(0, b"out"))
            self.assertTrue(capture.append(1, b"err!"))
        self.assertEqual(events, [(3, [0, 0]), (4, [3, 0])])
        sizes = capture.sizes
        sizes[0] = 999
        self.assertEqual(capture.sizes, [3, 4])
        self.assertEqual([p.read_bytes() for p in map(self.root.__truediv__, capture.names)], [b"out", b"err!"])

    def test_combined_cap_retains_exact_prefix_and_latches_overflow(self):
        capture = env.LiveOutput(self.root)
        self.addCleanup(capture.close)
        self.assertTrue(capture.append(0, b"o" * (env.MAX_OUTPUT - 2)))
        self.assertTrue(capture.append(1, b"ee"))
        self.assertFalse(capture.append(1, b"extra"))
        self.assertFalse(capture.append(0, b"later"))
        self.assertEqual(capture.sizes, [env.MAX_OUTPUT - 2, 2])
        self.assertTrue(capture.overflow.is_set())
        self.assertFalse(capture.failed.is_set())
        self.assertEqual((self.root / capture.names[1]).read_bytes(), b"ee")

    def test_concurrent_channels_share_one_cap(self):
        capture = env.LiveOutput(self.root)
        self.addCleanup(capture.close)
        threads = [threading.Thread(target=capture.append, args=(channel, bytes([65 + channel]) * 200000))
                   for channel in (0, 1)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(3)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sum(capture.sizes), env.MAX_OUTPUT)
        self.assertTrue(capture.overflow.is_set())
        self.assertFalse(capture.failed.is_set())
        self.assertEqual([p.stat().st_size for p in map(self.root.__truediv__, capture.names)], capture.sizes)

    def test_short_write_flush_write_and_force_errors_are_sticky_without_false_counts(self):
        for failure in ("short", "write", "flush", "fsync"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                capture = env.LiveOutput(root)
                self.assertTrue(capture.append(1, b"forced prior"))
                if failure != "fsync":
                    capture._files[0] = FaultFile(capture._files[0], failure)
                patcher = mock.patch.object(env.os, "fsync", side_effect=OSError("synthetic force"))
                with patcher if failure == "fsync" else mock.patch.object(env.time, "sleep"):
                    self.assertFalse(capture.append(0, b"uncertain write"))
                self.assertEqual(capture.sizes, [0, 12])
                self.assertTrue(capture.failed.is_set())
                self.assertFalse(capture.append(1, b"later"))
                self.assertFalse(capture.close())
                self.assertEqual((root / capture.names[1]).read_bytes(), b"forced prior")

    def test_invalid_append_and_closed_capture_never_write(self):
        for channel, data in ((True, b"x"), (2, b"x"), (0, bytearray(b"x")), (0, "x")):
            with self.subTest(channel=channel, data=data), tempfile.TemporaryDirectory() as directory:
                capture = env.LiveOutput(Path(directory).resolve())
                self.assertFalse(capture.append(channel, data))
                self.assertTrue(capture.failed.is_set())
                self.assertEqual(capture.sizes, [0, 0])
                capture.close()
        capture = env.LiveOutput(self.root)
        self.assertTrue(capture.close())
        self.assertTrue(capture.close())
        self.assertFalse(capture.append(0, b"after close"))
        self.assertEqual(capture.sizes, [0, 0])

    def test_close_failure_is_sticky_and_idempotent_preserves_bytes(self):
        capture = env.LiveOutput(self.root)
        self.assertTrue(capture.append(0, b"forced"))
        stream = FaultFile(capture._files[0], "close")
        capture._files[0] = stream
        self.assertFalse(capture.close())
        self.assertFalse(capture.close())
        self.assertEqual(stream.close_calls, 1)
        self.assertEqual(capture.sizes, [6, 0])
        self.assertEqual((self.root / capture.names[0]).read_bytes(), b"forced")

    def fake_supervise(self, *, reader_error=False, force_error=False, close_error=False, stop=False,
                       data=b"late output"):
        gate = threading.Event()
        child = mock.Mock(pid=123, returncode=0)
        child.stdin = io.BytesIO()
        child.stdout = DeferredPipe(gate, data, error=reader_error)
        child.stderr = io.BytesIO(b"")
        child.poll.return_value = None if stop else 0
        job = mock.Mock()
        job.close.side_effect = lambda: (gate.set() or True)
        original_force, original_close = env.os.fsync, env.LiveOutput.close
        force_calls = []

        def force(fd):
            force_calls.append(fd)
            if force_error and len(force_calls) > 2:
                raise OSError("Synthetic trailing force failure")
            original_force(fd)

        def close(capture):
            result = original_close(capture)
            if close_error:
                capture.failed.set()
                return False
            return result

        if stop:
            env.create_json(self.root / "stop-v1.json", {"version": 1, "proposal_sha256": "a" * 64, "action": "stop"})
        with mock.patch.object(env.subprocess, "Popen", return_value=child), mock.patch.object(
                env.host, "WindowsJob", return_value=job), mock.patch.object(
                env.os, "fsync", side_effect=force), mock.patch.object(env.LiveOutput, "close", new=close):
            return env.supervise(["fake-python"], b"barrier", self.root, 5, lambda _: True, "a" * 64)

    def test_late_reader_exception_overrides_child_exit(self):
        result = self.fake_supervise(reader_error=True)
        self.assertEqual(result["status"], "evidence_failed")
        self.assertTrue(result["cleanup_complete"])
        self.assertFalse(result["output_capture_complete"])

    def test_late_force_error_overrides_child_exit_and_retains_uncertain_bytes(self):
        result = self.fake_supervise(force_error=True)
        self.assertEqual(result["status"], "evidence_failed")
        self.assertEqual(result["stdout_bytes"], 0)
        self.assertEqual((self.root / env.LiveOutput.names[0]).read_bytes(), b"late output")
        self.assertFalse(result["output_capture_complete"])

    def test_late_close_error_overrides_exact_stop(self):
        result = self.fake_supervise(close_error=True, stop=True)
        self.assertEqual(result["status"], "evidence_failed")
        self.assertFalse(result["output_capture_complete"])
        self.assertTrue(result["cleanup_complete"])

    def test_trailing_overflow_is_output_limit_not_successful_capture(self):
        result = self.fake_supervise(data=b"x" * (env.MAX_OUTPUT + 1))
        self.assertEqual(result["status"], "output_limit")
        self.assertEqual(result["stdout_bytes"], env.MAX_OUTPUT)
        self.assertFalse(result["output_capture_complete"])
        self.assertTrue(result["cleanup_complete"])
        self.assertEqual((self.root / env.LiveOutput.names[0]).stat().st_size, env.MAX_OUTPUT)

    def test_successful_exit_retains_forced_output_without_terminal_receipt(self):
        result = self.fake_supervise()
        self.assertEqual(result["status"], "child_exited")
        self.assertTrue(result["output_capture_complete"] and result["cleanup_complete"])
        self.assertEqual(result["stdout_bytes"], 11)
        self.assertEqual((self.root / env.LiveOutput.names[0]).read_bytes(), b"late output")
        self.assertFalse((self.root / "owner-result-v1.json").exists())

    def test_stalled_reader_returns_unknown_counts_without_lock_or_close_wait(self):
        child = mock.Mock(pid=123, returncode=0)
        child.stdin, child.stdout, child.stderr = io.BytesIO(), io.BytesIO(), io.BytesIO()
        child.poll.return_value = 0
        readers = []

        def thread(**kwargs):
            value = mock.Mock()
            value.is_alive.return_value = True
            readers.append(value)
            return value

        real_capture = env.LiveOutput
        captures = []

        def capture(root):
            value = real_capture(root)
            captures.append(value)
            return value

        with mock.patch.object(env.subprocess, "Popen", return_value=child), mock.patch.object(
                env.host, "WindowsJob", return_value=mock.Mock(close=mock.Mock(return_value=True))), mock.patch.object(
                env.threading, "Thread", side_effect=thread), mock.patch.object(env, "LiveOutput", side_effect=capture):
            result = env.supervise(["fake"], b"barrier", self.root, 5, lambda _: True)
        self.assertEqual(result["status"], "evidence_failed")
        self.assertFalse(result["cleanup_complete"] or result["output_capture_complete"])
        self.assertIsNone(result["stdout_bytes"])
        self.assertIsNone(result["stderr_bytes"])
        self.assertFalse(captures[0]._closed)
        for reader in readers:
            reader.join.assert_called_once_with(timeout=2)
        # These synthetic readers never ran: release only our own test handles.
        captures[0].close()

    def test_invalid_budget_refuses_before_evidence_or_spawn(self):
        for seconds, request in ((0, b"x"), (1201, b"x"), (True, b"x"), (5, b"x" * 131073)):
            with self.subTest(seconds=seconds), mock.patch.object(env.subprocess, "Popen") as spawn:
                with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_budget"):
                    env.supervise(["must-not-spawn"], request, self.root, seconds, lambda _: True)
                spawn.assert_not_called()
                self.assertEqual(list(self.root.iterdir()), [])

    def test_actual_hard_owner_loss_retains_forced_prefix_and_kills_inner_job(self):
        worker = self.root / "fake-worker.py"
        worker.write_text(
            "import os,subprocess,sys,time,json\nfrom pathlib import Path\n"
            "sys.stdin.buffer.read()\n"
            "child=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(60)'])\n"
            "p=Path(sys.argv[1]);f=p.open('x');json.dump({'worker':os.getpid(),'descendant':child.pid},f);f.flush();os.fsync(f.fileno());f.close()\n"
            "os.write(1,b'forced stdout prefix\\n');os.write(2,b'forced stderr prefix\\n');time.sleep(60)\n", encoding="utf-8")
        driver = self.root / "fake-supervisor.py"
        driver.write_text(
            "import os,sys,threading\nfrom pathlib import Path\n"
            "sys.stdin.buffer.read();sys.path.insert(0,sys.argv[1])\n"
            "from benchmarks import receipt_avd_environment as env\n"
            "root=Path(sys.argv[2]); real=env.os.fsync; forced=set();lock=threading.RLock()\n"
            "def force(fd):\n"
            " real(fd)\n"
            " with lock:\n"
            "  for i,name in enumerate(env.LiveOutput.names):\n"
            "   path=root/name\n"
            "   if path.exists() and os.fstat(fd).st_ino>0 and os.stat(path).st_ino==os.fstat(fd).st_ino and path.read_bytes()==(b'forced stdout prefix\\n' if i==0 else b'forced stderr prefix\\n'):forced.add(i)\n"
            "  if forced=={0,1} and not (root/'forced-ack.json').exists():\n"
            "   env.create_json(root/'forced-ack.json',{'forced':True})\n"
            "   f=(root/'forced-ready-v1.txt').open('xb');f.flush();real(f.fileno());f.close()\n"
            "env.os.fsync=force\n"
            "result=env.supervise([sys.executable,'-B',str(root/'fake-worker.py'),str(root/'captured-pids.json')],b'barrier',root,30,lambda _:True)\n"
            "env.create_json(root/'owner-result-v1.json',result)\n", encoding="utf-8")
        supervisor = subprocess.Popen([sys.executable, "-B", str(driver), str(Path(env.__file__).resolve().parents[1]), str(self.root)],
                                      stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handles = []
        owner_job = env.host.WindowsJob(supervisor.pid)
        try:
            supervisor.stdin.write(b"barrier")
            supervisor.stdin.close()
            until = time.monotonic() + 10
            while not (self.root / "forced-ready-v1.txt").exists() and supervisor.poll() is None and time.monotonic() < until:
                time.sleep(.02)
            self.assertIsNone(supervisor.poll(), supervisor.stderr.read() if supervisor.poll() is not None else b"")
            self.assertTrue((self.root / "forced-ready-v1.txt").is_file())
            self.assertEqual(env.read_json(self.root / "forced-ack.json", 1024), {"forced": True})
            captured = env.read_json(self.root / "captured-pids.json", 1024)
            identities = {key: env.process_identity(pid) for key, pid in captured.items()}
            self.assertNotEqual(captured["worker"], captured["descendant"])
            for identity in identities.values():
                handle = kernel.OpenProcess(0x00100000, False, identity["pid"])  # SYNCHRONIZE, non-inheritable
                self.assertTrue(handle, "Cannot acquire exact live process handle")
                handles.append(handle)
                self.assertEqual(kernel.WaitForSingleObject(handle, 0), 258)  # WAIT_TIMEOUT: still alive
            self.assertFalse((self.root / "owner-result-v1.json").exists())
            # Kill ONLY the exact supervisor. Do not close the safety job until
            # both inner descendants are proven dead, well before their 60s timer.
            supervisor.kill()
            supervisor.wait(timeout=5)
            for handle in handles:
                self.assertEqual(kernel.WaitForSingleObject(handle, 5000), 0,
                                 "Exact inner process must terminate before safety-job cleanup")
            self.assertFalse((self.root / "owner-result-v1.json").exists())
            self.assertEqual((self.root / env.LiveOutput.names[0]).read_bytes(), b"forced stdout prefix\n")
            self.assertEqual((self.root / env.LiveOutput.names[1]).read_bytes(), b"forced stderr prefix\n")
        finally:
            self.assertTrue(owner_job.close())
            supervisor.wait(timeout=5)
            supervisor.stderr.close()
            for handle in handles:
                self.assertTrue(kernel.CloseHandle(handle))


if __name__ == "__main__":
    unittest.main()
