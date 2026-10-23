# D02 desktop shell verification — 2026-10-22

Scope: [#23](https://github.com/OptimumAF/LocalLore/issues/23), D02.01–D02.06,
under [#21](https://github.com/OptimumAF/LocalLore/issues/21). Implemented and
locally verified for owner review; acceptance/checklists remain with the owner.
No repository PR was merged, release published or setting changed by this work.

Implementation commit `80de9b0`; final integrated test source
**`fa6aea7be2c0e465743f600a3d6db125191cf5db`**, branch `impl/d02-desktop-shell`.
This incorporates accepted main `2c095ea` (#32/#33/#34) without changing their
implementation. D01 is accepted upstream; D02 therefore targets main directly.
Later handoff commits change documentation only. Exact PR is linked on #23.

## Delivered behavior and acceptance evidence

| Task | Implemented / observed evidence |
|---|---|
| D02.01 | Pinned React/TypeScript local bundle and Tauri Windows executable. `npm ci`, normal build and native build succeed. Embedded assets; no dev server, runtime CDN, account, API key or model download. Only Windows x64 tested. |
| D02.02 | Sidebar with up to four independent fixture sessions, central finalized-receipt transcript, collapsible inspector and compact scope/revision/provider/turn/error state. Play and explicit spoiler-bearing Story Lab. Persistent fake/in-memory labels and honest unavailable generation/model/library/export/author controls. Native accepted/narrow/enlarged captures inspected. |
| D02.03 | Actual frontend controller → native IPC → shared host/engine. Live give/wait/ability/dialogue; accepted, preflight rejected, provider rejected/malformed/failed/cancelled states. Transcript derives from finalized Rust receipts, never draft generation. Request/events and authoritative player-snapshot differences inspectable. Direct-engine full receipt equality passes before and after native reopen. |
| D02.04 | Submit/retry deduplication, original scoped key retained through lost acknowledgements, lookup before recovery, full request validation before receipt publication. Session/operation/observer/read epochs and monotonic revisions fence stale replies. Native prepare runs outside UI/canonical lock; controls bypass worker permits. Cancel/reset/switch/close/reopen/dispose cases pass, with native sessions/workers zero after teardown. Drafts isolated per session. |
| D02.05 | Labeled native controls, skip link, visible focus, pane-width controls, 100–200% text, inspector collapse and receipt pagination (12 DOM rows). Shared Enter/Shift+Enter/IME policy checked. Rendered widths/collapse/narrow overflow checked. Hostile HTML/script/URL dialogue remains inert. Copy uses explicit selected-receipt sink; no user clipboard changed during verification. Actual keyboard injection/screen-reader audit not performed. |
| D02.06 | **Actual hidden native WebView2** journeys pass 119 named assertions / 21 app-only render checkpoints, including engine receipts and close/reopen during pending work. Separate headless Chromium + real Rust stdio run passes the same 119 / 21. Native narrow (680×900) and 200% text PNGs inspected; no horizontal overflow. No desktop control, input injection, activation, desktop screenshots or other-app automation used. |

No new engine gameplay reducer, persistence, inference adapter, memory subsystem
or general diagnostics platform was introduced. Shared `host.rs` adds only a
coherent player snapshot, synthetic delayed mode and trusted resource counts.
Engine/inference rules, Android/JNI implementation and fixtures are unchanged
relative to accepted main. Current receipts concern the player's typed requests;
future NPC/background receipt transport needs an observer-policy review.

## Exact checks actually run

Commands below run from repository root except npm, which ran in `apps/desktop`.
All final commands listed exited 0. Cached `--offline` builds do not establish
a disconnected-network or outbound traffic capture test.

| Command | Observed result |
|---|---|
| `npm ci --ignore-scripts --no-audit --no-fund` | Fresh dependency install from lock; 32 packages added. No install scripts. |
| `npm run check` | Normal bundle, strict TypeScript, 25 original host fixtures + four current action builders against Rust schema, hostile wire/player-view inputs, 64-entry enum-only error ring, Enter/newline/IME policy, normal-bundle harness marker absence. |
| `npm run format:check` | All frontend/config/script inputs pass pinned Prettier. Generated request types use the same formatting config. |
| `npm run harness:native` | 21 semantic checkpoints / 21 `native-webview2` captures / 119 distinct assertions. Native close/reopen and direct-engine oracle pass; final disposal sessions/workers 0/0. |
| `npm run harness:headless` | 21 semantic checkpoints / 21 `headless-chromium` captures / 119 distinct assertions. Real Rust stdio host; zero unexpected asset requests. Not native IPC evidence. |
| `python scripts/check.py host --offline` | Format/Clippy; 26 domain + 8 Android-boundary + 5 accepted runtime-spike Rust tests; four fixture parity cases; 21 benchmark + 10 LiteRT-worker + 14 llama-worker Python tests; 18 runner/APK Python + 3 linker tests. Runtime worker tests use synthetic faults, not a new model measurement. |
| `cargo test -p locallore --features host --locked --offline` | 10 host + 26 domain tests and 5 runtime-spike example tests. Generated-schema equality, coherent player view, isolation/idempotency/worker bounds and threaded cancel/commit races pass. |
| `cargo clippy -p locallore --all-targets --features host --locked --offline -- -D warnings` | Pass, no warnings. |
| `cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check` | Pass. |
| `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness` | Two unique artifact-boundary tests pass in both binary module and integration wrapper; not four independent tests. |
| `cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --features dev-harness -- -D warnings` | Pass; actual command attributes and wrapper compile. |
| Normal `npm run check`, then `cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline -- -D warnings` and `cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline` | Ordinary native executable builds with only `host_call` registered, dev modules compiled out, normal frontend markers absent. |
| `python scripts/check.py android --offline --clean` | Accepted-main compatibility rerun: 79 Gradle tasks, all 79 executed; both Rust ABIs rebuilt; app/test APKs; 30 JVM tests, 0 failures/errors/skips; lint; permission/ABI/16 KiB ZIP+ELF audit passes. No fresh emulator/physical-device execution. |
| `git diff --check` | Pass. |

Android command used the existing JDK17/SDK environment:

```powershell
$env:JAVA_HOME='C:\Program Files\Android\Android Studio1\jbr'
$env:ANDROID_HOME="$env:LOCALAPPDATA\Android\Sdk"
python scripts/check.py android --offline --clean
```

The earlier pre-main-integration Android result (78 tasks / 11 JVM tests) and
native 109/112-assertion runs are superseded by the final integrated results
above. They do not prove the later regressions.

## Local artifact identity and visual inspection

Artifacts remain ignored beneath `apps/desktop/artifacts/`; no raw render or
story dump is uploaded. Both final summaries record source `fa6aea7…`,
`sourceDirty:false`, 119 distinct checks and 21 checkpoints. The driver records
hashes of controller/model/UI/journeys, schema/generated types, locks, scripts,
native sources, embedded bundle and tested executable. Documentation edits
follow those runs without changing these inputs.

| Backend | Local relative artifact leaf | Summary SHA-256 |
|---|---|---|
| Native | `native-33387cc5-c1e5-4e6e-a9ef-d91d9bc33c64` | `3bea5438560999b4b7f60095b7b8efc7e1e0004eee9e75a9b7eac6241a0da3ec` |
| Headless | `headless-710b5d9a-08a8-4114-9529-6395521154f0` | `f5985db846aa62b744c4e2bfa16c176a554e69552d04d175c00a31be8205668d` |

Selected final source SHA-256 identifiers:

| Input | SHA-256 |
|---|---|
| `ui/controller.ts` | `747f19e30261b9d094bec12b85ca40f6335a98c59d528f94178c0e1358340a15` |
| `ui/journeys.ts` | `7621985af10f02fd2998efdf99b4d9af30cc887dc5630cead2c4a90c41f6e2fa` |
| `crates/locallore/src/host.rs` | `7041c5ab6c60d2a46283f622ac2d0298d382af411b1e5806d9394782af14b213` |
| Harness frontend bundle | `ee66399d965b83fffc15d501af020131be1eab171e9aa0777661b37a369ddb42` |
| Native-run executable | `32087ca097e86c9ce11557cb1f2f8dbb5287002ae18c36335621b09d4764efac` |
| Headless-run executable | `3e664685f8eb2951f9a164dbef2fbad67a845f3246fce349a1cdbf90e2a2dc6c` |

Inspected final native `play-accepted.png`, `narrow.png`, `enlarged.png`: actual
app content is meaningful, synthetic and readable. At wide size the transcript
and receipt/state inspector appear alongside the session list; narrow/200% text
stacks panes with vertical scrolling. Native CapturePreview captures the app
viewport rather than a full scrolling document. DOM measurements establish no
horizontal overflow at those checkpoints; a PNG alone does not prove keyboard
or screen-reader usability. Headless PNGs are supplemental page captures.

Native teardown prints `PostMessage` invalid-window-handle and
`Chrome_WidgetWin_0` unregister (1412) warnings after successful close/reopen;
the harness and process exit 0. These warnings remain upstream teardown evidence,
not a leak/sanitizer qualification. Fixed-count lifecycle assertions establish
release of shared host sessions/workers, not every OS resource.

## Review findings resolved with durable regressions

[Independent review](D02_NATIVE_REVIEW.md) reproduced lost-ack duplicate effects,
stale recovery errors, regressing reads, cancellation during recovery, premature
receipt publication and late errors overwriting terminal outcomes. The final
controller retains unresolved ownership before submit, validates complete
structural requests before publication, serializes recovery and fences reads.
Known cancelled/committed outcomes survive late failures. A malformed recovered
receipt retains the original key until valid reconciliation.

Final native and headless runs execute named checks including
`uncertain-commit-retry-original-id-once`, `lost-submit-reuses-original-key`,
`recovery-deduplicated`, `old-recovery-error-cannot-publish`,
`old-read-cannot-regress-revision`,
`cancel-during-uncertain-recovery-resolves-original`,
`retry-after-recovery-cancel-not-stuck`,
`late-prepare-error-cannot-replace-authoritative-cancel`,
`late-transport-error-cannot-replace-authoritative-commit`,
`malformed-recovered-receipt-never-published` and
`malformed-recovery-retains-original-id`. No subscriber sees the deliberately
foreign recovered receipt, and no new-ID duplicate action is submitted.

Normal compilation omits native harness modules/handlers; ordinary frontend
build removes the driver. Static Tauri permission names alone register no API.
Development native hooks also check runtime activation and native window label,
with fresh launcher-selected artifacts and fixed allowlisted labels/presets.
No general-purpose server, arbitrary JS/file/shell capability or production
control endpoint exists. See [reproducible harness/bounds](D02_HARNESS.md).

## Versions, pins and limits

Tested Windows 11 Pro x64 build 26300; installed WebView2 155.0.4283.62;
Rust/Cargo 1.93.1; Node 23.10.0 / npm 11.2.0 for development only. Headless
Playwright browser: Chromium 156.0.8078.4 (revision 1248). Android: JDK 17.0.6,
Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21, SDK36 / Build Tools35 / NDK29.
No model/runtime/tokenizer was loaded by D02. Existing M01 runtime measurements
are separate accepted work and do not establish desktop inference integration.

| Added direct package | Pin | License / role |
|---|---|---|
| React / React DOM | 19.3.1 | MIT; embedded UI |
| @types/react / @types/react-dom | 19.3.0 | MIT; development types |
| TypeScript | 7.0.2 | Apache-2.0; development checker |
| esbuild | 0.28.2 | MIT; local asset bundler |
| json-schema-to-typescript | 16.0.0 | MIT; Rust-schema request types |
| Playwright | 1.64.1 | Apache-2.0; own headless development page |
| Prettier | 3.9.10 | MIT; deterministic development formatting |
| webview2-com / windows (optional) | 0.39.1 / 0.62.2 | MIT / MIT OR Apache-2.0; app-only development capture, same locked transitive versions as Tauri |

Ajv 8.20.0, Tauri 2.12.5, tauri-build 2.7.4 and Tokio 1.54.1 are retained pins;
Tokio enables `time`. npm/Cargo locks capture transitive dependencies/checksums.
License declarations were inspected in installed manifests; full redistributed
runtime notices/installer/update qualification remain D09. Primary API references:
[React root lifecycle](https://react.dev/reference/react-dom/client/createRoot),
[esbuild API](https://esbuild.github.io/api/),
[Playwright page capture](https://playwright.dev/docs/api/class-page#page-screenshot),
and [native capture review sources](D02_NATIVE_REVIEW.md#capture-implementation-and-dependencies).

Known dependency maintenance item: read-only GitHub alert inspection confirms
the existing [Dependabot alert #1](https://github.com/OptimumAF/LocalLore/security/dependabot/1)
is open for locked `glib 0.18.5`, GHSA-wrw7-89jp-8q8g (medium; patched 0.20.0).
It predates D02 and belongs to the unqualified GTK/Linux target graph; this
Windows slice retains that upstream lock graph. No alert was dismissed or
security clearance claimed. Resolve the upstream dependency path before a
Linux/redistribution gate; this packet does not silently broaden qualification.

No installer/package redistribution, macOS/Linux build, real inference, free-text
intent interpretation, durable save/resume, SQLite, archives, author edits,
production accessibility audit, actual OS clipboard write, traffic trace,
native sanitizer/leak audit, new emulator or physical-phone measurement is
claimed. `bundle.active=false`; native executable/window evidence satisfies the
local review slice, while owner clean-checkout acceptance remains pending.

Next runnable product task after D02 review: D03/#8 shared durable storage and
resume, followed by D04/#9 real local inference using the measured M01 boundary.
Keep both shared with Android; do not add desktop-only substitute authorities.
