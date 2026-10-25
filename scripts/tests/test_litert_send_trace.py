"""Pure send-boundary failure-wire checks; no model, SDK or device operations.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts.tests import test_litert_worker_trace as worker

PATH = Path(__file__).resolve().parents[2] / "benchmarks/litert_send_trace.py"
SPEC = importlib.util.spec_from_file_location("send_trace_under_test", PATH)
s = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s)


def value():
    return {"version": 1, "counts": {event: 0 for event in s.EVENTS}, "saturated": [],
        "last_ms": {event: None for event in s.EVENTS}, "snapshot_ms": 0, "time_saturated": False}


def value_v2():
    candidate = value()
    candidate.update(version=2, format_counts={kind: 0 for kind in s.FORMATS},
        format_saturated=[], last_format=None)
    return candidate


def raw(candidate=None):
    return json.dumps(value() if candidate is None else candidate, separators=(",", ":")).encode("ascii")


def record(candidate=None):
    return s.PREFIX.encode() + raw(candidate) + b"\n" + s.STATUS.encode() + b"\n"


def failed(candidate=None):
    return record(candidate) + b"FAILURES!!!\nTests run: 1, Failures: 1\nINSTRUMENTATION_CODE: -1\n"


class SendTraceTests(unittest.TestCase):
    def refuses(self, payload):
        with self.assertRaises((AssertionError, ValueError, TypeError)) as caught:
            s.parse_send_trace(payload)
        self.assertNotIn("PRIVATE_CANARY", str(caught.exception))

    def test_import_is_inert_and_controller_load_is_lazy(self):
        spec = importlib.util.spec_from_file_location("send_trace_inert", PATH)
        fresh = importlib.util.module_from_spec(spec)
        with patch.object(importlib.util, "spec_from_file_location", side_effect=AssertionError("Unexpected controller load")), \
             patch.object(Path, "read_bytes", side_effect=AssertionError("Unexpected file read")):
            spec.loader.exec_module(fresh)
        self.assertEqual(fresh._controller.cache_info().currsize, 0)

    def test_frozen_vocabulary_and_independent_failure_observations(self):
        self.assertEqual(s.EVENTS, ("ARGUMENTS_ENTERED", "ARGUMENTS_RETURNED", "ARGUMENTS_THROWN",
            "ASYNC_CALL_ENTERED", "ASYNC_CALL_RETURNED", "ASYNC_CALL_THROWN"))
        for observed in ({"ARGUMENTS_ENTERED": 1, "ARGUMENTS_THROWN": 1},
                {"ARGUMENTS_ENTERED": 1, "ARGUMENTS_RETURNED": 1, "ASYNC_CALL_ENTERED": 1, "ASYNC_CALL_THROWN": 1},
                {"ARGUMENTS_RETURNED": 4, "ASYNC_CALL_RETURNED": 9, "ASYNC_CALL_THROWN": 11}):
            candidate = value(); candidate["snapshot_ms"] = 7
            for event, count in observed.items(): candidate["counts"][event] = count; candidate["last_ms"][event] = 7
            self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
        with patch.object(s._controller().contract, "strict_json", wraps=s._controller().contract.strict_json) as decode:
            s.parse_send_trace(raw()); decode.assert_called_once()

    def test_closed_keys_exact_count_types_and_bounds(self):
        for count in (-1, s.MAX_COUNT+1, 2**64, True, False, 0.0, "PRIVATE_CANARY", None, [], {}):
            candidate = value(); candidate["counts"][s.EVENTS[0]] = count; self.refuses(raw(candidate))
        for key, bad in (("version", True), ("version", 2), ("version", "1"), ("counts", None),
                ("counts", []), ("saturated", {}), ("last_ms", []), ("time_saturated", 0)):
            candidate = value(); candidate[key] = bad; self.refuses(raw(candidate))
        for key in value():
            candidate = value(); del candidate[key]; self.refuses(raw(candidate))
        for container in ("counts", "last_ms"):
            candidate = value(); del candidate[container][s.EVENTS[-1]]; self.refuses(raw(candidate))
            candidate = value(); candidate[container]["PRIVATE_CANARY"] = 0; self.refuses(raw(candidate))
        candidate = value(); candidate["raw_error"] = "PRIVATE_CANARY/content://model"; self.refuses(raw(candidate))
        for candidate in ([], None, "PRIVATE_CANARY"):
            self.refuses(json.dumps(candidate).encode())

    def test_ordered_saturation_is_overflow_subset_not_exact_hit(self):
        candidate = value(); candidate["snapshot_ms"] = 1
        for event in s.EVENTS: candidate["counts"][event] = s.MAX_COUNT; candidate["last_ms"][event] = 1
        self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
        for subset in (list(s.EVENTS), [s.EVENTS[0], s.EVENTS[-1]]):
            candidate["saturated"] = subset; self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
        for bad in ([s.EVENTS[0], s.EVENTS[0]], [s.EVENTS[-1], s.EVENTS[0]], [True], ["PRIVATE_CANARY"], None):
            changed = copy.deepcopy(candidate); changed["saturated"] = bad; self.refuses(raw(changed))
        candidate["saturated"] = [s.EVENTS[0]]; candidate["counts"][s.EVENTS[0]] = s.MAX_COUNT-1
        self.refuses(raw(candidate))

    def test_last_times_and_time_saturation_have_independent_bounds(self):
        for cap, flag in ((0, False), (s.MAX_MS, False), (s.MAX_MS, True)):
            candidate = value(); candidate.update(snapshot_ms=cap, time_saturated=flag)
            self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
        for key, bad in (("snapshot_ms", -1), ("snapshot_ms", s.MAX_MS+1), ("snapshot_ms", True),
                ("snapshot_ms", 0.0), ("snapshot_ms", None), ("time_saturated", 1), ("time_saturated", None),
                ("time_saturated", "PRIVATE_CANARY")):
            candidate = value(); candidate[key] = bad; self.refuses(raw(candidate))
        candidate = value(); candidate["time_saturated"] = True; self.refuses(raw(candidate))
        for last in (0, 7):
            candidate = value(); candidate["snapshot_ms"] = 7; candidate["counts"][s.EVENTS[0]] = 1; candidate["last_ms"][s.EVENTS[0]] = last
            self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
        for count, bad in ((0, 0), (1, None), (1, -1), (1, 8), (1, True), (1, 0.0), (1, "PRIVATE_CANARY")):
            candidate = value(); candidate["snapshot_ms"] = 7; candidate["counts"][s.EVENTS[0]] = count; candidate["last_ms"][s.EVENTS[0]] = bad
            self.refuses(raw(candidate))

    def test_duplicate_nonfinite_and_raw_private_bytes_refuse(self):
        good = raw()
        variants = [good.replace(b'"version":1', b'"version":1,"version":1'),
            good.replace(b'"counts":{', b'"counts":{"ARGUMENTS_ENTERED":0,'),
            good.replace(b'"last_ms":{', b'"last_ms":{"ARGUMENTS_ENTERED":null,')]
        for nonfinite in (b"NaN", b"Infinity", b"-Infinity"):
            variants.append(good.replace(b'"snapshot_ms":0', b'"snapshot_ms":'+nonfinite))
        variants += [good+b"{}", good+b" PRIVATE_CANARY", good+b"\n", good+b"\r", good+b"\v", good+b"\f", good+b"\x00", good+b"\xff", b"PRIVATE_CANARY/path"]
        for payload in variants: self.refuses(payload)

    def test_prefix_inclusive_2048_ascii_limit(self):
        good = raw(); room = s.MAX_BYTES-len(s.PREFIX.encode())-len(good)
        self.assertGreater(room, 0)
        self.assertEqual(s.parse_send_trace(good+b" "*room), value())
        self.refuses(good+b" "*(room+1))
        for payload in (b"", "not bytes", bytearray(good)): self.refuses(payload)
        self.assertEqual(s.extract_send_trace(s.PREFIX.encode()+good+b" "*room+b"\n"+s.STATUS.encode()+b"\n"), value())

    def test_exact_lf_crlf_optional_absence_and_unrelated_statuses(self):
        self.assertEqual(s.extract_send_trace(failed()), value())
        self.assertEqual(s.extract_send_trace(failed().replace(b"\n", b"\r\n")), value())
        for payload in (b"OK (1 test)\nINSTRUMENTATION_CODE: -1\n", b"FAILURES!!!\n", b"\n",
                b"INSTRUMENTATION_STATUS: other=metadata\nINSTRUMENTATION_STATUS_CODE: 1337\n"):
            self.assertIsNone(s.extract_send_trace(payload))
        unrelated = b"INSTRUMENTATION_STATUS: other=metadata\nINSTRUMENTATION_STATUS_CODE: 1400\n"
        self.assertEqual(s.extract_send_trace(unrelated+failed()), value())

    def test_spoofed_key_code_duplicates_and_machine_framing_refuse(self):
        malformed = [record()+record(), record()+s.STATUS.encode()+b"\n", s.STATUS.encode()+b"\n",
            s.PREFIX.encode()+raw()+b"\n", record().replace(b"\nINSTRUMENTATION_STATUS_CODE", b"\n\nINSTRUMENTATION_STATUS_CODE"),
            b" "+record(), record()+s.STATUS_KEY.encode()+b"\n", b"INSTRUMENTATION_STATUS: other_"+s.STATUS_KEY.encode()+b"={}\n",
            record().replace(s.STATUS.encode(), b"INSTRUMENTATION_STATUS_CODE: 1337")]
        for code in (b"01338", b"+1338", b"1338 ", b"1338.0"):
            malformed.append(record()+b"INSTRUMENTATION_STATUS_CODE: "+code+b"\n")
        malformed += [record()+b" INSTRUMENTATION_STATUS_CODE: 1338\n",
            failed().replace(b"\n", b"\r\r\n"), failed().replace(b"\n", b"\v"), failed().replace(b"\n", b"\f"),
            failed()+b" "*131072]
        for payload in malformed:
            with self.subTest(payload=payload[:70]), self.assertRaises(AssertionError): s.extract_send_trace(payload)

    def test_failure_trace_can_never_accompany_passing_runner(self):
        for success in (b"OK (1 test)\n", b"OK (2 tests)\n"):
            with self.assertRaises(AssertionError): s.extract_send_trace(record()+success)

    def test_worker_1337_and_send_1338_remain_distinct_failure_channels(self):
        # A public callback may happen before the synchronous call returns or throws.
        # These separate snapshots impose no cross-channel lifecycle ordering.
        timed = worker.timed(); timed["snapshot_ms"] = 5
        timed["counts"].update(DONE_ENTERED=1, DONE_RETURNED=1)
        timed["last_ms"].update(DONE_ENTERED=3, DONE_RETURNED=4)
        send = value(); send["snapshot_ms"] = 5
        send["counts"].update(ASYNC_CALL_ENTERED=1, ASYNC_CALL_THROWN=1)
        send["last_ms"].update(ASYNC_CALL_ENTERED=2, ASYNC_CALL_THROWN=5)
        combined = worker.record(timed)+failed(send)
        self.assertEqual(s.extract_send_trace(combined), send)
        self.assertEqual(worker.w.extract_worker_trace(combined), timed)
        self.assertIsNone(s.extract_send_trace(worker.failed(timed)))
        self.assertIsNone(worker.w.extract_worker_trace(failed()))

    def test_declared_order_maximum_fixture_fits_both_wire_bounds(self):
        candidate = value(); candidate.update(snapshot_ms=s.MAX_MS, time_saturated=True)
        candidate["saturated"] = list(s.EVENTS)
        for event in s.EVENTS: candidate["counts"][event] = s.MAX_COUNT; candidate["last_ms"][event] = s.MAX_MS
        maximum = raw(candidate)
        self.assertEqual(s.parse_send_trace(maximum), candidate)
        self.assertEqual(len(maximum), 552)
        self.assertEqual(len(s.PREFIX.encode())+len(maximum), 602)
        self.assertLessEqual(len(s.PREFIX.encode())+len(maximum), s.MAX_BYTES)
        self.assertEqual(hashlib.sha256(maximum).hexdigest(), "12402ccfe90b5203a3abcf569d6cee9be95112778c8668b6a3733a5318bf86a6")


class SendTraceV2Tests(unittest.TestCase):
    refuses = SendTraceTests.refuses

    def test_versions_remain_closed_and_v1_has_no_fabricated_formats(self):
        self.assertEqual(s.FORMATS, ("REGEX", "JSON_OBJECT", "OTHER"))
        self.assertEqual(s.parse_send_trace(raw(value_v2())), value_v2())
        legacy = s.parse_send_trace(raw())
        self.assertEqual(legacy, value())
        self.assertEqual(tuple(legacy), tuple(value()))
        self.assertTrue(set(s.FORMATS).isdisjoint(legacy))
        for version in (0, 3, -1, True, False, 2.0, "2", None, [], {}):
            candidate = value_v2(); candidate["version"] = version; self.refuses(raw(candidate))
        for key in ("format_counts", "format_saturated", "last_format"):
            candidate = value_v2(); del candidate[key]; self.refuses(raw(candidate))
            candidate = value(); candidate[key] = value_v2()[key]; self.refuses(raw(candidate))
        candidate = value_v2(); candidate["PRIVATE_CANARY"] = "content://model"; self.refuses(raw(candidate))
        candidate = value_v2(); candidate["version"] = 1; self.refuses(raw(candidate))
        candidate = value(); candidate["version"] = 2; self.refuses(raw(candidate))

    def test_format_map_exact_order_keys_and_count_types(self):
        for kind in s.FORMATS:
            for count in (-1, s.MAX_COUNT+1, 2**64, True, False, 0.0, 1.5, "PRIVATE_CANARY", None, [], {}):
                candidate = value_v2(); candidate["format_counts"][kind] = count; self.refuses(raw(candidate))
            candidate = value_v2(); del candidate["format_counts"][kind]; self.refuses(raw(candidate))
        for counts in (None, [], 0, "PRIVATE_CANARY", {"REGEX": 0, "JSON_OBJECT": 0, "OTHER": 0, "PRIVATE_CANARY": 0},
                {"OTHER": 0, "JSON_OBJECT": 0, "REGEX": 0}, {"REGEX": 0, "OTHER": 0, "JSON_OBJECT": 0}):
            candidate = value_v2(); candidate["format_counts"] = counts; self.refuses(raw(candidate))

    def test_last_format_null_iff_all_zero_and_only_positive_kind(self):
        for kind in s.FORMATS:
            for count in (1, s.MAX_COUNT):
                candidate = value_v2(); candidate["format_counts"][kind] = count; candidate["last_format"] = kind
                self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
            for last in (None, True, 1, [], {}, "PRIVATE_CANARY") + tuple(other for other in s.FORMATS if other != kind):
                candidate = value_v2(); candidate["format_counts"][kind] = 1; candidate["last_format"] = last
                self.refuses(raw(candidate))
        for last in s.FORMATS + (True, 0, "PRIVATE_CANARY", [], {}):
            candidate = value_v2(); candidate["last_format"] = last; self.refuses(raw(candidate))
        candidate = value_v2(); candidate["format_counts"] = dict.fromkeys(s.FORMATS, 7)
        for kind in s.FORMATS:
            candidate["last_format"] = kind; self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)

    def test_format_saturation_is_ordered_overflow_subset(self):
        candidate = value_v2(); candidate["format_counts"] = dict.fromkeys(s.FORMATS, s.MAX_COUNT)
        candidate["last_format"] = "OTHER"
        for mask in range(8):
            candidate["format_saturated"] = [kind for bit, kind in enumerate(s.FORMATS) if mask & (1 << bit)]
            self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
        for overflow in (None, {}, True, "REGEX", [True], ["PRIVATE_CANARY"], ["REGEX", "REGEX"],
                ["OTHER", "REGEX"], ["JSON_OBJECT", "REGEX"], list(reversed(s.FORMATS))):
            changed = copy.deepcopy(candidate); changed["format_saturated"] = overflow; self.refuses(raw(changed))
        for kind in s.FORMATS:
            changed = copy.deepcopy(candidate); changed["format_saturated"] = [kind]
            changed["format_counts"][kind] = s.MAX_COUNT-1; self.refuses(raw(changed))

    def test_format_counters_do_not_impose_causal_crosscounter_patterns(self):
        # Format observation can precede a thrown dispatch; the wire never claims
        # SDK entry, enforcement, terminal state, or a relation to event totals.
        for kind in s.FORMATS:
            candidate = value_v2(); candidate["format_counts"][kind] = s.MAX_COUNT
            candidate["format_saturated"] = [kind]; candidate["last_format"] = kind
            self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
        candidate = value_v2(); candidate["snapshot_ms"] = 1
        for event in s.EVENTS: candidate["counts"][event] = 7; candidate["last_ms"][event] = 1
        self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)
        candidate["format_counts"]["OTHER"] = 1; candidate["last_format"] = "OTHER"
        self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)

    def test_v2_shared_event_and_time_invariants_still_apply(self):
        for key, bad in (("counts", {}), ("saturated", ["ARGUMENTS_ENTERED"]), ("last_ms", {}),
                ("snapshot_ms", True), ("snapshot_ms", s.MAX_MS+1), ("time_saturated", 1), ("time_saturated", True)):
            candidate = value_v2(); candidate[key] = bad; self.refuses(raw(candidate))
        candidate = value_v2(); candidate["counts"][s.EVENTS[0]] = 1
        self.refuses(raw(candidate))
        candidate["last_ms"][s.EVENTS[0]] = 0
        self.assertEqual(s.parse_send_trace(raw(candidate)), candidate)

    def test_v2_duplicate_keys_private_data_and_nonfinite_refuse(self):
        good = raw(value_v2())
        for before, after in ((b'"version":2', b'"version":2,"version":1'),
                (b'"format_counts":{', b'"format_counts":{"REGEX":0,'),
                (b'"format_saturated":[]', b'"format_saturated":[],"format_saturated":[]'),
                (b'"last_format":null', b'"last_format":null,"last_format":null')):
            self.refuses(good.replace(before, after))
        for count in (b"NaN", b"Infinity", b"-Infinity"):
            self.refuses(good.replace(b'"REGEX":0', b'"REGEX":'+count))
        for suffix in (b"\n", b"\r", b"\v", b"\f", b"\x00", b"\xff", b"{}", b" PRIVATE_CANARY"):
            self.refuses(good+suffix)
        for key in ("prompt", "schema", "pattern", "output", "throwable", "path", "sha256"):
            candidate = value_v2(); candidate[key] = "PRIVATE_CANARY"; self.refuses(raw(candidate))

    def test_v2_extractor_keeps_failure_channel_and_framing_rules(self):
        candidate = value_v2(); candidate["format_counts"]["REGEX"] = 1; candidate["last_format"] = "REGEX"
        self.assertEqual(s.extract_send_trace(failed(candidate)), candidate)
        self.assertEqual(s.extract_send_trace(failed(candidate).replace(b"\n", b"\r\n")), candidate)
        for payload in (record(candidate)+record(candidate), record()+record(candidate), record(candidate)+record(),
                record(candidate)+s.STATUS.encode()+b"\n", record(candidate)+b"OK (1 test)\n",
                record(candidate)+b"OK (2 tests)\n", b" "+record(candidate),
                record(candidate).replace(s.STATUS.encode(), b"INSTRUMENTATION_STATUS_CODE: 01338"),
                record(candidate).replace(b"\n", b"\r\r\n"), record(candidate).replace(b"\n", b"\v"),
                record(candidate).replace(b"\n", b"\f")):
            with self.subTest(payload=payload[:70]), self.assertRaises(AssertionError): s.extract_send_trace(payload)
        combined = worker.record(worker.timed())+failed(candidate)
        self.assertEqual(s.extract_send_trace(combined), candidate)
        self.assertEqual(worker.w.extract_worker_trace(combined), worker.timed())

    def test_v2_prefix_inclusive_limit_and_fresh_return_objects(self):
        good = raw(value_v2()); room = s.MAX_BYTES-len(s.PREFIX.encode())-len(good)
        self.assertGreater(room, 0)
        self.assertEqual(s.parse_send_trace(good+b" "*room), value_v2())
        self.refuses(good+b" "*(room+1))
        self.assertEqual(s.extract_send_trace(s.PREFIX.encode()+good+b" "*room+b"\n"+s.STATUS.encode()+b"\n"), value_v2())
        decoded = s.parse_send_trace(good); decoded["format_counts"]["REGEX"] = 99
        decoded["format_saturated"].append("PRIVATE_CANARY")
        self.assertEqual(s.parse_send_trace(good), value_v2())

    def test_dense_v2_fixture_matches_kotlin_declared_serialization(self):
        candidate = value_v2(); candidate.update(snapshot_ms=s.MAX_MS, time_saturated=True)
        candidate["saturated"] = list(s.EVENTS)
        for event in s.EVENTS: candidate["counts"][event] = s.MAX_COUNT; candidate["last_ms"][event] = s.MAX_MS
        candidate["format_counts"] = dict.fromkeys(s.FORMATS, s.MAX_COUNT)
        candidate["format_saturated"] = list(s.FORMATS); candidate["last_format"] = "OTHER"
        maximum = raw(candidate)
        self.assertEqual(tuple(candidate), ("version", "counts", "saturated", "last_ms", "snapshot_ms", "time_saturated",
            "format_counts", "format_saturated", "last_format"))
        self.assertEqual(s.parse_send_trace(maximum), candidate)
        self.assertEqual(len(maximum), 697)
        self.assertEqual(len(s.PREFIX.encode())+len(maximum), 747)
        self.assertEqual(hashlib.sha256(maximum).hexdigest(), "4359c8f70c2e3024b59e94fe7738e7d117a72a8caf9f682a944b6558f7e6fd65")
        self.assertLessEqual(len(s.PREFIX.encode())+len(maximum), s.MAX_BYTES)


if __name__ == "__main__": unittest.main()
