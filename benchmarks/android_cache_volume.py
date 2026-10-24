"""Explicit development admission for a separately backed Android cache volume.

Assessment does not collect evidence or establish identity, freshness or ownership.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
from dataclasses import dataclass, field
import json
import re

from android_probe_admission import GIB, MAX_BYTES, InvalidSample
from android_runtime_spike import strict_json

USERDATA_RESERVE = GIB
USERDATA_ALLOWANCE = 64 * 1024 ** 2
CACHE_RESERVE = GIB
CACHE_ALLOWANCE = GIB  # Planned growth, not a proven SDK maximum or live quota.
HOST_RESERVE = 4 * GIB
EVIDENCE_RESERVE = 10 * GIB
BYTE_KEYS = {"userdata_free_bytes", "cache_free_bytes", "cache_bytes", "userdata_host_free_bytes",
             "cache_host_free_bytes", "evidence_free_bytes"}
BOOL_KEYS = {"mounted", "primary", "emulated", "writable", "backing_verified"}
HOST_KEYS = {"userdata_host_volume", "cache_host_volume", "evidence_host_volume"}
DEVICE_KEYS = {"userdata_device", "cache_device"}
KEYS = {"version", "volume_uuid"} | BYTE_KEYS | BOOL_KEYS | HOST_KEYS | DEVICE_KEYS
UUID = re.compile(r"(?:[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}|[A-Fa-f0-9]{8}(?:-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})\Z")
ALIAS = re.compile(r"[a-z0-9_-]{1,64}\Z")


def copy_size(value):
    if type(value) is not int or not 0 <= value <= MAX_BYTES - CACHE_RESERVE - CACHE_ALLOWANCE:
        raise InvalidSample("copy_bytes")
    return value


def validate(sample):
    if type(sample) is not dict or set(sample) != KEYS:
        raise InvalidSample("sample_shape")
    if type(sample["version"]) is not int or sample["version"] != 1:
        raise InvalidSample("sample_version")
    if type(sample["volume_uuid"]) is not str or not UUID.fullmatch(sample["volume_uuid"]):
        raise InvalidSample("volume_uuid")
    if any(type(sample[k]) is not int or not 0 <= sample[k] <= MAX_BYTES for k in BYTE_KEYS):
        raise InvalidSample("byte_value")
    if any(type(sample[k]) is not int or not 1 <= sample[k] <= MAX_BYTES for k in DEVICE_KEYS):
        raise InvalidSample("device_value")
    if any(type(sample[k]) is not bool for k in BOOL_KEYS):
        raise InvalidSample("boolean_value")
    if any(type(sample[k]) is not str or not ALIAS.fullmatch(sample[k]) for k in HOST_KEYS):
        raise InvalidSample("host_alias")
    host_budgets(sample)  # Shared physical volume measurements must agree exactly.
    return dict(sample)


def host_budgets(sample, model_copy_bytes=0):
    groups = {}
    for volume_key, free_key, reserve, growth in (
            ("userdata_host_volume", "userdata_host_free_bytes", HOST_RESERVE, USERDATA_ALLOWANCE),
            ("cache_host_volume", "cache_host_free_bytes", HOST_RESERVE, CACHE_ALLOWANCE + model_copy_bytes),
            ("evidence_host_volume", "evidence_free_bytes", EVIDENCE_RESERVE, 0)):
        alias, free = sample[volume_key], sample[free_key]
        if alias in groups and groups[alias]["free"] != free:
            raise InvalidSample("inconsistent_host_free")
        group = groups.setdefault(alias, {"free": free, "reserve": 0, "growth": 0})
        group["reserve"] = max(group["reserve"], reserve)
        group["growth"] += growth
    return groups


def identity(sample):
    return tuple(sample[k] for k in sorted({"volume_uuid"} | DEVICE_KEYS | HOST_KEYS | BOOL_KEYS))


def report(phase, reasons, sample, **extra):
    # Raw UUIDs, host-volume aliases, mount paths and original exceptions stay private.
    return {"version": 1, "phase": phase, "status": "blocked" if reasons else "admitted",
            "reasons": reasons, "bytes": {k: sample[k] for k in sorted(BYTE_KEYS)} if sample else None, **extra}


def before_probe(sample, expected_uuid, model_copy_bytes=0):
    sample = validate(sample)
    model_copy_bytes = copy_size(model_copy_bytes)
    if type(expected_uuid) is not str or not UUID.fullmatch(expected_uuid):
        raise InvalidSample("expected_uuid")
    reasons = []
    for blocked, reason in (
            (sample["volume_uuid"] != expected_uuid, "volume_mismatch"),
            (not sample["mounted"], "not_mounted"), (sample["primary"], "primary_volume"),
            (sample["emulated"], "emulated_volume"), (not sample["writable"], "not_writable"),
            (not sample["backing_verified"], "backing_unverified"),
            (sample["cache_device"] == sample["userdata_device"], "shared_guest_filesystem"),
            (sample["userdata_free_bytes"] < USERDATA_RESERVE + USERDATA_ALLOWANCE, "userdata_headroom"),
            (sample["cache_free_bytes"] < CACHE_RESERVE + CACHE_ALLOWANCE + model_copy_bytes, "cache_headroom")):
        if blocked:
            reasons.append(reason)
    groups = host_budgets(sample, model_copy_bytes)
    if any(g["free"] < g["reserve"] + g["growth"] for g in groups.values()):
        reasons.append("host_headroom")
    return report("before", reasons, sample, model_copy_bytes=model_copy_bytes)


def after_probe(before, after, expected_uuid, model_copy_bytes=0):
    before, after = validate(before), validate(after)
    if before_probe(before, expected_uuid, model_copy_bytes)["status"] != "admitted":
        raise InvalidSample("before_not_admitted")
    reasons = []
    if identity(before) != identity(after):
        # A remounted/replaced volume is not a meaningful consumption comparison.
        return report("after", ["identity_changed"], after)
    if after["userdata_free_bytes"] < USERDATA_RESERVE:
        reasons.append("userdata_reserve")
    if after["cache_free_bytes"] < CACHE_RESERVE:
        reasons.append("cache_reserve")
    userdata_used = before["userdata_free_bytes"] - after["userdata_free_bytes"]
    cache_used = before["cache_free_bytes"] - after["cache_free_bytes"]
    growth = after["cache_bytes"] - before["cache_bytes"]
    for blocked, reason in ((growth < 0, "cache_decreased"), (growth > CACHE_ALLOWANCE, "cache_growth_budget"),
                            (userdata_used > USERDATA_ALLOWANCE, "userdata_consumption_budget"),
                            (cache_used > CACHE_ALLOWANCE + model_copy_bytes, "cache_consumption_budget")):
        if blocked:
            reasons.append(reason)
    pre_hosts, post_hosts = host_budgets(before, model_copy_bytes), host_budgets(after, model_copy_bytes)
    if any(g["free"] < g["reserve"] for g in post_hosts.values()):
        reasons.append("host_reserve")
    if any(g["free"] - post_hosts[k]["free"] > g["growth"] for k, g in pre_hosts.items()):
        reasons.append("host_consumption_budget")
    return report("after", reasons, after, observed_deltas={"cache_growth_bytes": growth,
                  "userdata_net_consumption_bytes": userdata_used, "cache_net_consumption_bytes": cache_used})


def _explanation(post=None, groups=None, error=None):
    return {"version": 1, "scope": "android_cache_post_explanation", "policy_version": 1,
            "error": error, "post": post, "comparison_available": groups is not None,
            "host_groups": groups if groups is not None else []}


def explain_post(before, after, expected_uuid, model_copy_bytes=0):
    """Explain the existing gate using supplied samples; collect or authorize nothing.

    The original verdict and reason order remain authoritative. Host-wide net
    deltas do not attribute consumption to an app or expose peak consumption.
    Logical roles describe shared physical groups without emitting their private
    aliases, UUID, device identities or paths. Identity drift forbids comparison.
    """
    before, after = validate(before), validate(after)
    model_copy_bytes = copy_size(model_copy_bytes)
    post = after_probe(before, after, expected_uuid, model_copy_bytes)
    if identity(before) != identity(after):
        return _explanation(post)
    pre_hosts, post_hosts = host_budgets(before, model_copy_bytes), host_budgets(after, model_copy_bytes)
    # First logical role determines order, never an arbitrary physical alias.
    roles = {}
    for role, key in (("userdata", "userdata_host_volume"), ("cache", "cache_host_volume"),
                      ("evidence", "evidence_host_volume")):
        roles.setdefault(before[key], []).append(role)
    rows = []
    for alias, members in roles.items():
        pre, final = pre_hosts[alias], post_hosts[alias]
        consumption = pre["free"] - final["free"]
        rows.append({"roles": members, "before_free_bytes": pre["free"], "after_free_bytes": final["free"],
                     "net_consumption_bytes": consumption, "reserve_bytes": pre["reserve"],
                     "allowance_bytes": pre["growth"], "reserve_satisfied": final["free"] >= pre["reserve"],
                     "consumption_satisfied": consumption <= pre["growth"]})
    return _explanation(post, rows)


@dataclass
class Observation:
    admission: dict
    post: dict = None
    dispatched: bool = False
    result: object = field(default=None, repr=False)
    failure: object = field(default=None, repr=False)
    sample_failure: object = field(default=None, repr=False)

    def metadata(self):
        return {"version": 1, "admission": self.admission, "post": self.post, "dispatched": self.dispatched,
                "operation_raised": self.failure is not None, "storage_checks_passed":
                self.admission["status"] == "admitted" and self.post is not None and self.post["status"] == "admitted"}


def run_with_admission(measure, operation, expected_uuid, model_copy_bytes=0):
    """One attempt; trusted caller owns fresh evidence, whole callback and later fencing.

    No device dispatch, provisioning, model integrity or cleanup recovery is built in.
    Unknown ownership means no dependent post-read, even if operation raised.
    """
    try:
        before = validate(measure())
        pre = before_probe(before, expected_uuid, model_copy_bytes)
    except Exception as error:
        return Observation(report("before", ["sample_failed"], None), sample_failure=error)
    observed = Observation(pre)
    if pre["status"] != "admitted":
        return observed
    observed.dispatched = True
    try:
        observed.result = operation()
    except Exception as error:
        observed.failure = error
        observed.post = report("after", ["operation_ownership_unknown"], None)
        return observed
    result = observed.result
    if type(result) is not dict or result.get("clients_cleaned") is not True or result.get("process_absent") is not True:
        observed.post = report("after", ["operation_ownership_unknown"], None)
        return observed
    try:
        observed.post = after_probe(before, measure(), expected_uuid, model_copy_bytes)
    except Exception as error:
        observed.sample_failure = error
        observed.post = report("after", ["sample_failed"], None)
    return observed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--after-sample", help="Explain a supplied post-sample without collecting or dispatching anything")
    parser.add_argument("--volume-uuid", required=True)
    parser.add_argument("--model-copy-bytes", type=int, default=0)
    args = parser.parse_args(argv)
    try:
        with open(args.sample, "rb") as source:
            raw = source.read(16385)
        if len(raw) > 16384:
            raise InvalidSample("sample_size")
        before = strict_json(raw)
        if args.after_sample is not None:
            with open(args.after_sample, "rb") as source:
                after_raw = source.read(16385)
            if len(after_raw) > 16384:
                raise InvalidSample("sample_size")
            value = explain_post(before, strict_json(after_raw), args.volume_uuid, args.model_copy_bytes)
            code = 0 if value["post"]["status"] == "admitted" else 2
        else:
            value = before_probe(before, args.volume_uuid, args.model_copy_bytes)
            code = 0 if value["status"] == "admitted" else 2
    except (OSError, ValueError, UnicodeError, RecursionError):
        value, code = (_explanation(error="sample_failed") if args.after_sample is not None
                       else report("before", ["sample_failed"], None)), 1
    print(json.dumps(value, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
