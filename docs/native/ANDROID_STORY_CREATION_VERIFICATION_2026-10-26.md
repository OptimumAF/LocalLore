# Explicit starter review and named creation — 2026-10-26

Supporting M09.02/M09.03/M09.06 and M10.01/M10.02; draft PR #213, stacked on
draft/unmerged #212 (`87f828e8`). Executable source is frozen at
`8f17ac7da2bc58a3e0f20436431cb44a9370ae7e`. Full task acceptance remains pending.

## Behavior and boundaries

The actual persistent Android New story action opens a Rust-owned, player-visible
Lantern Quay starter review. A bounded title and explicit Create are required.
Cancel before creation preserves the library, selection and unsent draft.
The engine validates the original starter/hash/title/creation ID, and the Store
compares or inserts in one IMMEDIATE transaction. An exact retained retry returns
the current accepted history without resetting it. Existing legacy fixture creation
and generic Store title behavior remain compatible; no migration/dependency was added.

The returned Engine must also retain the exact original Seed before Host attachment.
Retained editor actions consult both latest Compose state and synchronous ViewModel
eligibility, including between opening review and recomposition. A failed or cancelled
dispatched creation may already exist: confirmation is consumed, no automatic retry
occurs, and closing drains the finite operation then reconciles the library.

Premise, tone/content boundaries, player/character and rule-profile editing are still
unimplemented. This review exposes an existing original starter; it does not generate
new initial facts or invoke inference. Player-known facts and NPC knowledge remain
distinct. Canonical events own subsequent history; summaries gain no authority.
See the [contract](STORY_CREATION_CONTRACT_V1.md),
[probe compatibility](STORY_CREATION_PROBE_V2.md) and
[fixed nineteen-method protocol](ANDROID_STORY_CREATION_PROTOCOL.md).

## Host verification actually executed

Windows, Python3.14.7, Rust/Cargo1.93.1, JDK21, Gradle8.11.1/AGP8.10.1,
NDK29.0.14206865. Existing pinned/cached dependencies only; commands run offline.
Private owners retain command arrays, tool/source bindings, original streams,
before/after source maps, finite deadlines and terminal cleanup/capture records.

| Check | Result | Original private cohort |
|---|---|---|
| `python -I -B` unittest discovery in `scripts/tests` | 1,268 pass; owner119151ms/0;774 inputs unchanged | `host-full-v1` |
| Three-package `cargo test --locked --offline -p locallore -p locallore-storage -p locallore-workspace --all-features` | 785 pass,11 ignored,0 fail;111 harness summaries; standalone owner464521ms/0 | `rust-tests-v3` |
| Same three packages, `cargo clippy --locked --offline --all-targets --all-features -- -D warnings` | pass; owner18811ms/0 | `clippy-v1` |
| Full input-process debug build, clean/rerun JVM tests, both lints and eleven APK audits | pass; owner342494ms/0;259 tests/30 XML;0 failures/errors/skips; lint0 errors/3 warnings | `build-v1` |
| Model-receipt `:app:compileDebugAndroidTestKotlin`, native task excluded | pass; owner109500ms/0;774 inputs unchanged | `receipt-compile-v1` |
| Pinned offline npm restore, then frontend schema generation/type/build/verification and formatting | pass; restore15376ms/0; frontend17039ms/0 | `npm-offline-v1`, `frontend-v1` |

The complete current build is the versioned command:

```powershell
python -I -B benchmarks/android_process_verification.py build --out "$evidence/build-v1" --sdk "$sdk" --java "$java"
```

It builds x86_64 and ARM64 JNI, product/test/controller APKs, reruns259 JVM tests,
and checks signatures/manifests and the isolated profile. Artifact readback independently
matches all774 source inputs, five SQL files, thirty XML results and eleven audit records.
APK DEX readback confirms all nineteen new Android method bodies were compiled.
Compilation alone is not execution. The earlier JVM-only run (`jvm-main-v4`,84411ms/0)
has the same Android inputs; its full map predates exactly two later host-phase Python files.

The standalone Rust map has1,803 unchanged entries, equal to the Clippy map. One
historical Markdown file differs from its Git blob only by LF-to-CRLF conversion;
all other recorded entries match the frozen Git source bytes. The785 include ten
expected compile-fail doctests. Eleven ignored helper/historical/pressure/reparse
cases remain ignored; this run grants them no independent qualification.

The candidate compile uses the exclusive `.gradle-litert-worker` cache, all four
LiteRT/setup/volume/receipt flags, `org.gradle.java.installations.auto-download=false`,
the existing analyzer pin9.4.1, SDK download disabled and in-process Kotlin.
It resolves the existing pinned LiteRT-LM0.18.1/Kotlin2.4.0 graph but excludes native
compilation. It builds no APK and runs no model, inference, lint or device test.

## Original failures and corrections

- The initial broad Rust run (`rust-all-v1`,587231ms/101) failed an existing
  generation-consumer fixture's exclusive TEMP-directory creation on Windows.
  Add a process-local atomic suffix; keep all original six assertions/budgets.
  They pass focused and in both subsequent broad test executions.
- A new deterministic fault-port Host regression is genuinely RED
  (`seed-red-v1`,14658ms/101): a same-scope but different original Seed was accepted.
  The full Seed guard turns the focused Core3/Workspace9/consumer6/Store8 suite
  GREEN (`seed-green-v1`,39390ms/0); the original failure is retained.
- JVM setup attempts retain a cache-guard refusal and a private dry-graph matcher's
  mistaken rejection of the necessary `packageDebugResources` task. Correct the
  private invocation/matcher without changing product guards. A real Kotlin compile
  then rejected a public screen exposing internal `PlayDraftScope`; make the screen
  internal. The corrected JVM-only and full Android builds pass.
- The combined second broad test-plus-Clippy owner (`rust-all-v2`) expired at600015ms.
  Its111 test summaries show785 pass/11 ignored before Clippy starts, but the combined
  gate remains failed. Separate `clippy-v1` and single-command `rust-tests-v3` both
  complete successfully. No old failed record is relabelled.

## Frozen APKs

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Product | 32314536 | `767e511d8da322ee94ca50c244c6c0c00d6e4f69409bdc6e54518919c908ffc0` |
| Test | 2836682 | `99a5bff66e099da14465c54b3477f48340e63f55b51246147170a5777030ba28` |
| Controller | 54977 | `00ce5cc74364def1f44cdf57ce81f094025ad9b6c19d462e60c663278c85c9a0` |

The source-map file is99590 bytes, SHA256
`2e8fb9e75b5723a221695a34d5bdd18b101fefd8a0e09c445475ed6be8d764d4`.
All APKs share the verified debug signer. Compared with #212, the product's referenced
native payload grows339464 bytes and compressed DEX27463 bytes; unchanged entry count
and resources accompany7391649 bytes of additional ZIP layout overhead. Original
signing/ZIP records are preserved; no repacking or re-signing was performed. The exact
packager cause of the empty local-record gaps is unproven. No release-size claim follows.

## Android execution

Current native10 execution passes on API35/Google APIs/x86_64: the original three
classes' exact4/4/2 rosters,84 clean client records, owner425138ms/worker0 and known
cleanup/capture. Original class frames match their unique instrumentation client
copies. Component record SHA256 is
`abc288dd00d455b9dbd26c947c46200f9ed6d9ba5e306481a80b0d7e9dc6a754`.
The bound owned stop returns0; guest owner records `stop_requested`,489538ms,
worker1, cleanup/capture/closure true and `guest_flush_claimed:false`.
This grants no retroactive result to the older #212 APK or its failed preparations.

Two distinct new standard2GiB/two-CPU guest preparations have completed with known
SDK-client cleanup and prepared receipts. The first runs native10 above; the second
passes the fixed new19: exact8 wire,5 dialog,4 editor-fence and2 MainActivity methods,
87 clean contiguous clients, owner459943ms/worker0, known cleanup/capture and empty
owner stderr. Independent readback checks all774 unchanged inputs and original class
frames/client copies. Story record SHA256 is
`09ff7026408b96a2ac41465d1f330c6f77621816219d6ee2e008b20857148c33`.
All three packages were absent before each isolated installation; both runs use
the same frozen source/APKs. This new source/APK cohort follows terminal completion
of all coordinator build/test jobs. The unchanged4GiB physical-memory floor and6GiB
available-commit policy apply. Neither policy was relaxed and no favorable resampling,
system-setting change or stop of another project's emulator occurred.

The two real MainActivity methods exercise Cancel preserving the original library,
eligible canonical views, selected scope and unsent draft, then explicit Unicode-titled
creation, an accepted scripted potion gift and a second independent story. Fresh typed
native readers reopen the stored views. These are executed source-pinned canonical
assertions, not separately exported canonical sidecars, OS process death or real inference.
The new editor-fence methods also cover retained actions before recomposition.

After all clients terminate, the second bound owned stop returns0 and records
`stop_requested`,555596ms,worker1, cleanup/capture/closure true and no guest-flush claim.
Both owned guests are closed. A final read-only postflight matches both previously
recorded unrelated emulator native process identities and the original ADB server.
No server lifecycle operation was used. Native10/new19 do not substitute for broad89,
retained-archive2, the current probe2 external two-death controls or physical/real-model gates.

## Preservation and remaining gates

Source/tests/contracts are committed and pushed on `impl/m09-story-creation-preview`.
Original streams and private source/tool/owner records remain on C:, outside the
possibly cleaned D: working area. A verified terminal recovery set contains227 files,
19450899 bytes; ZIP4547362 bytes SHA256
`66a6b330b42440f6a8814e1955b6ef50291523246860f9e854c329df0837666d`;
index76547 bytes SHA256
`a25549a8e5ec180869cf1e720ec0f8d85c5376886ab250013d79f58e7b68cfb4`.
Every original/copy/ZIP member was rehashed. This set deliberately excludes then-live
build/runtime cohorts, targets, caches, model weights and saves. A first preservation
attempt refused Windows cross-API ctime differences before copying; its failure and
unchanged script remain, alongside the corrected within-API metadata checks.

A separate verified build/native recovery set contains309 files,37102335 bytes,
including all three APKs, the standalone Rust result, candidate compile and native10
originals plus the first guest's terminal records and three bound configuration INIs.
Its ZIP is18489028 bytes SHA256
`1ccc780f72beb3f8d7b9ceaacad0617fcd6018b8bbf34c588dc41452a23a18a8`;
index101843 bytes SHA256
`749b06b8496ff0881c9994aab12be4872e1a0366190a7a1001f4fd4e24da1f8c`.
It excludes then-live story-creation execution and all guest image/data subtrees.
The earlier227-file seal was rechecked unchanged.

The final UI recovery set contains213 files,639374 bytes: all87 original client
records/raws, four class outputs, source/owner results, the second guest's terminal
records and three bound INIs, plus exact authorization/presence/postflight inputs.
Its ZIP is226883 bytes SHA256
`2dc539c537ba81d73fefe22ef650206a1966c4ae3c61d77a05061c139c987c94`;
index72603 bytes SHA256
`af8463720e5e27a13c679ae6ecdebd6960d829d7ccb08ce145ad8984e5c2505b`.
Every original/copy/member was verified. All earlier227+309 originals, copies and
ZIP members were rechecked with zero mismatches and unchanged index/ZIP seals.
These recovery sets exclude guest images/data, caches, private saves and weights.

Physical-phone/model import, real inference, OS process death under current probe2,
joined native-resource drain, full customization, unfamiliar-user journeys and full
accessibility qualification remain separate gates. Prior results keep their dated
source/APK/probe attribution. No milestone box is checked, PR is merged or release published.

An aggregate of the already captured current-cohort device list finds two authorized
non-emulator candidates. This issues no new device calls and establishes neither
physical hardware identity nor a selected/qualified phone. Missing phone qualification
must not be described as a fresh observation that no phone is connected.

The next runnable verification task is M09.06/M10.02: unchanged broad89 and current
probe2 external restoration controls on their own fresh admitted guests. Phone
qualification first needs an identified authorized physical target and its separate
artifact/admission protocol; the emulator phase cannot silently adopt a phone.
Full M09.02 customization remains subsequent implementation work. Root claims are
released through the ticket handoff; task checkboxes require owner acceptance.
