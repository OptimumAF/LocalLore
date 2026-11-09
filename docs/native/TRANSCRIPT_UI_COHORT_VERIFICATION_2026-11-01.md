# Transcript UI cohort host verification — 2026-11-01

Refs #13 (M09.03/M09.06), #14 (M10.02). Implementation is in review; full tasks
remain unchecked. See [the fixed protocol](TRANSCRIPT_UI_COHORT_V1.md).

## Scope and provenance

This packet adds a source-fixed SDK10 profile, data-only frozen-build guard,
six-method controller, closed replay and host fixtures. Root coordinates
integration; separate profile and build writers used separate D: checkouts and
branches. An independent source reviewer identified concrete controller gaps.
Old branches, tracked-source ZIPs and 59 ignored files in the reused checkouts
were preserved. The dirty designated integration tree was not edited.

The base is PR #315 (`bb461ea227e77e4925c805e09bc2a0c74b0a1c6b`). Product dependency
PR #317 (`78f254bb50ca0478541f0107ccfbcb16afd40d72`) remains separately frozen.
No product code, APK, frozen proposal or earlier profile is modified here.

All commands ran from physical D: checkouts with process-local `TEMP`, `TMP`
and `TMPDIR` set to `D:/Dev/_Temp`, using installed Python 3.14 with `-I -S -B`.
No new dependency, Android/native build, model operation, phone discovery,
emulator action, shared-ledger write or system-setting change occurred.

## Actual checks

| Check | Actual result |
| --- | --- |
| Integrated new modules | 52 passed, zero failures/errors/skips, 93.279 seconds |
| Targeted older profile/storage regression | 148 passed, zero failures/errors/skips, 251.377 seconds |
| Profile/client/claims subset | 11 tests in the integrated 52 |
| Build graph/APK/source guard subset | 22 tests in the integrated 52 |
| Controller/raw replay subset | 15 tests in the integrated 52 |
| Retirement protocol subset | 4 tests in the integrated 52 |
| Controller and retirement after fixes | 19 passed, zero failures/errors/skips, 90.729 seconds |
| Unmocked `create_manifest()` against preserved PR #317 | Passed, 16.13 seconds |
| Fresh `verify_frozen_product(artifacts)` | Passed, 9.107 seconds; six fixed read-only Git queries, zero socket operations |

The integrated host driver imports `scripts.tests.test_transcript_ui_profile`,
`test_transcript_ui_build`, `test_transcript_ui_controller` and
`test_transcript_ui_retirement` through `unittest`, recording every case identity
and source hashes before/after. The 52-test run recorded stable source bytes,
zero child processes and zero real socket operations. Unit fixtures mock the
native process/socket observations. Controller fixture files are explicitly
synthetic, not APKs; their build boundary is mocked. This is separate from the
unmocked check of the real preserved APK/build graph.

The legacy driver runs 19 archive/record UI, player-presentation, SDK9 and
retirement modules. Its successful second run records all 148 unique identities,
stable watched sources and zero real socket operations. Only exact local Git
commands within its synthetic SDK9 build-fixture roots are permitted child
processes. No actual emulator/ADB command or production registry is involved.

The build guard recounts **existing B48** evidence: 420 passing JVM cases across
48 XML reports, successful Android-test compilation/lint and APK audits. These
checks were not rebuilt or rerun in this packet. The sealed local manifest is
342441 bytes, SHA-256
`d40a89b111e7ba6c23ea0678bb9f56f40bd14c482408739cd9a1868a00fec260`.

| Preserved APK | Bytes | SHA-256 |
| --- | ---: | --- |
| Product | 28012664 | `16b3b7761d64991c5906cb67c24ad8e562006acc1a349201a3b883fd7145d6d9` |
| Tests | 2275810 | `1b598a0f05ac1f24a85fef035d7c16a9ed5fabfb4cee988c7b5a9a028b68ee8e` |

## Failures retained and fixes verified

Four assertions failed against the initial controller, before the fixes:

1. A response for the app alone could satisfy an initial absence query for the
   test package. The new filter check refuses it before APK staging.
2. A consistently rebound method record with a 90001-ms deadline could pass
   closed replay. Replay now enforces the fixed per-command limit.
3. A wrong method label with consistently rebound proof contexts could replay.
   Replay now requires the producer's exact role/selector label.
4. A rebound staging capture containing 131073 stderr bytes could replay even
   though the producer limit is 131072. Replay now enforces both individual and
   combined byte limits.

The initial complete synthetic positive flow passed. Its normal package-list
fixture was subsequently corrected to mirror Android's real substring filter;
the explicit invalid-response injection and all four failing assertions were
retained. Original failing controller/test/fixture bytes and logs remain locally
preserved. The fixes did not increase time/byte limits or change old profiles.

The private Windows process observer also had setup failures. The first two
artifact-observer attempts expected argument lists (one also omitted Git's
`--no-optional-locks`); Windows CPython reports an encoded command-line string.
The corrected observer matches only exact read-only command strings. The first
legacy regression driver similarly rejected fixture-local Git setup before
14 existing tests could exercise their assertions. Its replacement permits
only the exact synthetic fixture's local Git setup/read commands with
per-command identity/hooks settings. Production code and test assertions were
unchanged by these observer corrections. Original logs remain preserved.

## Retention and remaining gates

Local control/evidence is under
`D:/Dev/Experiments/LocalLore/2026-11-01-transcript-ui-cohort-v1` (16 MiB limit).
Synthetic fixtures use separately owned D: temporary roots (128 MiB limit).
Selected source/control recovery has a separate 32 MiB limit. Existing B48
APK/source recovery stays in place; no images, weights, credentials or private
stories are published with this change.

The pre-publication inventory verifies 2347589 control bytes across 48 files,
81331507 retained synthetic bytes across 37 controller-fixture roots, all 59
original ignored-file hashes, and current source hashes for both successful
integrated runs. Later small sealing receipts are counted separately; the
original failing fixtures and logs remain in place.

All six Android executions remain **unrun**. No real guest, admission, plan,
reservation or retirement has been created for SDK10. An older exact approval
question remains pending and does not cover this new cohort. Next: prepare a
concrete bounded SDK10 run proposal after current storage/ownership checks, then
obtain applicable fresh approval before any guest preparation/boot. No merge
or full M09/M10 acceptance is claimed.
