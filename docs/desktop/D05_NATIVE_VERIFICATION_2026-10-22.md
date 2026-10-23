# D05 native inspection verification - 2026-10-22

D05.01–.07 bounded desktop UI integration is ready for review. The definitive
native run passed **81 distinct assertions, 14 app-owned PNG captures and a real
executable process restart** against one fresh synthetic SQLite workspace. No real
model was loaded or called. Shared M06/M07 memory/retrieval prerequisites, complete
D05 acceptance, release qualification and long-history performance remain open.

The run recorded clean source
49e641349b8b77c9f7b5efb21a764aee7b0d0f78, stacked on the coordinator's frozen
db3e6ed shared-query/D04 integration. Subsequent 30827e1 only formats the generated
schema with the root owner's explicit exception. Parsed JSON values before and
after are identical; canonical JSON SHA256:
98093ebe050bc293ddf76f0dc68febbcbef85c4e7cd5a86ad480c90119ff4d6b.
Generated request types and shared production sources were not changed by this UI
packet. Normal frontend assets and the default native executable were restored.

The committed [synthetic evidence](D05_NATIVE_EVIDENCE_2026-10-22.json) contains the
exact UI/native executable/shared Host/query/engine/storage source SHA256 map,
checks, fixed expected error categories and regression summary hashes. The source
summary SHA256 is
acbaa9f7531f0d7e603395049f1c03b056575af6d8d19cce6199da150eb780cf.
Local task-owned artifact directory on D:
desktop-inspector-artifacts/inspector-native-8afb53ea-8319-4351-9c90-9a2abbf21fdd.
Source hashes use exact local bytes; compare Git-normalized text if CRLF differs
between checkouts. The schema's later formatting is explicitly separate from the
executed build hash and changes no parsed value.

## Actual native coverage

The development launcher exercised the actual React frontend, production
Controller, frozen Host envelope and native IPC in this application's hidden
WebView2. Existing deterministic fake-provider commands established the synthetic
accepted potion, false-statement and belief history. All subsequent inspection
queries were read-only; canonical snapshots, story time and live-worker counts
were exactly unchanged by browsing. It did not use a simulated response service
or a real-model provider. The restart stage launches a second actual executable
and rebuilds historical state from the same saved database.

The executed checks cover:

- Typed profiles, actual historical seed inventory and current spent potion.
- Chat receipt to completed-turn comparison, with potion present before r1 and
  absent after it, rather than current state relabelled with an old timestamp.
- Event IDs, turn, time, participants, witnesses and consequences; selected
  records, exact field provenance, seed/event links and explicit local copying.
- Separate canonical truth, recorded false statement and subjective belief with
  confidence, plus independent directed relationship dimensions.
- Deliberate spoiler-modal acknowledgement and initial keyboard focus. Mira sees
  witnessed gift/speech events, no raw player/narrator Message rows, and zero secret
  search rows/count/cursor. Unwitnessed Sable sees neither event. Duplicate display
  names Oren and Sable retain separate actor IDs in the omniscient profile view.
- Bounded pagination without repeated records, previous-page context, unsupported
  summaries/indexes, and seed promise status with its recorded source.
- Late private Player response after switching to an NPC lens; delayed response
  after creating another story; explicit stale-head failure after an external
  accepted turn; refresh to the new head; and empty new-story history.
- Actual native API rejection of sibling scope, future revision, edited cursor,
  row limit65, search over256 bytes and a control-character search. Exact error
  categories are Scope, InvalidBoundary, InvalidCursor, TooLarge and InvalidRequest.
- Durable historical replay and event history after real process restart, without
  loading a model; browsing still leaves the saved projection unchanged.
- Valid memory-workspace skip target, focusable labelled native controls, captioned
  tables with row/column headers, bounded status messages and no render/unhandled
  errors. Narrow 680px output at150% text has no horizontal overflow.

The UI fixture's InvalidBoundary case is a future revision. Multi-event partial
boundaries and unprivileged trusted-Host grant denials are shared module/Host test
coverage, not separately executed native UI vectors in this packet. The normal
app owns a trusted Story Lab Host; the deliberate UI acknowledgement is not a
hostile-renderer security sandbox. The root-owned shared packet reports16 module
and2 actual Host/SQLite tests after its two observer-leak corrections. Those are
coordinator results; this specialist did not rerun or claim ownership of them.

## Checks actually run

Windows x64, Rust/Cargo1.93.1, installed WebView2 and the existing pinned Node/npm
tooling. Build/test debug information was disabled and incremental compilation
was off. New target, temp, profile, database and capture outputs used task-owned D
locations; existing C model/data/evidence were retained. Test flags:
CARGO_PROFILE_DEV_DEBUG=0, CARGO_PROFILE_TEST_DEBUG=0, CARGO_INCREMENTAL=0.

```powershell
node apps/desktop/inspector-harness.mjs
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target>
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --features dev-harness --target-dir <owned-D-target> -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --target-dir <owned-D-target> -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
```

All final checks passed. Default native tests: **15/15**. Development native tests:
**17/17 plus2/2** harness-wrapper tests. Strict all-target Clippy passed for both
configurations. Frontend checks passed strict TypeScript,25 original Rust action
fixtures plus four current builders, hostile-wire/bounded errors, keyboard policy,
normal-asset hook absence, export races, model-request recovery and the new actual
Controller inspection regression. The new case proves full-context late-response
fencing, object-field-order-independent observer matching, wrong-privacy rejection
and clearing when the inspection workspace closes. Frontend and Rust formatting
passed. The generated schema initially failed Prettier; only its authorized
whitespace formatting was applied and parsed equality verified.

Previous feature journeys passed again with trusted D output overrides:

| Runner | Actual result | Local artifact suffix |
| --- | --- | --- |
| node harness.mjs native |163 assertions /21 checkpoints |native-8def8155-c25b-4511-a815-5033ca3471cb |
| node harness.mjs headless |163 assertions /21 checkpoints |headless-68bb1a04-ae35-41ca-9fc9-6de600f104b3 |
| node durable-harness.mjs |33 assertions /11 PNGs |durable-native-e0dbc2f1-d0f2-42df-8efa-37014fca6a26 |
| node export-harness.mjs |36 assertions /14 PNGs /four publications |export-native-d7f5a382-484e-45c6-a812-daeb8799b247 |

These directories are under task-owned desktop-inspector-regressions on D. The
native/legacy journeys are explicitly fake memory fixtures; headless uses a real
Rust stdio Host and Chromium, not native WebView IPC. Durable/export use synthetic
SQLite and executable restart. The legacy headless run recorded dirty=true while
only the README/new inspection documentation was being drafted; the native legacy,
durable, export and definitive D05 runs each recorded clean source. Exact source
revisions and summary hashes are retained in the evidence. Later skip navigation
and schema formatting do not alter legacy gameplay paths.

## Render inspection and limitations

Visual review used app-owned CapturePreview only. Profile/context and restart
captures show story/root branch, current versus inspected revisions and privacy.
The focused selected-event capture shows turn/time/participants/witnesses and
source controls. The diff shows separate before/after values and seed provenance.
Knowledge displays distinct statement/belief/truth labels; Mira's private-character
History shows only her two witnessed events and no player display messages. The
narrow capture shows wrapped history rows and source controls, rather than only a
long sidebar. All14 semantic snapshots record no horizontal overflow and contain
no actual home paths. This is finite render/accessibility evidence, not a complete
screen-reader audit or every long-history layout.

Retained diagnostics include a consumer bug that compared JSON observer field
order instead of kind/ID, causing Wire for an otherwise valid Mira response; it
was fixed and covered by the actual-controller test. The first size-denial test
incorrectly expected InvalidRequest; the frozen API correctly returned TooLarge,
and the test was corrected without changing shared behavior. C disk exhaustion
interrupted one build; subsequent builds/temp/artifacts used D. No failed run was
relabeled as successful. Successful WebView shutdown sometimes emitted Chromium
class-unregistration error1412; process reports and exit codes were successful.

No desktop input/activation/screenshot, CUA, ADB, unrelated-app automation,
protected thread/device/process operation or model-source mutation occurred.
Normal frontend/default executable were restored without a normal visible launch.
No real model quality, networking, sustained performance, package installation,
advanced summary/retrieval/branch memory or complete D05 acceptance is inferred.
The next coordinator-owned work is review/integration and the remaining shared
memory prerequisites, followed by later inspector/debugger/evaluation slices.
