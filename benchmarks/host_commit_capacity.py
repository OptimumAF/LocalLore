"""Read-only Windows commit observation and a conservative admission policy.

A snapshot is neither a reservation nor an allocation guarantee. Physical RAM,
disk, profile, ownership and all other admission checks remain independent.
ABI: https://learn.microsoft.com/windows/win32/api/psapi/ns-psapi-performance_information
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ctypes
import sys

UINT64_MAX = (1 << 64) - 1
RESERVE_BYTES = 2 * 1024 * 1024 * 1024
POLICY_ID = "guest_plus_reserve_v2"
_SNAPSHOT_KEYS = {"version", "commit_total_bytes", "commit_limit_bytes", "available_commit_bytes"}
_REASONS = ("commit_unavailable", "commit_invalid", "commit_capacity")
DWORD = ctypes.c_uint32
BOOL = ctypes.c_int32
SIZE_T = ctypes.c_size_t


class HostCommitRefused(ValueError):
    def __init__(self, reason):
        self.reason = reason if type(reason) is str and reason in _REASONS else "commit_invalid"
        super().__init__(self.reason)


class PERFORMANCE_INFORMATION(ctypes.Structure):
    _fields_ = [("cb", DWORD), ("CommitTotal", SIZE_T), ("CommitLimit", SIZE_T),
                ("CommitPeak", SIZE_T), ("PhysicalTotal", SIZE_T), ("PhysicalAvailable", SIZE_T),
                ("SystemCache", SIZE_T), ("KernelTotal", SIZE_T), ("KernelPaged", SIZE_T),
                ("KernelNonpaged", SIZE_T), ("PageSize", SIZE_T), ("HandleCount", DWORD),
                ("ProcessCount", DWORD), ("ThreadCount", DWORD)]


def _require(condition):
    if not condition:
        raise HostCommitRefused("commit_invalid")


def _integer(value, low=0):
    _require(type(value) is int and low <= value <= UINT64_MAX)


def snapshot_from_pages(total_pages, limit_pages, page_size):
    """Convert pages with checked unsigned64 arithmetic; no assumed page size."""
    _integer(total_pages)
    _integer(limit_pages, 1)
    _integer(page_size, 1)
    _require(page_size & (page_size - 1) == 0)
    _require(total_pages <= limit_pages and limit_pages <= UINT64_MAX // page_size)
    total, limit = total_pages * page_size, limit_pages * page_size
    return {"version": 1, "commit_total_bytes": total, "commit_limit_bytes": limit,
            "available_commit_bytes": limit - total}


def read_commit():
    """One lazy GetPerformanceInfo call; no paths, error payloads or OS actions."""
    if sys.platform != "win32":
        raise HostCommitRefused("commit_unavailable")
    failed = False
    try:
        api = ctypes.WinDLL("psapi.dll", winmode=0x00000800, use_last_error=True)
        function = api.GetPerformanceInfo
        function.argtypes = [ctypes.POINTER(PERFORMANCE_INFORMATION), DWORD]
        function.restype = BOOL
        info = PERFORMANCE_INFORMATION()
        size = ctypes.sizeof(info)
        info.cb = size
        status = function(ctypes.byref(info), size)
    except Exception:
        failed = True
    if failed:
        raise HostCommitRefused("commit_unavailable")
    if type(status) is not int or not -(1 << 31) <= status <= (1 << 31) - 1 or status == 0:
        raise HostCommitRefused("commit_unavailable")
    _require(info.cb == size)
    return snapshot_from_pages(int(info.CommitTotal), int(info.CommitLimit), int(info.PageSize))


def require_capacity(snapshot, guest_mib):
    """Guest-sized allocation plus a separate project reserve, not a guarantee.

    The selected emulator's version-matched source attempts one guest-sized
    VirtualAlloc. Its 20% check is a diagnostic after allocation failure, not
    a requirement to retain two guest allocations. The extra 2GiB is our margin.
    https://android.googlesource.com/platform/external/qemu/+/2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a/util/oslib-win32.c
    """
    _require(type(snapshot) is dict and set(snapshot) == _SNAPSHOT_KEYS)
    _require(type(snapshot["version"]) is int and snapshot["version"] == 1)
    for key in ("commit_total_bytes", "commit_limit_bytes", "available_commit_bytes"):
        _integer(snapshot[key])
    total, limit, available = (snapshot[key] for key in
        ("commit_total_bytes", "commit_limit_bytes", "available_commit_bytes"))
    _require(limit > 0 and total <= limit and available == limit - total)
    _require(type(guest_mib) is int and guest_mib in (2048, 8192))
    guest_bytes = guest_mib * 1024 * 1024
    required = guest_bytes + RESERVE_BYTES
    if available < required:
        raise HostCommitRefused("commit_capacity")
    return dict(snapshot, guest_memory_bytes=guest_bytes, required_commit_bytes=required,
                reserve_bytes=RESERVE_BYTES)
