# Focused relationship browsing

B69, 2026-11-01. Refs #13 (M09.04; supporting M09.05/M09.06),
#14 (M10.02) and #307 (preservation). Supporting implementation is in review;
full task criteria remain unchecked pending qualification and owner acceptance.
Based on open, unmerged PR #337 at
`97d07f8923337f7e215d77f2f169ffd5cd4d2c1e`.

## Behavior and authority

Relationships offers **Focus on <target ID>** for a visible outgoing entry.
The focused view retains native dimensions, sources, totals and pagination,
and explicitly describes direction. **All relationships** returns to the list.
Search explicitly searches all relationships and clears focus. Next/First,
retry and return from evidence preserve it; section changes and reopening reset
it. The target is an opaque ID, not permission to read an NPC name, profile or
private thoughts. There is no local filtering of an eight-row page.

Native generic text search case-folds valid actor IDs. The initially proposed
serialized-target substring shortcut was rejected before implementation.
The narrow additive `inspection_relationship_focus` operation compares typed
eligible targets exactly and domain-separates focused cursors, including when
All has identical rows. Ordinary query digest bytes and Query/Page versions
remain unchanged. Existing candidate/response bounds, trusted observer grants,
scope/head and completed historical boundary checks still apply. The Host
resumes durable state before querying one immutable snapshot. No gameplay,
canonical event, storage schema, JNI ABI, dependency or model choice changes.

Kotlin preserves typed `to`, rejects malformed/wrong-target whole pages and
uses the actual native player binding. Exact displayed-entry and rendered-state
identity, generation, cancellation and disposal fences remain. Evidence retains
its original tuple through the current player lens, without opening a privileged
source branch. Browsing does not commit or cancel a gameplay turn.
[Protocol](../storage/RELATIONSHIP_FOCUS_V1.md) and
[Android contract](RECORD_QUERY2_CONTRACT_2026-10-31.md).

## Independent ownership and source

Existing separate D: worktrees are reused on new branches; old branches and
frozen outputs remain. Root owns shared Rust Core/Host and four Android adapter/
controller/ViewModel paths, integration, documentation and central execution.
A owns MainActivity wiring, Dialog and two new Compose journeys; C owns the
13 new JVM cases; B owns six Core and three durable native cases. A reviews
nonowned Core/Host/Kotlin/JVM source and closed evidence. C's static interface
review finds no mismatch. UI authorship overlap is disclosed; independent
source/evidence review is not owner acceptance. Claims are released at handoff.

| Contributor | Worktree / branch | Original commit |
| --- | --- | --- |
| Root | `D:/Worktrees/locallore-player-profile-ui-v1`, `impl/m09-relationship-focus-v1` | Core `29f0a4f6`; final tested `29814477` |
| A | `D:/Worktrees/locallore-record-actions-ui-v1`, `impl/m09-relationship-focus-ui-v1` | `719b5f59` |
| C | `D:/Worktrees/locallore-record-actions-tests-v1`, `test/m09-relationship-focus-v1` | `1f930404` |
| B | `D:/Worktrees/locallore-record-actions-flow-v1`, `test/m09-relationship-focus-native-v1` | `3180e75d` |

Root formats only the two new native test files before all executed checks.
The initial formatting check reports differences; the original source, diff and
returncode remain preserved. Assertions are unchanged. No runtime test failed,
and no meaningful behavioral FIRST reproduction is claimed. Final source differs
from the tested checkpoint only in README, the Android contract, this report
and the new protocol document.

## Verification actually executed

All three phases use code `29814477f446278aa0ecbab940e639bce7c890fb`,
2,574 identical raw tracked files before/after, and one shared immutable source
ZIP. Each phase has a 900-second Windows Job owner, actual child identity/start
barrier, complete raw capture and known cleanup. Process-local TEMP/TMP/TMPDIR
are `D:/Dev/_Temp`. Existing JDK21, Rust1.93.1, locked dependencies and installed
Android tooling are reused offline. D: Cargo/Gradle caches stay in place.
No dependency/runtime/model is introduced, upgraded or chosen.

| Actual command | Result |
| --- | --- |
| `cargo +1.93.1 test --locked --offline --package locallore --features host --test m09_relationship_focus --test inspection_query --test m08_query_v2 --test m08_query_v2_message_identity_review --test m08_v2_transport_capture_review -- --nocapture` | **39 pass**, zero failures/ignored/measured/filtered; owner19,404ms. |
| `cargo +1.93.1 test --locked --offline --package locallore-android --test relationship_focus --test external_workspace --test branch_catalog -- --nocapture` | **18 pass**, zero failures/ignored/measured/filtered; owner16,421ms. |
| `python -I -S -B scripts/check.py android --offline` | Exit0, owner209,309ms; **492 unique JVM methods / 59 XML**, zero failures/errors/skips, including13 new. Lint zero errors, one existing warning and one hint. Both public APK audits pass. |
| `git diff --check` | Pass before publication. |

The full ordinary Android profile executes **81 of81 tasks**, including fresh
Rust compilation outputs for both packaged ABIs. No native exclusion, clean,
install or device task is used. This proves build/package behavior, not ARM64,
JNI, emulator or physical-phone execution. Host Cargo uses two build jobs and
DEV/TEST debug0 with isolated `native-target` output.

Six new Core cases cover exact case/prefix IDs, complete native pagination,
cursor domain separation even for identical rows, observer/private boundaries,
invalid and historical requests, and actual corrected children retaining parent
evidence while excluding future/sibling/private data. Three new durable tests
call actual Store/WorkspaceRegistry/Host bytes, including closed/malformed/private
requests, fresh persisted heads and corrected reopen. Canonical projections and
records remain unchanged around reads; raw SQLite-file equality is not claimed.

Thirteen JVM cases exercise real adapter/controller/ViewModel with synthetic
transport: exact operation/case, strict query combinations and whole-page
rejection, paging, retry, reset, evidence Back, forged/equal-copy/stale entries,
late noncooperative reads, cancellation and disposal. All relationships supports
leaving a failed focused page; that specific escape lacks a direct assertion.

Two `RelationshipFocusScreenTest` journeys compile with public concrete runtime
JUnit method definitions only in the test APK (810/480 code units). They cover
later-page target focus/evidence/search and retained/equal-copy/case-distinct/
reopened/other-story controls against a synthetic reader. **UNRUN on Android.**
Source/DEX inspection is not rendered geometry, touch, keyboard, accessibility,
real JNI, native storage or process-death evidence.

## Artifacts and preservation

| APK | Bytes | SHA-256 |
| --- | ---: | --- |
| org.locallore.app | 28,071,776 | `e89e85ebd048f0b5d25007390102b403effdcedb5e5bf1ae7dc18ef8ffadb037` |
| org.locallore.app.test | 2,383,454 | `b9457e9a8ce4ae3e6af3dd4fff1170c734cd4801e09433690f3e91bbad6f8bff` |

Common recorded signer:
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Four packaged native libraries pass16KiB ELF/ZIP checks; the test APK requests
only REORDER_TASKS. Cargo release/deps aliases have the expected two-link identity;
generated/merged bytes match release, and stripped bytes match packaged bytes.
These checks do not execute native code on Android.

Captures: `D:/Dev/Experiments/LocalLore/2026-11-01-relationship-focus-v1`.
Selected local recovery: matching `D:/Dev/Recovery/LocalLore` path.
`closed-evidence-v1.json` is113,308 bytes, SHA256
`5f0b665d163855798e80d0be56f742e9d24fa4fa4cae09504dec828fdc35df51`.
Its source ZIP is11,377,341 bytes, SHA256
`8145b7317be2a322cec8ad173de895d07a60d158b549b1478566fb3c1dc2371c`.

All59 JUnit reports plus lint XML were copied before any future rerun. Both
APKs and both release native outputs have verified local copies (53,274,126
bytes). Six synthetic fixture files (three SQLite databases and ownership
markers) have closed-owner copies (315,485 bytes); originals stay in D: TEMP.
Their copy manifest is2,840 bytes, SHA256
`5d99facb769747d43e0692cb547661c147b577b450db0286f719ea01a394b461`.
The collector verifies original/copy hashes and archived source bytes; it does
not substitute for the independent reader. All unique captures and original
source commits remain. Recovery reconstruction uses the single tested ZIP
plus the four documentation overlays, without a second full source ZIP.

Independent closed-file readback takes2.492 seconds, with no concrete finding:
`independent-closed-reader-v1.json`, 62,458 bytes, SHA256
`b42fa1ea06c82927ef60c82f489de89846217cd368c04add97f1e44265ea8384`.
It independently joins raw owner/command results, source maps/ZIP, all native
and JVM cases, report copies, APK/native chains, recorded audit output, compiled
UI definitions and synthetic fixture copies. Exactly four documentation
overlays are excepted from current-versus-tested hashes; all original archive
entries are checked. No test/build/device or semantic signature audit is rerun.

New generated outputs are sampled every two seconds and at terminal below3GiB
(final1,416,350,513 bytes). Controls stay below64MiB; selected recovery stays
below256MiB. Sampling is not a filesystem quota and excludes global cache/TEMP
peaks. Ordinary generated scratch is not a full recovery backup. No report is
overwritten by a rerun in this packet. B66's documented earlier B65 XML retention
gap remains historical and is not repaired or promoted by these fresh reports.

## Remaining gates and next task

M09.04 supporting implementation is in review. M09.06/M10.02 current Android UI
qualification remains blocked/unrun pending matching authority and guarded
admission. Frozen SDK14 PR #338, its B66 product #337 and APK pair, and pending
SDK13 source/proposal stay untouched. Neither pending proposal includes this
new pair or these two new methods. The resurfaced October31 player-presentation
approval names the already executed/closed ten-method run; it does not grant
another guest or newer suite.

No emulator, ADB, phone discovery, ledger write, model transfer/inference,
system setting change, unrelated-process stop, private upload, merge or release
occurs here. Physical phone, real inference, ARM64 execution, broad accessibility,
visual comfort, causal OS-death and full milestone acceptance remain separate.
The next host-runnable task is to reconcile the archive dialog's corrected-
timeline availability copy against the actual V2 resume route, with a narrow
regression if the copy is stale. Current device qualification remains a separate
exact-approval task; do not build a new harness merely to replace a pending one.
