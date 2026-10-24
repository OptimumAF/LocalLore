# Private capture UI integration — 2026-10-23

Coordinator `/root`; claim #28 comment 6370020035. Partial D06.02/.03/.06/.07,
not full D06 acceptance. Accepted main `c1f2687` (#96) plus unchanged author and
independent regression/review commits is integrated at
`c011bf51a1b5b870b4d77ff11af185552fd0ece9` on
`impl/d06-capture-ui-integration`. The earlier author and reviewer cohorts remain
separately attributed in the companion reports. This report changes no product.

## Review and integration

The coordinator read the production native preview/save/revoke boundary, separate
typed broker and exact-file writer changes, controller barrier, originating-session
navigation fences, decoders and React panel. No remaining concrete blocker was
found in this frozen slice. Native preview obtains the actual Host read itself;
renderer input supplies strict selectors, never output bytes or a destination.
Saving requires a second consent and a native-selected directory. Existing
nonoverwrite atomic publication and cancellation/lease checks remain in use.
In-flight private previews remain within the retained encoded-byte budget after
revocation until their last holder releases them.

The demonstrated delayed metadata-clear/private-grant race is fixed by serializing
the entire metadata operation with private controls, not merely its initial RPC.
The independent regression is part of the frontend verifier. Late receipt links
bind both originating native session and scope before opening accepted evidence.
The omniscient presentation clears on lens/context change; character eligibility
and generation inputs still come from Rust. Inspection grants never teach actors.

The existing calm dark workspace and typography are preserved. Secondary raw
details start collapsed; source selection and accepted receipt are separate.
Private plaintext consent and staged-versus-durable labels remain explicit.
Opened 620px request/export text wraps rather than creating a horizontal scroll.

## Actual checks

Windows 10.0.26300, Rust/Cargo 1.93.1, Node 24.22.1/npm 11.19.1 and the existing
locked dependencies. Rust DEV/TEST debug=0, incremental=0; dedicated D-drive target
`archive-ui-native`, fresh task TEMP/TMP. Installed WebView2 includes 155.0.4283.62;
the root cohort does not independently record the loader's selected binary path.

From `apps/desktop`:

```text
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check "ui/*.{ts,tsx,html,css}" "*.{json,mjs}"
PASS, including actual-controller MOCK checks and independent ordering regression
```

From the repository root, with dedicated `$target`:

```text
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --target-dir $target
45 passed / 0 failed / 1 existing privilege-dependent ignore
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --features dev-harness --locked --offline --target-dir $target -- --test-threads=1
47 module + 2 harness-contract passes / 0 failed / 1 same ignore
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir $target models::tests::abandoned_import_reparse_file_is_preserved -- --exact --ignored
1 passed / 0 failed
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --features dev-harness --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
git diff --check
all PASS
```

The normal frontend and normal native executable were built after the native
journey. Normal frontend hook checks passed; the normal executable contains none
of `MALFORMED_SYNTHETIC_DIRECTOR`, `synthetic-private-capture` or
`LOCALLORE_D06_CAPTURE_EXPORT_ROOT`. This is compilation/source/marker evidence,
not permission to distribute a development harness build.

Actual native journey, from `apps/desktop`:

```powershell
$env:LOCALLORE_D06_CAPTURE_ARTIFACT_ROOT = '<own D output>/capture-integrated-artifacts'
$env:LOCALLORE_D06_CAPTURE_TARGET_DIR = '<own D output>/archive-ui-native'
node capture-harness.mjs
```

PASS: **73 distinct assertions, 15 app-owned PNGs, two actual process launches**.
The actual CaptureController/React/native IPC read production Play hook artifacts
from a fixed synthetic provider; fixed picker doubles select task-owned output.
No desktop input, activation, capture, system-dialog automation or CUA occurred.
This is native WebView2 rendering and IPC, not headless rendering or real-model
inference. Headless/controller checks above are a separate lane.

Clean source binding: c011bf5, `sourceDirty:false`. Local gitignored cohort:
`capture-integrated-artifacts/capture-native-f2f161f5-bc52-4566-9db7-7d9c2d8ccf9c`.
Summary SHA256:
`576eead1573fa10656a5f7bf2eae38e2a29725f3f56cb922d0a82ebf8eca9679`.
It records source/binary hashes, `actualProcessRestart:true`,
`realModelGeneration:false`, `desktopControl:false` and
`exactSavedExportVerified:true`. Saved capture bytes equal the visible preview
and manifest length/hash; only capture.json and manifest.json are present.
Initial bounded errors are one Agency and three Cancelled, all native; restart
has no errors. Both processes emit the preserved Chromium class-unregistration
1412 line at exit, with successful reports and artifact verification.

Coordinator viewed the actual opened request/export, context table, NPC lens and
restart PNGs. The 620px open-text semantic snapshots both report
`horizontalOverflow:false` and `nestedOverflow:false`; text and staged labels
are readable. Restart retains the accepted receipt while private future capture
is unconfirmed/off and no earlier attempt is reconstructed. Character lens
clears the private presentation. No desktop screenshot was taken.

Logs: `archive-ui-native/capture-integrated-{frontend,prettier,default,dev,
default-clippy,dev-clippy,harness,reparse,normal-frontend,normal-build,
normal-marker-scan}.log`. All raw synthetic traces/PNGs/exports stay local.

## Remaining gates

This slice changes no Core/Host/Store/JNI/Android bytes. Their accepted #96 cohort
already has 417 workspace passes/four qualification ignores and Android both-ABI
build/APKs, 128 JVM tests, lint and APK audit; it is historical prerequisite
compatibility, not a new Android execution for this UI. No device/emulator/ADB,
model run, offline firewall experiment or human quality review was performed.

Full D06 still needs its shared maintenance/summary interfaces and additional
real-model qualification; pause/step and rerunning generation remain unavailable.
Raw capture is bounded best effort with access-time expiry, not forensic erasure,
complete reconstruction or heap accounting. Full desktop acceptance remains open.
Next runnable integration is shared retention/schema/capacity prerequisites for
D08 timeline operations, followed by the missing production maintenance consumer.
