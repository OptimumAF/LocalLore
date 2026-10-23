"""Explicit two-role Android SDK experiment; never imported by gameplay/default CI.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import math
from pathlib import Path
import re
import shlex
import threading
import time
import uuid

import android_runtime_spike as spike

SESSION = re.compile(r"[0-9a-f]{32}")
FILES = ("request-1.json", "request-2.json", "result-1.json", "result-2.json", "cancel", "owner-v1")
STAGES = {"none", "unknown", "fixture", "preflight", "package_identity", "clean_start", "create_directory",
          "publish_request", "launch_instrumentation", "wait_result", "parse_result", "validate_director",
          "wait_terminal", "parse_terminal", "cancel", "join_launcher", "stop_package", "remove_directory", "commit",
          "model_identity", "initialize_device", "cache_artifacts", "provision_model"}
STATUSES = {"completed", "cancelled", "timeout", "setup_failed", "invalid_exchange", "invalid_terminal",
            "engine_rejected", "oracle_failed", "worker_failed", "cleanup_failed", "preflight_rejected", "committed"}


class WarmFailure(Exception):
    def __init__(self, category, stage):
        self.category = category if type(category) is str and category in STATUSES else "setup_failed"
        self.stage = stage if type(stage) is str and stage in STAGES else "unknown"
        super().__init__(self.category)


def parse_exchange(raw, session, step):
    if (type(raw) is not bytes or len(raw) > 131072 or type(session) is not str
            or not SESSION.fullmatch(session) or type(step) is not int or step not in (1, 2)):
        return None
    try:
        value = spike.strict_json(raw)
        if (not isinstance(value, dict) or set(value) != {"version", "session", "step", "result"}
                or type(value["version"]) is not int or value["version"] != 1
                or value["session"] != session or type(value["step"]) is not int or value["step"] != step):
            return None
        return spike.host.parse_worker(json.dumps(value["result"], allow_nan=False).encode("utf-8"))
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return None


def terminal_result(raw):
    """Validate final Java owners; process termination alone never supplies them."""
    if type(raw) is not bytes or len(raw) > 131072:
        return None
    parsed = spike.sdk_response(raw)
    if parsed is None:
        return None
    output, metrics = parsed
    worker = spike.host.parse_worker(output)
    if worker["text"]:
        return None
    try:
        lines = re.findall(rb"^INSTRUMENTATION_RESULT: metrics=(.*)\r?$", raw, re.MULTILINE)
        original = spike.strict_json(lines[0])
        for key in ("warm_engine_reused", "warm_cancel_observed"):
            if type(original.get(key)) is not bool:
                return None
            metrics[key] = original[key]
        count = original.get("warm_roles")
        if type(count) is not int or not 0 <= count <= 2:
            return None
        metrics["warm_roles"] = count
        if metrics["engines_opened"] not in (0, 1) or metrics["conversations_opened"] > 2:
            return None
        if metrics["warm_engine_reused"] != (count == 2):
            return None
        if worker["status"] == "completed" and not warm_owners(metrics):
            return None
        return worker, metrics
    except (ValueError, TypeError, UnicodeError, RecursionError, IndexError):
        return None


def warm_owners(metrics):
    return (isinstance(metrics, dict) and all(type(metrics.get(key)) is int and metrics[key] == value for key, value in
            {"engines_opened": 1, "engines_closed": 1, "conversations_opened": 2,
             "conversations_closed": 2, "warm_roles": 2}.items())
            and metrics.get("warm_engine_reused") is True and metrics.get("owners_balanced") is True
            and metrics.get("worker_off_main") is True and metrics.get("generated_text_logged") is False
            and metrics.get("warm_cancel_observed") is False
            and metrics.get("cleanup_requires_process_termination", False) is False)


def safe_session(value):
    value = value if isinstance(value, dict) else {}
    status = value.get("status")
    safe = {"status": status if type(status) is str and status in STATUSES else "cleanup_failed"}
    for key in ("stage", "cleanup_failure_stage"):
        stage = value.get(key, "none")
        safe[key] = stage if type(stage) is str and stage in STAGES else "unknown"
    for key in ("cleanup_complete", "adb_cleanup_complete", "directory_cleanup_complete", "cancel_requested"):
        safe[key] = value.get(key) is True
    wall = value.get("wall_ms", 0)
    safe["wall_ms"] = round(wall) if type(wall) in (int, float) and 0 <= wall <= 2 ** 31 and math.isfinite(wall) else 0
    source = value.get("sdk")
    safe["sdk"] = spike.safe_sdk_metrics(source)
    if isinstance(source, dict):
        for key in ("warm_engine_reused", "warm_cancel_observed"):
            if type(source.get(key)) is bool:
                safe["sdk"][key] = source[key]
        if type(source.get("warm_roles")) is int and 0 <= source["warm_roles"] <= 2:
            safe["sdk"]["warm_roles"] = source["warm_roles"]
    return safe


class BudgetedOracle:
    def __init__(self, native, session):
        self.native, self.session = native, session

    def run(self, *args, **kwargs):
        self.session.check_budget()
        if isinstance(self.session, WarmSdkSession):
            remaining = self.session.deadline - (time.monotonic() - self.session.started_at)
            if remaining < 1:
                raise WarmFailure("timeout", self.session.stage)
            kwargs["deadline"] = min(kwargs.get("deadline", 10), remaining)
        return self.native.run(*args, **kwargs)


def request_bytes(request, step):
    try:
        if (not isinstance(request, dict) or set(request) != {"version", "role", "prompt", "max_tokens", "context_tokens", "threads", "schema"}
                or type(step) is not int or step not in (1, 2)
                or request["role"] != ("director" if step == 1 else "narrator")
                or any(type(request[key]) is not int or request[key] != value for key, value in
                       {"version": 1, "context_tokens": 4096, "threads": 4}.items())
                or type(request["prompt"]) is not str or not request["prompt"].strip() or "\0" in request["prompt"]
                or type(request["max_tokens"]) is not int or not 1 <= request["max_tokens"] <= (350 if step == 1 else 220)
                or (request["schema"] is not None and not isinstance(request["schema"], dict))):
            raise ValueError()
        raw = json.dumps(request, allow_nan=False, ensure_ascii=False).encode("utf-8")
        if len(raw) > 32768:
            raise ValueError()
        return raw
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise WarmFailure("invalid_exchange", "publish_request") from None


class WarmSdkSession:
    def __init__(self, device, apk_sha256, deadline=60, cancel_after=None):
        if (type(deadline) not in (int, float) or not math.isfinite(deadline) or not 1 <= deadline <= 60
                or (cancel_after is not None and (type(cancel_after) not in (int, float)
                    or not math.isfinite(cancel_after) or not 0 < cancel_after <= deadline))):
            raise WarmFailure("setup_failed", "preflight")
        self.device, self.sdk = device, spike.SdkWorker(device, apk_sha256)
        self.session_id = uuid.uuid4().hex
        self.directory = "files/warm-" + self.session_id
        self.started_at, self.deadline, self.cancel_after = time.monotonic(), deadline, cancel_after
        self.stage, self.step, self.cancel_requested = "none", 0, False
        self.created, self.adb_clean, self.launcher, self.results = False, True, None, []
        self.host_cancel, self.finished = threading.Event(), threading.Event()
        self.final = None

    def check_budget(self):
        elapsed = time.monotonic() - self.started_at
        if self.cancel_after is not None and elapsed >= self.cancel_after:
            self.cancel_requested = True
            raise WarmFailure("cancelled", self.stage)
        if elapsed >= self.deadline:
            raise WarmFailure("timeout", self.stage)

    def private(self, command, request=b""):
        try:
            return self.device.shell("run-as", spike.PACKAGE, "/system/bin/sh", "-c", command, request=request)
        except Exception as error:
            self.adb_clean = self.adb_clean and getattr(error, "command_cleaned", False) is True
            raise

    def owned(self):
        path = shlex.quote(self.directory)
        self.private(f'[ -d {path} ] && [ ! -L {path} ] && [ ! -L {path}/owner-v1 ] && '
                     f'[ "$(cat {path}/owner-v1)" = locallore-warm-v1 ]')

    def read(self, name):
        if name not in FILES:
            raise WarmFailure("invalid_exchange", "wait_result")
        self.owned()
        path = shlex.quote(self.directory + "/" + name)
        return self.private(f'if [ -L {path} ]; then printf invalid; elif [ -f {path} ]; then '
                            f'if [ "$(stat -c %s {path})" -le 131072 ]; then head -c 131072 {path}; '
                            f'else printf oversized; fi; fi')

    def publish(self, name, data):
        if name not in FILES or name == "owner-v1":
            raise WarmFailure("invalid_exchange", "publish_request")
        self.control(self.sdk.verify_package)
        self.owned()
        path = shlex.quote(self.directory + "/" + name)
        partial = shlex.quote(self.directory + "/" + name + ".partial")
        # exec-in supplies stdin; adb shell stdin is not a binary request channel.
        command = f'[ ! -e {path} ] && [ ! -L {path} ] && [ ! -e {partial} ] && [ ! -L {partial} ] && umask 077 && cat > {partial}'
        try:
            result = self.device.raw(["exec-in", shlex.join(["run-as", spike.PACKAGE, "/system/bin/sh", "-c", command])], request=data)
        except Exception as error:
            self.adb_clean = self.adb_clean and getattr(error, "command_cleaned", False) is True
            raise
        self.adb_clean = self.adb_clean and result.cleanup_complete is True
        if result.status != "completed" or type(result.returncode) is not int or result.returncode != 0 or not result.cleanup_complete:
            raise WarmFailure("setup_failed", self.stage)
        if name.startswith("request-"):
            self.check_budget()
        self.private(f'[ ! -e {path} ] && [ ! -L {path} ] && mv {partial} {path}')

    def start(self):
        self.stage = "package_identity"
        self.control(self.sdk.verify_package)
        self.stage = "clean_start"
        if not self.control(self.sdk.stop):
            raise WarmFailure("cleanup_failed", self.stage)
        self.check_budget()
        self.stage = "create_directory"
        self.private("umask 077; mkdir " + shlex.quote(self.directory))
        self.created = True
        self.private("printf %s locallore-warm-v1 > " + shlex.quote(self.directory + "/owner-v1"))

    def control(self, function):
        try:
            return function()
        except Exception as error:
            self.adb_clean = self.adb_clean and getattr(error, "command_cleaned", False) is True
            raise

    def generate(self, request):
        step = self.step + 1
        raw = request_bytes(request, step)
        self.check_budget()
        if step == 1:
            self.start()
        elif self.launcher is None:
            raise WarmFailure("invalid_exchange", "publish_request")
        self.stage = "publish_request"
        # A step2 request/result already present cannot be a host-authorized next role.
        if self.read("request-2.json") or self.read("result-2.json"):
            raise WarmFailure("invalid_exchange", self.stage)
        self.check_budget()
        self.publish("request-" + str(step) + ".json", raw)
        if step == 1:
            self.check_budget()
            self.stage = "launch_instrumentation"
            def execute():
                try:
                    self.results.append(self.device.raw(["shell", shlex.join(["am", "instrument", "-w", "-r", "-e", "mode", "warm",
                        "-e", "session", self.session_id, spike.PACKAGE + "/.SpikeInstrumentation"])], deadline=80, cancel=self.host_cancel))
                except Exception:
                    self.results.append(spike.host.ProcessResult("spawn_failed", 0))
                finally:
                    self.finished.set()
            self.launcher = threading.Thread(target=execute, daemon=True)
            self.launcher.start()
        self.stage = "wait_result"
        while True:
            self.check_budget()
            terminal = self.finished.is_set()
            raw_result = self.read("result-" + str(step) + ".json")
            if raw_result:
                self.stage = "parse_result"
                parsed = parse_exchange(raw_result, self.session_id, step)
                if parsed is None:
                    raise WarmFailure("invalid_exchange", self.stage)
                if step == 1 and self.read("result-2.json"):
                    raise WarmFailure("invalid_exchange", self.stage)
                self.step = step
                return parsed
            # Publication can race launcher completion after the previous read.
            # Observe one read after completion before classifying a missing result.
            if terminal:
                raise WarmFailure("worker_failed", self.stage)
            self.finished.wait(.05)

    def finish(self):
        if self.final is not None:
            return self.final
        metadata = {"status": "cleanup_failed", "stage": "none", "cleanup_failure_stage": "none",
                    "cleanup_complete": False, "adb_cleanup_complete": False, "directory_cleanup_complete": False,
                    "cancel_requested": self.cancel_requested, "sdk": {}}
        launcher_clean, process_clean, files = False, False, False
        try:
            if self.launcher is not None and self.launcher.ident is not None:
                self.stage = "wait_terminal"
                # On failure/abandonment request cooperative drain. Never publish another role.
                if self.step < 2 or self.cancel_requested:
                    try:
                        self.stage = "cancel"
                        self.publish("cancel", b"")
                    except Exception:
                        metadata["cleanup_failure_stage"] = "cancel"
                until = time.monotonic() + (10 if self.step < 2 or self.cancel_requested else max(1, self.deadline - (time.monotonic() - self.started_at)))
                while not self.finished.wait(.05) and time.monotonic() < until:
                    pass
                self.host_cancel.set()
                self.stage = "join_launcher"
                self.launcher.join(timeout=8)
                launcher_clean = bool(not self.launcher.is_alive() and self.results and self.results[0].cleanup_complete is True)
                if launcher_clean:
                    result = self.results[0]
                    self.stage = "parse_terminal"
                    parsed = terminal_result(result.stdout)
                    if (result.status == "completed" and type(result.returncode) is int and result.returncode == 0 and parsed):
                        worker, metrics = parsed
                        metadata["sdk"] = metrics
                        metadata["status"] = "completed" if worker["status"] == "completed" else "worker_failed"
                    else:
                        metadata["status"] = "invalid_terminal"
                        metadata["stage"] = "parse_terminal"
                else:
                    metadata["cleanup_failure_stage"] = "join_launcher"
            else:
                # No started local launcher means no new SDK instrumentation was released.
                launcher_clean = True
                metadata["status"] = "setup_failed"
        except Exception as error:
            self.adb_clean = self.adb_clean and getattr(error, "command_cleaned", False) is True
            metadata["cleanup_failure_stage"] = self.stage if self.stage in STAGES else "unknown"
        finally:
            self.host_cancel.set()
            self.stage = "stop_package"
            try:
                process_clean = self.control(self.sdk.stop)
                if not process_clean:
                    metadata["cleanup_failure_stage"] = self.stage
                if process_clean and launcher_clean and self.adb_clean and self.created:
                    self.stage = "remove_directory"
                    self.owned()
                    names = FILES + tuple(name + ".partial" for name in FILES)
                    self.private("rm -f -- " + " ".join(shlex.quote(self.directory + "/" + name) for name in names))
                    self.private("rmdir " + shlex.quote(self.directory))
                    files = True
                elif not self.created and process_clean and launcher_clean and self.adb_clean:
                    files = True
            except Exception as error:
                self.adb_clean = self.adb_clean and getattr(error, "command_cleaned", False) is True
                metadata["cleanup_failure_stage"] = self.stage
            metadata.update(cleanup_complete=bool(process_clean and launcher_clean),
                            adb_cleanup_complete=bool(self.adb_clean and launcher_clean), directory_cleanup_complete=files)
            if not all(metadata[key] is True for key in ("cleanup_complete", "adb_cleanup_complete", "directory_cleanup_complete")):
                metadata["status"] = "cleanup_failed"
            metadata["wall_ms"] = min(2 ** 31, round((time.monotonic() - self.started_at) * 1000))
            self.final = metadata
        return metadata


def _run_warm(session, native, oracle_binary, case="gift"):
    report = {"version": 1, "scope": "android_sdk_shared_engine_smoke", "status": "not_started",
              "attempted_roles": 0, "roles": [], "oracle_runs": [], "phone_qualified": False,
              "quality_assessed": False, "durable_state": False, "failure_stage": "none"}
    observed = spike.ObservedOracle(BudgetedOracle(native, session), report["oracle_runs"])
    proposal, narration = None, None
    stage = "fixture"
    try:
        fixture = spike.oracle(observed, oracle_binary, "fixture", case)
        session.check_budget()
        if not fixture:
            raise WarmFailure("oracle_failed", stage)
        if fixture.get("preflight_error") is not None:
            report["status"] = "preflight_rejected" if fixture["preflight_error"] in spike.host.DOMAIN_ERRORS else "oracle_failed"
            return report
        if not isinstance(fixture.get("director"), dict):
            raise WarmFailure("oracle_failed", stage)
        request = fixture["director"]
        for step, role in enumerate(("director", "narrator"), 1):
            session.check_budget()
            request_bytes(request, step)
            report["attempted_roles"] += 1
            began = time.monotonic()
            row = {"role": role, "status": "not_completed"}
            report["roles"].append(row)
            generated = session.generate(request)
            # Revalidate even a defective adapter; raw text never enters a public row.
            generated = spike.host.parse_worker(json.dumps(generated, allow_nan=False).encode("utf-8"))
            if generated is None:
                raise WarmFailure("invalid_exchange", "parse_result")
            row.update({key: value for key, value in generated.items() if key not in ("version", "text")})
            row["wall_ms"] = min(2 ** 31, round((time.monotonic() - began) * 1000))
            if generated["status"] != "completed":
                raise WarmFailure("worker_failed", "wait_result")
            if not generated["thinking_disabled"] or not generated["template_applied"]:
                raise WarmFailure("invalid_exchange", "parse_result")
            if role == "director":
                proposal = generated["text"]
                stage = "validate_director"
                accepted = spike.oracle(observed, oracle_binary, "validate", case, proposal.encode("utf-8"))
                session.check_budget()
                if not accepted or accepted.get("status") != "accepted" or not isinstance(accepted.get("narrator"), dict):
                    raise WarmFailure("engine_rejected", stage)
                request = accepted["narrator"]
            else:
                narration = generated["text"]
        report["status"] = "completed"
    except WarmFailure as error:
        report.update(status=error.category, failure_stage=error.stage)
    except Exception:
        failed_stage = getattr(session, "stage", stage)
        report.update(status="setup_failed", failure_stage=failed_stage if type(failed_stage) is str and failed_stage in STAGES else "unknown")
    finally:
        try:
            report["session"] = safe_session(session.finish())
        except Exception:
            report["session"] = safe_session({})
    if report["status"] != "completed":
        return report
    final = report["session"]
    if final.get("cancel_requested") is True:
        report.update(status="cancelled", failure_stage="cancel")
        return report
    if (final.get("status") != "completed" or not all(final.get(key) is True for key in
            ("cleanup_complete", "adb_cleanup_complete", "directory_cleanup_complete")) or not warm_owners(final.get("sdk"))):
        report["status"] = "cleanup_failed"
        return report
    try:
        session.check_budget()
        accepted = spike.oracle(observed, oracle_binary, "commit", case,
                               json.dumps({"proposal": proposal, "narration": narration}).encode("utf-8"))
        expected = {"revision": 1, "events": 1, "recipient_observations": 1,
                    "absent_observations": 0, "exact_retry_unchanged": True}
        if (not accepted or accepted.get("status") != "committed"
                or any(type(accepted.get(key)) is not type(value) or accepted[key] != value for key, value in expected.items())):
            raise WarmFailure("engine_rejected", "commit")
        report.update(expected, status="committed")
    except WarmFailure as error:
        report.update(status=error.category, failure_stage=error.stage)
    except Exception:
        report.update(status="oracle_failed", failure_stage="commit")
    return report


def run_warm(session, native, oracle_binary, case="gift"):
    began = time.monotonic()
    report = _run_warm(session, native, oracle_binary, case)
    # Includes fixture/validation/commit plus model/control/cleanup; provisioning
    # precedes this timer. No UI display, persistence or prefill timing is implied.
    report["turn_wall_ms"] = min(2 ** 31, round((time.monotonic() - began) * 1000))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("adb", "owner", "oracle", "apk", "model", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--cancel-after", type=float)
    args = parser.parse_args()
    if args.cancel_after is not None and (not math.isfinite(args.cancel_after) or not 0 < args.cancel_after <= 60):
        parser.error("Cancellation offset must be finite and between zero and60seconds")
    stage = "model_identity"
    try:
        if spike.host.verify_model("litert", args.model):
            raise WarmFailure("setup_failed", "preflight")
        device = spike.Device(args.adb, args.serial)
        stage = "initialize_device"
        device.initialize()
        stage = "cache_artifacts"
        owner, oracle = [device.cached(path) for path in (args.owner, args.oracle)]
        identity = spike.sha256(args.apk)
        spike.SdkWorker(device, identity).verify_package()
        stage = "provision_model"
        device.provision_private_model(args.model)
        report = run_warm(WarmSdkSession(device, identity, cancel_after=args.cancel_after), spike.NativeWorker(device, owner), oracle)
        report["artifact"] = spike.host.ARTIFACTS["litert"][0]
        report["model_sha256"] = spike.host.ARTIFACTS["litert"][2]
    except Exception:
        report = {"version": 1, "status": "setup_failed", "failure_stage": stage, "attempted_roles": 0, "roles": []}
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] in ("committed", "preflight_rejected") else 2


if __name__ == "__main__":
    raise SystemExit(main())
