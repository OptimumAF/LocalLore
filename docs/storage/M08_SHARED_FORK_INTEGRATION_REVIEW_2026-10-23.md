# Shared native fork port integration review, 2026-10-23

Refs #12 (M08.01/.02 partial), #30 (D08.04 prerequisite). Independent reviewer
`/root/desktop_runtime_profile`, isolated `review/m08-shared-fork` /
`source-shared-fork-review`. Claims
[#12 6373035125](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6373035125),
[#30 6373035559](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6373035559).
Reviewer owns this new report only; no production or original tests were edited.

Reviewed production `08c5107d72de242d9c37d541396cf4c523703583`, corrected tests
`490972aa6153335644470214aa0fbea4b6a5196d` and author evidence
`3ae0acad4d513f4fcbd800562db89f6f4db254d8`, based on accepted
`b2c03d4151dc6d257f2dbddbb64b13950ddbf41e`. The reviewer did not author this
packet. No concrete correctness or authority blocker was found within the frozen
shared native port. This is not owner acceptance or full M08/D08 qualification.

## Reviewed authority and lifecycle boundaries

The only production additions are the typed request/outcome and synchronous
Host/Persistence seam in `crates/locallore/src/host.rs`, and direct Store mapping
in `crates/locallore-workspace/src/lib.rs`. Also inspected existing Store
`branches.rs`, retention admission, Engine completed-boundary/fork replay,
Host phases, cancel/finish/close paths, and both new test files. AGENTS, current
tickets/claims, README and workflow govern the review.

- `WorkspaceForkRequest` is not deserializable and is absent from `HostCommand`.
  This adds a trusted native Rust operation, not a model/renderer author command.
  The response is a typed serializable version-1 result for a future adapter;
  it does not add a wire capability or arbitrary Store/SQL/path access.
- Host fails closed on poisoned state, missing/closed session and exact
  session-to-parent scope mismatch. It scans all local sessions on that exact
  parent scope for queued/running/ready turns under the same owner lock used for
  gameplay admission/publication. An unrelated scope's active turn does not
  block the fork. Durable persistence is required; the trait default is
  `Unsupported` and no alternate in-memory implementation is introduced.
- The repository maps every request field directly to existing Store
  `ForkRequest` and maps the actual Store result back. Host does not pre-read a
  current/cached parent head and inadvertently reject legitimate existing-child
  recovery. Store still owns completed boundaries, ancestry/cycles/depth/capacity,
  active/retired target admission, transaction rollback and projection replay.
- The expected parent revision guards **new creation**. A retry of the same
  `(story, child branch, parent branch, fork revision)` resolves the immutable
  existing identity and returns its current child head. Parent/child advancement
  and a changed creation-only expected-head guard do not falsely become
  `RetryMismatch`. Changed immutable parent/fork point still rejects. This is
  intentionally different from full-request-byte idempotency.
- Store checks cancellation inside the transaction and commits atomically.
  Host does not check cancellation again after a committed result and falsely
  advertise rollback. No parent Engine/session refresh, child attachment,
  selection, downstream replay or author/observer grant occurs in this method.
  Original inherited receipt and event scopes remain authoritative Rust values.

The typed boundary can be called only by trusted application code. Its normal
API surface does not authenticate the current native window/activity. Keep this
distinction when adding a UI/JNI wrapper; a live Host session is not a fresh
window permission or consent signal.

## Independently executed durable vertical checks

After source review, the coordinator explicitly allocated one portable compiler
slot for the **unchanged seven-case** `fork_host` target only. On this exact
review tree, a fresh task-owned D-drive target and UUID TEMP/TMP were used:

```powershell
$env:CARGO_TARGET_DIR='<task-root>/shared-fork-review-rust'
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:TEMP='<task-root>/shared-fork-review-artifacts/temp-<fresh UUID>'
$env:TMP=$env:TEMP
cargo test --offline --locked -p locallore-workspace --test fork_host --jobs 1 -- --test-threads=1
```

Actual result: **7 passed, 0 failed, 0 ignored, exit 0**; fresh compilation
39.56 seconds, test execution 0.39 seconds. No failed setup/test attempt preceded
this reviewer run. Original test bytes were unchanged:
`fork_host.rs` SHA256
`a42d2ecff9f1388305048520c7d0885b28441056fe792effc5be0e1726c98679`.

The actual shared Host/Repository/SQLite cases verified:

| Journey | Independently observed result |
| --- | --- |
| Completed two-event boundary, inherited original scopes, later parent/sibling exclusion, Mira/Sable isolation | PASS; no child session attachment or parent canonical mutation |
| Pre-cancel and cancellation after child insertion | PASS; rolled back child absent, fixed-ID retry succeeds |
| Stale creation head, mid-receipt boundary, changed immutable child identity | PASS; authoritative rejection, no invalid branch retained |
| Discard actual committed acknowledgment, close/drop/reopen, advance parent and child, retry fixed ID | PASS; current child head returned, no duplicate receipts/canonical mutation; expected guard999 still resolves |
| Queued/ready parent work; unrelated story | PASS; same-parent Busy, independent scope allowed, cancellation then fork succeeds |
| Barrier-held actual Host generation path with synthetic provider | PASS; Running Busy, provider fails without commit, fork succeeds after settlement |
| Missing/closed session, wrong scope, injected JSON command, ephemeral Host | PASS; no new wire/author capability or ephemeral fork |

This execution uses synthetic typed events and one held fake provider, not a
real model, native application, UI, worker process or Android device. Observer
checks use actual Engine character contexts; ordinary Host character/omniscient
inspection remains `Forbidden`. The tests do not grant Lab privileges to pass.

The reviewer also source-read the two narrower Host unit tests: poisoned owner
lock fails before dispatch; minimal Persistence double's committed outcome wins
over late cancellation without a parent-head read. They were **not separately
executed by the reviewer**. The author's evidence reports both included in its
250-test default/all-feature scoped runs plus strict Clippy. Those broader
results remain attributed to the author, not duplicated as independent execution.
The original author compile failure involving opaque Receipt deserialization
remains preserved in `08c5107`/its report; no reviewer failure is invented.

## Required caller semantics and remaining work

These are integration requirements, not newly demonstrated port bugs:

1. Keep the same native child identity through unknown acknowledgment/restart.
   A different child ID can create another valid branch and is not recovery.
   A retry returns current child state, not an exact replay of the first response.
2. `Cancelled` does not prove a fixed child is absent from an **earlier**
   committed/lost-ack invocation. The cancellation check can precede the
   existing-child lookup. Resolve that identity through a later uncancelled
   retry/read before offering rollback/absence claims or creating a new identity.
3. The cancel callback executes while Host state and potentially the Store
   transaction are held. Use a short, non-reentrant atomic/cancellation signal;
   never call Host/Store/UI or wait on another action from it. Run the synchronous
   operation on the native I/O lane, with independent finite ownership/drain.
   A callback panic is treated as cancellation by the actual Store checks; this
   review does not extend that guarantee to arbitrary Persistence implementations.
4. Terminal cancellation can precede completion of a provider's cleanup. Such
   terminal workers may still drain although they are no longer active
   queued/running/ready turns; their existing cancellation/publication fences
   prevent committing canon. Do not infer zero workers or completed model cleanup
   from fork admission. Parent/child generation ownership remains the runtime
   manager's separate responsibility.
5. Session IDs are process-local and may be reused after restart. Native window/
   activity epoch and exact selected-scope/revision fences must protect admission
   and visible acknowledgment. Replacing or retiring a window must not make old
   replies select a child or imply author permission. No such adapter is supplied
   by this packet.

The author says accepted main advanced to tests/docs-only `e534f01` after its
base. Reviewer read-only `git diff b2c03d4..e534` on both production files is empty.
That does not make this run a test of the newer full main: results are bound to
the frozen review tree. Root still owns current-main reconciliation, schema4/
Store integration, native desktop/JNI callers and their platform verification.
No additional regression file was necessary for a concrete new failure here.

## Evidence and exact scope

Local `shared-fork-review-artifacts/fork-host-independent.log` SHA256:
`66b413df6ff4bbb863797449d66d6492c1891daf582ff598a2ac9184e48e2ddd`.
No private story/model data is in this log; machine paths stay local. Raw output,
fresh target and UUID task TEMP remain task-owned outside Git.

Actually queried environment: Windows 10.0.26300 x64, rustc1.93.1
`01f6ddf75 2026-02-11`, Cargo1.93.1 `083ac5135 2025-12-15`.
`git diff b2c03d4..3ae0acad --check` and this report's `git diff --check` PASS.
No extra full suite, Clippy, Android ABI, native app/UI, real-model/worker,
device/ADB, CUA/desktop, protected resource, setting, dependency download,
PR/merge or release action occurred. The compiler slot was released after the
single successful target; no reviewer heavy process remains.

Next runnable task: coordinator integrates/reviews this focused port, then wires
explicit fixed-ID native fork/recovery with epoch fences and actual UI/platform
tests. Rewind/edit/author corrections, automatic downstream replay and full
M08/D08 exit gates remain unimplemented/unaccepted by this slice.
