# Live selected-attempt narration validation: verification

2026-10-29. Refs #28 (D06.01/D06.03/D06.06/D06.07 supporting slice).
Full D06 remains unchecked. This record distinguishes source review, public Rust
Host tests, synthetic frontend execution and pending native rendering.

## Implemented bounded behavior

The debugger explicitly reads the selected original player attempt through the
existing generated `trace_narration_validation_read_v1` command and `host_call`.
It binds session, story/branch, current head, original base, turn and attempt;
the private lifecycle latch also retains the actual native player identity.
Current head need not equal the preparation base. The finite decision is
inspection metadata, separate from canonical commit, mechanical fallback and
human narrative quality. Native absence has no invented cause.

The same frontend codec checks the live Host data and the stored comparison
observation's decision/data. Live malformed data remains `Wire`; comparison
malformed data remains `ComparisonReaderWire`. Existing comparison envelopes,
provenance/binding/status checks and total-size limits remain in place. The live
decoder bounds detached **data** to 4096 bytes; Rust owns its total-envelope
4096-byte cap. These are different measurements.

Local UI admission requires shown debugger, acknowledged Story Lab/omniscient
lens, checked source/trace/selection, quiescent gameplay and Main's matching
presentation fence. It does not create native Story Lab permission. Rust still
validates the request and may refuse it. There is no new Host operation, store,
inference provider, schema, native authority field or persistence format.

Pending is published before IPC, then context is checked again after synchronous
subscribers. Duplicate pending reads preserve the original latch. Local cancel
retires display ownership without cancelling gameplay or the native read.
Session, scope, head, lens, selection, trace controls, gameplay and teardown
retire old content. Main marks stopping before publishing its null fence, so
still-registered Root/V2 callbacks cannot reopen access during cleanup.

The existing thin snapshot supplies trace identity for Domain1/Domain2 and
nonliteral players. Its App branch mounts only metadata debugger support.
Legacy inspection, receipt comparison, capture, exports, timeline navigation and
unsupported generation do not gain adapters through this change.

## Independent source lineage

Accepted production base is merged main `f4d2de0cb25fcc8dc2db48558fb489701f251fd8`.
The [accepted contract](D06_LIVE_NARRATION_DIAGNOSTIC_CONTRACT_2026-10-29.md)
retains its original proposal and appended Root acceptance/precision. Source
claims, releases and evidence are recorded on #28, not a replacement task tracker.

Public Host FIRST was independently authored as sole new test
`crates/locallore/tests/live_narration_validation_read_review.rs`, original
`fd7d0cf887fcec034880e764a202647bf10e84eb`, Root cherry `e3810aad`, formatter-only
`b7f9d202`. Raw SHA256:
`0c8c19c1943cd0105fc0c6fc07d148ae0f7b396b75da7b6f0cd8e91a39aeb542`.
Formatted SHA256:
`c069d59749d6004cb5994b48ed20061d2e6dfb237213ce8fbcbb63340f9ddc0f`.
Original and separately formatted derivative remain local; exact equality is
recorded in `d06-live-host-first-format-equality1.json`.

Frontend FIRST was independently frozen at
`62f2a642e0fab620966dd2b79635bb93dd8c3aa4`, Root cherry `a77be8e0`, formatter-only
`43df3466`. Its three original sources and formatter-derived copies remain local
under `d06-first-62f-*`; all three exact derived equalities are true in
`d06-first-62f-format-equality1.json`.

| Source | Original SHA256 | Formatted SHA256 |
| --- | --- | --- |
| `check-live-narration-diagnostic-review.mjs` | `4e834153fb1af6518912324b7b64f09a1667806f7a300889e53b3b8f00aa6145` | `8faaa3b45c49a4f31eae95889424dfd0a3cd3d2a59a8addb487f412ed553fa0f` |
| `check-main-live-narration-diagnostic-review.mjs` | `4acd78d287ad95c6fba01b2c9d3c29cc4afd8d32de49a082b7cc5e06cdf51cc9` | `7d2f3be01c1a146eb9b7789c430864372651207a4c7ba03bbbe83ef2dc5dfa65` |
| `live-narration-diagnostic-review-fixtures.mjs` | `19ffe66e1837f9bc695a50dc2a1b0f738b865044b204524d041d9db133572a6a` | `3ac37a988aac315b9393fa3e1ee916de5b2d8c001adb4e88e360cd071fdb9fff` |

Different-author codec/state/panel production was released at `d84d4a2a`, Root
cherry `84fad42a`, formatting `d058cb10`. Root authored Controller/Main/App in
`7b7ee1d0` plus detached trace retention `293868fa`; their independent source
review found no concrete blocker. These are source reviews, not GitHub approvals
or human quality acceptance. Frozen behavioral oracles were not changed.

## Executed evidence so far

Local evidence root (physically on D, outside source Git):
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/author-integration-artifacts`.
Each process record includes source, clean/unchanged status, exact command,
timestamps, exit, TEMP/TMP and Cargo home. Full logs remain local.

| Check | Source | Actual result | Local evidence family |
| --- | --- | --- | --- |
| Public Rust Host FIRST | `b7f9d202` | 8 passed, 0 failed, 0 ignored; 0.18s test / 5.7368907s command | `d06-live-host-first1` |
| Live codec/actual Controller/actual TurnDebugger static React | `d058cb10` | 120 passed, 0 failed, setup 0; 8 static HTML files | `d06-live-frontend-first1` |
| Actual Main/App/V2 with headless hooks and synthetic native gateway | `d058cb10` | 13 passed, 0 failed, setup 0 | `d06-live-main-first1` |
| Full frontend suite, strict TS/schema/normal build and existing regressions | `c6a88c1f` | exit 0; 17.4312084s; includes live120/Main13 and unchanged reader/trace oracles | `d06-live-frontend-full2` |
| Full frontend Prettier check | `c6a88c1f` | exit 0; 3.0511098s | `d06-live-frontend-format1` |

Host FIRST uses actual public Host/Core with a fixed counting **test** provider.
It tests nonlatest attempt/current-head binding, recorded decisions, exact
nonmutation, denial precedence, owner/lifecycle isolation and actual Domain2
metadata after author correction/persistence resume. It adds no product provider.
It is not the complete 25-tuple runtime matrix, native IPC, WebView or model proof.
The independent frontend checks cover the finite tuple matrix, hostile
descriptors/aliases, local gates, reentrancy, pending/cancel/retry, late success
and refusal, session/head/lens retirement and thin metadata-only mount.

The full frontend pass log SHA256 is
`ae9b3c823b50a6731c55c98b2e7cfe0d3bb3404f5f2a05d9fef7c3896dca794e`.
Host pass log SHA256 is
`a351518cf3acf947b476e7454409d8d792e5a02012ede9d7e895199001502b9a`.

Preserved failures:

- Initial live checker at `7b7ee1d0` exited 1: proposed shared module was missing,
  classified **SETUP**, 120 authored / 0 run / 0 behavioral failures. No behavioral
  RED is claimed (`d06-live-frontend-setup1`).
- Initial full frontend at `902c58d3` exited 1 on TS2352 for the shared Scope cast.
  `c6a88c1f` returns the already validated narrowed fields; the unchanged suite
  then passed. Failed log/process remain `d06-live-frontend-full1`.

## Native, compatibility and unavailable gates

Actual native IPC/WebView execution for this live diagnostic change is pending.
The separately [frozen harness contract](D06_LIVE_NARRATION_NATIVE_HARNESS_CONTRACT_2026-10-29.md)
requires the existing fixed scene provider/Store, exact real outcomes, local
cancel/stale completion, cold restart, bounded logs and individual image review.
No native pixels, OS isolation or model qualification is inferred from the
headless checks above. Current Rust/Android-host, native lint/test/build and final
integration checks will be recorded when executed on the final source.

Frontend data cannot recover raw duplicate JSON keys already overwritten by the
transport parser. The oversized adversary also violates identifier bounds; it
does not isolate a valid DTO exceeding the Rust envelope cap. An isolated
`context_changed` reason may be unconstructible because public lifecycle changes
clear old state first; defensive alias prevention is tested without private
state seeding. No complete trace-context/raw proposal/memory explanation,
pause/step, generation rerun or full D06 exit gate is claimed.

Frozen real-model samples and both human **needs improvement** assessments remain
unchanged. This metadata read does not backfill missing old diagnostics, fix
narration quality, establish scores or rerun the original real cohort. Physical
Android, SDK/emulator, installer/clean-profile, network/OS isolation and release
checks remain unavailable/stopped under their existing scope decisions.

## Reproduction and retention

Run project commands from the physical D checkout. In each shell first set
`TEMP=TMP=D:/Dev/_Temp`; reuse the existing locked offline Cargo cache/target.
For frontend checks set `LOCALLORE_CHECK_OUTPUT_DIR` to an existing D artifact
directory. Do not place project code or generated outputs in C, a profile folder
or Windows temporary directories. Use the pinned Node executable from the D
toolchain or its equivalent verified version.

```powershell
node apps/desktop/check-live-narration-diagnostic-review.mjs
node apps/desktop/check-main-live-narration-diagnostic-review.mjs
node apps/desktop/verify-frontend.mjs
cargo test -p locallore --features host --test live_narration_validation_read_review --locked --offline --target-dir <existing-D-target> -- --test-threads=1
# From apps/desktop (PowerShell must quote globs):
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
```

Source/frontend artifact admission is 128 MiB. A bounded top-level measurement
at 18:59 UTC found 180 new files / 35,524,268 bytes since the first raw preservation
at 18:49:54 UTC. This is not a recursive target/profile measurement. Native
execution has separate predeclared target-growth/artifact limits in its contract.
Preserve original oracles, failed outputs and all capture packets; no deletions
or replacement roots are authorized to evade a failed boundary.

Verified toolchain in the current local workflow: Rust/Cargo 1.93.1,
rustfmt 1.8.0-stable, Node 24.22.1, TypeScript 7.0.2, React 19.3.1,
Prettier 3.9.10, PowerShell 7.6.5, Windows 10.0.26300.0. Previous installed
WebView2 file metadata is 156.0.4314.50; it is not a loaded-module or new render
measurement. The live harness must record its actual rendered user agent.
