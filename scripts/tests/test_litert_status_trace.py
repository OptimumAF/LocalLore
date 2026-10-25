"""Pure finite declared-status wire tests; no SDK, model or device operations.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts.tests import test_litert_callback_trace as callback
from scripts.tests import test_litert_send_trace as send
from scripts.tests import test_litert_worker_trace as worker

PATH = Path(__file__).resolve().parents[2] / "benchmarks/litert_status_trace.py"
SPEC = importlib.util.spec_from_file_location("status_trace_under_test", PATH)
s = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s)


def value():
    return {"version": 1, "counts": {event: 0 for event in s.EVENTS}, "saturated": []}


def raw(candidate=None):
    return json.dumps(value() if candidate is None else candidate, separators=(",", ":")).encode("ascii")


def record(candidate=None):
    return s.PREFIX.encode() + raw(candidate) + b"\n" + s.STATUS.encode() + b"\n"


def failed(candidate=None):
    return record(candidate) + b"FAILURES!!!\nTests run: 1, Failures: 1\nINSTRUMENTATION_CODE: -1\n"


class StatusTraceTests(unittest.TestCase):
    def refuses(self, payload):
        with self.assertRaises((AssertionError, ValueError, TypeError)) as caught:
            s.parse_status_trace(payload)
        self.assertNotIn("PRIVATE_CANARY", str(caught.exception))

    def test_import_is_inert_with_lazy_trusted_decoder_loading(self):
        spec = importlib.util.spec_from_file_location("status_trace_inert", PATH)
        fresh = importlib.util.module_from_spec(spec)
        with patch.object(importlib.util, "spec_from_file_location", side_effect=AssertionError("Unexpected controller load")), \
             patch.object(Path, "read_bytes", side_effect=AssertionError("Unexpected file read")):
            spec.loader.exec_module(fresh)
        self.assertEqual(fresh._controller.cache_info().currsize, 0)

    def test_frozen_vocabulary_and_each_independent_declared_count(self):
        self.assertEqual(s.STATUS_KEY, "locallore_receipt_status_v1")
        self.assertEqual(s.STATUS_CODE, 1340)
        self.assertEqual(s.MAX_BYTES, 2048)
        self.assertEqual(s.MAX_COUNT, 1000000)
        expected = tuple("CODE_"+str(code) for code in range(17)) + ("UNRECOGNIZED",)
        self.assertEqual(s.EVENTS, expected)
        for event in expected:
            candidate = value(); candidate["counts"][event] = 1
            self.assertEqual(s.parse_status_trace(raw(candidate)), candidate)
        candidate = value(); candidate["counts"].update(CODE_0=7, CODE_16=3, UNRECOGNIZED=11)
        self.assertEqual(s.parse_status_trace(raw(candidate)), candidate)
        with patch.object(s._controller().contract, "strict_json", wraps=s._controller().contract.strict_json) as decode:
            s.parse_status_trace(raw()); decode.assert_called_once()

    def test_closed_shape_types_and_no_private_runtime_fields(self):
        for key in value():
            candidate = value(); del candidate[key]; self.refuses(raw(candidate))
        for key, wrong in (("version", True), ("version", 2), ("version", "1"), ("counts", None),
                ("counts", []), ("saturated", None), ("saturated", {}), ("saturated", [True])):
            candidate = value(); candidate[key] = wrong; self.refuses(raw(candidate))
        for key in ("message", "cause", "class", "stack", "path", "role", "snapshot_ms", "request_id"):
            candidate = value(); candidate[key] = "PRIVATE_CANARY/content://model"; self.refuses(raw(candidate))
        for candidate in (None, [], "PRIVATE_CANARY"):
            self.refuses(json.dumps(candidate).encode())

    def test_exact_counter_keys_and_integer_bounds_exclude_booleans(self):
        for wrong in (-1, s.MAX_COUNT+1, 2**64, True, False, 0.0, "PRIVATE_CANARY", None, [], {}):
            candidate = value(); candidate["counts"][s.EVENTS[0]] = wrong; self.refuses(raw(candidate))
        for event in s.EVENTS:
            candidate = value(); del candidate["counts"][event]; self.refuses(raw(candidate))
        for extra in ("CODE_17", "code_0", "PRIVATE_CANARY"):
            candidate = value(); candidate["counts"][extra] = 0; self.refuses(raw(candidate))
        candidate = value()
        for event in s.EVENTS: candidate["counts"][event] = s.MAX_COUNT
        self.assertEqual(s.parse_status_trace(raw(candidate)), candidate)

    def test_overflow_only_ordered_unique_saturation(self):
        candidate = value()
        for event in s.EVENTS: candidate["counts"][event] = s.MAX_COUNT
        for subset in ([], list(s.EVENTS), [s.EVENTS[0], s.EVENTS[-1]]):
            candidate["saturated"] = subset; self.assertEqual(s.parse_status_trace(raw(candidate)), candidate)
        for wrong in ([s.EVENTS[0], s.EVENTS[0]], [s.EVENTS[-1], s.EVENTS[0]], ["PRIVATE_CANARY"], [True]):
            changed = copy.deepcopy(candidate); changed["saturated"] = wrong; self.refuses(raw(changed))
        candidate["saturated"] = [s.EVENTS[0]]; candidate["counts"][s.EVENTS[0]] = s.MAX_COUNT-1
        self.refuses(raw(candidate))

    def test_json_key_permutations_allowed_but_duplicates_and_nonfinite_refuse(self):
        candidate = value(); candidate["counts"] = dict(reversed(list(candidate["counts"].items())))
        candidate = dict(reversed(list(candidate.items())))
        self.assertEqual(s.parse_status_trace(raw(candidate)), candidate)
        good = raw()
        variants = [good.replace(b'"version":1', b'"version":1,"version":1'),
            good.replace(b'"counts":{', b'"counts":{"CODE_0":0,'),
            good.replace(b'"saturated":[]', b'"saturated":[],"saturated":[]')]
        for nonfinite in (b"NaN", b"Infinity", b"-Infinity"):
            variants.append(good.replace(b'"CODE_0":0', b'"CODE_0":'+nonfinite))
        for payload in variants: self.refuses(payload)

    def test_raw_ascii_control_and_prefix_inclusive_2048_limit(self):
        good = raw(); room = s.MAX_BYTES-len(s.PREFIX.encode())-len(good)
        self.assertGreater(room, 0)
        self.assertEqual(s.parse_status_trace(good+b" "*room), value())
        self.refuses(good+b" "*(room+1))
        self.assertEqual(s.extract_status_trace(s.PREFIX.encode()+good+b" "*room+b"\n"+s.STATUS.encode()+b"\n"), value())
        for suffix in (b" PRIVATE_CANARY", b"{}", b"\n", b"\r", b"\v", b"\f", b"\x00", b"\xff"):
            self.refuses(good+suffix)
        for payload in (b"PRIVATE_CANARY/path", b"", "not bytes", bytearray(good)):
            self.refuses(payload)

    def test_optional_absence_differs_from_explicit_zero_record(self):
        self.assertEqual(s.extract_status_trace(failed()), value())
        for payload in (b"\n", b"FAILURES!!!\n", b"OK (1 test)\nINSTRUMENTATION_CODE: -1\n",
                b"INSTRUMENTATION_STATUS: unrelated=metadata\nINSTRUMENTATION_STATUS_CODE: 1500\n"):
            self.assertIsNone(s.extract_status_trace(payload))

    def test_exact_lf_crlf_transport(self):
        candidate = value(); candidate["counts"]["CODE_13"] = 2
        self.assertEqual(s.extract_status_trace(failed(candidate)), candidate)
        self.assertEqual(s.extract_status_trace(failed(candidate).replace(b"\n", b"\r\n")), candidate)

    def test_duplicate_disguised_or_unpaired_record_never_becomes_absent(self):
        malformed = [record()+record(), record()+s.STATUS.encode()+b"\n", s.STATUS.encode()+b"\n",
            s.PREFIX.encode()+raw()+b"\n", record().replace(b"\nINSTRUMENTATION_STATUS_CODE", b"\n\nINSTRUMENTATION_STATUS_CODE"),
            b" "+record(), record()+s.STATUS_KEY.encode()+b"\n", b"INSTRUMENTATION_STATUS: other_"+s.STATUS_KEY.encode()+b"={}\n",
            record().replace(s.STATUS.encode(), b"INSTRUMENTATION_STATUS_CODE: 1339")]
        for code in (b"01340", b"+1340", b"1340 ", b"1340.0"):
            malformed.append(record()+b"INSTRUMENTATION_STATUS_CODE: "+code+b"\n")
        malformed += [record()+b" INSTRUMENTATION_STATUS_CODE: 1340\n", failed().replace(b"\n", b"\r\r\n"),
            failed().replace(b"\n", b"\v"), failed().replace(b"\n", b"\f"), failed()+b" "*131072]
        for payload in malformed:
            with self.subTest(payload=payload[:70]), self.assertRaises(AssertionError): s.extract_status_trace(payload)

    def test_code_zero_and_unrecognized_do_not_override_a_passing_runner(self):
        candidate = value(); candidate["counts"].update(CODE_0=1, UNRECOGNIZED=1)
        for passed in (b"OK (1 test)\n", b"OK (2 tests)\n"):
            with self.assertRaises(AssertionError): s.extract_status_trace(record(candidate)+passed)
        self.assertEqual(s.extract_status_trace(failed(candidate)), candidate)

    def test_all_four_channel_helpers_remain_independent(self):
        declared = value(); declared["counts"].update(CODE_0=7, CODE_13=3, UNRECOGNIZED=11)
        callbacks = callback.value(1); callbacks["calls"][0]["counts"].update(DONE=2, SDK_JNI=1, CANCELLED=3)
        sent = send.value(); sent["snapshot_ms"] = 5
        sent["counts"]["ASYNC_CALL_THROWN"] = 1; sent["last_ms"]["ASYNC_CALL_THROWN"] = 5
        worked = worker.timed()
        previous = worker.record(worked)+send.record(sent)+callback.record(callbacks)
        combined = previous+failed(declared)
        self.assertEqual(s.extract_status_trace(combined), declared)
        self.assertEqual(callback.c.extract_callback_trace(combined), callbacks)
        self.assertEqual(send.s.extract_send_trace(combined), sent)
        self.assertEqual(worker.w.extract_worker_trace(combined), worked)
        self.assertIsNone(s.extract_status_trace(previous+b"FAILURES!!!\n"))
        self.assertIsNone(callback.c.extract_callback_trace(failed(declared)))
        self.assertIsNone(send.s.extract_send_trace(failed(declared)))
        self.assertIsNone(worker.w.extract_worker_trace(failed(declared)))

    def test_canonical_dense_fixture_matches_producer_byte_and_hash_pin(self):
        candidate = value(); candidate["saturated"] = list(s.EVENTS)
        for event in s.EVENTS: candidate["counts"][event] = s.MAX_COUNT
        dense = raw(candidate)
        self.assertEqual(s.parse_status_trace(dense), candidate)
        self.assertEqual(len(dense), 532)
        self.assertEqual(len(s.PREFIX.encode())+len(dense), 584)
        self.assertEqual(hashlib.sha256(dense).hexdigest(), "14007fc5a07f286147fdae2350af4d203b2470d7a9e674d95645dd10e1b574b3")


if __name__ == "__main__": unittest.main()
