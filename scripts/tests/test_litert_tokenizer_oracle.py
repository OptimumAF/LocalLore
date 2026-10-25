"""Original stdlib metadata controls; no model, tokenizer, SDK or native imports.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import unittest
from unittest import mock
from benchmarks import litert_tokenizer_oracle as o


def varint(value):
    data = bytearray()
    while value > 127:
        data.append((value & 127) | 128); value >>= 7
    return bytes(data + bytes([value]))


def msg(number, raw):
    return varint((number << 3) | 2) + varint(len(raw)) + raw


def ids(*values):
    return msg(1, msg(1, b"".join(varint(x) for x in values)))


def text(value):
    return msg(2, value.encode("utf-8"))


def hf(vocab=None, added=None, kind="BPE"):
    return json.dumps({"model": {"type": kind, "vocab": {"a": 0, "<eos>": 1, "\u2581b": 2} if vocab is None else vocab},
                       "added_tokens": [] if added is None else added}).encode()


class TokenizerOracleTests(unittest.TestCase):
    def refuses(self, raw, reason=None):
        context = self.assertRaises(o.TokenizerOracleRefused)
        with context:
            o.parse_stop_metadata(raw)
        if reason:
            self.assertEqual(context.exception.reason, reason)
        self.assertNotIn("private", str(context.exception))

    def test_packed_unpacked_order_exact_string_and_first_singleton(self):
        unpacked = msg(1, b"\x08\x00\x08\x02")
        raw = msg(1, ids(0)) + msg(2, unpacked) + msg(2, text("<eos>")) + msg(2, ids(2))
        parsed = o.parse_stop_metadata(raw)
        self.assertEqual(parsed.start.ids, (0,))
        self.assertEqual(parsed.stops[0].ids, (0, 2))
        self.assertEqual(o.resolve_stops(parsed, o.hf_raw_vocabulary(hf())), (1, ((0, 2), (1,), (2,))))

    def test_unknown_supported_wire_types_are_skipped_without_recursion(self):
        unknown = b"\x28\x01\x31" + b"x" * 8 + msg(9, b"arbitrary") + b"\x55" + b"y" * 4
        self.assertEqual(o.parse_stop_metadata(unknown + msg(2, ids(1))).stops[0].ids, (1,))

    def test_malformed_lengths_tags_varints_groups_and_empty_metadata_refuse(self):
        for raw in (b"", b"\x00", b"\x0b", b"\x0c", b"\x0f", b"\x80" * 11,
                    b"\x80" * 9 + b"\x02", b"\x12\xff", b"\x12\x08\x0a", b"\x0a\x00", msg(2, b"")):
            with self.subTest(raw=raw): self.refuses(raw)
        self.refuses(b"x" * (o.MAX_METADATA + 1), "metadata_bounds")

    def test_duplicate_start_or_oneof_and_wrong_wire_are_not_last_wins(self):
        for raw in (msg(1, ids(0)) * 2 + msg(2, ids(1)), msg(2, ids(1) + text("private")),
                    msg(2, text("private") * 2), b"\x10\x01", msg(2, msg(1, b"\x0dxxxx"))):
            with self.subTest(raw=raw): self.refuses(raw)

    def test_negative_int32_overlong_ids_stop_and_field_bounds(self):
        self.refuses(msg(2, ids(2 ** 64 - 1)), "token_ids")
        self.refuses(msg(2, ids(*range(o.MAX_IDS + 1))), "token_ids")
        self.refuses(msg(2, ids(1)) * (o.MAX_STOPS + 1), "stop_bounds")
        with mock.patch.object(o, "MAX_FIELDS", 2): self.refuses(msg(2, ids(1)), "protobuf")
        self.refuses(msg(2, msg(2, b"\xff")), "token_union")

    def test_eos_has_no_guessed_string_or_empty_stop_fallback(self):
        tokens = o.hf_raw_vocabulary(hf())
        with self.assertRaisesRegex(o.TokenizerOracleRefused, "tokenization_required"):
            o.resolve_stops(o.parse_stop_metadata(msg(2, text("private"))), tokens)
        with self.assertRaisesRegex(o.TokenizerOracleRefused, "eos"):
            o.resolve_stops(o.parse_stop_metadata(msg(2, ids(9))), tokens)
        with self.assertRaisesRegex(o.TokenizerOracleRefused, "eos"):
            o.resolve_stops(o.parse_stop_metadata(msg(2, ids(0, 2))), tokens)
        parsed = o.parse_stop_metadata(msg(2, ids()) + msg(2, ids(1)))
        self.assertEqual(o.resolve_stops(parsed, tokens), (1, ((1,),)))

    def test_raw_piece_strings_are_not_decoded_or_special_classified(self):
        tokens = o.hf_raw_vocabulary(hf())
        self.assertEqual(tokens, (b"a", b"<eos>", "\u2581b".encode()))
        report = o.vocabulary_report(tokens)
        self.assertEqual(report["pieces_with_ascii_space"], 0)
        self.assertNotIn("<eos>", str(report)); self.assertNotIn("\u2581", str(report))
        self.assertEqual(report, o.vocabulary_report(tokens))
        self.assertEqual(o.vocabulary_report((b" ", b"\t", b"\n"))["pieces_with_ascii_space"], 1)

    def test_added_tokens_exact_overlay_and_contiguous_addition(self):
        tokens = o.hf_raw_vocabulary(hf(added=[{"id": 1, "content": "<eos>"}, {"id": 3, "content": "new"}]))
        self.assertEqual(tokens[-1], b"new")
        self.assertEqual(len(tokens), 4)

    def test_vocab_holes_conflicts_booleans_duplicates_and_private_errors(self):
        bad = [hf({"a": 0, "b": 2}), hf({"a": True}), hf({"a": 0, "b": 0}),
               hf(added=[{"id": 1, "content": "private"}]), hf(added=[{"id": 3, "content": "a"}]),
               hf(added=[{"id": 1, "content": "<eos>"}] * 2), hf(added=[{"id": True, "content": "private"}]),
               hf(kind="unsupported"), b'{"model":{},"model":{}}', b'{"model":{"score":NaN}}',
               b'{"model":{"type":"BPE","vocab":{"\\ud800":0}}}']
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(o.TokenizerOracleRefused) as error:
                o.hf_raw_vocabulary(raw)
            self.assertNotIn("private", str(error.exception))

    def test_unigram_scores_are_finite_and_ids_stay_in_index_order(self):
        self.assertEqual(o.hf_raw_vocabulary(hf([["a", -1.0], ["b", 0]], kind="Unigram")), (b"a", b"b"))
        for vocab in ([["a", True]], [["a", "private"]], [["a", 0], ["a", 1]], [["a", 10 ** 1000]]):
            with self.assertRaises(o.TokenizerOracleRefused): o.hf_raw_vocabulary(hf(vocab, kind="Unigram"))
        with self.assertRaises(o.TokenizerOracleRefused): o.strict_json(b'{"private":1e9999}')

    def test_piece_and_vocab_caps_refuse_before_native_or_any_file_use(self):
        with mock.patch.object(o, "MAX_PIECE", 2), self.assertRaises(o.TokenizerOracleRefused):
            o.hf_raw_vocabulary(hf())
        with mock.patch.object(o, "MAX_VOCAB", 2), self.assertRaises(o.TokenizerOracleRefused):
            o.hf_raw_vocabulary(hf())
        with self.assertRaises(o.TokenizerOracleRefused): o.strict_json(b"[] trailing")

    def test_sentencepiece_raw_pieces_keep_order_without_normalization(self):
        raw = msg(1, msg(1, b"<eos>") + b"\x15\x00\x00\x00\x00") + msg(1, msg(1, "\u2581word".encode()))
        self.assertEqual(o.sp_raw_vocabulary(raw), (b"<eos>", "\u2581word".encode()))
        metadata = o.parse_stop_metadata(msg(2, text("<eos>")))
        self.assertEqual(o.resolve_stops(metadata, o.sp_raw_vocabulary(raw)), (0, ((0,),)))
        self.assertEqual(o.vocabulary_report(o.sp_raw_vocabulary(raw))["pieces_with_ascii_space"], 0)

    def test_sentencepiece_bad_wire_duplicates_missing_and_utf8_refuse(self):
        for raw in (b"\x08\x01", msg(1, b""), msg(1, msg(1, b"private") * 2),
                    msg(1, msg(1, b"a")) * 2, msg(1, msg(1, b"\xff"))):
            with self.subTest(raw=raw), self.assertRaises(o.TokenizerOracleRefused): o.sp_raw_vocabulary(raw)
        with mock.patch.object(o, "MAX_VOCAB", 1), self.assertRaises(o.TokenizerOracleRefused):
            o.sp_raw_vocabulary(msg(1, msg(1, b"a")) + msg(1, msg(1, b"b")))


if __name__ == "__main__": unittest.main()
