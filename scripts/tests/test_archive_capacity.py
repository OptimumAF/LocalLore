"""Original ownership and evidence faults; never launches ADB or an app."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import archive_capacity as proof


def verified(**change):
    value = dict(version=1, run="fixed-run", status="verified", archive_sha256=proof.common.digest(b"synthetic"),
                 source_revision=2, continued_revision=3, full_count=1, cache_only_relief=True)
    value.update(change)
    return json.dumps(value).encode()


class CapacityEvidence(unittest.TestCase):
    def test_record_requires_source_and_exact_typed_checks(self):
        self.assertEqual(1, proof.record(verified(), "fixed-run", b"synthetic")["full_count"])
        for changes in (dict(version=True), dict(run="other"), dict(status="ready"), dict(full_count=True),
                        dict(full_count=0), dict(full_count=2), dict(cache_only_relief=1),
                        dict(source_revision=True), dict(source_revision=3), dict(continued_revision=2),
                        dict(extra="unexpected"), dict(archive_sha256="a" * 64)):
            with self.subTest(changes=changes), self.assertRaises(proof.Failure):
                proof.record(verified(**changes), "fixed-run", b"synthetic")

    def test_duplicate_keys_invalid_utf8_and_oversized_records_are_rejected(self):
        for raw in (verified()[:-1] + b',"full_count":1}', b"\xff", b" " * 4097, b"[]"):
            with self.subTest(raw=raw[:20]), self.assertRaises(proof.Failure):
                proof.record(raw, "fixed-run", b"synthetic")

    def test_remote_path_restricts_run_and_never_reads_private_baselines(self):
        self.assertEqual("no_backup/archive-capacity/fixed-run/archive.json", proof.remote_path("fixed-run", "archive.json"))
        for run, name in (("../other", "archive.json"), ("-e injected", "owner-v1"),
                          ("fixed-run", "fixture-baseline.json"), ("fixed-run", "../archive.json")):
            with self.subTest(run=run, name=name), self.assertRaises(proof.Failure):
                proof.remote_path(run, name)

    def test_generalized_parser_binds_capacity_method_and_order(self):
        block = lambda code: ("INSTRUMENTATION_STATUS: class=" + proof.TEST_CLASS + "\n"
            "INSTRUMENTATION_STATUS: test=" + proof.TEST_METHOD + "\n"
            "INSTRUMENTATION_STATUS: numtests=1\nINSTRUMENTATION_STATUS_CODE: " + code + "\n")
        good = (block("1") + block("0") + "OK (1 test)\nINSTRUMENTATION_CODE: -1\n").encode()
        parse = lambda raw: proof.ownership.parse_transcript(raw, expected_class=proof.TEST_CLASS, expected_method=proof.TEST_METHOD)
        self.assertEqual(1, parse(good)["passed"])
        for raw in ((block("0") + block("1") + "OK (1 test)\nINSTRUMENTATION_CODE: -1\n").encode(),
                    good.replace(proof.TEST_METHOD.encode(), b"unrelated"), good + b"INSTRUMENTATION_CODE: -1\n",
                    good.replace(b"STATUS_CODE: 0", b"STATUS_CODE: -3")):
            with self.subTest(raw=raw[-40:]), self.assertRaises(proof.Failure): parse(raw)


class Ownership(unittest.TestCase):
    def setUp(self):
        self.identities = {proof.PACKAGE: "a" * 64, proof.TEST_PACKAGE: "b" * 64}
        self.commands = []
        def shell(*args, **kwargs):
            self.commands.append(args)
            return b"NAME\n" if args[0] == "ps" else b""
        self.device = SimpleNamespace(shell=shell)

    def test_changed_second_identity_prevents_all_stops(self):
        with patch.object(proof.common, "installed_hash", side_effect=("a" * 64, "c" * 64)):
            with self.assertRaisesRegex(proof.Failure, "owned_package_changed"):
                proof.stop_owned(self.device, self.identities)
        self.assertEqual([], self.commands)

    def test_owner_inventory_cannot_add_a_prior_package(self):
        with patch.object(proof.common, "installed_hash") as hashes:
            with self.assertRaisesRegex(proof.Failure, "owned_inventory"):
                proof.stop_owned(self.device, {**self.identities, "org.locallore.app": "c" * 64})
        hashes.assert_not_called()
        self.assertEqual([], self.commands)

    def test_matching_pair_drains_only_owned_packages_and_checks_colon_children(self):
        with patch.object(proof.common, "installed_hash", side_effect=("a" * 64, "b" * 64)):
            proof.stop_owned(self.device, self.identities)
        self.assertEqual([("am", "force-stop", proof.PACKAGE), ("am", "force-stop", proof.TEST_PACKAGE),
                          ("ps", "-A", "-o", "NAME")], self.commands)
        self.device.shell = lambda *args: b"NAME\n" + (proof.TEST_PACKAGE + ":chooser_test_provider\n").encode()
        with patch.object(proof.common, "installed_hash", side_effect=("a" * 64, "b" * 64)):
            with self.assertRaisesRegex(proof.Failure, "owned_process_cleanup"):
                proof.stop_owned(self.device, self.identities)

    def test_process_failure_retains_raw_without_issuing_marker_reads(self):
        attempted = SimpleNamespace(status="timeout", returncode=None, cleanup_complete=True, stdout=b"started only")
        self.device.raw = lambda *args, **kwargs: attempted
        with tempfile.TemporaryDirectory() as directory, patch.object(proof, "read_remote") as read:
            with self.assertRaisesRegex(proof.Failure, "process_failed"):
                proof.exercise(self.device, "fixed-run", Path(directory))
            self.assertEqual(b"started only", (Path(directory) / "instrumentation.raw.txt").read_bytes())
        read.assert_not_called()

    def test_valid_terminal_without_source_bound_record_is_not_a_success(self):
        attempted = SimpleNamespace(status="completed", returncode=0, cleanup_complete=True, stdout=b"passing wire")
        self.device.raw = lambda *args, **kwargs: attempted
        with tempfile.TemporaryDirectory() as directory, patch.object(proof.ownership, "parse_transcript", return_value={"passed":1}), \
                patch.object(proof, "read_remote", side_effect=(proof.MARKER, b"synthetic", verified(archive_sha256="f" * 64))):
            with self.assertRaisesRegex(proof.Failure, "record_source"):
                proof.exercise(self.device, "fixed-run", Path(directory))


if __name__ == "__main__":
    unittest.main()
