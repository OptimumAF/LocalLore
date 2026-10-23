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
