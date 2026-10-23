# D08.04 desktop fork: independent source review

Date: 2026-10-23. Status: findings and frozen regression sources handed to coordinator; no behavioral acceptance.

## Scope and source

Reviewer `/root/resource_metrics_review` read AGENTS, README, issue workflow, roadmap #3, current #30 claims, the native verification packet, and actual native/frontend integration. Separate branch `review/d08-desktop-fork`, worktree `source-desktop-fork-review`, starts from coordinator `3ed5f771d9cf8450c9bc918f2eede8c1d2b5e50e` on accepted schema-4 main ancestry. Claim #30 `6375853614` preceded edits. Only this new document and two new review-test files are owned; existing production, tests, fixtures and shared contracts are unchanged.

Coordinator source 3ed already contains the original six frozen callback/listener cases from `5a61a7a3fcfd85a7ff4c8a964815a5516dc4933e` and `6fa7d6866e05cbd23b500122dce5df89973a440e`. Those are distinct from this review's nine new cases. All execution of either set is pending at this handoff. The preparing-guard/live-check repair is coordinator-owned, not present in this retained pre-fix review tree.

| Frozen bytes | SHA-256 |
|---|---|
| Pre-fix `ui/fork-controller.ts` | `70988918ebdd57711a9e51ecffa83469cd32d324ddee846d6cda5d1fbebd43d6` |
| `src-tauri/src/fork_commands.rs` | `4aa8c78b60128974115d24dc98bbeb0a5fd884ee386a79b864b8488cea5d8d00` |
| New `ui/fork-independent-review-journeys.ts` | `93b3a32fbd224ea610453e863a1566137cdcc968109aa40d6c9e09f0cb56a150` |
| New `check-fork-independent-review.mjs` | `54f9324f125b91fcef1a964f05433654322c05a9c6185b86f4e81ee5c589b9e6` |

Paths in this report are under `apps/desktop` unless otherwise qualified.

## Concrete findings and frozen oracles

### Operation notification can admit a stale terminal result

In `ForkController.poll`, `this.patch({ operation })` calls subscribers synchronously. A subscriber can switch selection or dispose the owner. The terminal-success path then installs the old `complete/result` without rechecking `live(epoch)`. It can repopulate a replacement/disposed presentation after its cleanup already ran, and call the saved-library refresh for that retired operation. The initial pending-notification guards in 3ed do not cover this later notification.

Commit `35eea9121ef8b4f1a977f1765fee7d241edbd283` freezes two actual-controller/MOCK-IPC cases: an initial valid terminal operation 17 reply and a subscriber that switches selection or disposes when that operation ID is presented. They require one originally authorized start, the notification actually reached, no stale result/completion/consent/busy state, no metadata refresh and no second start. A switched owner retains the exact saved identity only for lookup. Returning a terminal initial snapshot is valid for the existing broker when its worker completes before the start response is consumed.

These are unexecuted source regressions. No RED/GREEN result is claimed by this reviewer. The smallest repair is a live check immediately after operation notification, before any terminal interpretation/presentation or later work.

### Recovery-save barrier must cover every admission control

3ed sets `preparing` around synchronous `saveRecovery`, but only `prepare` checks it. During a second explicit preparation, the callback can synchronously call `confirm` or `lookup` against the prior displayed request, or `restore` a different identity. The outer save is not yet reflected in presentation. Thus it can start old work or publish a competing recovery identity during the save barrier, before the new request is installed.

Commit `14bcf6dc6755b18b1fbd96e9d2c5636d52cd0cb1` freezes three cases, separately exercising nested confirm, lookup and restore during the second save. They require the same presentation object throughout the callback, zero native calls, exactly the two explicit saved IDs, and the final new request prepared with fresh consent still required. This does not ask a frontend guard to replace native authority; it prevents inconsistent local admission during the application's synchronous persistence callback. The proposed narrow repair is to check `preparing` in those three controls too.

### Result notification must fence subsequent metadata work

Both `poll` and `lookup` publish a successful result, synchronously notify subscribers, then refresh the saved library. A result subscriber can switch selection or dispose during notification. The local result variable remains non-null, so 3ed still starts the refresh. There is no need to reject the actual committed outcome or call it rollback; retirement should simply stop further owner work.

The same second commit freezes four cases: confirm-result and lookup-result notifications, each with switch and disposal. The successful reply is valid and reaches the result subscriber; retirement clears result/consent and must prevent the later refresh. Lookup must never issue `fork_start`. The normal production callback is the actual async `Controller.library`; no hypothetical synchronous-throw callback failure is asserted here. Recheck the epoch after result notification/before refresh on both paths.

### Finite continuation audit

| Notification site | Source-only conclusion at 3ed |
|---|---|
| `prepare` prepared/error presentation | No later request/native continuation; source/epoch guards already fence save return |
| `confirm` initial pending | Live check before native call is present |
| `poll` operation | Missing live check before terminal continuation; new two-case oracle |
| `poll` complete/result | Missing live check before refresh; new two-case oracle |
| Running poll after timer | Live check before next status call is present |
| `lookup` initial busy | Live check before native call is present |
| `lookup` complete/result | Missing live check before refresh; new two-case oracle |
| `failure`, `restore`, `setConsent` presentation | No later continuation; restore additionally needs the save-admission barrier above |

Existing initial pending/callback cases and these later sites are complementary. New guards must preserve cancellation, original consent/recovery identity and current-child-head semantics, not replace successful commits with cancellation errors.

## Native and application boundary inspection

No additional concrete native authority defect was found within this finite source pass. This is not runtime verification:

- `fork_commands::request` accepts exactly parent scope, child ID, expected parent revision and fork revision. Parent keys are exact; IDs are 1–64 ASCII characters; revisions are nonnegative integers bounded by JavaScript's safe maximum, with fork revision no greater than expected head. Observer/author/path/SQL/provider fields are not accepted. Host and Store still own actual session/scope, boundary, Busy, immutable retry and canonical validation.
- `fork_start` requires explicit consent, captures the actual `main-*` window lease, obtains the existing Host, and reuses the one existing `ArchiveBroker` worker/registration/operation namespace. It opens no separate Store and selects no child. Successful Host/Store return is not rewritten on a late cancel.
- `fork_lookup` is a separate lease-dispatched read of the existing bounded public Host branch catalog. Missing is only a catalog snapshot, not rollback evidence. Existing child identity checks original parent/fork point; retired child is Closed; current child head is reported. It does not execute a fork, create a session, or grant inspection/author access. Parent-head advancement does not turn lookup into creation.
- Both normal and dev native handler lists register the two closed commands. AppManifest and generated exact permissions match them. The inline capability is in `tauri.conf.json` and restricted to `main-*`; there is no separate `capabilities/main.json` file. The harness module/handler is feature-gated; a listed generated harness permission does not itself install a normal handler.
- Window destruction invalidates the lease synchronously, retires the shared broker, drains it before Host close and prevents reuse until cleanup. Work cancellation checks the epoch. A committed operation can survive loss of its renderer acknowledgment; cleanup is not an erasure or rollback guarantee.
- `main.tsx` blocks competing archive/fork starts while the originating live frontend is busy, protecting its one broker result. If the owner abandons an operation during selection change, its saved fixed identity remains the lookup path. Shared native worker admission independently returns Busy while work is running.
- `ForkPanel` distinguishes selected context/receipt/original scope, the next boundary draft, immutable exact request, consent, pending/uncertain/error/result, and explicit child open. `resumeTimeline` uses the existing controller path. Preparing, confirming or looking up a fork does not auto-select the child or replay downstream turns.
- Recovery storage contains only the four-field fixed identity and is written before dispatch. It is not canonical authority or qualified power-loss storage. Restored/context-changed requests are lookup-only; absence never automatically creates them. No general code/file/shell endpoint or remote debugging server is added.

The native parser and lifecycle conclusions rely on the actual accepted Host/Store interface; this review does not requalify shared fork semantics, author corrections, Core Play 2.4 integration, or cross-platform transfer.

## Evidence attribution and reproduction

The author's `docs/desktop/D08_FORK_NATIVE_VERIFICATION_2026-10-23.md` reports actual source `ed33fd792ba6e6d1a277211c961e078b532c9e88`: 132 assertions, 14 application-owned native WebView images and two actual processes, with sourceDirty=false. It separately records normal native 60-pass/one existing ignore, dev native 64-pass/one ignore plus two harness-contract tests, original fork 63/timeline 83 mocked assertions, strict Clippy and normal-hook exclusion. Counts overlap and are not additive. The author inspected its images; this reviewer neither opened images nor ran an app. That evidence predates coordinator callback changes and does not establish execution of this review's vectors or their pending repair.

The new tests import the production `ForkController` directly; they implement no alternate controller, persistence or canonical evaluator. Their only replies are synthetic closed IPC objects. A coordinator with its existing locked frontend dependencies and an execution slot can run:

```powershell
$env:LOCALLORE_CHECK_OUTPUT_DIR='<own-local-output>'
node apps/desktop/check-fork-independent-review.mjs
```

This command bundles the actual controller and nine review cases with existing esbuild, writes a bounded nine-result report and compiled test module to local artifacts, and fails if any case fails. It does not render a browser/WebView or execute native IPC. Run unchanged on retained pre-fix 3ed and on the frozen repair to establish actual RED/GREEN; preserve both logs. Strict types, existing controller/native suites, normal-hook exclusion and any necessary native UI rerun remain coordinator gates. The new checker is deliberately not inserted into the existing verifier by this review.

Actual reviewer operations were read-only `gh issue view`, `Get-Content`, `rg`, `git show/log/diff/status`, native `git worktree add`, SHA-256 file hashing and document/test-source commits. Git whitespace checks passed. Git is 2.33.0.windows.2; PowerShell is 7.6.5. A read of nonexistent `capabilities/main.json` failed and was corrected by inspecting the actual inline capability; no files were created at that path. No Node, Cargo, Gradle, compiler, browser, native app, model, device, ADB, CUA, desktop control or settings operation was executed for this review.

The review branch retains pre-fix production and nine frozen unrun oracles. Claim release and exact report commit are posted on #30. Next runnable task: coordinator executes unchanged RED, freezes the narrow preparing/live-check fix, then executes unchanged GREEN and the relevant integration gates. Full D08/M08 remain unchecked; no approval score, PR, merge, release, physical-device support or new native acceptance is claimed.
