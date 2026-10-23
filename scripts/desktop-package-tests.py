#!/usr/bin/env python3
"""Adversarial package format checks; synthetic bytes, no app/model execution."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location("desktop_package", Path(__file__).with_name("desktop-package.py"))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.worker = b"MZ synthetic worker, never executed"
        self.pin = patch.object(package, "WORKER_SHA", package.sha(self.worker))
        self.pin.start()
        self.addCleanup(self.pin.stop)

    def files(self):
        files = {"LocalLore Desktop.exe": b"MZ synthetic application, never executed",
                 "runtime/locallore-llama-worker.exe": self.worker,
                 "runtime/profile-v1.json": package.encode({"runtime_commit": package.RUNTIME_COMMIT, "downloads": False}),
                 "LICENSE": b"synthetic license", "README.txt": b"synthetic readme"}
        return self.seal(files)

    def seal(self, files):
        files["build-manifest.json"] = package.encode({
            "kind": "unsigned-windows-x64-developer-folder-v1", "source_commit": "test",
            "model_weights_included": False, "dev_harness": False,
            "files": {n: {"sha256": package.sha(b), "bytes": len(b)}
                      for n, b in files.items() if n != "build-manifest.json"}})
        return files

    def archive(self, files):
        path = self.directory / "package.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, value in files.items():
                archive.writestr(name, value)
        return path

    def test_closed_inventory_round_trip(self):
        result = package.inspect_archive(self.archive(self.files()))
        self.assertEqual(result["members"], 6)
        self.assertEqual(result["source_commit"], "test")

    def test_missing_tampered_and_unapproved_worker_fail(self):
        for name in ["LICENSE", "LocalLore Desktop.exe", "runtime/locallore-llama-worker.exe"]:
            with self.subTest(name=name):
                files = self.files()
                del files[name]
                with self.assertRaises(ValueError):
                    package.validate_files(files)
        files = self.files()
        files["README.txt"] += b" tampered"
        with self.assertRaisesRegex(ValueError, "inventory"):
            package.validate_files(files)
        files = self.files()
        files["runtime/locallore-llama-worker.exe"] += b" changed"
        self.seal(files)  # Self-consistent external manifest cannot replace pinned worker.
        with self.assertRaisesRegex(ValueError, "UnapprovedWorker"):
            package.validate_files(files)

    def test_extra_weights_save_symbols_and_traversal_fail_even_when_resealed(self):
        for name in ["model.gguf", "story.db", "app.pdb", "runtime/extra.dll",
                     "NOTICES/../model.gguf", "NOTICES/C:/private.txt", "NOTICES\\escape.txt"]:
            with self.subTest(name=name):
                files = self.files()
                files[name] = b"unexpected"
                self.seal(files)
                with self.assertRaisesRegex(ValueError, "Unexpected package member"):
                    package.validate_files(files)

    def test_duplicate_zip_member_and_symlink_fail(self):
        path = self.archive(self.files())
        with zipfile.ZipFile(path, "a") as archive:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr("README.txt", b"duplicate")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            package.inspect_archive(path)
        path.unlink()
        path = self.archive(self.files())
        with zipfile.ZipFile(path, "a") as archive:
            info = zipfile.ZipInfo("NOTICES/link")
            info.external_attr = 0o120777 << 16
            archive.writestr(info, "../private")
        with self.assertRaisesRegex(ValueError, "member type"):
            package.inspect_archive(path)

    def test_unapproved_compression_and_metadata_budget_fail(self):
        path = self.directory / "package.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_LZMA) as archive:
            archive.writestr("README.txt", "tiny")
        with self.assertRaisesRegex(ValueError, "member type"):
            package.inspect_archive(path)
        files = self.files()
        files["runtime/profile-v1.json"] = b" " * 32769
        self.seal(files)
        with self.assertRaisesRegex(ValueError, "Metadata budget"):
            package.validate_files(files)

    def test_development_and_model_policy_flags_are_not_accepted(self):
        for field in ["dev_harness", "model_weights_included"]:
            files = self.files()
            manifest = json.loads(files["build-manifest.json"])
            manifest[field] = True
            files["build-manifest.json"] = package.encode(manifest)
            with self.assertRaisesRegex(ValueError, "policy"):
                package.validate_files(files)

    def test_profile_download_change_and_non_native_app_fail(self):
        files = self.files()
        files["runtime/profile-v1.json"] = package.encode({"runtime_commit": package.RUNTIME_COMMIT, "downloads": True})
        self.seal(files)
        with self.assertRaisesRegex(ValueError, "profile"):
            package.validate_files(files)
        files = self.files()
        files["LocalLore Desktop.exe"] = b"not a PE application"
        self.seal(files)
        with self.assertRaisesRegex(ValueError, "executable"):
            package.validate_files(files)

    def test_notice_binary_and_size_budget_fail(self):
        files = self.files()
        files["NOTICES/hidden.txt"] = b"MZ\0binary"
        self.seal(files)
        with self.assertRaisesRegex(ValueError, "notice"):
            package.validate_files(files)
        files["NOTICES/hidden.txt"] = b"a" * (1024 * 1024 + 1)
        self.seal(files)
        with self.assertRaisesRegex(ValueError, "notice"):
            package.validate_files(files)

    def test_worker_rejection_precedes_build_and_output_creation(self):
        worker = self.directory / "worker.exe"
        worker.write_bytes(b"MZ unapproved")
        args = argparse.Namespace(target_dir=self.directory / "target", output=self.directory / "output",
                                  worker=worker, node=self.directory / "node.exe", npm_cli=self.directory / "npm-cli.js")
        with patch.object(package.sys, "platform", "win32"), patch.object(package, "run") as run:
            with self.assertRaisesRegex(ValueError, "UnapprovedWorker"):
                package.build(args)
            run.assert_not_called()
        self.assertFalse(args.output.exists())

    def test_existing_output_is_preserved_without_reading_or_building(self):
        output = self.directory / "output"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_text("keep")
        args = argparse.Namespace(target_dir=self.directory / "target", output=output,
                                  worker=self.directory / "missing", node=Path("node"), npm_cli=Path("npm"))
        with patch.object(package.sys, "platform", "win32"), patch.object(package, "run") as run:
            with self.assertRaisesRegex(ValueError, "already exists"):
                package.build(args)
            run.assert_not_called()
        self.assertEqual(sentinel.read_text(), "keep")

    def test_build_override_cannot_silently_replace_normal_build_inputs(self):
        args = argparse.Namespace(target_dir=self.directory / "target", output=self.directory / "output",
                                  worker=self.directory / "missing", node=Path("node"), npm_cli=Path("npm"))
        with patch.object(package.sys, "platform", "win32"), patch.dict(os.environ, {"TAURI_CONFIG": "override"}), patch.object(package, "run") as run:
            with self.assertRaisesRegex(ValueError, "Remove build override"):
                package.build(args)
            run.assert_not_called()

    def test_workflow_keeps_runtime_fixture_before_all_target_checks(self):
        # Regression for the standalone runtime missing from the root workspace.
        # Text policy guard, not a YAML parser or proof GitHub executed the job.
        workflow = (package.ROOT / ".github/workflows/desktop.yml").read_text()
        fixture = workflow.index("--features development-worker,engine-adapter --bin protocol-fixture --locked")
        test = workflow.index("test --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --features development-worker,engine-adapter --locked")
        clippy = workflow.index("clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --features development-worker,engine-adapter --locked -- -D warnings")
        self.assertLess(fixture, test)
        self.assertLess(test, clippy)
        for marker in ["persist-credentials: false", "package-manager-cache: false", "contents: read", "--no-audit --no-fund"]:
            self.assertIn(marker, workflow)
        for marker in ["pull_request_target", "self-hosted", "secrets.", "upload-artifact", "write-all", "contents: write", "npm run harness", "--features scene-probe"]:
            self.assertNotIn(marker, workflow)


if __name__ == "__main__":
    unittest.main()
