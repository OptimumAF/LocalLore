# Player-visible promises in the Android story record

Date: 2026-10-30. Packet B33. Refs #13 (M09.04), supporting M09.03 and
#14 (M10.02). This read-only slice is implemented and locally verified, in review.
Full task criteria and owner acceptance remain open. It is stacked on unmerged
PR #294 at `ea9f153aba36afbac221aff72ac8dc406c0cb4c0`.

## Behavior and authority

The story record now offers **Promises** alongside its four existing sections.
It displays the engine's terms, parties, status, deadline in story time, optional
return item and provenance. Open/Overdue/Fulfilled are presentations of Rust's
returned status. Kotlin does not calculate overdue state, infer completion,
advance time, create obligations, issue reminders or change canon.

The existing Query1 contract rejects domain-2 original stories. The new section
therefore uses the already implemented Query2, which supports both domains.
This is not a new Rust schema, command, dependency or production runtime choice.
The four existing sections keep their Query1 behavior, including their existing
domain-2 limitation. Further migration of those sections remains required.

The new view requests only the current frozen story/branch/head and player
observer. Query2 source events retain original story, branch and sequence as
typed references. They are never flattened into current-branch event numbers.
Seed and withheld sources remain non-navigable. The view labels promise status
as a derived comparison rather than a new world fact.

Opening evidence requires a reference currently present in the accepted page
and the captured rendered context. The controller searches the exact serialized
EventRow prefix through Query2 HISTORY in the **same current player lens**.
It does not open the source branch or grant an observer role. The resulting
single event must match the original scope and sequence, frozen time/head,
player witness, version and provenance. Unknown, ambiguous, stale or unavailable
results fail safely. Source buttons and event detail show the original scope.

Version-2 pages/cursors are bound explicitly. Typed source shapes, numeric
types, source counts, current-story identifiers and response byte limits are
checked. Existing generation fencing, read cancellation, immutable publication,
dismissal, disposal and ViewModel context checks remain active. The unchanged
DurableGateway binds the native read to its captured session/scope/revision.
Rust still owns eligibility, accepted events and every gameplay transition.

## Executed sources and checks

All final execution used clean
`1a012fc28fb2ce5ced83218f2483fe8e5414e70e`, with 2,332 tracked raw inputs,
at `D:\Worktrees\LocalLore-promise-records-v1`. Later reporting adds only this
document. Independent test authorship used the separate
`D:\Worktrees\LocalLore-promise-records-tests-v1`; the independent reviewer
used a separate existing read-only checkout. No shared file had two writers.

| Actual command/procedure | Result |
| --- | --- |
| Original 14-case baseline on `a33c2d79`, focused `:app:testDebugUnitTest --tests org.locallore.app.PromiseStoryRecordTest`, archive profile/offline | Test compilation failed at three unavailable JSONObject.keySet calls. No JUnit test ran. Owner 225,156 ms, child 1; capture/cleanup complete. |
| Corrected original baseline on `b79397aa`, same focused command | 14 tests, 14 assertion failures for the missing Promises section; zero errors/skips. Owner 33,594 ms, child 1; known capture/cleanup. |
| `python -I -S -B scripts/check.py android --archive-verification --offline` on `1a012fc2` | Exit 0; **365 unique JVM cases / 42 XML suites**, including all 20 new cases; zero failures/errors/skips. Both APKs build; lint zero Error/Fatal, one existing warning and one hint; both public APK audits pass. |
| `cargo +1.93.1 test --locked --offline --package locallore --features host --test inspection_query --test m08_query_v2 --test m08_query_v2_message_identity_review -- --nocapture` | **32 named cases pass**, in groups 16/10/6, zero failures/ignored/filtered. Existing native semantics, privacy, inherited scope, cursor and message-identity tests; no new Rust production code. |
| `git diff --check` | Pass. |

The Android owner finishes in 113,025 ms, child 0, complete cleanup/capture,
stdout 7,539 bytes and stderr zero. The native-host owner finishes in 23,851 ms,
child 0, complete cleanup/capture, stdout 3,001 and stderr 1,487 bytes. Each
phase joins the actual child identity to its request/start records, pins its
helper, and verifies all raw sources unchanged before/after.

The first baseline actually compiled the unchanged JNI libraries for x86_64
and ARM64. The later successful Android gate reports
`buildRustAndroid UP-TO-DATE`; it is not a fresh native compilation claim.
Both libraries pass the package audits. No ARM64 execution is inferred.
Installed JDK 21, existing Android SDK/build tooling and Rust 1.93.1 are used in
place; no dependency is introduced or upgraded. Rust host test debug data is
disabled for bounded output size. Process-local temporary/cache/build paths
stay on D:, with the existing signing credential used in place and not copied.

The three test compilation fixes change only key enumeration to Android's
existing keys iterator. The same expected key sets/assertions remain. All
14 corrected baseline test bodies are unchanged in the final 20-method roster;
six scoped-navigation methods are appended. They exercise real decoder,
controller and ViewModel code with original synthetic Host rows and narrow
reader/gateway seams, rather than stubbing validation verdicts.

Coverage includes exact display and native status retention; incoming/outgoing
promises; required nullable return item; malformed types/origins/parties;
bounded source/identifier/UTF-8 values; version/scope/head/observer/privacy and
cursor checks; pagination/search; inherited evidence; same sequence on another
branch; wrong/unwitnessed event; unavailable retry; no flattened-ID dispatch;
late noncooperative reads; dismissal/disposal; and a retained ViewModel callback
after a branch/head change while the same reference remains visible.

## Artifacts and independent verification

| APK | Bytes | SHA-256 |
| --- | ---: | --- |
| org.locallore.app.archiveverify | 27,756,156 | `357aed8ca0ba661c7d5cfdd9e0bdf04a6066f7d58f74604dd54059cae5aa3ca0` |
| org.locallore.app.archiveverify.test | 2,220,171 | `ae7fac7e2115a172537f54f45535d294e6b57274578b9ce61944f23b97169367` |

The paired public audit reports matching certificate
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Test permissions remain solely android.permission.REORDER_TASKS.

Independent source review verifies all seven production files against the
reviewed draft, actual final test bodies, and the existing native Query2
contract. It finds no concrete blocker; it is review evidence rather than
owner acceptance. Final source-review receipt SHA-256:
`16b45e8e7807fef85d13709cbdc2a8033074b506a8627c6e1f14061c4012b25f`.

An independent closed-file reader verifies all four phase request/start/actual-child/
command/result chains, current source maps, all 365 unique XML test identities
including the exact 20 new methods, all 32 named Rust results, lint and the
actual APK bytes/public audit outputs. It exits 0: 1,594 ms body / 1,748 ms
outer, with a 60-second stdlib subprocess bound, not a separate Windows Job
attestation. Receipt: 86,571 bytes, SHA-256
`3d9d2c1a469ec79925ffbee41e850ed6f5b9fe116c0677ab08b046983d6ad4dd`.

Two earlier reader failures remain preserved: an incorrect helper-file role
for GREEN, then an assumed package field absent from the product-audit schema.
Corrections bind the actual helper and exact producer schema; the separate
paired-audit package checks remain. These are checker errors, not product
failures. The reader does not rerun tests/audits, import project code, query
native processes, or inspect tools, keys, models, guests or the storage ledger.
It uses read-only Git and closed source/log/XML/APK files.

## Retention and remaining qualification

Private controls, original failed and successful logs/XML, source maps, review
receipts and selected recovery stay under the matching
`2026-10-30-promise-records-v1` Experiment/Recovery roots on D:. Source and
generated outputs in both worktrees remain in place. The packet declares an
8 GiB cap for new source/build/control/selected recovery, with stop monitoring
before 7 GiB during checks. Ticket handoff records the final retained size and
recovery seals. Existing shared tool caches are reused in place; no full cache,
image, model, key or source-bundle backup is created.

This packet runs **no emulator, phone, model or ADB operation**. B32's ten
emulator passes used different APKs and do not qualify this source. The new
Promises Compose journey, touch/scroll/large-text/TalkBack behavior, actual
Android/JNI round trip and process recreation remain unrun. JVM synthetic
frames plus separate Rust tests do not substitute for that end-to-end target
journey. Full Android journeys, real-model quality/performance, provider-running
cancellation, causal OS death, physical-device/ARM64 and privacy gates remain
separate. No settings/access change, other-emulator stop, merge or release.

Next runnable implementation candidate is the separately recorded
M05.03/M10.04 narration substring-grounding defect: establish a real regression
before changing it. A target promise journey needs a reviewed fixed protocol,
fresh source/artifact admission, storage capacity and applicable authorization.
The earlier single emulator grant remains spent; this feature grants none.
