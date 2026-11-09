"""Exercise SDK24 retirement preservation with an isolated synthetic D: guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import cross_owner_deletion_ui_failed_close as close
from benchmarks import cross_owner_deletion_ui_retirement_preservation as preservation
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage


REFUSALS = (OSError, RuntimeError, ValueError)
CREDENTIALS = ("emulator/adbkey", "emulator/adbkey.pub")
CLOSURE = "guest-storage-closure-v1.json"


class CrossOwnerDeletionRetirementPreservationTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(TemporaryDirectory(dir="D:/Dev/_Temp"))).resolve()
        self.registry = self.base / "registry"
        self.guest = self.base / "guest"
        self.close_output = self.base / "close"
        self.output = self.base / "preservation"
        self.existing = self.base / "existing-private-copies"
        for path in (self.registry, self.guest, self.close_output, self.output, self.existing):
            path.mkdir()
        self.ledger = self.registry / "ledger-v1.json"
        self.enterContext(patch.object(storage, "DEFAULT_REGISTRY", self.registry))
        self.enterContext(patch.object(close.h, "LEDGER", self.ledger))
        self.enterContext(patch.object(close.h, "GUEST", self.guest))
        self.enterContext(patch.object(close, "OUT", self.close_output))
        for name in ("PLAN", "AUTHORITY", "CLAIM", "BEFORE", "AFTER", "REVIEW"):
            self.enterContext(patch.object(close, name, self.close_output / (name.lower() + ".json")))
        self.enterContext(patch.object(preservation, "OUT", self.output))
        for name, leaf in (
            ("RECORDS", "records"), ("STAGED", "staged-v1.json"),
            ("CREDENTIALS", "existing-credentials-v1.json"), ("MANIFEST", "manifest-v1.json"),
        ):
            self.enterContext(patch.object(preservation, name, self.output / leaf))

        self.ordinary = ("config.ini", "logs/failure.txt")
        self.image = storage.CONTENT + "userdata-qemu.img"
        originals = {
            self.ordinary[0]: b"synthetic config",
            self.ordinary[1]: b"preserved synthetic failure",
            self.image: b"synthetic image bytes",
            CREDENTIALS[0]: b"fake test private credential",
            CREDENTIALS[1]: b"fake test public credential",
        }
        self.original = {}
        for relative, payload in originals.items():
            self.original[relative] = self.write(self.guest / relative, payload)
        self.backups = {relative: self.write(self.existing / relative, originals[relative])
                        for relative in CREDENTIALS}

        self.evidence = {}
        for role in ("operation", "observed", "run", "admission", "inner_terminal", "worker"):
            self.evidence[role] = self.save(self.base / (role + ".json"), {"synthetic": role})
        self.retained_entry = dict(root=str(self.guest), proposal_sha256=self.evidence["run"]["sha256"],
                                   state="retained", reserved_bytes=storage.RESERVATION_BYTES,
                                   closure=None, retirement=None, retirement_receipt=None, recovery=None)
        self.ledger_before = self.save(self.ledger, dict(
            version=2, max_guests=storage.MAX_GUESTS, budget_bytes=storage.BUDGET_BYTES,
            reservation_bytes=storage.RESERVATION_BYTES, entries=[self.retained_entry],
        ))
        self.evidence["ledger"] = self.ledger_before
        processes = [dict(identity=dict(pid=i, creation_filetime=i + 1000,
                                       executable=r"C:\Synthetic\python.exe"), status="pid_absent")
                     for i in range(31, 38)]
        self.report = dict(version=1, scope=close.review.SCOPE, disposition="guarded_closure_review_required",
                           existing_retirement_eligible=False, execution_authorized=False,
                           evidence=self.evidence, processes=processes)
        self.review_pin = self.save(close.REVIEW, self.report)
        self.enterContext(patch.object(close, "_fresh_review", side_effect=self.fresh_review))
        self.enterContext(patch("subprocess.Popen", side_effect=AssertionError("unexpected process")))
        self.enterContext(patch("socket.socket", side_effect=AssertionError("unexpected socket")))
        self.plan = self.save(close.PLAN, close.build_plan(self.review_pin))

    @staticmethod
    def save(path, value):
        env.create_json(path, value)
        return storage.binding(path)

    @staticmethod
    def write(path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return storage.binding(path)

    def fresh_review(self, review_pin, ledger_pin, *, locked_entry=None):
        self.assertEqual(review_pin, self.review_pin)
        self.assertEqual(ledger_pin, self.ledger_before)
        if locked_entry is not None:
            self.assertEqual(locked_entry, self.retained_entry)
        return copy.deepcopy(self.report)

    def stage(self):
        with patch.object(storage, "_atomic_write", side_effect=AssertionError("unexpected ledger mutation")) as write:
            staged = preservation.stage(self.plan)
        write.assert_not_called()
        self.assertEqual(staged, storage.binding(preservation.STAGED))
        return staged

    def close_guest(self):
        authority = self.save(close.AUTHORITY, dict(
            version=1, scope=close.AUTHORITY_SCOPE, plan=self.plan,
            approval_reference="synthetic closure-only approval",
            allow_close=True, allow_retirement=False, allow_boot=False,
        ))
        return close.execute(authority)["ledger"]

    def credentials(self, records=None):
        records = self.backups if records is None else records
        return self.save(preservation.CREDENTIALS, dict(
            version=1, root=str(self.guest),
            files=[dict(relative=name, binding=pin) for name, pin in records.items()],
        ))

    def complete(self, staged_pin, credentials_pin, ledger_pin):
        with patch.object(storage, "_atomic_write", side_effect=AssertionError("unexpected ledger mutation")) as write:
            result = preservation.complete(staged_pin, credentials_pin, ledger_pin)
        write.assert_not_called()
        return result

    def assert_no_completion(self):
        self.assertFalse(preservation.MANIFEST.exists())
        self.assertFalse((preservation.RECORDS / CLOSURE).exists())

    def assert_originals_intact(self):
        for pins in (self.original, self.backups):
            for pin in pins.values():
                self.assertEqual(storage.binding(pin["path"]), pin)

    def test_stage_copies_only_ordinary_records_without_changing_ledger_or_originals(self):
        protected = {self.guest / name for name in (*CREDENTIALS, self.image)}
        open_file = Path.open

        def guarded_open(path, *args, **kwargs):
            self.assertNotIn(path, protected)
            return open_file(path, *args, **kwargs)

        with patch.object(Path, "open", guarded_open):
            self.stage()
        files = storage._files(preservation.RECORDS)
        self.assertEqual(set(files), set(self.ordinary))
        for name in self.ordinary:
            copy_pin = storage.binding(files[name])
            self.assertNotEqual(copy_pin["path"], self.original[name]["path"])
            self.assertEqual(copy_pin["bytes"], self.original[name]["bytes"])
            self.assertEqual(copy_pin["sha256"], self.original[name]["sha256"])
        self.assertEqual(storage.binding(self.ledger), self.ledger_before)
        self.assert_originals_intact()
        self.assert_no_completion()

    def test_complete_preserves_exact_manifest_and_reuses_two_external_credential_copies(self):
        staged = self.stage()
        ledger = self.close_guest()
        credentials = self.credentials()
        self.assertEqual(self.complete(staged, credentials, ledger), storage.binding(preservation.MANIFEST))
        manifest = storage.read_json(preservation.MANIFEST)
        self.assertEqual(set(manifest), {"version", "root", "complete", "files"})
        self.assertEqual(manifest["root"], str(self.guest))
        self.assertIs(manifest["complete"], True)
        rows = {row["relative"]: row["binding"] for row in manifest["files"]}
        self.assertEqual(set(rows), {*self.ordinary, *CREDENTIALS, CLOSURE})
        for name in CREDENTIALS:
            self.assertEqual(rows[name], self.backups[name])
        self.assertEqual(set(storage._files(preservation.RECORDS)), {*self.ordinary, CLOSURE})
        files = storage._files(self.guest)
        preserved = {name: files[name] for name in rows}
        entry = storage._entry(storage.read_json(self.ledger), self.guest)
        self.assertEqual(storage._evidence(self.guest, preservation.MANIFEST, preserved, entry["closure"]),
                         storage.binding(preservation.MANIFEST))
        preview = storage.preview_retirement(self.guest, preservation.MANIFEST, self.registry)
        self.assertEqual(preview["plan"]["remove"], [storage.binding(files[self.image])])
        self.assertIs(preview["registry_written"], False)
        self.assertIs(preview["deletes_images"], False)
        self.assertEqual(storage.binding(self.ledger), ledger)
        self.assert_originals_intact()

    def test_retained_entry_cannot_publish_complete_manifest(self):
        staged = self.stage()
        with self.assertRaises(REFUSALS):
            self.complete(staged, self.credentials(), self.ledger_before)
        self.assertEqual(storage.binding(self.ledger), self.ledger_before)
        self.assert_no_completion()

    def test_missing_credential_copy_refuses_before_any_completion_output(self):
        staged = self.stage()
        ledger = self.close_guest()
        incomplete = self.credentials({CREDENTIALS[0]: self.backups[CREDENTIALS[0]]})
        with self.assertRaises(REFUSALS):
            self.complete(staged, incomplete, ledger)
        self.assertEqual(storage.binding(self.ledger), ledger)
        self.assert_no_completion()

    def test_changed_credential_copy_refuses_before_any_completion_output(self):
        staged = self.stage()
        ledger = self.close_guest()
        credentials = self.credentials()
        path = Path(self.backups[CREDENTIALS[0]]["path"])
        path.write_bytes(b"unrelated synthetic credential")
        with self.assertRaises(REFUSALS):
            self.complete(staged, credentials, ledger)
        self.assertEqual(storage.binding(self.ledger), ledger)
        self.assert_no_completion()

    def test_changed_original_or_staged_record_refuses_before_any_completion_output(self):
        staged = self.stage()
        ledger = self.close_guest()
        credentials = self.credentials()
        for root in (self.guest, preservation.RECORDS):
            path = root / self.ordinary[0]
            original = path.read_bytes()
            path.write_bytes(original.upper())
            try:
                with self.subTest(root=root), self.assertRaises(REFUSALS):
                    self.complete(staged, credentials, ledger)
                self.assertEqual(storage.binding(self.ledger), ledger)
                self.assert_no_completion()
            finally:
                path.write_bytes(original)

    def test_stale_ledger_refuses_staging_without_copying(self):
        self.ledger.write_bytes(self.ledger.read_bytes() + b" ")
        changed = storage.binding(self.ledger)
        with self.assertRaises(REFUSALS):
            self.stage()
        self.assertFalse(preservation.RECORDS.exists())
        self.assertFalse(preservation.STAGED.exists())
        self.assertEqual(storage.binding(self.ledger), changed)

    def test_stage_refuses_an_output_ancestor_of_another_registered_guest(self):
        registry = storage.read_json(self.ledger)
        unrelated_root = preservation.RECORDS / "logs"
        registry["entries"].append(dict(self.retained_entry, root=str(unrelated_root), state="preparing"))
        self.ledger.write_bytes(storage.encoded(registry))
        self.ledger_before = storage.binding(self.ledger)
        self.report["evidence"]["ledger"] = self.ledger_before
        close.REVIEW.write_bytes(env.encoded(self.report))
        self.review_pin = storage.binding(close.REVIEW)
        planned = storage.read_json(close.PLAN)
        close.PLAN.write_bytes(env.encoded(dict(planned, ledger=self.ledger_before, review=self.review_pin)))
        self.plan = storage.binding(close.PLAN)

        with self.assertRaisesRegex(env.EnvironmentRefused, "^output_overlap$"):
            self.stage()
        self.assertFalse(unrelated_root.exists())
        self.assertFalse(preservation.RECORDS.exists())
        self.assertFalse(preservation.STAGED.exists())
        self.assertEqual(storage.binding(self.ledger), self.ledger_before)

    def test_stale_closed_ledger_refuses_completion_without_copying(self):
        staged = self.stage()
        ledger = self.close_guest()
        self.ledger.write_bytes(self.ledger.read_bytes() + b" ")
        changed = storage.binding(self.ledger)
        with self.assertRaises(REFUSALS):
            self.complete(staged, self.credentials(), ledger)
        self.assertEqual(storage.binding(self.ledger), changed)
        self.assert_no_completion()

    def test_original_credential_cannot_supply_its_own_external_backup(self):
        staged = self.stage()
        ledger = self.close_guest()
        records = dict(self.backups)
        records[CREDENTIALS[0]] = self.original[CREDENTIALS[0]]
        with self.assertRaises(REFUSALS):
            self.complete(staged, self.credentials(records), ledger)
        self.assertEqual(storage.binding(self.ledger), ledger)
        self.assert_no_completion()

    def test_manifest_validation_refusal_never_publishes_final_manifest(self):
        staged = self.stage()
        ledger = self.close_guest()
        credentials = self.credentials()

        def refuse(_root, manifest_path, _preserved, _closure):
            self.assertTrue(Path(manifest_path).is_file())
            self.assertNotEqual(Path(manifest_path), preservation.MANIFEST)
            self.assertFalse(preservation.MANIFEST.exists())
            raise storage.StorageRefused("synthetic_manifest_refusal")

        with (patch.object(storage, "_evidence", side_effect=refuse) as evidence,
              self.assertRaisesRegex(storage.StorageRefused, "^synthetic_manifest_refusal$")):
            self.complete(staged, credentials, ledger)
        evidence.assert_called_once()
        self.assertFalse(preservation.MANIFEST.exists())
        self.assertEqual(storage.binding(self.ledger), ledger)
