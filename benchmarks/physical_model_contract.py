"""Pure pre-install admission for one explicitly observed physical profile.

No evidence collection, authorization, IO or allocation occurs here. A successful
snapshot is neither a reservation nor a model/runtime feasibility result.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

GIB = 1024 ** 3
MODEL_BYTES = 2_588_147_712
MODEL_SHA256 = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
APP = "org.locallore.app.phoneverify"
TEST = APP + ".test"
PROFILE = "s918u1_api36_arm64_4k_v1"
SHARED_RESERVE_BYTES = 2 * GIB
REQUIRED_INTERNAL_FREE_BYTES = 2 * MODEL_BYTES + SHARED_RESERVE_BYTES
MIN_AVAILABLE_MEMORY_BYTES = 4 * GIB
MIN_TOTAL_MEMORY_BYTES = 10 * GIB
MAX_TOTAL_MEMORY_BYTES = 12 * GIB
MAX_BYTES = (1 << 63) - 1

SAMPLE_KEYS = frozenset((
    "version", "authorized", "physical", "model", "api", "soc_model", "board_platform",
    "abis", "page_bytes", "memory_total_bytes", "memory_available_bytes", "internal_free_bytes",
    "battery_level", "battery_scale", "usb_powered", "temperature_tenths_celsius",
    "thermal_status", "new_app_absent", "new_test_absent", "prior_pair_unchanged",
))
REASONS = (
    "invalid_sample", "unauthorized", "not_physical", "profile_mismatch", "memory_capacity",
    "storage_capacity", "power_or_temperature", "thermal_capacity", "namespace_collision",
    "prior_pair_changed",
)
_BOOL_KEYS = ("authorized", "physical", "usb_powered", "new_app_absent", "new_test_absent", "prior_pair_unchanged")
_BYTE_KEYS = ("page_bytes", "memory_total_bytes", "memory_available_bytes", "internal_free_bytes")
_OBSERVED_KEYS = (
    "memory_total_bytes", "memory_available_bytes", "internal_free_bytes", "battery_level",
    "battery_scale", "temperature_tenths_celsius", "thermal_status",
)
_ABIS = frozenset(("arm64-v8a", "armeabi-v7a", "armeabi", "x86_64", "x86", "riscv64"))


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _metadata(value):
    return (type(value) is str and 1 <= len(value) <= 64 and
            all(char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-" for char in value))


def _valid(sample):
    if (type(sample) is not dict or len(sample) != len(SAMPLE_KEYS) or
            any(type(key) is not str for key in sample) or set(sample) != SAMPLE_KEYS):
        return False
    if not _integer(sample["version"], 1, 1):
        return False
    if any(type(sample[key]) is not bool for key in _BOOL_KEYS):
        return False
    if any(not _integer(sample[key], 0, MAX_BYTES) for key in _BYTE_KEYS):
        return False
    if sample["memory_available_bytes"] > sample["memory_total_bytes"]:
        return False
    if not _integer(sample["api"], 0, (1 << 31) - 1):
        return False
    if any(not _metadata(sample[key]) for key in ("model", "soc_model", "board_platform")):
        return False
    abis = sample["abis"]
    if (type(abis) is not list or not 1 <= len(abis) <= 8 or
            any(type(abi) is not str or abi not in _ABIS for abi in abis) or len(set(abis)) != len(abis)):
        return False
    if (not _integer(sample["battery_level"], 0, 100) or not _integer(sample["battery_scale"], 1, 100) or
            sample["battery_level"] > sample["battery_scale"]):
        return False
    return (_integer(sample["temperature_tenths_celsius"], -1000, 2000) and
            _integer(sample["thermal_status"], 0, 6))


def _report(reasons, observed):
    return {"version": 1, "scope": "physical_model_admission", "profile": PROFILE,
            "status": "refused" if reasons else "admitted", "reasons": reasons,
            "required_internal_free_bytes": REQUIRED_INTERNAL_FREE_BYTES,
            "required_available_memory_bytes": MIN_AVAILABLE_MEMORY_BYTES, "observed": observed}


def assess(sample):
    """Assess trusted observations; never treat caller booleans as evidence.

    Only pre-install admission is represented. New app UID/path ownership and
    remaining-copy capacity must be independently rechecked after installation.
    Malformed or unavailable observations return no partial observed values.
    """
    if not _valid(sample):
        return _report(["invalid_sample"], None)
    reasons = []
    conditions = (
        (not sample["authorized"], "unauthorized"),
        (not sample["physical"], "not_physical"),
        (sample["model"] != "SM-S918U1" or sample["api"] != 36 or sample["soc_model"] != "SM8550" or
         sample["board_platform"] != "kalama" or sample["abis"][0] != "arm64-v8a" or sample["page_bytes"] != 4096 or
         not MIN_TOTAL_MEMORY_BYTES <= sample["memory_total_bytes"] <= MAX_TOTAL_MEMORY_BYTES, "profile_mismatch"),
        (sample["memory_available_bytes"] < MIN_AVAILABLE_MEMORY_BYTES, "memory_capacity"),
        (sample["internal_free_bytes"] < REQUIRED_INTERNAL_FREE_BYTES, "storage_capacity"),
        (not sample["usb_powered"] or sample["battery_scale"] != 100 or sample["battery_level"] < 20 or
         not 0 <= sample["temperature_tenths_celsius"] < 400, "power_or_temperature"),
        (sample["thermal_status"] != 0, "thermal_capacity"),
        (not sample["new_app_absent"] or not sample["new_test_absent"], "namespace_collision"),
        (not sample["prior_pair_unchanged"], "prior_pair_changed"),
    )
    for refused, reason in conditions:
        if refused:
            reasons.append(reason)
    return _report(reasons, {key: sample[key] for key in _OBSERVED_KEYS})
