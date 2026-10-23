"""Explicit, test-only UI save/resume proof across a production-app force-stop.

Never installs, clears app data, or runs automatically from the host checks.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from runtime_spike import run_process

APP = "org.locallore.app"
TEST_APP = APP + ".test"
RUNNER = TEST_APP + "/androidx.test.runner.AndroidJUnitRunner"
CLASS = "org.locallore.app.DurableRestartTest"
METHODS = ("checkpointAcceptedStory", "resumeAfterProcessStop")
STAGES = {"local_apk", "app_identity", "test_identity", "checkpoint", "stop_identity",
          "stop_command", "stop_absence", "resume", "final_identity", "final_stop",
          "final_absence", "none"}


class ProbeFailure(Exception):
    """Only fixed stages escape to reports; never retain command output."""
    def __init__(self, stage):
        self.stage = stage if stage in STAGES else "none"


def apk_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def passed_instrumentation(data, method):
    """Recognize one real JUnit pass, not merely an ADB exit code or OK substring."""
    try:
        text = data.decode("utf-8", errors="strict")
        records, record, result, code = [], {}, {}, None
        continuation = None
        for line in text.splitlines():
            if line.startswith("INSTRUMENTATION_STATUS: "):
                key, separator, value = line[24:].partition("=")
                if not separator or key in record:
                    return False
                record[key] = value
                continuation = (record, key)
            elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
                number = line[29:]
                if number not in ("1", "0"):
                    return False
                records.append((number, record))
                record = {}
                continuation = None
            elif line.startswith("INSTRUMENTATION_RESULT: "):
                key, separator, value = line[24:].partition("=")
                if not separator or key in result or code is not None:
                    return False
                result[key] = value
                continuation = (result, key)
            elif line.startswith("INSTRUMENTATION_CODE: "):
                if code is not None:
                    return False
                code = line[22:]
                continuation = None
            elif line.startswith("INSTRUMENTATION_"):
                return False
            elif line:
                if continuation is None or continuation[1] not in ("stream", "stack"):
                    return False
                values, key = continuation
                values[key] += "\n" + line
        if record or code != "-1" or [number for number, _ in records] != ["1", "0"]:
            return False
        for _, values in records:
            if any(values.get(key) != value for key, value in {
                "class": CLASS, "test": method, "numtests": "1", "current": "1"}.items()):
                return False
            if "stack" in values or "Error" in values:
                return False
        stream = result.get("stream", "")
        return (set(result) <= {"stream"} and
                re.fullmatch(r"\s*Time: [0-9.]+\s+OK \(1 test\)\s*", stream) is not None)
    except (UnicodeError, ValueError, TypeError):
        return False


class Transport:
    def __init__(self, adb, serial, process=run_process):
        self.adb, self.serial, self.process = str(adb), serial, process
        self.clients_cleaned = True

    def command(self, arguments, stage, deadline=20):
        # Once a launcher is unaccounted for, do not race it with another client.
        if not self.clients_cleaned:
            raise ProbeFailure(stage)
        try:
            result = self.process([self.adb, "-s", self.serial, *arguments],
                                  deadline=deadline, max_output=131_072)
        except Exception:
            self.clients_cleaned = False
            raise ProbeFailure(stage) from None
        self.clients_cleaned = self.clients_cleaned and result.cleanup_complete is True
        if (not self.clients_cleaned or result.status != "completed" or
                type(result.returncode) is not int or result.returncode != 0):
            raise ProbeFailure(stage)
        if not isinstance(result.stdout, bytes):
            raise ProbeFailure(stage)
        return result.stdout

    def identity(self, package, expected, stage):
        data = self.command(["shell", "pm", "path", package], stage)
        try:
            paths = data.decode("ascii").splitlines()
            if len(paths) != 1 or not re.fullmatch(r"package:/data/app/[A-Za-z0-9_./+=~-]+\.apk", paths[0]):
                raise ProbeFailure(stage)
            path = paths[0][8:]
            output = self.command(["shell", "sha256sum " + shlex.quote(path)], stage)
            if output.decode("ascii").strip() != expected + "  " + path:
                raise ProbeFailure(stage)
        except UnicodeError:
            raise ProbeFailure(stage) from None

    def stop(self, expected, stages):
        self.identity(APP, expected, stages[0])
        self.command(["shell", "am", "force-stop", APP], stages[1])
        # pidof 1 means absent; errors and unexpected exit codes remain unknown.
        probe = ("pidof " + APP + " >/dev/null 2>&1; c=$?; "
                 "if [ \"$c\" = 0 ]; then printf running; "
                 "elif [ \"$c\" = 1 ]; then printf absent; else exit 2; fi")
        if self.command(["shell", probe], stages[2]) != b"absent":
            raise ProbeFailure(stages[2])

    def phase(self, method, token, stage):
        output = self.command(["shell", "am", "instrument", "-w", "-r", "-e", "class",
                               CLASS + "#" + method, "-e", "localloreRestart", token,
                               RUNNER], stage, deadline=180)
        if not passed_instrumentation(output, method):
            raise ProbeFailure(stage)


def execute(transport, apk, test_apk):
    """Return only fixed metadata. All attempts are retained before execution."""
    report = {"version": 1, "scope": "android_test_only_app_process_restart", "status": "failed",
              "apk_sha256": None, "test_apk_sha256": None, "attempts": [],
              "adb_clients_cleaned": True, "app_process_absent": False,
              "final_cleanup_stage": "none", "failure_stage": "none"}
    token = uuid.uuid4().hex
    expected = None
    paths = (apk, test_apk)
    def identities(stage_app="app_identity", stage_test="test_identity"):
        for path, digest in zip(paths, expected):
            if apk_digest(path) != digest:
                raise ProbeFailure("local_apk")
        transport.identity(APP, expected[0], stage_app)
        transport.identity(TEST_APP, expected[1], stage_test)
    def attempt(phase, action):
        row = {"phase": phase, "passed": False, "failure_stage": "none",
               "adb_clients_cleaned": transport.clients_cleaned}
        report["attempts"].append(row)
        try:
            action()
            row["passed"] = True
        except ProbeFailure as error:
            row["failure_stage"] = error.stage
            raise
        except OSError:
            row["failure_stage"] = "local_apk"
            raise ProbeFailure("local_apk") from None
        finally:
            row["adb_clients_cleaned"] = transport.clients_cleaned
    try:
        expected = tuple(apk_digest(path) for path in paths)
        report["apk_sha256"], report["test_apk_sha256"] = expected
        def checkpoint():
            identities()
            transport.phase(METHODS[0], token, "checkpoint")
        attempt("checkpoint", checkpoint)
        def process_stop():
            if apk_digest(apk) != expected[0]:
                raise ProbeFailure("local_apk")
            transport.stop(expected[0], ("stop_identity", "stop_command", "stop_absence"))
        attempt("process_stop", process_stop)
        def resume():
            identities()
            transport.phase(METHODS[1], token, "resume")
        attempt("resume", resume)
        report["status"] = "passed"
    except ProbeFailure as error:
        report["failure_stage"] = error.stage
    except Exception:
        report["failure_stage"] = "local_apk"
    finally:
        if expected is not None:
            try:
                if apk_digest(apk) != expected[0]:
                    raise ProbeFailure("final_identity")
                transport.stop(expected[0], ("final_identity", "final_stop", "final_absence"))
                report["app_process_absent"] = True
            except ProbeFailure as error:
                report["final_cleanup_stage"] = error.stage
                report["status"] = "failed"
            except Exception:
                report["final_cleanup_stage"] = "final_identity"
                report["status"] = "failed"
        report["adb_clients_cleaned"] = transport.clients_cleaned
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("adb", "apk", "test-apk", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--serial", required=True)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", args.serial):
        parser.error("invalid serial")
    report = execute(Transport(args.adb, args.serial), args.apk, args.test_apk)
    # The explicit output is the only report destination; no raw logs are written.
    try:
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        print('{"status":"failed","failure_stage":"report_write"}')
        return 2
    print(json.dumps(report))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
