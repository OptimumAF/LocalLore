# D06 explicit private production capture — shared prerequisite

2026-10-23; D06.01/.02/.03/.06/.07 partial, not the full desktop exit gate.
Coordinator claim #28 comment 6361450910. Source `8c42188`, accepted worker
adoption `a2bb663` reconciled in tested tree `951aa91476402d63427e05c6e8eae2d1732b8232`.
No frontend capture consumer or private export preview is included in this slice.

## Actual artifacts and authority

The existing production `play::execute_traced` observes its real compiler result,
the exact structured requests sent to the provider, raw director/repair bytes,
parsed Proposal, validated plan, raw narrator bytes and final candidate Receipt.
It does not run a second context builder, model request or commit path. The plan
is labeled `validated_plan_not_durable_commit`; the final candidate is labeled
`accepted_candidate_not_durable_commit`. The Host/storage atomic commit remains
authoritative. Capturing a candidate never establishes that it was saved.
Existing metadata traces continue to identify committed/cancelled/stale outcomes.

Request copies retain the actual role, prompt, schema, model profile, scope,
turn, revision and budgets. Raw output copies contain exact UTF-8 text or hex
bytes with a full SHA256; unsupported/oversized copies are refused as whole
artifacts. Context copies preserve the production compiler's source references,
mandatory flags, estimates, omissions and diagnostics. These remain the player's
generation inputs even when a Story Lab reader inspects them. No omniscient
reconstruction is substituted, and nothing from this diagnostic store is read
by generation, Engine, storage, archives or character knowledge.

Both the regular metadata ring and raw capture are process-local. Default raw
capture is disabled. The legacy unscoped `request_full_capture()` remains
unsupported; the new consented API deliberately requires session ownership.
Existing metadata responses remain metadata-only and do not embed raw text.

## Host-v1 extension and privacy

Two additive commands use the same native-created Host capability and fresh
session/scope/persisted-head checks as metadata reads:

```text
trace_capture_configure {session,scope,expected_head,enabled,consent}
trace_capture_read {session,scope,expected_head,base_revision,turn,attempt}
```

Enabling requires trusted Story Lab construction plus explicit consent. It clears
earlier details and applies only to future attempts in that exact native session
and scope. A wire boolean cannot grant Story Lab capability. Read requires Lab
and an exact turn/attempt/base revision; it cannot request another observer's raw
data. Current head is checked independently of the captured immutable base.
Foreign owner, scope or selector never reveals an artifact. Generated Rust JSON
schema and TypeScript command union are updated together; no Host version bump,
Android-specific fork or persistence migration is added.

Capture can contain original input, spoilers and failed/unsafe model text. It
never auto-uploads or enters a normal story archive. No filesystem persistence
or export endpoint exists here. UI opt-in/preview and an export destination must
be implemented separately before claiming D06.06 complete.

## Limits, deletion and failure behavior

At most 3 attempts, 16 artifacts per attempt, 49,152 encoded bytes per artifact,
196,608 per attempt and 524,288 total retained encoded artifact bytes. These are
serialized-content caps, not a promise about Rust allocator overhead, OS paging,
all temporary buffers or forensic erasure. Structured serialization stops at
the artifact cap; prompt copying refuses >32,000 bytes, raw output >16,384.
Eviction drops the oldest attempt. Reads are also bounded by Host's 262,144-byte
response limit.

Consent expires after 600 seconds, checked on access/capture. There is no timer
that guarantees physical memory disappears exactly at expiry. Clear/disable,
reconfiguration and owner revocation discard retained artifacts and invalidate
old attempt epochs, preventing late callbacks from restoring them. Session close
atomically retires its owner before a best-effort diagnostic lock; the next
access clears even if that lock was busy at close. Model unload cancels work but
keeps the session owner live. Process/window teardown retires all session owners.

Details report disabled, expired, not_retained, recorded or truncated.
`exact_reconstruction` is always false: optional nonblocking hooks may drop when
busy, and incomplete traces are never rebuilt later from current state. Recorded
means the retained copies are actual observations, not a guarantee every stage
published. Stage callback panics are caught and disable the sink; capture time
is excluded from the existing gameplay deadline clock. Allocation failure is
not claimed recoverable. Existing wall-clock StageTiming values can vary between
runs even when semantic receipts and canonical state agree.

## Executed checks and limits

These initial results are historical development cohorts. The final integration
cohort and failures/retries are recorded at the end; do not add counts from
different source revisions together.

Windows, Rust/Cargo 1.93.1, locked/offline; task `m07-context` target/TEMP/TMP,
DEV/TEST debug=0, incremental=0. Frontend Node24.22.1 with pinned checked-in lock
dependencies. All new test providers are synthetic; no model or desktop control.

```text
cargo +1.93.1 test --workspace --all-features --locked --offline --target-dir <target>
299 passed, 0 failed, 0 ignored.
cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline --target-dir <target> -- -D warnings
PASS
cargo +1.93.1 test -p locallore --features host --test turn_capture --test turn_capture_host --locked --offline --target-dir <target>
5 production capture tests + 1 Host wire journey passed.
cargo +1.93.1 fmt --all -- --check
PASS (formatting also applied before the frozen source commit).
node apps/desktop/verify-frontend.mjs
PASS: build/type/schema/controller checks and normal-bundle hook exclusions.
node apps/desktop/node_modules/prettier/bin/prettier.cjs --check 'apps/desktop/ui/*.{ts,tsx,html,css}' 'apps/desktop/*.{json,mjs}'
PASS
git diff --check
PASS
```

Four private-store unit cases exercise opt-in/owner/epoch/TTL/clear, exact hex,
whole-artifact refusal, attempt eviction, actual global/attempt/count caps,
capacity recovery and owner retirement. One Host unit proves teardown revocation
while holding the trace lock and proves model unload keeps the session usable.
The production tests compare actual provider request role/prompt/schema, state,
events and semantic Receipt with capture off/on. Only nondeterministic existing
StageTiming elapsed values are normalized. They cover contradictory narration
fallback, malformed output with one repair, rule rejection without a candidate,
cancellation with no invented output/receipt, late clear/re-enable and callback
panic. The wire journey checks consent/Lab/fresh-head/selector guards, captured
base versus committed head, disable deletion and closed-session refusal.

Initial test-author errors are retained locally: an invented Request.actor field
was correctly rejected as Malformed; a post-close expectation was corrected from
UnknownSession to the established Closed error. Root source review also found
and fixed owner retirement accidentally attached to model unload rather than
close_all, and added the busy-close/unload regression before source freeze.

Local logs under `<target>`: `private-capture-workspace.log`,
`private-capture-clippy.log`, `private-capture-focused-final.log`,
`private-capture-frontend.log`, `private-capture-frontend-format.log`.
Independent review and platform integration results are recorded separately.

Additional coordinator platform checks on the same frozen production tree:

```text
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <target>
9 passed, 0 failed.
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <target> -- -D warnings
PASS
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <target>
30 native module tests + 2 harness contracts passed; 1 existing test ignored.
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <target> -- -D warnings
PASS
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <task>/android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain '-Pandroid.builder.sdkDownload=false'
BUILD SUCCESSFUL in 33s; 78 tasks, 21 executed/57 up-to-date.
python scripts/audit_apk.py <task>/android-build/_app/outputs/apk/debug/app-debug.apk
PASS with ANDROID_HOME explicitly set.
```

Android used existing JDK17.0.6/Gradle8.11.1/AGP8.10.1/Kotlin2.2.21,
SDK36/NDK29.0.14206865 and task-owned Gradle/build outputs. Both x86_64/arm64-v8a
JNI libraries and debug/test APKs built; 38 JVM tests, zero failures/errors/skips,
lint and APK permission/16KiB ELF checks passed. No Android device/emulator was
operated. The first manual APK-audit retry lacked ANDROID_HOME and failed with
that fixed prerequisite error; the explicit configured retry above passed.
The asynchronous Gradle observation handle was absent when polled, so its
terminal BUILD SUCCESSFUL log and test XML were inspected rather than restarting
the completed build. Platform logs use the private-capture-eval/native/android
prefixes under the task target. These are compatibility checks, not native UI
rendering or a real-model capture journey.

No new WebView image, native UI journey, real-model capture, persistent private
capture/export preview, summary maintenance trace, pause/re-run sandbox or full
D06 acceptance is implied. Existing actual metadata/inspector/evaluation panels
remain available; missing capabilities must remain visibly unavailable until
their corresponding shared/UI work is implemented.

## Final accepted-main integration cohort

Production source `744b722` includes accepted main
`bffa7e66bf888411a6a5fce47165965fa247a2ce` (#86) and the new private-owner
retirement fix for the accepted #81 whole-story deletion path. The coordinator
did not modify the concurrent Android work. `Host::invalidate_story` retires
every matching session owner before cancellation/removal, preserves unrelated
owners, and recovers a poisoned state guard only for cleanup without clearing
the poison. It releases that guard before a best-effort trace lock. Private
copies behind a busy diagnostic lock become inaccessible immediately and are
pruned on the next access; this is not an immediate physical-erasure promise.

Windows Rust/Cargo 1.93.1; Node 24.22.1/npm 11.19.1; development/test debug=0,
incremental=0; locked/offline Rust dependencies and task-owned D-drive targets.
Exact final commands use the command templates above, with these results:

| Check | Final result |
| --- | --- |
| Workspace `test --workspace --all-features` | 388 passed, 0 failed, 4 existing qualification tests ignored |
| Workspace default and all-feature `clippy --all-targets -- -D warnings` | Both passed |
| Native desktop `test --features dev-harness` | 30 module + 2 harness contract tests passed; 1 existing ignored |
| Native desktop strict dev-harness Clippy | Passed |
| Workspace fmt, frontend verifier, frontend Prettier, diff whitespace | Passed |
| Android debug + debug-test APKs, JVM tests and lint | Both Rust JNI ABIs built; 128 JVM tests, 0 failures/errors/skips; BUILD SUCCESSFUL in 1m53s, 78 tasks (29 executed, 49 up-to-date) |
| Current APK permission and ELF alignment audit | Passed; all four native library entries have 16KiB load alignment |

The final workspace first attempt failed in the existing database-copy test's
temporary-directory constructor with Windows AlreadyExists (code 183), before
its story checks. Repeating the complete workspace suite with a new UUID
task-owned TEMP/TMP directory passed all 388 tests. The failure log remains
`private-capture-final-workspace.log`; the complete passing retry is
`private-capture-final-workspace-retry.log`. No production or test assertion was
changed to make that retry pass.

The first combined Android build failed while compressing three stale generated
fixture asset JARs in a reused task-owned build directory. Both Rust ABIs had
compiled. The coordinator moved only those exact three generated files to a
local retained failure directory, then repeated all four Gradle tasks. That
retry and the subsequent audit passed on source `744b722`; the earlier audit of
an old APK is not counted. Logs: `private-capture-gate-android.log`,
`private-capture-gate-android-retry.log`,
`private-capture-gate-apk-audit-retry.log`. Existing Android instrumentation
compiler warnings remain visible. No device/emulator was operated.

Final Rust/native/frontend logs use `private-capture-final-*` under the task's
`m07-context` target. The independent review document records its own source
and checks separately. No UI for private artifact capture, raw export, real
model capture journey, summary maintenance or D06 exit gate is claimed here.
