# Synthetic platform roundtrip fixture v1

M08.06 verification only, stacked on unmerged Android archive PR #76. Shared
archive v1, Store/Engine and existing JNI/Host are unchanged. No model calls,
desktop UI, system chooser or physical-phone qualification is implied.

## Native fixture example (exclusive native agent)

`cargo +1.93.1 run -p locallore-android --example platform_roundtrip --locked --offline -- --development-fixtures <generate|verify|check-final> --directory NEW [--inputs DIR] [--fixtures DIR]`

Require the explicit development switch; exact known arguments only. Optional
`--owned-stdin` requires EOF from a bounded one-byte stdin read before filesystem
work; the process-owning runner supplies it, manual commands need no stdin. Each
command creates a NEW output directory, refuses existing/linked targets, writes
only fixed files and never recursively deletes anything. Inputs are fixed names
in explicitly selected directories, regular nonlinks, at most 128 KiB each for
this small fixture (not a change to the production archive's 32 MiB limit).
Errors print fixed categories, no SQL/prose/paths. No new dependency pins.

`generate`: original Lantern Quay seed with story `platform-windows-v1`, root
`main`, title `Synthetic Windows transfer`. Apply wait/1 as `shared-prefix`,
fork `child` at 1, give sole potion to Mira on main as `same-turn-key`, consume
sole potion on child as `same-turn-key`, fork `sibling` from main at 1, say
`PLATFORM_SIBLING_CANARY` only to Mira on sibling as `sibling-private`.
All three heads are 2, four local receipts total. Export `windows-origin.json`.
Create a source noncommitted draft `EXCLUDED_PLATFORM_DRAFT`; confirm absent
from archive. Shared canonical state hashes are computed by Store, not Kotlin.

Using actual WorkspaceRegistry Host submit/prepare/commit, continue sibling with
give potion to Mira as `android-transfer-gift-v1`, expected head 2, accepted head
3; export `windows-continued.json`. Exact retry must not increment the head;
new-key duplicate spend must reject without mutation. Reopen and preserve
main/child heads and canonical state. Emit `expectations.json`:

```
{version:1,fixture:"locallore-platform-roundtrip-v1",
 windows:{story:"platform-windows-v1",root:"main",continuation_branch:"sibling",
  continuation_turn:"android-transfer-gift-v1",branch_heads:{main:2,child:2,sibling:2},
  snapshots:{main:<play_snapshot data>,child:<data>,sibling:<data>},
  continued_snapshots:{main:<data>,child:<data>,sibling:<data>}}}
```

Snapshots are exact engine-derived Host `play_snapshot` data, excluding no fields;
they include scope/revision/rules/player/inventory/receipts with original scopes.
Host `inspect` allows player only in Android's non-Lab adapter; NPC requests must
remain Forbidden. Independently compare real Engine contexts for player/Mira/Sable
on Windows before/after transfers, including sibling/future/hidden-fact canaries.
The accepted workspace catalog lists one row per story root, not one row per
branch. Verify the three branch snapshots/heads separately; import adds one
catalog row. Source inspection corrected the initial test assumption before run.

`verify --inputs DIR --fixtures DIR`: inputs fixed `windows-return.json`,
`windows-continued.json`, `android-origin.json`. Compare returned Windows bytes
exactly to generated fixture files, validate/replay/import in fresh owned stores,
check resources/contexts/receipts/heads and unrelated-story preservation. Android
origin is actual Host-created Lantern Quay with random engine-owned story ID,
title `Lantern Quay`, root main/head1, one accepted give-potion receipt with turn
`android-origin-gift-v1`. Construct expected Engine from the unchanged fixture
seed with only story ID substituted; compare exact seed, canonical state,
receipts and NPC contexts. No archive-provided rule/reference is auto-loaded.
Export same bytes after import/reopen, retry original committed receipt exactly,
then actual Host wait/1 as `windows-return-wait-v1`, head1 ->2. Emit
`android-return.json`. Confirm duplicate potion spend refuses without mutation.
Clone/import into another fresh test Store, actual Host wait/1 as
`android-final-wait-v1`, head2 ->3, emit `expected-android-final.json`.

`check-final --inputs DIR --fixtures DIR`: fixed input `android-final.json`,
fixtures from previous verify output with `expected-android-final.json`.
Require exact byte equality, actual Store validation/import/reopen/replay,
canonical fingerprint/receipts and observer checks. Emit small fixed-category
`result.json` and print a small fixed summary in every successful CLI mode.

## Android instrumentation (exclusive Android agent)

Only NEW `ArchivePlatformRoundTripTest.kt`, one `@Test` method with explicit Unit.
Arguments: `platform_phase=outbound|return`, `platform_run=<[a-z0-9-]{1,48}>`.
Use IO workers, actual NativeArchive and NativeWorkspace; no new JNI/prod API.
All calls close exact handles in finally, assert staging empty, never touch the
default workspace or delete existing fixtures. Use fresh child DB directories
within `noBackupFilesDir/platform-roundtrip/<run>` exclusively created at outbound,
marker `owner-v1` bytes `locallore-platform-roundtrip-v1` (no newline). Base may
exist only if a real nonlinked directory. Refuse preexisting run. All output
fixed names with create-new semantics. Keep files as evidence.

Test assets are root-owned generated `platform-roundtrip-v1/windows-origin.json`,
`windows-continued.json`, `expectations.json`. Bound fixture reads to 128 KiB.

Outbound imports Windows origin into fresh SQLite opened via NativeWorkspace;
before explicit commit, library must contain no imported story. Reopen, export
exact original bytes as `windows-return.json`, compare every branch's actual
Host play_snapshot to manifest and verify nonplayer inspect remains Forbidden.
Continue sibling with the fixed give command via actual fake Host and verify
exact committed retry/no duplicate spend, unchanged other branches and exact
`windows-continued.json` expected bytes; write that output. Separately create a
new synthetic story using actual Host create/lantern-quay-v1, submit/prepare/commit
give-potion as `android-origin-gift-v1`, head0 ->1; retry exact original key,
new-key duplicate spend rejects/head stays1. Export `android-origin.json`.

Return phase requires existing exact owned run marker, fixed regular nonlinked
input `android-return.json` written exclusively by the coordinator. Import to a
NEW fresh DB, reexport identical bytes after reopen, root main/head2. Retry the
recorded `windows-return-wait-v1` receipt using its original request, then new-key
give-potion rejects/head stays2. Actual Host wait/1 as `android-final-wait-v1`
commits head3; retry exact key/head stable. Export `android-final.json`.
Do not print archive prose, paths, story IDs or process output in failures.

## Coordinator and reviewer

Root owns fixture assets, orchestration script/tests, builds/APK guards, both
selected AVDs, fresh host artifact directories, transport and structured evidence.
The public runner does not install APKs: it requires installed isolated app/test
APK hashes to match supplied build artifacts. It uses fresh runs and exact fixed
file paths, existing bounded process owner, exclusive writes and hash verification.
It compares protected package hashes before/after; no clear/uninstall/model copy.
Native/headless versus Android execution, each attempt/failure, origins and
direction are recorded separately. Reviewer owns a new report only and checks
actual artifacts/tests, not a score. Full M08/D08 remains pending owner acceptance
and remaining UI/failure/physical-device gates.
