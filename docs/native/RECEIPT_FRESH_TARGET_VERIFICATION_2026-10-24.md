# Fresh-emulator receipt verification - 2026-10-24

The corrected Android receipt fixture passed **four methods** on one newly
created, isolated emulator, including cancellation and recovery after owned
child-process death. All eight proof files, 43 required checks, package/UID
identities, capacity floors and final zero owned/passive app processes validated.
This is a synthetic storage prerequisite for M05.05 and supporting M01.05 work;
active setup integration, real inference and full milestone acceptance remain pending.

This packet adds development tooling: a create-only AVD helper with retained
process ownership and a separate fresh-target controller. See the
[protocol](RECEIPT_FRESH_TARGET_PROTOCOL.md),
[environment contract](../runtime/android/RECEIPT_AVD_ENVIRONMENT.md),
[capacity settlement](RECEIPT_CAPACITY_SETTLEMENT_2026-10-24.md) and
[independent review](RECEIPT_CAPACITY_REVIEW_2026-10-24.md).
The app, Rust engine, receipt implementation, active setup route and dependencies
have no code changes in this packet. The B controller remains unchanged.

## Source and versions

Execution source: `40a7f8ede02cfad9c72a57cebb59494cdd35c5b1`.
The frozen source snapshot contains 1,403 files / 16,514,752 bytes, index SHA-256
`f90ca7e8357ec6c1fe0091ae62de30b35cf36d7edffb2438af4a4cd83795639f`.
All 395 non-Markdown app/build rows match the preceding corrected APK compilation
snapshot. Only documentation changes after execution for this handoff.

Actual host: Windows, Python 3.9.12; installed emulator 35.3.12/build 12990079,
command-line tools 11.0, platform-tools 37.0.1, JBR 17.0.6. Image: Android 35 Google
APIs x86_64 revision 9, extension 13, minimum emulator 33.1.24. No installation,
download, dependency update or license acceptance occurred. The new profile
requests 12 GiB userdata / 8 GiB SD / 2 GiB RAM / two CPUs. Actual guest identity checks
confirmed API 35, x86_64 and 4,096-byte pages.

Reused, audited artifacts (no fresh APK build):

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Volume-debug app | 74,851,232 | `8232c5f81284b31d392e447968a0aa87ba853e2781fa2ae7245feaec405447f8` |
| Android test | 1,904,147 | `a8aecff0610a45384531cf55de684741e766c466487e8a95daaa65de8a596b2a` |

The preceding signature, permission, private-service, backup and native packaging
audits remain source-supported. Its 323 JVM tests/lint are historical evidence,
not reruns here. The original 63-byte fixture SHA-256 is
`648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0`.

## Actual checks

`python -B -E -m unittest discover -s scripts/tests -v` passed **537 tests**,
zero failures/errors/skips, 36.194 s. Original owned execution: completed 0,
known descendant cleanup, 36,828 ms, 61,831-byte stdout SHA-256
`b7dfc99459175815f9e55f3dfb0f5f077aeef8e364edad9f79ea3b3b163ec79f`.
This includes 52 environment tests and 14 mocked fresh-target tests, with actual
Windows descendant termination and regressions for the observed failures.

Separate `plan-prepare`/`prepare`, `plan-run`/`run`, then guest-controller `run`
admissions used immutable proposals. Root and reviewer independently verified
the inputs. Prepare binds 909 files / 5,046,134,929 B; guest binds 35 files / 86,665,208 B.

| Admission | Proposal SHA-256 |
|---|---|
| Prepare | `3c6ab58b73e0b928d8d5ebe801463da0bca6a229883b3b3c466d53a0f2d07c57` |
| Retained run | `04a49aaafe91b87809eacb0ab65bd9e8a65fced669efd07d49ab816a0015a405` |
| Guest cohort | `ca54e87f7d7bc70bf55ca3b2463617636882c25766190caeedf687ebf7bd69a8` |

Prepare's SDK child completed 0/known cleanup in 17,047 ms; stdout 87 B SHA-256
`f8a408665fb80180169a6ef44d3f071b0da14c493f2dabc40e26871ce45952c8`,
stderr 645 B. Initial SD was exactly 8,589,934,592 B; userdata was absent. Closure
verified source/tool, default-registry metadata and the existing console-token
hash. The running descriptor explicitly established no boot evidence.

The separately admitted controller executed 59 clients: boot/identity/capacity,
two fresh installs, one ordinary instrumentation class, proof reads and final
facts. Every client completed 0 with known cleanup and matching retained raw
stdout hashes/lengths. Install stderr counts were 146 / 156 B; all others zero.
Unretained stderr text is not interpreted.

Actual class selector:

```text
am instrument -w -r -e class org.locallore.app.ReceiptVolumeQualificationTest org.locallore.app.modelvolumeverify.test/androidx.test.runner.AndroidJUnitRunner
```

Runner: **4 PASS / 0 FAIL**, 37.961 s, 2,736 raw bytes SHA-256
`d9d39095014f18bd93a23436faf20452323afcea674669e545570b7080a9213a`.
Methods cover accept/reopen, cancellation across acceptance, foreign/incomplete
data refusal and recovery after owned process death. Original guest execution:
completed 0/known cleanup in 72,891 ms, stdout 306 B SHA-256
`2c199d5cdcb8aacbdbffc2073b7b467ea855925c242fd6901939d5090cc8fbde`,
outer stderr zero.

Four JSON proofs and four empty ready-marker reads validated. All 43 checks were
true, with one consistent historical parent and a distinct same-UID PROCESS
child. The process method exercised held-lock Busy, arm acknowledgement, binding
release, observed child death, lock reacquisition and source-free accepted-byte
verification. All SDK/native-publication flags were false and candidate-absence
flags true. Root and reviewer independently reparsed raw runner/proof bytes.

| Capacity observation | Available bytes |
|---|---:|
| Userdata before installs | 11,562,930,176 |
| Userdata after installs | 11,480,317,952 |
| Final userdata | 11,356,491,776 |
| Minimum proof external space before operation | 8,572,968,960 |
| Minimum proof external space after operation | 8,572,952,576 |

Unchanged floors: controller userdata 1,207,959,552 B, external proof 2,147,483,648 B.
Actual APK lengths were reserved before either install. Final APK hashes/new UIDs
and volume identity matched; owned/passive process counts were both zero.

After consuming the original guest terminal 0, root requested the exact owner stop
and consumed its original terminal 0. Owner: `stop_requested`, known cleanup and
verified closure, 215,891 ms. All three recorded process identities closed and both
owned ports were free. Source/tool/config/default-registry/token preservation
checks passed. Job drain establishes no graceful guest-flush or power-loss result.

## Preserved failures and closure

Three earlier namespaces remain retained: a generated-config `AvdId` assumption
refused after SDK creation; the next launcher rejected the Windows-capped
`-partition-size 12288` argument; then a boot-property read passed but exact
console CRCRLF framing refused before installs. Fixes validate/normalize only a
fresh config, omit the capped override while retaining 12 GiB, and accept only
exact expected console-name/OK forms. Shared/B normalization remains unchanged.
All original failures and subsequent known closures remain recorded in the
environment contract and independent review. The earlier Android three-pass/
one-PROCESS result is also preserved; its sole cause is not established.

B's read-only settlement still lacks 60,866,995 staging bytes before installer
overhead. No old data was cleared, adopted or retried. Final private inventories,
independently rehashed:

| Inventory | Files/bytes | SHA-256 |
|---|---:|---|
| Host source/tests | 1,412/16,806,099 | `cc8bdaffd557ab9e628b05467a588303c2f9b4329c796f357325f9b2e25fb6d0` |
| Environment proposals/control | 6/365,259 | `b0712c568869c627305646941109a1c6477b0b4a39a1c7d2bb651e6c134f8d91` |
| Guest/control closure | 187/86,797,683 | `e6be2845cec0b1112a6eef040fb9be07b7d28ecf0057a6111f8bef664245cb70` |

All 35 guest inputs were archived byte-for-byte; archive index SHA-256
`8f2f21320158e77d1555d5150570a9ac53124a6bf4015468e6eaa5691395a529`.
Virtual disks remain mutable retained state; final disk rows are size metadata,
without content-integrity/flush assertions. Raw identifiers/diagnostics stay private.

## Remaining gates

M05.05/M01.05 remain unchecked pending full criteria and owner acceptance. M01.01
lacks an established authorized reference phone. Phone / ARM64 / 16 KiB execution,
real-model capacity/inference, quality, sustained memory/thermal, power loss,
media replacement and confidentiality remain unqualified. A/#117/#119 holds are
unchanged. No merge, release or access change occurred.

Next runnable task: separately scoped receipt integration in the isolated debug
candidate-setup experiment, keeping canonical data internal and retaining
owner/model/storage gates, followed by actual cancellation/restart checks.
ADR-0011 and real-model provisioning need separate review and evidence.
