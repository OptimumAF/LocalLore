# Retained-parent deletion UI qualification

Supporting M10.02/M08.05/M08.01, stacked on draft/unmerged PR #208.
This defines a test, not an executed result or milestone acceptance.
The existing production MainActivity, deletion dialog/controller and typed
NativeArchive APIs remain the path under test. Kotlin does not decide retention.

## Original fixture and actual UI

Use the isolated input-process debug product, API35/x86_64 owned guest and
existing deterministic scripted provider. No model or phone result follows.
Append only new original synthetic stories to the Context-derived product
workspace; preserve earlier test stories. Seed through existing typed Rust
workspace/fork APIs, never SQL, a replacement gateway or a custom database path.
Close raw fixture owners before launching the real MainActivity.

The fixture has root1, nonroot parent P with inherited ROOT and PREFIX at2,
retained child G forked at2, and an unreachable parent TAIL at P3. Full eligible
player/receipt views and catalog records are captured through existing native
APIs. Claims remain statements, not grants of world truth. Do not individually
retire a root. [ADR-0009](../adr/0009-retained-parent-deletion.md) and the
[retention contract](PARENT_RETENTION_CONTRACT.md) still apply.

The only selected class is `RetainedParentDeletionUiTest`, with two fixed methods:

1. `cancelThenConfirmRetainedParentDeletionPreservesChildHistory`: select P
   through the real saved-story/timeline UI, display its captured native preview,
   and cancel through the dialog. Require unchanged native catalog/root/P3/G2
   views and receipts. Cancellation may reconcile to the default root; explicitly
   reselect P before opening a new preview. Click the actual rendered confirmation
   button once. Require the native completion/retention result, public P refusal,
   unchanged root/G2 eligible history and original receipt scopes without TAIL.
   Close and refresh, require P unavailable and explicitly select retained G2.
2. `staleParentPreviewCannotDeleteChangedHistory`: capture the real P3 preview,
   advance only P to4 through an independent typed native writer, and capture the
   complete post-writer native baseline. Click the old rendered confirmation once.
   Require the fixed Stale notice, no prepared confirmation/deleted result, and
   exact post-writer catalog/root/P4/G2 equality. Close, explicitly reselect P,
   and require a new preview at4; cancel it without automatic retry or deletion.

Direct controller callbacks cannot substitute for the Compose button wiring.
Native raw-handle closure does not establish that the app adapter's asynchronous
close request is a joined drain. No OS process-death, power-loss, full hidden-world
equality or forensic-erasure claim belongs to these two methods.

## Fixed host boundary

`android_process_verification.py retained-ui` uses the existing fresh build,
tool/server/source pins, original raw-before-validation capture, primary user0,
live owned guest lease and fresh absence of all three product/test/controller
packages before installation. No used external fixture is adopted.

```powershell
python -I -B benchmarks/android_process_verification.py retained-ui --out "$evidence/retained-ui" --sdk "$sdk" --powershell "$powershell" --build "$evidence/build/result-v1.json" --proposal "$runProposal" --running "$runningReceipt" --server "$evidence/server/server-v1.json"
```

The closed result is `retained_ui-v1.json`, version1, phase `retained-ui`, exactly
one class/two source-pinned methods, clean clients, method_count2 and
external_controller_case_executedfalse. It requires original complete runner
start/pass pairs, successful footer, exact ordered numbered class-client copies,
and all ancillary client schemas/bytes/hashes/cleanup. The ordinary
`instrument-user` row is fully checked but cannot masquerade as a class copy.
Skips, extra/missing/duplicate/foreign methods, altered raw output or uncertain
ownership refuse success. There is no class, method or alternate-profile option.

The native component10 and broad89 rosters/results remain distinct and frozen;
neither accepts this new result. The existing850-second SDK session,900-second
owner and180-second/262144-byte instrumentation-client bounds remain. Close only
the owned guest through its proposal-bound stop after clients are terminal.

Record exact executed source maps, APK identities, original failures and private
recovery hashes in a dated report and tickets before claiming qualification.
