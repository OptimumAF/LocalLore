"""SDK25 outbound order and byte-binding tests with synthetic capture records."""
import copy
import hashlib
from pathlib import PureWindowsPath
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_build as build
from benchmarks import archive_roundtrip_outbound as outbound
from benchmarks import owned_archive_roundtrip_client as client
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_archive_roundtrip_owner as owner
from scripts.tests import test_android_instrumentation_evidence as junit
from scripts.tests import test_owned_archive_roundtrip_profile as profile
from scripts.tests import test_owned_target_contract as legacy


def binding(path, data):
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class CaptureFixture:
    def __init__(self, admission, windows):
        self.admission = admission
        self.session = legacy.session(admission)
        self.session["protocol"] = contract.SDK_PROTOCOL
        self.session["descriptor"]["protocol"] = contract.PROTOCOL
        self.root = PureWindowsPath(admission["root"]) / "archive-transfer-v1"
        self.session["root"] = str(self.root)
        self.session_pin = legacy.pin(self.root / contract.SESSION_FILE)
        self.steps = []
        self.verified = []
        self.windows = windows
        self.capture = client.OwnedArchiveRoundtripSdkCapture.__new__(client.OwnedArchiveRoundtripSdkCapture)
        self.capture.clean, self.capture.count = True, 0
        self.capture._session_binding = self.session_pin
        self.capture._session = copy.deepcopy(self.session)
        self.capture.lease = SimpleNamespace(admission=admission)
        self.capture.close = Mock()
        self.capture.shell = lambda argv, label, **options: self.dispatch(argv, label, None)
        self.capture.stream = lambda argv, source, label, **options: self.dispatch(argv, label, source)

    def step(self, label, argv, raw, source=None, seconds=15):
        index = len(self.steps) + 1
        stem = self.root / "clients" / f"command-{index:04d}"
        stdout = binding(stem.with_suffix(".stdout.bin"), raw)
        stderr = binding(stem.with_suffix(".stderr.bin"), b"")
        self.steps.append({
            "index": index, "label": label, "operation": {"argv": argv, "stdin": source},
            "stdout": stdout, "stderr": stderr, "effective_deadline_ms": seconds * 1000,
            "raw": raw, "pin": legacy.pin(stem.with_suffix(".json")),
        })

    def dispatch(self, argv, label, source):
        index = self.capture.count
        step = self.steps[index]
        if step["label"] != label or step["operation"] != dict(argv=argv, stdin=source):
            raise AssertionError(f"unexpected synthetic dispatch at {index + 1}")
        self.capture.count += 1
        return step["raw"]

    def _json(self, pin):
        if pin != self.session_pin:
            raise AssertionError("unbound synthetic session")
        return copy.deepcopy(self.session)

    def _pin(self, path):
        name = PureWindowsPath(str(path)).name
        if name == contract.SESSION_FILE:
            return self.session_pin
        return self.steps[int(name.removeprefix("command-").removesuffix(".json")) - 1]["pin"]

    def verify_client_record(self, pin, session, admission):
        if session != self.session or admission != self.admission:
            raise AssertionError("unbound synthetic replay")
        for step in self.steps:
            if step["pin"] == pin:
                self.verified.append(step["index"])
                return copy.deepcopy(step)
        raise AssertionError("unknown synthetic record")

    def _raw(self, pin, cap):
        for step in self.steps:
            if step["stdout"] == pin and len(step["raw"]) <= cap:
                return step["raw"]
        raise AssertionError("unbound synthetic stdout")

    def set_raw(self, step, raw):
        step["raw"] = raw
        step["stdout"] = binding(step["stdout"]["path"], raw)

    def first(self, label):
        return next(step for step in self.steps if step["label"] == label)

    def ready(self):
        a = self.admission
        boot = ["getprop", "sys.boot_completed"]
        self.step("boot", boot, b"0\n")
        self.step("boot", boot, b"1\n")
        for key, raw in (("ro.build.version.sdk", b"35\n"), ("ro.product.cpu.abi", b"x86_64\n"),
                         ("ro.kernel.qemu", b"1\n")):
            self.step("target", ["getprop", key], raw)
        self.step("user", ["am", "get-current-user"], b"0\n")
        packages = ("org.locallore.app.archiveverify", "org.locallore.app.archiveverify.test")

        def package_list(package):
            return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]

        for package in packages:
            self.step("package-absent", package_list(package), b"")
        for role in ("product_apk", "test_apk"):
            source = a["artifacts"][role]
            remote = contract.staged_path(a, role)
            self.step("apk-stage", contract.stage_argv(a, role), b"", source, 120)
            self.step("apk-sha", ["sha256sum", remote], (source["sha256"] + "  " + remote + "\n").encode())
            self.step("apk-install", ["pm", "install", "-R", "-t", "--user", "0", remote], b"Success\n", seconds=120)

        def installed():
            rows = [(f"package:{package} uid:{10001 + index}\n").encode()
                    for index, package in enumerate(packages)]
            for i, (package, role) in enumerate(zip(packages, ("product_apk", "test_apk"), strict=True)):
                self.step("installed-uid", package_list(package), b"".join(rows) if i == 0 else rows[1])
                path = "/data/app/~~token/" + package + "-token/base.apk"
                self.step("installed-path", ["cmd", "package", "path", "--user", "0", package],
                          ("package:" + path + "\n").encode())
                self.step("installed-sha", ["sha256sum", path],
                          (a["artifacts"][role]["sha256"] + "  " + path + "\n").encode())

        installed()
        class_name = "org.locallore.app.ArchivePlatformRoundTripTest"
        method = "platformRoundTrip"
        passed = (junit.bundle(method, 1, 1, cls=class_name, count=1) +
                  junit.bundle(method, 1, 0, cls=class_name, count=1) + junit.ending(1)).encode()
        self.step("archive_outbound", contract.outbound_argv(a), passed, seconds=120)
        self.step("owner-marker", contract.read_argv(a, "owner-v1"), b"locallore-platform-roundtrip-v1")
        for leaf, data in self.windows.items():
            self.step("archive-read", contract.read_argv(a, leaf), data)
        installed()
        return self


class ArchiveOutboundTests(unittest.TestCase):
    def setUp(self):
        self.files = {
            "windows-return.json": b"synthetic Windows origin",
            "windows-continued.json": b"synthetic Windows continuation",
            "android-origin.json": b"synthetic Android origin for later Rust validation",
        }
        entries = dict(build._WINDOWS_ARTIFACTS)
        for role, leaf in (("windows_origin", "windows-return.json"), ("windows_continued", "windows-continued.json")):
            data = self.files[leaf]
            entries[role] = (entries[role][0], len(data), hashlib.sha256(data).hexdigest())
        self.enterContext(patch.object(build, "_WINDOWS_ARTIFACTS", entries))
        self.fixture = CaptureFixture(profile.admission(), self.files).ready()
        self.enterContext(patch.object(owner, "VERIFIER", self.fixture))
        self.sleep = self.enterContext(patch.object(outbound.time, "sleep"))

    def replay(self, count=None):
        return outbound.replay_prefix(self.fixture.admission, self.fixture.session_pin,
                                      len(self.fixture.steps) if count is None else count)

    def test_live_and_closed_replay_verify_same_31_command_prefix(self):
        fixture = self.fixture
        live = outbound.run(fixture.capture)
        self.assertEqual(len(live["records"]), 31)
        self.assertEqual(live["files"], self.files)
        self.assertTrue(live["instrumentation"]["passed"])
        self.assertEqual(live["installed"]["product_apk"]["uid"], 10001)
        self.assertEqual(fixture.verified, list(range(1, 32)))
        self.sleep.assert_called_once_with(2)
        fixture.step("later-command", ["getprop", "sys.boot_completed"], b"1\n")
        self.assertEqual(self.replay(31), live)
        fixture.capture.close.assert_not_called()

    def test_package_collision_aborts_before_staging(self):
        fixture = self.fixture
        step = [step for step in fixture.steps if step["label"] == "package-absent"][1]
        fixture.set_raw(step, b"package:org.locallore.app.archiveverify.test uid:10002\n")
        with self.assertRaisesRegex(outbound.OutboundRefused, "^package_present$"):
            outbound.run(fixture.capture)
        self.assertEqual(fixture.capture.count, step["index"])
        fixture.capture.close.assert_called_once_with()

    def test_wrong_user_aborts_before_package_inspection(self):
        fixture = self.fixture
        step = fixture.first("user")
        fixture.set_raw(step, b"10\n")
        with self.assertRaisesRegex(outbound.OutboundRefused, "^target$"):
            outbound.run(fixture.capture)
        self.assertEqual(fixture.capture.count, step["index"])

    def test_foreign_installed_path_refuses_before_using_it(self):
        fixture = self.fixture
        step = fixture.first("installed-path")
        fixture.set_raw(step, b"package:/data/app/~~token/other.package-token/base.apk\n")
        with self.assertRaisesRegex(outbound.OutboundRefused, "^package_identity$"):
            outbound.run(fixture.capture)
        self.assertEqual(fixture.capture.count, step["index"])

    def test_staged_hash_mismatch_aborts_before_install(self):
        fixture = self.fixture
        step = fixture.first("apk-sha")
        fixture.set_raw(step, b"not-the-staged-hash\n")
        with self.assertRaisesRegex(outbound.OutboundRefused, "^apk_stage$"):
            outbound.run(fixture.capture)
        self.assertEqual(fixture.capture.count, step["index"])

    def test_bad_terminal_refuses_before_private_read(self):
        fixture = self.fixture
        step = fixture.first("archive_outbound")
        fixture.set_raw(step, step["raw"].replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2"))
        with self.assertRaises(outbound.instrumentation.EvidenceRefused):
            self.replay()
        self.assertEqual(fixture.verified[-1], step["index"])

    def test_bad_marker_refuses_before_archive_read(self):
        fixture = self.fixture
        step = fixture.first("owner-marker")
        fixture.set_raw(step, b"wrong-owner")
        with self.assertRaisesRegex(outbound.OutboundRefused, "^owner_marker$"):
            self.replay()
        self.assertEqual(fixture.verified[-1], step["index"])

    def test_same_size_wrong_windows_bytes_refuse_before_continuation(self):
        fixture = self.fixture
        step = fixture.first("archive-read")
        fixture.set_raw(step, b"x" * len(step["raw"]))
        with self.assertRaisesRegex(outbound.OutboundRefused, "^windows_archive_drift$"):
            self.replay()

    def test_final_package_uid_drift_refuses(self):
        fixture = self.fixture
        step = [step for step in fixture.steps if step["label"] == "installed-uid"][-1]
        earlier = [row for row in fixture.steps if row["label"] == "installed-uid"][-2]
        for row in (earlier, step):
            fixture.set_raw(row, row["raw"].replace(b"10002", b"10003"))
        with self.assertRaisesRegex(outbound.OutboundRefused, "^package_drift$"):
            self.replay()

    def test_bad_record_index_label_or_input_cannot_fill_required_step(self):
        fixture = self.fixture
        step = fixture.first("apk-stage")
        original = copy.deepcopy(step)
        for field, value in (("index", step["index"] + 1), ("label", "apk-install"),
                             ("operation", dict(step["operation"], stdin=None))):
            with self.subTest(field=field):
                step.update(original)
                step[field] = value
                with self.assertRaisesRegex(outbound.OutboundRefused, "^command_evidence$"):
                    self.replay()

    def test_wrong_prefix_count_refuses_missing_or_trailing_steps(self):
        with self.assertRaisesRegex(outbound.OutboundRefused, "^command_count$"):
            self.replay(30)
        with self.assertRaisesRegex(outbound.OutboundRefused, "^command_count$"):
            self.replay(32)

    def test_closed_capture_cap_and_empty_stderr_match_live_requirements(self):
        fixture = self.fixture
        step = fixture.first("target")
        fixture.set_raw(step, b"x" * (outbound.SETUP_CAP + 1))
        with self.assertRaisesRegex(outbound.OutboundRefused, "^command_evidence$"):
            self.replay()
        fixture.set_raw(step, b"35\n")
        step["stderr"]["bytes"] = 1
        with self.assertRaisesRegex(outbound.OutboundRefused, "^command_evidence$"):
            self.replay()

    def test_session_must_live_under_exact_admission_output(self):
        self.fixture.session["root"] = "D:/Synthetic/other-transfer"
        with self.assertRaisesRegex(outbound.OutboundRefused, "^session$"):
            self.replay()
        self.assertEqual(self.fixture.verified, [])

    def test_conflicting_test_uid_in_product_query_refuses(self):
        fixture = self.fixture
        step = fixture.first("installed-uid")
        fixture.set_raw(step, step["raw"].replace(b"10002", b"10003"))
        with self.assertRaisesRegex(outbound.OutboundRefused, "^package_identity$"):
            self.replay()

    def test_expired_boot_refuses_before_any_live_dispatch(self):
        fixture = self.fixture
        with patch.object(outbound.time, "monotonic", side_effect=[0, 121]):
            with self.assertRaisesRegex(outbound.OutboundRefused, "^boot$"):
                outbound.run(fixture.capture)
        self.assertEqual(fixture.capture.count, 0)

    def test_late_boot_success_refuses_before_target_queries(self):
        fixture = self.fixture
        fixture.set_raw(fixture.steps[0], b"1\n")
        original = fixture.capture.shell
        fixture.capture.shell = Mock(side_effect=original)
        with patch.object(outbound.time, "monotonic", side_effect=[0, 119.5, 120.1]):
            with self.assertRaisesRegex(outbound.OutboundRefused, "^boot$"):
                outbound.run(fixture.capture)
        fixture.capture.shell.assert_called_once_with(["getprop", "sys.boot_completed"],
                                                       "boot", seconds=0.5, cap=4096)
        self.assertEqual(fixture.capture.count, 1)

    def test_live_session_drift_refuses_before_dispatch(self):
        self.fixture.capture._session["deadline_epoch"] += 1
        with self.assertRaisesRegex(outbound.OutboundRefused, "^session$"):
            outbound.run(self.fixture.capture)
        self.assertEqual(self.fixture.capture.count, 0)

    def test_replay_refuses_foreign_session_path_before_reading(self):
        pin = dict(self.fixture.session_pin, path="D:/Synthetic/other/sdk-session-v25.json")
        with patch.object(self.fixture, "_json", side_effect=AssertionError("unexpected read")):
            with self.assertRaisesRegex(outbound.OutboundRefused, "^session$"):
                outbound.replay_prefix(self.fixture.admission, pin, 31)

    def test_boot_timeout_consumes_only_bounded_reads(self):
        fixture = self.fixture
        fixture.steps.clear()
        for _ in range(outbound.BOOT_READS):
            fixture.step("boot", ["getprop", "sys.boot_completed"], b"0\n")
        with self.assertRaisesRegex(outbound.OutboundRefused, "^boot$"):
            self.replay(outbound.BOOT_READS + outbound.FIXED_COMMANDS)
        self.assertEqual(len(fixture.verified), outbound.BOOT_READS)


if __name__ == "__main__":
    unittest.main()
