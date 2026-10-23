# Desktop durable app verification - 2026-10-22

Refs #8 (M04 adapter integration), #24 (D03.01/.02 and durability portion .07).
Implemented and locally verified; owner acceptance and full milestone gates remain separate.

The definitive suite ran from clean source `1a18d12393082dc83186e3af24080d04d63b0b85`,
including the shared owner fixes through `7bf5b7e`. The versioned
[synthetic evidence summary](APP_DURABILITY_EVIDENCE_2026-10-22.json) records
`sourceDirty:false`, the exact assertions, and SHA-256 bindings for the frontend,
recorded native harness executable, lease, shared Host, workspace and storage
sources. The coordinator verified the source against the integration checkout;
where Windows checkout line endings differed, Git-normalized text equality was
checked separately from the recorded raw-byte SHA-256 values. The harness
executable hash describes the dev executable used for captures, before restoring
the normal build.

## Executed checks

Commands below ran from `apps/desktop` on Windows x64, Rust/Cargo 1.93.1,
Node 23.10.0 and npm 11.2.0. Tauri 2.12.5, tauri-build 2.7.4 and Playwright
1.64.1 remain pinned. Native rendering used installed Evergreen WebView2; its
exact loaded runtime version was not recorded in the harness.

| Command | Actual result |
|---|---|
| `npm ci --offline --ignore-scripts --no-audit --no-fund` | Fresh isolated node_modules; 32 packages installed |
| `npm run check` | Pass: strict TypeScript, 25 original wire fixtures, four actual action builders, hostile wire/bounded errors/keyboard policy, normal bundle excludes dev control hooks |
| `npm run format:check` | Pass |
| `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check` | Pass |
| `cargo test --manifest-path src-tauri/Cargo.toml --locked --offline --features dev-harness` | Pass: four unique cases (two lease and two artifact contracts); the separate harness wrapper repeats the two artifact cases |
| `cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets --locked --offline --features dev-harness -- -D warnings` | Pass |
| `npm run harness:durable` | Pass: 33 assertions, 11 native app-only captures; same synthetic SQLite database through WebView close/reopen and actual executable process restart |
| `npm run harness:native` | Pass: legacy D02 memory fixtures, 119 assertions and 21 native checkpoints |
| `npm run harness:headless` | Pass: legacy D02 memory fixtures, 119 assertions and 21 headless Chromium checkpoints with real Rust stdio host |
| `cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets --locked --offline -- -D warnings` | Pass after restoring normal frontend |
| `cargo build --manifest-path src-tauri/Cargo.toml --locked --offline` | Pass after restoring normal frontend; normal visible app was not launched |
| `git diff --check` | Pass |

The final native durable root is ignored local
`apps/desktop/artifacts/durable-native-d60a4b4d-d6e6-42d2-9046-66acee3213bd`.
Final D02 native and headless roots are respectively
`native-e6e215ba-0a93-4f02-819f-a6eb82275696` and
`headless-29fd8580-3484-4d36-aa72-89e22a34f614` under the same ignored artifact
parent. Their JSON/PNGs remain local. The native resumed and storage-failure
PNGs were visually inspected: readable library/transcript/rules and spent potion,
with an explicit storage error and disabled play on initialization failure.
The durable semantic JSON and DOM text redact the synthetic absolute save path;
a recursive scan found no home/worktree path in its JSON. The normal UI still
discloses its actual app-local save location on request.

## Verified behavior and boundaries

The real frontend/controller and native IPC verify an empty workspace creating a
saved original scene, authoritative rules before the first turn, accepted receipt
persistence, stale rejection, cancellation without a canonical receipt, preserved
session-local unsent text, lost commit acknowledgement resolved under the original
turn key, explicit library resume, close retaining the save, and New/Reset retaining
prior stories. A submitted but uncommitted request survives close/restart, with an
honest warning and no automatic commit or cancellation. Validated transcript and
spent potion survive restart; the brass key correctly remains. An old exact
request returns its original stored receipt with no double application. A fresh
process sends a distinct turn key, and stored receipts match direct engine replay.
A separate fixed invalid-storage-root case renders failure without a memory fallback.

The native lease regression barriers cover a captured call released after Destroyed,
delayed initialization, cleanup completion before reopen, and rejection of the old
window identity. The same gate is used by production initialization and non-prepare
dispatch; generation remains outside it and is fenced by shared session ownership.

Earlier candidates exposed two test/harness issues: the first inventory assertion
incorrectly expected no owned items despite the retained brass key; and the old
intercepted HTTP headless origin lacked the standard Web Crypto UUID API. These
were corrected to assert the spent potion specifically and use intercepted HTTPS.
The definitive results above supersede those candidates. The existing upstream
WebView teardown class-unregister warning 1412 (and intermittent invalid-window
PostMessage warning on earlier candidates) remains a documented teardown limit;
final native runs reported PASS and exited zero. No native leak or network-trace
qualification is inferred.

No desktop control, input injection, activation, desktop screenshot, other-app
operation, emulator/model/runtime-control action, public artifact upload, merge,
release or repository-settings change was performed by this specialist. The
protected chat and its worktrees/processes were not accessed or messaged. Test
storage and WebView profiles were fresh launcher-owned synthetic roots; production
app data was not opened. CapturePreview captured only this app's hidden WebView.

The current integration is one app-local SQLite workspace with original fake-provider
stories and at most four live sessions. Unsubmitted composer text is not durable.
No real-model pipeline, arbitrary story generation, export/import/fork/delete UI,
installer, cross-device round trip, screen-reader, OS clipboard, OS backup or
physical-phone qualification is claimed. Android/core evidence belongs to the
coordinator's integration report; these desktop checks do not execute those gates.
