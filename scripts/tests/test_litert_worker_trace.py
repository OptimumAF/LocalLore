"""Pure bounded worker-wire tests; no device, model, SDK or build calls.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[2] / "benchmarks/litert_worker_trace.py"
SPEC = importlib.util.spec_from_file_location("worker_trace_under_test", PATH)
w = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(w)


def value():
    return {"version": 1, "counts": {event: 0 for event in w.EVENTS}, "saturated": []}


def timed():
    return {"version": 2, "counts": {event: 0 for event in w.EVENTS}, "saturated": [],
        "last_ms": {event: None for event in w.EVENTS}, "snapshot_ms": 0, "time_saturated": False,
        "creations_total": 0, "creations_saturated": False, "creations": []}


def creation(ordinal=1):
    return {"ordinal": ordinal, "role": "DIRECTOR", "entered_ms": 0,
        "returned_ms": None, "failed_ms": None, "failure": "NONE"}


def raw(candidate=None):
    return json.dumps(value() if candidate is None else candidate, separators=(",", ":")).encode("ascii")


def record(candidate=None):
    candidate = value() if candidate is None else candidate
    prefix = w.V1_PREFIX if candidate["version"] == 1 else w.PREFIX
    return prefix.encode() + raw(candidate) + b"\n" + w.STATUS.encode() + b"\n"


def failed(candidate=None):
    return b"INSTRUMENTATION_STATUS: test=fixedWorkerTest\n" + record(candidate) + b"FAILURES!!!\nTests run: 1,  Failures: 1\nINSTRUMENTATION_CODE: -1\n"


class WorkerTraceTests(unittest.TestCase):
    def refuses(self, payload):
        with self.assertRaises((AssertionError, ValueError, TypeError)):
            w.parse_worker_trace(payload)

    def test_import_is_inert_and_lazy(self):
        spec = importlib.util.spec_from_file_location("worker_trace_inert", PATH)
        fresh = importlib.util.module_from_spec(spec)
        with patch.object(importlib.util, "spec_from_file_location", side_effect=AssertionError("Unexpected controller load")), patch.object(Path, "read_bytes", side_effect=AssertionError("Unexpected file read")):
            spec.loader.exec_module(fresh)
        self.assertEqual(fresh._controller.cache_info().currsize, 0)

    def test_frozen_vocabulary_and_independent_counter_observations(self):
        expected = ("ADMISSION_ENTERED", "ADMISSION_RETURNED", "ENGINE_CREATE_ENTERED", "ENGINE_CREATE_RETURNED",
            "INITIALIZE_ADMISSION_ENTERED", "INITIALIZE_ADMISSION_RETURNED", "INITIALIZE_ENTERED", "INITIALIZE_RETURNED",
            "ROLE_ADMISSION_ENTERED", "ROLE_ADMISSION_RETURNED", "CONVERSATION_CREATE_ENTERED", "CONVERSATION_CREATE_RETURNED",
            "SEND_ADMISSION_ENTERED", "SEND_ADMISSION_RETURNED", "SEND_ENTERED", "SEND_RETURNED", "MESSAGE_ENTERED", "MESSAGE_RETURNED",
            "DONE_ENTERED", "DONE_RETURNED", "ERROR_ENTERED", "ERROR_RETURNED", "DRAIN_SETTLED", "CANCEL_ENTERED", "CANCEL_RETURNED",
            "CONVERSATION_CLOSE_ENTERED", "CONVERSATION_CLOSE_KNOWN", "ENGINE_CLOSE_ENTERED", "ENGINE_CLOSE_KNOWN", "UNCERTAIN")
        self.assertEqual(w.EVENTS, expected)
        candidate = value()
        candidate["counts"].update(ADMISSION_ENTERED=0, ADMISSION_RETURNED=9, ENGINE_CREATE_ENTERED=1,
            ENGINE_CREATE_RETURNED=0, CONVERSATION_CLOSE_KNOWN=12, ENGINE_CLOSE_KNOWN=21, UNCERTAIN=17)
        self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        with patch.object(w._controller().contract, "strict_json", wraps=w._controller().contract.strict_json) as decode:
            w.parse_worker_trace(raw(candidate))
            decode.assert_called_once()

    def test_saturation_exact_hits_and_ordered_overflow_subset(self):
        candidate = value()
        for event in w.EVENTS:
            candidate["counts"][event] = w.MAX_COUNT
        self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        candidate["saturated"] = list(w.EVENTS)
        self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        candidate["saturated"] = [w.EVENTS[0], w.EVENTS[-1]]
        self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        for bad in ([w.EVENTS[0], w.EVENTS[0]], [w.EVENTS[-1], w.EVENTS[0]], ["PRIVATE_CANARY"]):
            changed = copy.deepcopy(candidate); changed["saturated"] = bad
            self.refuses(raw(changed))
        candidate["counts"][w.EVENTS[0]] = w.MAX_COUNT - 1
        self.refuses(raw(candidate))

    def test_count_types_bounds_and_closed_top_level(self):
        for count in (-1, w.MAX_COUNT + 1, 2 ** 64, True, False, 0.0, "PRIVATE_CANARY", None, [], {}):
            candidate = value(); candidate["counts"][w.EVENTS[0]] = count
            self.refuses(raw(candidate))
        for key, field in (("version", True), ("version", 2), ("version", "1"), ("counts", []),
                           ("counts", None), ("saturated", None), ("saturated", {}), ("saturated", [True])):
            candidate = value(); candidate[key] = field
            self.refuses(raw(candidate))
        for missing in ("version", "counts", "saturated"):
            candidate = value(); del candidate[missing]
            self.refuses(raw(candidate))
        candidate = value(); del candidate["counts"][w.EVENTS[-1]]
        self.refuses(raw(candidate))
        candidate = value(); candidate["counts"]["PRIVATE_CANARY"] = 0
        self.refuses(raw(candidate))
        candidate = value(); candidate["path"] = "PRIVATE_CANARY/content://secret"
        self.refuses(raw(candidate))
        for candidate in ([], "PRIVATE_CANARY", None):
            self.refuses(json.dumps(candidate).encode())

    def test_duplicate_keys_nonfinite_and_raw_private_payloads_refuse(self):
        good = raw()
        variants = [good.replace(b'"version":1', b'"version":1,"version":1'),
            good.replace(b'"counts":{', b'"counts":{"ADMISSION_ENTERED":0,'),
            good.replace(b'"saturated":[]', b'"saturated":[],"saturated":[]')]
        for spelling in (b"NaN", b"Infinity", b"-Infinity"):
            variants.append(good.replace(b'"ADMISSION_ENTERED":0', b'"ADMISSION_ENTERED":' + spelling))
        variants += [b"PRIVATE_CANARY/path", good + b" PRIVATE_CANARY", good + b"{}", good + b"\n", good + b"\x00",
            good + b"\v", good + b"\f", good + b"\xff"]
        for payload in variants:
            self.refuses(payload)

    def test_combined_wire_size_and_ascii_limits(self):
        good = raw()
        room = w.MAX_BYTES - len(w.PREFIX.encode()) - len(good)
        self.assertGreater(room, 0)
        self.assertEqual(w.parse_worker_trace(good + b" " * room), value())
        self.refuses(good + b" " * (room + 1))
        for payload in (b"", "not bytes", bytearray(good)):
            self.refuses(payload)

    def test_exact_record_lf_crlf_and_no_trace_success(self):
        self.assertEqual(w.extract_worker_trace(failed()), value())
        self.assertEqual(w.extract_worker_trace(failed().replace(b"\n", b"\r\n")), value())
        self.assertIsNone(w.extract_worker_trace(b"OK (1 test)\nINSTRUMENTATION_CODE: -1\n"))
        self.assertIsNone(w.extract_worker_trace(b"FAILURES!!!\nTests run: 1, Failures: 1\n"))
        for summary in (b"OK (1 test)\n", b"OK (2 tests)\n"):
            with self.assertRaises(AssertionError): w.extract_worker_trace(record() + summary)

    def test_record_count_adjacency_key_substrings_and_cross_domain_codes(self):
        malformed = [record() + record(), record() + w.STATUS.encode() + b"\n", w.STATUS.encode() + b"\n",
            w.PREFIX.encode() + raw() + b"\n", record().replace(b"\nINSTRUMENTATION_STATUS_CODE", b"\n\nINSTRUMENTATION_STATUS_CODE"),
            b" " + record(), record() + b"locallore_receipt_worker_v1\n", record().replace(w.STATUS.encode(), b"INSTRUMENTATION_STATUS_CODE: 01337"),
            record() + b"INSTRUMENTATION_STATUS_CODE: 1337 \n", record() + b" INSTRUMENTATION_STATUS_CODE: 1337\n",
            record() + b"INSTRUMENTATION_STATUS_CODE: 1337.0\n", b"INSTRUMENTATION_STATUS: locallore_receipt_failure_v1={}\n" + w.STATUS.encode() + b"\n",
            b"INSTRUMENTATION_STATUS: other_locallore_receipt_worker_v1={}\n", record() + b"INSTRUMENTATION_STATUS: locallore_receipt_failure_v1={}\n" + w.STATUS.encode() + b"\n"]
        for payload in malformed:
            with self.subTest(payload=payload[:100]), self.assertRaises(AssertionError):
                w.extract_worker_trace(payload)
        for payload in (failed().replace(b"\n", b"\r\r\n"), failed().replace(b"\n", b"\v"),
                        failed().replace(b"\n", b"\f"), failed() + b" " * 131072):
            with self.assertRaises(AssertionError): w.extract_worker_trace(payload)

    def test_play_persists_only_valid_trace_and_keeps_passive_values(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory))
            candidate = value(); candidate["counts"]["UNCERTAIN"] = 100
            self.assertEqual(w.observe_worker_trace(owner, failed(candidate), "PLAY"), candidate)
            path = owner.directory / "play-worker-trace-v1.json"
            self.assertEqual(json.loads(path.read_bytes()), candidate)
            with self.assertRaises(FileExistsError): w.observe_worker_trace(owner, failed(candidate), "PLAY")
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory))
            self.assertIsNone(w.observe_worker_trace(owner, b"OK (1 test)\n", "PLAY"))
            with self.assertRaises(AssertionError): w.observe_worker_trace(owner, record() + b"OK (1 test)\n", "PLAY")
            self.assertEqual(list(owner.directory.iterdir()), [])

    def test_other_phases_forbid_worker_key_but_do_not_consume_setup_channel(self):
        setup = b"INSTRUMENTATION_STATUS: locallore_receipt_failure_v1={}\nINSTRUMENTATION_STATUS_CODE: 1337\n"
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory))
            for phase in ("SOURCE_PREFLIGHT", "IMPORT", "REOPEN"):
                self.assertIsNone(w.observe_worker_trace(owner, setup, phase))
                with self.assertRaises(AssertionError): w.observe_worker_trace(owner, failed(), phase)
                with self.assertRaises(AssertionError): w.observe_worker_trace(owner, w.STATUS_KEY.encode() + b"_private\n", phase)
            with self.assertRaises(AssertionError): w.observe_worker_trace(owner, setup, "ARBITRARY")
            self.assertEqual(list(owner.directory.iterdir()), [])

    def test_private_canary_is_refused_before_any_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory))
            candidate = value()
            candidate["counts"]["INITIALIZE_ENTERED"] = "PRIVATE_CANARY/content://model/secret"
            with self.assertRaises(AssertionError) as failure:
                w.observe_worker_trace(owner, failed(candidate), "PLAY")
            self.assertNotIn("PRIVATE_CANARY", str(failure.exception))
            self.assertEqual(list(owner.directory.iterdir()), [])

    def test_persistence_failure_propagates_without_another_action(self):
        owner = SimpleNamespace(directory=Path("unused-private-evidence"))
        original = OSError("PRIVATE_CANARY evidence failure")
        with patch.object(w._controller(), "write_json", side_effect=original) as write:
            with self.assertRaises(OSError) as failure:
                w.observe_worker_trace(owner, failed(), "PLAY")
            self.assertIs(failure.exception, original)
            write.assert_called_once_with(owner.directory / "play-worker-trace-v1.json", value())

    def test_v2_closed_constants_empty_and_independent_scopes(self):
        self.assertEqual(w.V1_STATUS_KEY, "locallore_receipt_worker_v1")
        self.assertEqual(w.STATUS_KEY, "locallore_receipt_worker_v2")
        self.assertEqual(w.MAX_MS, 180_000)
        self.assertEqual(w.MAX_CREATIONS, 3)
        self.assertEqual(w.parse_worker_trace(raw(timed())), timed())
        candidate = timed(); candidate.update(snapshot_ms=100, creations_total=9)
        candidate["counts"]["SEND_RETURNED"] = 5
        candidate["last_ms"]["SEND_RETURNED"] = 0
        candidate["creations"] = [creation(i) for i in range(1, 4)]
        candidate["creations"][0].update(entered_ms=80, returned_ms=99)
        candidate["creations"][1].update(role="NARRATOR", entered_ms=1, failed_ms=2, failure="OTHER")
        # Base counters, retained scopes and different scopes' times do not
        # establish cross-counter or inter-scope lifecycle consistency.
        self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)

    def test_v2_exact_top_level_and_versions(self):
        for key in timed():
            candidate = timed(); del candidate[key]
            self.refuses(raw(candidate))
        candidate = timed(); candidate["path"] = "PRIVATE_CANARY/content://model"
        self.refuses(raw(candidate))
        for version in (True, False, 0, 3, "2", 2.0, None):
            candidate = timed(); candidate["version"] = version
            self.refuses(raw(candidate))
        candidate = timed(); candidate["version"] = 1
        self.refuses(raw(candidate))
        for key in ("counts", "saturated"):
            for invalid in (None, True, 1, "PRIVATE_CANARY"):
                candidate = timed(); candidate[key] = invalid
                self.refuses(raw(candidate))

    def test_v2_last_time_matches_only_its_counter_and_snapshot(self):
        candidate = timed(); candidate["snapshot_ms"] = 7
        for last in (0, 7, True, "PRIVATE_CANARY"):
            changed = copy.deepcopy(candidate); changed["last_ms"][w.EVENTS[0]] = last
            self.refuses(raw(changed))
        candidate["counts"][w.EVENTS[0]] = 1
        for last in (0, 7):
            changed = copy.deepcopy(candidate); changed["last_ms"][w.EVENTS[0]] = last
            self.assertEqual(w.parse_worker_trace(raw(changed)), changed)
        for last in (None, -1, 8, True, 0.0, "PRIVATE_CANARY", [], {}):
            changed = copy.deepcopy(candidate); changed["last_ms"][w.EVENTS[0]] = last
            self.refuses(raw(changed))
        for last in (None, [], "PRIVATE_CANARY"):
            changed = timed(); changed["last_ms"] = last
            self.refuses(raw(changed))
        changed = timed(); del changed["last_ms"][w.EVENTS[-1]]
        self.refuses(raw(changed))
        changed = timed(); changed["last_ms"]["PRIVATE_CANARY"] = None
        self.refuses(raw(changed))

    def test_v2_snapshot_bounds_and_overflow_only_time_flag(self):
        for snapshot in (0, w.MAX_MS):
            candidate = timed(); candidate["snapshot_ms"] = snapshot
            self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        candidate["time_saturated"] = True
        self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        for snapshot in (-1, w.MAX_MS + 1, 2 ** 64, True, False, 0.0, None, "PRIVATE_CANARY"):
            candidate = timed(); candidate["snapshot_ms"] = snapshot
            self.refuses(raw(candidate))
        candidate = timed(); candidate["time_saturated"] = True
        self.refuses(raw(candidate))
        for flag in (0, 1, None, "PRIVATE_CANARY", []):
            candidate = timed(); candidate["time_saturated"] = flag
            self.refuses(raw(candidate))

    def test_v2_creation_total_retention_and_overflow_only_flag(self):
        for total in (0, 1, 2, 3, 4, w.MAX_COUNT):
            candidate = timed(); candidate["creations_total"] = total
            candidate["creations"] = [creation(i) for i in range(1, min(total, 3) + 1)]
            self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        candidate["creations_saturated"] = True
        self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        for total in (-1, w.MAX_COUNT + 1, 2 ** 64, True, False, 1.0, None, "PRIVATE_CANARY"):
            candidate = timed(); candidate["creations_total"] = total
            self.refuses(raw(candidate))
        for total, retained in ((0, 1), (1, 0), (2, 1), (3, 4), (4, 2)):
            candidate = timed(); candidate.update(creations_total=total, creations=[creation(i) for i in range(1, retained + 1)])
            self.refuses(raw(candidate))
        for field in (None, {}, "PRIVATE_CANARY"):
            candidate = timed(); candidate["creations"] = field
            self.refuses(raw(candidate))
        candidate = timed(); candidate["creations_saturated"] = True
        self.refuses(raw(candidate))
        for flag in (0, 1, None, "PRIVATE_CANARY", []):
            candidate = timed(); candidate["creations_saturated"] = flag
            self.refuses(raw(candidate))

    def test_v2_creation_scope_closed_identity_and_ends(self):
        base = timed(); base.update(snapshot_ms=10, creations_total=1, creations=[creation()])
        for end, failure in (("returned_ms", "NONE"), ("failed_ms", "CANCELLED"), ("failed_ms", "OTHER")):
            for terminal in (0, 10):
                candidate = copy.deepcopy(base); candidate["creations"][0].update({end: terminal, "failure": failure})
                self.assertEqual(w.parse_worker_trace(raw(candidate)), candidate)
        for key in creation():
            candidate = copy.deepcopy(base); del candidate["creations"][0][key]
            self.refuses(raw(candidate))
        for key, invalid in (("ordinal", True), ("ordinal", 0), ("ordinal", 2), ("ordinal", "1"),
                ("role", "REPAIR"), ("role", "PRIVATE_CANARY"), ("role", None), ("role", 1),
                ("entered_ms", -1), ("entered_ms", 11), ("entered_ms", True), ("entered_ms", 0.0),
                ("returned_ms", -1), ("returned_ms", 11), ("returned_ms", True), ("returned_ms", 0.0),
                ("failed_ms", -1), ("failed_ms", 11), ("failed_ms", True), ("failed_ms", 0.0),
                ("failure", "CANCELLED"), ("failure", None), ("failure", 0), ("failure", "PRIVATE_CANARY")):
            candidate = copy.deepcopy(base); candidate["creations"][0][key] = invalid
            self.refuses(raw(candidate))
        for changes in ({"entered_ms": 5, "returned_ms": 4}, {"entered_ms": 5, "failed_ms": 4, "failure": "OTHER"},
                {"returned_ms": 5, "failed_ms": 5, "failure": "OTHER"}, {"failed_ms": 5},
                {"failed_ms": 5, "failure": "NONE"}, {"raw_error": "PRIVATE_CANARY"}):
            candidate = copy.deepcopy(base); candidate["creations"][0].update(changes)
            self.refuses(raw(candidate))
        for invalid in (None, [], "PRIVATE_CANARY"):
            candidate = copy.deepcopy(base); candidate["creations"][0] = invalid
            self.refuses(raw(candidate))
        candidate = timed(); candidate.update(creations_total=3, creations=[creation(1), creation(1), creation(3)])
        self.refuses(raw(candidate))

    def test_v2_duplicate_nonfinite_and_private_raw_data(self):
        good = raw(timed())
        payloads = [good.replace(b'"snapshot_ms":0', b'"snapshot_ms":0,"snapshot_ms":0'),
            good.replace(b'"last_ms":{', b'"last_ms":{"ADMISSION_ENTERED":null,'),
            good.replace(b'"creations":[]', b'"creations":[],"creations":[]'), good + b"\n", good + b"\xff"]
        for spelling in (b"NaN", b"Infinity", b"-Infinity"):
            payloads.append(good.replace(b'"snapshot_ms":0', b'"snapshot_ms":' + spelling))
        for payload in payloads:
            self.refuses(payload)
        candidate = timed(); candidate.update(creations_total=1, creations=[creation()])
        candidate["creations"][0]["failure"] = "PRIVATE_CANARY/content://model"
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory))
            with self.assertRaises(AssertionError) as failure: w.observe_worker_trace(owner, failed(candidate), "PLAY")
            self.assertNotIn("PRIVATE_CANARY", str(failure.exception))
            self.assertEqual(list(owner.directory.iterdir()), [])

    def test_v2_maximum_cross_language_wire_fits_and_cap_is_exact(self):
        candidate = timed()
        candidate.update(counts={event: w.MAX_COUNT for event in w.EVENTS}, saturated=list(w.EVENTS),
            last_ms={event: w.MAX_MS for event in w.EVENTS}, snapshot_ms=w.MAX_MS, time_saturated=True,
            creations_total=w.MAX_COUNT, creations_saturated=True,
            creations=[dict(ordinal=i, role="NARRATOR", entered_ms=w.MAX_MS, returned_ms=None,
                failed_ms=w.MAX_MS, failure="CANCELLED") for i in range(1, 4)])
        payload = raw(candidate)
        self.assertEqual(len(payload), 2908)
        self.assertEqual(len(w.PREFIX.encode()) + len(payload), 2960)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), "bd2f1b19bc833f90227b87531da9f35037a948643ef3072c151b51d3baef2b31")
        self.assertLessEqual(len(w.PREFIX.encode()) + len(payload), w.MAX_BYTES)
        self.assertEqual(w.parse_worker_trace(payload), candidate)
        room = w.MAX_BYTES - len(w.PREFIX.encode()) - len(payload)
        self.assertEqual(w.parse_worker_trace(payload + b" " * room), candidate)
        self.refuses(payload + b" " * (room + 1))

    def test_v1_v2_exact_channel_version_and_mixed_refusal(self):
        for candidate in (value(), timed()):
            self.assertEqual(w.extract_worker_trace(failed(candidate)), candidate)
            self.assertEqual(w.extract_worker_trace(failed(candidate).replace(b"\n", b"\r\n")), candidate)
        invalid = [record(value()) + record(timed()), record(timed()) + record(timed()),
            record(value()).replace(w.V1_PREFIX.encode(), w.PREFIX.encode()),
            record(timed()).replace(w.PREFIX.encode(), w.V1_PREFIX.encode()), record(timed()) + b"OK (1 test)\n",
            b"other_" + record(timed()), record(timed()) + w.V1_STATUS_KEY.encode(), record(value()) + w.STATUS_KEY.encode(),
            record(timed()) + b"INSTRUMENTATION_STATUS: locallore_receipt_failure_v1={}\n",
            b"INSTRUMENTATION_STATUS: locallore_receipt_failure_v1={}\n",
            record(timed()).replace(w.STATUS.encode(), b"INSTRUMENTATION_STATUS_CODE: +1337"),
            record(timed()) + b"INSTRUMENTATION_STATUS_CODE: 1337\n",
            record(timed()).replace(b"\n", b"\r\r\n"), record(timed()).replace(b"\n", b"\v"),
            record(timed()).replace(b"\n", b"\f")]
        for payload in invalid:
            with self.subTest(payload=payload[:80]), self.assertRaises(AssertionError): w.extract_worker_trace(payload)
        self.assertIsNone(w.extract_worker_trace(b"INSTRUMENTATION_STATUS: test=ordinaryFailure\n"))

    def test_v2_persistence_and_nonplay_both_key_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory))
            self.assertEqual(w.observe_worker_trace(owner, failed(timed()), "PLAY"), timed())
            self.assertEqual(json.loads((owner.directory / "play-worker-trace-v2.json").read_bytes()), timed())
            self.assertFalse((owner.directory / "play-worker-trace-v1.json").exists())
            with self.assertRaises(FileExistsError): w.observe_worker_trace(owner, failed(timed()), "PLAY")
            for phase in ("SOURCE_PREFLIGHT", "IMPORT", "REOPEN"):
                for candidate in (value(), timed()):
                    with self.assertRaises(AssertionError): w.observe_worker_trace(owner, failed(candidate), phase)
                for key in (w.V1_STATUS_KEY, w.STATUS_KEY):
                    with self.assertRaises(AssertionError): w.observe_worker_trace(owner, (key + "_private").encode(), phase)
        original = OSError("PRIVATE_CANARY evidence failure")
        owner = SimpleNamespace(directory=Path("unused-private-evidence"))
        with patch.object(w._controller(), "write_json", side_effect=original) as write:
            with self.assertRaises(OSError) as failure: w.observe_worker_trace(owner, failed(timed()), "PLAY")
            self.assertIs(failure.exception, original)
            write.assert_called_once_with(owner.directory / "play-worker-trace-v2.json", timed())


if __name__ == "__main__":
    unittest.main()
