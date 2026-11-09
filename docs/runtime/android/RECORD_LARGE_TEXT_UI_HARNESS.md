# Guarded Story Record large-text profile

Refs #13 (M09.05) and #14 (supporting M10.02). The fixed SDK19 profile
connects the existing guarded target owner and v4 client and proof verifier
to the audited Story Record accessibility build from [PR #401](https://github.com/OptimumAF/LocalLore/pull/401).
It is stacked on [PR #398](https://github.com/OptimumAF/LocalLore/pull/398)
for the current shared storage and Windows commit guards.

The product is `org.locallore.app.archiveverify`. The test package is
`org.locallore.app.archiveverify.test`. The profile permits this one
instrumentation selector under `androidx.test.runner.AndroidJUnitRunner`:

```text
org.locallore.app.StoryRecordLargeTextTest#narrowRecordReflowsAtDoubleTextSizeAndKeepsActionsReachable
```

The B124 app, test APK and build attestation are three fixed local byte
bindings. Admission data must match all three roles, paths, sizes and hashes.
The parent, worker and live lease entry points recheck those files before
proceeding. The existing transport checks the staged bytes against the admitted
role. Other methods, model operations, process lookup and force-stop are
refused by the profile. The test exercises the dialog with synthetic Compose
state at standard and 2× text.

Host tests run from the profile checkout with temporary files on D:.

```powershell
python -I -S -B -c "import sys, unittest; sys.path.insert(0, '.'); unittest.main(module=None)" scripts.tests.test_record_large_text_ui_profile
```

The intended guest root is
`D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-ui-v1/avd-v1`.
The shared contract requires API 35 x86_64, 8 GiB guest RAM, four cores and
a 30-minute guest ceiling. A controller must still bind the install and
instrumentation sequence to this profile and verify the complete run evidence.
Actual preparation and execution require the current
[shared storage guard](RECEIPT_AVD_STORAGE.md), fresh readiness checks and
authorization for the exact operation. The Android layout and touch results
and separate screen-reader checks are pending.
