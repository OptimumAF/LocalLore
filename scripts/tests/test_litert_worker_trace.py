"""Pure bounded worker-wire tests; no device, model, SDK or build calls.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
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


def raw(candidate=None):
    return json.dumps(value() if candidate is None else candidate, separators=(",", ":")).encode("ascii")


def record(candidate=None):
    return w.PREFIX.encode() + raw(candidate) + b"\n" + w.STATUS.encode() + b"\n"


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


if __name__ == "__main__":
    unittest.main()
