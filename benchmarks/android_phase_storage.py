"""Bounded storage facts for a fixed Android /data query; no device operations.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import re

MAX_BYTES = 2 ** 63 - 1
MAX_KIB = MAX_BYTES // 1024
MOUNTS = {"/data", "/data/user/0"}
HEADER = [b"Filesystem", b"1K-blocks", b"Used", b"Available", b"Use%", b"Mounted", b"on"]


def parse_df(raw, requested_dev, display_dev):
    """Validate `df -k /data` plus separately observed stat device identities.

    The caller obtains both identities in the same namespace, for the fixed
    requested path and the displayed allowed alias, before using available
    bytes. This decoder neither collects those facts nor authorizes a write.
    """
    if (type(raw) is not bytes or not 0 < len(raw) <= 2048
            or type(requested_dev) is not int or type(display_dev) is not int
            or not 0 < requested_dev <= MAX_BYTES or requested_dev != display_dev):
        return None
    if b"\r" in raw:
        normalized = raw.replace(b"\r\n", b"\n")
        if b"\r" in normalized or normalized.replace(b"\n", b"\r\n") != raw:
            return None
        raw = normalized
    if any(value < 32 and value not in (9, 10) or value > 126 for value in raw):
        return None
    lines = raw.split(b"\n")
    if len(lines) != 3 or lines[-1] != b"" or lines[0].split() != HEADER:
        return None
    row = lines[1].split()
    if len(row) != 6 or re.fullmatch(rb"/dev/block/[A-Za-z0-9_-]{1,64}", row[0]) is None:
        return None
    if any(re.fullmatch(rb"(?:0|[1-9][0-9]{0,15})", value) is None for value in row[1:4]):
        return None
    total, used, available = (int(value) for value in row[1:4])
    if not 0 < total <= MAX_KIB or used > total or available > total or used + available > total:
        return None
    if re.fullmatch(rb"(?:0|[1-9][0-9]{0,2})%", row[4]) is None or int(row[4][:-1]) > 100:
        return None
    mount = row[5].decode("ascii")
    if mount not in MOUNTS:
        return None
    return {"version": 1, "available_bytes": available * 1024, "display_mount": mount}
