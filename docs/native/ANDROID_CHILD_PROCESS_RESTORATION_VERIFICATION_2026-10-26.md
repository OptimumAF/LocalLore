# Active-child Android process restoration — 2026-10-26

M10.02 supporting mobile lifecycle testing, M05.05 supporting restart behavior,
M08.01 branch integration supporting and M09.03 draft preparation. The
implementation is based on open/unmerged PR #198 at `e3eb20a2`, with no merge or
release. This verified supporting slice is **in review**. Full task criteria
and owner acceptance remain pending.

## Scope and implementation

The [closed child-case protocol](ANDROID_CHILD_PROCESS_RESTORATION_PROTOCOL.md)
extends the external controller to the actual fork UI, inherited parent receipt,
selected active child and scoped unsent draft. The root case is preserved.
The child case is create-only, with its own fixed private fixture and exact
case; failed partial setup cannot be adopted or retried as a fresh cohort.

Two original native stories are created through the product. B receives one
explicit parent Dialogue at head1. The existing boundary review, explicit
consent, confirmed fork and explicit child Resume controls create a child at1.
The test then saves a distinct child draft, kills only the stopped background
product process, verifies the restored child, sends once on the child, and
repeats the actual saved-task death. Required final heads are A0/Broot1/child2,
with inherited parent text and exact child draft preserved. This is a test
contract until actual results below establish its execution.

`NativeForkGateway` adds an optional trusted observer immediately before
register/run JNI attempts. MainActivity wires it only in the existing debug
process profile, mapping a fixed label to the unchanged probe's `other` key.
No new observation field, canonical protocol, native method, Rust rule, schema,
runtime/model dependency or gameplay authority is introduced. The secondary
one-argument constructor preserves existing trailing-lambda callers. Status,
lookup and cancel/close resource operations are outside this mutation counter.

The existing timeline popup and fork dialog expose their test tags only under
the existing opt-in flag. `fork-scroll` names only the dialog's existing scroll
column. Default false behavior, user-facing copy and callbacks remain unchanged.
No accessibility or other system setting changes.

Source commits: `cfc65b26` optional observer and three actual-JNI tests;
`bf8f8c65` opt-in presentation/wiring; `0d5c5a67` child controller;
`37626440` bounded dialog/consent readiness. Independent source review caught
the child head2 parser bound and missing final native-reread check before
execution. The parser keeps root<=1 and child<=2 with fixed bound controls.
Root review added waits for the dialog and checked consent after the sole
clicks. These are source findings/corrections, not measured runtime REDs.

## Reproduction and environment

Use the [parent's pinned tools and isolated build
command](ANDROID_PROCESS_RESTORATION_VERIFICATION_2026-10-26.md), including
`localLoreInputDraftVerification=true`, `localLoreInputProcessVerification=true`,
exclusive `.gradle-input-process`, offline dependencies and disabled SDK/tool
downloads. The final invocation also runs `:draft-process-controller:clean`
before its assemble/lint tasks. No dependencies are added or updated.

Product, controller and platform-test APKs are audited using the same two
repository auditors plus actual badging, manifest and signing readback. The
ordinary product remains separate from the fixed `.draftprocessverify` identity.
Native libraries for both ABIs package with16KiB alignment; this packet executes
only API35 Google APIs x86_64 with4KiB guest pages.

Use separate fresh LocalLore AVD cohorts for `restore_non_default` and
`restore_child_branch`, with exact signed APKs and `cohort=create`. The existing
four fixed instrumentation arguments, self-targeted controller and full
saved-ack/STOPPED/new-PID/same-task/postmortem counter checks remain mandatory.
The controller case cap stays120s, and individual instrumentation clients stay
bounded at180s. A client exit0 alone never establishes a passing oracle.

Each owned UI-only AVD uses2GiB/two CPUs and320×640. Admission requires4GiB
available host physical memory,2GiB guest commit plus2GiB reserve, and
C:64GiB/D:16GiB free. This is not a supported model profile and does not relax
the independent physical-phone/model gate. Existing AVD registry/configuration,
ADB server and unrelated emulator remain untouched. Only exact owned LocalLore
SDK jobs may be stopped after their clients close; no guest-flush claim follows.

## Actual verification

| Check | Actual result |
| --- | --- |
| Product baseline at `bf8f8c65` | Owner132,377ms/0,516 unchanged source inputs.234 JVM tests/27 classes actually execute, zero failures/errors/skips. New three-method native observer class compiles; runtime is a separate gate.81 tasks:19 executed/62 UP-TO-DATE. |
| Final controller at `37626440` | Owner21,162ms/0,516 stable inputs including Java. Clean controller Java compiles; app/JVM results retained UP-TO-DATE.125 tasks:45 executed/80 UP-TO-DATE. |
| Signed artifact checks | Owner2,393ms/0;11 commands and raw outputs checked. Exact package/permissions, disabled backup, runner targets, matching signing and native ABI/alignment audits pass. Product lint0 errors/1 existing warning; controller0 errors/2 warnings (DataExtractionRules, MissingApplicationIcon). Not a whole-DEX absence audit. |
| Root-case control | **82 checks/two actual deaths pass**, owner208,478ms/0,92 clean completed clients with zero stderr,516 stable source/helper bindings. Three distinct process identities, one task, factory1 and both restored states; old terminal vectors zero then one free_text/prepare/commit. One additional parser-bound self-control explains82 versus the parent's81. |
| First broader regression |79 pass/3 fail, no skips, across82 methods/17 classes; owner281,474ms/1,101 clean clients and516 stable inputs. All three new actual-JNI observer methods and four existing native/app fork methods pass. Three existing panel tests fail on partial text expectations with `assertTextContains`' default exact-item matching; correct full UI labels are retained in the raw failures. |
| Test-only expectation correction `2c9cbe13` | Changes the import and four expectations to `assertTextEquals` with full parent/child/outcome labels. Production UI, callbacks, consent/counters, no-auto assertions and method rosters are unchanged. Rebuild129,165ms/0,516 stable inputs;8 tasks execute/116 UP-TO-DATE. JVM results retained, not rerun. |
| Corrected signed artifacts | Owner2,287ms/0,11 audit commands pass. Product and controller bytes/hashes are identical to the root-control artifacts; only the test APK changes. Existing owned package UIDs and all old APK hashes are checked before updating only the test package, then exact new bindings are checked. No uninstall, data clear or unowned package update. |
| Corrected broader regression | **82 methods/17 classes pass**, zero failures/skips; owner329,475ms/0,133 completed0/clean clients with zero stderr,516 stable source/helper hashes. Every source method's start/pass pair, exact roster and final `OK` are checked. |

The root oracle uses the exact final product/controller; its auxiliary test
APK predates the test-only correction and is not retroactively relabeled.
The corrected82-method run uses the new test APK. Both516-input source snapshots
are retained; their only source difference is the panel test expectations.
The old panel file is recovered from exact `37626440` Git bytes and checked
against the original source-owner hash, not reconstructed from memory.

After all clients close, the root-control SDK job is stopped explicitly:
1,286,182ms, `stop_requested`, worker1, known cleanup/capture, unchanged
helper/manifest and external registry/token observations. Worker1 reflects the
requested termination; no guest-disk-flush guarantee is claimed. Its canonical
fixtures are not cleared or silently adopted for the child case.

The actual child controller completes **123 checks/two genuine process deaths,
DONE/NONE/passed**. Its raw success proof verifies parent setup/fork through the
real UI, three distinct process identities in one task, factory1 and restored
state twice, both final old-process vectors, inherited parent text, the exact
child draft, one explicit child Send and fresh native A0/Broot1/child2 heads.
All85 captured clients complete0/known cleanup/zero stderr, with516 stable
source/helper hashes. No model call occurs.

The initial host owner is **205,943ms/1**, not a green wrapper result: after the
controller completes, its expected-text digest check fails. The external driver
builder's Python pipe uses `cp1252`; both bad literals exactly equal the intended
UTF-8 bytes decoded asCP1252. This is a host verifier error, not an Android
input/model-transfer failure. The device's two digests match the intended
original text. The failed script/output remains unchanged and retained.

A separate **read-only collector**, owner103,886ms/0,67 clean completed clients,
uses ASCII Unicode escapes and explicit UTF-8 reads/writes. It revalidates the
retained completed raw RESULT_OK proof, exact closed fixture/owner/signing/APK
and text hashes, three process identities/two terminal vectors, current final
product PID and fixed private created/saved/commands/fixture records. It invokes
no instrumentation, UI action, install, fork or gameplay operation. Its summary
records `controller_reexecuted=false`. The already committed journey is not
replayed and its fixture is not adopted as a new attempt. The controller result
and the repaired readback remain separately attributable.

After that collector closes, only the exact child LocalLore SDK job is stopped:
550,033ms, `stop_requested`, worker1, known cleanup/capture and unchanged
helper/manifest/external registry/token observations; no guest-flush claim.

| Final retained signed APK | Bytes | SHA256 |
| --- | ---: | --- |
| Product |24,554,470| `b5bd5840cf7f6f2d2be71e08f137ad5713af879102b1307620ca3d0cd4715852` |
| Android tests |2,664,443| `ce5af9e99c966aafd7486d5100137b1ac1fbac1f6f3ad5a73c90542d09798643` |
| Controller |42,737| `1d2857d32103dc316748f41e5f7aa77abb2b09d251afccc4a0c69896502698d2` |

The selected private index binds2,419 files/19,107,467B, SHA256
`222c247907813784bdaefbe5c34246f2904ef242aa823a311e6b0de691dd4e5e`.
It includes the failed original regression and host verifier, corrected raw
rosters/readback, source snapshots, external drivers, frozen helper exports and
JVM/lint reports. APKs are retained separately; model weights, compiled caches,
guest images, app databases and other-project data are excluded. This is the
listed selection, not an assertion that every possible transient output was
saved. No private records or binaries are uploaded.

Next runnable lifecycle task: the missing/retired selected-child recovery path
and its visible fallback notice. Later-parent/sibling visibility and physical
model qualification remain separate gates; no passing result here closes them.

## Limits and next work

The intended child case covers one active child at a completed parent boundary,
not later parent advancement, siblings, retired ancestors, missing/deleted
selection, all Android APIs, force-stop, task dismissal, power loss or physical
device behavior. Native canonical scope/replay rules remain authoritative;
the controller observes the UI/native route rather than supplying ledger data.
Scripted inference establishes plumbing, not model performance or story quality.
Host-owner durations include admission/startup/checking and are not latency
benchmarks. Private evidence, unique IDs, APKs, guest images, saves and model
weights remain outside Git; only synthetic fixture sources and bounded reports
are public.

The [phone harness PR #186](https://github.com/OptimumAF/LocalLore/pull/186)
records the reconnected device's memory-admission refusal. No repeated favorable
sampling or phone model copy/load/inference is performed by this packet.
Full M05.05/M08.01/M09.03/M10.02 and reference-phone/model/quality gates remain
unchecked pending their wider criteria and owner acceptance. No merge/release.
