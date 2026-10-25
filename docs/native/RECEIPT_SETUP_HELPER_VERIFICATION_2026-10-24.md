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

## Actual environment and stopped guest attempt

The unchanged installed-image-only environment helper uses JBR 17.0.6,
emulator 35.3.12/build12990079, platform-tools37.0.1 and API35 Google APIs
x86_64 image9/ext13. The separate create-only root requests 12 GiB userdata,
8 GiB SD, 2 GiB RAM and two CPUs. Root/reviewer independently checked all 909
inputs plus preserved registry/token metadata. No token contents are printed
or copied. This packet introduces no runtime or model dependency.

Prepare proposal SHA-256:
`043e337ba0d8477ff071b93129c39340d4f8827ea4eabb6e6b0ba951d4ad1429`.
Preparation completed0 with known child cleanup and preservation closure;
original execution93300 was consumed terminal0. The SDK child took4,344ms,
stdout87 bytes SHA-256
`f8a408665fb80180169a6ef44d3f071b0da14c493f2dabc40e26871ce45952c8`.
The exact separate RUN proposal SHA-256 is
`980b312ee187c3878988ef3ed2123fa8a5765d14cc7598db519886c9b5aa3513`.
The supervisor announced its live descriptor, which explicitly is not boot
proof. Root and reviewer separately validated the actual live lease before
guest authorization. The reviewer's first read-only invocation used an old
worktree import context and refused; its corrected central-source invocation
passed. Neither reviewer invocation made a device call.

The guest proposal binds frozen source `058c796560a433f585e7632d74397bf4ac5ff366`,
the exact APK pair and 48 inputs/86,158,025 bytes. Its SHA-256 is
`7f77564f0d80f7e065a98c63c5709a65a5c353101fed73ecd0e8f7bfac3df9c2`.
The source snapshot contains1,421 files/16,755,487 bytes; index SHA-256
`cf0a678e3ea797ebba8ad0303b3be73a353c081de79229979a495f61809b9c5d`.
Both final-source/artifact flags are true in that proposal; device calls stay
false/root-go pending until its separate exact four-key root authorization.

```text
python -B -E benchmarks/receipt_avd_environment.py run --proposal <new-run-proposal> --authorization <exact-run-authorization>
python -B -E benchmarks/receipt_setup_qualification.py run --proposal <new-guest-proposal> --authorization <exact-guest-authorization> --evidence <new-device-root>
```

Guest identity observations passed API35/x86_64/4096-byte pages and fresh empty
LocalLore packages/processes. Initial userdata availability was11,610,693,632
bytes. Two exact APK installs completed, followed by distinct installed UIDs,
exact APK hashes, the same single public volume and empty APP/TEST inventories.
Installed userdata availability was 11,510,231,040 bytes. This does
not establish final capacity or a model import.

Client28 started `importsAndRechecksThroughActualReceiptSetup` but completed255
with only the runner's first-method START, no completion/result. All28 clients
have known cleanup. The386-byte runner stdout SHA-256 is
`48d997addc4e53aead1474d66fcddddeee7cbd98212c1e88104d1289d6761baa`.
The worker stopped at instrumentation: completed2/known cleanup,73,265ms,
stdout355 bytes SHA-256
`52b689d0cb08ded5316231dfa74c2ccf5e1c34cc1885855d4b4469360fe2b63f`,
stderr0. Original guest84719 was consumed with outer terminal1. There is no
completed method, helper binding, restart, proof read or44-check result in this
attempt. The prior three passes are historical, not adopted into this cohort.

The original supervisor31624 subsequently became unavailable to the execution
tool. Its three recorded host process IDs were absent, without owner stdout,
stderr or a final owner-result. No known supervisor terminal, descendant-cleanup
or orderly closure is claimed. No cause for the runner255 or host-owner loss is
established. A separately proposed four-client read-only crash diagnostic was
left disabled and unrun after owner loss; its authorization remains absent.
The dead supervisor was not recreated and no stop receipt was fabricated.
Post-loss host preservation checks are recorded separately below.

The separate post-loss check completed with original execution95279 terminal0:
installation bindings, preserved external/default registry and token metadata,
prepared config/immutable inputs, and free owned ports all pass. All three
recorded host identities are absent. These observations do not reconstruct a
missing supervisor terminal result or prove cleanup of its entire descendant
tree. Saved disks remain retained; only their size/time metadata was captured,
without a full disk hash, integrity, orderly guest flush or power-loss claim.

Private raw evidence belongs in the new `D:/LocalLore-receipt-helper-` host,
environment, device and AVD namespaces. Preserve all earlier targets and stopped
attempts. No private diagnostics or model weights are uploaded.

All 48 admitted guest inputs were archived create-only and rehashed. Their
index SHA-256 is
`980e5aa2898aa8071701b494d35833df55e41e2a6314c2af0ff0f44cfb58938d`.
The final local inventories exclude the inventory file itself and retain the
disabled, unrun diagnostic proposal:

| Private inventory | Files | Bytes | Index SHA-256 |
|---|---:|---:|---|
| Host |1,430|93,974,121|`9d0a22d756aaf5d317f51d0c957d3bc39b9c52de5ab5292fbe036e1a2f88f367`|
| Environment |19|378,584|`939de1cdaa6d73767fd13733821e2c0e7b927d4aff45c81e7c765e301a4b0eba`|
| Device |117|86,225,090|`33938714a27dca1d918677bf6ee77397b62bcc91d44458c52ca75fc7e039a449`|

## Remaining gates

Require actual three initial methods plus one separate-process reopen, all eight
proof reads and 44 checks, final exact identities/capacity/process observations,
and known emulator-owner cleanup. These remain incomplete. The next runnable
prerequisite is bounded durable supervisor diagnostic capture and a loss-case
test before another separately admitted fresh qualification; no blind repeat,
old-target repair or inference follows this failure. Even success would qualify
only synthetic receipt setup. DocumentsUI delivery,
real-model import/SDK inference, reference phone, ARM64/16 KiB execution,
cache/privacy, power loss, quality and sustained behavior remain separate.
Existing A/#117/#119 holds remain unchanged.

The [independent review](RECEIPT_SETUP_HELPER_REVIEW_2026-10-24.md) rehashes every
final inventory and archived input with zero mismatches. This partial slice is
in review in [draft PR #148](https://github.com/OptimumAF/LocalLore/pull/148),
stacked on unmerged #147. Claims are released to PR review; full task acceptance
remains pending. No merge, release or repository access change was performed.
