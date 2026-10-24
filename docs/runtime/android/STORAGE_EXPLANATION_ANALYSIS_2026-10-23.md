# Storage explanation from sealed evidence, 2026-10-23

Refs #5, M01.05. Host-only reconstruction reproduced the
[role-observation experiment's](ROLE_OBSERVATION_DEVICE_2026-10-23.md) original
`host_consumption_budget` failure exactly. It also independently reproduced the
retained cache-metadata discrepancy. Neither reconstruction establishes the
cause of the host-space drop, metadata drift or director timeout. The experiment
remains failed and milestone acceptance remains pending.

No device, app, model, inference, build or emulator-lifecycle operation ran in
this packet. No gate changed. Seventeen small diagnostic inputs, totaling
121,418 bytes, were copied into a fresh private analysis namespace only after
verifying their size/hash bindings against the original sealed index:
`cb676ad461d2038e3c533ce10bbafc3049a047d76562e2c843bbc77b023f8b8a`.
The selected original inputs were rechecked unchanged before sealing analysis.
No weights, cache payloads or database contents were read.

## Independent storage arithmetic

The executed policy's SHA-256, verified against the original SDK authorization,
was `005194bc7a2d0e4df94d3dae5302f55fc810d6982bb3295c54bff99bf15f3d62`.
Its original post-verdict was reproduced from the supplied pre/post samples.
Independent arithmetic then agreed with the new pure `explain_post` result.
Sampled host-volume identities matched at both endpoints.

The userdata host and the shared cache/evidence host are separate budget groups.
Within one group, reserve is the maximum required reserve and growth allowances
are summed. Thus cache plus evidence requires a 10 GiB reserve and 1 GiB growth
allowance; those roles do not receive two independent free-space balances.
Model-copy bytes were zero.

| Host roles | Before free bytes | After free bytes | Net consumption | Reserve | Consumption allowance | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Userdata | 12,667,879,424 | 10,284,752,896 | 2,383,126,528 | 4,294,967,296 | 67,108,864 | Consumption failed |
| Cache + evidence | 322,707,947,520 | 321,902,133,248 | 805,814,272 | 10,737,418,240 | 1,073,741,824 | Passed |

Both host groups met their reserve floors. The userdata-host consumption exceeded
its **64 MiB** allowance by **2,316,017,664 bytes**. The cache/evidence group
remained **267,927,552 bytes** below its separate **1 GiB** allowance. The latter
headroom cannot cover the former group's failure.

The separate guest observations also reproduced the retained post-report:

- Userdata free-space net consumption: 90,112 bytes, within 64 MiB.
- Cache-filesystem free-space net consumption: 788,422,656 bytes, within 1 GiB.
- Logical cache-file growth: 788,412,770 bytes, within 1 GiB.

These quantities measure different layers. Guest free-space changes, logical
file sizes and host-volume free-space changes are not a per-writer accounting
ledger. Subtracting one from another cannot identify an app's physical writes.
Endpoint net changes do not reveal peak consumption or when within the operation
the change occurred. Stable sampled volume identities do not exclude concurrent
writers. The records supply no causal link from the host-space drop to the
director timeout, and the budget failure alone does not establish storage
exhaustion or an I/O failure.

## Retained metadata comparison

The analysis re-read the exact retained command outputs already bound by the
local closure receipt. It independently matched every recorded difference.
The older prior-cache metadata matched completely. In the older guarded cache:

- The directory's reported `stat` inode field differed.
- Its 34-byte owner marker's modification and change timestamps each decreased
  by one reported second.
- Every other reported field in those four metadata rows matched, including the
  model-stat row and generated-cache-file row.

Those are observed shell-stat differences. They do not establish directory
replacement, marker-content change or which operation caused the discrepancy.
No cache/marker payload hash was captured. Timestamp values do not supply a
reliable event ordering for this unexplained drift. No repair, permission change,
cache eviction or further device query was performed to test a hypothesis.

The original closure assertion correctly remained failed. Its interruption left
final re-observation of the old canonical databases/phase journals, final inventory
and final storage accounting incomplete. Earlier preparation preservation checks
cannot fill those gaps. This analysis does not retrospectively declare them
passed.

## Reproducibility and limits

The private analysis script verified selected input bindings, exact original
policy reproduction, independent host-group arithmetic, equality with the new
explanation, sampled host identities and raw metadata differences. The actual
host-only CLI used the extracted before/after samples with:

```text
python -B -E benchmarks/android_cache_volume.py --sample BEFORE.json --after-sample AFTER.json --volume-uuid PRIVATE_EXPECTED_UUID
```

It returned **2** in 157 ms, with 1,444 stdout bytes and no stderr. The decoded
explanation exactly matched the independent arithmetic and original post-verdict;
its sole reason remained `host_consumption_budget`. This command only assessed
supplied evidence; it collected no measurements and authorized no device work.
The explaining module SHA-256 was
`f0493b72b3db69b4152bef2f5e28c2dac2faef81ff1dbdda113cdf5773c10d6a`.

The retained SDK/observer durations describe one failed attempt. There are no
continuous host-I/O or per-writer measurements to place the storage drop within
those durations or explain its relation to the timeout. The old cache metadata
was observed before/after the cohort, without an intervening mutation trace.
No root cause, successful runtime profile, model quality, physical-phone result
or ARM execution qualification follows from this analysis.

The next runnable task is host-only review of a bounded timing/storage-observation
contract and deterministic attribution-limit fixtures before proposing another
device experiment. This report authorizes no rerun or threshold adjustment.

## Sealed analysis

The new private index binds 30 files / 160,893 bytes: selected inputs, frozen
policy/explaining sources, arithmetic script/results, CLI raw output/process
receipt and sanitized handoff. Original sealed evidence remains separate.

- Analysis index SHA-256:
  `651d80e56d59a04280b46693eda371733b2a16ed3481a476079d63626bd56cca`.
- Sanitized handoff SHA-256:
  `921f9ec297621d8fca48143c83f4ff4a7913316c7acef69b6fa7d7fa43f3cc54`.
