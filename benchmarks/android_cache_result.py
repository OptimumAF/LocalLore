"""Strict fixed cache-harness evidence decoding; never a gameplay authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import math
import re

import android_cache_volume as storage
import android_play_probe as play
from android_runtime_spike import strict_json

ERRORS = {"invalid_request", "identity_invalid", "volume_invalid", "volume_ambiguous", "volume_missing",
          "capacity_blocked", "path_invalid", "cache_inventory_limit", "probe_failed", "volume_changed",
          "model_missing", "runtime_unavailable", "runtime_failed"}
BASE = {"version", "operation", "status", "error", "metrics"}
OPTIONAL = {"volumes", "sample", "post_sample", "play_result", "explicit_cache_directory"}
VOLUME = {"volume_uuid", "mounted", "primary", "emulated", "writable", "cache_device", "cache_free_bytes"}
SAMPLE = VOLUME | {"userdata_device", "userdata_free_bytes", "cache_bytes"}
COUNTS = {"engines_opened", "engines_closed", "conversations_opened", "conversations_closed", "main_pulses"}
PLAY_NUMBERS = {"play_roles", "play_load_ms", "play_generation_ms", "play_input_tokens", "play_output_tokens"}
INTEGER_METRICS = COUNTS | {"play_roles", "play_input_tokens", "play_output_tokens", "generation_main_pulses"}
NUMBERS = COUNTS | PLAY_NUMBERS | {"generation_main_pulses", "cancel_call_ms"}
BOOLS = {"owners_balanced", "cleanup_requires_process_termination", "cancel_called", "terminal_callback",
         "cancel_terminal_callback", "generate_terminal_callback"}
MODEL_SHA256 = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
MODEL_BYTES = 2_588_147_712
MODEL_KEYS = {"verified", "sha256", "bytes", "diagnostic"}
MODEL_DIAGNOSTICS = {"verified", "absent", "mismatch", "unstable", "incomplete", "not_regular",
                     "wrong_volume", "invalid_receipt", "read_failed"}


def terminal(raw):
    if type(raw) is not bytes or len(raw) > 131072:
        return None
    codes = list(re.finditer(rb"^INSTRUMENTATION_CODE: (-?\d+)\r?$", raw, re.M))
    rows = list(re.finditer(rb"^INSTRUMENTATION_RESULT: cache_result=(.*)\r?$", raw, re.M))
    if (len(codes) != 1 or codes[0].group(1) != b"-1" or len(rows) != 1
            or rows[0].end() >= codes[0].start() or b"INSTRUMENTATION_FAILED" in raw):
        return None
    return strict_json(rows[0].group(1))


def integer(value, minimum=0, maximum=storage.MAX_BYTES):
    return type(value) is int and minimum <= value <= maximum


def volume(value, selected=False, expected_uuid=None):
    keys = SAMPLE if selected else VOLUME
    if type(value) is not dict or set(value) != keys:
        return False
    uuid = value["volume_uuid"]
    if uuid is not None and (type(uuid) is not str or not storage.UUID.fullmatch(uuid)):
        return False
    if any(type(value[k]) is not bool for k in ("mounted", "primary", "emulated", "writable")):
        return False
    if not integer(value["cache_device"]) or not integer(value["cache_free_bytes"]):
        return False
    if not selected:
        return True
    return (uuid == expected_uuid and value["mounted"] and not value["primary"] and not value["emulated"]
            and value["writable"] and integer(value["cache_device"], 1) and integer(value["userdata_device"], 1)
            and value["cache_device"] != value["userdata_device"] and integer(value["userdata_free_bytes"])
            and integer(value["cache_bytes"]))


def samples_valid(value, expected_uuid):
    before, after = value.get("sample"), value.get("post_sample")
    if not volume(before, True, expected_uuid) or not volume(after, True, expected_uuid):
        return False
    return all(before[k] == after[k] for k in ("volume_uuid", "cache_device", "userdata_device",
                                               "mounted", "primary", "emulated", "writable"))


def metrics_valid(value, has_play):
    if type(value) is not dict or set(value) - (NUMBERS | BOOLS):
        return False
    if not (COUNTS | {"owners_balanced", "cleanup_requires_process_termination"}) <= set(value):
        return False
    if has_play and not PLAY_NUMBERS <= set(value):
        return False
    if any(type(value[k]) is not bool for k in BOOLS & set(value)):
        return False
    for k in NUMBERS & set(value):
        if type(value[k]) not in (int, float) or not math.isfinite(value[k]) or not 0 <= value[k] <= 2 ** 31:
            return False
        if k in INTEGER_METRICS and type(value[k]) is not int:
            return False
    return (value["owners_balanced"] is True and value["cleanup_requires_process_termination"] is False
            and value["engines_opened"] == value["engines_closed"]
            and value["conversations_opened"] == value["conversations_closed"])


def parse_result(raw, case, expected_uuid):
    """Return a safe observation, retaining valid receipts despite an outer post error.

    Samples are shape/identity observations, not fresh host/backing admission.
    Missing new-protocol metrics are never synthesized from the old protocol.
    Caller retains raw bytes privately before this decoder, including refusals.
    """
    try:
        if (type(raw) is not bytes or len(raw) > 131072 or case not in play.CASES
                or type(expected_uuid) is not str or not storage.UUID.fullmatch(expected_uuid)):
            return None
        value = terminal(raw)
        if (type(value) is not dict or not BASE <= set(value) or set(value) - (BASE | OPTIONAL)
                or type(value["version"]) is not int or value["version"] != 1 or value["operation"] != "play"
                or value["status"] not in ("completed", "error")):
            return None
        if value["status"] == "completed":
            if value["error"] is not None or not OPTIONAL <= set(value):
                return None
        elif type(value["error"]) is not str or value["error"] not in ERRORS:
            return None
        volumes = value.get("volumes", [])
        if type(volumes) is not list or len(volumes) > 16 or not all(volume(v) for v in volumes):
            return None
        has_play = "play_result" in value
        metrics = value["metrics"]
        if not metrics_valid(metrics, has_play):
            return None
        result = None
        if has_play:
            if value.get("explicit_cache_directory") is not True:
                return None
            validated = play.validate_play_result(value["play_result"], metrics, case)
            if validated is None:
                return None
            result = validated[0]
            if metrics["play_roles"] != result["roles"]:
                return None
        elif value["status"] != "error" or metrics["engines_opened"] or metrics["conversations_opened"]:
            return None
        valid_samples = samples_valid(value, expected_uuid)
        if valid_samples:
            matching = [v for v in volumes if v["volume_uuid"] == expected_uuid]
            valid_samples = len(matching) == 1 and all(matching[0][k] == value["sample"][k] for k in VOLUME)
        return {"result": result, "sdk": metrics, "status": value["status"], "error": value["error"],
                "storage_samples_valid": valid_samples}
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
        return None


def parse_model_identity(raw, expected_uuid):
    """Bind a completed app-domain full read to the selected framework volume.

    This produces only the trusted control callback shape. Caller still verifies
    artifact, transport cleanup, actual backing and fresh storage admission.
    """
    try:
        if type(expected_uuid) is not str or not storage.UUID.fullmatch(expected_uuid):
            return None
        value = terminal(raw)
        if (type(value) is not dict or set(value) != BASE | {"volumes", "sample", "post_sample", "model_identity"}
                or type(value["version"]) is not int or value["version"] != 1
                or value["operation"] != "verify_model" or value["status"] != "completed" or value["error"] is not None):
            return None
        metrics = value["metrics"]
        if (not metrics_valid(metrics, False)
                or set(metrics) != COUNTS | {"owners_balanced", "cleanup_requires_process_termination"}
                or any(metrics[k] != 0 for k in COUNTS - {"main_pulses"})):
            return None
        volumes = value["volumes"]
        if (type(volumes) is not list or len(volumes) > 16 or not all(volume(v) for v in volumes)
                or not samples_valid(value, expected_uuid)):
            return None
        matching = [v for v in volumes if v["volume_uuid"] == expected_uuid]
        if len(matching) != 1 or any(matching[0][k] != value["sample"][k] for k in VOLUME):
            return None
        model = value["model_identity"]
        if (type(model) is not dict or set(model) != MODEL_KEYS or type(model["verified"]) is not bool
                or type(model["sha256"]) is not str or not re.fullmatch(r"(?:[0-9a-f]{64})?", model["sha256"])
                or not integer(model["bytes"]) or type(model["diagnostic"]) is not str
                or model["diagnostic"] not in MODEL_DIAGNOSTICS):
            return None
        exact = model["bytes"] == MODEL_BYTES and model["sha256"] == MODEL_SHA256
        if model["verified"] != (model["diagnostic"] == "verified") or model["verified"] and not exact:
            return None
        return dict(model, volume_uuid=expected_uuid)
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
        return None
