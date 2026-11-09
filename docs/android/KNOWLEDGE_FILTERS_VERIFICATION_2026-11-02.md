# Knowledge record filter verification

B86, 2026-11-02. Refs #13 (M09.04), supporting M09.06 / #14 (M10.02).
Implemented and locally verified for review; full tasks remain unchecked pending
their broader acceptance criteria and owner acceptance. No merge.

This packet stacks on open/unmerged PR #356 at
`5300267c537512d6e2055c60d93532f5a6ca9ecc`. The existing PR #354 recovery
operator, proposal, frozen product/APKs and pending execution authority remain
separate. These new bytes and tests are not added to its proposed run.

## Behavior and authority

[The contract](KNOWLEDGE_FILTERS_V1.md) defines five local choices: All, Known as
observed, Statements, Beliefs and Discoveries. Only Knowledge/Query2 admits an
active choice. The existing native literal search selects the exact serialized
origin before Rust counts and pages eligible player records. Kotlin forwards
the request and validates replies; it does not filter rows, recompute totals,
grant another observer or establish world truth. Both the wire decoder and
typed controller independently reject wrong-origin replies.

Choosing a facet clears search and starts at page one. Search returns to All;
section selection/reselection resets the facet. First, Next, Retry and evidence
Back preserve the chosen view. MainActivity captures the exact rendered state.
The dialog retains its existing referential keys and now checks a private
per-mount lifetime/current key on every callback route. Removed dialog callbacks
cannot regain authority when the same record object is remounted.

Five chips appear only in Knowledge, in rows of at most two, with minimum 48dp
height. Their explanation distinguishes an observation learned then from
current world truth. The original origin, confidence and evidence projections
remain; no CanonicalTruth facet, native schema/production change, dependency,
model, gameplay rule or storage owner is introduced.

## Actual checks

All commands ran from physical
`D:\Worktrees\LocalLore-record-query2-fixtures-v1`, with process-local
TEMP/TMP/TMPDIR `D:\Dev\_Temp`, offline D: Cargo/Gradle caches, installed JDK
21.0.4 / CPython 3.14.7 and pinned Rust 1.93.1. Each host job has a 900-second
Windows job owner, binary output capture, source archive and before/after source
map. Generated outputs are bounded at 3 GiB, controls at 64 MiB and selected
recovery at 192 MiB. No Android/ADB process is started by these checks.

| Phase | Source | Actual result | Owned elapsed |
|---|---|---|---|
| Native producer | `dbe2433f91f22ee007bdc41e7b9f6aab57526a04` | All fixture assertions pass; 18 original Query2 pages | 12.798s |
| Initial JVM setup | `14cbf97d208c7f549d662b9cd0aae04385bf4ffb` | Compilation refuses two unavailable `JSONObject.similar` calls; **zero new tests** | 23.839s |
| Corrected targeted JVM | `d02d5c9af79179a82958970a18bd3d561a138bf1` | 13 unique methods, zero failures/errors/skips | 25.813s |
| Full offline Android gate | Same `d02d5c9a` | 579 unique JVM methods / 69 XML suites, zero failures/errors/skips; both APK builds/audits pass | 44.664s |

The setup failure and original source/captures remain. Android's compile-time
JSON surface omits `similar`; a test-only recursive comparison now checks exact
object keysets, array order and scalar representations. No production change,
dependency or expected-value relaxation was needed. This new feature does not
claim a pre-existing product regression or a RED-to-GREEN experiment. The 13
targeted methods also occur within 579; they are not extra distinct tests.

Reproduce the native check:

```powershell
cargo +1.93.1 run --locked --offline --jobs=2 -p locallore --example android_knowledge_filter_fixture
```

The targeted Gradle task is `:app:testDebugUnitTest --tests
org.locallore.app.StoryRecordKnowledgeFilterTest` with offline/max-workers-two
settings. The full gate is:

```powershell
python -I -S -B scripts/check.py android --offline
```

Lint reports zero errors, one existing warning and one hint. The Android Rust
task is **UP-TO-DATE**, using the previously preserved B84 native libraries;
this is neither a fresh Android native build nor ARM64 execution. The new host
Core fixture really compiles and executes independently.

## Native corpus and cross-boundary assertions

The original synthetic Lantern Quay seed is derived explicitly: remove the
player's initial relic knowledge, create nine witnessed speech/belief pairs,
move and discover the relic, then return. A real author correction creates a
Domain2 child with changed hidden world truth; a later parent-only statement
is then committed. Both heads are 22, so equal numeric revisions cannot stand
in for lineage. The producer checks unchanged canonical bytes, mechanical
projection, canonical records and accepted-history basis across all reads.

| Scope/domain | All | Observed | Statements | Beliefs | Discoveries |
|---|---:|---:|---:|---:|---:|
| Parent / Domain1 | 22 | 2 | 10 | 9 | 1 |
| Corrected child / Domain2 | 21 | 2 | 9 | 9 | 1 |

Beliefs use actual native pages of 8 + 1. All uses 8/8/6 and 8/8/5. The fixture
compares each exact filtered typed-row partition with eligible unfiltered rows,
including original sources, subjects and confidence. Escaped origin-like prose
cannot spoof another facet. Private NPC belief, unseen corrected proposition,
author reason and future parent canaries stay out of player pages. The player's
original observation and discovery retain their old proposition and parent
event source after the hidden correction.

The producer writes one compact JSON object plus LF, **54,699 bytes**, SHA256
`b224b559410ad3c34a83f71a1f4a097001d94e366d1ad12a59e9a36e80ebe5ab`.
It is copied byte-identically to
`apps/android/app/src/test/resources/story-record-knowledge-filters-v1.json`,
with an exact `-text` attribute. No native page is reconstructed for the normal
positive cases. JVM tests consume every original page, match complete native
query JSON, and preserve totals/cursors/row text/confidence/source tuples.

The 13 JVM methods also cover otherwise-valid wrong-origin ALL positives and
active-facet negatives, legacy v1 canonical-truth compatibility versus v2
refusal, incompatible requests, paging/retry/reset, typed-reader rejection,
noncooperative late reads, loading/close/disposal, evidence Back and exact
rendered VM identity including equal-valued reopen and a fresh positive action.
Synthetic read ports establish adapter ownership, not native eligibility.

Final raw test source pins (also unchanged across targeted/full runs):

- JVM: 29,537 bytes,
  `165a5d23ee4a8468c05097f44570e4449a0348a1323389301cc9c971e1403d08`.
- Compose: 14,880 bytes,
  `7b16a0521ebf7c43f461bd8694189d5be042859b98598ac63a50bba2e1cf57b3`.

Four new Compose methods compile/package: five literal facet labels and
selection/48dp controls only in Knowledge; retained real actions after changed
or equal-distinct states; same-state removal/remount retiring facet and Close;
and doubled-font scrolling with unchanged origin/evidence text and reachable
Close. Their callbacks deliberately have no outside VM guard. Geometry uses
the actual separate Dialog surface. **Zero of these four executed on Android**;
compilation proves neither geometry nor accessibility/interaction acceptance.

## Artifacts, preservation and limits

Both public APK audits pass with the existing signer
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`:

- Product: 28,398,596 bytes,
  `cfcc4210dcf14e47d77c6308912f09a080ea9ba357c9f1d87d7b2fe294231299`.
- Test: 2,645,072 bytes,
  `3241aaff3c42fc6c155f04da40cae88aa54e39cd68c10f7cb5178a0b77a9c5db`.

Private OUT and REC roots use
`D:\Dev\Experiments\LocalLore\2026-11-02-knowledge-record-filters-v1` and
the matching `D:\Dev\Recovery\LocalLore` child. Original captures, all four
closed phase records, three full source archives, selected reports/artifacts,
independent source/closed reviews and their verified copies remain there.
Canonical copy receipts and final claim release are linked from #13/#14/#3.
The initial compile refusal never borrows inherited XML as a passing result.
Before reusing outputs, all 129 B85 immutable copies and 73 current artifact
bindings were reverified. Nothing from the failed recovery or prior packets
is deleted or relabeled.

No emulator, phone, JNI execution, model import/inference, IME, TalkBack,
process-death or physical performance result follows. No ledger transition,
settings change, unrelated emulator stop, private upload or merge occurred.
The charged reservation and PR #354 remain frozen behind that run's pending
applicable approval; earlier spent approvals are not extended to this packet.

Next runnable preparation: bind these four Knowledge journeys to a separately
reviewed bounded Android run proposal. Actual target execution needs applicable
approval and the unchanged storage/ownership gates; PR #354 retains its own
four library-action selectors. M09.04, M09.06 and M10.02 full gates stay open.
