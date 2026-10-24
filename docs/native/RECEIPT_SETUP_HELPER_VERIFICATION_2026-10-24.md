# Receipt setup helper boundary verification - 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 support). This follow-up corrects the
test controller's process classification. App, Rust, runtime, model and native
dependencies have no implementation changes. Full milestone acceptance remains
pending; no merge or production backend selection is authorized here.

## Observation and correction

The [preceding run](RECEIPT_SETUP_VERIFICATION_2026-10-24.md) passed three initial
UI methods, then refused because the TEST APK main process remained while the
APP target was absent. Its restart method and host proof reads did not run.
That refusal and saved target remain preserved; this packet uses a new target.

The strict shared process parser remains unchanged. The new `ProcessBoundary`
requires no LocalLore process before or after installation. Only after three
exact initial passes, in the first post-initial inventory, may it bind one
TEST-main PID/UID/name under the pinned distinct TEST UID. APP, service, provider
and foreign rows still refuse. Version 2 facts record `target` and `test_helper`
separately; a surviving helper is not called quiet, passive or an SDK owner.

Later observations require the same helper or observed disappearance. After
observed disappearance the row is permanently revoked. A new, replaced or
observably reappearing helper refuses, as does a late helper after an initially
absent one. Order, stage, method count and UID maps are typed and closed; a
failure is sticky. Matching a snapshot tuple does not prove continuous liveness
or detect unobserved PID reuse. The helper grants no file/runtime authority.
The independent APP restart proof still requires its linked changed PID/start.

The [protocol](RECEIPT_SETUP_PROTOCOL.md) retains existing capacity floors,
exact APK/UID/media checks, 180/165-second worker/cohort limits, raw-before-parse
evidence, all 44 proof checks, and no force-stop, clear, reinstall, arbitrary
shell, model transfer or SDK command. Source and record parsing remain in the
same receipt engine; no canonical gameplay authority moves into this tooling.

## Actual host validation

```text
python -B -E -m unittest discover -s scripts/tests -v
```

All **579 tests passed**, zero failures/errors/skips, 54.193 seconds. The original
owned execution completed 0 with known cleanup, 54,953 ms. Its 67,403-byte stdout
SHA-256 is `24bc3812a68433b86055afc0e462afa7f11e3de7297ac5ac1c5bf914d4a63f98`.
This includes the 20 new boundary/cohort tests, plus unchanged prior controller,
APK audit and Windows process-ownership regressions.

The independent author also ran the 20 new tests: 20 PASS, zero failures,
9.093 seconds; owned completion 0/known cleanup, 9,531 ms. Stdout 2,815 bytes,
SHA-256 `8f62305d389254dd2f6825b2775f2b94c35c6b79f7d9c0282c862b28b00e1af1`.
All four source bindings remained unchanged. Tests cover real `Owner`/cohort
orchestration through mocked transports, not actual Android execution.

No new Android build is claimed. Root and reviewer independently compared all
457 relevant app/native/build/script rows, 5,975,443 bytes, against the actual
preceding compilation snapshot. They match. The reuse-index SHA-256 is
`d9234c090328b66d40037f8615a5a24ac747dd7e13234a108d00de8bf4e162de`.
The same previously audited APKs are reused:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| App |74,867,728|`983f381ed493fdbb8d8d3227a50a164cc6a89ced57cbe0cbeb6dbcefa6f828f7`|
| Android test |1,922,331|`ec35b26743ae7433d51d1d6b4abfa31db888c031d4ccea18b33cdfaa9a234428`|

Their 340-test receipt/regular SDK and 206-test ordinary builds, lint, native
packaging and capability audits are historical results linked from the preceding
report. No fresh JVM/Gradle, ARM64 or 16 KiB execution is inferred here.

## Environment and pending guest evidence

Use the unchanged installed-image-only environment helper and proven JBR 17.
The separate create-only root requests 12 GiB userdata, 8 GiB SD, 2 GiB RAM and
two CPUs. Root/reviewer independently checked all 909 inputs plus preserved
registry/token metadata. No token contents are printed or copied.

Prepare proposal SHA-256:
`043e337ba0d8477ff071b93129c39340d4f8827ea4eabb6e6b0ba951d4ad1429`.
Actual preparation/closure, boot and guest qualification results remain pending
in this draft report. A prepared environment alone is not guest evidence.

Private raw evidence belongs in the new `D:/LocalLore-receipt-helper-` host,
environment, device and AVD namespaces. Preserve all earlier targets and stopped
attempts. No private diagnostics or model weights are uploaded.

## Remaining gates

Require actual three initial methods plus one separate-process reopen, all eight
proof reads and 44 checks, final exact identities/capacity/process observations,
and known emulator-owner cleanup. No such pass is claimed before observation.
Even success would qualify only synthetic receipt setup. DocumentsUI delivery,
real-model import/SDK inference, reference phone, ARM64/16 KiB execution,
cache/privacy, power loss, quality and sustained behavior remain separate.
Existing A/#117/#119 holds remain unchanged.
