# Public archive APK audit and check selection — 2026-10-30

Refs #14 (M10.03 supporting implementation). This packet is stacked on
open/unmerged [PR #284](https://github.com/OptimumAF/LocalLore/pull/284) at
`d16e577078342c3fc693b03d8772cca139cf7ed8`. Full M10.03 acceptance remains open.
No phone, ADB service, guest, model, installation or system setting is operated.

## Behavior and scope

The existing archive profile could pass the pure manifest auditor but had no
public audit selector. The standard Android checker also always selected the
ordinary output path/package. Both public commands now accept explicit
`--archive-verification`. The audit selects exactly
`org.locallore.app.archiveverify`; all seven existing model/input options are
incompatible and refuse before ZIP/AAPT work. No arbitrary package selector,
prefix matching, relaxed policy or implicit fallback is added.

`check.py android --archive-verification` adds only the existing Gradle property
`-PlocalLoreArchiveVerification=true`, selects the existing
`build-archive-verification` product APK, and forwards the audit flag. Default
three-argument `android_commands` callers and ordinary command vectors remain
valid. `host --archive-verification` refuses before creating a work directory or
starting checks. The existing ZIP, SDK, manifest, backup and receipt-service
policies remain unchanged. There are no app, Rust, runtime or dependency changes.

See [the shared check instructions](../ci/CHECKS.md) for reproducible commands.
The standard Android plan is unit-tested here; a new Gradle build is **not**
executed. Actual artifact verification runs the new public audit CLI against
the preserved B17 product APK, with its original build attribution retained.

## Independent original tests

Eight original methods were committed at `ab817ee3` before candidate inspection.
An unrun follow-up removes an unpromised ZIP-entry ordering assumption.
The first actual baseline at `dacef093` executes eight methods with twelve
assertion failures, zero errors/skips. Counts include LF/CRLF and malformed
metadata subcases; this is not twelve separate test methods. Unsupported
archive arguments and the absent planner parameter are the witnesses, not a
claim the old parser accepted unsafe APKs. Normal/default, unknown-argument and
early-refusal controls pass.

Root then finds a Windows-only fixture directory in the new test. Commit
`3461dda4` changes only fixture temp selection to the process-selected directory
and removes its D-drive assertion; all eight behavioral method ASTs remain
identical. The candidate diff was read after the first baseline, before that
Root-requested fixture-only correction; it was not used to change assertions.
The corrected portable original file remains unchanged for RED and GREEN,
SHA-256 `968bb44d77ee13c6ea0aebeafd36ffc250645e049388104ed0502611828b03fd`.

Its actual old-production baseline again executes **8 methods / 12 assertion
failures / 0 errors/skips**, with the same controls. Result SHA-256:
`57a41335cbeb33b313d4371437274d8e0c42857ef2d81b17ea706284d5451771`.
Both baselines, source commits and temporary fixture records remain preserved.

## Fixed verification

Executed source is `3f33c3d5f080a942bc6c52f5f4352f24545e225c`, 2,295 tracked raw
files. Production integration changes only two command-entry files (21 lines
added, five removed); existing pure auditor functions are unchanged.

The actual focused cohort executes **53 unique methods, 0 failures/errors/skips**:
31 existing APK tests, eight backup tests, four backup edge cases, two archive
manifest tests and the eight unchanged portable originals. The positive LF and
CRLF CLI cases reach actual pure ZIP/manifest/backup validators with synthetic
AAPT output. Eight unsafe metadata variants refuse through policy, seven mixed
options refuse before ZIP/AAPT, and default command vectors remain exact for all
offline/clean combinations. Owner 1,976 ms / worker 0, complete capture/cleanup;
all 2,295 source pins remain stable. Result SHA-256:
`19e786b7024887278bee576f8dd7d609849fc0699bcfb58283de122d8c0058ca`.
Independent production/CI-document review finds no concrete unresolved gap.

The complete existing `scripts.tests.test_check` suite also executes unchanged:
**17 unique methods, 0 failures/errors/skips**. Four pinned Cargo 1.93.1
`metadata --no-deps --locked --offline` calls (root, desktop and two standalone
manifests) and Python `check.py --help` all return 0. This is manifest/command
verification, not Rust compilation, native tests or an Android build.
Owner 2,590 ms / worker 0, complete capture/cleanup, all 2,295 source and tool
pins stable. Result SHA-256:
`5ecc0a9327a5706acf8868767f128f2d147fc64e61af3949f6cbeae3efb4abcc`.
The two disjoint cohorts total 70 passing methods; no full Python-suite claim.

Its first private runner incorrectly expected the Windows subprocess audit
event to contain an argument list. It captures 17 methods / two harness errors,
then refuses its own Git postflight; it is retained as a runner failure, not a
product regression. The corrected runner accepts only the same eight exact
command vectors represented with Python's Windows `list2cmdline`, keeping tests,
arguments, tool restrictions and budgets unchanged. Actual test-requested tool
output is labelled decoded/newline-normalized API output (`text=True`); suite
streams are separately captured raw. The existing tests create only the
authorized empty ignored `target/checks` directory, retained in place.

The actual public CLI then runs three fixed commands in one 90-second owned
job, using the unchanged B17 product APK (27,739,312 bytes, SHA-256
`7ac3c6f9471ccc89975e5ad3d342e5028377895eb67723d2ea0294f80b3e9608`)
and byte-pinned installed Build Tools 35.0.0 AAPT2:

| Case | Actual result |
| --- | --- |
| APK with `--archive-verification` | Exit 0; JSON has exactly status, permissions and four native-library records, equal to the original B17 audit. |
| Same archive APK without a profile flag | Exit 1, exactly `APK audit failed: Wrong app package`. |
| Absent APK with archive + LiteRT flags | Exit 1, exactly `APK audit failed: Archive verification is a separate profile`. |

Every command has complete raw stdout/stderr, no timeout/overflow, and empty
stderr. The owner passes in 13,246 ms, worker 0, complete cleanup/capture and
empty owner streams. This is one enclosing timing, not per-command latency or
a device benchmark. Result SHA-256:
`be405fc88c5ac5a4f8d76be1c29f5aeec348d00368e7a04881df3333c3a4fce0`.
The absent-path control combines actual refusal with source ordering and
mocked-call assertions; no OS-level file-open trace is claimed. Individual
internal AAPT outputs are not separately exported by the public CLI.

All 2,295 current source hashes, APK/tool pins and 673 original app/native/profile
inputs remain unchanged before/after. The APK remains attributed to B17
`84e9bfce`; no rebuilt APK, JVM run, Android instrumentation or model result is
substituted. Root independently joins all 70 actual test IDs, both suites' and
the CLI's source maps, and every current original/source-ZIP member. Its first
readback compares full-pin and SHA-only schemas incorrectly; that refused
checker is retained. Corrected schema handling keeps exact path/size/hash
checks and passes without rerunning any test or SDK command.

## Source and retention

The exact executed raw-source ZIP contains 2,295 members / 31,970,134 raw bytes,
10,237,036 compressed bytes, SHA-256
`e61807a5778b0ec596d2b11d21174a2a75129a998dff64d48e49f03d4c7cd85f`.
Manifest SHA-256:
`41d50d40c302f5addf585e14684d9fac011953b80708f30cdc59001f90255397`.
Every original/member matches the actual focused-suite before/after source map;
the declared build-input prefix has 997 entries. This preserves raw checkout
bytes, separately from normalized Git history and later report-only changes.

Private scripts, original/fixed captures and source archive remain at
`D:\Dev\Experiments\LocalLore\2026-10-30-archive-audit-cli-v1`. Selected verified
recovery uses the matching `D:\Dev\Recovery\LocalLore` root; exact seals and
independent readback belong in the final ticket handoff. The packet's original
cap is 512 MiB, including three new source trees, temporary growth, captures and
recovery. Prior B17 artifacts/recovery stay read-only and are not duplicated.
There is no cache, guest, source or recovery deletion.

No passing CLI audit or command-plan test proves a fresh Android build, device
execution, offline gameplay, outbound-traffic absence, model quality, ARM64
execution or full M10.03 acceptance. The previous three Compose methods remain
unrun on Android. No merge/release, SDK/model download or access change occurs.

Next runnable host work is M10.03's instrumentation APK pairing gate: the
standard checker currently assembles both APKs but audits only the product.
Expose exact test runner/target/permission and signer-pair verification through
the public checker, reusing the preserved app/test pair with original negative
fixtures. This is separate from actually running the three Compose journeys,
which still requires approved Android target admission.
