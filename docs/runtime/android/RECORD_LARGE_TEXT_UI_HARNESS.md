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
a 30-minute guest ceiling. `record_large_text_ui_activation.py` consumes the
prepared guest's approved run records from the fixed SDK19 runtime folder.
It checks the canonical preparation result and its reserved ledger entry
before dispatch. The existing Windows Job supervisor bounds the activation
worker to 1,800 seconds and the separate controller child to 1,200 seconds.
The worker binds the child identities and capture receipts, then publishes
one guarded stop after the controller's terminal state is known.

Qualification requires the original owner's known exit, exact worker proof
replay, matching guest closure in the schema-2 ledger, and replay of the
controller against its independently observed caller. An incomplete receipt
or uncertain cleanup keeps the attempt unqualified. Storage transitions are
owned by the existing guard.

`record_large_text_ui_operation.py` joins guarded preparation and activation
under a 2,400-second Windows Job. Its fixed operation directory holds the
reviewed proposal, bound plan and explicit approval record. The plan pins
the preparation proposal, Python, installed inputs, sources and artifacts.
The reviewed proposal includes one line each for `Plan SHA-256 <hex>` and
`Ledger SHA-256 <hex>`. The approval binds those exact plan and ledger pins.
The operator creates a single attempt record before starting its worker, which checks
readiness and calls the current guarded preparation. The shared storage
guard still makes the fresh locked admission decision. A spent attempt
keeps its records and any storage charge. The operator grants only the
derived prepare and run records needed for this approved attempt.

Qualification requires known outer job cleanup and an exact join to the
activation and ledger closure. Before an actual run, freeze and review the
SDK19 plan, qualify current readiness, and obtain approval for that exact
operation under the [shared storage guard](RECEIPT_AVD_STORAGE.md).
The Android layout and touch results and separate screen-reader checks are pending.

## Host readiness before approval

After freezing the installed-tool and preparation bindings and the SDK19
plan at the fixed operation paths, inspect the exact plan from the same
physical D: source directory that would execute it.

```powershell
python -I -S -B scripts/inspect_record_large_text_ui_readiness.py --plan-sha256 <plan-sha256>
```

The Windows inspector requires the authority and attempt paths to be absent.
It uses the same byte, ledger, resource and temporary loopback bind checks as
the operation. It repeats the source, APK, plan, preparation and ledger
bindings before it publishes its create-only advisory report. It retains a
finite refusal category if a check fails. The report is private local evidence
under the fixed SDK19 readiness directory. It grants no admission. Actual
execution still requires the reviewed proposal, exact human approval and fresh
guard checks.
