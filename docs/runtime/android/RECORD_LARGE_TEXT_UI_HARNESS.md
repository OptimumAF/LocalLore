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

`record_large_text_ui_controller.py` accepts the bound admission and running
records for an already owned target. It waits for boot, checks API, ABI and
user, and requires both isolated packages to be absent. It stages and hashes
each APK, installs it, and checks package paths, UIDs and bytes. It runs the
single selector with a 90-second limit, validates its complete JUnit output,
then checks both installed identities again. The 1,200-second qualification
deadline covers preflight, commands and evidence verification. An outer
owned process supervisor must enforce the wall limit for an actual run.

The controller retains a create-only request, SDK19 session, raw clients and
proofs, and result under `controller-v1`. Replay requires the independent
caller and the exact admission and running records. It verifies the closed
client and proof roster and reconstructs the result from raw command output.
Unknown cleanup, interruption, incomplete JUnit output and source drift
cannot qualify a result. The controller's observer cleanup is separate from
the owner process's guest and service closure.

The intended guest root is
`D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-ui-v1/avd-v1`.
The shared contract requires API 35 x86_64, 8 GiB guest RAM, four cores and
a 30-minute guest ceiling. The next operation layer must join the controller
to guarded preparation and verify owner closure. Actual preparation and
execution require the current
[shared storage guard](RECEIPT_AVD_STORAGE.md), fresh readiness checks and
authorization for the exact operation. The Android layout and touch results
and separate screen-reader checks are pending.
