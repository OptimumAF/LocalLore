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

## Prepared-guest handoff

SDK21 uses the reviewed v2 shared ledger guard from
[PR #446](https://github.com/OptimumAF/LocalLore/pull/446). It checks the approved
ledger under the preparation lock and compares the original preparation digest
under the transition lock before retaining a prepared guest for boot.

The owner requires the fixed handoff, spent attempt, exact approval, plan, and
run admission. It joins the prepared result and scoped prepare evidence to the
same guest, verifies the fixed APKs, and checks that the v2 ledger still holds the
40 GiB preparation reservation. Parent and worker also verify the live outer
supervisor, its process job, and the launch window. Boot consumes the existing
create-only claim.

Closed replay joins the observed owner and worker records to a normal stop, known
handle and capture cleanup, and the matching v2 ledger closure. It can be used
alongside the controller's exact twelve-result replay by the outer supervisor.

## Single-use operation

The SDK21 operator takes the SHA-256 of the exact approval at the fixed
operation path. It consumes one attempt before dispatching the supervised
worker. The worker checks the source, APKs, installed tools, storage, memory,
commit headroom and unused ports. Guarded preparation compares the approved
ledger under lock before allocating the guest. The prepared result and its raw
SDK capture must bind to the observed operation worker.

The outer Windows Job bounds the operation to 2,400 seconds. Activation has
up to 1,800 seconds under that ceiling and binds its runtime and controller
processes to the approved attempt. It requests stop only through the owned
observer. Qualification requires the controller's twelve results and the
replayed owner, process and ledger closure. Refused and interrupted attempts
retain their claim and any charged reservation.

A fresh readiness check and exact approval are required before running the
operator. Earlier frozen profiles keep their own source, artifact and
authority bindings.
