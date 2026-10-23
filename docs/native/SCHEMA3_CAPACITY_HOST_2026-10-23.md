# Schema3 host capacity calibration, 2026-10-23

Refs [#8](https://github.com/OptimumAF/LocalLore/issues/8) (M04.04).
Base `a1b1cc97639860bccf1d92253c9bcfe286d15809`; final host source
`61fe628f020f6efbb62d12e877b2a8c143dfd9b0`.
This qualifies the bounded synthetic host fixtures on schema3. Android
qualification and owner acceptance remain separate. Historical schema1 capacity
reports remain unchanged and describe their original binaries.

## Measured boundaries

All runs used fresh retained task-owned directories and isolated Cargo targets
on a roomy secondary host volume. Each capped target separately compiled bundled
SQLite with its stated `LIBSQLITE3_FLAGS`; ordinary build caches were not reused.
The fixture uses the existing Lantern Quay seed, prefix0, original 36-byte key,
deterministic accepted provider and typed potion gift. No gameplay/store/JNI
production rule or dependency changed.

| Run | Actual result |
|---|---|
| Uncapped | Create/draft/Ready: 69,632 bytes, **17 pages**; accepted gift: 73,728 bytes, **18 pages**. Exact retry and reopen passed. |
| Old 15-page ceiling | Failed at story `create`; it cannot exercise the old Ready-to-Full fixture on current schema3. |
| 16-page ceiling | Failed at story `create`. |
| 17-page ceiling | Create/draft/Ready fit; two gift commits returned `Full`. The live original key stayed Ready, canonical snapshot stayed unchanged, and reopening recovered the original queued key at revision0. |
| 32-page relief, accept | Fill14 rows; insert15 returned SQLite Full, pages32/free0. Drop14 rows restored exact schema, freeing15 pages. The same live Ready key committed once at revision1/receipt1; exact retry and strict reopen passed. |
| 32-page relief, cancel | Same measured fill/drop. Cancel while full left revision0/receipt0 and a terminal original key after relief and strict reopen. |

The minimum measured ceiling that fits this exact Ready fixture while making its
gift Full is **17**; 16 fails earlier. The relief ceiling remains **32**. Both
relief paths issued **zero fresh submits and zero fresh prepares** after relief.
Native reopen rejected the temporary padding schema; only exact restoration
permitted subsequent native reopening. These are SQLite page-ceiling simulations,
not partition/disk ENOSPC tests. They establish no device, model, ARM64, latency
or physical-phone qualification.

## Exact schema and helper guards

The [Python helper](../../scripts/capacity_padding_probe.py) builds its reference
in a separate in-memory connection by executing migrations001,002,003 in order.
It does not adopt the incoming database as its reference. Before **opening the
target writable**, it checks the owned absolute canonical directory, non-link marker and
database, fixed basename, bounded database size, then opens `mode=ro` and checks:

- application ID `0x4c4c4f52`, user version3, page size4096, DELETE journal,
  auto-vacuum0 and no active transaction;
- every expected user schema object and its exact SQL, with only the one fixed
  owned padding table allowed for removal;
- exact migration rows `(1,locallore-storage-v1)`,
  `(2,locallore-storage-v2-derived-memory)`,
  `(3,locallore-storage-v3-branch-retention)`;
- measured initial17 pages/free0 before filling, or bounded contiguous padding
  IDs with the exact owner and 3,500-byte zero payloads before removal.

After closing the reader it rechecks path/marker and file identity, opens
`mode=rw`, and repeats schema, migration and metadata validation before changing
the connection ceiling or writing. It only creates/inserts/drops
`locallore_capacity_pad_v1`; no arbitrary SQL input exists. Removal validates
owned rows first and proves exact schema/migration restoration afterward. The
temporary extra table deliberately violates the production exact-schema gate.

Reference and actual Rust Store files matched this digest:
`c05ced1f0439fb767f97d2ff93a34ef44eb6fbc27da6814a75fad455fb0b2c17`.
The shared cross-platform digest recipe is:

```sql
SELECT type,name,tbl_name,sql FROM sqlite_master
WHERE name NOT GLOB 'sqlite_*' AND name<>'locallore_capacity_pad_v1'
ORDER BY type,name,tbl_name;
```

For each of the four fields in row order, hash byte0 for null; otherwise byte1,
then a big-endian unsigned32 UTF-8 byte length, then those UTF-8 bytes. Hash the
concatenation with SHA256. The helper's exact-row comparison also rejects any
unexpected pad or other user object; excluding the pad from the reference digest
does not permit arbitrary extra schema. The independently migrated empty SQL
reference has15 pages; the actual seeded Ready fixture has17.

Both examples and helper reports now use **version2/database_schema_version3**;
the helper also reports `schema_sha256`. The relief runner binds those fields,
the fixed measured fill/removal counts and its 32-page ceiling. Child outputs are
bounded to4KiB, execution to10 seconds, and terminal cleanup observation to2
seconds after kill. Unknown child ownership prohibits further helper/Host work.
A failed fill attempts only fixed owned-table cleanup after known child exit;
it never proceeds to Host calls. The actual Python `sqlite3` library reported
SQLite **3.38.2**. Its missing `sqlite_errorcode` attribute
required the existing exact `database or disk is full` fallback for the fixed
INSERT; arbitrary errors stay failures.

## Reproduction and checks

The following preserve the actual argument sets, with private host locations
replaced by `$capacityRoot` and `$python`. Use a fresh task-owned root on a roomy
volume, create its `tmp` directory, and set `TEMP`/`TMP` there. Every example
directory below must not exist. Outputs and failed attempts were retained.

```powershell
$env:TEMP="$capacityRoot\tmp"
$env:TMP=$env:TEMP
Remove-Item Env:LIBSQLITE3_FLAGS -ErrorAction SilentlyContinue
$env:CARGO_TARGET_DIR="$capacityRoot\uncapped-target"
cargo +1.93.1 run -p locallore-workspace --example capacity_probe --locked --offline -- --directory "$capacityRoot\uncapped-prefix0-final" --prefix 0

# Run each ceiling in a separate Cargo target; 15 and16 intentionally fail create.
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=15'
$env:CARGO_TARGET_DIR="$capacityRoot\cap15-target"
cargo +1.93.1 run -p locallore-workspace --example capacity_probe --locked --offline -- --directory "$capacityRoot\cap15-prefix0" --prefix 0 --expect-full
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=16'
$env:CARGO_TARGET_DIR="$capacityRoot\cap16-target"
cargo +1.93.1 run -p locallore-workspace --example capacity_probe --locked --offline -- --directory "$capacityRoot\cap16-prefix0" --prefix 0 --expect-full
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=17'
$env:CARGO_TARGET_DIR="$capacityRoot\cap17-target"
cargo +1.93.1 run -p locallore-workspace --example capacity_probe --locked --offline -- --directory "$capacityRoot\cap17-prefix0-final" --prefix 0 --expect-full

$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=32'
$env:CARGO_TARGET_DIR="$capacityRoot\cap32-target"
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline -- --directory "$capacityRoot\cap32-accept-final" --python $python
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline -- --directory "$capacityRoot\cap32-cancel-final" --python $python --cancel
cargo +1.93.1 clippy -p locallore-workspace --all-targets --locked --offline -- -D warnings
python -B -m unittest discover -s scripts/tests -p test_capacity_padding_probe.py -v
cargo +1.93.1 fmt --all -- --check
git diff --check
```

Final results: both relief paths and the uncapped/17-page examples passed;
**26 Python guards**, package/all-target strict Clippy, formatting and whitespace
checks passed. Guards include old/future/foreign versions, missing/altered schema,
missing migration records, read-only-before-writable refusal, metadata/marker
drift, wrong/modified/noncontiguous padding, bounded files, unsupported actions
and exact Full classification. No full workspace test suite or device execution
is claimed by these commands.

## Retained attempt identities

Raw logs stay private; the following lengths/digests identify all13 retained
attempt/check logs. Early uncapped/15/16/17 logs preceded reportversion2; final
uncapped/17 and relief runs verified the final source. The initial relief run
preceded explicit measured-count assertions; its successful result was retained,
then both final paths passed with those assertions. No failed run was discarded.

| Evidence ID | Bytes | SHA256 |
|---|---:|---|
| cap15-prefix0.log | 2157 | `ff3f53dbe46453425f4379a27644a49c62a85f05b4c05cbb0dfdc4c44a825bc4` |
| cap16-prefix0.log | 2157 | `2190987503c18175fddcdd2d9b7866ea790208b18760f2fcc381dd53e8178d29` |
| cap17-prefix0-final.log | 1096 | `596d63fcf74c932009f3f19dde2148b20ce54328e38f780ad248244163b6b9e6` |
| cap17-prefix0.log | 2280 | `014f96701f72b5cf03e909579332c8ee36571e639147e9fea5ead7d97c32a7a4` |
| cap32-accept-final.log | 1384 | `0f6d57f5992fbc163ca378567a8454d31fa9bd5e0178f5d86ded3a3eebac341c` |
| cap32-accept-initial.log | 2887 | `d08a89613ca0e26f3b8fa059c627ea32b09d504537265d74b7a6342783df1f2f` |
| cap32-cancel-final.log | 1456 | `6dc52590ef6ac0269e29e19358b6618e1aad9eca01f9e86d3446e6eeb4fdf89c` |
| clippy-final.log | 1216 | `2585a5e8b1909acb1dcea7ba945e0973437af5c09617f8fcbb208f7c570ecc92` |
| fmt-final.log | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| python-final.log | 2910 | `122626bcc98e4a8b98a8f02d54ba7f7f44e9b49ed64cbf236d0f6cb1de800398` |
| python-initial.log | 2910 | `dc23d5261a93f61683303b6072763b1adf53f3a24828d493d4539c9b39c7c265` |
| uncapped-prefix0-final.log | 932 | `96b218a64d9133a1a2eac9e295873c6bae5730ad393beab4f8808ad4a9c3e360` |
| uncapped-prefix0.log | 2275 | `c7d72c54ec70c720e327b81b345a66ab5fb44973a3b4739e458575e561875718` |

The private aggregate `handoff-measurements.json` SHA256 is
`2f20da0606e8342291a0b616480bb90835e20505729cdcba3f0370b71ac10630`.
No raw database/story content, private paths or model data is included here.
