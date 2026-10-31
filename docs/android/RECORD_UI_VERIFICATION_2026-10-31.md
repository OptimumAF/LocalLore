# Native player-record UI qualification harness

2026-10-31, B38. Refs #14 (M10.02), #13 (M09.06; supporting M09.04).
Supporting implementation is locally verified/in review; full tasks and owner
acceptance remain open. Base is unmerged PR304, exact
`12857ac7f563c5a9c61092ae8dcabacc6cd4d4cd`. No newer-main or separate
authoring/narrator-stack qualification, merge or release.

## What changed

A distinct fixed SDK7/model-free profile selects ten inspector methods over the
existing shared owner/wire/proof/storage mechanisms. Source code chooses its
contract/client/verifier, not admission data. New build/controller protocol IDs
prevent retagging old evidence. All six original archive-UI adapters remain
byte-identical; their 345/41 build requirement and old ten-method roster persist.
See [operational guide](../runtime/android/RECORD_UI_HARNESS.md) and
[frozen interfaces/roster](RECORD_UI_CONTRACT_2026-10-31.md).

Three independent writer worktrees supplied 21 host adversaries, a genuine Rust
archive producer, and two Compose cases plus an existing-test migration. Root
owns shared contracts, fixed adapters, generated assets and integration. Reviews
were independent source/file readers, not device runs or human acceptance.

The old unrun screen test still expected a flat `Event #1` source label and
CanonicalTruth under the new default. It now asserts the exact original scoped
tuple/presentation and KnownAsObserved, retaining its existing method/assertions.
New cases browse before/corrected/rediscovered heads, all five paginated views,
non-navigable private correction notices, exact ancestor evidence, stale rendered
callbacks across branch/story/disposal and ordinary owner reopen. Accepted views
and turn counts must remain unchanged during inspection; current valid callbacks
are positive controls. Two new methods are compiled/packaged but **UNRUN**.

## Genuine corrected fixture

Normal Android workspaces deliberately have no Story Lab author-correction API.
The new Workspace example uses existing Host authority in an isolated synthetic
SQLite Store, then exports production Archive3. No new app privilege, fake
inspection rows, changed domain flag or dependency was added. Workspace owns
the example because putting Storage/Workspace dependencies in Core would cycle.

Actual typed Discover/Dialogue/Promise/Wait, native author correction, real fork
and rediscovery yield original/corrected/rediscovered heads4/5/6, story time1,
with genuine opaque player `a-dbe9fdf212277ede0240-0`. Before/unseen correction
retain amber knowledge; actual rediscovery yields violet. Production export,
fresh-Store import and re-export must match exact bytes. Each role/import also
requires actual player location, all three Nia outgoing relationship dimensions
and the exact open survey-notes promise with original main/event3 evidence.

Archive **14,497B**, SHA256
`904c725e6bae3e87b9bb42d2f91b956b6044af747fc27ea2695dd3f5c078e94c`;
metadata **859B**, SHA256
`336a0548e0f58b7443e70bf3386ff714623231455394969b21314db6576d4e81`.
The committed test-only assets are exact binary stdout/metadata stderr, verified
against native metadata and Git blob. Exact-path `-text` prevents Git newline
conversion. Refined output is byte-identical to the first successful run.
Source/roundtrip SQLite files in both fresh D: scratch directories are retained.

The canonical synthetic archive necessarily contains its private seed/reason
canaries; real player Query2/UI assertions exclude their names/sheets/beliefs/
facts/reasons. Existing relationship eligibility includes the player's outgoing
seeded edges to opaque targets. This packet preserves that policy and does not
claim unknown-character existence or opaque-ID hiding.

Independent review found that initial tests paginated all views but required
meaningful content only in Knowledge/History. Native and Compose assertions were
strengthened for the other three without changing seed/known_by or eligibility.
The refined native execution passes. Original review/setup failures remain.

## Exact checks and attribution

Final executable **`535acb855177ca1df87743a7afabd7e5d18ad273`**, 2,355 raw inputs,
is frozen at `D:/Worktrees/LocalLore-record-ui-v1`, branch
`impl/m10-record-ui-v1`. Reporting uses the reused, clean host-writer worktree
on `impl/m10-record-ui-packet-v1`; subsequent changes there are documentation
only. Do not substitute the reporting checkout into the build proof graph.

Physical-D commands use installed Java21/SDK, Rust1.93.1 and existing D: caches;
TEMP/TMP/TMPDIR stay D:. No runtime/model/library/SDK dependency or lock change.

```text
python -I -S -B <private-fixed-cohort-driver>
cargo +1.93.1 build --locked --offline -p locallore-workspace --example record_ui_archive_fixture
<built-record_ui_archive_fixture.exe> <fresh-ordinary-D-scratch-directory>
cargo +1.93.1 clippy --locked --offline -p locallore-workspace --example record_ui_archive_fixture -- -D warnings
cargo +1.93.1 fmt --all -- --check
python -I -S -B scripts/check.py android --archive-verification --offline
python -I -S -B benchmarks/record_ui_build.py --public-run <closed-public-run> --output <new-manifest>
```

The fixed Python driver loads archive-UI contract/client/owner/build/controller,
owned-target/restart contracts, SDK4/5 clients, owned-target/receipt storage and
storage integration, and new record-UI contract/client/build/controller modules.
All 248 named cases pass, including21 new (5/4/7/5), zero failures/errors/skips,
at `b52b835b`. Those Python source/test bytes remain unchanged at final executable;
later edits are native/Android fixtures, assets, attributes and contract wording.
This is not a whole-Python-suite rerun or actual kernel/SDK/target qualification.

| Closed cohort | Source prefix | Result | Owner elapsed ms |
| --- | --- | --- | ---: |
| python-v1 | 828de689 | isolated discovery import setup failure | 670 |
| python-v2 | 828de689 | nonimportable start-directory setup failure | 519 |
| python-v3 | b52b835b | 248 actual passes, including21 new | 174,663 |
| native-build-v1 | 849707f5 | exit0, host example compiled | 14,714 |
| native-fixture-v1 | 849707f5 | exit0, genuine archive/round trip | 872 |
| clippy-v1 | 849707f5 | exit101, newline-inclusive bound style | 5,822 |
| fmt-v1 | a9e13712 | exit1, new example formatting | 2,336 |
| native-build-v2 | d98ef788 | exit0, stronger assertions compiled | 1,125 |
| native-fixture-v2 | d98ef788 | exit0, stronger checks, identical bytes | 873 |
| clippy-v2 | 535acb85 | exit0, warnings denied | 875 |
| fmt-v2 | 535acb85 | exit0 | 2,287 |
| android-v1 | 535acb85 | exit0, public pipeline below | 227,429 |
| build-admission-v1 | 535acb85 | exit0, actual current build manifest | 3,600 |

Durations include finite host supervision/cleanup, not just test time. Every
closed cohort joins actual child, source/helper, global/per-job admission and
capture/cleanup; no unexpected meter error or unknown worker outcome. First
setup failures are not product RED. Initial Clippy changed only the equivalent
`len()+1 <= limit` expression; format touched only the new example. Early reader
filename/checkpoint/shell-preparation failures also remain separately retained.

The unmodified public gate has a separate inner900-second owner, actual222,905ms,
and fresh source/tool pins before/after. Both Rust JNI ABIs actually compile
(release logs1m12s/1m08s); Kotlin/instrumentation and both APKs build. All380 JVM
cases/43 fresh XML pass (includes the existing FIRST15; not additive to it),
zero failures/errors/skips. Lint0 errors/one existing Warning/one Hint. Public
product and instrumentation-pair audits pass, all four packaged libraries have
16,384-byte ELF LOAD alignment; test permission only REORDER_TASKS.

| Isolated APK | Bytes | SHA256 |
| --- | ---: | --- |
| `org.locallore.app.archiveverify` | 27,756,156 | `60656e21a4dbdfcd506c473290067ea61b835c35fc01e7abd761738dd28cde78` |
| `org.locallore.app.archiveverify.test` | 2,261,656 | `929b302275b82dfd56014fbad20e813808c89e03f4834c50dbe793103aef5784` |

Certificate SHA256 is
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Forty-six sealed files retain both APKs,43 JVM XMLs and lint XML.
The genuine current manifest is15,780B, SHA256
`5cceffeea484ca15abaa156f83b23dd9cdd6e6cf66cd93b1456dceac28750d28`.
It validates all ten actual annotated test DEX/source selectors,380/43, exact
FIRST15/Transcript8, source/head/tool/raw/task/APK roles. A separate real
`verify_current` replay with minimal artifact references passes in3,083ms;
no target admission, caller, service or device was created by that replay.

## Retention and remaining gates

Private originals are under
`D:/Dev/Experiments/LocalLore/2026-10-31-record-ui-v1`; selected create-only
recovery is prepared at the matching `D:/Dev/Recovery/LocalLore` root. Ticket
handoff records actual recovery seals/readback. Four source worktrees, all failed
captures, both SQLite scratch pairs and targets remain. Selected recovery is
capped256MiB raw, excludes build targets/caches/models/keys/guest images, and
includes the actual native SQLite pairs. Other owned temporary test outputs are
retained in place, not claimed as completely backed up.

Host forecast1.5–4GiB, cap8GiB/stop7GiB, owned TEMP512MiB/stop384MiB remain.
The final build admission measured1,033,006,912 named-root bytes before sealing,
with41,092,487 owned temporary bytes. Prior packets remain separately retained;
shared caches/Git metadata/peak are not fully attributed. No cleanup occurred.

No emulator, ADB, app, phone, model or ledger operation ran. The designated
starter-native guard was inspected read-only and remains dirty/different from
this committed guard; both are preserved. The ledger inventory has two unretired
closed roots, so fresh guest admission and fresh applicable boot authority remain
required. No old one-run grant is reused; no other emulator, shared service or
system setting changed. Compiled tests, host fixtures and older-APK UI results
do not qualify this SDK7/current-source Android run.

Current UI/touch/accessibility/JNI execution, process recreation/causal OS-death,
SDK resource drain, privacy traffic, real model/story quality and ARM64/physical
performance remain unverified. M01.01/M01.02/M10.05 device gates stay blocked.
Next runnable supporting task is exact preservation/retirement-capacity proposal
under the current shared guard, then a separately authorized bounded current
inspector run. Full M09/M10 criteria and owner acceptance remain unchanged.
