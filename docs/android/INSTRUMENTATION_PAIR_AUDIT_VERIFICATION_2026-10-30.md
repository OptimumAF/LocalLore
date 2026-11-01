# Public instrumentation APK pairing gate — 2026-10-30

Refs #14 (M10.03 supporting implementation). Stacked on unmerged
[PR #285](https://github.com/OptimumAF/LocalLore/pull/285) at
`cbc5f458fb64a5fda29fd384f8ae26a2bf8af0b8`. Full M10.03 acceptance stays open.
No Android target, service, guest, model or system setting is operated here.

## Resulting behavior

The standard Android checker previously built both APKs but audited only the
product. It now preserves the build/product-audit command prefix and appends
`audit_instrumentation_apk.py APP TEST [--archive-verification]` as its third
command. Ordinary and archive output paths are explicit; no arbitrary package
selector or model/input mode is introduced. A failed pair check fails the gate.

The new paired audit verifies the exact package/SDK/runner/target contract, test
permissions, existing closed test activity/provider inventory, no shared/aliased
identity or test-application overrides, distinct stable APK bytes, product ZIP
policy and one matching verified signer. Full product backup-rule validation
remains in the preceding product audit. Pairing does not prove a trusted release
publisher, test execution, or general hostile-APK safety.

The phone auditor's test-manifest block is extracted into a shared pure helper.
Independent AST comparison confirms the old block after only fixed package-role
binding substitutions; the legacy phone entry point and other checks remain.
Its optional explicit Java argument preserves the old two-argument requirement;
the new checker uses the existing Java selection (`JAVA_HOME` or PATH), without
environment changes or installation. No new dependency, profile, app, Rust,
gameplay predicate or model capability is added.

Signature checks reuse the existing SDK/JDK and only
`apksigner verify --verbose --print-certs`. The current
[official command reference](https://developer.android.com/tools/apksigner)
distinguishes verification from signing. No private key is read/generated, no APK is
signed or modified. Policy failures expose only bounded existing messages;
unexpected I/O/value failures retain a generic error category. See
[shared check instructions](../ci/CHECKS.md) for commands and prerequisites.

## Original tests and actual failure

Original tests were committed at `dab1f909` before candidate inspection; the
separate Java-PATH compatibility refinement at `d641b81a` adds a thirteenth
method while preserving the first twelve behavioral ASTs. The final original
file stays unchanged throughout RED and GREEN, SHA-256:
`6b18ecac467587e312c49c1652278e41bc2fb30b95fdcf3b279ab142a3540bb3`.

On old production, **13 methods / 51 assertion failures / 0 errors/skips**:
42 missing-module assertions and nine missing-third-command assertions, including
subcases. These are feature-absence witnesses, not claims the old policy
accepted unsafe APKs. The old phone-manifest positive control reaches its
existing validator and passes. Baseline result SHA-256:
`718aff88f5c0c6c94b9feebd2dc9d9aae698c47bb5b1b3d8e023e3435d642682`.

The integrated initial candidate then runs all thirteen methods with **one
genuine failure**, zero errors/skips: application-level `taskAffinity` is
accepted. All other controls pass. Actual owner 566 ms / worker 1, complete
capture/cleanup, 2,298 raw source pins stable. Candidate result SHA-256:
`503ce63bf77d05c39e0a962cb38186413c5db71a3f181ecfa3cffad41c9a700e`.

The fix adds only `taskAffinity` to the rejected application-override tuple.
No original assertion changes. Separately, two older command-plan tests are
intentionally extended for the third check: every previous build/product prefix
assertion remains, and new pair-vector/count assertions are added. They are not
described as byte-identical old tests. Original candidate, diagnostics-only
follow-up and failed captures remain preserved.

## Fixed host evidence

Executed checkpoint `fdcc5aaa672d4b2d454ae3fe8556311465afedf9` has 2,298 tracked
raw files. The focused mock-only cohort runs **91 unique methods, zero
failures/errors/skips**: APK31, backup8, backup edges4, archive manifest2,
archive CLI8, legacy physical audit25, original pair13. It covers normal/archive
LF/CRLF, package/SDK/runner/permission/component errors, provider namespaces and
grants, real certificate parsing with fake tool output, signer errors, changed
APK bytes, identical files, Java PATH compatibility and legacy behavior.
The unchanged task-affinity negative now passes. Owner 2,483 ms / worker 0,
complete capture/cleanup, all source pins stable. Result SHA-256:
`1160610b118e8e7f2bee039e6d55c38e141820d586f12a3614d219b3b330c941`.

The complete existing checker cohort also passes **17 unique methods**, zero
failures/errors/skips. Sixteen methods are unchanged; the seventeenth retains
the original two vectors and checks the new third command. Four pinned Cargo
1.93.1 metadata calls and Python `check.py --help` all return zero. No compilation
or native product execution occurs. Tool-requested text output is labelled
decoded/newline-normalized API capture; raw suite streams remain separate.
Owner 2,489 ms / worker 0 with known capture/cleanup; source/tool pins stable.
Result SHA-256:
`0519c24d2d670aadd68eccf1d9f4a0e15ee027d591a9cba471a88523b213f4ff`.
These disjoint cohorts total **108 methods**, not the complete Python suite.
The authorized empty ignored `target/checks` directory remains retained.

## Actual public paired command

One 90-second owned capture runs the new public command against the preserved
B17 archive app/test APKs; both retain their original `84e9bfce` build attribution.

| Case | Actual result |
| --- | --- |
| Archive app + test, explicit archive flag | Exit 0; exact seven-key success data includes expected packages, REORDER_TASKS, matching certificate and both original byte/hash identities. |
| Same pair, no archive flag | Exit 1; exact failed JSON reason `Wrong manifest package`. |
| Product path supplied twice | Exit 1; exact failed JSON reason `Invalid APK pair`. |

The actual owner passes in **13,801 ms**, worker 0, complete capture/cleanup,
empty owner streams. All three case records have complete raw output, no
timeout/overflow and empty stderr. Result SHA-256:
`73a790b0a98b9cf3059814f2c33c7752c167b377481df5e0234e5ce2eca555be`.
Four AAPT and two signature-verification calls are source-inferred, not separate
per-call receipts or timings. The early refusal control is supported by source,
unit call spies and actual output, not an OS-level process/file-open trace.

The product remains 27,739,312 bytes,
SHA-256 `7ac3c6f9471ccc89975e5ad3d342e5028377895eb67723d2ea0294f80b3e9608`;
the test APK remains 2,200,091 bytes,
SHA-256 `29955f526518dc034fbcaad250bee95e6c6211ea8d9e70838cc91d4bf515346a`.
All 673 app/native/profile inputs and all current source, APK, Java, AAPT and
apksigner JAR pins match before/after. Root independently replays all 108 unique
IDs, both suites'/CLI source maps and every source-ZIP/current-original member.
No new APK, JVM, Gradle or Android instrumentation run is claimed; the new
standard three-command build plan is unit-tested, not executed end to end here.

## Retention and remaining gates

Exact raw executed-source archive: 2,298 members / 32,005,341 raw bytes,
10,249,324 compressed bytes, SHA-256
`abcfce3ea2c238caca941d96ef240be007c2163d7d6de158a1650c1f15c5ce8f`.
Manifest SHA-256:
`5f22262dae516484fcf6ee9330c6d056eb5aa689d03e8dd8331bd01ab6114e0e`.
The declared build-input prefix has 999 entries; raw checkout bytes are retained
separately from canonical Git history and the later report-only change.

Original scripts, source archive and baseline/candidate/fixed captures stay at
`D:\Dev\Experiments\LocalLore\2026-10-30-test-apk-pair-v1`. Selected verified
recovery uses the matching `D:\Dev\Recovery\LocalLore` root; final ticket
handoff records exact seals, independent readback and measured scope totals.
The original 512 MiB packet cap includes three source trees, captures, recovery
and an explicit 32 MiB temporary-growth allowance. No prior APK, global cache,
guest, source or recovery is duplicated, deleted or retired. Generated/temporary
originals remain in place; no backup of every ignored byte is claimed.

M10.03 supporting work is in review; full criteria and owner acceptance remain
open. Android/UI, physical/model/ARM64, offline-play and outbound-traffic gates
remain separate. No phone discovery, emulator stop, system setting, access,
merge or release operation occurs. The next runnable host task is to execute
the standard Android checker end to end with the new pair gate, under a fresh
bounded build/storage packet; current compiled UI journeys still need separately
approved Android target admission.
