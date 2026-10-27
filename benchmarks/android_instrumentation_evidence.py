"""Bounded app-class AndroidJUnitRunner evidence; never invokes a process/device.

The caller owns invocation, source/artifact binding, and private raw retention.
External controller proof instrumentation has a different protocol.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

MAX_BYTES = 262_144
MAX_SOURCE_BYTES = 1_048_576
MAX_METHODS = 256
_METHOD = re.compile(r"[A-Za-z_][A-Za-z_0-9]{0,255}", re.ASCII)
_CLASS = re.compile(r"[A-Za-z_$][A-Za-z_0-9$]*(?:\.[A-Za-z_$][A-Za-z_0-9$]*)+", re.ASCII)
_ANNOTATION = re.compile(r"@(?:org\.junit\.)?Test\b", re.ASCII)
_OTHER_ANNOTATION = re.compile(r"@[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*", re.ASCII)
_DECLARATION = re.compile(r"\s*(?:(?:public|internal|suspend)\s+)*fun\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(\s*\)", re.ASCII)
_STATUS = "INSTRUMENTATION_STATUS: "
_STATUS_CODE = "INSTRUMENTATION_STATUS_CODE: "
_RESULT = "INSTRUMENTATION_RESULT: "
_FINAL = "INSTRUMENTATION_CODE: "
_FIELDS = {"class", "test", "current", "numtests", "id", "stream", "stack"}


class EvidenceRefused(RuntimeError):
    """Fixed refusal, with no raw test text, paths, or exception messages."""


def _require(condition: bool, reason: str = "instrumentation_refused") -> None:
    if not condition:
        raise EvidenceRefused(reason)


def _code_only(source: str) -> str:
    """Mask comments and Kotlin literals, keeping offsets and line boundaries.

    This is a lexical roster reader for the repository's ordinary @Test fun
    declarations, not a Kotlin compiler or support for generated/aliased tests.
    """
    out = list(source)
    i = 0
    while i < len(source):
        start = i
        if source.startswith("//", i):
            end = source.find("\n", i)
            i = len(source) if end < 0 else end
        elif source.startswith("/*", i):
            i += 2
            depth = 1
            while i < len(source) and depth:
                if source.startswith("/*", i):
                    depth += 1
                    _require(depth <= 64, "roster_refused")
                    i += 2
                elif source.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            _require(depth == 0, "roster_refused")
        elif source.startswith('"""', i):
            end = source.find('"""', i + 3)
            _require(end >= 0, "roster_refused")
            i = end + 3
        elif source[i] in ('"', "'"):
            quote = source[i]
            i += 1
            closed = False
            while i < len(source):
                _require(source[i] not in "\r\n", "roster_refused")
                if source[i] == "\\":
                    i += 2
                elif source[i] == quote:
                    i += 1
                    closed = True
                    break
                else:
                    i += 1
            _require(closed, "roster_refused")
        else:
            i += 1
            continue
        for at in range(start, i):
            if source[at] not in "\r\n":
                out[at] = " "
    return "".join(out)


def _after_annotation(code: str, pos: int) -> int:
    while pos < len(code) and code[pos].isspace():
        pos += 1
    if pos < len(code) and code[pos] == "(":
        depth = 1
        pos += 1
        while pos < len(code) and depth:
            depth += (code[pos] == "(") - (code[pos] == ")")
            _require(depth <= 64, "roster_refused")
            pos += 1
        _require(depth == 0, "roster_refused")
    while pos < len(code) and code[pos].isspace():
        pos += 1
    return pos


def test_roster(source: Path) -> list[str]:
    """Read source order; refuse missing/duplicate/unsupported test declarations."""
    _require(isinstance(source, Path), "roster_refused")
    try:
        with source.open("rb") as handle:
            raw = handle.read(MAX_SOURCE_BYTES + 1)
        _require(0 < len(raw) <= MAX_SOURCE_BYTES, "roster_refused")
        text = raw.decode("utf-8", errors="strict")
    except (OSError, UnicodeError, ValueError):
        raise EvidenceRefused("roster_refused") from None
    _require("\x00" not in text, "roster_refused")
    code = _code_only(text)
    methods = []
    for annotation in _ANNOTATION.finditer(code):
        pos = _after_annotation(code, annotation.end())
        # Android annotations such as @SdkSuppress do not change the source
        # roster. Their actual skip/failure outcome still cannot pass below.
        while pos < len(code) and code[pos] == "@":
            extra = _OTHER_ANNOTATION.match(code, pos)
            _require(extra is not None, "roster_refused")
            pos = _after_annotation(code, extra.end())
        declaration = _DECLARATION.match(code, pos)
        _require(declaration is not None, "roster_refused")
        method = declaration.group(1)
        _require(_METHOD.fullmatch(method) is not None and method not in methods, "roster_refused")
        methods.append(method)
        _require(len(methods) <= MAX_METHODS, "roster_refused")
    _require(bool(methods), "roster_refused")
    return methods


def validate_instrumentation(raw: bytes, class_name: str, methods: list[str]) -> dict:
    """Accept one complete class run with exactly one start/pass pair per method.

    JUnit can execute a different order from source order. Optional current and
    numtests must describe the observed pair ordinal and complete roster. Only
    stream/stack bundle fields have multiline continuations; a stack or any
    nonzero test outcome refuses success. Nothing from raw prose is returned.
    """
    _require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES and raw.endswith(b"\n"))
    _require(type(class_name) is str and len(class_name) <= 256 and _CLASS.fullmatch(class_name) is not None)
    _require(type(methods) is list and 1 <= len(methods) <= MAX_METHODS)
    _require(all(type(m) is str and _METHOD.fullmatch(m) is not None for m in methods))
    _require(len(set(methods)) == len(methods))
    try:
        text = raw.decode("utf-8", errors="strict").replace("\r\n", "\n")
    except UnicodeError:
        raise EvidenceRefused("instrumentation_refused") from None
    _require("\r" not in text and "\x00" not in text)
    fields: dict[str, str] = {}
    continuation = None
    active = None
    seen: set[str] = set()
    final_stream = None
    finished = False
    for line in text.split("\n"):
        if not line:
            if final_stream is not None and not finished:
                final_stream += "\n"
            continue  # Empty framing lines occur in Windows runner captures.
        _require(not finished)
        if line.startswith(_STATUS):
            _require(final_stream is None)
            key, separator, value = line[len(_STATUS):].partition("=")
            _require(bool(separator) and key in _FIELDS and key not in fields)
            fields[key] = value
            continuation = key
        elif line.startswith(_STATUS_CODE):
            _require(final_stream is None and {"class", "test"} <= fields.keys())
            _require(fields["class"] == class_name and fields["test"] in methods)
            _require("id" not in fields or fields["id"] == "AndroidJUnitRunner")
            _require("current" not in fields or fields["current"] == str(len(seen) + 1))
            _require("numtests" not in fields or fields["numtests"] == str(len(methods)))
            _require("stack" not in fields)
            code = line[len(_STATUS_CODE):]
            method = fields["test"]
            if code == "1":
                _require(active is None and method not in seen)
                active = method
            else:
                _require(code == "0" and active == method and method not in seen)
                seen.add(method)
                active = None
            fields = {}
            continuation = None
        elif line.startswith(_RESULT):
            _require(final_stream is None and not fields and active is None and seen == set(methods))
            key, separator, value = line[len(_RESULT):].partition("=")
            _require(bool(separator) and key == "stream")
            final_stream = value
            continuation = None
        elif line.startswith(_FINAL):
            _require(final_stream is not None and not fields and active is None and seen == set(methods))
            _require(line[len(_FINAL):] == "-1")
            noun = "test" if len(methods) == 1 else "tests"
            summary = (r"\n*Time: (?:0|[1-9][0-9]*)(?:\.[0-9]+)?\n+OK \("
                       + str(len(methods)) + " " + noun + r"\)\n*")
            _require(re.fullmatch(summary, final_stream) is not None)
            finished = True
        elif line.startswith("INSTRUMENTATION_"):
            raise EvidenceRefused("instrumentation_refused")
        elif final_stream is not None:
            final_stream += "\n" + line
        else:
            _require(continuation in ("stream", "stack"))
            fields[continuation] += "\n" + line
    _require(finished and not fields and active is None and seen == set(methods))
    return {"class": class_name, "methods": list(methods), "method_count": len(methods),
            "stdout_sha256": hashlib.sha256(raw).hexdigest(), "passed": True}
