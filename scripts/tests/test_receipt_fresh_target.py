"""Pure fresh-target ownership/bootstrap tests; never run Android clients."""
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

SPEC = importlib.util.spec_from_file_location("fresh_target", Path(__file__).resolve().parents[2] / "benchmarks/receipt_fresh_target.py")
fresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fresh)
c = fresh.contract


def proposal(root):
    apks = {fresh.APP: str(root / "app-debug.apk"), fresh.TEST: str(root / "app-debug-androidTest.apk")}
    for path in apks.values():
        Path(path).write_bytes(b"synthetic APK placeholder; never installed")
    environment, running, adb = root / "environment.json", root / "running-v1.json", root / "adb.exe"
    for path in (environment, running, adb):
        path.write_bytes(b"synthetic binding; never executed")
    sources = ("benchmarks/receipt_fresh_target.py", "scripts/android_receipt_qualification_probe.py")
    paths = [fresh.ROOT / name for name in sources] + [environment, running, adb, *map(Path, apks.values())]
    return {"version": 1, "scope": "receipt_fresh_target", "source_commit": "a" * 40,
        "source_final": True, "artifacts_final": True, "allow_device_calls": False, "root_go_pending": True,
        "selected_alias": "C", "environment_proposal_path": str(environment), "running_path": str(running),
        "running_sha256": fresh.sha(running.read_bytes()), "adb_path": str(adb), "apk_paths": apks,
        "apk_sha256": {key: fresh.sha(Path(path).read_bytes()) for key, path in apks.items()},
        "bindings": {str(path.resolve()): fresh.sha(path.read_bytes()) for path in paths}, "evidence_root": str(root)}


class Lease:
    def __init__(self, value):
        self.descriptor = {"serial": "emulator-5592", "avd_name": "LocalLoreReceiptFreshC", "adb_path": value["adb_path"]}
        self.live, self.checks = True, 0

    def check(self):
        self.checks += 1
        if not self.live:
            raise RuntimeError("owner_lost")


def transcript():
    rows = []
    for number, method in enumerate(sorted(c.METHODS), 1):
        for code in (1, 0):
            rows += ["INSTRUMENTATION_STATUS: class=" + c.CLASS,
                "INSTRUMENTATION_STATUS: current=" + str(number), "INSTRUMENTATION_STATUS: id=AndroidJUnitRunner",
                "INSTRUMENTATION_STATUS: numtests=4", "INSTRUMENTATION_STATUS: stream=" + ("." if code == 0 else ""),
                "INSTRUMENTATION_STATUS: test=" + method, "INSTRUMENTATION_STATUS_CODE: " + str(code)]
    return ("\n".join(rows) + "\nINSTRUMENTATION_RESULT: stream=\n\nTime: 0.02\n\nOK (4 tests)\n\nINSTRUMENTATION_CODE: -1\n").encode()


def proof(phase):
    value = {"version": 1, "phase": phase, "pid": 601, "start": 1000, "uid": 10310, "process": fresh.APP,
        "fixture_bytes": 63, "fixture_sha256": c.FIXTURE_SHA256, "candidate_root_absent": True,
        "publication_native_invoked": False, "sdk_invoked": False,
        "external_free_before": c.EXTERNAL_FLOOR + 1000000, "external_free_after": c.EXTERNAL_FLOOR,
        "userdata_free_before": c.USERDATA_FLOOR + 1000000, "userdata_free_after": c.USERDATA_FLOOR,
        "checks": {key: True for key in c.PHASES[phase][2]}}
    if phase == "PROCESS":
        value.update(child_pid=602, child_start=1100, child_uid=10310)
    return value


class Transport:
    def __init__(self, value, lease):
        self.value, self.lease, self.calls = value, lease, []
        self.installs, self.instrumented, self.last_check = 0, False, 0
        self.foreign_name, self.foreign_package, self.uid_drift = False, False, False
        self.foreign_process, self.bad_test, self.bad_manifest, self.bad_proof = False, False, False, False
        self.lose_owner, self.uncertain = False, False
        self.boot_outputs = []

    def __call__(self, command, **kwargs):
        assert command[1:3] == ["-s", self.lease.descriptor["serial"]]
        assert self.lease.checks > self.last_check
        self.last_check = self.lease.checks
        self.calls.append((command, kwargs))
        boot_override = None
        if command[3:] == list(fresh.AVD_NAME):
            raw = (("foreign" if self.foreign_name else self.lease.descriptor["avd_name"]) + "\r\nOK\r\n").encode()
        elif command[3] == "install":
            assert command[3:5] == ["install", "--no-streaming"] and len(command) == 6
            self.installs += 1
            raw = b"Performing Push Install\r\nSuccess\r\n"
        else:
            assert command[3] == "shell"
            op = tuple(shlex.split(command[4]))
            if op in c.IDENTITY:
                raw = (b"1\n", b"35\n", b"x86_64\n", b"4096\n")[c.IDENTITY.index(op)]
                if op == c.IDENTITY[0] and self.boot_outputs:
                    boot_override = self.boot_outputs.pop(0)
                    raw = boot_override[1]
            elif op == c.PACKAGES:
                packages = dict(self.value["apk_sha256"]) if self.installs == 2 else {}
                if self.foreign_package:
                    packages["org.locallore.foreign"] = "f" * 64
                raw = "".join(name + "|" + digest + "  /data/app/synthetic-%d/base.apk\n" % number
                              for number, (name, digest) in enumerate(packages.items())).encode()
            elif op == c.UIDS:
                uids = {fresh.APP: 10310, fresh.TEST: 10311} if self.installs == 2 else {}
                if self.uid_drift and self.instrumented:
                    uids[fresh.APP] = 10312
                raw = "".join("package:%s uid:%d\n" % row for row in uids.items()).encode()
            elif op == c.PS:
                raw = b"PID UID NAME\n1 1000 system_server\n"
                if self.foreign_process:
                    raw += b"606 10310 org.locallore.foreign\n"
            elif op == c.VOLUMES:
                raw = b"public:253,80 mounted 0000-0000\n"
            elif op == c.DF:
                raw = b"Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/dm-46 10000000 1000000 9000000 10% /data/user/0\n"
            elif op == c.DEVICES:
                raw = b"123\n123\n"
            elif op in (c.PROOF_ABSENT, c.INTERNAL_CANDIDATE_ABSENT):
                raw = b""
            elif op == c.INSTRUMENT:
                self.instrumented = True
                raw = transcript()
                if self.bad_test:
                    raw = raw.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2", 1)
            elif op == c.PROOF_MANIFEST:
                names = sorted(c.PROOF_FILES) + (["unexpected"] if self.bad_manifest else [])
                raw = "".join(c.PROOF_ROOT + "/" + name + "\n" for name in names).encode()
            else:
                matched = False
                for phase, (stem, _, _) in c.PHASES.items():
                    for name in (stem + "-ready-v1.txt", stem + "-v1.json"):
                        if op == c.proof_command(name, 10310):
                            value = proof(phase)
                            if self.bad_proof and phase == "PROCESS":
                                value["child_uid"] = 10311
                            raw = b"" if name.endswith(".txt") else json.dumps(value).encode()
                            matched = True
                assert matched, op
        if self.lose_owner:
            self.lease.live = False
        return SimpleNamespace(status="completed", returncode=boot_override[0] if boot_override else 0,
            cleanup_complete=not self.uncertain, stdout=raw, stderr_bytes=boot_override[2] if boot_override else 0, elapsed_ms=1)


class FreshTargetTests(unittest.TestCase):
    def execute(self, value, lease, transport):
        owner = fresh.Owner(value, lease)
        with patch.object(fresh.host, "run_process", side_effect=transport), patch.object(fresh.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
            result = fresh.run_cohort(owner)
        return owner, result

    def test_empty_to_pair_full_four_proofs_and_fresh_uids(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory))
            lease = Lease(value)
            transport = Transport(value, lease)
            owner, result = self.execute(value, lease, transport)
            self.assertEqual(result["before"]["packages"], {})
            self.assertEqual(result["final"]["uid_map"], {fresh.APP: 10310, fresh.TEST: 10311})
            self.assertEqual(result["tests"]["passed"], 4)
            self.assertEqual(set(result["proofs"]), set(c.PHASES))
            self.assertEqual(owner.installs, {fresh.APP: 1, fresh.TEST: 1})
            self.assertEqual(owner.methods, 1)
            self.assertEqual(owner.count, len(transport.calls))
            self.assertGreaterEqual(lease.checks, 2 * owner.count)
            self.assertTrue(all(command[2] == "emulator-5592" for command, _ in transport.calls))
            self.assertTrue(all(0 < kwargs["deadline"] <= 120 for _, kwargs in transport.calls))

    def test_foreign_name_package_or_process_stops_before_install(self):
        for flag in ("foreign_name", "foreign_package", "foreign_process"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory))
                lease = Lease(value)
                transport = Transport(value, lease)
                setattr(transport, flag, True)
                owner = fresh.Owner(value, lease)
                with patch.object(fresh.host, "run_process", side_effect=transport), patch.object(fresh.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                    with self.assertRaises((AssertionError, KeyError)):
                        fresh.run_cohort(owner)
                self.assertEqual(transport.installs, 0)
                self.assertFalse(transport.instrumented)
                self.assertFalse((owner.directory / "before-facts.json").exists())

    def test_owner_loss_or_unknown_cleanup_retains_raw_and_prevents_later_clients(self):
        for flag in ("lose_owner", "uncertain"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory))
                lease = Lease(value)
                transport = Transport(value, lease)
                setattr(transport, flag, True)
                owner = fresh.Owner(value, lease)
                owner.stage = "before"
                with patch.object(fresh.host, "run_process", side_effect=transport):
                    with self.assertRaises((AssertionError, RuntimeError)):
                        owner.dispatch(list(fresh.AVD_NAME))
                    self.assertEqual((owner.commands / "command-0001.stdout.bin").read_bytes(), b"LocalLoreReceiptFreshC\r\nOK\r\n")
                    self.assertTrue((owner.commands / "command-0001.json").exists())
                    with self.assertRaises((AssertionError, RuntimeError)):
                        owner.dispatch(list(fresh.AVD_NAME))
                self.assertEqual(len(transport.calls), 1)

    def test_capacity_boundary_and_short_refusal_before_mutation(self):
        for short in (0, 1):
            with self.subTest(short=short), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory))
                lease, owner = Lease(value), None
                transport = Transport(value, lease)
                owner = fresh.Owner(value, lease)
                original = owner.facts
                def facts(label, packages):
                    result = original(label, packages)
                    if label == "before":
                        result["userdata"]["available_bytes"] = c.USERDATA_FLOOR + sum(Path(p).stat().st_size for p in value["apk_paths"].values()) - short
                    return result
                with patch.object(owner, "facts", side_effect=facts), patch.object(fresh.host, "run_process", side_effect=transport), patch.object(fresh.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                    if short:
                        with self.assertRaises(AssertionError):
                            fresh.run_cohort(owner)
                        self.assertEqual(transport.installs, 0)
                        self.assertFalse(transport.instrumented)
                    else:
                        self.assertEqual(fresh.run_cohort(owner)["tests"]["passed"], 4)

    def test_bounded_boot_wait_retries_only_closed_clean_results(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory))
            lease = Lease(value)
            transport = Transport(value, lease)
            transport.boot_outputs = [(1, b"", 20), (0, b"0\r\n", 0), (0, b"\n", 0), (0, b"1\n", 0)]
            owner = fresh.Owner(value, lease)
            with patch.object(fresh.host, "run_process", side_effect=transport), patch.object(fresh.time, "sleep") as pause:
                owner.wait_boot()
            self.assertEqual(owner.stage, "before")
            self.assertEqual(len(transport.calls), 4)
            self.assertEqual(pause.call_count, 3)
            self.assertEqual(transport.installs, 0)
            self.assertTrue(all(command[3:] == ["shell", shlex.join(c.IDENTITY[0])] for command, _ in transport.calls))
        for kind in ("exhausted", "uncertain", "unexpected"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory))
                lease = Lease(value)
                transport = Transport(value, lease)
                transport.boot_outputs = [(0, b"unexpected\n" if kind == "unexpected" else b"0\n", 0)]
                transport.uncertain = kind == "uncertain"
                clock = [0]
                with patch.object(fresh.time, "monotonic", side_effect=lambda: clock[0]):
                    owner = fresh.Owner(value, lease)
                    def expired(_): clock[0] = 61
                    with patch.object(fresh.host, "run_process", side_effect=transport), patch.object(fresh.time, "sleep", side_effect=expired):
                        with self.assertRaises(AssertionError):
                            fresh.run_cohort(owner)
                self.assertEqual(len(transport.calls), 1)
                self.assertEqual(transport.installs, 0)
                self.assertFalse(transport.instrumented)

    def test_uid_drift_failed_test_or_proof_drift_stops_without_final_facts(self):
        for flag, stage in (("uid_drift", "after"), ("bad_test", "instrumentation"), ("bad_manifest", "proofs"), ("bad_proof", "proofs")):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory))
                lease = Lease(value)
                transport = Transport(value, lease)
                setattr(transport, flag, True)
                owner = fresh.Owner(value, lease)
                with patch.object(fresh.host, "run_process", side_effect=transport), patch.object(fresh.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                    with self.assertRaises(AssertionError):
                        fresh.run_cohort(owner)
                self.assertEqual(owner.stage, stage)
                self.assertEqual(owner.methods, 1)
                self.assertFalse((owner.directory / "final-facts.json").exists())
                self.assertTrue((owner.commands / ("command-%04d.stdout.bin" % owner.count)).exists())

    def test_both_files_verified_before_first_install(self):
        for content in (b"", b"changed"):
            with tempfile.TemporaryDirectory() as directory:
                value = proposal(Path(directory))
                Path(value["apk_paths"][fresh.TEST]).write_bytes(content)
                lease = Lease(value)
                transport = Transport(value, lease)
                with self.assertRaises(AssertionError):
                    self.execute(value, lease, transport)
                self.assertEqual(transport.installs, 0)

    def test_closed_dispatch_no_lifecycle_or_serial_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory))
            lease = Lease(value)
            owner = fresh.Owner(value, lease)
            owner.stage = "before"
            with patch.object(fresh.host, "run_process") as execute:
                for args in (["devices", "-l"], ["shell", "am force-stop " + fresh.APP], ["shell", "pm clear " + fresh.APP], ["emu", "kill"]):
                    with self.assertRaises(AssertionError):
                        owner.dispatch(args)
                execute.assert_not_called()
            lease.descriptor["serial"] = "emulator-5584"
            with self.assertRaises(AssertionError):
                owner.dispatch(list(fresh.AVD_NAME))

    def test_empty_and_pair_parsers_are_closed_and_leave_B_parser_strict(self):
        self.assertEqual(fresh.parse_packages(b"", {}), {})
        self.assertEqual(fresh.parse_uids(b"", {}), {})
        for raw in (b"\n", b"package:org.locallore.other\n"):
            with self.assertRaises(AssertionError):
                fresh.parse_packages(raw, {})
        with self.assertRaises(AssertionError):
            c.parse_packages(b"")
        with self.assertRaises(AssertionError):
            fresh.parse_uids(("package:%s uid:10310\npackage:%s uid:10310\n" % (fresh.APP, fresh.TEST)).encode(), {fresh.APP: "a" * 64, fresh.TEST: "a" * 64})

    def test_authorization_closed_keys_and_binding_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = proposal(root)
            path, auth = root / "proposal.json", root / "auth.json"
            fresh.write_json(path, value)
            fresh.write_json(auth, {"version": 1, "proposal_sha256": fresh.sha(path.read_bytes()), "allow_device_calls": True, "root_go_pending": False})
            with patch.object(fresh, "SOURCE_FILES", ("benchmarks/receipt_fresh_target.py", "scripts/android_receipt_qualification_probe.py")), patch.object(fresh, "APK_HASHES", value["apk_sha256"]):
                self.assertEqual(fresh.authorize(path, auth, root), value)
                Path(value["running_path"]).write_bytes(b"descriptor changed")
                with self.assertRaises(AssertionError):
                    fresh.authorize(path, auth, root)
            extra = dict(value, serial="emulator-5584")
            with self.assertRaises(AssertionError):
                fresh.validate_proposal(extra)

    def test_lease_open_uses_exact_environment_api_and_pinned_client(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory))
            lease = Lease(value)
            module = SimpleNamespace(open_live_owner=lambda *args: lease)
            with patch.dict(fresh.sys.modules, {"receipt_avd_environment": module}):
                with patch.object(module, "open_live_owner", return_value=lease) as opener:
                    self.assertIs(fresh.open_lease(value), lease)
                opener.assert_called_once_with(value["environment_proposal_path"], value["running_path"], value["running_sha256"])
                lease.descriptor["adb_path"] = str(Path(directory) / "alternate-adb.exe")
                with self.assertRaises(AssertionError):
                    fresh.open_lease(value)

    def test_worker_barrier_refuses_before_admission_and_rechecks_after_release(self):
        with patch.object(fresh.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b"wrong\n"))), patch.object(fresh, "authorize") as admit:
            with self.assertRaises(AssertionError):
                fresh.worker("proposal", "auth", "evidence")
            admit.assert_not_called()
        with patch.object(fresh.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(fresh.REQUEST))), patch.object(fresh, "authorize", side_effect=AssertionError("changed_binding")) as admit, patch.object(fresh, "open_lease") as open_owner:
            with self.assertRaises(AssertionError):
                fresh.worker("proposal", "auth", "evidence")
            admit.assert_called_once_with("proposal", "auth", "evidence")
            open_owner.assert_not_called()

    def test_cli_owned_worker_arguments_request_deadline_and_raw_result(self):
        for rc, clean in ((0, True), (2, True), (0, False)):
            with self.subTest(rc=rc, clean=clean), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                value = proposal(root)
                path, auth = root / "proposal.json", root / "auth.json"
                path.write_bytes(b"mock proposal")
                auth.write_bytes(b"mock auth")
                lease = Lease(value)
                result = SimpleNamespace(status="completed", returncode=rc, cleanup_complete=clean, stdout=b"raw child\n", stderr_bytes=0, elapsed_ms=10)
                with patch.object(fresh, "authorize", return_value=value), patch.object(fresh, "open_lease", return_value=lease), patch.object(fresh.host, "run_process", return_value=result) as execute, redirect_stdout(io.StringIO()):
                    actual = fresh.main(["run", "--proposal", str(path), "--authorization", str(auth), "--evidence", str(root)])
                self.assertEqual(actual, 0 if rc == 0 and clean else 2)
                args, kwargs = execute.call_args
                self.assertEqual(args[0][1:5], ["-B", "-E", str(Path(fresh.__file__).resolve()), "worker"])
                self.assertEqual(kwargs, {"request": fresh.REQUEST, "deadline": 180, "max_output": 32768})
                self.assertEqual((root / "receipt-owned-stdout-v1.bin").read_bytes(), b"raw child\n")
                self.assertEqual(json.loads((root / "receipt-owned-result-v1.json").read_bytes())["cleanup_complete"], clean)


if __name__ == "__main__":
    unittest.main()
