"""Pure controller tests. Every transport is mocked; no Android client is executed.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import redirect_stdout
import copy
import importlib.util
import io
import json
from pathlib import Path
import shlex
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("receipt_setup_controller",
    Path(__file__).resolve().parents[2] / "benchmarks/receipt_setup_qualification.py")
q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q)
c = q.contract


def proposal(root):
    apks = {q.APP: root / "app-debug.apk", q.TEST: root / "app-debug-androidTest.apk"}
    for index, path in enumerate(apks.values(), 1):
        path.write_bytes((b"Synthetic APK fixture, never installed." + bytes([index]) * 2048)[:index * 1024])
    environment, running, adb = root / "environment.json", root / "running-v1.json", root / "adb.exe"
    for path in (environment, running, adb):
        path.write_bytes(b"Synthetic input, never executed.")
    files = [q.ROOT / name for name in q.SOURCE_FILES] + [environment, running, adb, *apks.values()]
    return {"version": 1, "scope": "receipt_setup_qualification", "source_commit": "b" * 40,
        "source_final": True, "artifacts_final": True, "allow_device_calls": False, "root_go_pending": True,
        "selected_alias": "S", "environment_proposal_path": str(environment), "running_path": str(running),
        "running_sha256": q.sha(running.read_bytes()), "adb_path": str(adb),
        "apk_paths": {key: str(path) for key, path in apks.items()},
        "apk_sha256": {key: q.sha(path.read_bytes()) for key, path in apks.items()},
        "bindings": {str(path.resolve()): q.sha(path.read_bytes()) for path in files}, "evidence_root": str(root)}


def proof(phase):
    count = {"SETUP": 1, "CANCELLATION": 2, "DRAIN": 1, "REOPEN": 0}[phase]
    value = {"version": 1, "phase": phase, "pid": 601, "start": 1000, "uid": 10310, "process": q.APP,
        "fixture_bytes": 63, "fixture_sha256": c.FIXTURE_SHA256, "direct_callback": True,
        "candidate_roots_absent": True, "publication_native_invoked": False, "sdk_invoked": False,
        "external_free_before": c.EXTERNAL_FLOOR + 63, "external_free_after": c.EXTERNAL_FLOOR,
        "userdata_free_before": c.PROOF_USERDATA_FLOOR, "userdata_free_after": c.PROOF_USERDATA_FLOOR,
        "source_opened": count, "source_closed": count, "checks": {name: True for name in q.PHASES[phase][2]}}
    if phase == "REOPEN":
        value.update(pid=602, start=2000, prior_pid=601, prior_start=1000)
    return value


def transcript(restart=False):
    cls = q.RESTART_CLASS if restart else q.INITIAL_CLASS
    methods = sorted(q.RESTART_METHODS if restart else q.INITIAL_METHODS)
    rows = []
    for number, method in enumerate(methods, 1):
        for code in (1, 0):
            rows += ["INSTRUMENTATION_STATUS: class=" + cls,
                "INSTRUMENTATION_STATUS: current=" + str(number), "INSTRUMENTATION_STATUS: id=AndroidJUnitRunner",
                "INSTRUMENTATION_STATUS: numtests=" + str(len(methods)),
                "INSTRUMENTATION_STATUS: stream=" + ("." if code == 0 else ""),
                "INSTRUMENTATION_STATUS: test=" + method, "INSTRUMENTATION_STATUS_CODE: " + str(code)]
    summary = "OK (%d %s)" % (len(methods), "test" if restart else "tests")
    return ("\n".join(rows) + "\nINSTRUMENTATION_RESULT: stream=\n\nTime: 0.03\n\n" +
            summary + "\n\nINSTRUMENTATION_CODE: -1\n").encode()


class Lease:
    def __init__(self, value):
        self.descriptor = {"serial": "emulator-5592", "avd_name": "ReceiptSetupSynthetic",
                           "adb_path": value["adb_path"]}
        self.live, self.checks = True, 0

    def check(self):
        self.checks += 1
        if not self.live:
            raise RuntimeError("Synthetic owner lost")


class Transport:
    def __init__(self, value, lease):
        self.value, self.lease, self.calls = value, lease, []
        self.installs, self.instruments, self.last_check = 0, 0, 0
        self.foreign_package = self.foreign_process = self.active_after_initial = False
        self.uid_drift = self.bad_initial = self.bad_restart = self.bad_manifest = False
        self.lose_owner = self.uncertain = False
        self.proof_changes = {}
        self.available = 9_000_000 * 1024
        self.boot_outputs = []

    def __call__(self, command, **kwargs):
        assert command[:3] == [self.value["adb_path"], "-s", self.lease.descriptor["serial"]]
        assert self.lease.checks > self.last_check
        self.last_check = self.lease.checks
        self.calls.append((command, kwargs))
        override = None
        if command[3:] == list(q.AVD_NAME):
            raw = self.lease.descriptor["avd_name"].encode() + b"\r\r\nOK\r\r\n"
        elif command[3] == "install":
            assert command[3:5] == ["install", "--no-streaming"] and len(command) == 6
            self.installs += 1
            raw = b"Performing Push Install\r\nSuccess\r\n"
        else:
            assert len(command) == 5 and command[3] == "shell"
            op = tuple(shlex.split(command[4]))
            if op in c.IDENTITY:
                raw = (b"1\n", b"35\n", b"x86_64\n", b"4096\n")[c.IDENTITY.index(op)]
                if op == c.IDENTITY[0] and self.boot_outputs:
                    override = self.boot_outputs.pop(0)
                    raw = override[1]
            elif op == c.PACKAGES:
                packages = dict(self.value["apk_sha256"]) if self.installs == 2 else {}
                if self.foreign_package:
                    packages["org.locallore.other"] = "a" * 64
                raw = "".join("%s|%s  /data/app/synthetic%d/base.apk\n" % (name, digest, index)
                    for index, (name, digest) in enumerate(packages.items())).encode()
            elif op == c.UIDS:
                uids = {q.APP: 10310, q.TEST: 10311} if self.installs == 2 else {}
                if self.uid_drift and self.instruments:
                    uids[q.APP] = 10312
                raw = "".join("package:%s uid:%d\n" % row for row in uids.items()).encode()
            elif op == c.PS:
                raw = b"PID UID NAME\n1 1000 system_server\n"
                if self.foreign_process:
                    raw += b"604 10310 org.locallore.foreign\n"
                if self.active_after_initial and self.instruments == 1:
                    raw += ("601 10310 " + q.APP + "\n").encode()
            elif op == c.VOLUMES:
                raw = b"public:253,80 mounted 0000-0000\n"
            elif op == c.DF:
                raw = ("Filesystem 1K-blocks Used Available Use%% Mounted on\n/dev/block/dm-46 "
                       "10000000 1000000 %d 10%% /data/user/0\n" % (self.available // 1024)).encode()
            elif op == c.DEVICES:
                raw = b"123\n123\n"
            elif op in (q.PROOF_ABSENT, c.INTERNAL_CANDIDATE_ABSENT):
                raw = b""
            elif op in (q.INITIAL_INSTRUMENT, q.RESTART_INSTRUMENT):
                restart = op == q.RESTART_INSTRUMENT
                self.instruments += 1
                raw = transcript(restart)
                if self.bad_restart if restart else self.bad_initial:
                    raw = raw.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2", 1)
            elif op == q.PROOF_MANIFEST:
                phases = set(q.PHASES) if self.instruments == 2 else set(q.PHASES) - {"REOPEN"}
                names = [q.PROOF_ROOT + "/" + q.PHASES[phase][0] + suffix for phase in phases
                         for suffix in ("-v1.json", "-ready-v1.txt")]
                if self.bad_manifest:
                    names += [q.PROOF_ROOT + "/unexpected"]
                raw = "".join(name + "\n" for name in sorted(names)).encode()
            else:
                found = False
                for phase, (stem, _, _) in q.PHASES.items():
                    for suffix in ("-ready-v1.txt", "-v1.json"):
                        if op == q.proof_command(stem + suffix, 10310):
                            value = proof(phase)
                            value.update(self.proof_changes.get(phase, {}))
                            raw = b"" if suffix.endswith(".txt") else json.dumps(value).encode()
                            found = True
                assert found, op
        if self.lose_owner:
            self.lease.live = False
        return SimpleNamespace(status="completed", returncode=override[0] if override else 0,
            cleanup_complete=not self.uncertain, stdout=raw, stderr_bytes=override[2] if override else 0, elapsed_ms=1)


class ReceiptSetupControllerTests(unittest.TestCase):
    def execute(self, value, lease, transport):
        owner = q.Owner(value, lease)
        with patch.object(q.host, "run_process", side_effect=transport), patch.object(q.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
            result = q.run_cohort(owner)
        return owner, result

    def test_complete_initial_and_separate_restart_with_all_44_checks(self):
        original_hashes = dict(q.APK_HASHES)
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
            owner, result = self.execute(value, lease, transport)
            self.assertEqual(result["initial_tests"]["passed"], 3)
            self.assertEqual(result["restart_test"]["passed"], 1)
            self.assertEqual(sum(len(p["checks"]) for p in result["proofs"].values()), 44)
            self.assertEqual(result["before"]["packages"], {})
            self.assertEqual(result["final"]["uid_map"], {q.APP: 10310, q.TEST: 10311})
            self.assertEqual(owner.methods, 2)
            self.assertEqual(owner.installs, {q.APP: 1, q.TEST: 1})
            self.assertGreaterEqual(lease.checks, 2 * owner.count)
            self.assertTrue(result["direct_callback_only"])
            self.assertFalse(result["DocumentsUI_qualified"])
            self.assertFalse(result["real_model_or_SDK_qualified"])
            for _, kwargs in transport.calls:
                self.assertTrue(0 < kwargs["deadline"] <= 120)
        self.assertEqual(q.APK_HASHES, original_hashes)

    def test_proof_closed_types_bounds_and_exact_check_maps(self):
        for phase in q.PHASES:
            valid = proof(phase)
            self.assertEqual(q.parse_proof(json.dumps(valid).encode(), phase, 10310), valid)
            for key, bad in (("version", True), ("pid", 0), ("start", True), ("uid", 10311),
                             ("fixture_bytes", 64), ("fixture_sha256", "0" * 64), ("direct_callback", 1),
                             ("candidate_roots_absent", False), ("sdk_invoked", True), ("source_closed", -1),
                             ("external_free_before", c.EXTERNAL_FLOOR + 62),
                             ("userdata_free_after", c.PROOF_USERDATA_FLOOR - 1)):
                changed = dict(valid, **{key: bad})
                with self.subTest(phase=phase, key=key), self.assertRaises(AssertionError):
                    q.parse_proof(json.dumps(changed).encode(), phase, 10310)
            for checks in ({}, dict(valid["checks"], unexpected=True), {key: 1 for key in valid["checks"]}):
                with self.assertRaises(AssertionError):
                    q.parse_proof(json.dumps(dict(valid, checks=checks)).encode(), phase, 10310)
        raw = json.dumps(proof("SETUP")).encode()
        for bad in (raw[:-1] + b',"version":1}', b" " * 4097, b"[]", raw.replace(b'"version": 1', b'"version": NaN')):
            with self.assertRaises((AssertionError, ValueError)):
                q.parse_proof(bad, "SETUP", 10310)

    def test_restart_requires_linked_new_identity_but_permits_pid_reuse(self):
        valid = {phase: proof(phase) for phase in q.PHASES}
        self.assertTrue(q.match_restart(valid))
        for changes in ({"pid": 601, "start": 1000}, {"prior_pid": 999}, {"prior_start": 999}, {"uid": 10311}):
            changed = copy.deepcopy(valid); changed["REOPEN"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(AssertionError):
                q.match_restart(changed)
        for pid, start in ((601, 2000), (602, 1000)):
            changed = copy.deepcopy(valid); changed["REOPEN"].update(pid=pid, start=start)
            self.assertTrue(q.match_restart(changed))
        valid["DRAIN"]["start"] = 999
        with self.assertRaises(AssertionError):
            q.match_restart(valid)

    def test_transcripts_require_exact_selected_pairs_summary_and_runner(self):
        for restart in (False, True):
            cls, methods = (q.RESTART_CLASS, q.RESTART_METHODS) if restart else (q.INITIAL_CLASS, q.INITIAL_METHODS)
            raw = transcript(restart)
            self.assertEqual(q.parse_instrumentation(raw, cls, methods)["passed"], len(methods))
            self.assertEqual(q.parse_instrumentation(raw.replace(b"\n", b"\r\n"), cls, methods)["failed"], 0)
            bads = [raw.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2", 1),
                raw.replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: -01"),
                raw.replace(b"INSTRUMENTATION_RESULT: stream=", b"INSTRUMENTATION_RESULT: shortMsg=Process crashed."),
                raw.replace(b"Time: 0.03", b"Time: 120.1"), raw.replace(b"Time: 0.03", b"Time: NaN"),
                raw.replace(b"\nOK (", b"\nError hidden in result\nOK ("), raw + b"unexpected prose\n",
                raw.replace(cls.encode(), b"org.locallore.app.ForeignTest", 1),
                raw.replace(b"INSTRUMENTATION_STATUS: id=AndroidJUnitRunner", b"INSTRUMENTATION_STATUS: id=ForeignRunner", 1)]
            for bad in bads:
                with self.subTest(restart=restart, bad=bad[-100:]), self.assertRaises((AssertionError, ValueError)):
                    q.parse_instrumentation(bad, cls, methods)

    def test_fixed_keyword_phase_budget_boundaries_and_synthetic_default(self):
        for restart in (False, True):
            cls, methods = (q.RESTART_CLASS, q.RESTART_METHODS) if restart else (q.INITIAL_CLASS, q.INITIAL_METHODS)
            raw = transcript(restart)
            for budget in (30_000, 120_000, 150_000, 170_000):
                seconds = str(budget // 1000).encode()
                exact = raw.replace(b"Time: 0.03", b"Time: " + seconds)
                self.assertEqual(q._parse_selected_instrumentation(exact, cls, methods, phase_budget_ms=budget)["passed"], len(methods))
                self.assertEqual(q._parse_selected_instrumentation(exact.replace(b"\n", b"\r\n"), cls, methods, phase_budget_ms=budget)["failed"], 0)
                beyond = raw.replace(b"Time: 0.03", b"Time: " + seconds + b".000000001")
                with self.assertRaises(AssertionError): q._parse_selected_instrumentation(beyond, cls, methods, phase_budget_ms=budget)
            self.assertEqual(q.parse_instrumentation(raw.replace(b"Time: 0.03", b"Time: 120"), cls, methods)["passed"], len(methods))
            with self.assertRaises(AssertionError): q.parse_instrumentation(raw.replace(b"Time: 0.03", b"Time: 120.000000001"), cls, methods)
            for budget in (True, False, None, 0, -1, "150000", 150000.0, 30001, 120001, 180000, 999999):
                with self.subTest(budget=budget), self.assertRaises(AssertionError):
                    q._parse_selected_instrumentation(raw, cls, methods, phase_budget_ms=budget)
            with self.assertRaises(TypeError): q._parse_selected_instrumentation(raw, cls, methods, 170000)

    def test_larger_fixed_phase_budget_does_not_relax_machine_framing(self):
        raw = transcript(True).replace(b"Time: 0.03", b"Time: 150")
        cls, methods = q.RESTART_CLASS, q.RESTART_METHODS
        bads = [raw.replace(b"STATUS_CODE: 0", b"STATUS_CODE: -2"), raw + raw,
            raw.replace(b"current=1", b"current=2"), raw.replace(b"numtests=1", b"numtests=2"),
            raw.replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: 0"),
            raw.replace(b"Time: 150", b"Time: NaN"), raw.replace(b"Time: 150", b"Time: 1.5e2"),
            raw.replace(b"Time: 150", b"Time: -1"), raw + b"unexpected prose\n"]
        for bad in bads:
            with self.assertRaises((AssertionError, ValueError)):
                q._parse_selected_instrumentation(bad, cls, methods, phase_budget_ms=170_000)

    def test_foreign_packages_processes_and_surviving_initial_owner_stop_restart(self):
        for flag in ("foreign_package", "foreign_process", "active_after_initial"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
                setattr(transport, flag, True)
                with self.assertRaises(AssertionError):
                    self.execute(value, lease, transport)
                self.assertEqual(transport.instruments, 1 if flag == "active_after_initial" else 0)
                self.assertNotIn(q.RESTART_INSTRUMENT, [tuple(shlex.split(cmd[4])) for cmd, _ in transport.calls if cmd[3] == "shell"])

    def test_stale_prior_bad_proofs_tests_or_manifests_cannot_produce_final_facts(self):
        for flag in ("uid_drift", "bad_initial", "bad_restart", "bad_manifest", "stale_prior", "reused_identity"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
                if flag == "stale_prior": transport.proof_changes["REOPEN"] = {"prior_start": 999}
                elif flag == "reused_identity": transport.proof_changes["REOPEN"] = {"pid": 601, "start": 1000}
                else: setattr(transport, flag, True)
                owner = q.Owner(value, lease)
                with patch.object(q.host, "run_process", side_effect=transport), patch.object(q.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                    with self.assertRaises(AssertionError): q.run_cohort(owner)
                self.assertFalse((owner.directory / "final-facts.json").exists())
                self.assertTrue((owner.commands / ("command-%04d.stdout.bin" % owner.count)).exists())

    def test_unknown_cleanup_or_owner_loss_retains_raw_then_stops(self):
        for flag in ("lose_owner", "uncertain"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
                setattr(transport, flag, True)
                owner = q.Owner(value, lease); owner.stage = "before"
                with patch.object(q.host, "run_process", side_effect=transport):
                    with self.assertRaises((AssertionError, RuntimeError)): owner.dispatch(list(q.AVD_NAME))
                    with self.assertRaises((AssertionError, RuntimeError)): owner.dispatch(list(q.AVD_NAME))
                self.assertEqual(len(transport.calls), 1)
                self.assertTrue((owner.commands / "command-0001.stdout.bin").exists())
                row = json.loads((owner.commands / "command-0001.json").read_bytes())
                self.assertEqual(row["stdout_sha256"], q.sha((owner.commands / "command-0001.stdout.bin").read_bytes()))

    def test_evidence_failure_and_aggregate_expiry_prevent_next_transport(self):
        for kind in ("evidence", "deadline"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
                owner = q.Owner(value, lease); owner.stage = "before"
                if kind == "deadline": owner.until = q.time.monotonic() - 1
                with patch.object(q.host, "run_process", side_effect=transport), patch.object(q, "write_json", side_effect=OSError("Synthetic output failure")):
                    with self.assertRaises((AssertionError, OSError)): owner.dispatch(list(q.AVD_NAME))
                    with self.assertRaises((AssertionError, OSError)): owner.dispatch(list(q.AVD_NAME))
                self.assertEqual(len(transport.calls), 1 if kind == "evidence" else 0)

    def test_staging_reserve_exact_boundary_and_shortfall_before_install(self):
        for delta in (0, -1024):
            with self.subTest(delta=delta), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
                transport.available = c.USERDATA_FLOOR + sum(Path(p).stat().st_size for p in value["apk_paths"].values()) + delta
                if delta == 0:
                    self.execute(value, lease, transport)
                    self.assertEqual(transport.installs, 2)
                else:
                    with self.assertRaises(AssertionError): self.execute(value, lease, transport)
                    self.assertEqual(transport.installs, 0)
                    self.assertEqual(transport.instruments, 0)

    def test_both_apks_validated_before_first_install(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
            Path(value["apk_paths"][q.TEST]).write_bytes(b"changed")
            with self.assertRaises(AssertionError): self.execute(value, lease, transport)
            self.assertEqual(transport.installs, 0)

    def test_boot_wait_is_bounded_and_only_repeats_clean_boot_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
            transport.boot_outputs = [(1, b"", 20), (0, b"0\r\n", 0), (0, b"1\n", 0)]
            owner = q.Owner(value, lease)
            with patch.object(q.host, "run_process", side_effect=transport), patch.object(q.time, "sleep") as pause:
                owner.wait_boot()
            self.assertEqual(owner.stage, "before")
            self.assertEqual(len(transport.calls), 3)
            self.assertEqual(pause.call_count, 2)
            self.assertTrue(all(command[3:] == ["shell", shlex.join(c.IDENTITY[0])] for command, _ in transport.calls))
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
            transport.boot_outputs = [(0, b"0\n", 0)]
            now = [0]
            with patch.object(q.time, "monotonic", side_effect=lambda: now[0]):
                owner = q.Owner(value, lease)
                with patch.object(q.host, "run_process", side_effect=transport), patch.object(q.time, "sleep", side_effect=lambda _: now.__setitem__(0, 61)):
                    with self.assertRaises(AssertionError): owner.wait_boot()
            self.assertEqual(len(transport.calls), 1)
            self.assertEqual(transport.installs, 0)

    def test_every_client_budget_is_clamped_to_remaining_aggregate(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory)); lease = Lease(value); transport = Transport(value, lease)
            owner = q.Owner(value, lease); owner.stage = "before"
            owner.until = q.time.monotonic() + .25
            with patch.object(q.host, "run_process", side_effect=transport):
                owner.dispatch(list(q.AVD_NAME), deadline=15)
            self.assertTrue(0 < transport.calls[0][1]["deadline"] <= .25)

    def test_package_uid_parsers_and_production_unfrozen_apk_map_refuse(self):
        self.assertEqual(q.parse_packages(b"", {}), {})
        self.assertEqual(q.parse_uids(b"", {}), {})
        for raw in (b"\n", b"package:org.locallore.other\n"):
            with self.assertRaises(AssertionError): q.parse_packages(raw, {})
        packages = {q.APP: "a" * 64, q.TEST: "b" * 64}
        for rows in (("package:%s uid:10310\npackage:%s uid:10310\n" % (q.APP, q.TEST)),
                     ("package:%s uid:10310\npackage:%s uid:10311\n" % (q.APP, q.APP))):
            with self.assertRaises(AssertionError): q.parse_uids(rows.encode(), packages)
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory))
            with patch.object(q, "APK_HASHES", {}), self.assertRaises(AssertionError):
                q.validate_proposal(value)

    def test_closed_dispatch_refuses_mutations_repeats_and_alternate_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory)); lease = Lease(value); owner = q.Owner(value, lease); owner.stage = "before"
            with patch.object(q.host, "run_process") as client:
                for args in (["devices"], ["emu", "kill"], ["shell", "pm clear " + q.APP],
                             ["shell", "am force-stop " + q.TEST], ["shell", "rm -r no_backup"],
                             ["shell", "input tap 10 10"], ["shell", shlex.join(q.INITIAL_INSTRUMENT)]):
                    with self.assertRaises(AssertionError): owner.dispatch(args)
                owner.stage = "updating"; owner.pending_install = q.APP
                with self.assertRaises(AssertionError): owner.dispatch(["install", "-r", value["apk_paths"][q.APP]])
                client.assert_not_called()
            owner.stage = "before"; lease.descriptor["serial"] = "emulator-5554"
            with self.assertRaises(AssertionError): owner.dispatch(list(q.AVD_NAME))

    def test_proof_paths_are_closed_and_readiness_markers_must_be_empty(self):
        for name in ("../model", "setup-v1.json;cat secret", "model.litertlm"):
            with self.assertRaises(AssertionError): q.proof_command(name, 10310)
        for uid in (True, 9999, 2 ** 31):
            with self.assertRaises(AssertionError): q.proof_command("setup-v1.json", uid)
        ready = q.proof_command("setup-ready-v1.txt", 10310)
        self.assertIn("-eq 0", ready[-1])
        self.assertIn("-le 4096", ready[-1])

    def test_admission_binds_sources_descriptor_apks_and_exact_authorization(self):
        original_hashes = dict(q.APK_HASHES)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); value = proposal(root)
            path, auth = root / "proposal.json", root / "auth.json"
            q.write_json(path, value)
            authorization = {"version": 1, "proposal_sha256": q.sha(path.read_bytes()), "allow_device_calls": True, "root_go_pending": False}
            q.write_json(auth, authorization)
            with patch.object(q, "APK_HASHES", value["apk_sha256"]):
                self.assertEqual(q.authorize(path, auth, root), value)
                changed = copy.deepcopy(value); changed["bindings"][str((q.ROOT / q.SOURCE_FILES[0]).resolve())] = "0" * 64
                with self.assertRaises(AssertionError): q.validate_proposal(changed)
                changed = dict(value, serial="emulator-5554")
                with self.assertRaises(AssertionError): q.validate_proposal(changed)
                for altered in (dict(authorization, allow_device_calls=False), dict(authorization, version=True),
                                dict(authorization, proposal_sha256="0" * 64), dict(authorization, extra=True)):
                    auth.write_text(json.dumps(altered), encoding="utf-8")
                    with self.assertRaises(AssertionError): q.authorize(path, auth, root)
                Path(value["running_path"]).write_bytes(b"changed descriptor")
                with self.assertRaises(AssertionError): q.validate_proposal(value)
            self.assertEqual(q.APK_HASHES, original_hashes)

    def test_lease_open_pins_client_and_exact_environment_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory)); lease = Lease(value)
            module = SimpleNamespace(open_live_owner=lambda *args: lease)
            with patch.dict(q.sys.modules, {"receipt_avd_environment": module}), patch.object(module, "open_live_owner", return_value=lease) as opener:
                self.assertIs(q.open_lease(value), lease)
                opener.assert_called_once_with(value["environment_proposal_path"], value["running_path"], value["running_sha256"])
                lease.descriptor["adb_path"] = str(Path(directory) / "other-adb.exe")
                with self.assertRaises(AssertionError): q.open_lease(value)

    def test_worker_requires_barrier_and_fresh_admission_before_owner(self):
        with patch.object(q.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b"wrong"))), patch.object(q, "authorize") as admit:
            with self.assertRaises(AssertionError): q.worker("p", "a", "e")
            admit.assert_not_called()
        with patch.object(q.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(q.REQUEST))), patch.object(q, "authorize", side_effect=AssertionError("Binding changed")), patch.object(q, "open_lease") as owner:
            with self.assertRaises(AssertionError): q.worker("p", "a", "e")
            owner.assert_not_called()

    def test_owned_cli_records_result_and_uses_actual_runtime_budget_validator(self):
        real = q.host.run_process
        for rc, clean in ((0, True), (2, True), (0, False)):
            with self.subTest(rc=rc, clean=clean), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); value = proposal(root)
                path, auth = root / "proposal.json", root / "auth.json"
                path.write_bytes(b"mock admitted proposal"); auth.write_bytes(b"mock authorization")
                lease = Lease(value)
                calls = []
                def owned(command, **kwargs):
                    cancel = threading.Event(); cancel.set()
                    with patch.object(q.host.subprocess, "Popen") as spawn:
                        validated = real(command, cancel=cancel, **kwargs)
                    spawn.assert_not_called()
                    self.assertEqual(validated.status, "cancelled")
                    calls.append((command, kwargs))
                    return SimpleNamespace(status="completed", returncode=rc, cleanup_complete=clean,
                                           stdout=b"synthetic child result", stderr_bytes=0, elapsed_ms=1)
                with patch.object(q, "authorize", return_value=value), patch.object(q, "open_lease", return_value=lease), patch.object(q.host, "run_process", side_effect=owned), redirect_stdout(io.StringIO()):
                    actual = q.main(["run", "--proposal", str(path), "--authorization", str(auth), "--evidence", str(root)])
                self.assertEqual(actual, 0 if rc == 0 and clean else 2)
                self.assertEqual(len(calls), 1)
                command, kwargs = calls[0]
                self.assertEqual(command[1:5], ["-B", "-E", str(Path(q.__file__).resolve()), "worker"])
                self.assertEqual(kwargs, {"request": q.REQUEST, "deadline": 180, "max_output": 32768})
                self.assertEqual((root / "receipt-owned-stdout-v1.bin").read_bytes(), b"synthetic child result")
        cancelled = threading.Event(); cancelled.set()
        with self.assertRaises(ValueError): real(["must-not-spawn"], cancel=cancelled, deadline=360)


if __name__ == "__main__":
    unittest.main()
