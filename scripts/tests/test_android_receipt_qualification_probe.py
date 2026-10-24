"""Pure mocked protocol tests. No Android client, build, model or cache access."""
import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import shlex
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("receipt_probe", Path(__file__).resolve().parents[1] / "android_receipt_qualification_probe.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def identities():
    names = [probe.APP, probe.TEST] + ["org.locallore.fixture%d.test" % number for number in range(33)]
    packages = {name: "a" * 64 for name in names}
    uids = {name: 10200 + number for number, name in enumerate(names)}
    passive = {name + ":chooser_test_provider": uids[name] for name in names[2:11]}
    return packages, uids, passive


def proposal(directory, readiness=True):
    packages, uids, passive = identities()
    apks = {probe.APP: str(directory / "app-debug.apk"), probe.TEST: str(directory / "app-debug-androidTest.apk")}
    for path in apks.values():
        Path(path).write_bytes(b"synthetic APK placeholder; never installed")
    return {"version": 1, "scope": "android_receipt_readiness" if readiness else "android_receipt_qualification",
        "source_commit": "a" * 40, "source_final": True, "artifacts_final": not readiness,
        "allow_device_calls": False, "root_go_pending": True, "selected_alias": "B", "serial": "emulator-5584",
        "adb_path": str(directory / "adb.exe"), "evidence_root": str(directory), "prior_packages": packages,
        "prior_uid_map": uids, "known_passive_provider_uids": passive,
        "apk_paths": {} if readiness else apks,
        "apk_sha256": {} if readiness else {key: probe.sha(Path(path).read_bytes()) for key, path in apks.items()},
        "bindings": {str((probe.ROOT / name).resolve()): probe.sha((probe.ROOT / name).read_bytes()) for name in probe.SOURCE_FILES[:3]}}


def proof(phase):
    value = {"version": 1, "phase": phase, "pid": 500, "start": 1000, "uid": 10200, "process": probe.APP,
        "fixture_bytes": 63, "fixture_sha256": probe.FIXTURE_SHA256, "candidate_root_absent": True,
        "publication_native_invoked": False, "sdk_invoked": False,
        "external_free_before": probe.EXTERNAL_FLOOR + 1000000, "external_free_after": probe.EXTERNAL_FLOOR + 1000000,
        "userdata_free_before": probe.USERDATA_FLOOR + 1000000, "userdata_free_after": probe.USERDATA_FLOOR + 1000000,
        "checks": {key: True for key in probe.PHASES[phase][2]}}
    if phase == "PROCESS":
        value.update(child_pid=501, child_start=1100, child_uid=10200)
    return value


def transcript(methods=None):
    methods = list(methods or sorted(probe.METHODS))
    rows = []
    for index, method in enumerate(methods, 1):
        for code in (1, 0):
            rows += ["INSTRUMENTATION_STATUS: class=" + probe.CLASS,
                "INSTRUMENTATION_STATUS: current=" + str(index), "INSTRUMENTATION_STATUS: id=AndroidJUnitRunner",
                "INSTRUMENTATION_STATUS: numtests=4", "INSTRUMENTATION_STATUS: stream=" + ("." if code == 0 else ""),
                "INSTRUMENTATION_STATUS: test=" + method, "INSTRUMENTATION_STATUS_CODE: " + str(code)]
    rows += ["INSTRUMENTATION_RESULT: stream=", "", "Time: 0.03", "", "OK (4 tests)", "", "INSTRUMENTATION_CODE: -1", ""]
    return "\n".join(rows).encode("ascii")


def failure_transcript():
    method = probe.PHASES["PROCESS"][1].encode()
    raw = transcript()
    raw = raw.replace(b"INSTRUMENTATION_STATUS: test=" + method + b"\nINSTRUMENTATION_STATUS_CODE: 0",
        b"INSTRUMENTATION_STATUS: stack=java.lang.IllegalStateException: synthetic START\nINSTRUMENTATION_STATUS: test=" + method + b"\nINSTRUMENTATION_STATUS_CODE: -2")
    return raw.replace(b"OK (4 tests)", b"FAILURES!!!\nTests run: 4,  Failures: 1")


def recovery_proposal(directory):
    value = proposal(directory)
    value["scope"] = "android_receipt_recovery"
    path = directory / "command-0025.stdout.bin"
    path.write_bytes(failure_transcript())
    value.update(failure_path=str(path), failure_sha256=probe.sha(path.read_bytes()))
    value["bindings"][str(path.resolve())] = value["failure_sha256"]
    return value


class FakeTransport:
    def __init__(self, value):
        self.value, self.calls, self.installs = value, [], 0
        self.owned, self.extra_manifest, self.bad_ready = False, False, False
        self.package_drift, self.uid_drift = False, False

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if command[1:] == ["devices", "-l"]:
            raw = b"List of devices attached\nemulator-5584 device product:synthetic\n\n"
        elif command[3] == "install":
            self.installs += 1
            raw = b"Performing Push Install\r\nSuccess\r\n"
        else:
            assert command[1:3] == ["-s", "emulator-5584"] and command[3] == "shell"
            op = tuple(shlex.split(command[4]))
            if op in probe.IDENTITY:
                raw = ("1\n", "35\n", "x86_64\n", "4096\n")[probe.IDENTITY.index(op)].encode()
            elif op == probe.PACKAGES:
                packages = self.value["prior_packages"].copy()
                if self.installs == 2:
                    packages.update(self.value["apk_sha256"])
                    if self.package_drift:
                        packages[next(name for name in packages if name not in (probe.APP, probe.TEST))] = "b" * 64
                raw = "".join(name + "|" + digest + "  /data/app/fixed-%d/base.apk\n" % index
                              for index, (name, digest) in enumerate(packages.items())).encode()
            elif op == probe.UIDS:
                uids = self.value["prior_uid_map"].copy()
                if self.uid_drift and self.installs == 2:
                    uids[probe.APP] = 19999
                raw = "".join("package:%s uid:%d\n" % row for row in uids.items()).encode()
            elif op == probe.PS:
                raw = b"PID UID NAME\n1 1000 system_server\n"
                if self.owned:
                    raw += ("500 10200 " + probe.SERVICE + "\n").encode()
            elif op == probe.VOLUMES:
                raw = b"public:253,80 mounted 0000-0000\n"
            elif op == probe.DF:
                raw = b"Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/dm-46 10000000 1000000 9000000 10% /data/user/0\n"
            elif op == probe.DEVICES:
                raw = b"123\n123\n"
            elif op in (probe.PROOF_ABSENT, probe.INTERNAL_CANDIDATE_ABSENT):
                raw = b""
            elif op == probe.INSTRUMENT:
                raw = transcript()
            elif op == probe.PROOF_MANIFEST:
                names = sorted(probe.PROOF_FILES) + (["unknown"] if self.extra_manifest else [])
                raw = "".join(probe.PROOF_ROOT + "/" + name + "\n" for name in names).encode()
            elif op == probe.RECOVERY_MANIFEST:
                names = sorted(probe.RECOVERY_FILES) + (["process-v1.json"] if self.extra_manifest else [])
                raw = "".join(probe.RECOVERY_ROOT + "/" + name + "\n" for name in names).encode()
            else:
                found = False
                for root in (probe.PROOF_ROOT, probe.RECOVERY_ROOT):
                    for phase, (stem, _, _) in probe.PHASES.items():
                        if root == probe.RECOVERY_ROOT and phase not in probe.RECOVERY_PHASES:
                            continue
                        if op == probe.proof_command(stem + "-ready-v1.txt", 10200, root):
                            raw, found = (b"stale-marker" if self.bad_ready else b""), True
                        elif op == probe.proof_command(stem + "-v1.json", 10200, root):
                            raw, found = json.dumps(proof(phase)).encode(), True
                assert found
        return SimpleNamespace(stdout=raw, status="completed", returncode=0, cleanup_complete=True, stderr_bytes=0)


class ProofTests(unittest.TestCase):
    def test_all_four_closed_proofs_and_parent_identity(self):
        values = {phase: probe.parse_proof(json.dumps(proof(phase)).encode(), phase, 10200) for phase in probe.PHASES}
        self.assertTrue(probe.match_parent_identities(values))

    def test_extra_missing_duplicate_and_nonfinite_refused(self):
        value = proof("ACCEPT")
        malformed = [dict(value, extra=True), {key: item for key, item in value.items() if key != "phase"}, dict(value, start=float("nan"))]
        for item in malformed:
            with self.assertRaises((AssertionError, ValueError)):
                probe.parse_proof(json.dumps(item).encode(), "ACCEPT", 10200)
        with self.assertRaises(AssertionError):
            probe.parse_proof(json.dumps(value).replace('"version": 1', '"version": 1, "version": 1').encode(), "ACCEPT", 10200)

    def test_coercions_checks_wrong_phase_identity_and_native_calls_refused(self):
        for key, wrong in (("version", True), ("start", 1.0), ("uid", 10201), ("phase", "REFUSAL"),
                           ("fixture_bytes", 64), ("process", probe.SERVICE), ("sdk_invoked", True),
                           ("publication_native_invoked", True), ("candidate_root_absent", False),
                           ("external_free_before", probe.EXTERNAL_FLOOR)):
            value = proof("ACCEPT")
            value[key] = wrong
            with self.assertRaises(AssertionError):
                probe.parse_proof(json.dumps(value).encode(), "ACCEPT", 10200)
        for checks in ({}, dict(proof("ACCEPT")["checks"], extra=True), {key: 1 for key in probe.PHASES["ACCEPT"][2]}):
            value = dict(proof("ACCEPT"), checks=checks)
            with self.assertRaises(AssertionError):
                probe.parse_proof(json.dumps(value).encode(), "ACCEPT", 10200)

    def test_child_and_parent_consistency_refused(self):
        for change in ({"child_pid": 500}, {"child_uid": 10201}, {"child_start": 0}):
            with self.assertRaises(AssertionError):
                probe.parse_proof(json.dumps(dict(proof("PROCESS"), **change)).encode(), "PROCESS", 10200)
        values = {phase: proof(phase) for phase in probe.PHASES}
        values["PROCESS"]["start"] = 999
        with self.assertRaises(AssertionError):
            probe.match_parent_identities(values)

    def test_after_capacity_uses_actual_retained_floor(self):
        value = proof("ACCEPT")
        value["external_free_after"] = probe.EXTERNAL_FLOOR
        self.assertEqual(probe.parse_proof(json.dumps(value).encode(), "ACCEPT", 10200)["external_free_after"], probe.EXTERNAL_FLOOR)
        value["external_free_after"] -= 1
        with self.assertRaises(AssertionError):
            probe.parse_proof(json.dumps(value).encode(), "ACCEPT", 10200)


class InstrumentationTests(unittest.TestCase):
    def test_exact_four_passes_any_method_order_and_crlf(self):
        for methods in (sorted(probe.METHODS), list(reversed(sorted(probe.METHODS)))):
            raw = transcript(methods)
            self.assertEqual(probe.parse_instrumentation(raw)["passed"], 4)
            self.assertEqual(probe.parse_instrumentation(raw.replace(b"\n", b"\r\n"))["methods"], methods)

    def test_failure_skip_missing_duplicate_and_summary_refused(self):
        raw = transcript()
        names = sorted(probe.METHODS)
        for malformed in (raw.replace(b"STATUS_CODE: 0", b"STATUS_CODE: -2", 1), raw.replace(b"STATUS_CODE: 0", b"STATUS_CODE: -3", 1),
                          raw.replace(b"STATUS_CODE: 0", b"NO_TERMINAL", 1), raw.replace(names[0].encode(), names[1].encode()),
                          raw.replace(b"OK (4 tests)", b"OK (5 tests)"), raw.replace(b"INSTRUMENTATION_CODE: -1", b"")):
            with self.assertRaises((AssertionError, ValueError)):
                probe.parse_instrumentation(malformed)

    def test_early_terminal_after_terminal_abort_and_control_framing_refused(self):
        raw = transcript()
        for malformed in (b"INSTRUMENTATION_CODE: -1\n" + raw, raw + b"INSTRUMENTATION_STATUS: test=late\n",
                          raw + b"INSTRUMENTATION_ABORTED: stopped\n", raw.replace(b"\n", b"\v"),
                          raw.replace(b"\n", b"\r\n", 1), raw.replace(b"Time: 0.03", b"Time: 121")):
            with self.assertRaises((AssertionError, ValueError)):
                probe.parse_instrumentation(malformed)


class OwnershipTests(unittest.TestCase):
    def test_recovery_reads_only_three_old_proofs_and_reports_owned_presence(self):
        with tempfile.TemporaryDirectory() as directory:
            value = recovery_proposal(Path(directory))
            self.assertTrue(probe.validate_proposal(value))
            owner, transport = probe.Owner(value), FakeTransport(value)
            transport.owned = True
            with patch.object(probe.host, "run_process", side_effect=transport), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                result = probe.run_recovery(owner)
            self.assertEqual(set(result["proofs"]), set(probe.RECOVERY_PHASES))
            self.assertFalse(result["qualification_passed"])
            self.assertFalse(result["owned_quiet_final"])
            self.assertEqual(owner.methods, 0)
            self.assertEqual(sum(owner.installs.values()), 0)
            self.assertFalse(any(command[3] == "install" or "am instrument" in " ".join(command) for command, _ in transport.calls))

    def test_recovery_extra_process_proof_and_changed_failure_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            value = recovery_proposal(Path(directory))
            owner, transport = probe.Owner(value), FakeTransport(value)
            transport.extra_manifest = True
            with patch.object(probe.host, "run_process", side_effect=transport), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                with self.assertRaises(AssertionError):
                    probe.run_recovery(owner)
            self.assertEqual(owner.stage, "proofs")
            Path(value["failure_path"]).write_bytes(transcript())
            with self.assertRaises(AssertionError):
                probe.validate_proposal(value)
        with self.assertRaises(AssertionError):
            probe.parse_recovery_failure(transcript())
        with self.assertRaises(AssertionError):
            probe.parse_recovery_failure(b"INSTRUMENTATION_CODE: -1\n" + failure_transcript())

    def test_readiness_only_has_read_commands_and_preserves_all_35(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory))
            self.assertTrue(probe.validate_proposal(value))
            owner, transport = probe.Owner(value), FakeTransport(value)
            with patch.object(probe.host, "run_process", side_effect=transport), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                result = probe.run_readiness(owner)
            self.assertTrue(result["read_only"])
            self.assertEqual(owner.installs, {probe.APP: 0, probe.TEST: 0})
            self.assertEqual(owner.methods, 0)
            self.assertTrue(all(command[1:] == ["devices", "-l"] or command[3] == "shell" for command, _ in transport.calls))

    def test_qualification_complete_exact_manifest_and_proofs(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory), readiness=False)
            owner, transport = probe.Owner(value), FakeTransport(value)
            with patch.object(probe.host, "run_process", side_effect=transport), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                result = probe.run_cohort(owner)
            self.assertEqual(result["tests"]["passed"], 4)
            self.assertEqual(owner.installs, {probe.APP: 1, probe.TEST: 1})
            self.assertEqual(owner.methods, 1)

    def test_unknown_manifest_or_nonempty_ready_stops_without_followon(self):
        for change in ("extra_manifest", "bad_ready"):
            with tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory), readiness=False)
                owner, transport = probe.Owner(value), FakeTransport(value)
                setattr(transport, change, True)
                with patch.object(probe.host, "run_process", side_effect=transport), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                    with self.assertRaises(AssertionError):
                        probe.run_cohort(owner)
                self.assertEqual(owner.stage, "proofs")
                self.assertFalse((owner.directory / "final-facts.json").exists())

    def test_preinstall_capacity_exact_boundary_and_one_byte_short(self):
        for short in (0, 1):
            with tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory), readiness=False)
                total = sum(Path(path).stat().st_size for path in value["apk_paths"].values())
                owner, transport = probe.Owner(value), FakeTransport(value)
                facts = owner.facts
                def capacity(label, expected):
                    observed = facts(label, expected)
                    if label == "before":
                        observed["userdata"]["available_bytes"] = probe.USERDATA_FLOOR + total - short
                    return observed
                with patch.object(owner, "facts", side_effect=capacity), patch.object(probe.host, "run_process", side_effect=transport), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                    if short:
                        with self.assertRaises(AssertionError):
                            probe.run_cohort(owner)
                        self.assertEqual(owner.installs, {probe.APP: 0, probe.TEST: 0})
                        self.assertEqual(owner.methods, 0)
                        self.assertFalse(any(command[3] == "install" or "am instrument" in " ".join(command) for command, _ in transport.calls))
                    else:
                        result = probe.run_cohort(owner)
                        self.assertEqual(result["tests"]["passed"], 4)
                        self.assertEqual(owner.installs, {probe.APP: 1, probe.TEST: 1})

    def test_preinstall_validates_both_files_before_first_update(self):
        for invalid in (b"", b"changed"):
            with tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory), readiness=False)
                Path(value["apk_paths"][probe.TEST]).write_bytes(invalid)
                owner, transport = probe.Owner(value), FakeTransport(value)
                with patch.object(probe.host, "run_process", side_effect=transport), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                    with self.assertRaises(AssertionError):
                        probe.run_cohort(owner)
                self.assertEqual(owner.installs, {probe.APP: 0, probe.TEST: 0})
                self.assertEqual(owner.methods, 0)

    def test_post_update_package_or_uid_drift_stops_before_instrumentation(self):
        for change in ("package_drift", "uid_drift"):
            with tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory), readiness=False)
                owner, transport = probe.Owner(value), FakeTransport(value)
                setattr(transport, change, True)
                with patch.object(probe.host, "run_process", side_effect=transport), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                    with self.assertRaises(AssertionError):
                        probe.run_cohort(owner)
                self.assertEqual(owner.stage, "installed")
                self.assertEqual(owner.methods, 0)
                self.assertFalse(any("am instrument" in " ".join(command) for command, _ in transport.calls))

    def test_unknown_process_uid_and_live_owned_service_refused(self):
        packages, uids, passive = identities()
        for row in ("500 10201 " + probe.SERVICE, "500 10200 org.locallore.unknown", "500 10200 " + next(iter(passive))):
            with self.assertRaises(AssertionError):
                probe.parse_processes(("PID UID NAME\n" + row + "\n").encode(), uids, passive)
        parsed = probe.parse_processes(("PID UID NAME\n500 10200 " + probe.SERVICE + "\n").encode(), uids, passive)
        self.assertEqual(len(parsed["owned"]), 1)

    def test_expired_deadline_never_dispatches(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = probe.Owner(proposal(Path(directory)))
            owner.until = 0
            with patch.object(probe.host, "run_process") as dispatch:
                with self.assertRaises(AssertionError):
                    owner.shell(probe.PS)
                dispatch.assert_not_called()

    def test_unclean_raw_retained_and_no_later_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = probe.Owner(proposal(Path(directory)))
            result = SimpleNamespace(stdout=b"bounded raw", status="cleanup_failed", returncode=None, cleanup_complete=False, stderr_bytes=3)
            with patch.object(probe.host, "run_process", return_value=result) as dispatch:
                with self.assertRaises(AssertionError):
                    owner.shell(probe.PS)
                self.assertEqual((owner.commands / "command-0001.stdout.bin").read_bytes(), b"bounded raw")
                with self.assertRaises(AssertionError):
                    owner.shell(probe.PS)
                self.assertEqual(dispatch.call_count, 1)

    def test_retention_failure_poisoned_and_readiness_cannot_install_or_instrument(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = probe.Owner(proposal(Path(directory)))
            with patch.object(probe.host, "run_process") as dispatch:
                owner.stage, owner.pending_install = "updating", probe.APP
                with self.assertRaises(AssertionError):
                    owner.dispatch(["install", "--no-streaming", "-r", "anything"])
                owner.stage = "instrumentation"
                with self.assertRaises(AssertionError):
                    owner.shell(probe.INSTRUMENT)
                dispatch.assert_not_called()
            owner.stage = "before"
            result = SimpleNamespace(stdout=b"raw", status="completed", returncode=0, cleanup_complete=True, stderr_bytes=0)
            with patch.object(probe.host, "run_process", return_value=result) as dispatch, patch.object(probe, "write_json", side_effect=OSError("synthetic retention failure")):
                with self.assertRaises(OSError):
                    owner.shell(probe.PS)
                with self.assertRaises(AssertionError):
                    owner.shell(probe.PS)
                self.assertEqual(dispatch.call_count, 1)

    def test_changed_authorization_or_source_refused_before_owned_start(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = proposal(root)
            raw = json.dumps(value).encode()
            (root / "proposal.json").write_bytes(raw)
            authorization = {"version": 1, "proposal_sha256": "0" * 64, "allow_device_calls": True, "root_go_pending": False}
            (root / "auth.json").write_text(json.dumps(authorization))
            with patch.object(probe.host, "run_process") as dispatch:
                with self.assertRaises(AssertionError):
                    probe.run_owned(root / "proposal.json", root / "auth.json", root)
                dispatch.assert_not_called()
            authorization["proposal_sha256"] = probe.sha(raw)
            (root / "auth.json").write_text(json.dumps(authorization))
            value["bindings"][str(Path(probe.__file__).resolve())] = "0" * 64
            (root / "proposal.json").write_text(json.dumps(value))
            authorization["proposal_sha256"] = probe.sha((root / "proposal.json").read_bytes())
            (root / "auth.json").write_text(json.dumps(authorization))
            with self.assertRaises(AssertionError):
                probe.authorize(root / "proposal.json", root / "auth.json", root)
            self.assertFalse((root / "receipt-owned-start-v1.json").exists())

    def test_actual_cli_owned_worker_success_refusal_and_unknown_cleanup(self):
        cases = ((True, "completed", 0, True, 0), (False, "completed", 2, True, 2),
                 (False, "cleanup_failed", None, False, 2))
        for readiness, status, code, cleaned, expected in cases:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                value = proposal(root, readiness=readiness)
                proposal_path, authorization_path = root / "proposal.json", root / "auth.json"
                proposal_path.write_text(json.dumps(value))
                authorization_path.write_text("{}")
                result = SimpleNamespace(stdout=b"worker raw first", status=status, returncode=code,
                                         cleanup_complete=cleaned, elapsed_ms=7, stderr_bytes=9)
                output = io.StringIO()
                with patch.object(probe, "authorize", return_value=value), patch.object(probe.host, "run_process", return_value=result) as dispatch, redirect_stdout(output):
                    actual = probe.main(["run", "--proposal", str(proposal_path), "--authorization", str(authorization_path), "--evidence", str(root)])
                self.assertEqual(actual, expected)
                args, options = dispatch.call_args
                self.assertEqual(args[0][:5], [probe.sys.executable, "-B", "-E", str(Path(probe.__file__).resolve()), "worker"])
                self.assertEqual(options["request"], probe.REQUEST)
                self.assertEqual(options["deadline"], 90 if readiness else 180)
                self.assertEqual(options["max_output"], 32768)
                self.assertEqual((root / "receipt-owned-stdout-v1.bin").read_bytes(), result.stdout)
                retained = json.loads((root / "receipt-owned-result-v1.json").read_bytes())
                self.assertEqual(json.loads(output.getvalue()), retained)
                self.assertEqual((retained["status"], retained["returncode"], retained["cleanup_complete"]), (status, code, cleaned))


if __name__ == "__main__":
    unittest.main(verbosity=2)
