# Guarded record cancellation UI profile

M10.02 `RECORD_CANCELLATION_UI_PROFILE`, supporting M09.04/M09.06.

SDK18 is an internal harness protocol version, not a new Android dependency.
This separate fixed model-free profile connects PR #387's B111 build attestor to
the existing checked owner, finite binary transport, proof replay and guarded
cleanup mechanisms. Android platform/API35, dependencies and shared mechanisms
are unchanged. Existing SDK16/SDK17 files and their frozen evidence are unchanged.

## Product and authority

Tooling parent: PR #387, `029f5dab4a60e34f4c75f270ef054e5dbe261815`.
The product remains separately frozen PR #386,
`7e29fb724ed781e953f321385f66a5f8982ad0f1`, on PR #385. Rebuilding the tooling
branch does not replace those APKs. B111's `verify_frozen_product` remains the
full source/build/artifact authority. The new `project_manifest` is only a
detached compatibility projection, not independent evidence or run consent.
`record_cancellation_ui_profile_build.verify_current(admission)` validates and
revalidates sources, calls the fixed verifier, validates exact facts/roster/APK
joins, revalidates again and returns the unchanged raw B111 object.

The closed protocols are `owned-emulator-record-cancellation-ui-v1`,
`sdk-record-cancellation-ui-v1` and `record-cancellation-ui-socket-proof-v1`.
The session is `sdk-session-v18.json`. Roles are exactly `build`, `product_apk`
and `test_apk`; model material is false. The signer is fixed from the package
audit. Selectors `record_cancel_1` through `record_cancel_5` are the five exact
`StoryRecordCancellationScreenTest` methods pinned by B111, in order; code units
are 381,536,317,518,529. No caller-supplied selector or implementation is allowed.

The fixed guest is
`D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1/avd-v1`.
The fixed runtime is
`D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-runtime-v1`.
The activation source is this packet's raw frozen candidate at
`D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/candidate-source-v1`;
its input must be the separately supplied `run-controls-v1/run-input-v1.json`
under that packet. This host packet created none of those operational paths.
Future admitted activation creates bounded owned control/capture/output
directories; the profile does not create an approval, run input, admission,
preparation proposal or prepared guest.

Current source admission has 28 required benchmark bindings, including the
additional B111 shared diagnostic reader and ledger-v2 recovery reader. The
optional `__init__.py` is absent in this snapshot. Two transitive checker sources
outside the benchmark grammar have fixed byte/hash pins. Cached decoder/base,
build/reader origins and the actual bound shared-reader alias are checked.

## Concrete operations and resources

Concrete classes are `LiveOwnedRecordCancellationUiTarget`,
`_RecordCancellationUiTargetRuntime` and `OwnedRecordCancellationUiSdkCapture`.
Subclasses and foreign leases refuse before observation or I/O. The finite grammar
permits only fixed setup, binary-safe staging, installed identity and selected
instrumentation operations. General shell, arbitrary instrumentation, `pidof`,
`am force-stop` including its valid legacy `--user 0` form, and model streaming
are denied. Kotlin and gameplay rules are unchanged.

The standalone controller completes running/source/build preflight before
creating output beneath the supplied admitted owner root. Its binary reader
reads at most pinned bytes+1, retains both binding checks and checks exact
length/hash. Each method has a 90-second ceiling inside a 1200-second controller;
one successful boot query yields exactly 30 clients and 60 proof brackets.
Additional permitted boot polls each add their own record. Complete replay
requires all ordered claims, raw instrumentation/JUnit evidence, installed
UID/path/hash before and after, and closed file/client rosters. Missing, borrowed,
reordered, extra, stale or boolean-coerced evidence refuses.

Activation retains the 1800/1700/1730-second outer/owner/parent ceilings and
1230-second caller ceiling. These are bounded orchestration parameters, not
performance results or authority. Cleanup still attempts observer closure,
stop publication when the existing known-controller/caller guard permits it,
owner wait, capture and terminal recording after faults.
Unknown closure, failed publication, interruption or zero exit alone cannot
qualify a run. A caught interruption at the final success update explicitly
revokes `passed`; later positive metadata cannot repair it.

## Qualification gates

Host fake-wire proofs execute real parsers/replay and orchestration methods with
explicitly synthetic native/process/storage observations. They are not ADB,
Android, native owner/cleanup or device results. Recorded B110 JVM425/50 and five
compiled Compose methods retain their original attribution; Android is 0/5 here.

This packet supplies no fresh preparation bridge, reservation or boot authority.
Future execution requires exact reviewed inputs, preparation/handoff integration,
current shared-ledger admission, source/Python/tool/ownership/port checks and fresh
exact approval. The unchanged limits are two unretired roots,64GiB admission and
40GiB per preparing/live guest. Pending retirement-only authority is not a boot
grant. Old spent grants do not authorize SDK18. No other emulator, shared ADB,
settings, model, guest images, canonical story data or repository acceptance is
changed by this host packet.
