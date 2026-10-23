# M07 borrowed observer-event port and cancellation fixture source review

Refs #11 M07.01/.03/.04 prerequisites. Reviewer claim
[6358904442](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6358904442),
coordinator port claim6358857260. This is a bounded independent **source review**,
not a test execution, full M07 acceptance, performance measurement or release
recommendation. This reviewer did not implement the port or runtime fixture fix.
The reviewer previously authored the finite intent/query modules and D09 packet;
this report does not independently approve those implementations.

## Reviewed source and method

The port is coordinator commit **`dcb6b5a3f756ef0198663ef5bc394023a5aaa1c0`**,
branch impl/m07-observer-event-port, based on accepted main32173cb. Its complete
production diff is `engine.rs`: the borrowed visit method and extraction of the
unchanged lineage/witness predicate for reuse by `character_context`. Its other
file is the new three-case `tests/actor_observations.rs`. The review branch
review/m07-event-port starts at this commit and adds only this document.

The separate runtime test correction is
**`2c0c293323fa19b17ecdf8f04a3247e46ba4ccf1`** in source-context. The root checkout
advanced to documentation commit3de844a during review; this report pins the
reviewed runtime delta to2c0c293, not an unpinned moving working tree. The reviewer
read that checkout without copying or committing its implementation.

Actually performed: read Git status/history/diffs, Engine construction/head/fork/
receipt/context methods, Lineage eligibility/fork bounds, all new test sources,
runtime adapter lifecycle/test setup, ordinary protocol fixture, Cargo feature/bin
declarations and the old blocked-stdin test/fixture path. Compared before/after
runtime changes and computed file hashes. No compiler/test, model/worker/app,
device/browser/desktop/CUA, process control, network-policy or protected-chat
operation was performed. No root source or active writer's file was edited.

## Port findings

**No concrete blocking defect was found in this source review.** The method is a
native borrowed read port, not a new inspector, search, memory or wire authority.

1. **Binding fails before callbacks.** Scope must equal `self.scope` (both story
   and branch), revision must equal the current canonical completed head, the
   observer must exist, and `after <= through <= revision`. Failure returns the
   existing typed Scope/Stale/UnknownReference/Rule error before any visitor.
   Historical projection reconstruction is not claimed. The range is an event
   interval `(after, through]`; partial-turn interval endpoints do not turn the
   current projection into a historical one.
2. **Privacy/time/lineage precede materialization.** The loop tests the range and
   shared `actor_event_eligible` before handing out `&AcceptedEvent`. The helper
   is exactly the former context predicate: `lineage.eligible(scope, revision,
   event.scope, event.sequence) && witnesses.contains(observer)`. No alternate
   observer rule, caller-supplied eligibility flag, hidden record, excluded count,
   raw receipt/proposal or search corpus is handed to the visitor. Character
   context still clones its eligible observations as before; its rule is unchanged.
3. **Fork/time behavior remains centralized.** Lineage rejects other stories,
   unknown branches/zero sequences, caps each inherited branch at its fork point,
   tracks cycles and bounds ancestry traversal to32. Explicit fork construction
   already refuses deeper ancestry. The port uses that same implementation,
   rather than independently approximating ancestor membership with a branch name.
4. **Borrowed/nonmutating traversal.** The Engine receiver is immutable and
   traversal borrows existing accepted events in receipt order; it does not clone
   the entire history or mutate projection/receipts/lineage. It constructs no
   fallback memory or derived canonical state. Visitor/cancellation closures can
   mutate their own caller-owned state; the port does not publish it anywhere.
5. **Cooperative cancellation includes excluded history.** Initial cancellation
   is checked after binding; the scan polls at index0 and every32 scanned events,
   before every eligible callback, and after a complete scan. Thus a long run of
   hidden/out-of-range events does not suppress cancellation checks. A false
   visitor explicitly stops normally with Ok, before the final cancellation check.

Contract limits to preserve in consumers:

- Cancellation can return after earlier eligible callbacks. A consumer accumulating
  a prepared packet must discard/reject partial accumulation on Err and separately
  fence publication against current source/head. The read port is not a transactional
  callback rollback or derived-cache publication authority.
- This is still **O(total accepted events)** and the cancellation closure/visitor
  execute caller code. Every32 scans is a polling bound, not a measured wall-clock
  bound, hard real-time guarantee or constant-time secrecy promise. Native callers
  are trusted; they already have Engine receipt/state APIs. Do not serialize poll
  counts/timing or treat this port as isolation from hostile native code.
- Actor selection remains the trusted caller's responsibility. There is no Lab
  grant/new renderer command here; consumers must bind the intended observer and
  retain the existing authorization/lens restrictions before invoking it.

The new tests are meaningful finite source cases: complete equality with existing
character contexts for player/Mira/Sable on parent and fork, explicit invisible
Sable and forked Mira expectations, unchanged canonical bytes/receipts, rejected
binding with zero callback delivery, exact/exclusive/empty range endpoints,
single-callback false early stop, pre-cancel and cancellation during100 hidden
events. The three tests do not exhaust sibling/deep-ancestry, every cancellation
boundary, empty-history, after-some-visible-callback or maximal-scale cases; no
claim of such execution or proof is made. Existing Lineage/contract tests remain
the complementary central eligibility coverage.

Integration note: the port base predates the separate M07 context/fork replay
correction. Preserve source-context's private `commit_recorded` replay/fork path
and its v2.1 fixture tests when combining this method; applying this narrow port
does not justify replacing the newer Engine with its older baseline wholesale.
No schema/storage/Host/app capability change is required by this port itself.

## Runtime test correction findings

The adapter's changes are confined to its existing
`#[cfg(all(test, feature = "development-worker"))]` module. Production compile,
provider identity, inference, cancellation, child drain and fail behavior are
unchanged. `protocol-fixture` remains an explicit development-worker-required
binary, distinct from the packaged C++ worker. The fix does not change its hash,
staging, model/role policies or production wire protocol.

The old cancellation test started a role then slept30ms. Under scheduling delay,
cancellation could precede native generation; production legitimately preserves
a loaded owner on that path. The assertion expecting Failed/reaped was then about
a different state from the one exercised. New mode `blocked-generation-observed`
still answers/flushed the load request, but only creates its unique fixture-local
`generation-started` marker **after parsing an actual `op=generate` frame**. It
then blocks without a generation response. The test waits for that marker before
cancelling. File existence is enough for this ordering: marker creation itself
occurs after frame parsing, even if the test observes it before the marker write
finishes. Per-process sequential fixture directories reject collisions rather
than reusing an old marker; no private model or shared path is involved.

This is an out-of-band synthetic test acknowledgment, not an extra protocol
reply. The fixture still consumes cancel frames without emitting an ack. The
test retains prompt-poll (<50ms), bounded drain (<4s), Failed status and exact
child `try_wait` assertions; its marker wait is bounded at5s. These finite timing
thresholds remain scheduler/environment-sensitive checks, not production latency
qualification, but eliminate the incorrect assumption that30ms proves dispatch.

Importantly, old mode **`blocked-generation` is unchanged**: it sends/flushed the
initial load reply and then sleeps before reading another line. Existing
`blocked_stdin_writer_is_released_by_owned_child_reap` still uses that mode and a
30,000-character generation prompt, asserting Cleanup and bounded return. Moving
that old mode's sleep after generate would weaken its pipe-writer coverage; this
patch adds a separate mode instead. No cancellation/reap assertion was removed.

## Exact files and execution attribution

SHA256 values below identify reviewed working-tree bytes; Git commits identify
canonical source history (line-ending normalization can change byte hashes).

| Source | SHA256 |
|---|---|
| Port `crates/locallore/src/engine.rs` | `5ef7d38c4543f58922b0e8f8b7d37cfd2388314361b5e743f9af5ecba9cd5e85` |
| Port `crates/locallore/tests/actor_observations.rs` | `404d9774c8155fe385ddcef0c6a8b6a9ef9ddd0062fcdb2caef259186ca609de` |
| Existing `crates/locallore/src/scope.rs` | `191337033061d0dfeefc3c8495c9ae3801f63d427260d38d8a3f05e6d50d4570` |
| Runtime2c0c293 `src/adapter.rs` | `11c6736fe82743d772c9158abbdb52ec23148413b1acb9a634cec9bf9c2879c9` |
| Runtime2c0c293 `src/bin/protocol_fixture.rs` | `6b17b4ed3eb9f7e8edbb50d19629c0ed6238c3444476df6ce8996653629f03c2` |
| Unchanged runtime `src/lib.rs` | `eb017282cea79973c31922136dc36ca7c88b771c512b80efe0ed898379550ff6` |
| Runtime Cargo.toml development-bin gate | `e39122e22dc004b0904fdd5f2bdbb40207403f62fbd816eec7f1ab5023961014` |

The coordinator reports29 focused port/contract passes (3new+26contracts), strict
locallore all-target Clippy/fmt; and runtime23passes/1ignored plus the separately
explicit ignored case passed, strict Clippy/fmt. Those executions were **not
rerun by this reviewer** and are coordinator-attributed results, not reviewer
execution evidence. The reviewer inspected the assertions/control flow, not a
real inference or derived-memory production run.

Disposition: return this source report to the coordinator for integration review.
Full M07/derived-summary/maintenance/FTS/long-history/model/offline/device gates
remain unchecked. Next consumer validation should include partial-callback cancel
discard, current-source/head publication fencing, paired hidden histories and
large-history responsiveness using the actual derived-cache implementation. No
implementation edit, PR, merge, release, model/device or owner acceptance is
performed by this report.

Follow-up source read: coordinator documentation-only
`3cb807fb0e4171790dac87698884d519e40a1134` adds M07_BORROWED_OBSERVATIONS.md.
Its explicit partial-cancellation discard, native caller authorization and
O(total-history)/nonconstant-time limits match the contract above. Git diff confirms
no Engine/test behavior change fromdcb6b5a; this follow-up does not add reviewer
test execution or extend acceptance to the derived-memory consumer.
