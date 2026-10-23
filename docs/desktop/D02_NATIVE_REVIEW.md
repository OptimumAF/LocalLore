# D02 application-owned native evidence boundary

Date: 2026-10-22. Scope: D02.06 development hooks in `src-tauri/src/harness.rs`
under [#23](https://github.com/OptimumAF/LocalLore/issues/23). This is source
review and bounded module verification, not owner acceptance or qualification
of the full shell. The coordinator records integrated journey/render results
separately. Baseline: D01 `77f6d38`, stacked branch `impl/d02-native-harness`.

## Boundary and integration

The module and its app-command registration must be compiled only with Cargo
feature `dev-harness` (off by default). Runtime activation additionally requires
`LOCALLORE_D02_HARNESS=1`. Only the native `main` app window may invoke commands.
There is no server, listener, remote-debug port, desktop capture, injected
input, window activation, arbitrary JavaScript execution or frontend-selected
file path. Normal builds omit the module and command handler registration.
The generated/static ACL names may remain in the manifest: permission names
alone do not register compiled-out handlers. Environment activation alone
cannot add compiled-out commands.

The launcher selects `LOCALLORE_D02_ARTIFACT_DIR`, a fresh absolute leaf beneath
its ignored synthetic artifact parent. The module creates the leaf itself;
an existing file/directory/symlink fails. Fixed allowlisted checkpoint labels
form filenames, and `create_new` forbids overwriting existing artifacts. IPC
cannot select a path or read/write any other file. OS-local processes and the
launcher's chosen artifact parent are trusted; this is not an OS sandbox.

`harness_checkpoint(window, state, label, snapshot)` requires `synthetic:true`
and an unsigned `uiRevision`. The frontend supplies its coherent snapshot of
view, selected session/observer, pending operation, turn status, receipt,
inspection, transcript page, visible error and bounded local error categories.
The coordinator's journey runs must await checkpoint completion before changing
that state. Semantic JSON and capture metadata share the frontend revision;
the PNG is an application render observation, not an independently inferred
canonical engine snapshot. Native engine receipts remain authoritative.

Checkpoint labels are fixed in Rust; each may be used once per process. The
cap is 40 checkpoints (the allowlist is smaller). Pretty JSON is capped at
256 KiB per snapshot/report. Capture output is capped at 16 MiB and must have
the PNG signature. File/COM/transport failures return stable categories, never
OS exception text or local paths. The final report requires `synthetic:true`
and a Boolean `passed`, writes `report.json`, then exits 0/1. A frontend pass
flag alone is not sufficient feature evidence: review the checks and artifacts.

`harness_viewport` permits only this app window's `wide` (1280×900) and `narrow`
(680×900) sizes. It does not show, focus or activate the window. The coordinator
owns hidden creation (`visible(false)`, `focused(false)`), bounded timeout,
synthetic fixtures, fixed close/reopen lifecycle hooks, frontend action/controller
journeys and native IPC/headless receipt comparison. These are integration
requirements, not claims established by the module unit tests below.

## Capture implementation and dependencies

On Windows, Tauri `with_webview` schedules a closure on the application's UI
thread. Its WebView2 controller provides `ICoreWebView2::CapturePreview`, which
writes the app WebView render to an in-memory `IStream`. A completion callback
reads the bounded PNG and returns bytes through a one-shot channel; timeout is
10 seconds. The callback retains its stream until completion. No desktop or
other application's pixels are requested. Failure/timeout still saves semantic
JSON and capture-category metadata. Other platforms report `CaptureUnsupported`.
Hidden-window rendering support must be established by actual runtime artifacts;
it is not inferred from successful compilation. A PNG also needs visual review
for meaningful content. Headless-browser render evidence must be labeled
separately from `native-webview2` capture evidence.

Existing Tauri stays pinned at **2.12.5**. Optional Windows dependencies pin
**webview2-com 0.39.1** (MIT) and **windows 0.62.2** (MIT OR Apache-2.0), matching
the already locked Tauri/Wry transitive versions. The lockfile adds them only
as direct package dependencies; no transitive package version changed. Local
registry source signatures were inspected against the implemented API calls.
These dependencies are enabled by `dev-harness`; Tauri already uses them for
the ordinary Windows host. Existing Tokio 1.54.1 adds its `time` feature for
the capture timeout. Runtime WebView2 remains provided by Windows; these hooks
do not establish offline-installer or runtime redistribution qualification.

Primary sources checked 2026-10-22:
[Tauri `with_webview`](https://docs.rs/tauri/latest/tauri/webview/struct.Webview.html#method.with_webview),
[Microsoft `CapturePreview`](https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/win32/icorewebview2?view=webview2-1.0.3537.50#capturepreview),
[WebView2 Rust bindings/license](https://github.com/wravery/webview2-rs/blob/main/LICENSE),
[Microsoft Windows Rust license](https://github.com/microsoft/windows-rs/blob/master/license-mit).
Microsoft specifies that CapturePreview must run after ContentLoading; here it
is requested by the loaded app's own frontend after render/journey readiness.
Tauri recommends pinning the minor version when using platform WebView handles.

## Module verification

Actually run in the specialist worktree on Windows x64 with the repository's
Rust toolchain:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --test harness_contract
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --test harness_contract -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
git diff --check
```

All four commands exited 0; Clippy reported no warnings. **2 tests passed**.
Checks reject non-synthetic/missing-revision and
oversized JSON; require a fresh output leaf; reject traversal labels and
duplicate labels; refuse overwriting an existing fixed artifact. Test-created
synthetic temporary files are removed. The source file is also a dedicated
Cargo test target; command attributes are disabled only in that standalone test
root to avoid Tauri's exported-command macro reimport collision. The actual app
build/integrated native journeys must verify command registration and permission
handling. These module tests do not launch a WebView, capture a render, compare
native receipts, verify close/reopen, or establish Android/device behavior.

Normal-feature compilation must separately demonstrate omission of harness
commands. App-owned native harness runs, visual review of resulting PNGs,
headless-browser checks and Android compatibility are the coordinator's
remaining integration evidence. No desktop-control tool was used for this module.

## Independent controller/host review during implementation

Reviewed the coordinator's working `ui/controller.ts`, `ui/model.ts`, shared
`host.rs` PlaySnapshot/Mode::Delayed extension, and existing inference/contracts
on 2026-10-22. Findings below describe the inspected working version, not final
PR disposition. Controller SHA-256 at reproduction:
`40762634651dfbda8d4cbba9f943ddc70409d52139b3bcddef07b794080cc018`.
The coordinator owns fixes and integrated regressions. No coordinator source
file was changed by this reviewer.

Three fault-injection cases were actually executed by bundling that controller
and model with the installed esbuild into a temporary Node ES module, then
calling the same Controller actions through synthetic deferred Gateways. The
temporary bundle was removed. This is frontend/controller evidence, not native
IPC, a browser render, or direct-engine evidence.

1. **P1: acknowledgement uncertainty could duplicate effects.** The synthetic
   gateway applied the first commit, then rejected its acknowledgement and the
   follow-up `turn_status` lookup with `Transport`. The controller reported
   `failed` / `Transport` despite one authoritative synthetic commit. `retry()`
   submitted a new ID: `["desktop-1","desktop-2"]`, producing two commits.
   `run()` assigned `unresolved` only after a successful lookup reporting
   ready/running. It must retain the original turn as unresolved before lookup,
   including lookup failure, and block new turn IDs until authoritative outcome
   recovery. Lost submit acknowledgements need the analogous original-turn
   reconciliation rather than assuming submission never happened.
2. **P2: stale recovery errors reached a new session.** After an uncertain
   commit produced a ready lookup, `retry()` started a deferred recovery
   `turn_status`. `attach()` switched to session `b`; its visible error was
   null. Rejecting the old lookup then set session `b`'s error to
   `TransportUnknown`. `recover()` needs epoch/session guards on error and
   nonterminal branches, and recovery promises need serialization/tracking for
   deduplication and disposal. A successful old recovery must likewise be fenced.
3. **P2: same-session snapshot responses could regress revision.** Held a
   revision-0 `refresh()` snapshot reply, then published a second refresh at
   revision 1. Releasing the first reply changed displayed revision from 1 back
   to 0. Session/epoch checks alone do not fence overlapping reads within one
   session. Use a refresh sequence and/or monotonic displayed revision check;
   inspection must stay tied to the winning view revision.

The coordinator already identified property-order-sensitive intent comparison
and cancellation before submit acknowledgement. Review confirmed that receipt
validation should compare the complete typed request structurally (including
version and scope) and events' scope/sequence, rather than JSON property order
or an incomplete fallback. Runtime receipt parsers should reject malformed
shapes as `Wire` without publishing partial status. Do not infer complete wire
validation from a TypeScript cast.

PlaySnapshot source review found the native mutex-protected expected-revision
check and player-context construction appropriate for this bounded fixture;
inventory is filtered by player ownership. Receipts are currently only outcomes
of the player's explicit typed requests. If future NPC/background receipts enter
that collection, their observer transport must be revisited before reuse.
No raw omniscient projection enters this view, and controller request building
does not consume Story Lab inspection. Mode::Delayed uses four 50 ms waits
outside the canonical lock/native UI thread with cancellation checked by the
provider; this is synthetic pending behavior, not real-model latency evidence.

Required final disposition: rerun the three cases as durable coordinator
regressions against fixed source; verify lost-submit and lost-commit recovery,
duplicate Retry, switching/disposal during recovery, and read-response ordering
in the integrated journey suite. These findings remain a request for concrete
fix/test evidence until the coordinator records that disposition.

## Follow-up disposition and integrated evidence inspection

Reread coordinator source after the first native harness run. At that review,
SHA-256 values were:

| File | SHA-256 |
|---|---|
| `ui/controller.ts` | `39fa78797c9ebf845c0411ffff1e202c491f04a7cbea2011472a710818b1b928` |
| `ui/model.ts` | `11253b9752c83c0af8107c1376318bb100d973c20fff37c84a3a55074670ce15` |
| `ui/journeys.ts` | `5296efee401cedcf196095da38cec09892979d339a605cce453f124b5cb9f388` |
| `ui/main.tsx` | `472d17eb3a59bb801d3ca9b116a660175da4f5a8eebb74b08f8a117cfc51e077` |
| `harness.mjs` | `21d5c73c7d5f7008856ec8377de71f96f8c9a563f2881b97abe5c96a4e050d95` |
| `src-tauri/src/main.rs` | `01eeb1699d6d4178e57a6e480207534ea933bf072dc5715c691abe636c30e72a` |
| `src-tauri/src/test_bridge.rs` | `6a824b1dcf059c0ceab6a22a1773a9cba76ab5bc4431944a94705e436a2c18ed` |

The original three findings have concrete fixes in that source: unresolved
ownership is established before submission and retained on transport uncertainty;
recovery is serialized/tracked and guards session/epoch before publishing;
refreshes carry a read sequence and reject lower displayed revisions. Structural
request comparison now covers version/scope/intent independently of JSON order.

Independently read the coordinator's local synthetic native-run `summary.json`,
`report.json` and all 21 per-checkpoint capture metadata records under ignored
`artifacts/native-a550051b-a6d5-45ec-8e5d-c25850190836`. Summary reports 109 distinct
assertions; every capture reports `native-webview2`; final reopened-stage report
passes with no recorded errors. Inspected corresponding `journeys.ts` assertions:
`commit-and-lookup-loss-is-unknown`,
`uncertain-commit-retry-original-id-once`, `lost-submit-ack-is-unknown`,
`lost-submit-reuses-original-key`, `old-read-cannot-regress-revision`,
`recovery-deduplicated`, `old-recovery-error-cannot-publish`,
`native-close-released-sessions-workers`, `reopened-direct-engine-receipt-equality`
and `disposal-native-resources-zero`. The reviewer read existing artifacts and
source; the coordinator executed that native run and visually inspected its
accepted/narrow/200% captures. This follow-up did not rerun native rendering or
use a desktop-control tool. The artifacts predate later fixes; final evidence
must identify the final tested source rather than treating these hashes as it.

The native module, stdio test bridge, command functions and invoke registrations
are all guarded by Cargo `dev-harness`; default registration exposes only
`host_call`. Static generated permission names do not register compiled-out
handlers. Frontend `build.mjs` defines `__DEV_HARNESS__` false by default. Ran an
in-memory esbuild normal bundle using the same entry/defines, without writing
coordinator build artifacts: 248,312 bytes; none of `harness_checkpoint`,
`harness_finish`, `harness_reopen`, `harness_viewport`, `dropCommit` or
`commit-and-lookup-loss-is-unknown` remained. This supports normal frontend hook
elimination; the coordinator still owns the final ordinary Rust build evidence.

The stdio bridge uses only typed synthetic host commands, stats and direct-engine
receipt comparison; it has no socket, path selector, arbitrary evaluation or
shell execution. Input is bounded to 1,024 frames of less than 32,768 bytes,
host payloads to the shared input limit, four preparation workers, 64 oracle
receipts and 256 KiB oracle serialization. Native capture/JSON limits remain
those above. Runner invokes only local build/app processes and its own headless
browser page, with allowlisted local assets and blocked external requests.

Follow-up findings sent to coordinator for final disposition:

- **P2: cancelling recovery could strand the original turn.** Executed another
  temporary-bundle controller case: lose submit acknowledgement; begin Retry
  with a deferred queued lookup; Cancel; release lookup; Retry again. Observed
  `submits:1`, `cancels:0`, `phase:"unknown"`, `pending:null`, `visibleError:null`.
  `recover()`'s cancellation guards returned while retaining a permanently
  cancelled unresolved operation. Native original turn remained queued. Recovery
  must reconcile and publish authoritative cancellation (or a winning commit),
  clear terminal unresolved ownership, and allow the next distinct attempt.
- **Runner timeout cleanup:** the headless success `Promise.race` retained its
  180-second timer, keeping a successful Node process alive until expiration.
  Clear/unref the timer; bound backend close/per-call waits so timeout cleanup
  cannot wait indefinitely. Bind final artifacts to source revision plus dirty
  state/content hashes because integration runs occur before the final commit.
- **Wire robustness:** validate a committed status and complete receipt before
  publishing `turnStatus`; previously subscribers could observe a foreign
  receipt before structural validation threw. `playView` should explicitly
  reject null/malformed nested receipt/event/scope shapes as `Wire`. The trusted
  Rust host currently guarantees those shapes; review did not demonstrate an
  engine observer-isolation breach.

These follow-up observations are source/controller fault-injection findings,
not owner acceptance, a release gate, or evidence that normal operation exposed
private data. Final coordinator evidence must record their disposition.

## Final source follow-up before rerunning integrated evidence

Reviewed the formatted coordinator source with controller SHA-256
`29535e936437a27f82b07cc62f5e1d0fb82e0b68eab9beb9115aad6bc5d3e135`, model
`04fa5aab6a63af4ae85dc5549fbd73609f0e80e6d6c0387fe50692eb9b17c2a4`, journeys
`e5205bd73bccd5ef42503537a8ab76220ec0869f6444b6841f58fee69eddfec3`, and runner
`8ab69b39d9e142f699ddacb24d804c66a7a5cfa6aa0567c9348387915949d303`.

Confirmed source changes resolving the prior follow-up findings:

- `cancel()` reconciles the original native key even without a submit
  acknowledgement; `recover()` applies cancellation intent and publishes the
  authoritative terminal outcome. `publishResult()` clears terminal unresolved
  ownership. Journeys now contain
  `cancel-during-uncertain-recovery-resolves-original` and
  `retry-after-recovery-cancel-not-stuck`.
- Status/request/receipt validation precedes status publication, and play-view
  parsing explicitly rejects null/malformed receipt/event/scope shapes as Wire.
- Headless journey timeout is cleared in `finally`; bridge calls have 15-second
  deadlines and bridge close has a five-second kill fallback. The summary now
  includes SHA-256 input content identifiers. Final source commit and rerun
  results remain coordinator evidence; older 109/112 assertion results do not
  prove the subsequently added cancellation cases ran.
- The standalone command-attribute workaround above is superseded. Cargo's
  `harness_contract` target now points to `tests/harness_contract.rs`, which
  imports the same module in a module context; command attributes remain
  enabled. Main's feature cfg and the test target's required feature retain the
  boundary. This addresses Tauri command macro context in all-target checks.

Two final concrete guard issues were sent to the coordinator before its final
reruns:

1. A terminal branch in `recover()` cleared `unresolved` before
   `publishResult()` validated the recovered receipt. A malformed committed
   reply could therefore throw Wire after ownership was lost; the catch's
   ownership guard would swallow it and a later Retry could allocate a new ID.
   Preserve unresolved ownership until successful validated publication; the
   publication helper already performs that terminal clear.
2. Executed a temporary-bundle controller race: defer preparation reply; await
   `cancel()` publishing authoritative `cancelled`; reject the old preparation
   reply with Transport. Observed `afterCancel:"cancelled"` followed by
   `finalPhase:"unknown",finalError:"TransportUnknown"`. The `run()` catch
   needed the same unresolved-ownership guard as recovery so a stale failure
   cannot overwrite an already validated terminal outcome. The analogous
   winning-commit acknowledgement race must preserve known commitment and
   prevent a new-ID duplicate.

No other concrete defect was identified in this bounded reread. These hashes
identify the reviewed snapshot with those final guard requests still present;
they do not identify final fixed source or establish owner acceptance. Record
the two guards' disposition and fresh integrated regression results before
treating this review as resolved. No desktop-control operation occurred.

## Resolved disposition at final tested source

Read-only final review inspected integration commit
`fa6aea7be2c0e465743f600a3d6db125191cf5db` (implementation `80de9b0` plus accepted
main integration through #34), current controller/journey source, and the
coordinator's final local evidence. No application was launched or controlled
by this review. Current documentation edits do not change the tested input
hashes below.

Both final guard findings are **resolved** in the inspected source and named
regressions:

- Recovery retains `unresolved` through `publishResult()` validation; only
  successfully validated terminal publication clears it. The journeys corrupt
  a recovered committed receipt, subscribe for accidental foreign-scope
  publication, then retry the original turn without an additional submit.
  `malformed-recovered-receipt-never-published` and
  `malformed-recovery-retains-original-id` passed in both final backends.
- The normal run catch now requires both the original current session/epoch
  and `this.unresolved === op`. A completed authoritative cancellation/commit
  therefore fences its late transport failure. Journeys hold preparation or
  commit acknowledgements, publish native cancellation or the winning commit,
  then reject the held reply/lookup. Both
  `late-prepare-error-cannot-replace-authoritative-cancel` and
  `late-transport-error-cannot-replace-authoritative-commit` passed in both final
  backends. The cancellation-during-recovery and subsequent-retry regressions
  also passed.

Inspected final ignored artifact sets:

| Local artifact leaf under `apps/desktop/artifacts/` | Recorded backend | Result |
|---|---|---|
| `native-33387cc5-c1e5-4e6e-a9ef-d91d9bc33c64` | Actual native WebView IPC and WebView2 CapturePreview | PASS; 119 unique assertions, 21 captures |
| `headless-710b5d9a-08a8-4114-9529-6395521154f0` | Headless Chromium rendering and real Rust stdio host | PASS; 119 unique assertions, 21 captures |

A read-only Node artifact audit compared all 18 recorded source/build-input
SHA-256 values (excluding generated `dist/app.js` and executable outputs) with
the current files: **zero mismatches** for both sets. Each summary records the
full final source revision above and `sourceDirty:false`. All 21 PNG files in
each set have a PNG signature; all native capture metadata says
`native-webview2`, and all headless metadata says `headless-chromium`. Both final
reports pass with empty final-stage frontend errors; the headless report also
records zero unexpected requests. The coordinator owns execution/visual QA;
this audit inspected existing results and assertion implementations. It did
not re-execute or claim equality of executable files overwritten by later
builds. Final controller SHA-256 is
`747f19e30261b9d094bec12b85ca40f6335a98c59d528f94178c0e1358340a15`, and final
journeys SHA-256 is
`7621985af10f02fd2998efdf99b4d9af30cc887dc5630cead2c4a90c41f6e2fa`.

All concrete findings raised by this bounded review have a source disposition
and regression evidence. This resolves the review requests; it does not grant
owner acceptance or establish real inference, persistence, physical-device,
installer, screen-reader or other-platform qualification. Normal handlers
remain feature-gated despite inert static ACL names. No desktop input,
activation, desktop screenshot, other-app automation or new native launch was
used in the final review.
