# Combined Story Record test binding

Refs #14 (M10.02) and #13 (M09.04–M09.06). The model-free archive
verification APKs built at
[#455, commit `25ab2e9a`](https://github.com/OptimumAF/LocalLore/tree/25ab2e9a3cd201bae4765efc3c705df185921f61)
have the package names `org.locallore.app.archiveverify` and
`org.locallore.app.archiveverify.test`.

`benchmarks.combined_record_ui_binding` fixes the build receipt and both APK
bindings by path, length, and SHA-256. It also checks the exact pair audit,
including package names, signer and APK digests. The host receipt must agree
with the twelve ordered selectors. These consist of five cancellation cases,
three stale-action cases, one larger-text case, and three scroll cases.

From a physical D: checkout with the original retained artifacts, verify the
binding locally:

```powershell
python -I -S -B -c "import sys; sys.path.insert(0, '.'); from benchmarks import combined_record_ui_binding as b; b.verify_artifacts(b.artifact_bindings())"
```

The selector policy returns the exact single-method AndroidJUnitRunner
arguments accepted by the existing owned-target wire. The same selector
must appear in a complete JUnit start/pass sequence. Untrusted runner output
passes through the shared bounded evidence parser.

## Owned SDK21 controller

`combined_record_ui_controller.run(admission_binding, running_binding)`
requires the SDK21 admission and running records for an independently owned
API 35 x86_64 guest. The controller has a 1,200-second deadline, with up to
120 seconds for boot checks and up to 90 seconds per test, limited by the
remaining time. The outer supervisor owns process lifetime and guest closure.

The controller checks the empty isolated install, stages and hashes the exact
APK pair, and verifies package paths, hashes, and distinct UIDs before and
after the twelve tests. Each instrumentation command consumes one existing
owned-wire claim. The result retains the ordered client bindings and records
whether the observer closed its handles.

`verify_controller_result` requires the outer supervisor's independently
observed caller. It replays the same command sequence from the closed capture
and validates each raw JUnit result and socket proof. Partial runs, extra or
reordered commands, and uncertain observer cleanup cannot qualify a result.
Guest and private ADB closure still require the outer operation's proof.

The SDK21 modules provide an observer and controller for an existing target.
The approved preparation and boot handoff remains a separate step. Live
readiness and applicable human approval are required before preparation.
Existing frozen profiles keep their original artifacts and selectors.
