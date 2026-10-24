"""Read-only, hash-only model observations; never provisions or initializes a model.

These receipts describe trusted local reads, not an adversarial filesystem proof.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat

CHUNK_BYTES = 32 * 1024 * 1024
MAX_BYTES = 16 * 1024 * 1024 * 1024
DIGEST = re.compile(r"[0-9a-f]{64}")


class InvalidObservation(ValueError):
    """Fixed category only: do not expose model paths or exception contents."""


def require(condition, category):
    if not condition:
        raise InvalidObservation(category)


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def digest(value):
    return type(value) is str and DIGEST.fullmatch(value) is not None


def validate(observation):
    require(type(observation) is dict and set(observation) == {
        "version", "chunk_bytes", "identity_unchanged", "before", "after", "chunks"}, "observation_shape")
    require(type(observation["version"]) is int and observation["version"] == 1, "version")
    require(type(observation["chunk_bytes"]) is int and observation["chunk_bytes"] == CHUNK_BYTES, "chunk_size")
    require(type(observation["identity_unchanged"]) is bool, "identity_flag")
    for name in ("before", "after"):
        value = observation[name]
        require(type(value) is dict and set(value) == {"bytes", "sha256"}, "identity_shape")
        require(integer(value["bytes"], 1, MAX_BYTES) and digest(value["sha256"]), "identity_value")
    rows = observation["chunks"]
    size = observation["before"]["bytes"]
    expected = (size + CHUNK_BYTES - 1) // CHUNK_BYTES
    require(type(rows) is list and len(rows) == expected, "incomplete_coverage")
    for index, row in enumerate(rows):
        require(type(row) is dict and set(row) == {"index", "offset", "bytes", "sha256"}, "chunk_shape")
        offset = index * CHUNK_BYTES
        require(type(row["index"]) is int and row["index"] == index and
                type(row["offset"]) is int and row["offset"] == offset and
                type(row["bytes"]) is int and row["bytes"] == min(CHUNK_BYTES, size - offset), "chunk_order_or_size")
        require(digest(row["sha256"]), "chunk_digest")
    return observation


def stable(observation):
    return observation["identity_unchanged"] and observation["before"] == observation["after"]


def compare(reference, observed, expected_bytes, expected_sha256):
    """Compare complete receipts; a stable mismatch never grants inference admission."""
    require(integer(expected_bytes, 1, MAX_BYTES) and digest(expected_sha256), "expected_identity")
    validate(reference)
    validate(observed)
    require(stable(reference), "source_changed")
    require(reference["before"] == {"bytes": expected_bytes, "sha256": expected_sha256}, "source_identity")
    require(stable(observed), "observed_changed")
    if observed["before"]["bytes"] != expected_bytes:
        return {"status": "size_mismatch", "matches": False, "coverage_bytes": observed["before"]["bytes"],
                "differing_chunks": None}
    changed = [{key: row[key] for key in ("index", "offset", "bytes")}
               for original, row in zip(reference["chunks"], observed["chunks"])
               if original["sha256"] != row["sha256"]]
    same_full = observed["before"]["sha256"] == expected_sha256
    require(same_full == (not changed), "inconsistent_hashes")
    return {"status": "identity_match" if same_full else "identity_mismatch", "matches": same_full,
            "coverage_bytes": expected_bytes, "differing_chunks": changed}


def fingerprint(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def read_hash(source, size):
    """Read exactly the initial bound plus one-byte growth detection, in bounded RAM."""
    source.seek(0)
    whole = hashlib.sha256()
    rows = []
    offset = 0
    while offset < size:
        count = min(CHUNK_BYTES, size - offset)
        chunk = hashlib.sha256()
        remaining = count
        while remaining:
            block = source.read(min(1024 * 1024, remaining))
            require(bool(block), "file_shrank")
            remaining -= len(block)
            chunk.update(block)
            whole.update(block)
        rows.append({"index": len(rows), "offset": offset, "bytes": count, "sha256": chunk.hexdigest()})
        offset += count
    require(source.read(1) == b"", "file_grew")
    return {"bytes": size, "sha256": whole.hexdigest()}, rows


def inspect_file(path):
    """Two complete read-only passes over one handle; return no path or weight bytes.

    Fingerprints bind that handle and the named entry before/after; this cannot
    defeat same-UID adversarial races or prove backend writeback durability.
    """
    path = Path(path)
    initial = path.lstat()
    require(stat.S_ISREG(initial.st_mode) and not path.is_symlink(), "regular_file_required")
    require(integer(initial.st_size, 1, MAX_BYTES), "file_size")
    with path.open("rb") as source:
        opened = os.fstat(source.fileno())
        require(fingerprint(initial) == fingerprint(opened), "file_replaced")
        before, rows = read_hash(source, opened.st_size)
        after, repeated = read_hash(source, opened.st_size)
        closed = os.fstat(source.fileno())
    final = path.lstat()
    unchanged = fingerprint(initial) == fingerprint(closed) == fingerprint(final)
    # Whole-file stability must agree with all repeated chunk digests too.
    unchanged = unchanged and rows == repeated
    return validate({"version": 1, "chunk_bytes": CHUNK_BYTES, "identity_unchanged": unchanged,
                     "before": before, "after": after, "chunks": rows})


def load_receipt(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "duplicate_key")
            value[key] = item
        return value
    with Path(path).open("rb") as source:
        raw = source.read(256 * 1024 + 1)
    require(len(raw) <= 256 * 1024, "receipt_size")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda _: require(False, "nonfinite"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    scan = actions.add_parser("inspect", help="Two read-only local-file passes; prints hashes only")
    scan.add_argument("--model", required=True)
    comparison = actions.add_parser("compare", help="Validate two complete hash receipts")
    comparison.add_argument("--reference", required=True)
    comparison.add_argument("--observed", required=True)
    comparison.add_argument("--expected-bytes", type=int, required=True)
    comparison.add_argument("--expected-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "inspect":
            report = inspect_file(args.model)
            status = 0 if stable(report) else 2
        else:
            report = compare(load_receipt(args.reference), load_receipt(args.observed),
                             args.expected_bytes, args.expected_sha256)
            status = 0 if report["matches"] else 2
        print(json.dumps(report, indent=2))
        return status
    except (OSError, ValueError, UnicodeError, RecursionError) as failure:
        category = str(failure) if isinstance(failure, InvalidObservation) else "inspection_failed"
        print(json.dumps({"status": "failed", "category": category}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
