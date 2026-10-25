"""Bounded tokenizer metadata interpretation; no imports load native code or files.

Original development controls only, never gameplay or a replacement SDK tokenizer.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from dataclasses import dataclass
import hashlib
import json
import math

MAX_METADATA = 1024 * 1024
MAX_JSON = 128 * 1024 * 1024
MAX_VOCAB = 1024 * 1024
MAX_PIECE = 16384
MAX_FIELDS = 8192
MAX_STOPS = 64
MAX_IDS = 64
REASONS = frozenset(("metadata_bounds", "protobuf", "token_union", "token_ids", "stop_bounds",
    "json", "vocabulary", "piece_bounds", "tokenization_required", "eos"))


class TokenizerOracleRefused(Exception):
    def __init__(self, reason):
        self.reason = reason if reason in REASONS else "metadata_bounds"
        super().__init__(self.reason)


def require(value, reason):
    if not value:
        raise TokenizerOracleRefused(reason)


def _varint(raw, offset):
    value = 0
    for index in range(10):
        require(offset < len(raw), "protobuf")
        byte = raw[offset]; offset += 1
        require(index != 9 or byte <= 1, "protobuf")
        value |= (byte & 127) << (7 * index)
        if byte < 128:
            return value, offset
    raise TokenizerOracleRefused("protobuf")


def _fields(raw, budget):
    offset = 0
    while offset < len(raw):
        budget[0] += 1
        require(budget[0] <= (budget[1] if len(budget) > 1 else MAX_FIELDS), "protobuf")
        tag, offset = _varint(raw, offset)
        number, wire = tag >> 3, tag & 7
        require(0 < number < 2 ** 29 and wire in (0, 1, 2, 5), "protobuf")
        if wire == 0:
            value, offset = _varint(raw, offset)
        else:
            size = (8 if wire == 1 else 4) if wire != 2 else None
            if size is None:
                size, offset = _varint(raw, offset)
            require(size <= len(raw) - offset, "protobuf")
            value = raw[offset:offset + size]; offset += size
        yield number, wire, value


@dataclass(frozen=True)
class TokenReference:
    ids: tuple = ()
    text: str = None


@dataclass(frozen=True)
class StopMetadata:
    start: TokenReference
    stops: tuple


def _reference(raw, budget):
    reference = None
    for number, wire, value in _fields(raw, budget):
        if number not in (1, 2):
            continue
        require(wire == 2 and reference is None, "token_union")
        if number == 2:
            require(len(value) <= MAX_PIECE, "piece_bounds")
            try:
                text = value.decode("utf-8", "strict")
                text.encode("utf-8", "strict")
            except (UnicodeError, ValueError):
                raise TokenizerOracleRefused("token_union") from None
            reference = TokenReference(text=text)
        else:
            ids = []
            for inner, kind, contents in _fields(value, budget):
                if inner != 1:
                    continue
                require(kind in (0, 2), "token_ids")
                if kind == 0:
                    ids.append(contents)
                else:
                    offset = 0
                    while offset < len(contents):
                        token, offset = _varint(contents, offset)
                        ids.append(token)
                        require(len(ids) <= MAX_IDS, "token_ids")
                require(len(ids) <= MAX_IDS and all(0 <= token < 2 ** 31 for token in ids), "token_ids")
            reference = TokenReference(ids=tuple(ids))
    require(reference is not None, "token_union")
    return reference


def parse_stop_metadata(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_METADATA, "metadata_bounds")
    start, stops = None, []
    budget = [0]
    for number, wire, value in _fields(raw, budget):
        if number == 1:
            require(wire == 2 and start is None, "token_union")
            start = _reference(value, budget)
        elif number == 2:
            require(wire == 2 and len(stops) < MAX_STOPS, "stop_bounds")
            stops.append(_reference(value, budget))
    require(stops, "stop_bounds")
    return StopMetadata(start, tuple(stops))


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "json")
        result[key] = value
    return result


def strict_json(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, "json")
    def nonfinite(_):
        raise TokenizerOracleRefused("json")
    def floating(value):
        result = float(value)
        require(math.isfinite(result), "json")
        return result
    try:
        return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs,
                          parse_constant=nonfinite, parse_float=floating)
    except (ValueError, UnicodeError, RecursionError):
        raise TokenizerOracleRefused("json") from None


def _piece(text):
    require(type(text) is str, "vocabulary")
    try:
        data = text.encode("utf-8", "strict")
    except UnicodeError:
        raise TokenizerOracleRefused("vocabulary") from None
    require(len(data) <= MAX_PIECE, "piece_bounds")
    return data


def hf_raw_vocabulary(raw):
    """SDK GetTokens ID-to-token strings, NOT decoded byte/tokenizer equivalence."""
    value = strict_json(raw)
    require(type(value) is dict and type(value.get("model")) is dict, "vocabulary")
    model, vocab = value["model"], value["model"].get("vocab")
    pieces, by_text = {}, {}
    def add(text, token, overlay=False):
        require(type(token) is int and 0 <= token < MAX_VOCAB, "vocabulary")
        data = _piece(text)
        require(token not in pieces or overlay and pieces[token] == data, "vocabulary")
        require(text not in by_text or overlay and by_text[text] == token, "vocabulary")
        pieces[token] = data; by_text[text] = token
    if model.get("type") in ("BPE", "WordLevel", "WordPiece"):
        require(type(vocab) is dict and 0 < len(vocab) <= MAX_VOCAB, "vocabulary")
        for text, token in vocab.items():
            add(text, token)
    elif model.get("type") == "Unigram":
        require(type(vocab) is list and 0 < len(vocab) <= MAX_VOCAB, "vocabulary")
        for token, entry in enumerate(vocab):
            require(type(entry) is list and len(entry) == 2 and type(entry[1]) in (int, float), "vocabulary")
            try:
                finite = math.isfinite(entry[1])
            except OverflowError:
                finite = False
            require(finite, "vocabulary")
            add(entry[0], token)
    else:
        raise TokenizerOracleRefused("vocabulary")
    added = value.get("added_tokens", [])
    require(type(added) is list and len(added) <= MAX_VOCAB, "vocabulary")
    seen_ids, seen_text = set(), set()
    for entry in added:
        require(type(entry) is dict and type(entry.get("id")) is int and type(entry.get("content")) is str, "vocabulary")
        token, text = entry["id"], entry["content"]
        require(token not in seen_ids and text not in seen_text, "vocabulary")
        seen_ids.add(token); seen_text.add(text); add(text, token, True)
    require(set(pieces) == set(range(len(pieces))) and len(pieces) <= MAX_VOCAB, "vocabulary")
    result = tuple(pieces[token] for token in range(len(pieces)))
    require(sum(map(len, result)) <= MAX_JSON, "piece_bounds")
    return result


def sp_raw_vocabulary(raw):
    """ModelProto.pieces in index order only; no SentencePiece encoder/decoder claim."""
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, "metadata_bounds")
    tokens, seen, total = [], set(), 0
    budget = [0, MAX_VOCAB * 8]
    for number, wire, value in _fields(raw, budget):
        if number != 1:
            continue
        require(wire == 2 and len(tokens) < MAX_VOCAB, "vocabulary")
        piece = None
        for inner, kind, contents in _fields(value, budget):
            if inner == 1:
                require(kind == 2 and piece is None and len(contents) <= MAX_PIECE, "piece_bounds")
                try:
                    piece = _piece(contents.decode("utf-8", "strict"))
                except UnicodeError:
                    raise TokenizerOracleRefused("vocabulary") from None
        require(piece is not None and piece not in seen, "vocabulary")
        total += len(piece); require(total <= MAX_JSON, "piece_bounds")
        tokens.append(piece); seen.add(piece)
    require(tokens, "vocabulary")
    return tuple(tokens)


def resolve_stops(metadata, tokens):
    """Exact TokenToId lookup only; unsupported encode fallback refuses, never guesses."""
    require(isinstance(metadata, StopMetadata) and type(tokens) is tuple and 0 < len(tokens) <= MAX_VOCAB, "eos")
    lookup = {}
    for token, piece in enumerate(tokens):
        require(type(piece) is bytes and piece not in lookup, "vocabulary")
        lookup[piece] = token
    resolved = []
    for reference in metadata.stops:
        if reference.text is not None:
            data = _piece(reference.text)
            require(data in lookup, "tokenization_required")
            ids = (lookup[data],)
        else:
            ids = reference.ids
            require(all(type(token) is int and 0 <= token < len(tokens) for token in ids), "eos")
        if ids:
            resolved.append(ids)
    singleton = next((ids[0] for ids in resolved if len(ids) == 1), None)
    require(singleton is not None, "eos")
    return singleton, tuple(resolved)


def vocabulary_report(tokens):
    """Aggregate bytes only: no pieces, special spellings or model paths in reports."""
    require(type(tokens) is tuple and 0 < len(tokens) <= MAX_VOCAB, "vocabulary")
    digest = hashlib.sha256()
    for piece in tokens:
        require(type(piece) is bytes and len(piece) <= MAX_PIECE, "piece_bounds")
        digest.update(len(piece).to_bytes(4, "little")); digest.update(piece)
    return {"tokens": len(tokens), "raw_bytes": sum(map(len, tokens)), "sha256": digest.hexdigest(),
            "pieces_with_ascii_space": sum(b" " in piece for piece in tokens),
            "pieces_with_ascii_tab": sum(b"\t" in piece for piece in tokens),
            "pieces_with_ascii_newline": sum(b"\n" in piece for piece in tokens)}
