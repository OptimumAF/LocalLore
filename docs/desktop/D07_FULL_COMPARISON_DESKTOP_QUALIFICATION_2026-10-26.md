# Full comparison desktop scripted slice: qualification draft

Supporting **D07.06/.02/.04**, under [Root claim6422925411](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6422925411).
This draft records completed, source-bound checks. **Actual hidden WebView and
final aggregate qualification remain pending.** It awards no full D07 acceptance,
human quality approval, native-model desktop qualification or release readiness.

The [frozen contract](D07_FULL_COMPARISON_DESKTOP_CONTRACT_2026-10-26.md)
started at `f77c36e2`, following accepted `1bb152f9`/PR209. Draft integration
source is `7f7d870c295463b6788315ccadb7127a0d935ad6`; earlier checks below retain
their actual source attribution. Root executed the checks. This document's
author read terminal records/logs only and performed no application execution.

## Implemented boundary

Ordinary desktop controls run fixed **ScriptedBaseline fake inference** through
the existing Rust `EvaluationManager` parent Job/worker and shared protocol3
`literal_v3::run_comparison/inspect_comparison`. Paired runs use the existing
scripted reference APIs; rollout runs use each arm's actual history. Literal and
Relevant constructions remain the compiled shared descriptors, not renderer
choices. No new engine, Store, memory semantics, provider or model owner is added.

Each native-owned UUID directory contains bounded `desktop.json` index metadata,
shared authoritative output under `work/`, and paired-only `reference-source/`.
The index's kind/protocol/full shared binding must match an existing manifest.
Canonical receipts, source checks, replay and evidence remain shared Rust duties.
Status, lookup, open and an exact repeated start never implicitly resume work.
Resume is explicit, with1..4 new scenes; a completed resume performs no new work.

The closed `evaluation_comparison_run` transport captures the actual native
WindowLease and Host Story Lab permission. Cleanup close does not require the
grant. Execution completion is **not** permission to read private evidence:
managed inspection obtains independent native spoiler-read consent and reuses
the existing reader's actual Query2 observer filtering and raw-evidence guards.

## Preserved failures and corrections

| Attempt | Actual source / retained log | Result and disposition |
|---|---|---|
| First service compile | `7e4556d6`; `d07-full-comparison-service-first1.log` | Exit101, E0308 in the token guard; no tests executed. This is a compile failure, not behavioral RED. Its process record says terminal source unchanged=false; no immutable-cohort claim is made. |
| Original seven service tests | `7e0423d8`; `d07-full-comparison-service-first2.log` | **6 passed /1 failed**,456.79s test time. Paired resume3 hit the test's180s scheduling wait while operation2 was running with null error. Failure retained. |
| Scheduling fixture correction | Authored `68889826`, integrated `001e8faf` | Only the helper wait180→600s and its comment changed. Remaining18 scenario turns/both arms incur repeated SQLite prefix/cold validation. Behavioral assertions and product/runtime/consent/cancel/resource/quality limits were unchanged. This correction is not a latency qualification. |
| Per-run budget regression | `6986a65d`; `d07-full-comparison-budget-red1.log` | **0 passed /1 failed**,27.77s. A partial real rollout plus three owned12MiB padding files exceeded the existing32MiB leaf cap; resume changed the inventory before reporting budget failure. This is actual behavioral RED. |
| Budget fix | `4a00f5b8`; `d07-full-comparison-budget-green1.log` | **1 passed /0 failed**,9.19s. Prework budget refusal preserves canonical DB/checkpoint/invocation/ledger bytes. Synthetic padding is not a disk-full experiment. |
| First frontend checker | `6986a65d`; `d07-full-comparison-fe-first1.log` | **54/54 passed**, but its mock parsed query strings and masked the native object's required wire shape. Not native wire-conformance evidence. |
| Strengthened frontend boundary | `6fad061b`; `d07-full-comparison-fe-wire-red1.log` | **47/56 passed,9 failed**. Checker now requires a nonnull/nonarray object and includes a positive actual-controller dispatch case. Original54 assertions retained. |
| Object-forwarding fix | `8bb22d96`, checked at `4a00f5b8`; `d07-full-comparison-fe-wire-green1.log` | **56/56 passed**. Controller sends the object; native parsing was not relaxed to accept strings. |

The frontend cases use synthetic transport, actual controller code and React
static HTML. They are not native IPC, WebView rendering or model evidence.
No failed attempt above is silently replaced by its later success.

## Completed integration checks

| Check | Source | Exact observed result |
|---|---|---|
| Native Rust full-comparison service + managed reader | `f4270d8bc5c31720e97ad0f9605ef4d18b1fc16c` | **11 passed,0 failed,0 ignored**,465.39s test time;17.39s compile. Process exit0, clean source and terminal source unchanged=true. |
| Closed native command parser | `7f7d870c295463b6788315ccadb7127a0d935ad6` | **8 passed,0 failed,0 ignored**,0.01s test time;30.62s compile. Process exit0, clean/unchanged source. |
| Wired full frontend verifier | `7f7d870c295463b6788315ccadb7127a0d935ad6` | Exit0; strict TypeScript, request/schema checks, existing controller/headless suites and normal-frontend development-hook exclusions passed. Process clean/unchanged. No aggregate assertion count inferred. |
| Earlier full frontend verifier | `c3b31e4af9f3403de18aa9595a393406c05d7c6e` | Exit0; retained separately, not additive evidence. |

The eleven native service cases comprise the original seven, one budget guard
and three post-implementation managed-reader cases. They cover paired1→resume3,
rollout4, actual report3/48 rows, reference immutability, completed-resume file
equality, exact-client retry/conflicts/lookup, cold reopen/new epoch, wrong native
index/shared manifest/checkpoint refusal, global worker exclusion, cancellation,
stale operation, retirement and spawn failure. Managed-reader tests additionally
cover independent consent, late-close suppression, actual Store-cut History
queries for Player/Mira/Sable, early raw denial and retained read-lock exclusion
until explicit close. These finite tests are not a universal concurrency proof.

Eight parser cases cover closed keys/actions, lowercase UUIDs, safe operations,
integer1..4 batches,4096-byte encoded Value cap and refusal of renderer-selected
provider/policy/path/consent. Parsing an already decoded Value does not prove
duplicate-key rejection in arbitrary raw transport bytes.

## Reproduction

From repository root, using the coordinator's existing isolated native target:

```powershell
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir <NATIVE_TARGET> --bin locallore-desktop-spike evaluation::comparison_run::review_tests:: -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir <NATIVE_TARGET> --bin locallore-desktop-spike comparison_run_commands:: -- --nocapture --test-threads=1
```

From `apps/desktop`:

```powershell
<NODE> check-comparison-run.mjs
<NODE> verify-frontend.mjs
```

`<NATIVE_TARGET>` is a task-owned existing directory, not a shared/protected
checkout. `<NODE>` in the retained frontend process record is the bundled
Node24.22.1 executable; no fresh version measurement was performed by this
document author. Final source-bound environment versions remain pending below.
Native Rust test process records include exact arguments and timestamps; test
durations above are not total command wall times or user-facing latency metrics.

## Pending final qualification — coordinator completion required

| Gate | Current disposition |
|---|---|
| Actual hidden/unfocused app-owned WebView journey, initial and fresh-process restart | **PENDING**; no terminal counts, source/artifact seal or pass inferred from the active launcher. |
| Actual UI paired/resume/rollout, unknown ACK/recovery, independent reader/privacy and cold reopen | **PENDING** native IPC/controller journey evidence; Rust/mock results above do not replace it. |
| Application-owned PNG/semantic captures and visual inspection of every produced image | **PENDING**; no image/layout claim in this draft. |
| Bounded frontend/native error buffers, stderr, process exits/timeouts/truncation | **PENDING** for this actual application cohort; prior lifecycle findings are not current zero-error evidence. |
| Final native normal/development suites, strict lint and format | **PENDING** final candidate results; filtered11/8 results are not whole native suites. |
| Final frontend/format and normal frontend/native production restoration | **PENDING** final source/artifact binding; earlier verifier success remains attributed above. |
| Shared compatibility, Android Rust-host/dependency checks, any unavailable checks | **PENDING** final coordinator packet. No SDK/JVM/ABI/APK/device execution is claimed. |
| Final source closure, artifact manifest/counts/hashes, environment versions and PR status | **PENDING**. No aggregate evidence seal or PR-ready declaration is made. |

The planned fixed launcher is `apps/desktop/comparison-run-harness.mjs`, using
the existing development harness and native-only synthetic fixture surface.
It is listed as a reproducer, **not as a completed run** in this draft. The user
forbids desktop control: any future evidence must remain application-owned
CapturePreview/semantic output, with no desktop screenshots, input injection,
window activation or unrelated application automation.

## Retained local evidence

Logs/process records are private, gitignored under `<TASK_ARTIFACTS>`; no raw
story, model path or machine-specific absolute directory is published here.
The following hashes identify the terminal logs read for this draft. They are
not a final whole-cohort manifest and exclude all active application logs.

| Log basename | SHA256 |
|---|---|
| `d07-full-comparison-service-first2.log` | `252957ac904cfaf29f7ab32bb039d941c9392cda38fdc6857cd4b636213be6be` |
| `d07-full-comparison-budget-red1.log` | `8d4986056e10a917debfd4e57ac1c40d6608f61129ae151a7a958dde2bd36523` |
| `d07-full-comparison-budget-green1.log` | `674e2f07a4c56d21d9dfbd57bafde24d75ad6dd3a001b00d787d02ed79d16c21` |
| `d07-full-comparison-service-corrected1.log` | `ecc1acc051470b11df9246fa22c1ac89fe462a94de85acb00221000ee3bb5c5b` |
| `d07-full-comparison-fe-first1.log` | `fbb61499605bca8ac4d07608003dd183c59df4e628baac5bf6aa57bc3c0b1688` |
| `d07-full-comparison-fe-wire-red1.log` | `7920b7f3be8f32c97c4e09b49910e9cc63ffc081cb048e6ce750548f3c6fe20d` |
| `d07-full-comparison-fe-wire-green1.log` | `f8b46b4e62c085f5ee988750248173a738215ba65d175c6b4686acd740bcebe2` |
| `d07-full-comparison-frontend-wired1.log` | `14fd3c0159dce9f75f6ca210a4c8e2fdc9721cdedc2ece2a269175d102edd0b9` |
| `d07-full-comparison-wire-native1.log` | `88a0c97dc64679e3691971df8af1030cf12b4b870acc35a4a5d0d4dc6fd43b13` |

Ordinary desktop **native-model execution remains unavailable** in this scripted
slice, although shared native producers have separately qualified prerequisites.
Scripted reports preserve real outcomes and do not establish prose quality,
human enjoyment, fair model superiority, offline/whole-RAM/performance behavior
or phone parity. No downloaded assets, provider selection escape, canonical
rewrite, competing persistence or automatic inference on inspection is authorized.
The next gate is the pending actual UI/final compatibility packet, followed by
coordinator review of this document's final source-bound additions.
