"""Explicit development storage gate around the complete legacy play probe.

No runtime, device mutation or model read occurs merely by importing this module.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path

import android_play_probe as play

GIB = 1024 ** 3
HOST_RESERVE = 4 * GIB
GUEST_RESERVE = GIB
EVIDENCE_RESERVE = 10 * GIB
CACHE_GROWTH_BUDGET = GIB  # Development allowance, not a maximum proven for the SDK.
MAX_BYTES = 2 ** 63 - 1
SAMPLE_KEYS = {"version", "host_free_bytes", "evidence_free_bytes", "guest_free_bytes", "cache_bytes"}


class InvalidSample(ValueError):
    pass


def validate(sample):
    if type(sample) is not dict or set(sample) != SAMPLE_KEYS:
        raise InvalidSample("sample_shape")
    if type(sample["version"]) is not int or sample["version"] != 1:
        raise InvalidSample("sample_version")
    if any(type(sample[k]) is not int or not 0 <= sample[k] <= MAX_BYTES for k in SAMPLE_KEYS - {"version"}):
        raise InvalidSample("sample_value")
    return dict(sample)


def verdict(sample, phase, reasons, **extra):
    return {"version": 1, "phase": phase, "status": "blocked" if reasons else "admitted",
            "reasons": reasons, "sample": sample, "requirements": {
                "host_reserve_bytes": HOST_RESERVE, "guest_reserve_bytes": GUEST_RESERVE,
                "evidence_reserve_bytes": EVIDENCE_RESERVE, "cache_growth_budget_bytes": CACHE_GROWTH_BUDGET}, **extra}


def before_probe(sample):
    sample = validate(sample)
    reasons = [name for key, needed, name in (
        ("host_free_bytes", HOST_RESERVE + CACHE_GROWTH_BUDGET, "host_headroom"),
        ("guest_free_bytes", GUEST_RESERVE + CACHE_GROWTH_BUDGET, "guest_headroom"),
        ("evidence_free_bytes", EVIDENCE_RESERVE, "evidence_headroom")) if sample[key] < needed]
    return verdict(sample, "before", reasons)


def after_probe(before, after):
    before, after = validate(before), validate(after)
    if before_probe(before)["status"] != "admitted":
        raise InvalidSample("before_not_admitted")
    reasons = [name for key, needed, name in (
        ("host_free_bytes", HOST_RESERVE, "host_reserve"),
        ("guest_free_bytes", GUEST_RESERVE, "guest_reserve"),
        ("evidence_free_bytes", EVIDENCE_RESERVE, "evidence_reserve")) if after[key] < needed]
    cache_growth = after["cache_bytes"] - before["cache_bytes"]
    host_consumption = before["host_free_bytes"] - after["host_free_bytes"]
    guest_consumption = before["guest_free_bytes"] - after["guest_free_bytes"]
    if cache_growth < 0:
        reasons.append("cache_decreased")
    for value, name in ((cache_growth, "cache_growth_budget"), (host_consumption, "host_consumption_budget"),
                        (guest_consumption, "guest_consumption_budget")):
        if value > CACHE_GROWTH_BUDGET:
            reasons.append(name)
    # Free-space deltas include other OS activity: they are not causal cache measurements.
    return verdict(after, "after", reasons, observed_deltas={
        "cache_growth_bytes": cache_growth, "host_net_consumption_bytes": host_consumption,
        "guest_net_consumption_bytes": guest_consumption})


@dataclass
class Observation:
    admission: dict
    post: dict = None
    probe_dispatched: bool = False
    result: object = field(default=None, repr=False)
    failure: object = field(default=None, repr=False)
    sample_failure: object = field(default=None, repr=False)

    def metadata(self):
        return {"version": 1, "admission": self.admission, "post": self.post,
                "probe_dispatched": self.probe_dispatched, "probe_raised": self.failure is not None,
                "storage_checks_passed": self.admission["status"] == "admitted" and self.post is not None
                and self.post["status"] == "admitted"}


def sample_failure(phase, reason):
    return {"version": 1, "phase": phase, "status": "blocked", "reasons": [reason], "sample": None}


def run_play_probe_with_admission(measure, device, apk_sha, case, raw_sink=None):
    """Guard the entire trusted controller, including its initial SDK stop.

    The caller owns fresh identity/process admission and the sampler's bounded
    read-only storage/cache collection. This wrapper adds no model/owner proof.
    Legacy direct run_probe callers remain unchanged; use this explicit entry.
    Raw probe result/original exception remain separate from storage verdicts.
    """
    try:
        before = validate(measure())
        pre = before_probe(before)
    except Exception as error:
        return Observation(sample_failure("before", "sample_failed"), sample_failure=error)
    observed = Observation(pre)
    if pre["status"] != "admitted":
        return observed
    observed.probe_dispatched = True
    try:
        observed.result = play.run_probe(device, apk_sha, case, False, raw_sink)
    except Exception as error:
        observed.failure = error
        observed.post = sample_failure("after", "probe_ownership_unknown")
        return observed
    result = observed.result
    if type(result) is not dict or result.get("clients_cleaned") is not True or result.get("process_absent") is not True:
        observed.post = sample_failure("after", "probe_ownership_unknown")
        return observed
    try:
        observed.post = after_probe(before, measure())
    except Exception as error:
        observed.sample_failure = error
        observed.post = sample_failure("after", "sample_failed")
    return observed


def load_sample(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise InvalidSample("duplicate_key")
            value[key] = item
        return value
    with Path(path).open("rb") as source:
        raw = source.read(16 * 1024 + 1)
    if len(raw) > 16 * 1024:
        raise InvalidSample("sample_size")
    return validate(json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                               parse_constant=lambda _: (_ for _ in ()).throw(InvalidSample("nonfinite"))))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", required=True, help="Local, freshly captured storage sample JSON")
    args = parser.parse_args(argv)
    try:
        report = before_probe(load_sample(args.sample))
        code = 0 if report["status"] == "admitted" else 2
    except (OSError, ValueError, UnicodeError, RecursionError):
        report, code = sample_failure("before", "sample_failed"), 1
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
