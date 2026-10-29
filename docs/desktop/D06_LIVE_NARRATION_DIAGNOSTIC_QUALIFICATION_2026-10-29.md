# Live selected-attempt narration validation: verification

2026-10-29. Refs #28 (D06.01/D06.03/D06.06/D06.07 supporting slice).
Full D06 remains unchecked. This record distinguishes source review, public Rust
Host tests, synthetic frontend execution and actual application-owned native rendering.

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

## Executed evidence

Local evidence root (physically on D, outside source Git):
`<task-owned-D-evidence>/author-integration-artifacts` (a sanitized placeholder;
exact private task paths remain in local process records).
Each process record includes source, clean/unchanged status, exact command,
timestamps, exit, TEMP/TMP and Cargo home. Full logs remain local.

| Check | Source | Actual result | Local evidence family |
| --- | --- | --- | --- |
| Public Rust Host FIRST | `b7f9d202` | 8 passed, 0 failed, 0 ignored; 0.18s test / 5.7368907s command | `d06-live-host-first1` |
| Live codec/actual Controller/actual TurnDebugger static React | `d058cb10` | 120 passed, 0 failed, setup 0; 8 static HTML files | `d06-live-frontend-first1` |
| Actual Main/App/V2 with headless hooks and synthetic native gateway | `d058cb10` | 13 passed, 0 failed, setup 0 | `d06-live-main-first1` |
| Full frontend suite, strict TS/schema/normal build and existing regressions | `c6a88c1f` | exit 0; 17.4312084s; includes live120/Main13 and unchanged reader/trace oracles | `d06-live-frontend-full2` |
| Full frontend Prettier check | `c6a88c1f` | exit 0; 3.0511098s | `d06-live-frontend-format1` |
| Final frontend suite after native wiring, scale correction and CSS | `ade9a877` | exit 0; 15.8164820s; live120/Main13/process43 and existing regressions | `d06-live-frontend-full4` |
| Final full frontend format | `ade9a877` | exit 0; 2.6042356s | `d06-live-frontend-format2` |
| Strict native Clippy, all targets, dev-harness | `a9a632b1` | exit 0; 16.7412885s; compilation only | `d06-live-native-clippy1` |
| Rust Android crate on Windows host | `a9a632b1` | exit 0; 0.5360290s; no SDK/device execution | `d06-live-android-host1` |
| Rust format | `a9a632b1` | exit 0; 0.6035794s | `d06-live-rust-format1` |
| Exact app-bin artifact bounds / create-new allowlist tests | `a9a632b1` | 1/0 then 1/0, zero ignored; two distinct Rust cases | `d06-live-native-artifact-{bounds1,ownership1}` |
| Separate harness_contract target | `a9a632b1` | 2/0, zero ignored; repeats those same two cases | `d06-live-native-contract1` |
| Public Host FIRST after integration | `a9a632b1` | 8/0/0 ignored; 0.16s test / 1.0053473s command | `d06-live-host-integration1` |
| Actual native IPC/WebView initial and cold restart | `ade9a877` | exit 0; 47.1333970s; 117 initial / 17 restart assertions; 10 individually inspected PNGs | `d06-live-native-webview2` |

The native Rust files and Core/Android production sources are unchanged between
`a9a632b1` and `ade9a877`; subsequent changes are the Node policy checker/launcher,
frontend verification registration, corrected development journey and debugger CSS.
Clippy compiles the offline qualifier but does not execute it. App-bin tests use
exact names; no broad qualifier/OS-probe test command was run.

Host FIRST uses actual public Host/Core with a fixed counting **test** provider.
It tests nonlatest attempt/current-head binding, recorded decisions, exact
nonmutation, denial precedence, owner/lifecycle isolation and actual Domain2
metadata after author correction/persistence resume. It adds no product provider.
It is not the complete 25-tuple runtime matrix, native IPC, WebView or model proof.
The independent frontend checks cover the finite tuple matrix, hostile
descriptors/aliases, local gates, reentrancy, pending/cancel/retry, late success
and refusal, session/head/lens retirement and thin metadata-only mount.

The earlier full frontend pass at `c6a88c1f` has log SHA256
`ae9b3c823b50a6731c55c98b2e7cfe0d3bb3404f5f2a05d9fef7c3896dca794e`.
Host pass log SHA256 is
`a351518cf3acf947b476e7454409d8d792e5a02012ede9d7e895199001502b9a`.
Final frontend log SHA256:
`298be756ba92632936cd3ca8b66837541517afdd9714fdefcf07e90c79b2be3f`.
Final native command log SHA256:
`6509dc054b7d25eccd24f6d201e6f185eb802bc4686298324d9f06787fb1e395`.

Preserved failures:

- Initial live checker at `7b7ee1d0` exited 1: proposed shared module was missing,
  classified **SETUP**, 120 authored / 0 run / 0 behavioral failures. No behavioral
  RED is claimed (`d06-live-frontend-setup1`).
- Initial full frontend at `902c58d3` exited 1 on TS2352 for the shared Scope cast.
  `c6a88c1f` returns the already validated narrowed fields; the unchanged suite
  then passed. Failed log/process remain `d06-live-frontend-full1`.
- Native journey typing at `bf98492b` failed TS2531 because two separate pure
  `get()` calls do not retain null narrowing. Independently reviewed `a9a632b1`
  retains one local coldTrace binding; every asserted value/operator is unchanged.
  Strict typing and live120/Main13 then passed (`d06-live-native-wiring-*`).

## Native FIRST, process ownership and visible correction

Independent native sources were frozen at `b2eb0c22`, Root cherry `ba41c926`,
formatter-only `84b6478d`. The two raw files total 55,770 bytes. Raw launcher
SHA256 `6c1adf2e9c396f2a683d32b96177f2955dcda5b435cdd8749121870b163b3287`;
raw journey `d6024f35a5d4bc9cbb3e4203af36e6f148190b7771a4c1d98d6443f19b289b1b`.
Original/derived equality is in `d06-native-first-b2-format-equality1.json`.
The later typing-only and demonstrated scale corrections are explicit deltas,
not falsely described as byte-identical to the original formatted journey.

Independent process-policy FIRST `8930d2b2` / Root `ae5419fb` / formatter `ab5adcc0`
extracts eight actual launcher source blocks into a VM with fake children,
timers and storage. At `ab5adcc0` it ran 43 cases: 35 passed, eight behavioral
failures, setup zero. Four pipe-error cases escaped ownership handling and four
inventory failures allowed restoration to reconsider launching work. Root
`d5bee17e` fixed the actual launcher; the unchanged 43 cases passed, setup zero.
This is simulated policy evidence, not OS process containment or native rendering.
Raw checker SHA256 `e62ffc73044f37f9423c8fd5d8d0f87c5390904f922fc981fb72805df050b6bf`;
formatted `2b1d7743c0c3278fb18de98927e5f9788499f62ff62012c58820dd99778ad1fe`.
Raw/derived proof: `d06-policy-first-893-format-equality1.json`. Failed and green
logs remain `d06-live-process-policy-{red1,green1}`.

The first actual native packet,
`d06-live-narration-native-21e249ec-8294-496e-888b-fc273a868daf`, ran on `d5bee17e`:
exit 0 / 56.1855702s, 114 initial / 17 restart assertions, ten original images.
Root individually viewed all ten. They exposed a real test-construction defect:
the journey requested `layout(1,1,1.5)`, while the existing API accepts percent
values and clamps 1.5 to 100. That packet qualifies its wide viewport, **not 150%
text**. It also retains the narrow split Attempt header and undersized context.
No failed image or criterion was removed.

Original author `c4452995` corrected only 1.5 to 150 and added state, mounted
text-150 class and computed app/root font ratio assertions before the unchanged
capture. Root cherry `98d9850b`, formatting `4384e66a`; raw correction SHA256
`b2674f2cf4415377db258ea214d39cbcf56b31ac2488b2c503fc9c7ae9130bf2`, formatted
`82f5306be2a9be91c82547ab341038e6a37f979cbfdc13b2b88b98d0c57dd776`.
Root CSS `ade9a877` increases only debugger scope text/wrapping and gives the
Attempt column sufficient width. Existing geometry assertions are unchanged.

Corrected actual packet:
`d06-live-narration-native-ab85f94c-a0e4-431f-a048-d7f453ae614a`.
Initial 117 assertions / 97 distinct labels; restart 17 / 17. Root individually
inspected all ten new images: context, controls and statuses remain legible;
the narrow Attempt heading is intact and wide 150% text is genuinely larger.
All measured context/control/status boxes have positive area, remain in view
and pass their hit tests; there is no horizontal overflow. No whole-page or
desktop accessibility/OS qualification is inferred.

The journey uses the existing literal scene provider and actual V2 controller,
mounted handlers, host_call, Host and Store. It makes exactly two intentionally
scripted free-text commits: the UI turn at r1→r2, then the explicit external turn
at r2→r3 to provoke an actual Stale refusal against the retained r2 selection.
Initial provider counts are two factories / four polls; cold restart zero/zero.
Canonical/observer hashes match before/after read-only operations and across that
packet's cold restart. Other branch/story prefixes and observer isolation pass
the unchanged Store proof. This is durable save/reopen evidence using fake
inference, not real-model narrative quality.

Nine actual diagnostic dispatches cover accepted data, explicit retry,
unavailability after an external Host metadata clear, actual Stale refusal and
reconciled fresh selection. Pending/late-reply cases delay a **real completed IPC
reply** in the development Gateway; they do not hold a Rust validator/worker.
Local cancellation makes zero attempted gameplay Cancel calls. Character/player
lenses and session switches clear private results; local actor admission is not
native grant-denial proof. Initial error/refusal roster is exactly one native
Stale; restart has zero errors/refusals and zero diagnostic dispatches. Restart
shows default-disabled/empty private traces, without reconstruction or inference.

All six build/app/restore children and 28 Git children in the corrected packet
record known direct closure, exit zero, no timeout and no unknown drain. This
does not establish process-tree containment. Normal frontend/native restoration
passed; the normal app was not launched. Normal frontend SHA256 is
`61552ce15d51775d53cfa6f607c4230cf5a164b2a1ea52cd61d95dc56f59e9b2`.
Ordinary model status/shutdown may inspect an absent task-owned model candidate;
there is no independent SDK-load counter or zero-filesystem-probe claim.

First packet: 134 frozen files / 9,468,872 bytes, freeze SHA256
`d9485dc5c1374e46011f3f3b8de2937386a49c670ff42d1dddc6ba6d92185679`.
Corrected packet: 134 / 9,536,797 bytes, freeze SHA256
`0784f002b0814c4302cf32975b21627b12e44ad4aafbc6a923ea24ad9ca322d9`.
Both file maps remain local; the first was rechecked unchanged after the second.
Individual image-review records `d06-live-native{1,2}-render-inspection.json`
have SHA256 `55c0e323210f7b9d25ed3c91a10345c1d7c6b85b0ec588e322332fe947b91ab4`
and `a913df505f1a2d22c36616f855ac689b37374ea5c85c8de1d421e5fc2a165fef`.

## Native, compatibility and unavailable gates

The [native harness contract](D06_LIVE_NARRATION_NATIVE_HARNESS_CONTRACT_2026-10-29.md)
is exercised by the corrected packet above. Native rejected-narration decisions
and native Domain2/nonliteral-player journeys remain unqualified for this slice;
their Host/frontend tests do not become native evidence. Rust Android compilation
is Windows host compatibility only. No APK/Gradle/JVM/ADB/device/emulator,
offline-qualifier execution or targeted OS/network experiment was performed.

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
node apps/desktop/check-live-narration-process-policy-review.mjs
node apps/desktop/verify-frontend.mjs
cargo test -p locallore --features host --test live_narration_validation_read_review --locked --offline --target-dir <existing-D-target> -- --test-threads=1
# From apps/desktop (PowerShell must quote globs):
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
```

For the closed synthetic native runner, from the repository root, set
`CARGO_HOME` to the existing D locked cache and
`LOCALLORE_D06_LIVE_ARTIFACT_ROOT` / `LOCALLORE_D06_LIVE_TARGET_DIR` to existing
ordinary D directories outside the checkout. Set `CARGO_NET_OFFLINE=true`,
`CARGO_BUILD_JOBS=1`, `CARGO_INCREMENTAL=0`, development/test debug levels to 0,
and keep `LIBSQLITE3_FLAGS` empty. Then run
`node apps/desktop/live-narration-harness.mjs` with no arguments. It builds the
development frontend and only the locallore-desktop-spike bin, runs its fixed
initial/restart cases, and restores the normal build after known closure.
It never launches the normal app. Preserve all packets; no cleanup is authorized
to evade failure. Unknown drain, failed inventory or budget breach stops work.

Source/frontend artifact admission is 128 MiB. A bounded top-level measurement
at 18:59 UTC found 180 new files / 35,524,268 bytes since the first raw preservation
at 18:49:54 UTC. This is not a recursive target/profile measurement. Native
execution has separate predeclared target-growth/artifact limits in its contract.
Preserve original oracles, failed outputs and all capture packets; no deletions
or replacement roots are authorized to evade a failed boundary.
After the final full frontend check, the corresponding flat source/frontend
outputs were 525 files / 104,884,593 bytes, below 128 MiB; small later provenance
records are additionally retained. Both native packets total 19,005,669 bytes,
below the cumulative 256-MiB admission. Corrected target inventory was
8,259,980,576 logical bytes versus the pre-Rust D06 baseline 8,258,436,028;
cumulative growth 1,544,548 bytes, below 2 GiB. No evidence deletion occurred.

Verified toolchain in the current local workflow: Rust/Cargo 1.93.1,
rustfmt 1.8.0-stable, Node 24.22.1, TypeScript 7.0.2, React 19.3.1,
Prettier 3.9.10, PowerShell 7.6.5, Windows 10.0.26300.0. Previous installed
WebView2 file metadata is 156.0.4314.50; it is not a loaded-module or new render
measurement. The actual corrected renderer reports Chrome/Edg 156.0.0.0.
Fresh versions are retained in `d06-live-tool-versions1.json`; no downloaded or
upgraded dependency/model is part of this change.
