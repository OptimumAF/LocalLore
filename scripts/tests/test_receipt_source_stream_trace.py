"""Original synthetic host-read observations, never transfers or model accesses.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import dataclasses
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("source_stream_trace_under_test",
    Path(__file__).resolve().parents[2] / "benchmarks/receipt_source_stream_trace.py")
s = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = s; SPEC.loader.exec_module(s)
PRIVATE = "ORIGINAL_PRIVATE_STREAM_CANARY"


def encode(value):
    return json.dumps(value, separators=(",", ":")).encode("ascii")


def initial():
    return s.SourceStreamSnapshot(s.StreamPhase.GATE, 63).as_dict()


class Clock:
    value = 0
    def __call__(self): return self.value


class SourceStreamTraceTest(unittest.TestCase):
    def refuses(self, block):
        with self.assertRaises(s.SourceStreamTraceRefused) as caught:
            block()
        self.assertEqual("source_stream_trace_invalid", str(caught.exception))
        self.assertNotIn(PRIVATE, str(caught.exception)); self.assertIsNone(caught.exception.__context__)

    def test_wire_constants_defaults_and_all_declared_entered_phases(self):
        self.assertEqual(["GATE", "SOURCE_OPEN", "SOURCE_HASH", "CLIENT", "SOURCE_POSTCHECK", "LEASE_POSTCHECK", "COMPLETE"],
                         [phase.value for phase in s.StreamPhase])
        self.assertEqual("LOCALLORE_RECEIPT_SOURCE_STREAM_V1=", s.PREFIX)
        self.assertEqual((1024, 4096, 17179869184, 150000, 180000),
            (s.MAX_BYTES, s.MAX_CAPTURE, s.MAX_EXPECTED_BYTES, s.MAX_CLIENT_MS, s.MAX_ELAPSED_MS))
        clock = Clock(); trace = s.SourceStreamTrace(63, clock_ns=clock)
        self.assertEqual(initial(), s.parse_source_stream_trace(trace.json().encode()))
        for phase in s.StreamPhase:
            trace.phase(phase)
            self.assertEqual(phase.value, s.parse_source_stream_trace(trace.json().encode())["phase"])

    def test_entered_stage_is_not_success_and_budget_is_not_elapsed(self):
        clock = Clock(); trace = s.SourceStreamTrace(63, clock_ns=clock)
        trace.phase(s.StreamPhase.SOURCE_HASH); trace.source_verified(); trace.client_start(150000)
        clock.value = 1234567890
        trace.client_return(7); trace.position(12); trace.phase(s.StreamPhase.COMPLETE)
        value = s.parse_source_stream_trace(trace.json().encode())
        self.assertEqual("COMPLETE", value["phase"]); self.assertEqual(7, value["client_returncode"])
        self.assertEqual(150000, value["client_timeout_ms"]); self.assertEqual(1234, value["elapsed_ms"])
        self.assertEqual(12, value["source_position"])
        self.assertNotIn("destination_verified", value); self.assertNotIn("remote_exit_status_known", value)

    def test_full_or_partial_host_cursor_does_not_verify_source_or_destination(self):
        trace = s.SourceStreamTrace(63, clock_ns=Clock())
        for position in [0, 1, 32, 63, 0]:
            trace.position(position)
            value = s.parse_source_stream_trace(trace.json().encode())
            self.assertEqual(position, value["source_position"]); self.assertFalse(value["source_verified"])
            self.assertIsNone(value["client_returncode"]); self.assertEqual(0, value["client_timeout_ms"])
        self.assertNotIn("destination", trace.json())

    def test_snapshots_are_immutable_historical_and_dicts_are_fresh(self):
        trace = s.SourceStreamTrace(63, clock_ns=Clock()); first = trace.snapshot(); wire = first.json()
        trace.source_verified(); trace.client_start(1); trace.client_timeout(); trace.position(63)
        self.assertEqual(wire, first.json()); self.assertFalse(first.source_verified)
        value = first.as_dict(); value["phase"] = PRIVATE; self.assertEqual(wire, first.json())
        with self.assertRaises(dataclasses.FrozenInstanceError): first.source_position = 63
        self.assertTrue(trace.snapshot().client_timed_out)

    def test_exact_integer_endpoints_and_bool_float_string_refusals(self):
        fields = {"version": (1, 1), "expected_bytes": (1, s.MAX_EXPECTED_BYTES),
                  "client_timeout_ms": (0, s.MAX_CLIENT_MS), "client_returncode": (-(1 << 31), (1 << 31) - 1),
                  "source_position": (0, 63), "elapsed_ms": (0, s.MAX_ELAPSED_MS)}
        for name, (low, high) in fields.items():
            for endpoint in {low, high}:
                value = initial(); value["source_verified"] = True; value["client_timeout_ms"] = 1
                value[name] = endpoint
                self.assertEqual(endpoint, s.parse_source_stream_trace(encode(value))[name])
            for invalid in [True, False, 1.0, "1", low - 1, high + 1]:
                value = initial(); value["source_verified"] = True; value["client_timeout_ms"] = 1; value[name] = invalid
                self.refuses(lambda: s.parse_source_stream_trace(encode(value)))
        for invalid in [0, -1, s.MAX_EXPECTED_BYTES + 1, True, 1.0, None]:
            self.refuses(lambda: s.SourceStreamTrace(invalid))
        self.assertEqual(s.MAX_EXPECTED_BYTES, s.SourceStreamTrace(s.MAX_EXPECTED_BYTES).snapshot().expected_bytes)

    def test_closed_boolean_types_and_minimal_client_correlations(self):
        for key in ["source_verified", "client_timed_out", "time_saturated"]:
            for invalid in [0, 1, None, "false", [], {}]:
                value = initial(); value[key] = invalid
                self.refuses(lambda: s.parse_source_stream_trace(encode(value)))
        for changes in [{"client_returncode": 0}, {"client_timed_out": True},
                        {"client_timeout_ms": 1}, {"source_verified": True, "client_returncode": 0},
                        {"source_verified": True, "client_timeout_ms": 1, "client_returncode": 0, "client_timed_out": True},
                        {"time_saturated": True}]:
            value = initial() | changes
            self.refuses(lambda: s.parse_source_stream_trace(encode(value)))
        for code in [None, -(1 << 31), 0, 7, (1 << 31) - 1]:
            value = initial() | {"source_verified": True, "client_timeout_ms": 1, "client_returncode": code}
            self.assertEqual(code, s.parse_source_stream_trace(encode(value))["client_returncode"])

    def test_single_client_state_mutations_refuse_before_changing_history(self):
        trace = s.SourceStreamTrace(63, clock_ns=Clock())
        self.refuses(lambda: trace.client_start(1)); self.refuses(lambda: trace.client_return(0)); self.refuses(trace.client_timeout)
        self.refuses(lambda: trace.phase("GATE")); self.refuses(lambda: trace.position(64)); self.refuses(lambda: trace.position(True))
        trace.source_verified()
        for invalid in [0, 150001, True, 1.5, None]: self.refuses(lambda: trace.client_start(invalid))
        trace.client_start(1); before = trace.snapshot().json()
        self.refuses(lambda: trace.client_start(2)); self.assertEqual(before, trace.snapshot().json())
        trace.client_return(-1)
        self.refuses(trace.client_timeout); self.refuses(lambda: trace.client_return(0))
        self.assertEqual(-1, trace.snapshot().client_returncode)
        other = s.SourceStreamTrace(63, clock_ns=Clock()); other.source_verified(); other.client_start(150000); other.client_timeout()
        self.refuses(other.client_timeout); self.refuses(lambda: other.client_return(0)); self.assertTrue(other.snapshot().client_timed_out)

    def test_elapsed_exact_cap_overflow_stickiness_regression_and_narrowing(self):
        clock = Clock(); clock.value = -100
        trace = s.SourceStreamTrace(63, clock_ns=clock)
        for raw, ms, saturated in [(-1000, 0, False), (999899, 0, False), (999900, 1, False),
                                   (180000000000 - 100, 180000, False), (180000000001 - 100, 180000, True),
                                   (-1000, 180000, True), (10 ** 100, 180000, True)]:
            clock.value = raw; value = trace.snapshot()
            self.assertEqual((ms, saturated), (value.elapsed_ms, value.time_saturated))
            self.assertEqual(value.as_dict(), s.parse_source_stream_trace(value.json().encode()))

    def test_clock_errors_are_closed_and_serialization_errors_are_not_fabricated_records(self):
        def hostile(): raise RuntimeError(PRIVATE)
        self.refuses(lambda: s.SourceStreamTrace(63, clock_ns=hostile))
        for value in [True, 1.0, None, PRIVATE]: self.refuses(lambda: s.SourceStreamTrace(63, clock_ns=lambda: value))
        clock = Clock(); trace = s.SourceStreamTrace(63, clock_ns=clock)
        trace._clock_ns = hostile
        self.refuses(trace.snapshot)
        with patch.object(s.json, "dumps", side_effect=RuntimeError(PRIVATE)):
            self.refuses(lambda: s.SourceStreamSnapshot(s.StreamPhase.GATE, 63).json())
        # The root call site owns these guards; the trace never catches/replaces a
        # core result or exception because it has no core-operation callback API.
        original = AssertionError("original synthetic failure")
        observed = None
        try:
            try: raise original
            except BaseException:
                try: trace.json()
                except BaseException: pass
                raise
        except BaseException as failure: observed = failure
        self.assertIs(original, observed); self.assertEqual("original synthetic failure", str(observed))

    def test_json_unknown_missing_private_duplicate_nonfinite_unicode_and_size_refusals(self):
        for key in initial():
            value = initial(); del value[key]; self.refuses(lambda: s.parse_source_stream_trace(encode(value)))
        for extra in ["path", "uid", "argv", "hash", "error", "message", "stack", "destination_verified", "remote_exit_status_known"]:
            self.refuses(lambda: s.parse_source_stream_trace(encode(initial() | {extra: PRIVATE})))
        value = encode(initial())
        for raw in [b"", value[:-1], b"[]", b"null", b"{!}", value + b"x", value.replace(b'"version":1', b'"version":true'),
                    value.replace(b'"version":1', b'"version":1,"version":1'),
                    value.replace(b'"version":1', b'"version":1,"\\u0076ersion":1'),
                    value.replace(b'"expected_bytes":63', b'"expected_bytes":NaN'),
                    value.replace(b'"expected_bytes":63', b'"expected_bytes":Infinity'),
                    value.replace(b'"expected_bytes":63', b'"expected_bytes":1e99999'),
                    value.replace(b'GATE', "雪".encode()), b" " * (s.MAX_BYTES - len(s.PREFIX) + 1)]:
            self.refuses(lambda: s.parse_source_stream_trace(raw))
        self.refuses(lambda: s.SourceStreamSnapshot("GATE", 63))
        self.refuses(lambda: s.SourceStreamSnapshot(s.StreamPhase.GATE, 63, time_saturated=True))

    def test_one_exact_prefixed_line_lf_crlf_and_optional_absence(self):
        payload = s.SourceStreamSnapshot(s.StreamPhase.CLIENT, 63, True, 150000, None, True, 32, 150001).json()
        legacy = '{"version":1,"status":"stream_failed","remote_exit_status_known":false}'
        for ending in ["\n", "\r\n"]:
            raw = (s.PREFIX + payload + ending + legacy + ending).encode()
            self.assertEqual(s.parse_source_stream_trace(payload.encode()), s.extract_source_stream_trace(raw))
        for raw in [b"", (legacy + "\n").encode(), b'\n{"legacy":"unchanged"}\n']:
            self.assertIsNone(s.extract_source_stream_trace(raw))

    def test_extractor_refuses_spoofs_duplicates_controls_suffixes_and_capture_overflow(self):
        record = (s.PREFIX + s.SourceStreamSnapshot(s.StreamPhase.GATE, 63).json()).encode()
        for raw in [record + b"\n" + record, b" " + record, b"x" + record, record + b"x", record + b"\r",
                    record + b"\v", record + b"\f", record + b"\r\r\n", record + b"\n" + s.PREFIX[:-1].encode(),
                    s.PREFIX[:-1].encode(), b'"' + record + b'"', b"x" * (s.MAX_CAPTURE + 1), record + "雪".encode()]:
            self.refuses(lambda: s.extract_source_stream_trace(raw))

    def test_dense_wire_remains_closed_ascii_and_within_prefix_inclusive_cap(self):
        snapshot = s.SourceStreamSnapshot(s.StreamPhase.LEASE_POSTCHECK, s.MAX_EXPECTED_BYTES,
            True, 150000, -(1 << 31), False, s.MAX_EXPECTED_BYTES, 180000, True)
        raw = snapshot.json().encode("ascii")
        self.assertLessEqual(len(s.PREFIX) + len(raw), 1024)
        self.assertEqual(set(initial()), set(s.parse_source_stream_trace(raw)))
        self.assertEqual(snapshot.as_dict(), s.extract_source_stream_trace(s.PREFIX.encode() + raw + b"\n"))
        for private in ["path", "uid", "argv", "model", "hash", "cause", "stack", "destination", "remote_exit"]:
            self.assertNotIn(private, snapshot.json())

    def test_module_import_does_not_open_files_or_accept_arbitrary_callback_writers(self):
        code = SPEC.loader.get_code(SPEC.name)
        probe = types.ModuleType("source_stream_inert_probe"); sys.modules[probe.__name__] = probe
        try:
            with patch("builtins.open", side_effect=AssertionError(PRIVATE)), patch.object(Path, "open", side_effect=AssertionError(PRIVATE)):
                exec(code, probe.__dict__)
        finally: del sys.modules[probe.__name__]
        for name in ["open", "Path", "subprocess", "main"]: self.assertFalse(hasattr(s, name))


if __name__ == "__main__":
    unittest.main()
