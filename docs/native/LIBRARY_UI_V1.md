# Current library and recovery UI qualification profile

Refs #14 (M10.02), supporting #13 (M09.02/M09.03/M09.06).

SDK15 is a separate model-free profile for the four current library journeys
compiled by [PR #351](https://github.com/OptimumAF/LocalLore/pull/351). It uses
the current guarded recovery/owner source from
[PR #347](https://github.com/OptimumAF/LocalLore/pull/347). Neither dependency
is merged by this change. Host qualification does not establish Android
execution, physical-device results or milestone acceptance.

## Fixed product and authority

`owned_library_ui_contract.py` permits only these ordered methods of
`org.locallore.app.ui.LibraryActionScopeScreenTest`:

1. `oldRecoverCannotBorrowAnEqualFailedRetryAndFreshUnselectedRecoveryWorks`
2. `oldStoryRowsAndOpenerCannotActOnReopenedOrEqualRefreshedLibrary`
3. `oldTimelineRowCannotActOnReopenedMenuAndFreshChoiceWorks`
4. `disposedScreenRowCannotBorrowSameViewModelAfterRemount`

The ordinary app/test packages are `org.locallore.app` and
`org.locallore.app.test`. No model material, general shell operation, force-stop,
`pidof`, screenshot or caller-selected implementation/profile is admitted.
Concrete owner/client type checks remain in force. SDK15 has distinct wire,
proof, session, claim and activation identifiers; SDK14's nineteen selectors
and earlier approvals grant no SDK15 authority.

The source closure contains 25 required benchmark files, including
`prepare_recovery_contract.py`, plus the existing optional initializer rule.
Live paths revalidate the exact current bytes. Structural metadata cannot omit
the recovery dependency or select historical source as a fallback.

## Frozen build replay

`library_ui_build.create_manifest()` returns data without publishing it or
building an APK. Its literal baseline is
`D:/Worktrees/locallore-record-actions-tests-v1/benchmarks/library_ui_build_baseline.json`;
moving the reader cannot relocate that identity. The only prospective manifest
is `D:/Dev/Experiments/LocalLore/2026-11-02-library-ui-harness-v1/library-ui-build-v1.json`.

The fixed byte-attestation graph binds B80's final product source
`7ab4918fa1044d960edcb1172fe7684474eb3a89`, executed source
`8516871469f769c9363fc9189200c88a8e3a6931`, six phase chains, four source archives,
raw JVM/XML/audit evidence, preservation copies and inherited native origin.
The final product/test APK hashes are respectively
`3c355ec7568e8a6468790c417d986d413f5414f43cde2719f77a9041ea15abb6` and
`5a96cfd007e42a5eb7e739375316c2ba43263490c2cca784b35d91b83712b698`.

The original FIRST assertion failures and failed `android-v1` compile remain
failed. Its passing JVM subset, partial product and inherited older test APK
cannot qualify the final pair. Recorded B80 JVM/audit/source review is bound
by bytes; this reader does not repeat the semantic tools or execute Android.
Native outputs were up to date in B80, with separately bound historical
compilation provenance; there is no new native-compilation claim.

The product audit must contain exactly
`org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`, the existing
AndroidX signature-protected receiver permission. The separate test audit must
contain exactly `android.permission.REORDER_TASKS`. An empty list, duplicate,
extra permission or network permission refuses. This preserves the original
auditor policy; it does not add an app permission.

The existing reader limits remain 120 seconds and 512 MiB read per replay,
held-stream/path/parent identity checks, ordinary physical D: files and single
links. Only the exact two Cargo release/deps aliases may have two links, with
matching identity. Missing or changed evidence refuses; no rebuild, resealing
or older-product fallback occurs.

## Controller, activation and storage

The controller stages binary APK bytes, verifies their device hashes, installs
the exact pair and checks package paths, UIDs and hashes before and after the
four methods. Original JUnit bytes must name exactly the selected class/method
and report one successful test plus an explicit instrumentation exit. Complete
replay consumes every client and refuses extra or missing records. With one
boot poll the grammar contains 29 clients (`Nboot + 28`); setup and package
checks were not removed to reduce that count.

Deadlines stay 90 seconds per method, 1,200 controller, 1,230 caller, 1,700 owner,
1,730 parent, 1,800 outer and 400 for readiness. There is one claim per selector,
no retry or extension. Activation joins the original caller, owner, worker,
raw captures, source and controller evidence before it accepts known cleanup.
Unknown caller/cleanup, changed history or missing final storage closure
cannot become a pass. `feature_acceptance` remains false.

Fixed prospective paths:

| Role | Path |
| --- | --- |
| Source | `D:/Worktrees/locallore-record-actions-tests-v1` |
| Controls | `D:/Dev/Experiments/LocalLore/2026-11-02-library-ui-harness-v1/run-controls-v1` |
| Runtime | `D:/Dev/Experiments/LocalLore/2026-11-02-current-library-ui-run-v1` |
| Existing charged guest | `D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1` |

No new root admission is implemented. The shared production registry, two-root
limit, 64 GiB admission budget and existing 40 GiB reservation remain unchanged.
The current [recovery contract](../runtime/android/PREPARE_RECOVERY.md) must
produce known cleanup and immutable history before normal owner launch can
retain the reservation with its distinct RUN digest. That transition still
precedes the SDK15 boot claim and guest launch. Verified parent closure must
then join the original history, worker cleanup, handles, final source and
capture before storage can record closure.

SDK15 recovery metadata must be generated from the frozen SDK15 source.
The preserved Flow5907 recovery plan is bound to different source paths/bytes
and cannot be transferred. Importing this profile creates no recovery metadata,
migration or authorization. Host tests create those records only in isolated
synthetic registries; they create no production recovery metadata, production
ledger migration, live execution authorization, SDK operation or emulator.
A future operation needs a concrete reviewed proposal and fresh exact
authority for its recovery source, current APK pair and four selectors. Earlier
spent grants cannot be reused. Your other emulator and shared ADB remain outside
this profile's lifecycle authority.

## Host checks

From the physical SDK15 D: checkout, set process-local `TEMP`, `TMP` and
`TMPDIR` to `D:/Dev/_Temp`, then run:

```powershell
python -S -B -m unittest -v scripts.tests.test_library_ui_build
python -S -B -m unittest -v scripts.tests.test_library_ui_profile
python -S -B -m unittest -v scripts.tests.test_library_ui_controller
python -S -B -m unittest -v scripts.tests.test_library_ui_activation
python -S -B -m unittest -v scripts.tests.test_library_ui_recovered_storage_handoff
```

The recorded bounded driver adds isolated Python mode and explicitly inserts
the physical checkout into `sys.path` after its job-assignment barrier.
Host fixtures use tiny D: files and simulated native,
socket, SDK and build ports; the recovered-storage tests use real isolated
ledger/journal transitions. These are separate from genuine fixed build replay
and from actual Android execution. See the dated verification report for the
commands actually executed and their limits.
