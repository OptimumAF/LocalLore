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

This verification reads files. It creates no device operation, lease or
reservation. A future guarded controller must bind this policy to its
owned target, install and verify the exact isolated packages, supervise the
twelve results and verify cleanup. Live readiness and applicable human
approval are required before preparation. Existing frozen profiles keep
their original artifacts and selectors.
