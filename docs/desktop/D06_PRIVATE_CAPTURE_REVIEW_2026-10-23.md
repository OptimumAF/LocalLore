# D06 private capture: independent review — 2026-10-23

Reviewed frozen implementation `8c42188e045f9bfb2275eac1c496d3a360bf33a6`.
Reviewer `/root/app_storage_review`, isolated `review/d06-private-capture`;
claim #28 comment 6362012542. Owned only this report and new
`crates/locallore/tests/turn_capture_review.rs` (`dabc6dd`). No production edit.

The issue IDs are D06.01/.02/.03/.06/.07 **partial**. D06.04 maintenance and .05
pause/replay are not implemented by this capture slice. Capture UI, private
export preview and full D06 acceptance remain separate gates. The reviewer did
not author this implementation; earlier query/intent/fork/archive contributions
are distinct foundations, not claimed independently reviewed here.

## Findings at the frozen source

**P2 — default feature strict Clippy fails.** `turn_trace.rs:248` defines
`TraceOwner::retire`, but production calls exist only under the Host feature.
Actual default/non-Host Clippy of the new review target fails `-D dead-code`;
all-feature Clippy passes. Gate the method for Host/tests or apply equivalent
narrow feature hygiene. Default tests still pass with the warning. The reviewer
has not changed the production source to hide it.

**P2 — teardown retirement misses poisoned State when trace is busy.**
`Host::close_all` at `host.rs:460` traverses/retire owners only if `state.lock()`
returns Ok. If State is poisoned and the trace mutex is also held, it neither
retires owners nor disables/clears the ring. A later callback can therefore
remain authorized by the still-live owner after this teardown call. The existing
unit covers a busy trace lock with healthy State, not this combination. Suggested
private unit: retain a session owner, poison State in a caught synthetic panic,
hold trace, invoke close_all and assert owner.live() is false. Recovering the
poisoned guard only to retire/cancel/clear is cleanup, not gameplay recovery.

This second finding follows the actual branch condition; the reviewer cannot
access Host's private locks from the assigned integration test and has not
executed that private repro. Host wire access itself fails closed after State
poisoning, so this is a lifecycle/retention gap, not demonstrated wire disclosure.
Both findings were sent to the coordinator before report completion. Their
correction/disposition is pending in this initial frozen-source report.

## Production authority and privacy observations

Play hooks borrow the actual selected ContextPackage, provider GenerationRequest,
returned bytes, parsed Proposal, validated plan and final prepared candidate.
They do not construct a second context builder or commit path. Captured plan and
candidate kinds explicitly say `not_durable_commit`; their contents cannot
establish storage acceptance. Metadata remains separate from private artifacts.

The request copy carries exact structured prompt/schema data, a bounded profile
identifier and generation budgets, without adding model paths/provider errors.
Raw UTF-8 is retained as data; invalid UTF-8 uses exact hex plus source-byte hash.
This is private material that can include original input/spoilers/personal text,
not a redacted Player export or safe material for automatic issue upload.

Capture is disabled by default and requires explicit local consent at the Host
boundary, plus trusted native Story Lab construction. JSON cannot grant Story
Lab. Reads enforce live session/scope/current head and exact captured base,
Player observer, turn and u32 attempt; generic ring reads additionally require a
Story Lab Reader and opaque owner identity. The trusted native Reader constructor
is a caller boundary, not cryptographic authentication. A grant never enters
character generation or changes canonical knowledge.

Consent is one owner/scope namespace per ring. Clear/reconfigure rotates the
detail epoch; old handles do not backfill after new consent. Closing retires the
owner even if the diagnostic lock is busy on the normal path. Model unload must
preserve the session and its consent: it cancels FreeText work but does not retire
the owner. The new independent actual-Host test verifies read and fresh generation
after unload, then closed-session refusal.

Production RingSink uses nonblocking try_lock. Serialization/budget failure drops
a complete artifact and marks truncation; callback panic deactivates the sink.
Trace-side overhead is tracked separately from gameplay deadline accounting.
Busy lock drops can leave Recorded status with missing artifacts, so
`exact_reconstruction=false` is essential and is tested. Do not present Recorded
as a complete exact attempt. Director stage wall-clock measurement can include
request-capture overhead even though gameplay accounting excludes it; no new
pure-inference timing or performance claim is inferred here.

## What the bounds actually mean

The limits count serialized **retained artifact** bytes: 49,152 per artifact,
196,608 per attempt, 524,288 across at most three attempts and 16 artifacts per
attempt. They are per CaptureStore/TraceRing (normally one Host/window), not a
process-wide cap across every Host instance. Identity/wrapper/metadata bytes are
not included in that private artifact sum; Host independently caps whole replies.

These are not heap/RSS limits. Values are retained as a serde_json tree; serializer
buffers and detached read clones add transient allocations, and object allocation
overhead can exceed encoded length. Limited serialization bounds typed copies;
raw-output input is bounded before its copy, but JSON escaping may expand it and
cause whole-artifact rejection. The independent test covers that expansion.

Ten-minute expiration is checked on access/begin/record, not a background deletion
timer. Outstanding detached copies, OS paging and forensic zeroization are outside
this deletion guarantee. Private artifacts are process-local; there is no new
file writer/upload path. The storage archive has no reference to this ring, so
normal archive behavior does not acquire capture data through this change.

## Reviewer execution

Windows; Rust/Cargo 1.93.1; locked/offline; own
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/d06-private-capture-review`
target and task TEMP/TMP, debug 0/incremental off. Explicit deterministic fake
providers only. No models, devices, app/CUA, settings or protected resources.
The review was interrupted to repair the separately demonstrated staging-sidecar
blocker, then resumed without changing D06 production source.

Executed at frozen source plus the new test file:

```text
cargo +1.93.1 test -p locallore --all-features --test turn_capture --test turn_capture_host --test turn_capture_review --locked --offline --target-dir <own-target>
5 + 1 + 4 passed; 0 failed.
cargo +1.93.1 test -p locallore --lib --all-features --locked --offline --target-dir <own-target> capture -- --nocapture
5 passed (four capture-module cases and existing busy-close/unload unit).
cargo +1.93.1 test -p locallore --test turn_capture_review --locked --offline --target-dir <own-target>
3 passed; retire dead-code warning.
cargo +1.93.1 clippy -p locallore --test turn_capture_review --all-features --locked --offline --target-dir <own-target> -- -D warnings
PASS
cargo +1.93.1 clippy -p locallore --test turn_capture_review --locked --offline --target-dir <own-target> -- -D warnings
FAIL: retire is unused without Host.
cargo +1.93.1 fmt --all -- --check
PASS
git diff --check
PASS
```

New independent cases prove escaped-byte budget rejection with exact binary copy;
consent rotation, same identity reuse after metadata eviction and cross-ring
handle isolation; a deliberately busy actual request-capture hook preserving
actual provider prompts/canonical result while honestly losing an artifact; and
actual Host model unload/session continuation/capture read/close behavior. Only
nondeterministic accepted StageTiming elapsed_ms values are normalized when
comparing receipts. Canonical state and actual prompt/schema data are compared
without normalization. Existing tests additionally execute TTL, count/byte caps,
panic/cancellation, repairs/rejection and Host consent/selection guards.

Local logs: `capture-review-first.log`, `capture-review-production-tests.log`,
`capture-review-unit-tests.log`, `capture-review-default-tests.log`,
`capture-review-clippy.log`, `capture-review-default-clippy.log`.

## Frozen bytes and remaining gates

| File under crates/locallore/ | SHA-256 |
| --- | --- |
| src/turn_capture.rs | `4522814d02281639220505b3865340027aebc4e3383746224d7f944f13b22a98` |
| src/turn_trace.rs | `373338aede1d95c9b7d858de9bfc599dcf6bc8927642015d92b0fc8dcb1d692c` |
| src/play.rs | `2a9e3757d2642abb66c4e35d70a4493ed8fc313bad7102d1c650c2c9dc67c75d` |
| src/host.rs | `cef0117f7550b7bf46dce79a35c48242ed6b6778bceb3b5d132700838218d365` |
| tests/turn_capture_review.rs | `e35665b8d631915c0ef0dc3b34ab4287ef202de9d5d2cb745b65674d900457a3` |

Next: coordinator correction/disposition of the two findings, source-bound
regression and platform compatibility, then separately claimed capture UI and
exact private export consent/preview. No independent favorable score, human
acceptance, pause/maintenance, full-reconstruction or full D06 gate is claimed.
