# Cached native Player state view - 2026-11-01

Refs #13 (M09.04; supporting M09.03/M09.05/M09.06), #307, and #14 (M10.02).
Implementation and host/build checks are in review. Full criteria remain unchecked.

## What changes

Android previously validated all nine native Actor fields in `self_state` and
then discarded them from its chat presentation DTO. It now retains exact name,
location, alive, energy, abilities/ranks, signed attributes, injuries, affiliations
and goals, plus the separately returned native observer. Nullable snapshot/state
fields distinguish unavailable data from known empty collections. All five
nested collection lists are detached and unmodifiable at decode and publication.

A cached read-only Player state dialog shows accepted revision and full values,
with a scrolling body and a separate Close control. Native Narrative rules do
not track energy/ranks/attributes, so those sections are explicitly inapplicable.
No maximum, cost, eligibility, skill name or actor identity is inferred. Native
location is not the database path. No native query or gameplay callback is added.

The existing Query2/Story Record Progression view already exposes canonical
fields with provenance; it and source-event navigation remain. This is an
accepted-snapshot overview, not new progression authority or a context compiler.
Inventory/profile dialogs are exclusive. Current scope/eligibility guards fence
retained callbacks and close the view on recovery, workflows or unavailable data.
Cached data remains readable during generation/provider unavailability, while
same-scope accepted refreshes update the view. Drafts and messages are preserved.
The outer chat LazyColumn item/key/count contract remains unchanged.

The [native presentation contract](../native/PLAYER_PRESENTATION_V2.md#android-cached-self-profile)
and existing Gateway attachment/session/scope/head/native-observer fences stay
in force. Self state has no embedded actor ID: Kotlin cannot prove ownership by
matching actor contents. Native selection and genuine foreign-canary checks own
that boundary. Rust authority, schema, JNI ABI and dependencies are unchanged.

## Executed checks and source

Base is frozen PR #330 `ba548cbf6982c58d8a221aea2ed3606232d013d9`.
Executed integrated code is `b42a34f15d323ba2234aa3e4f125014af2a6163b`:
Core retention `d1451d51`, UI from `00c5c03c` integrated as `ae9e9ad0`,
independent JVM tests from `06d02fb6` integrated as `3b4f3c71`, and native fixtures
from `522409ff` integrated as `b42a34f1`. Later source changes are documentation only.
Four writers used separate D: worktrees and explicit paths; Root owns integration.

Each native/quality row is a separate bounded execution. No combined full Rust
suite is claimed. The 15 new JVM methods are included in the full 454-case run.

| Check actually executed | Result | Recorded owner duration |
| --- | --- | --- |
| Explicit native golden producer | 1 pass, 4 filtered; four complete genuine replies | 10.968s |
| Default native profile fixture tests | 4 pass, 1 intentionally ignored producer, 0 failures | 0.312s |
| `cargo +1.93.1 fmt -p locallore -- --check` | Pass | 1.231s |
| Targeted host Clippy with `--locked --offline -- -D warnings` | Pass, no lint warnings/errors | 6.624s |
| `python -I -S -B scripts/check.py android --offline` | Pass; 81/81 tasks executed, native builds included | 129.168s |
| JVM tests in that public gate | 454 unique methods / 55 XML, 0 failures/errors/skips | Same gate |
| Lint in that gate | 0 errors, 1 existing GradleDependency warning, 1 AutoboxingStateCreation hint | Same gate |
| Public APK audits | Product permissions/native alignment and paired identity/signing pass | Same gate |

The public command itself records 129.029s; the outer Windows Job records
129.168s with known cleanup/capture and child exit0. Raw output is 10,797 stdout
bytes and 354 stderr bytes. No clean, native exclusion, install, connected test,
model download or device command was used. Before the documentation-only handoff, all 2,560 tracked raw inputs matched
before/after/current source and the tested-source ZIP.

Commands ran from physical D: checkouts with TEMP/TMP/TMPDIR set to D:/Dev/_Temp.
Existing D: Cargo/Gradle caches, installed Rust1.93.1, JDK21.0.4, SDK platform36,
Build Tools35.0.0 and NDK29.0.14206865 were retained; no dependency changed.

## Meaningful native and JVM coverage

Four original full Host success envelopes cover both domains and both rule
profiles. Opaque player `a-71be92c40d6f8a53c201-0` is selected by the real engine.
Fantasy learn/use/consume/move produce rank, energy, injury and location changes;
narrative keeps legitimate zero energy/empty combat fields with Unicode state.
Domain2 uses actual corrected accepted history, not a version retag. Full Actor,
response and canonical accepted-state/history conservation assertions exclude
private NPC/belief/item/goal/attribute, truth and author-reason canaries. The
read-only Persistence test port records zero writes. Domain1 export conservation
excludes only its wall-clock manifest timestamp; legacy Domain2 export Version
refusal remains. These are real Engine/Host fixtures, not SQLite/JNI/device proof.

The six decoder tests consume those exact native assets and cover full field
preservation, malformed/private extra fields, numeric/UTF-8/uniqueness bounds,
JSON nonmutation and immutable detached collections. Six publication/lifecycle
tests cover mutable caller collections, null/known-empty replacement, coherent
refresh/recovery, same-head story/branch replacement and noncooperative cancelled/
disposed completions. Three real-Gateway tests use actual presentation replies
with explicitly synthetic session/catalog transport, exercising existing observer,
head, attachment and close fences without new native operations. Structural
alive=false/65535 boundaries are not claimed as genuine progression outcomes.

## Artifacts and compilation

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK | 28,045,456 | `4129009f12f9bc21528c08afcd4d81ff56e8a96d8bc9cbb324b8130778f15a86` |
| Test APK | 2,336,350 | `4935ef0df5b10a8dd718556c2d92a9b46d2b29c7ea4ece7eb287c3908117cba2` |

Recorded signer remains
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Both JNI ABI builds complete. Four packaged libraries pass 16KiB ZIP/ELF checks.
The two named Cargo release/deps aliases have exactly two links to the same
object; generated/merged hashes equal release and stripped bytes equal APK bytes.
Other stage/APK copies are single-link. The four genuine assets are byte-identical
in generated/source/test-APK copies and absent from product.

The test APK contains all three concrete public nonnative zero-argument void
JUnit methods of `PlayerSelfProfileScreenTest`, with runtime annotations and
bounded nonempty code bodies (859 / 1227 / 881 code units). Their class family
is absent from the product APK. The methods cover field/empty/unavailable/demo/
narrative presentation, retained scope/workflow/cross-inspector callbacks with
refresh/draft conservation, and doubled-font Unicode/collection/Close reachability.
**They are compiled, not executed.** The test's 360x620 content Box does not
constrain Dialog's separate window; no small-window/IME/landscape geometry proof
is inferred from it.

## Review, retained failures and limits

Independent source reviews found no concrete unresolved blocker. Reviewers
focused on non-owned Core/UI/native paths; authorship overlap on UI/native/JVM
work is disclosed and is not owner acceptance. A separate closed build reader
joins source/control/child/XML/public audit/APK/DEX/asset evidence. The JVM test
author's XML readback is not independent oracle review.

Native cohorts passed on their first execution. A later metadata console print
hit Windows cp1252 after binary asset copies and UTF-8 bindings were complete;
that failure remains separate, with no native retry. An artifact reader first
refused a CRLF task-heading regex; splitlines/exact fullmatch corrected only the
reader. Root's first closed collector incorrectly assumed one-line audit JSON;
two complete pretty-printed frames from unchanged stdout are now decoded, and
existing verified APK copies were retained. No build/test, guard or assertion
was weakened or rerun to hide those reader/setup failures.

Exact helpers, binary outputs, source/tool maps, reports and APK copies remain
under `D:/Dev/Experiments/LocalLore/2026-11-01-player-self-profile-v1`. Declared
budgets: source trees256MiB total, generated project output3GiB, controls64MiB,
fixtures128MiB and selected recovery256MiB. Native generation/quality use separate
owned targets; only those two exact generated directories are excluded from the
control allowance. Closed measured generated output is 921,758,320 bytes;
controls before the final meter record are 42,883,556 bytes, both within allowance. Original generated trees remain; no full global-cache/TEMP
high-water or full generated-tree byte-backup claim is made. Final recovery seals
and independent readback are posted on tickets after execution.

All current-source Android instrumentation, including the three new journeys,
remains UNRUN. Physical/ARM64 execution, SQLite/JNI behavior of this view,
TalkBack, touch/real IME/orientation/visual quality, real-model stories, causal
process death, full journeys and release acceptance remain separate gates.
Pending SDK12 consent covers the older frozen #330/#331 pair, not these APKs;
no grant was reused. No emulator/ADB/phone discovery or lifecycle, model transfer,
ledger mutation, deletion, settings change, unrelated-emulator stop or merge.
