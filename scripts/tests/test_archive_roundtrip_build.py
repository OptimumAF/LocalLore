"""Host-only admission checks for the archive round-trip cohort."""
from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
from io import StringIO
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import archive_roundtrip_build as build


class ArchiveRoundtripBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = self.enterContext(tempfile.TemporaryDirectory())
        root = Path(temporary)
        self.apk = root / "apk"
        self.windows = root / "windows"
        self.artifacts = {}
        for evidence_root, roster in (
                (self.apk, build._APK_ARTIFACTS), (self.windows, build._WINDOWS_ARTIFACTS)):
            synthetic = {}
            for role, (relative, _, _) in roster.items():
                data = ("synthetic " + role).encode("ascii")
                path = evidence_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                digest = hashlib.sha256(data).hexdigest()
                synthetic[role] = (relative, len(data), digest)
                self.artifacts[role] = dict(path=str(path), bytes=len(data), sha256=digest)
            roster_name = "_APK_ARTIFACTS" if evidence_root == self.apk else "_WINDOWS_ARTIFACTS"
            self.enterContext(patch.object(build, roster_name, synthetic))
        if root.drive.upper() != "D:":
            # The physical D gate is tested independently. Exercise the real
            # shared path and file checks with host-local portable fixtures.
            self.enterContext(patch.object(
                build, "_root", side_effect=lambda value: build.environment.safe_path(value, directory=True)))

    def test_collect_and_recheck_exact_role_bindings(self):
        self.assertEqual(build.collect(self.apk, self.windows), self.artifacts)
        build.verify_current({"artifacts": copy.deepcopy(self.artifacts)})

    def test_same_size_change_refuses_digest(self):
        path = Path(self.artifacts["test_apk"]["path"])
        path.write_bytes(b"x" * path.stat().st_size)
        with self.assertRaisesRegex(build.BuildRefused, "^digest$"):
            build.verify_current({"artifacts": self.artifacts})

    def test_oversized_input_refused_before_opening(self):
        path = Path(self.artifacts["product_apk"]["path"])
        with path.open("ab") as output:
            output.write(b"x")
        with patch.object(Path, "open", side_effect=AssertionError("unexpected read")):
            with self.assertRaisesRegex(build.BuildRefused, "^file$"):
                build._verify_file(self.artifacts["product_apk"])

    def test_file_missing_is_a_refusal(self):
        path = Path(self.artifacts["fixture_executable"]["path"])
        path.rename(path.with_name("retained-fixture.exe"))
        with self.assertRaisesRegex(build.BuildRefused, "^path$"):
            build.collect(self.apk, self.windows)

    def test_cli_missing_input_reports_fixed_category_without_path(self):
        path = Path(self.artifacts["build"]["path"])
        path.rename(path.with_name("retained.json"))
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = build.main(["--apk-root", str(self.apk), "--windows-root", str(self.windows)])
        self.assertEqual(code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "Archive input refusal: path\n")

    def test_hardlink_is_a_refusal(self):
        path = Path(self.artifacts["fixture_executable"]["path"])
        os.link(path, path.with_name("alias.exe"))
        with self.assertRaisesRegex(build.BuildRefused, "^file$"):
            build._verify_file(self.artifacts["fixture_executable"])

    def test_linked_ancestor_is_a_refusal(self):
        path = self.windows / "current-fixtures"
        original = path.with_name("retained-fixtures")
        path.rename(original)
        try:
            path.symlink_to(original, target_is_directory=True)
        except (OSError, NotImplementedError) as failure:
            self.skipTest(f"synthetic symlink unavailable: {type(failure).__name__}")
        with self.assertRaisesRegex(build.BuildRefused, "^path$"):
            build.collect(self.apk, self.windows)

    def test_file_identity_change_refuses_even_with_unchanged_digest(self):
        observed = build._stamp
        calls = 0

        def stamp(info):
            nonlocal calls
            calls += 1
            return observed(info) if calls < 4 else ("different file",)

        with patch.object(build, "_stamp", side_effect=stamp):
            with self.assertRaisesRegex(build.BuildRefused, "^identity$"):
                build._verify_file(self.artifacts["product_apk"])

    def test_mismatched_owner_artifact_refuses_before_read(self):
        for edit in (
                lambda a: a.pop("test_apk"),
                lambda a: a.update(model=a["test_apk"]),
                lambda a: a["test_apk"].update(path=a["product_apk"]["path"]),
                lambda a: a["test_apk"].update(sha256="0" * 64),
                lambda a: a["test_apk"].update(bytes=True),
                lambda a: a["test_apk"].update(extra="field")):
            with self.subTest(edit=edit):
                changed = copy.deepcopy(self.artifacts)
                edit(changed)
                with patch.object(build, "_verify_file", side_effect=AssertionError("unexpected read")):
                    with self.assertRaisesRegex(build.BuildRefused, "^binding$"):
                        build.verify_current({"artifacts": changed})

    def test_overlapping_roots_refuse_before_read(self):
        (self.apk / "nested").mkdir()
        with patch.object(build, "_verify_file", side_effect=AssertionError("unexpected read")):
            with self.assertRaisesRegex(build.BuildRefused, "^root$"):
                build.collect(self.apk, self.apk)
            with self.assertRaisesRegex(build.BuildRefused, "^root$"):
                build.collect(self.apk, self.apk / "nested")


class ArchiveEvidenceRootTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows alias normalization")
    def test_normalized_android_home_is_refused(self):
        alias = Path("D:/evidence/ANDROID~1/packet")
        canonical = Path("D:/evidence/.android/packet")
        with patch.object(build.environment, "safe_path", return_value=alias) as safe:
            with patch.object(Path, "resolve", return_value=canonical) as resolve:
                with self.assertRaisesRegex(build.BuildRefused, "^root$"):
                    build._root(alias)
        safe.assert_called_once_with(alias, directory=True)
        resolve.assert_called_once_with(strict=True)

    def test_relative_or_non_d_path_refuses_before_lookup(self):
        with patch.object(build.environment, "safe_path", side_effect=AssertionError("unexpected lookup")):
            for path in ("relative", "C:/existing", "E:/existing", "D:relative"):
                with self.subTest(path=path):
                    with self.assertRaisesRegex(build.BuildRefused, "^root$"):
                        build._root(path)


if __name__ == "__main__":
    unittest.main()
