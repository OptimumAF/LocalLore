"""Original in-memory selected-container adversaries; no model/native/filesystem IO.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import dataclasses
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch
import zlib

SPEC = importlib.util.spec_from_file_location("tokenizer_metadata_under_test",
    Path(__file__).resolve().parents[2] / "benchmarks/litert_tokenizer_metadata.py")
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)

ORIGINAL = b'{"model":{"type":"BPE","vocab":{"original":0}},"added_tokens":[]}'
PRIVATE = "ORIGINAL_PRIVATE_ERROR_CANARY"
_UNSET = object()


def hf(data=ORIGINAL, declared=None):
    return struct.pack("<Q", len(data) if declared is None else declared) + zlib.compress(data)


class Directory:
    """Small forward-offset builder of original fixtures, not a production writer."""
    def __init__(self, negative=False, shared=False):
        self.data = bytearray(4)
        self.negative, self.shared, self.vtables = negative, shared, {}
        self.strings, self.item_fields, self.item_vectors = [], [], []

    def align(self, width):
        self.data.extend(b"\0" * (-len(self.data) % width))

    def table(self, widths, omit=()):
        offsets, cursor = [], 4
        for index, width in enumerate(widths):
            if index in omit:
                offsets.append(0)
                continue
            cursor += -cursor % width
            offsets.append(cursor)
            cursor += width
        size = cursor + (-cursor % 4)
        vt_bytes = struct.pack("<HH", 4 + 2 * len(widths), size) + struct.pack("<" + "H" * len(widths), *offsets)
        key = (tuple(widths), tuple(offsets))
        vt = self.vtables.get(key) if self.shared else None
        if vt is None and not self.negative:
            self.align(2); vt = len(self.data); self.data.extend(vt_bytes)
        self.align(8); pos = len(self.data); self.data.extend(b"\0" * size)
        if vt is None:
            self.align(2); vt = len(self.data); self.data.extend(vt_bytes)
        self.vtables[key] = vt
        struct.pack_into("<i", self.data, pos, pos - vt)
        return pos, [pos + value if value else None for value in offsets]

    def reference(self, field, target):
        struct.pack_into("<I", self.data, field, target - field)

    def vector(self, count):
        self.align(4); pos = len(self.data)
        self.data.extend(struct.pack("<I", count) + b"\0" * (4 * count))
        return pos

    def string(self, text):
        value = text.encode("utf-8")
        self.align(4); pos = len(self.data)
        self.data.extend(struct.pack("<I", len(value)) + value + b"\0")
        self.strings.append(pos)
        return pos

    def items(self, field, entries):
        vec = self.vector(len(entries)); self.reference(field, vec); self.item_vectors.append(vec)
        for index, (key, value, discriminator) in enumerate(entries):
            pos, fields = self.table((4, 1, 4)); self.item_fields.append(fields)
            self.reference(vec + 4 + index * 4, pos)
            self.reference(fields[0], self.string(key)); self.data[fields[1]] = discriminator
            width = {1: 1, 2: 1, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 8: 1, 9: 4, 10: 8, 11: 8, 12: 8}[discriminator]
            value_pos, value_fields = self.table((width,)); self.reference(fields[2], value_pos)
            if discriminator == 9:
                self.reference(value_fields[0], self.string(value))
            else:
                fmt = {1: "B", 2: "b", 3: "H", 4: "h", 5: "I", 6: "i", 7: "f", 8: "B", 10: "Q", 11: "q", 12: "d"}[discriminator]
                struct.pack_into("<" + fmt, self.data, value_fields[0], value)


class Container:
    def __init__(self, sections=None, negative=False, shared=False, version=(1, 7, 0), system=None):
        self.specs = sections if sections is not None else [
            (6, hf(), []), (5, b"\x0a\x02\x08\x01", []),
            (3, b"ORIGINAL_GRAPH_DO_NOT_READ", []), (7, b"ORIGINAL_WEIGHTS_DO_NOT_READ", [])]
        self.fb = Directory(negative, shared)
        self.root, root_fields = self.fb.table((4, 4), omit=(0,) if system is None else ())
        self.fb.reference(0, self.root)
        if system is not None:
            pos, fields = self.fb.table((4,)); self.fb.reference(root_fields[0], pos)
            self.fb.items(fields[0], system)
        self.section_metadata, sm = self.fb.table((4,)); self.fb.reference(root_fields[1], self.section_metadata)
        self.vector = self.fb.vector(len(self.specs)); self.fb.reference(sm[0], self.vector)
        self.tables, self.fields = [], []
        for index, (kind, payload, entries) in enumerate(self.specs):
            pos, fields = self.fb.table((4, 8, 8, 1), omit=(0,) if entries is None else ())
            self.tables.append(pos); self.fields.append(fields)
            self.fb.reference(self.vector + 4 + index * 4, pos); self.fb.data[fields[3]] = kind
            if entries is not None:
                self.fb.items(fields[0], entries)
        self.header_end = 32 + len(self.fb.data)
        self.ranges, cursor = [], self.header_end
        for index, (_, payload, _) in enumerate(self.specs):
            begin = cursor + (-cursor % m.BLOCK_SIZE); end = begin + len(payload)
            self.ranges.append((begin, end)); cursor = end
            struct.pack_into("<Q", self.fb.data, self.fields[index][1], begin)
            struct.pack_into("<Q", self.fb.data, self.fields[index][2], end)
        self.data = bytearray(cursor)
        self.data[:32] = b"LITERTLM" + struct.pack("<III", *version) + b"\0" * 4 + struct.pack("<Q", self.header_end)
        self.data[32:self.header_end] = self.fb.data
        for (_, payload, _), (begin, end) in zip(self.specs, self.ranges):
            self.data[begin:end] = payload

    def number(self, offset, fmt, value):
        struct.pack_into("<" + fmt, self.data, 32 + offset, value)

    def read(self):
        stream = ReadRecorder(self.data)
        return m.extract_tokenizer_metadata(stream, len(self.data)), stream


class ReadRecorder(io.BytesIO):
    def __init__(self, data):
        super().__init__(data); self.reads = []

    def read(self, count=-1):
        assert 0 <= count <= 65536, "Unbounded reader request"
        start = self.tell(); value = super().read(count)
        self.reads.append((start, start + len(value)))
        return value


class TokenizerMetadataTest(unittest.TestCase):
    def refused(self, container, reason=None, size=_UNSET):
        stream = ReadRecorder(container.data)
        with self.assertRaises(m.TokenizerMetadataRefused) as caught:
            m.extract_tokenizer_metadata(stream, len(container.data) if size is _UNSET else size)
        if reason is not None:
            self.assertEqual(reason, caught.exception.reason)
        self.assertIn(str(caught.exception), {item.value for item in m.RefusalReason})
        self.assertNotIn(PRIVATE, str(caught.exception)); self.assertIsNone(caught.exception.__context__)
        return stream

    def header_only(self, stream, container):
        self.assertTrue(all(end <= container.header_end for _, end in stream.reads))

    def test_hf_exact_original_bytes_hashes_and_only_selected_payload_reads(self):
        c = Container(); value, stream = c.read()
        self.assertEqual((1, 7, 0), value.container_version); self.assertEqual(c.header_end, value.header_end)
        self.assertEqual(m.TokenizerKind.HF_JSON, value.selected_kind); self.assertEqual(m.Selection.UNTYPED, value.selection)
        self.assertEqual(hf(), value.original_payload); self.assertEqual(ORIGINAL, value.decoded_json)
        self.assertEqual(b"\x0a\x02\x08\x01", value.llm_metadata)
        self.assertEqual(hashlib.sha256(hf()).hexdigest(), value.original_sha256)
        self.assertEqual(hashlib.sha256(ORIGINAL).hexdigest(), value.decoded_sha256)
        self.assertEqual(hashlib.sha256(value.llm_metadata).hexdigest(), value.llm_sha256)
        for begin, end in c.ranges[2:]:
            self.assertFalse(any(max(begin, left) < min(end, right) for left, right in stream.reads))
        for left, right in stream.reads:
            self.assertTrue(right <= c.header_end or any(left >= start and right <= end for start, end in c.ranges[:2]))
        self.assertNotIn(ORIGINAL.decode(), repr(value)); self.assertNotIn("BPE", repr(value))
        self.assertTrue(all(not item.repr for item in dataclasses.fields(value)
                            if item.name in ("original_payload", "decoded_json", "llm_metadata")))
        with self.assertRaises(dataclasses.FrozenInstanceError): value.header_end = 0
        with self.assertRaises(dataclasses.FrozenInstanceError): value.tokenizer_range.end = 0

    def test_typed_ascii_case_selection_ignores_audio_without_reading_it(self):
        c = Container([(6, hf(), [("MODEL_TYPE", "TF_LITE_PREFILL_DECODE", 9)]),
                       (6, b"NOT_DEFLATE_DO_NOT_READ", [("model_type", "tf_lite_audio_encoder", 9)]),
                       (5, b"metadata", [])])
        value, stream = c.read(); self.assertEqual(m.Selection.TYPED, value.selection)
        a, b = c.ranges[1]; self.assertFalse(any(max(a, left) < min(b, right) for left, right in stream.reads))

    def test_untyped_fallback_is_not_audio_or_hf_fallback_for_sentencepiece(self):
        raw = b"ORIGINAL_SENTENCEPIECE_PROTO_NOT_JSON"
        c = Container([(4, raw, None), (5, b"", None), (6, b"unread", [("model_type", "audio", 9)])])
        value, stream = c.read()
        self.assertEqual(m.TokenizerKind.SENTENCEPIECE, value.selected_kind); self.assertIsNone(value.decoded_json)
        self.assertIsNone(value.decoded_sha256); self.assertEqual(raw, value.original_payload); self.assertEqual(b"", value.llm_metadata)
        a, b = c.ranges[2]; self.assertFalse(any(max(a, left) < min(b, right) for left, right in stream.reads))

    def test_major_minor_policy_and_explicit_patch_all_supported_versions(self):
        for minor in range(8):
            value, _ = Container(version=(1, minor, 4294967295)).read()
            self.assertEqual((1, minor, 4294967295), value.container_version)
        for version in [(0, 7, 0), (2, 7, 0), (1, 8, 0), (1, 4294967295, 0)]:
            c = Container(version=version); self.header_only(self.refused(c, m.RefusalReason.VERSION), c)

    def test_input_fixed_header_magic_endian_and_bounded_header_before_allocation(self):
        c = Container()
        for size in [True, False, None, 31, -1, 1.0, 1 << 63]:
            self.assertEqual([], self.refused(c, m.RefusalReason.INPUT, size).reads)
        c.data[0] = 0; self.refused(c, m.RefusalReason.HEADER)
        for end in [0, 32, 35, len(c.data) + 1]:
            c = Container(); struct.pack_into("<Q", c.data, 24, end); self.refused(c, m.RefusalReason.HEADER)
        c = Container(); struct.pack_into(">Q", c.data, 24, c.header_end); self.refused(c, m.RefusalReason.HEADER)
        c = Container(); struct.pack_into("<Q", c.data, 24, m.MAX_HEADER + 1)
        stream = self.refused(c, m.RefusalReason.LIMIT, m.MAX_HEADER + 1)
        self.assertEqual([(0, 32)], stream.reads)

    def test_negative_and_shared_vtables_are_valid_not_assumed_backward_only(self):
        for negative, shared in [(True, False), (True, True), (False, True)]:
            c = Container(negative=negative, shared=shared)
            value, _ = c.read(); self.assertEqual(ORIGINAL, value.decoded_json)
            if negative: self.assertLess(struct.unpack_from("<i", c.data, 32 + c.root)[0], 0)

    def test_root_vtable_object_reference_vector_and_string_corruptions_stop_before_payload(self):
        changes = [(0, "I", 0), (0, "I", 0xffffffff), (0, "I", 5)]
        for offset, fmt, value in changes:
            c = Container(); c.number(offset, fmt, value); self.header_only(self.refused(c, m.RefusalReason.FLATBUFFER), c)
        for field in ["vtable", "object", "field", "ref", "vector", "string", "nul", "utf8"]:
            c = Container(system=[("original", "private", 9)])
            if field == "vtable": c.number(c.root, "i", 0x7fffffff)
            elif field == "object":
                vt = c.root - struct.unpack_from("<i", c.data, 32 + c.root)[0]; c.number(vt + 2, "H", 65535)
            elif field == "field":
                vt = c.root - struct.unpack_from("<i", c.data, 32 + c.root)[0]; c.number(vt + 4, "H", 1)
            elif field == "ref": c.number(c.fb.item_fields[0][0], "I", 0xffffffff)
            elif field == "vector": c.number(c.vector + 4, "I", 0xffffffff)
            elif field == "string": c.number(c.fb.strings[0], "I", 0xffffffff)
            elif field == "nul":
                string = 32 + c.fb.strings[0]; length, = struct.unpack_from("<I", c.data, string); c.data[string + 4 + length] = 1
            else: c.data[32 + c.fb.strings[0] + 4] = 0xff
            self.header_only(self.refused(c, m.RefusalReason.FLATBUFFER), c)

    def test_omitted_optional_items_and_scalar_defaults_are_valid(self):
        c = Container([(6, hf(), None), (5, b"metadata", None), (0, b"unselected", None)])
        # Default NONE data_type is omitted via a zero vtable slot.
        vt = c.tables[2] - struct.unpack_from("<i", c.data, 32 + c.tables[2])[0]
        c.number(vt + 4 + 3 * 2, "H", 0)
        value, _ = c.read(); self.assertEqual(0, value.sections[2].data_type)
        scalar_cases = [("u8", 255, 1), ("i8", -128, 2), ("u16", 65535, 3), ("i16", -32768, 4),
                        ("u32", 4294967295, 5), ("i32", -2147483648, 6), ("float", 1.25, 7),
                        ("bool", 1, 8), ("text", "雪", 9), ("u64", (1 << 64) - 1, 10), ("i64", -(1 << 63), 11), ("double", 1.5, 12)]
        value, _ = Container(system=scalar_cases).read(); self.assertEqual(ORIGINAL, value.decoded_json)

    def test_required_tables_vectors_union_discriminators_and_nonfinite_scalars_refuse(self):
        for kind in [0, 13, 255]:
            c = Container(system=[("original", "value", 9)]); c.data[32 + c.fb.item_fields[0][1]] = kind
            self.header_only(self.refused(c, m.RefusalReason.FLATBUFFER), c)
        for key, val, kind in [("bool", 2, 8), ("float", float("nan"), 7), ("double", float("inf"), 12)]:
            c = Container(system=[(key, val, kind)]); self.header_only(self.refused(c, m.RefusalReason.FLATBUFFER), c)
        c = Container(system=[("original", "value", 9)])
        c.number(c.fb.item_fields[0][2], "I", 0); self.header_only(self.refused(c, m.RefusalReason.FLATBUFFER), c)
        c = Container(); c.number(c.section_metadata, "i", 0); self.header_only(self.refused(c), c)

    def test_omitted_union_scalar_defaults_and_string_default_are_not_guessed(self):
        for key, val, kind in [("unknown", 55, 5), ("unknown", "value", 9), ("model_type", "tf_lite_prefill_decode", 9)]:
            c = Container([(6, hf(), [(key, val, kind)]), (5, b"meta", [])])
            pointer = c.fb.item_fields[0][2]
            target = pointer + struct.unpack_from("<I", c.data, 32 + pointer)[0]
            vt = target - struct.unpack_from("<i", c.data, 32 + target)[0]
            c.number(vt + 4, "H", 0)
            if key == "model_type": self.header_only(self.refused(c, m.RefusalReason.SELECTION), c)
            else: self.assertEqual(ORIGINAL, c.read()[0].decoded_json)
        for slot in [0, 2]:
            c = Container(system=[("original", "value", 9)])
            key_table = c.fb.item_fields[0][0] - 4
            vt = key_table - struct.unpack_from("<i", c.data, 32 + key_table)[0]
            c.number(vt + 4 + slot * 2, "H", 0)
            self.header_only(self.refused(c, m.RefusalReason.FLATBUFFER), c)

    def test_directory_caps_and_duplicate_keys_are_checked_before_payloads(self):
        c = Container(); c.number(c.vector, "I", 257); self.header_only(self.refused(c, m.RefusalReason.LIMIT), c)
        c = Container(system=[]); c.number(c.fb.item_vectors[0], "I", 65); self.header_only(self.refused(c, m.RefusalReason.LIMIT), c)
        for entries in [[("private", "one", 9), ("private", "two", 9)],
                        [("model_type", "tf_lite_prefill_decode", 9), ("MODEL_TYPE", "audio", 9)]]:
            c = Container([(6, hf(), entries), (5, b"metadata", [])]); self.header_only(self.refused(c), c)

    def test_unknown_utf8_keys_are_bounded_but_do_not_become_model_type(self):
        value, _ = Container([(6, hf(), [("模型", "tf_lite_prefill_decode", 9)]), (5, b"metadata", [])]).read()
        self.assertEqual(m.Selection.UNTYPED, value.selection)
        value, _ = Container(system=[("model_type", "非ASCII_SYSTEM_IGNORED", 9),
                                      ("MODEL_TYPE", 1, 5)]).read()
        self.assertEqual(m.Selection.UNTYPED, value.selection)
        for entry in [("model_type", "非ASCII", 9), ("model_type", 1, 5)]:
            c = Container([(6, hf(), [entry]), (5, b"metadata", [])]); self.header_only(self.refused(c, m.RefusalReason.SELECTION), c)

    def test_ambiguous_missing_sp_hf_duplicate_and_typed_metadata_refuse(self):
        token = (6, hf(), [])
        variants = [[token, token], [token, (4, b"SP", [])],
                    [token, (6, hf(), [("model_type", "tf_lite_prefill_decode", 9)])],
                    [(6, hf(), [("model_type", "audio", 9)])], []]
        for tokens in variants:
            c = Container(tokens + [(5, b"meta", [])]); self.header_only(self.refused(c, m.RefusalReason.SELECTION), c)
        for metadata in [[], [(5, b"a", []), (5, b"b", [])], [(5, b"meta", [("model_type", "audio", 9)])]]:
            c = Container([token] + metadata); self.header_only(self.refused(c, m.RefusalReason.SELECTION), c)

    def test_ranges_alignment_header_alias_overlap_reversed_eof_and_unknown_type_refuse(self):
        for change in ["alignment", "header", "overlap", "reverse", "eof", "type"]:
            c = Container()
            if change == "alignment": c.number(c.fields[0][1], "Q", c.ranges[0][0] + 1)
            elif change == "header": c.number(c.fields[0][1], "Q", 0)
            elif change == "overlap": c.number(c.fields[1][1], "Q", c.ranges[0][0])
            elif change == "reverse": c.number(c.fields[0][2], "Q", c.ranges[0][0] - 1)
            elif change == "eof": c.number(c.fields[0][2], "Q", len(c.data) + 1)
            else: c.number(c.fields[0][3], "B", 12)
            self.header_only(self.refused(c, m.RefusalReason.SECTION), c)

    def test_exact_aligned_end_can_equal_next_begin_without_extra_block(self):
        c = Container([(4, b"S" * m.BLOCK_SIZE, []), (5, b"meta", [])])
        self.assertEqual(c.ranges[0][1], c.ranges[1][0]); value, _ = c.read()
        self.assertEqual(b"S" * m.BLOCK_SIZE, value.original_payload)

    def test_payload_caps_are_validated_before_selected_reads(self):
        c = Container()
        with patch.object(m, "MAX_COMPRESSED", len(hf()) - 1): self.header_only(self.refused(c, m.RefusalReason.LIMIT), c)
        with patch.object(m, "MAX_METADATA", 3): self.header_only(self.refused(c, m.RefusalReason.LIMIT), c)
        with patch.object(m, "MAX_COMPRESSED", len(hf())), patch.object(m, "MAX_METADATA", 4):
            self.assertEqual(ORIGINAL, c.read()[0].decoded_json)
        self.assertEqual((4194304, 256, 64, 1048576, 33554432, 134217728),
            (m.MAX_HEADER, m.MAX_SECTIONS, m.MAX_ITEMS, m.MAX_METADATA, m.MAX_COMPRESSED, m.MAX_DECODED))

    def test_hf_prefix_lengths_stream_end_truncation_trailing_concat_and_zlib_errors(self):
        variants = [b"", b"1234567", struct.pack("<Q", len(ORIGINAL) - 1) + zlib.compress(ORIGINAL),
                    struct.pack("<Q", len(ORIGINAL) + 1) + zlib.compress(ORIGINAL), hf()[:-1], hf() + b"x",
                    hf() + zlib.compress(b"{}"), struct.pack("<Q", 2) + b"not-zlib", struct.pack(">Q", len(ORIGINAL)) + zlib.compress(ORIGINAL)]
        for payload in variants:
            c = Container([(6, payload, []), (5, b"unread_metadata", [])])
            stream = self.refused(c)
            a, b = c.ranges[1]; self.assertFalse(any(max(a, left) < min(b, right) for left, right in stream.reads))
        c = Container([(6, hf(declared=m.MAX_DECODED + 1), []), (5, b"meta", [])])
        self.refused(c, m.RefusalReason.LIMIT)

    def test_streaming_deflate_bomb_cannot_exceed_declared_or_policy_length(self):
        c = Container([(6, hf(b" " * 200000, declared=2), []), (5, b"meta", [])])
        self.refused(c, m.RefusalReason.DEFLATE)
        with patch.object(m, "MAX_DECODED", len(ORIGINAL)):
            self.assertEqual(ORIGINAL, Container().read()[0].decoded_json)
        with patch.object(m, "MAX_DECODED", len(ORIGINAL) - 1):
            self.refused(Container(), m.RefusalReason.LIMIT)
        large = json.dumps({"original": "x" * 200000}, separators=(",", ":")).encode()
        self.assertEqual(large, Container([(6, hf(large), []), (5, b"meta", [])]).read()[0].decoded_json)

    def test_hf_json_strict_utf8_duplicates_nonfinite_surrogates_and_complete_root(self):
        for data in [b'{"a":1,"a":2}', b'{"a":1,"\\u0061":2}', b'{"a":NaN}', b'{"a":Infinity}',
                     b'{"a":1e999999}', b'{"a":"\\ud800"}', b'{"\\udfff":0}', b'{"a":"\xff"}',
                     b'{!}', b'{} trailing', b'[]', b'null', b'\xef\xbb\xbf{}', b'{"a":1,}']:
            c = Container([(6, hf(data), []), (5, b"meta", [])]); self.refused(c, m.RefusalReason.JSON)
        valid = '{"雪":"line\\n\\uD83D\\uDE00","bool":true,"number":1.25}'.encode()
        self.assertEqual(valid, Container([(6, hf(valid), []), (5, b"meta", [])]).read()[0].decoded_json)

    def test_partial_binary_reads_are_exact_and_read_failures_have_no_payload_exception(self):
        c = Container()
        class Partial(ReadRecorder):
            def read(self, count=-1): return super().read(min(count, 3))
        self.assertEqual(ORIGINAL, m.extract_tokenizer_metadata(Partial(c.data), len(c.data)).decoded_json)
        class Hostile(io.BytesIO):
            def read(self, count=-1): raise OSError(PRIVATE)
        with self.assertRaises(m.TokenizerMetadataRefused) as caught:
            m.extract_tokenizer_metadata(Hostile(c.data), len(c.data))
        self.assertEqual(m.RefusalReason.READ, caught.exception.reason)
        self.assertEqual("read_failed", str(caught.exception)); self.assertIsNone(caught.exception.__context__)
        stream = ReadRecorder(c.data[:32])
        with self.assertRaises(m.TokenizerMetadataRefused): m.extract_tokenizer_metadata(stream, len(c.data))

    def test_module_import_is_inert_and_errors_are_closed(self):
        ast.parse(SPEC.loader.get_source(SPEC.name), feature_version=(3, 9))
        self.assertIsInstance(m.TokenizerMetadata.__annotations__["decoded_json"], str)
        code = SPEC.loader.get_code(SPEC.name)  # Only this owned source, before the IO guard.
        probe = types.ModuleType("tokenizer_metadata_inert_probe")
        sys.modules[probe.__name__] = probe
        try:
            with patch("builtins.open", side_effect=AssertionError(PRIVATE)), \
                 patch("io.open", side_effect=AssertionError(PRIVATE)), \
                 patch.object(Path, "open", side_effect=AssertionError(PRIVATE)):
                exec(code, probe.__dict__)
        finally:
            del sys.modules[probe.__name__]
        self.assertFalse(hasattr(m, "main")); self.assertFalse(hasattr(m, "open"))
        self.assertFalse(hasattr(m, "Path")); self.assertFalse(hasattr(m, "subprocess"))
        with self.assertRaises(TypeError): m.TokenizerMetadataRefused(PRIVATE)
        for reason in m.RefusalReason:
            self.assertEqual(reason.value, str(m.TokenizerMetadataRefused(reason)))


if __name__ == "__main__":
    unittest.main()
