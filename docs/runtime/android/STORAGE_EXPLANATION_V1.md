# Offline storage explanation, version 1

Refs #5, M01.05 partial. This is a read-only explanation of supplied benchmark
samples. It collects no measurements, launches no subprocess/device/model operation,
and grants no permission to write, retry inference or disregard a failed gate.

## Invocation and validation

```powershell
python benchmarks/android_cache_volume.py --sample <private-before.json> --after-sample <private-after.json> --volume-uuid <expected-volume>
```

Each file contains one existing exact cache-volume sample, not a wrapper or
controller report. Both reads are bounded to 16 KiB and use the existing strict
JSON/sample validator. The before sample must pass the unchanged admission
policy. Duplicate/extra keys, nonfinite values, invalid types, inconsistent
measurements for one physical host, invalid copy size and unadmitted before
samples fail without a partial explanation. Input paths and exception text are
not echoed in the result. `--model-copy-bytes` has its existing accounting
meaning; it performs no copy.

The original CLI without `--after-sample` and every controller report retain
their existing output format and behavior. Exit codes in the explicit new mode:
0 means the supplied post-sample passes the existing gate; 2 means blocked;
1 means unavailable/malformed input. None proves fresh device admission.
Argument-syntax errors, including a noninteger `--model-copy-bytes` value,
retain standard argparse usage/stderr and exit 2 before this JSON protocol.

## Result contract

`explain_post(before, after, expected_uuid, model_copy_bytes=0)` returns exactly:

| Key | Meaning |
|---|---|
| `version` | 1, explanation format |
| `scope` | `android_cache_post_explanation` |
| `policy_version` | 1, the current unchanged budget policy |
| `error` | Null on a valid explanation; CLI input failure is `sample_failed` |
| `post` | Exact existing `after_probe` result; null on CLI input failure |
| `comparison_available` | Whether identity permits comparing physical-host groups |
| `host_groups` | At most three rows, empty when comparison is unavailable |

The Python function raises `InvalidSample` on invalid input; for sample/file
and parsed numeric-domain failures the CLI emits the
bounded failure envelope with null post, false comparison and no rows. Identity
drift produces the original blocked `identity_changed` post and no comparisons.
A true comparison flag means comparable supplied observations, not a passing
cohort, authenticated evidence, peak measurement or causal attribution.

Each row has exactly `roles`, `before_free_bytes`, `after_free_bytes`,
`net_consumption_bytes`, `reserve_bytes`, `allowance_bytes`,
`reserve_satisfied`, and `consumption_satisfied`. Roles are ordered
`userdata`, `cache`, `evidence`; the first member determines row order. No
physical alias, UUID, device ID, mount path or private diagnostic is emitted.
Renaming aliases without changing the physical partition does not change output.

## Budget meaning

The existing policy groups logical roles by their observed physical host:

- Reserve is the **maximum** applicable floor, not the sum of free space.
- Allowance is the **sum** of planned growth on that physical host.
- Userdata host contributes 4 GiB reserve and 64 MiB allowance.
- Cache host contributes 4 GiB reserve and 1 GiB plus declared model-copy bytes.
- Evidence host contributes 10 GiB reserve and zero additional growth.

Shared cache/evidence therefore has 10 GiB reserve and 1 GiB growth when no copy
is declared. All three roles on one host have that reserve and 1 GiB +64 MiB
growth. The separate guest userdata/cache and logical-cache-growth checks remain
in `post`; passing host rows cannot override their failure.

Net consumption is before free minus after free, including negative values when
free space increases. It is a whole-volume endpoint observation. It does not
identify an app, responsible writer, allocation peak, lifetime or reason for
consumption. This calculation cannot explain the preceding old-cache metadata
drift or reconstruct missing final preservation checks. Canonical replay,
resource ownership, storage acceptance and preservation remain distinct gates.
