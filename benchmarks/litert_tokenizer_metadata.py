"""Bounded selected-section LiteRT-LM reader; no CLI, source admission or EOS oracle.

Only the caller's stream is touched, and only on an explicit extraction call.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math
import struct
import zlib

MAX_HEADER = 4 * 1024 * 1024
MAX_SECTIONS = 256
MAX_ITEMS = 64
MAX_METADATA = 1024 * 1024
MAX_COMPRESSED = 32 * 1024 * 1024
MAX_DECODED = 128 * 1024 * 1024
BLOCK_SIZE = 16 * 1024
_CHUNK = 65536


class RefusalReason(str, Enum):
    INPUT = "input_invalid"
    READ = "read_failed"
    HEADER = "header_invalid"
    VERSION = "version_unsupported"
    FLATBUFFER = "flatbuffer_invalid"
    LIMIT = "limit_exceeded"
    SECTION = "section_invalid"
    SELECTION = "selection_ambiguous_or_missing"
    DEFLATE = "deflate_invalid"
    JSON = "json_invalid"


class TokenizerMetadataRefused(ValueError):
    def __init__(self, reason):
        if not isinstance(reason, RefusalReason):
            raise TypeError("reason_invalid")
        self.reason = reason
        super().__init__(reason.value)


def _refuse(reason):
    raise TokenizerMetadataRefused(reason)


class TokenizerKind(str, Enum):
    HF_JSON = "HF_JSON"
    SENTENCEPIECE = "SENTENCEPIECE"


class Selection(str, Enum):
    TYPED = "TYPED"
    UNTYPED = "UNTYPED"


@dataclass(frozen=True)
class SectionRange:
    index: int
    data_type: int
    begin: int
    end: int


@dataclass(frozen=True)
class TokenizerMetadata:
    container_version: tuple
    header_end: int
    sections: tuple
    selected_kind: TokenizerKind
    selection: Selection
    tokenizer_range: SectionRange
    metadata_range: SectionRange
    original_payload: bytes = field(repr=False)
    decoded_json: bytes | None = field(repr=False)
    llm_metadata: bytes = field(repr=False)
    original_sha256: str
    decoded_sha256: str | None
    llm_sha256: str


def _read(stream, offset, length):
    """Exact bounded binary reads; no exception message from the stream escapes."""
    failed = False
    chunks = []
    try:
        if stream.seek(offset) != offset:
            failed = True
        remaining = length
        while not failed and remaining:
            chunk = stream.read(min(remaining, _CHUNK))
            if type(chunk) is not bytes or not chunk or len(chunk) > min(remaining, _CHUNK):
                failed = True
                break
            chunks.append(chunk)
            remaining -= len(chunk)
    except Exception:
        failed = True
    if failed:
        _refuse(RefusalReason.READ)
    return b"".join(chunks)


def _ascii_lower(value):
    return value.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"))


class _FlatBuffer:
    """Pinned schema verifier over the bounded declared header, never payloads."""
    def __init__(self, data):
        self.data = data
        self.strings = {}
        self.string_bytes = 0

    def span(self, pos, size):
        if pos < 0 or size < 0 or pos > len(self.data) - size:
            _refuse(RefusalReason.FLATBUFFER)

    def number(self, pos, fmt):
        width = struct.calcsize(fmt)
        self.span(pos, width)
        if pos % width:
            _refuse(RefusalReason.FLATBUFFER)
        return struct.unpack_from("<" + fmt, self.data, pos)[0]

    def reference(self, pos):
        delta = self.number(pos, "I")
        if delta < 4:
            _refuse(RefusalReason.FLATBUFFER)
        target = pos + delta
        self.span(target, 4)
        return target

    def table(self, pos, widths):
        if pos % 4:
            _refuse(RefusalReason.FLATBUFFER)
        displacement = self.number(pos, "i")  # Shared vtable may follow this table.
        vt = pos - displacement
        size, object_size = self.number(vt, "H"), self.number(vt + 2, "H")
        if size < 4 or size % 2 or size > 4 + 2 * len(widths) or object_size < 4:
            _refuse(RefusalReason.FLATBUFFER)
        self.span(vt, size)
        self.span(pos, object_size)
        if max(vt, pos) < min(vt + size, pos + object_size):
            _refuse(RefusalReason.FLATBUFFER)
        fields, occupied = [], []
        for index, width in enumerate(widths):
            offset = self.number(vt + 4 + index * 2, "H") if 4 + index * 2 < size else 0
            if not offset:
                fields.append(None)
                continue
            if offset < 4 or offset > object_size - width or (pos + offset) % width:
                _refuse(RefusalReason.FLATBUFFER)
            if any(max(offset, start) < min(offset + width, end) for start, end in occupied):
                _refuse(RefusalReason.FLATBUFFER)
            occupied.append((offset, offset + width))
            fields.append(pos + offset)
        return fields

    def required_ref(self, field_pos):
        if field_pos is None:
            _refuse(RefusalReason.FLATBUFFER)
        return self.reference(field_pos)

    def vector(self, field_pos, cap):
        pos = self.required_ref(field_pos)
        count = self.number(pos, "I")
        if count > cap:
            _refuse(RefusalReason.LIMIT)
        self.span(pos + 4, count * 4)
        return [self.reference(pos + 4 + 4 * index) for index in range(count)]

    def string(self, field_pos):
        pos = self.required_ref(field_pos)
        if pos in self.strings:
            return self.strings[pos]
        length = self.number(pos, "I")
        self.span(pos + 4, length + 1)
        if self.data[pos + 4 + length] != 0:
            _refuse(RefusalReason.FLATBUFFER)
        self.string_bytes += length
        if self.string_bytes > MAX_HEADER:
            _refuse(RefusalReason.LIMIT)
        invalid = False
        try:
            value = self.data[pos + 4:pos + 4 + length].decode("utf-8", "strict")
        except UnicodeError:
            invalid = True
        if invalid:
            _refuse(RefusalReason.FLATBUFFER)
        self.strings[pos] = value
        return value

    def items(self, field_pos, required=False, selection_keys=False):
        if field_pos is None and not required:
            return {}
        result, reserved_seen = {}, False
        for pos in self.vector(field_pos, MAX_ITEMS):
            key_pos, discriminator_pos, value_pos = self.table(pos, (4, 1, 4))
            key = self.string(key_pos)
            if key in result:
                _refuse(RefusalReason.FLATBUFFER)
            reserved = selection_keys and _ascii_lower(key) == "model_type"
            if reserved and reserved_seen:
                _refuse(RefusalReason.SELECTION)
            reserved_seen = reserved_seen or reserved
            discriminator = self.number(discriminator_pos, "B") if discriminator_pos is not None else 0
            if not 1 <= discriminator <= 12:
                _refuse(RefusalReason.FLATBUFFER)
            value_table = self.required_ref(value_pos)
            if discriminator == 9:
                string_pos, = self.table(value_table, (4,))
                value = self.string(string_pos) if string_pos is not None else None
            else:
                fmt = {1: "B", 2: "b", 3: "H", 4: "h", 5: "I", 6: "i", 7: "f",
                       8: "B", 10: "Q", 11: "q", 12: "d"}[discriminator]
                scalar_pos, = self.table(value_table, (struct.calcsize(fmt),))
                value = self.number(scalar_pos, fmt) if scalar_pos is not None else 0
                if (discriminator == 8 and value not in (0, 1)) or (discriminator in (7, 12) and not math.isfinite(value)):
                    _refuse(RefusalReason.FLATBUFFER)
            if reserved and (discriminator != 9 or not isinstance(value, str) or not value.isascii()):
                _refuse(RefusalReason.SELECTION)
            result[key] = (discriminator, value)
        return result


def _model_type(items):
    for key, (_, value) in items.items():
        if _ascii_lower(key) == "model_type":
            return _ascii_lower(value)
    return None


def _directory(data, header_end, file_size):
    fb = _FlatBuffer(data)
    system_pos, sections_pos = fb.table(fb.reference(0), (4, 4))
    if system_pos is not None:
        entries_pos, = fb.table(fb.reference(system_pos), (4,))
        fb.items(entries_pos, required=True)
    if sections_pos is None:
        _refuse(RefusalReason.SELECTION)
    objects_pos, = fb.table(fb.reference(sections_pos), (4,))
    rows = []
    for index, pos in enumerate(fb.vector(objects_pos, MAX_SECTIONS)):
        items_pos, begin_pos, end_pos, type_pos = fb.table(pos, (4, 8, 8, 1))
        begin = fb.number(begin_pos, "Q") if begin_pos is not None else 0
        end = fb.number(end_pos, "Q") if end_pos is not None else 0
        data_type = fb.number(type_pos, "B") if type_pos is not None else 0
        if data_type > 11 or begin % BLOCK_SIZE or begin < header_end or begin > end or end > file_size:
            _refuse(RefusalReason.SECTION)
        rows.append((SectionRange(index, data_type, begin, end), _model_type(fb.items(items_pos, selection_keys=True))))
    occupied = sorted((row.begin, row.end) for row, _ in rows if row.begin != row.end)
    if any(right[0] < left[1] for left, right in zip(occupied, occupied[1:])):
        _refuse(RefusalReason.SECTION)
    eligible = [(row, model_type) for row, model_type in rows
                if row.data_type in (4, 6) and model_type in (None, "tf_lite_prefill_decode")]
    # A typed and an untyped choice, including SP/HF, is deliberately not guessed.
    metadata = [row for row, model_type in rows if row.data_type == 5 and model_type is None]
    if len(eligible) != 1 or len(metadata) != 1 or any(row.data_type == 5 and model_type is not None for row, model_type in rows):
        _refuse(RefusalReason.SELECTION)
    selected, model_type = eligible[0]
    if selected.begin == selected.end:
        _refuse(RefusalReason.SELECTION)
    if selected.end - selected.begin > MAX_COMPRESSED or metadata[0].end - metadata[0].begin > MAX_METADATA:
        _refuse(RefusalReason.LIMIT)
    return tuple(row for row, _ in rows), selected, metadata[0], Selection.UNTYPED if model_type is None else Selection.TYPED


def _decoded_hf(payload):
    if len(payload) < 8:
        _refuse(RefusalReason.DEFLATE)
    expected, = struct.unpack_from("<Q", payload)
    if expected > MAX_DECODED:
        _refuse(RefusalReason.LIMIT)
    decoder, output, length, failed = zlib.decompressobj(), [], 0, False
    try:
        for offset in range(8, len(payload), _CHUNK):
            pending = payload[offset:offset + _CHUNK]
            if decoder.eof:
                failed = True
                break
            while pending:
                value = decoder.decompress(pending, min(_CHUNK, expected - length + 1))
                length += len(value)
                if length > expected or decoder.unused_data:
                    failed = True
                    break
                output.append(value)
                rest = decoder.unconsumed_tail
                if rest == pending and not value:
                    failed = True
                    break
                pending = rest
            if failed:
                break
    except zlib.error:
        failed = True
    if failed or not decoder.eof or decoder.unused_data or length != expected:
        _refuse(RefusalReason.DEFLATE)
    decoded = b"".join(output)
    _strict_json(decoded)
    return decoded


def _strict_json(data):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    def constant(_):
        raise ValueError()

    def floating(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError()
        return result

    failed = False
    try:
        value = json.loads(data.decode("utf-8", "strict"), object_pairs_hook=pairs,
                           parse_constant=constant, parse_float=floating)
        if type(value) is not dict:
            failed = True
        pending = [value]
        while pending:
            item = pending.pop()
            if isinstance(item, str):
                item.encode("utf-8", "strict")
            elif isinstance(item, dict):
                pending.extend(item.keys()); pending.extend(item.values())
            elif isinstance(item, list):
                pending.extend(item)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        failed = True
    if failed:
        _refuse(RefusalReason.JSON)


def extract_tokenizer_metadata(stream, file_size):
    """Read the bounded header and exactly one tokenizer and LlmMetadata payload.

    The caller owns source identity/no-link/size stability and provenance. A
    directory declaring sections inside the header is refused after header read;
    no selected payload is read until the complete directory passes validation.
    Version support is explicit policy, not full future-patch compatibility.
    """
    if type(file_size) is not int or not 32 <= file_size <= (1 << 63) - 1:
        _refuse(RefusalReason.INPUT)
    fixed = _read(stream, 0, 32)
    if fixed[:8] != b"LITERTLM":
        _refuse(RefusalReason.HEADER)
    version = struct.unpack_from("<III", fixed, 8)
    if version[0] != 1 or not 0 <= version[1] <= 7:
        _refuse(RefusalReason.VERSION)
    header_end, = struct.unpack_from("<Q", fixed, 24)
    if not 36 <= header_end <= file_size:
        _refuse(RefusalReason.HEADER)
    if header_end > MAX_HEADER:
        _refuse(RefusalReason.LIMIT)
    sections, selected, metadata, selection = _directory(_read(stream, 32, header_end - 32), header_end, file_size)
    payload = _read(stream, selected.begin, selected.end - selected.begin)
    decoded = _decoded_hf(payload) if selected.data_type == 6 else None
    raw_metadata = _read(stream, metadata.begin, metadata.end - metadata.begin)
    return TokenizerMetadata(version, header_end, sections,
        TokenizerKind.HF_JSON if decoded is not None else TokenizerKind.SENTENCEPIECE,
        selection, selected, metadata, payload, decoded, raw_metadata,
        hashlib.sha256(payload).hexdigest(), hashlib.sha256(decoded).hexdigest() if decoded is not None else None,
        hashlib.sha256(raw_metadata).hexdigest())
