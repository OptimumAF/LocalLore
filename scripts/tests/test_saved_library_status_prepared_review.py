
"""Synthetic refusal tests for the SDK23 prepared-guest review.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import ExitStack
import hashlib
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import warnings
from zipfile import ZipFile

from benchmarks import owned_saved_library_status as contract
from benchmarks import receipt_avd_storage as storage
from benchmarks import saved_library_status_handoff as handoff
from benchmarks import saved_library_status_prepared_review as review
from scripts.tests.test_owned_target_contract import pin
from scripts.tests.test_saved_library_status_handoff import REFUSED


def worker_result():
    executable = r"C:\Synthetic\Python\python.exe"
    row = dict.fromkeys(contract.WORKER_KEYS)
    row.update(
        version=1,
        protocol=contract.PROTOCOL,
        admission=pin(handoff.ADMISSION),
        request=pin(handoff.OWNED_ROOT / "request-v1.json"),
        worker=dict(pid=701, creation_filetime=800, executable=executable),
        server=dict(pid=702, creation_filetime=801, executable=r"C:\Synthetic\adb.exe"),
        guest_ancestry=[],
        server_capture=pin(handoff.OWNED_ROOT / "server-capture-v1.json"),
        server_returncode=1,
        reason="not_authorized",
        stop_requested=False,
        elapsed_ms=200,
        cleanup={key: not key.startswith("guest_") for key in contract.CLEANUP_KEYS},
    )
    return row


def supervisor():
    return dict(status="child_exited", worker_returncode=1, cleanup_complete=True,
                output_capture_complete=True, elapsed_ms=200, stdout_bytes=0, stderr_bytes=0)


PREPARE_DIGEST = "1" * 64


def ledger_entry():
    return dict(root=str(handoff.GUEST), proposal_sha256=PREPARE_DIGEST, state="prepared",
                reserved_bytes=storage.RESERVATION_BYTES, closure=None, recovery=None,
                retirement=None, retirement_receipt=None)


class ArchiveRecords:
    """Serve real ZIP bytes and digest-pinned original records entirely in memory."""

    def __init__(self, change_entries=None):
        self.terminal = "launch/launch-terminal-v1.json"
        self.verification = "launch/terminal-verification-v1.json"
        self.raw = {
            self.terminal: b'{"returncode":1}\n',
            self.verification: b'{"passed":false}\n',
            "launch/operation-stdout-v1.bin": b"",
        }
        self.pins = {
            name: self.bind(review.RECORD_ROOTS["launch"] / name.split("/", 1)[1], data)
            for name, data in self.raw.items()
        }
        entries = list(self.raw.items())
        if change_entries:
            change_entries(entries)
        stream = BytesIO()
        with warnings.catch_warnings(), ZipFile(stream, "w") as archive:
            warnings.filterwarnings("ignore", message="Duplicate name:", category=UserWarning)
            for name, data in entries:
                archive.writestr(name, data)
        zip_bytes = stream.getvalue()
        archive_pin = self.bind(review.ARCHIVE, zip_bytes)
        self.files = {self.pins[name]["path"]: data for name, data in self.raw.items()}
        self.files[archive_pin["path"]] = zip_bytes
        total = sum(len(data) for data in self.raw.values())
        self.manifest = dict(archive=archive_pin, original_and_archive_bytes=total + len(zip_bytes),
                             original_bytes=total, records=len(self.raw),
                             records_allowance=256 * 1024**2, records_by_name=self.pins,
                             terminal=self.pins[self.terminal],
                             verification=self.pins[self.verification])

    @staticmethod
    def bind(path, data):
        return pin(path, size=len(data), sha=hashlib.sha256(data).hexdigest())

    def bound(self, requested, *, cap):
        raw = self.files.get(requested["path"])
        if raw is None or len(raw) > cap or self.bind(requested["path"], raw) != requested:
            raise handoff.env.EnvironmentRefused("binding")
        return raw

    def inspect(self):
        manifest_pin = self.bind(review.MANIFEST, handoff.env.encoded(self.manifest))

        def read(requested, path, *, cap=handoff.RECORD_CAP):
            if requested != manifest_pin or path != review.MANIFEST or requested["bytes"] > cap:
                raise handoff.env.EnvironmentRefused("binding")
            return self.manifest

        with patch.object(handoff, "at", side_effect=read), \
                patch.object(handoff.files, "_bound", side_effect=self.bound):
            return review._archive(manifest_pin)


class SavedLibraryStatusPreparedReviewTests(unittest.TestCase):
    def test_exact_preboot_receipt_requires_known_private_server_cleanup(self):
        review._check_preboot(worker_result())

    def test_preboot_worker_refuses_a_different_terminal_reason_or_invalid_binding(self):
        for key, value in (
            ("reason", "stop_requested"), ("version", True), ("protocol", "foreign-profile"),
            ("server", None), ("server_capture", None), ("server_returncode", True),
            ("stop_requested", 0), ("guest_ancestry", None),
        ):
            with self.subTest(key=key, value=value):
                with self.assertRaises(REFUSED):
                    review._check_preboot(dict(worker_result(), **{key: value}))

    def test_preboot_worker_refuses_each_guest_lifecycle_indicator(self):
        for key in (
            "launcher", "guest", "guest_capture", "guest_job", "guest_inputs",
            "guest_preflight", "guest_returncode", "guest_terminal", "boot_claim",
            "readiness", "ready", "running",
        ):
            with self.subTest(key=key):
                with self.assertRaises(REFUSED):
                    review._check_preboot(dict(worker_result(), **{key: False}))

    def test_preboot_cleanup_is_an_exact_set_of_boolean_results(self):
        for key in sorted(contract.CLEANUP_KEYS):
            with self.subTest(key=key):
                row = worker_result()
                row["cleanup"][key] = not row["cleanup"][key]
                with self.assertRaises(REFUSED):
                    review._check_preboot(row)
        for mutate in (
            lambda cleanup: cleanup.pop("client_sockets_closed"),
            lambda cleanup: cleanup.update(unreviewed=True),
            lambda cleanup: cleanup.update(client_sockets_closed=1),
            lambda cleanup: cleanup.update(guest_wait_completed=0),
        ):
            row = worker_result()
            mutate(row["cleanup"])
            with self.assertRaises(REFUSED):
                review._check_preboot(row)

    def test_supervisor_requires_complete_cleanup_and_strict_failure_exit(self):
        review._check_supervisor(supervisor())
        for key, value in (
            ("status", "timeout"), ("worker_returncode", 0), ("worker_returncode", True),
            ("cleanup_complete", False), ("output_capture_complete", 1),
            ("elapsed_ms", -1), ("stdout_bytes", False), ("stderr_bytes", -1),
        ):
            with self.subTest(key=key, value=value):
                with self.assertRaises(REFUSED):
                    review._check_supervisor(dict(supervisor(), **{key: value}))

    def test_supervisor_refuses_missing_or_unexpected_record_fields(self):
        row = supervisor()
        row.pop("stderr_bytes")
        with self.assertRaises(REFUSED):
            review._check_supervisor(row)
        with self.assertRaises(REFUSED):
            review._check_supervisor(dict(supervisor(), additional=True))

    def test_exact_prepared_charge_is_the_only_eligible_ledger_state(self):
        review._check_ledger_entry(ledger_entry(), PREPARE_DIGEST)
        for key, value in (
            ("state", "retained"), ("state", "closed"), ("reserved_bytes", storage.RESERVATION_BYTES - 1),
            ("reserved_bytes", float(storage.RESERVATION_BYTES)), ("proposal_sha256", "2" * 64),
            ("root", str(Path(handoff.GUEST).with_name("foreign-guest"))),
            ("closure", {}), ("recovery", {}), ("retirement", {}), ("retirement_receipt", {}),
        ):
            with self.subTest(key=key, value=value):
                with self.assertRaises(REFUSED):
                    review._check_ledger_entry(dict(ledger_entry(), **{key: value}), PREPARE_DIGEST)

    def test_archive_matches_manifest_and_all_originals_including_an_empty_capture(self):
        records = ArchiveRecords()
        self.assertEqual(records.inspect(), (records.pins, records.raw))

    def test_archive_refuses_missing_extra_duplicate_or_changed_members(self):
        for mutate in (
            lambda entries: entries.pop(),
            lambda entries: entries.append(("launch/extra.json", b"{}")),
            lambda entries: entries.append(entries[0]),
            lambda entries: entries.__setitem__(0, (entries[0][0], b'{"returncode":2}\n')),
        ):
            with self.subTest(mutate=mutate):
                with self.assertRaises(REFUSED):
                    ArchiveRecords(mutate).inspect()

    def test_archive_refuses_drift_in_an_original_even_when_the_zip_still_matches(self):
        records = ArchiveRecords()
        original = records.pins[records.terminal]["path"]
        records.files[original] = b'{"returncode":2}\n'
        with self.assertRaises(REFUSED):
            records.inspect()

    def test_archive_refuses_a_foreign_original_binding_for_identical_bytes(self):
        records = ArchiveRecords()
        alternate = review.RECORD_ROOTS["launch"] / "alternate-terminal.json"
        raw = records.raw[records.terminal]
        alternate_pin = records.bind(alternate, raw)
        records.pins[records.terminal] = alternate_pin
        records.manifest["terminal"] = alternate_pin
        records.files[alternate_pin["path"]] = raw
        with self.assertRaises(REFUSED):
            records.inspect()

    def test_archive_refuses_traversal_even_if_the_replacement_bytes_are_pinned(self):
        records = ArchiveRecords()
        name = "launch/../outside.json"
        records.pins[name] = records.pins.pop("launch/operation-stdout-v1.bin")
        with self.assertRaises(REFUSED):
            records.inspect()

    def test_failure_refuses_a_null_upstream_pin_even_if_the_receipt_is_archived(self):
        authority = pin(handoff.AUTHORITY)
        rows = {
            "launch/launch-claim-v1.json": dict(source=review.EXECUTED_HEAD, no_retry=True, authority=authority),
            "launch/launch-terminal-v1.json": dict(no_retry=True, returncode=1, timed_out=False),
            "attempt/operation-result-v1.json": dict(scope=handoff.OPERATION_SCOPE, passed=False,
                                                     feature_acceptance=False, reason="owner",
                                                     authority=authority, supervisor=None),
            "attempt/operation-supervisor-v1.json": supervisor(),
        }
        raw = {name: handoff.env.encoded(row) for name, row in rows.items()}
        pins = {name: ArchiveRecords.bind(review.RECORD_ROOTS[label] / tail, data)
                for name, data in raw.items() for label, tail in [name.split("/", 1)]}
        with patch.object(review, "_check_supervisor") as check, \
                patch.object(handoff, "approved_plan") as read_approval:
            with self.assertRaises(REFUSED):
                review._failure(pins, raw)
        check.assert_not_called()
        read_approval.assert_not_called()

    def test_archive_manifest_rejects_non_integer_counts_and_inconsistent_totals(self):
        for change in (
            {"records": True}, {"records": 4}, {"original_bytes": -1},
            {"original_and_archive_bytes": 0}, {"records_allowance": 1},
        ):
            with self.subTest(change=change):
                records = ArchiveRecords()
                records.manifest.update(change)
                with self.assertRaises(REFUSED):
                    records.inspect()




class ReviewSnapshot:
    """Keep ledger, original files and guest observations synthetic."""

    def __init__(self):
        self.manifest = pin(review.MANIFEST)
        self.ledger = pin(handoff.LEDGER)
        self.entry = ledger_entry()
        self.receipt = pin(handoff.OWNED_ROOT / "guest-inputs-v1.json")
        self.proposal = dict(prepare_proposal={"sha256": PREPARE_DIGEST},
                             paths={"content": str(handoff.GUEST / "content")})
        self.plan = {"source_root": str(handoff.ROOT)}
        self.archive_pin = pin(review.ARCHIVE)
        self.record = pin(handoff.ATTEMPT)
        self.config = pin(handoff.GUEST / "content" / "config.ini")
        self.present = set()
        self.archive = Mock(return_value=({"attempt/claim-v1.json": self.record}, {}))
        self.failure = Mock(return_value=(self.receipt, self.proposal, self.plan))
        self.verify_prepared = Mock(return_value={"immutable": [self.config]})
        self.check_binding = Mock()
        self.mutate = Mock(side_effect=AssertionError("review attempted to mutate state"))

    def inspect(self, ledger=None):
        with ExitStack() as stack:
            for module, name, value in (
                (handoff, "ledger_entry", Mock(return_value=(self.ledger, self.entry))),
                (handoff, "at", Mock(return_value={"archive": self.archive_pin})),
                (handoff.files, "_bound", self.mutate),
                (review, "_archive", self.archive),
                (review, "_failure", self.failure),
                (review, "_verify_original_preparation", self.verify_prepared),
                (handoff.env, "verify_prepared", self.mutate),
                (handoff.env, "check_binding", self.check_binding),
                (handoff.os.path, "lexists", lambda path: path in self.present),
                (handoff.env, "create_json", self.mutate),
                (storage, "record_state", self.mutate),
                (storage, "reserve_prepare", self.mutate),
            ):
                stack.enter_context(patch.object(module, name, value))
            return review.inspect(self.manifest, self.ledger if ledger is None else ledger)


class SavedLibraryStatusPreparedReviewIntegrationTests(unittest.TestCase):
    def test_inspect_verifies_initial_guest_and_rereads_input_bindings(self):
        snapshot = ReviewSnapshot()
        report = snapshot.inspect()
        self.assertEqual(report["status"], "prepared_candidate")
        self.assertIs(report["execution_authorized"], False)
        self.assertEqual(report["reserved_bytes"], storage.RESERVATION_BYTES)
        snapshot.verify_prepared.assert_called_once_with(snapshot.proposal, snapshot.plan)
        for binding in (snapshot.manifest, snapshot.archive_pin, snapshot.ledger, snapshot.record, snapshot.config):
            snapshot.check_binding.assert_any_call(binding)
        snapshot.mutate.assert_not_called()

    def test_inspect_refuses_boot_claim_before_opening_archive(self):
        snapshot = ReviewSnapshot()
        snapshot.present.add(handoff.GUEST / contract.BOOT_CLAIM_FILE)
        with self.assertRaises(REFUSED):
            snapshot.inspect()
        snapshot.archive.assert_not_called()
        snapshot.verify_prepared.assert_not_called()
        snapshot.mutate.assert_not_called()

    def test_inspect_refuses_ledger_lock_before_or_during_replay(self):
        lock = handoff.LEDGER.with_name("admission.lock")
        locked_before = ReviewSnapshot()
        locked_before.present.add(lock)
        with self.assertRaises(REFUSED):
            locked_before.inspect()
        locked_before.archive.assert_not_called()

        locked_during = ReviewSnapshot()

        def acquire_lock(*args):
            locked_during.present.add(lock)
            return locked_during.verify_prepared.return_value

        locked_during.verify_prepared.side_effect = acquire_lock
        with self.assertRaises(REFUSED):
            locked_during.inspect()
        locked_during.verify_prepared.assert_called_once()
        locked_during.mutate.assert_not_called()

    def test_inspect_refuses_stale_ledger_before_replaying_failed_receipt(self):
        snapshot = ReviewSnapshot()
        stale = dict(snapshot.ledger, sha256="0" * 64)
        with self.assertRaises(REFUSED):
            snapshot.inspect(stale)
        snapshot.archive.assert_not_called()
        snapshot.failure.assert_not_called()
        snapshot.mutate.assert_not_called()

    def test_inspect_refuses_guest_started_during_initial_guest_verification(self):
        snapshot = ReviewSnapshot()
        def start_guest(*args):
            snapshot.present.add(handoff.OWNED_ROOT / "running-v1.json")
            return snapshot.verify_prepared.return_value

        snapshot.verify_prepared.side_effect = start_guest
        with self.assertRaises(REFUSED):
            snapshot.inspect()
        snapshot.verify_prepared.assert_called_once()
        snapshot.mutate.assert_not_called()

    def test_inspect_refuses_binding_drift_after_initial_guest_verification(self):
        snapshot = ReviewSnapshot()

        def check(binding):
            if binding == snapshot.ledger:
                raise handoff.env.EnvironmentRefused("binding")

        snapshot.check_binding.side_effect = check
        with self.assertRaises(REFUSED):
            snapshot.inspect()
        snapshot.verify_prepared.assert_called_once()
        snapshot.check_binding.assert_any_call(snapshot.ledger)
        snapshot.mutate.assert_not_called()



class OriginalPreparationReplay:
    """Intercept the pinned Python invocation before it reaches the host."""

    def __init__(self):
        self.source_name = Path("benchmarks/receipt_avd_environment.py")
        self.source = pin(review.EXECUTED_ROOT / self.source_name)
        self.python = {"executable": {"path": r"C:\Synthetic\Python\python.exe"}}
        self.plan = dict(source_root=str(review.EXECUTED_ROOT), sources=[self.source], python=self.python)
        self.proposal = {"prepared": pin(handoff.GUEST / "prepared-v1.json")}
        self.prepared = {"immutable": []}
        self.completed = SimpleNamespace(returncode=0, stderr=b"", stdout=handoff.env.encoded(self.prepared))
        self.run = Mock(return_value=self.completed)
        self.check = Mock()

    def verify(self):
        with (
            patch.object(review.python_pins, "_python_bindings", return_value=self.python),
            patch.object(contract, "source_bindings", return_value=[pin(handoff.ROOT / self.source_name)]),
            patch.object(handoff.env, "check_binding", self.check),
            patch.object(handoff, "at", return_value=self.prepared) as read,
            patch.object(review.subprocess, "run", self.run),
        ):
            result = review._verify_original_preparation(self.proposal, self.plan)
        read.assert_called_once_with(self.proposal["prepared"], handoff.GUEST / "prepared-v1.json")
        return result


class OriginalPreparationReplayTests(unittest.TestCase):
    def test_replay_uses_pinned_python_and_the_original_checkout(self):
        fixture = OriginalPreparationReplay()
        self.assertEqual(fixture.verify(), fixture.prepared)
        self.assertEqual(fixture.run.call_args.args[0][:5],
                         [fixture.python["executable"]["path"], "-I", "-S", "-B", "-c"])
        self.assertEqual(fixture.run.call_args.kwargs["cwd"], review.EXECUTED_ROOT)
        self.assertEqual(fixture.run.call_args.kwargs["input"], handoff.env.encoded(fixture.proposal))
        self.assertEqual(fixture.run.call_args.kwargs["timeout"], 120)
        self.assertEqual(fixture.check.call_count, 2)
        fixture.check.assert_called_with(fixture.source)

    def test_replay_refuses_wrong_checkout_or_python_before_spawning(self):
        for change in (
            dict(source_root=str(review.EXECUTED_ROOT.with_name("foreign-source"))),
            dict(python={"executable": {"path": r"C:\Synthetic\foreign-python.exe"}}),
            dict(sources=[]),
        ):
            with self.subTest(change=change):
                fixture = OriginalPreparationReplay()
                fixture.plan.update(change)
                with self.assertRaises(REFUSED):
                    fixture.verify()
                fixture.run.assert_not_called()

    def test_replay_refuses_child_failure_or_unbound_prepared_output(self):
        for field, value in (
            ("returncode", 1), ("stderr", b"diagnostic output"),
            ("stdout", handoff.env.encoded({"immutable": ["changed"]})),
        ):
            with self.subTest(field=field):
                fixture = OriginalPreparationReplay()
                setattr(fixture.completed, field, value)
                with self.assertRaises(REFUSED):
                    fixture.verify()
                fixture.run.assert_called_once()
