# M07 desktop broker-retention coordinator-diff review — 2026-10-23

Partial #11 M07.01/.03/.04 / #29 D07.02/.06; source-only review by coordinator-delegated `desktop_memory_ui`. Frozen reviewed source **`06b3746c1774d9c7b6ae3fd1b5b8a750f9ffb98f`**, isolated `review/m07-broker-retention` / `source-memory-gate-review`. Claims before edits: #11 comment6376959163 / #29 comment6376959426. Own only NEW review journey, checker and this report. Root owns all production changes and qualification. The reviewer previously authored the initial gate and memory packet: this review concerns coordinator changes and is **not independent approval of that original implementation**.

Read the actual current strict decoder reuse, consumption latch, existing seven coordinator review cases, eighteen original pure-gate assertions, thirty-two callback assertions, original memory controller and main's subscriptions/start/recovery/late status routing. No existing source or test was edited. Two concrete source findings require coordinator correction; no actual RED/GREEN is claimed here.

## F1 — late known foreign operation poisons current certainty

In `ui/broker-retention.ts`, `observe` invokes the current memory operation's strict `decodeMemoryOperation` before excluding a different known operation ID. A legitimate delayed native `archive_status` or `archive_cancel` response for retired operation1 can arrive after operation2 has completed and been consumed. `main.tsx` routes those responses through the same `observe`. The decoder correctly rejects the old operation ID against2, but its catch incorrectly marks **operation2 unknown**. The already known saved result becomes an unresolved global barrier; subsequent starts require unnecessary recovery or explicit unresolved acknowledgement.

Reject a known foreign ID before applying a current-operation decoder result or uncertainty mutation. Keep strict closed decoding for the actual current operation. An invalid current payload must still remain unknown across context changes; the existing four malformed-current coordinator oracles remain unchanged. The original foreign-ID pure oracle only checks retained ID/terminal, so it did not detect the new uncertainty mutation.

NEW frozen vector `late-known-old-id-cannot-poison-current-consumed-memory-outcome` uses two full valid memory Status results, then delivers the valid old result. It requires the entire current retention snapshot (identity, operation, certainty and consumption) to remain unchanged, and a subsequent explicit second-surface start to be admitted. No native broker/fork result semantics are simulated as evidence; that second result is explicitly gate-only mocked transport.

## F2 — new passive recovery inherits previous consumption latch

`recoverMemory` announces `{inFlight:true,recoveringMemory:true}` and registers a new passive broker operation without resetting `consumed`. The previous latch can already be true. A concrete existing caller path is Status1 consumed, then a pending-gameplay refusal of Admit **before native broker admission**: actual `MemoryMaintenanceController` becomes uncertain while the gate still retains consumed Status1. Explicit Status recovery creates Status2. It must consume Status2 independently.

On current source, the inherited true latch survives Status2's pending and terminal notifications. A synchronous gate subscriber can start a second surface while the actual memory controller is still busy decoding/accepting Status2. Main's `fork_start` lacks the separate memory-busy frontend guard used by archive starts, so the shared gate must retain this boundary itself. The native broker still owns canonical safety; this defect concerns result-retention and stale/cross-surface presentation guarantees.

Reset consumption for the new operation **before its pending notification**, retaining the original fixed recovery identity and uncertainty protocol. Latch the new result only after its own actual controller acceptance. Preserve the coordinator's seventh positive oracle: a consumed prior result must still allow the next explicitly requested action once this independent new consumption occurs.

NEW frozen vector `new-passive-recovery-must-consume-its-own-outcome-before-crosssurface-start` uses the actual memory controller and a mock invocation implementing the existing main-wrapper pre-admission Busy branch. It records consumption on recovery-pending notifications, attempts a second-surface start at Status2 terminal delivery while the controller remains busy, requires Busy/no dispatch, then proves explicit admission after actual controller acceptance. It changes no original production or oracle.

## Frozen evidence and pending commands

NEW source/checker freeze **`d532c43d06e58bf6607180d589c6f55e506437b4`**:

- `apps/desktop/ui/broker-retention-incarnation-review-journeys.ts` SHA-256 `5ad8f6effc4f38a03f9f2bdb3a5e6c9aef89043ef4cafec04bca83471c40abda`.
- `apps/desktop/check-broker-retention-incarnation-review.mjs` runs both cases, writes a bounded case/result report to the existing ignored local output directory, then fails if any case fails.

Actual reviewer checks: source/Git/ticket reads, SHA-256 and `git diff --check` PASS. Both new cases are **UNCOMPILED/UNRUN**. No Node, Cargo, Gradle, application, native IPC, WebView, images, browser, model, device, desktop control, protected-resource, download, PR or merge execution occurred. No new runtime/version is inferred. Root reported the latest prior native cohort113 assertions/14 images; that attribution does not test these new vectors or establish final acceptance.

After Root assigns its exclusive resource slot, from `apps/desktop`, using the existing reviewed Node/dependency installation and own `LOCALLORE_CHECK_OUTPUT_DIR`:

```powershell
node check-broker-retention-incarnation-review.mjs
```

That is a pending command, not an executed result. Root should first retain actual RED against frozen06b3746 plus these new files, then run the same unchanged vectors against narrow production corrections. Re-run unchanged7/18/32/63/frontend strict checks and actual native journeys as warranted. Keep every failure and distinguish mock-controller evidence from actual native execution. Existing controller/gate source, seven prior coordinator cases and original eighteen/thirty-two/sixty-three/five-native test bodies remain untouched here.

Reviewer claims release on source handoff. Root owns correction, actual evidence, final source reconciliation and PR/acceptance. No full M07/D07 or native/model/device/package gate is completed by this review.

## Follow-up exact-fix review and F3 — before a new start acknowledgement

Root reports actual unchanged first-two RED at `484b832` (0PASS/2FAIL, local incarnation-red log/JSON retained) and GREEN at **`085a72abca802339a2bccdb8959bddfa99b7ecfc`** (2PASS/0FAIL), plus unchanged7/18/32/63/full frontend checks. These are **Root-attributed executions**, not reviewer runs. Source review of that exact production diff confirms F1 now excludes a valid different known operation ID before decoding against the current identity, and F2 resets `consumed:false` before recovery's pending notification. The original strict decoder and its malformed-current cases remain. These findings' narrow corrections are consistent with their frozen oracles; this is not blanket acceptance or independent approval of the original gate.

The exact-fix review found **F3**, a distinct pre-acknowledgement gap. A new `start` resets the reservation to `operation:null,inFlight:true`, then awaits its own native start reply. During that await, a legitimate late external status/cancel result for the previous operation can enter public `observe` through main's existing routing. Since there is no current known ID yet, the old full valid same-context Status1 is adopted as the new reservation's ID/terminal outcome. The actual awaited Start2 reply then meets the new known-foreign-ID filter and is ignored by the gate. The actual memory controller independently accepts running operation2, while the gate can latch the old terminal1 as consumed. Once native operation2 finishes, a cross-surface fork may overwrite its still-unconsumed result. This violates result-retention; canonical safety remains Rust/native-broker authoritative.

Root's proposed correction separates **private processing of the operation's own awaited admission/recovery reply** from **public external status observation restricted to an already known matching operation ID**. An old external response must never establish a new unidentified reservation's operation. Do not silently ignore malformed OWN admission replies or add a general current-operation endpoint. Root owns the actual production implementation and qualification.

Claim extension before edits: #11 comment6377167689 / #29 comment6377167857. Reviewer first merged Root085 as coordinator-authored baseline (`c1c98b3`). Git's two add/add conflicts were only the reviewer's NEW test/checker versus Root's formatted versions; resolution took **exact Root085 versions**, preserving the first-two behavioral oracles. No production source was manually edited by the reviewer.

Additive third source/checker freeze **`25b0d24aa140555cf7480061c886f4124a651dfa`**, same two NEW test paths; full journey SHA-256 **`9f3efcf814d1be5c70af5579286f3a9276be6b943a67e5fe7245241e50bda0e9`**. Existing first-two case bodies are unchanged from Root085, checker expected case count becomes3. New case `late-old-status-cannot-adopt-new-unacknowledged-start-operation` uses the actual memory controller, a held mock Start2 reply, and a full valid late external Status1. It requires the reservation remain unidentified/nonterminal, then tracks the actual running2 acknowledgement, blocks a second-surface start, observes/consumes exact terminal2 without restart and permits a subsequent explicit fork. The held mock promise is always released **before any behavioral assertion**, including on broken source, so failure does not leave a pending fixture request.

The third case is **UNCOMPILED/UNRUN by the reviewer**. Actual reviewer follow-up remains source/Git/hash/whitespace only. No Node/Cargo/Gradle/app/native/render/model/device/desktop/protected-resource execution or production edit occurred. Root should retain actual third-case RED on085, apply the narrow private-admission/known-status fix, rerun all three unchanged cases and existing regressions/current native qualification. Earlier successful native cohorts become historical source-attributed evidence once production changes; no completion is inferred here. Claims release again at handoff; full M07/D07 remains open.
