# Fresh-target Android receipt qualification

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). This development-only
controller qualifies the existing synthetic receipt fixture on a separately
admitted, factory-created local emulator. It adds no setup/runtime route and
does not grant model-copy, inference, phone or release qualification.

## Why a separate target

The [preceding packet](MODEL_RECEIPT_ANDROID_VERIFICATION_2026-10-24.md) passed
three Android methods and failed PROCESS at START. Its corrected service uses
fresh v2 case/proof roots, but the existing B target lacks APK staging headroom.
A separately admitted [read-only settlement](RECEIPT_CAPACITY_SETTLEMENT_2026-10-24.md)
confirmed the capacity gate. Preserve B, A, all old roots and consumed evidence.
The B controller's exact 35-package/UID rules remain unchanged.

The fresh-target controller has a different closed bootstrap: an independently
owned factory environment with no LocalLore packages, followed by only the
exact existing signed app/test APKs and newly discovered UIDs. Do not describe
it as continuation of B's identity, history, capacity or qualification.

## Environment and process ownership

Use the separately reviewed [environment contract](../runtime/android/RECEIPT_AVD_ENVIRONMENT.md)
and its separate prepare/run admissions. All persistent AVD registry,
configuration and data artifacts belong to a new create-only namespace.
Installed SDK/image use is offline preparation; this is not a blanket claim
that the emulator OS has no network access. No old AVD is resized, migrated,
cleared or used as a data template. No dependency/tool/image download,
privileged feature enablement or account operation is authorized by this test.

The environment supervisor retains its owned Windows Job through the complete
bootstrap and qualification. Its running descriptor is evidence of started
owned processes, not guest boot success. Root retains and polls the original
live execution handle; no detached or breakaway emulator is allowed. The
environment's fixed stop request and terminal job cleanup are separate from
receipt-test success. Terminating that process tree does not prove guest flush
or power-loss durability.

A fresh immutable qualification proposal binds the environment proposal,
running-descriptor SHA, environment/controller sources, SDK client and exact
APK/audit/source evidence. A fresh matching root authorization is required.
No import or disabled proposal performs device work. The source-bound live
lease validates frozen inputs on opening and checks exact process identities,
creation times, deadline, pinned metadata and stop/result absence before each
device dispatch. It must also be checked after a client returns. Unknown owner
state stops further calls; a serial, name, state file or open port alone cannot
establish ownership.

The only target serial, AVD name and client binary come from the pinned live
environment descriptor. No alternate serial, old-emulator fallback or arbitrary
shell surface is accepted. Confirm actual guest identity with the fixed AVD
name command, boot completion, API35, x86_64 and 4096-byte pages. Startup retries
are bounded and retain every actual client result; uncertain cleanup ends the
cohort. The owner budget does not extend the qualification worker's own limits.

The console name response accepts only the expected lease-derived name and
`OK`, with consistent LF, CRLF or the observed Windows CRCRLF delimiters. Mixed
delimiters, extra bytes and foreign names refuse. This command-specific parser
does not change shared shell/proof normalization or the existing B controller.

## Empty-to-two bootstrap

Before installing, require an empty LocalLore package/UID inventory and no
LocalLore processes on the fresh target. Observe exactly one mounted public
volume; actual app selection still requires the unchanged Context-derived
removable-files volume policy. Configured disk sizes do not prove guest space.

Validate both bounded actual APK lengths and pinned hashes before the first
install. Require incoming pair bytes above the unchanged 1,207,959,552-byte
controller userdata floor; this remains a necessary lower bound, not calibrated
installer-overhead sufficiency. Host and device floors remain unchanged.
Install only the exact `.modelvolumeverify` app/test pair. Record their actual
new bounded distinct UIDs, exact package hashes and quiet process state. Never
project B's UIDs into the new target or adopt another package. Recheck the
original capacity floor after installs. Any mismatch preserves the new state
and stops before instrumentation; no repair, clear, uninstall or cleanup retry.

Require the fixed v2 proof namespace and internal default candidate root to be
absent after install. The app fixture independently derives and checks its
current candidate/case paths through trusted Context and volume admission.
The controller cannot select filesystem paths for that fixture.

## Existing four-method proof

Run one ordinary class-selected instrumentation command for
`org.locallore.app.ReceiptVolumeQualificationTest`, without per-test process
orchestrators. Qualification requires exactly four passes and no failures.
The unchanged closed runner/proof parsers from the B controller remain the
shared interpretation contract; a client exit code zero is insufficient.

Read exactly the eight regular, nonlink files under the fixed v2 proof root,
with bounded JSON and empty ready markers, expected phase/check maps, 63-byte
size/digest, false SDK/publication flags and true candidate-absence assertions.
All four proofs must have one historical parent identity matching the new app
UID. PROCESS must record a distinct child PID with the same app UID. That proof
must follow the actual held-lock, binding-release, child-death, lock-reacquisition
and source-free accepted-hash assertions in the existing instrumentation.
Proof PIDs need not remain alive when the controller reads them.

Final observations require only the exact two package hashes/new UIDs, quiet
owned processes, unchanged observed volume identity and retained capacity
floors. The cohort invokes no SDK inference, native publication, Rust engine or
canonical workspace. No force-stop, clear, uninstall, model transfer, old-root
cleanup or AVD lifecycle command belongs to this controller.

## Evidence and limits

Use a source-bound stdin-barrier worker, a bounded outer owned process, a
separate aggregate deadline and bounded individual clients. Force raw stdout
before interpretation, retain byte counts/hashes/status/cleanup for every
client, and stop on persistence or ownership uncertainty. Create-only evidence
and admissions cannot be reused. Root must consume each original terminal and
separately close the environment owner; observation timeout is not completion.

Mocks establish controller behavior only. Actual boot, capacity, package
installation, four passing methods, proof checks and final process/resource
observations are required before reporting success. Even such a pass would
qualify only this synthetic emulator slice. Real model/SDK behavior, physical
phone, ARM64/16 KiB execution, media replacement, power loss, confidentiality,
model quality and sustained runtime remain separate gates. Summaries and
diagnostic records never become canonical story authority.
