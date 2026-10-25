"""Pure finite callback-wire checks; no model, SDK, build or device operations.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts.tests import test_litert_send_trace as send
from scripts.tests import test_litert_worker_trace as worker

PATH = Path(__file__).resolve().parents[2] / "benchmarks/litert_callback_trace.py"
SPEC = importlib.util.spec_from_file_location("callback_trace_under_test", PATH)
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def call(ordinal=1):
    return {"ordinal": ordinal, "role": "DIRECTOR", "context_tokens": 4096, "max_output_tokens": 350,
        "prompt_bytes": 0, "schema_bytes": 2, "counts": {event: 0 for event in c.EVENTS}, "saturated": []}


def value(requests=0):
    return {"version": 1, "requests": requests, "requests_saturated": False,
        "calls": [call(ordinal) for ordinal in range(1, min(requests, c.MAX_CALLS)+1)]}


def raw(candidate=None):
    return json.dumps(value() if candidate is None else candidate, separators=(",", ":")).encode("ascii")


def record(candidate=None):
    return c.PREFIX.encode() + raw(candidate) + b"\n" + c.STATUS.encode() + b"\n"


def failed(candidate=None):
    return record(candidate) + b"FAILURES!!!\nTests run: 1, Failures: 1\nINSTRUMENTATION_CODE: -1\n"


class CallbackTraceTests(unittest.TestCase):
    def refuses(self, payload):
        with self.assertRaises((AssertionError, ValueError, TypeError)) as caught:
            c.parse_callback_trace(payload)
        self.assertNotIn("PRIVATE_CANARY", str(caught.exception))

    def test_import_is_inert_and_controller_loading_is_lazy(self):
        spec = importlib.util.spec_from_file_location("callback_trace_inert", PATH)
        fresh = importlib.util.module_from_spec(spec)
        with patch.object(importlib.util, "spec_from_file_location", side_effect=AssertionError("Unexpected controller load")), \
             patch.object(Path, "read_bytes", side_effect=AssertionError("Unexpected file read")):
            spec.loader.exec_module(fresh)
        self.assertEqual(fresh._controller.cache_info().currsize, 0)

    def test_frozen_wire_and_explicit_zero_differ_from_absence(self):
        self.assertEqual(c.STATUS_KEY, "locallore_receipt_callback_v1")
        self.assertEqual(c.STATUS_CODE, 1339)
        self.assertEqual(c.MAX_BYTES, 4096)
        self.assertEqual(c.MAX_COUNT, 1000000)
        self.assertEqual(c.MAX_CALLS, 3)
        self.assertEqual(c.EVENTS, ("OUTPUT_CHUNKS", "OUTPUT_BYTES", "DONE", "CANCELLED", "SDK_JNI", "OTHER"))
        self.assertEqual(c.parse_callback_trace(raw()), value())
        self.assertEqual(c.extract_callback_trace(failed()), value())
        self.assertIsNone(c.extract_callback_trace(b"FAILURES!!!\n"))
        with patch.object(c._controller().contract, "strict_json", wraps=c._controller().contract.strict_json) as decode:
            c.parse_callback_trace(raw()); decode.assert_called_once()

    def test_request_counts_omission_and_overflow_only_flags(self):
        for requests in (0, 1, 2, 3, 4, 100, c.MAX_COUNT):
            candidate = value(requests)
            self.assertEqual(c.parse_callback_trace(raw(candidate)), candidate)
            self.assertEqual(len(candidate["calls"]), min(requests, 3))
        candidate = value(c.MAX_COUNT); candidate["requests_saturated"] = True
        self.assertEqual(c.parse_callback_trace(raw(candidate)), candidate)
        for count in (-1, c.MAX_COUNT+1, True, False, 0.0, "PRIVATE_CANARY", None, [], {}):
            candidate = value(); candidate["requests"] = count; self.refuses(raw(candidate))
        for flag in (0, 1, None, "PRIVATE_CANARY", []):
            candidate = value(); candidate["requests_saturated"] = flag; self.refuses(raw(candidate))
        candidate = value(3); candidate["requests_saturated"] = True; self.refuses(raw(candidate))
        for requests, retained in ((0, 1), (1, 0), (2, 1), (3, 2), (4, 2), (4, 4)):
            candidate = value(requests); candidate["calls"] = [call(i) for i in range(1, retained+1)]
            self.refuses(raw(candidate))

    def test_closed_top_level_and_retained_call_fields(self):
        for key in value():
            candidate = value(1); del candidate[key]; self.refuses(raw(candidate))
        for key, wrong in (("version", True), ("version", 2), ("version", "1"), ("calls", None),
                ("calls", {}), ("calls", "PRIVATE_CANARY")):
            candidate = value(1); candidate[key] = wrong; self.refuses(raw(candidate))
        for key in call():
            candidate = value(1); del candidate["calls"][0][key]; self.refuses(raw(candidate))
        for wrong in (None, [], "PRIVATE_CANARY", 1):
            candidate = value(1); candidate["calls"][0] = wrong; self.refuses(raw(candidate))
        for wrong in (None, [], "PRIVATE_CANARY"):
            self.refuses(json.dumps(wrong).encode())
        candidate = value(); candidate["path"] = "PRIVATE_CANARY/content://model"; self.refuses(raw(candidate))

    def test_contiguous_ordinals_fixed_roles_and_permuted_roles(self):
        for wrong in (0, -1, 2, True, 1.0, "1", None):
            candidate = value(1); candidate["calls"][0]["ordinal"] = wrong; self.refuses(raw(candidate))
        candidate = value(3); candidate["calls"] = list(reversed(candidate["calls"])); self.refuses(raw(candidate))
        candidate = value(3); candidate["calls"][1]["ordinal"] = 1; self.refuses(raw(candidate))
        for wrong in ("REPAIR", "PRIVATE_CANARY", "director", True, 1, None, []):
            candidate = value(1); candidate["calls"][0]["role"] = wrong; self.refuses(raw(candidate))
        candidate = value(3)
        for entry, role in zip(candidate["calls"], ("NARRATOR", "DIRECTOR", "NARRATOR")): entry["role"] = role
        self.assertEqual(c.parse_callback_trace(raw(candidate)), candidate)

    def test_configured_request_bounds_and_combined_byte_budget(self):
        for context, output, prompt, schema in ((512, 1, 0, 2), (4096, 350, 32766, 2),
                (512, 350, 0, 32768), (4096, 1, 16384, 16384)):
            candidate = value(1); candidate["calls"][0].update(context_tokens=context, max_output_tokens=output,
                prompt_bytes=prompt, schema_bytes=schema)
            self.assertEqual(c.parse_callback_trace(raw(candidate)), candidate)
        for key, wrong in (("context_tokens", 511), ("context_tokens", 4097), ("max_output_tokens", 0),
                ("max_output_tokens", 351), ("prompt_bytes", -1), ("prompt_bytes", 32769),
                ("schema_bytes", 1), ("schema_bytes", 32769)):
            candidate = value(1); candidate["calls"][0][key] = wrong; self.refuses(raw(candidate))
        for key in ("context_tokens", "max_output_tokens", "prompt_bytes", "schema_bytes"):
            for wrong in (True, False, 1.0, "PRIVATE_CANARY", None, []):
                candidate = value(1); candidate["calls"][0][key] = wrong; self.refuses(raw(candidate))
        candidate = value(1); candidate["calls"][0].update(prompt_bytes=16385, schema_bytes=16384)
        self.refuses(raw(candidate))

    def test_exact_counter_keys_types_and_boundaries(self):
        for wrong in (-1, c.MAX_COUNT+1, 2**64, True, False, 0.0, "PRIVATE_CANARY", None, [], {}):
            candidate = value(1); candidate["calls"][0]["counts"][c.EVENTS[0]] = wrong; self.refuses(raw(candidate))
        for wrong in (None, [], "PRIVATE_CANARY"):
            candidate = value(1); candidate["calls"][0]["counts"] = wrong; self.refuses(raw(candidate))
        candidate = value(1); del candidate["calls"][0]["counts"][c.EVENTS[-1]]; self.refuses(raw(candidate))
        candidate = value(1); candidate["calls"][0]["counts"]["PRIVATE_CANARY"] = 0; self.refuses(raw(candidate))
        candidate = value(1)
        for event in c.EVENTS: candidate["calls"][0]["counts"][event] = c.MAX_COUNT
        self.assertEqual(c.parse_callback_trace(raw(candidate)), candidate)

    def test_counter_saturation_is_ordered_unique_overflow_subset(self):
        candidate = value(1); entry = candidate["calls"][0]
        for event in c.EVENTS: entry["counts"][event] = c.MAX_COUNT
        for subset in ([], list(c.EVENTS), [c.EVENTS[0], c.EVENTS[-1]]):
            entry["saturated"] = subset; self.assertEqual(c.parse_callback_trace(raw(candidate)), candidate)
        for wrong in (None, {}, "PRIVATE_CANARY", [True], ["PRIVATE_CANARY"],
                [c.EVENTS[0], c.EVENTS[0]], [c.EVENTS[-1], c.EVENTS[0]]):
            changed = copy.deepcopy(candidate); changed["calls"][0]["saturated"] = wrong; self.refuses(raw(changed))
        entry["saturated"] = [c.EVENTS[0]]; entry["counts"][c.EVENTS[0]] = c.MAX_COUNT-1
        self.refuses(raw(candidate))

    def test_independent_repeated_terminal_and_output_observations(self):
        candidate = value(4)
        candidate["calls"][0]["counts"].update(OUTPUT_CHUNKS=0, OUTPUT_BYTES=c.MAX_COUNT, DONE=7, CANCELLED=3, SDK_JNI=5, OTHER=2)
        candidate["calls"][0]["max_output_tokens"] = 1
        candidate["calls"][1]["counts"].update(DONE=2, SDK_JNI=4)
        candidate["calls"][2]["counts"].update(CANCELLED=8, OTHER=9)
        self.assertEqual(c.parse_callback_trace(raw(candidate)), candidate)

    def test_json_key_permutation_allowed_but_duplicates_and_nonfinite_refuse(self):
        candidate = value(1)
        entry = candidate["calls"][0]
        entry["counts"] = dict(reversed(list(entry["counts"].items())))
        candidate["calls"][0] = dict(reversed(list(entry.items())))
        candidate = dict(reversed(list(candidate.items())))
        self.assertEqual(c.parse_callback_trace(raw(candidate)), candidate)
        good = raw(value(1))
        variants = [good.replace(b'"version":1', b'"version":1,"version":1'),
            good.replace(b'"ordinal":1', b'"ordinal":1,"ordinal":1'),
            good.replace(b'"counts":{', b'"counts":{"DONE":0,'),
            good.replace(b'"saturated":[]', b'"saturated":[],"saturated":[]')]
        for nonfinite in (b"NaN", b"Infinity", b"-Infinity"):
            for field in (b'"requests":1', b'"prompt_bytes":0', b'"DONE":0'):
                variants.append(good.replace(field, field.split(b":")[0]+b":"+nonfinite))
        for payload in variants: self.refuses(payload)

    def test_private_fields_and_raw_nonascii_or_control_payloads_refuse(self):
        for key in ("prompt", "schema", "message", "error", "class", "cause", "path", "token_text"):
            candidate = value(1); candidate["calls"][0][key] = "PRIVATE_CANARY/content://model"; self.refuses(raw(candidate))
        good = raw(value(1))
        for suffix in (b" PRIVATE_CANARY", b"{}", b"\n", b"\r", b"\v", b"\f", b"\x00", b"\xff"):
            self.refuses(good+suffix)
        for payload in (b"PRIVATE_CANARY/path", b"", "not bytes", bytearray(good)):
            self.refuses(payload)

    def test_prefix_inclusive_size_bound_and_canonical_dense_fixture(self):
        good = raw(); room = c.MAX_BYTES-len(c.PREFIX.encode())-len(good)
        self.assertGreater(room, 0)
        self.assertEqual(c.parse_callback_trace(good+b" "*room), value())
        self.refuses(good+b" "*(room+1))
        self.assertEqual(c.extract_callback_trace(c.PREFIX.encode()+good+b" "*room+b"\n"+c.STATUS.encode()+b"\n"), value())
        candidate = value(c.MAX_COUNT); candidate["requests_saturated"] = True
        for entry in candidate["calls"]:
            entry.update(role="NARRATOR", context_tokens=4096, max_output_tokens=350, prompt_bytes=16384, schema_bytes=16384)
            entry["counts"] = {event: c.MAX_COUNT for event in c.EVENTS}; entry["saturated"] = list(c.EVENTS)
        dense = raw(candidate)
        self.assertEqual(c.parse_callback_trace(dense), candidate)
        self.assertEqual(len(dense), 1055)
        self.assertEqual(len(c.PREFIX.encode())+len(dense), 1109)
        self.assertEqual(hashlib.sha256(dense).hexdigest(), "754c4eef06b6ea5fa2bd395ec449be37779c875799f8a71cce5115e368d754b3")

    def test_exact_failure_transport_lf_crlf_and_optional_absence(self):
        candidate = value(1)
        self.assertEqual(c.extract_callback_trace(failed(candidate)), candidate)
        self.assertEqual(c.extract_callback_trace(failed(candidate).replace(b"\n", b"\r\n")), candidate)
        for payload in (b"\n", b"FAILURES!!!\n", b"OK (1 test)\nINSTRUMENTATION_CODE: -1\n",
                b"INSTRUMENTATION_STATUS: unrelated=metadata\nINSTRUMENTATION_STATUS_CODE: 1400\n"):
            self.assertIsNone(c.extract_callback_trace(payload))

    def test_duplicate_spoofed_or_unpaired_status_refuses_without_false_absence(self):
        malformed = [record()+record(), record()+c.STATUS.encode()+b"\n", c.STATUS.encode()+b"\n",
            c.PREFIX.encode()+raw()+b"\n", record().replace(b"\nINSTRUMENTATION_STATUS_CODE", b"\n\nINSTRUMENTATION_STATUS_CODE"),
            b" "+record(), record()+c.STATUS_KEY.encode()+b"\n", b"INSTRUMENTATION_STATUS: other_"+c.STATUS_KEY.encode()+b"={}\n",
            record().replace(c.STATUS.encode(), b"INSTRUMENTATION_STATUS_CODE: 1338")]
        for code in (b"01339", b"+1339", b"1339 ", b"1339.0"):
            malformed.append(record()+b"INSTRUMENTATION_STATUS_CODE: "+code+b"\n")
        malformed += [record()+b" INSTRUMENTATION_STATUS_CODE: 1339\n", failed().replace(b"\n", b"\r\r\n"),
            failed().replace(b"\n", b"\v"), failed().replace(b"\n", b"\f"), failed()+b" "*131072]
        for payload in malformed:
            with self.subTest(payload=payload[:70]), self.assertRaises(AssertionError): c.extract_callback_trace(payload)

    def test_custom_callback_record_never_accompanies_passing_runner(self):
        for passed in (b"OK (1 test)\n", b"OK (2 tests)\n"):
            with self.assertRaises(AssertionError): c.extract_callback_trace(record(value(1))+passed)

    def test_independent_worker_send_callback_channels_do_not_infer_lifecycle(self):
        observed = value(1); observed["calls"][0]["counts"].update(DONE=2, CANCELLED=1, SDK_JNI=3)
        send_value = send.value(); send_value["snapshot_ms"] = 5
        send_value["counts"]["ASYNC_CALL_THROWN"] = 1; send_value["last_ms"]["ASYNC_CALL_THROWN"] = 5
        worker_value = worker.timed()
        combined = worker.record(worker_value)+send.record(send_value)+failed(observed)
        self.assertEqual(c.extract_callback_trace(combined), observed)
        self.assertEqual(send.s.extract_send_trace(combined), send_value)
        self.assertEqual(worker.w.extract_worker_trace(combined), worker_value)
        self.assertIsNone(c.extract_callback_trace(worker.record(worker_value)+send.failed(send_value)))
        self.assertIsNone(send.s.extract_send_trace(failed(observed)))
        self.assertIsNone(worker.w.extract_worker_trace(failed(observed)))


if __name__ == "__main__": unittest.main()
