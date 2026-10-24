# Offline storage explanation verification, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.05 partial, claim
`6376019687`. Exact base is open/unmerged [#117](https://github.com/OptimumAF/LocalLore/pull/117),
`16453e77c6b45d160bfa2c996178d83f68edcd2e`.

## Working change and unchanged authority

The existing generic `host_consumption_budget` reason was correct, but lacked a
physical-group allowance breakdown. The preceding reports initially confused
the userdata host's 64 MiB allowance with the distinct cache host's 1 GiB.
That reporting error motivated an executable explanation, not a different gate.

`android_cache_volume.explain_post` and the explicit `--after-sample` CLI mode
now provide logical-role groups, maximum reserves, summed allowances, signed
endpoint consumption and separate reserve/consumption booleans. Existing strict
input validation, admission verdicts, reason ordering, original CLI and controller
report shapes remain unchanged. Identity drift suppresses comparisons. Invalid
input emits no partial rows or private diagnostic. The [protocol](STORAGE_EXPLANATION_V1.md)
defines the complete bounded schema, exit codes and limitations.

AST comparison against the exact base confirmed all original module assignments
and nine original policy/report/ownership functions/classes unchanged. No Android,
Rust, JNI, SDK, runtime, model or dependency change occurred. No new device call,
model read, inference, installation, copy, eviction, emulator lifecycle or build
was performed. Supplied observations do not establish fresh admission or permit
an inference retry. Diagnostics cannot establish accepted gameplay outcomes.

## Actual checks

```powershell
python -B -E -m unittest discover -s scripts/tests -v
python benchmarks/android_cache_volume.py --sample <private-before.json> --after-sample <private-after.json> --volume-uuid <expected-volume>
```

The final script selection passed **380 tests** in 5.369 seconds. This includes
25 existing volume tests and 20 new independent methods. The independent focused
20-method run also passed; it overlaps the full selection. Tests cover all five
physical partitions, role ordering/alias renaming, shared max-reserve/summed
allowances, model-copy accounting, one-byte boundaries, signed deltas, guest-only
failure despite passing host rows, strict malformed/overflow/type/identity
refusal, no input mutation, bounded CLI JSON, privacy and legacy CLI compatibility.
No device or model is used by these tests. No new JVM, native or physical-device
execution is inferred from earlier checks.

Root verified the original sealed index and exact selected source-file byte
counts/hashes before extracting two private samples. The CLI returned expected
**exit 2**, 1,444 stdout bytes, no stderr. Its `post` object equals the retained
controller's original post **exactly**, including `host_consumption_budget`.
The independent analysis repeated the reconstruction against the frozen old
policy and obtained the same result from the new function/CLI.

| Logical physical group | Reserve | Allowance | Net consumption | Result |
|---|---:|---:|---:|---|
| Userdata host | 4,294,967,296 | 67,108,864 | 2,383,126,528 | Reserve met; consumption exceeded by 2,316,017,664 bytes |
| Shared cache/evidence host | 10,737,418,240 | 1,073,741,824 | 805,814,272 | Reserve and consumption met |

Guest userdata consumption90,112 bytes, guest cache free-space drop788,422,656
bytes and logical cache growth788,412,770 bytes retain their separate checks.
The shared host row does not double-count cache/evidence free space. These are
whole-volume endpoint observations, not peak allocation or app attribution.
The CLI stdout SHA256 is `97f7830024748454a081e7210de1fbbbd9c93dcce73b013706cc9d94ea25f69b`.

## Retained failures and limits

The independent [analysis](STORAGE_EXPLANATION_ANALYSIS_2026-10-23.md) recomputed
the older cache metadata differences from retained raw output. Directory stat
inode and the 34-byte marker's mtime/ctime differed; payload contents were not
hashed. No evidence identifies the writer, physical replacement, timing or cause.
The record cannot attribute the host drop or director timeout either. No new
control or repair was attempted to make these failures disappear.

The preceding director timeout, failed storage gate and incomplete final old
SQLite/journal preservation all remain unchanged. A valid new-turn canonical
replay does not establish preservation of other workspaces. No missing final
preservation or inventory check is reconstructed from inference or intent.

The [safe aggregate](STORAGE_EXPLANATION_RESULTS_2026-10-23.json) contains
**2,706 LF bytes**, SHA256 `c8f1fa6ce0ea71adf28b41a8b160cbef6c692dea4298414cbc9233d940c1273d`.
It includes the original blocked post and content-free explanation; raw sample
identities, aliases, UUIDs, private paths, cache/journal payloads and weights
remain local. See the independent [review](STORAGE_EXPLANATION_REVIEW_2026-10-23.md).

M01.05 remains **in_review, partial**, unchecked pending full criteria and owner
acceptance. M01.01 physical-phone qualification remains blocked. Successful
guarded generation, narration, quality, ARM execution, sustained memory/thermal
and a production backend/profile remain unqualified. Tickets own the plan/worklog;
retired trackers stay pointers. No merge, release or access/protection change.

Next runnable task: implement a bounded preservation collector that records
independent old-workspace checks separately when metadata differs, while still
stopping all dependent reads on uncertain client/process ownership. Host fault
fixtures must prove later canonical checks are not silently skipped or promoted.
Any later device sampling requires a separate fresh ownership/capacity gate;
this packet admits no new device or inference operation.

## Selected-file integrity checkpoints

These private selections bind exact input/log/source bytes and overlap; they do
not seal entire directory trees or add up to unique measurements. Root rehashed
the analysis and independent-test selections with zero mismatches.

| Selection | Files / selected bytes | Index bytes / SHA256 |
|---|---|---|
| Host reconstruction / full script checks | 10 / 50,982 | 1,624 / `bf251aa7a7325d3e8bcac58c4fad533912d8566e63787c95c47f0bb5d4d506c2` |
| Independent retained analysis | 30 / 160,893 | 5,196 / `651d80e56d59a04280b46693eda371733b2a16ed3481a476079d63626bd56cca` |
| Independent focused tests | 6 / 22,851 | 1,391 / `88d00e60a7096c047d1d203cbe3a9049bf925c63f769ab770934ee82529cdd51` |
