# Guarded native literal execution and replay

Scope: D07.04 / M07.01 prerequisite. Accepted base PR184,
`4768cf0faa44b4d16d294d6fa7ad5ad03e98a6c3`; implemented and tested source
`3e280195eca052c15319d9c04ac84ea637671413`. GitHub #29/#11 own task status.

This adds an explicit **native Rust execution construction**, exercised with
scripted fake providers and real Core receipts. It uses the existing turn
pipeline, engine authority and narrator. It adds no competing inference,
persistence, memory implementation or story format. No Host configuration,
evaluator/report protocol, frontend/JNI decoder or UI route is exposed here.
Ordinary Play remains2.5 with its existing mandatory state and policies.

## Frozen version and authority

`play::execute_traced_with_literal_director_v1` takes the same actual mutable
Engine, Request, InferenceProvider, Cancellation, PlayProfile and optional
TraceSink as the normal traced entry. It selects a private native construction,
never a new ContextPolicy or JSON grant. The shared pipeline retains finite
action compilation and actual staging before provider work, actual parsed
proposal validation afterward, one malformed-output repair, grounded narration,
fallback, deadlines, cancellation and atomic candidate installation.

The guard's expected command does not enter the literal prompt/schema and never
substitutes for a model proposal. A wrong returned command is rejected. The
literal source/renderer is built from the actual before-Engine and shared
full-forwarded budget; no retrieved/compiled context or coverage is constructed.
The narrator still receives only actual sanitized staged evidence, excluding
old conversation and raw current Dialogue. This controls supplied evidence;
finite prose checks remain an imperfect semantic filter.

The immutable tuple is:

- `LITERAL_PLAY_PROMPT_VERSION_V1 = locallore-play-v2.6-literal-director-v1`;
- Domain1 actual player; source/render/schema/packing versions1;
- Director request schema ID `locallore-director-literal-v1`;
- grounded-prose-v2.2 narrator, existing `locallore-narrator-v2` request label;
- PlayRecord version2, `context=None` and `context_policy=None`.

Those absent fields mean no compiler/coverage provenance. They are never
Raw/Missing/Verified substitutes. No new serialized field or storage schema is
introduced. Source/render/schema/packing changes require a new literal version,
not repointing this identifier. Existing global PROMPT_VERSION, ContextPolicy,
old validators and Play2.1–2.5 encodings are unchanged.

The new `Engine::commit_staged_literal_play_v1` consumes the existing opaque
actual stage through a strict separate commit target. Public
`commit_staged_play_v25` still admits V25 only for fresh work. Both use the same
exact source basis check, regenerated candidate/evidence equality, bounded
append to a clone and final cancellation checkpoint before installation.

Literal record admission/replay checks the exact tuple, re-extracts the source
from the actual before-history and rerenders Initial and any used Repair under
the recorded profile. It trusts no serialized source counts/proof. Engine
commit/history/prepared/continuation dispatch recognizes only the exact literal
version before existing branches. Persisted metadata does not prove that a
provider ran; actual request/capture evidence is separate.

Exact recorded retry intentionally wins before changed construction, profile,
cancellation or target checks. It returns the original receipt and version with
zero provider calls, including an existing normal Domain2 receipt retried through
the literal entry. New unrecorded Domain2 literal work returns Version. A cached
normal result is not relabeled literal; the reverse also retains original bytes.

## Verification

Windows NT10.0.26300 x64, PowerShell7.6.5, Rust1.93.1 (`01f6ddf75`),
Cargo1.93.1 (`083ac5135`), LLVM21.1.8. Existing cached dependencies only;
locked/offline, one Cargo job, debug0/incremental0, owned target/TEMP. Every
terminal check below recorded clean and unchanged source. No install/download.

Frozen test source `f6e9a0f4` was integrated as `ae0ee62d` before implementation.
Its missing-API compile observation exited101 in0.580s; this is not behavioral
RED. New implementation3e280195 passed all nine groups on its first run:
0.14s tests /8.01s compilation /8.490s command. No expectation was relaxed.

The nine groups verify:

1. Both modes: actual provider and TraceSink Director bytes equal the accepted
   renderer, exact schema IDs, no compiled context artifact, sanitized narrator.
2. Actual malformed-first Director repair with exact Initial/Repair bytes and
   malformed narrator falling back to the actual approved mechanical narration.
3. Finite guard refusals with zero calls, actual wrong proposals with one call
   and no substituted command or canonical change; exhausted repair refusal.
4. Director/narrator cancellation without commit and new Domain2 refusal.
5. Cross-construction retries with invalid profile/cancellation, zero calls and
   unchanged original receipt, including existing normal Domain2 history.
6. Strict fresh V25/literal target fences and actual literal-stage installation.
7. Stage append/same-head different seed or history rejection, cancellation and
   caught callback panic without source mutation.
8. Full receipt/prepared/canonical replay, direct restore and fork continuation
   with exact bytes and no provider supplied to replay.
9. Eight defined single-field record mutations rejected on an uncommitted base
   through both native commit and real restore; actual Domain2-stage refusal.

The mutation tests are not cryptographic authentication against rewriting every
field into another valid historical contract. The fixed panic-hook message is
expected while the caught cancellation test passes.

| Check | Exact result / command time |
|---|---|
| Four accepted current-Play stable projections, before/after |1PASS each; unchanged original hashes;1.696s/1.401s |
| Six original whole PolicyCompilation references, before/after |1PASS each; unchanged original hashes;0.396s/1.134s |
| Default Rust workspace with locallore/host |837PASS/0FAIL/11ignored,125 result groups;663.018s command |
| Core all-target/all-feature strict Clippy |PASS;13.67s Cargo/13.919s command |
| Workspace Rust format |PASS;2.145s command |
| Desktop all-target/all-feature strict Clippy |PASS;14.06s Cargo/14.307s command |
| Normal desktop build |PASS;28.34s Cargo/28.464s command; executable not launched |

The full workspace includes Core, storage, workspace and Android Rust host
tests, including the new nine groups, eight renderer groups, source/cap tests,
old Play2.1–2.5 compatibility, SQLite recovery/transactions/archives, long-history
retrieval, job interruption/cancellation, Host traces and eight no-serde doctests.
It took1m30s Cargo compilation and545.19s summed test-group durations; neither is
application/model latency. Eleven ignored default entries comprise four
original-source historical probes, one compiled-page-profile opt-in, one
expensive16MiB boundary opt-in, two Windows symlink-privilege tests, one
superseded passive-refresh test, and two child-worker entrypoints invoked only
by their parent process tests. Parent interruption tests pass; the ignored
entrypoints are still reported as ignored. No ignored case is awarded here.

The four stable projection references explicitly exclude varying remaining
deadlines/stage timings and validate those separately. The six policy references
hash whole DTOs. Neither is a cross-run whole generated-receipt hash. Their
[pre-edit capture contracts](D07_LITERAL_DIRECTOR_RENDER_QUALIFICATION_2026-10-25.md)
remain unchanged. Independent bounded source review found no concrete defect in
the memory path, version/guard/commit fences, source validation or cancellation;
the reviewer performed no execution and supplied no human quality approval.

## Reproduce and boundaries

Use task-owned absolute target/TEMP paths; serialize with other heavy work:

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''
$env:TEMP='<task-temp>'; $env:TMP=$env:TEMP
cargo test --locked --offline -p locallore --jobs 1 --target-dir <target> --test literal_guarded_play -- --nocapture --test-threads=1
cargo test --locked --offline -p locallore --jobs 1 --target-dir <target> --test literal_director_legacy_bytes --test literal_transcript_legacy_bytes -- --nocapture --test-threads=1
cargo test --locked --offline --features locallore/host --jobs 1 --target-dir <target> -- --test-threads=1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <target>
cargo fmt --all -- --check
```

Raw synthetic logs/process records remain local and ignored under
`d07-literal-play-*`. Full-workspace log SHA256:
`b657c4000d792beca59dd572eee3bdc3d56ce9b62fb1823425bb2d691c8fcafe`.
Focused nine-group log:
`c4b43b72b5935e1e9871a1a8e4d9e64596dca2a35fca12d1ecb617910c8bf7b8`.
No private prompts/stories, personal paths, weights or raw diagnostics published.

These are Engine/host Rust tests and native compilation. There is no new
frontend/headless/WebView/native IPC rendering, installed-model execution,
model-cleanup qualification, Android ABI/JVM/Gradle/emulator/phone, performance,
RAM, installer or narrative-quality result. Existing moderate GLib advisory is
unchanged/open. Existing model and desktop evidence stays historical.

Next runnable work is typed Host construction and strict evaluator/capture/
decoder closure before UI exposure, with actual isolated replay/rerun/resource
ownership. No old report may be relabeled literal. Real-model paired runs,
inspection/persistence integration and human quality gates remain required.
Domain2 literal and unapproved maintenance remain unavailable. The previously
observed unrelated-library narration failure is unresolved. No full D07/M07
checkbox, desktop completion or release qualification is awarded by this slice.
