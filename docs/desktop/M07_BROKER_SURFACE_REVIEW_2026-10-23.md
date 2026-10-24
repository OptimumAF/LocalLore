# M07 broker Archive/Fork surface review — 2026-10-23

Partial #11 M07.01/.03/.04 / #29 D07.02/.06. Coordinator-delegated `desktop_memory_ui`, isolated `review/m07-broker-surfaces` / `source-memory-surface-review`, frozen production **`038dfe9e655040d4cb744ebfcebb7879c045c68d`**. Claims before editing: #11 comment6377259736 / #29 comment6377259954. Own only this NEW report, NEW `ui/broker-surface-review-journeys.ts` and NEW `check-broker-surface-review.mjs`. No existing production/test file is changed. Reviewer authored the original memory gate; this review of coordinator integration does not independently approve that original implementation.

## Exact preceding fix

Source review of038 confirms that public external `observe` cannot establish an unidentified new operation, while private processing of its own awaited start/recovery reply may establish that identity. This addresses the prior frozen pre-acknowledgement finding without ignoring malformed OWN memory admission replies. No further concrete defect was found in that narrow fix. Root reports prior three-case RED2PASS/1FAIL, then038GREEN3PASS and native113 assertions/14 captures; these are **Root-attributed historical executions**, not reviewer tests or final acceptance.

## Remaining semantic-retention findings

The gate strictly decodes memory completions, but its Archive/Fork paths accept any object as a terminal `result`, subject only to the generic envelope. The actual surface controllers have stricter, request-bound validators. Therefore `terminal:true,unknown:false` can be recorded for an outcome the actual owning controller rejects with Wire.

For **Archive**, this is a demonstrated release: `decodeStatus` rejects malformed `{}`; an otherwise valid export preview supplied to an import-preview command also fails the existing command-kind check. `ArchiveController.contextChanged` clears the old error/busy state. The gate's consumption subscription can then mark the semantically malformed terminal consumed, allowing another surface to start. Unknown metadata must remain retained independently of that cleared old presentation.

For **Fork**, the precise behavior differs: `contextChanged` preserves an existing request's `status:uncertain`. It does **not** alone clear the local uncertainty or release the barrier. Nevertheless the gate wrongly reports `unknown:false`, hiding global unresolved metadata and its explicit acknowledgement flow even when the actual controller's existing `outcome(request)` rejects `{}` or a valid-shaped wrong-child result. The frozen cases explicitly preserve this nuance; they do not claim a context-only Fork release.

Both owners can retire their context before an awaited malformed OWN reply arrives. The current owner suppresses obsolete error/result presentation; that suppression must not turn the global malformed outcome into a known consumable result. Separate frozen cases cover Archive and Fork in this order. The mock admission promise is always released before assertions; no held test request is left pending on failure.

## Frozen cases and actual RED

Initial six-case source freeze **`8b9b37173f93bd3a7dc3bc0f7a9165c9c23a0577`** precedes execution. Additive two retired-context cases and final checker freeze **`43ca19c4ac46a6362e53b88d6de3363f7562e79a`** also precede execution. Full journey SHA-256 **`0c344e471e78f69ed77085584577e927cb2bd1ed723c8b299f08a9e064f2e22c`**. Existing source/original7/18/32/63/native5 assertions remain untouched.

Coordinator granted an exclusive **light Node-only** slot after freezing, using the existing reviewed dependency installation through this checkout's ignored junction. Windows x64, actual Node24.22.1 (reported in the retained failure), esbuild0.28.2 (installed package metadata). No package installation/download/update. From `apps/desktop`, with own local `LOCALLORE_CHECK_OUTPUT_DIR`:

```powershell
node check-broker-surface-review.mjs
```

Actual command used the installed absolute Node path under the task's `d09-build-security/node-v24.22.1-win-x64` directory. **Exit1; 8 actual controller/gate mock cases: 2PASS/6FAIL.** The six failures match the six semantic-retention negatives; both complete valid native-shaped positive outcomes pass. They are mocked IPC replies, **not native execution**.

| Frozen case | Actual result |
| --- | --- |
| Archive malformed terminal, then context reset | FAIL: global uncertainty lost |
| Archive valid preview with wrong command kind, then reset | FAIL: global uncertainty lost |
| Fork malformed terminal, then context change | FAIL: global retained uncertainty absent; local uncertainty preserved |
| Fork valid-shaped wrong child, then context change | FAIL: global retained uncertainty absent; local uncertainty preserved |
| Archive context retired before malformed own admission reply | FAIL: global uncertainty absent despite suppressed obsolete presentation |
| Fork context retired before malformed own admission reply | FAIL: global uncertainty absent despite suppressed obsolete presentation |
| Actual ArchiveController accepts full valid-shaped native cancelled result | PASS: own consumption and subsequent explicit start |
| Actual ForkController accepts full valid-shaped exact-child outcome | PASS: own consumption and subsequent explicit start |

Local ignored evidence directory: task `memory-controls-artifacts/surface-review-red-43ca19c`. `checks/broker-surface-review.json` contains all8 actual case results before the checker deliberately fails. `surface-red.log` preserves stdout/stderr and the final assertion; `exit.txt` records1. SHA-256:

- `surface-red.log`: `e5b42ac3595976d2be8e78ef4a05b027e672c48a9aff1760ba0d8c0c83ed4177`.
- `checks/broker-surface-review.json`: `75a64801c5cc0d431c92629fbc24fa5c1973b770990266c0c98594a63203706e`.
- `exit.txt`: `6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b`.

The Node slot was released immediately after this single0.33-second checker process completed; no child process remains. Other actual reviewer checks: source/Git reads, hashes and whitespace PASS. No TypeScript strict suite, other Node suite, Cargo, Gradle, app, native IPC, WebView, image, browser, model, device, desktop-control or protected-resource execution occurred. No PR/merge/settings action. No generated evidence is tracked.

## Narrow correction proposal and next runnable work

Root owns production changes. Reuse `archive-model.decodeStatus` and a **pure request-bound Archive completion helper extracted from the existing controller's checks**, shared by controller and gate. Shape validation alone does not catch the demonstrated valid wrong-kind preview; existing final-import root and final-export hash checks also require the original already validated preview metadata. Root proposed a bounded pre-dispatch binding `{kind,story_id,root_branch,payload_sha256,token?}`: IDs/hash only, no full preview/private prose/path, no new native IPC or persistence. Capture it before dispatch/context retirement so late replies can still be validated. Root must freeze the exact helper DTO/path before editing those existing files.

For Fork, export/reuse the **same existing `outcome(request)` validator** (for example `decodeForkOutcome`), leaving canonical authority in Rust and preserving existing poll/reentrancy behavior. Do not create a duplicate outcome validator. The gate's fixed retained request identifies expected parent/child/boundary. Preserve strict malformed-current/foreign-ID/admission/recovery rules from earlier fixes.

Existing earlier gate/incarnation positive fixtures intentionally used minimal gate-only synthetic results. Root must transparently upgrade their MOCK metadata to complete valid native-shaped envelopes **before the new semantic decoder**, preserving original assertions/history and documenting this fixture correction. These new surface positives already use complete valid-shaped outcomes. Do not weaken semantic validation to accommodate old incomplete fixtures.

Next Root retains this actual RED, freezes the shared helper/binding and existing-validator exception claims, applies narrow corrections, executes these unchanged8 cases to GREEN and reruns relevant original controller/gate/native qualifications. Reviewer claims release at handoff. Full M07/D07/model/device/package gates remain open; this mock RED does not establish native rendering, quality or acceptance.
