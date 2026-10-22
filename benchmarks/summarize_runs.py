"""Offline aggregate calculator for synthetic M01 traces; never runs inference.

Input is JSONL with one completed turn per record. It accepts host or physical
measurements, but keeps their provenance separate and refuses fake-provider data.
No generated prose, prompt, device ID, or hidden reasoning is needed by this tool.
"""

import argparse
import json
import math
import re
from pathlib import Path

TIMINGS = (
    "retrieval_ms", "director_prefill_ms", "director_decode_ms", "validation_ms",
    "repair_ms", "narrator_prefill_ms", "narrator_decode_ms", "commit_ms",
    "turn_ms", "first_final_response_ms",
)
PROVENANCE = (
    "environment", "profile_id", "app_commit", "runtime_commit", "model_sha256",
    "fixture_version", "schema_version", "prompt_version", "condition",
)


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return value


def percentile(values, percent):
    """Nearest rank; caller supplies at least one finite sample."""
    return sorted(values)[max(0, math.ceil(percent * len(values)) - 1)]


def summarize(records):
    if not records:
        raise ValueError("No measured completed turns; no statistics can be reported")
    seen = set()
    identity = None
    for row in records:
        if row.get("kind") != "real_model_measurement":
            raise ValueError("Fake/provider unit traces are not real-model measurements")
        current = tuple(row.get(key) for key in PROVENANCE)
        if any(not isinstance(value, str) or not value for value in current):
            raise ValueError("Complete string provenance is required")
        if row["environment"] not in ("host", "physical_android"):
            raise ValueError("Unknown measurement environment")
        if row["condition"] not in ("cold", "warm", "sustained"):
            raise ValueError("Unknown measurement condition")
        for key, length in (("app_commit", 40), ("runtime_commit", 40), ("model_sha256", 64)):
            if not re.fullmatch(f"[0-9a-f]{{{length}}}", row[key]):
                raise ValueError(f"{key} must be an exact lowercase hexadecimal digest")
        if identity is not None and identity != current:
            raise ValueError("Split different profiles, revisions, and conditions before aggregation")
        identity = current
        turn_id = row.get("turn_id")
        if not isinstance(turn_id, str) or not turn_id or turn_id in seen:
            raise ValueError("Unique completed turn IDs are required")
        seen.add(turn_id)
        for key in TIMINGS:
            number(row.get(key), key)
        if row["first_final_response_ms"] < row["turn_ms"]:
            raise ValueError("Final response cannot precede the completed commit")
        stages = sum(row[key] for key in TIMINGS[:8])
        if stages > row["turn_ms"]:
            raise ValueError("Sequential stage timings exceed end-to-end turn time")
        for key in ("schema_valid_before_repair", "proposal_accepted", "repaired", "narrator_faithful"):
            if not isinstance(row.get(key), bool):
                raise ValueError(f"{key} requires an explicit Boolean assessment")
        repairs = row.get("repair_count")
        if isinstance(repairs, bool) or not isinstance(repairs, int) or repairs not in (0, 1):
            raise ValueError("Initial protocol permits at most one repair")
        if row["repaired"] != (repairs == 1):
            raise ValueError("Repair count and assessment disagree")
        if row.get("peak_memory_bytes") is not None:
            number(row["peak_memory_bytes"], "peak_memory_bytes")
    count = len(records)
    result = {"status": "aggregate_only_not_qualification", "sample_count": count,
              "provenance": dict(zip(PROVENANCE, identity)), "percentile_method": "nearest_rank"}
    result["timings_ms"] = {
        key: {"p50": percentile([r[key] for r in records], .5),
              "p95": percentile([r[key] for r in records], .95)} for key in TIMINGS
    }
    result["assessments"] = {
        key: {"count": sum(r[key] for r in records), "denominator": count}
        for key in ("schema_valid_before_repair", "proposal_accepted", "repaired", "narrator_faithful")
    }
    observed = [r["peak_memory_bytes"] for r in records if r.get("peak_memory_bytes") is not None]
    result["peak_memory_bytes"] = {"max_observed": max(observed) if observed else None,
                                   "observed_count": len(observed)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    try:
        # Bounded input keeps accidental raw diagnostic dumps out of this calculator.
        if args.trace.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("Trace exceeds the 8 MiB aggregate input limit")
        rows = [json.loads(line) for line in args.trace.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) > 10000 or any(not isinstance(row, dict) for row in rows):
            raise ValueError("Expected at most 10000 turn objects")
        print(json.dumps(summarize(rows), indent=2, allow_nan=False))
    except (ValueError, OSError) as error:
        parser.exit(2, f"Invalid measurement trace: {error}\n")


if __name__ == "__main__":
    main()
