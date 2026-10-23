"""Explicit model-free checks on one authorized emulator. Never part of default CI."""
import argparse
import json
from pathlib import Path
import shlex
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "benchmarks"))
import android_runtime_spike as spike


def checks(device, owner, rows=None):
    rows = [] if rows is None else rows
    worker = spike.NativeWorker(device, owner)
    for name, command, kwargs, expected in (
        ("success", "printf synthetic-ok", {}, "completed"),
        ("ignore_term_cancel", 'trap "" TERM; while :; do :; done', {"cancel_after": 2}, "cancelled"),
        ("cancel_before_release", ": > forbidden-child", {"cancel_after": 1, "release": False}, "cancelled"),
        ("nonzero_child_exit", "exit 23", {}, "failed"),
    ):
        result = worker.run("/system/bin/sh", ["-c", command], deadline=10, **kwargs)
        passed = result.status == expected and result.cleanup_complete and result.adb_cleanup_complete
        rows.append({"check": name, "status": result.status, "exit_code": result.returncode,
                     "remote_cleanup": result.cleanup_complete, "adb_cleanup": result.adb_cleanup_complete,
                     "passed": passed})
    result = worker.run(spike.REMOTE + "/cache/missing-executable", [], deadline=10)
    rows.append({"check": "exec_failure", "status": result.status, "exit_code": result.returncode,
                 "remote_cleanup": result.cleanup_complete, "adb_cleanup": result.adb_cleanup_complete,
                 "passed": result.status == "failed" and result.returncode == 127
                           and result.cleanup_complete and result.adb_cleanup_complete})
    for name in ("lost_adb_client", "independent_deadline", "blocked_output"):
        row = {"check": name, "status": "started", "passed": False}
        rows.append(row)
        run = spike.REMOTE + "/runs/" + uuid.uuid4().hex
        device.shell("mkdir", "-m", "700", run)
        device.shell("ln", "-s", "/system/bin/sh", run + "/worker")
        device.put_bytes(b"", run + "/request")
        device.script(": > " + shlex.quote(run + "/release"))
        command = ("while :; do printf '%1024s' x; done" if name == "blocked_output"
                   else 'trap "" TERM HUP; while :; do :; done')
        cancelled = threading.Event()
        timer = threading.Timer(.8, cancelled.set) if name == "lost_adb_client" else None
        if timer:
            timer.start()
        try:
            result = device.raw(["shell", "exec " + shlex.join([owner, run, "3", run + "/worker", "-c", command])],
                                deadline=10, cancel=cancelled)
        finally:
            if timer:
                timer.cancel()
                timer.join()
        until, done, gone = time.monotonic() + 8, None, False
        while time.monotonic() < until:
            done = spike.parse_done(device.read_optional(run + "/done"))
            if done:
                pid = int(device.read_optional(run + "/owner"))
                gone = device.identity(pid) is None
                if gone:
                    break
            time.sleep(.05)
        expected = {"lost_adb_client": "cancelled", "independent_deadline": "completed", "blocked_output": "output_limit"}[name]
        passed = bool(done and done[0] in ("timeout", "cancelled") and gone and result.status == expected
                      and result.cleanup_complete)
        row.update(adb_status=result.status, native_status=done[0] if done else None,
                   exit_code=done[1] if done else None, owner_gone=gone, passed=passed)
        row.pop("status")
        if passed:
            device.shell("rm", "-f", "--", *[run + "/" + item for item in ("worker", "request", "release", "owner", "done")])
            device.shell("rmdir", run)
    return {"version": 1, "scope": "android_model_free_process_ownership", "checks": rows,
            "passed": all(row["passed"] for row in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--owner", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    try:
        device = spike.Device(args.adb, args.serial)
        device.initialize()
        report = checks(device, device.cached(args.owner), rows)
    except (spike.Failure, OSError, ValueError):
        report = {"version": 1, "passed": False, "status": "controller_check_failed", "checks": rows}
    text = json.dumps(report, indent=2) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
