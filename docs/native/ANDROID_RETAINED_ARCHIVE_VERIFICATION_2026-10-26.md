# Retained-parent archive chooser verification — 2026-10-26

Supporting M08.04/M08.06/M10.02 in draft [PR #212](https://github.com/OptimumAF/LocalLore/pull/212),
stacked on draft/unmerged #210 at `6e05fc87`. Full task checkboxes remain
unchecked pending broader criteria and owner acceptance. No merge is authorized.

## Implementation and discovered prerequisite

The [fixed protocol](ANDROID_RETAINED_ARCHIVE_PROTOCOL.md) adds two original
MainActivity/DocumentsUI tests for archivev2/source schema5 with a retired parent
and retained child. Rust remains the authority. Exact export bytes, original
receipt scopes, reserved-ID refusal, child-only continuation and hostile/version/
conflict/cancel refusal are the selected assertions. The separate host phase
does not modify or substitute native10, broad89 or retained-ui2.

Review found a real prerequisite: a zero-argument confirmation retained from
preview A could use newer preview B. The same issue affected export picker and
Open imported. Three actual JVM tests failed by assertion on the unchanged API,
not by compilation/setup failure. The fix passes the exact rendered immutable
prepared/imported object through Compose/MainActivity/ShellViewModel and checks
reference identity before side effects. Equal copies and foreign objects refuse;
availability, kind, picker, generation, disposal and single-use guards remain.
No no-argument bypass remains. Native validation and commit are unchanged.

Independent ownership was explicit: Android author `05507de2`, core contract/
tests `786de966`/`40dda68d`, consent fix `37421262`; root reviewed and integrated
these into executed mapped source `f87e5900`. Later documentation-only commits
do not change the mapped input bytes. No dependency, permission, model or system
setting was introduced.

## Executed host and build checks

| Check | Actual result |
|---|---|
| Fixed driver module | 46 passed; 18.359s runner,19,269ms owner;758 unchanged inputs, clean cleanup/stderr |
| Integrated Python suite | 1,257 passed;150.816s runner,152,710ms owner;759 unchanged inputs, clean cleanup/stderr |
| Original consent API reproductions | Three executed tests, three `AssertionError` failures; zero errors/skips;99,500ms owned worker1 |
| Fixed focused JVM suite | 26 passed, zero failures/errors/skips;91,999ms owned worker0 |
| Unified Android build | Passed;293,488ms owned worker0; cleanup/capture known, owner stderr0 |
| Unified JVM reports | 244 actually executed tests across28 XML suites; zero failures/errors/skips |
| Lint and artifact checks | Both lints pass;11 product/controller/signature/badging/manifest audits pass |
| Rust archive compatibility | 24 passed:11 retention,7 archivev3,6 hostile;9,155ms owned worker0 |

The46 driver tests are included in1,257, not additive. The26 focused JVM tests
are included in244. Rust ran independently on pinned Rust/Cargo1.93.1 in an
isolated C: target. Its1,781-entry tracked map stayed unchanged; this broader
Rust map is distinct from the Android759-entry map. Initial22 and follow-up24
Rust results retain their separate original source attribution. New Rust cases
exercise legacy source schema3/4 import/reopen/current5 re-export and future6
refusal in empty and colliding-ID stores, preserving original accepted histories.

Commands, with private paths replaced by local variables:

```powershell
python -B -m unittest scripts.tests.test_android_process_verification
python -B -m unittest discover -s scripts/tests -p 'test_*.py'
cargo test --locked --offline -p locallore-storage --test branch_retention_archive --test m08_archive3 --test m08_archive3_hostile
python -I -B benchmarks/android_process_verification.py build --out "$evidence/build-v1" --sdk "$sdk" --java "$java"
```

The Python commands ran through retained private workers under the existing
bounded Windows owner. The full-suite worker uses discovery from scripts/tests;
the first private discovery attempt added an inappropriate top-level directory
and exited1 before tests (193ms,stderr622B counted, no raw stderr retained by
that helper). Its command/owner/output record is preserved, separate from the
corrected1,257-test runs. Earlier1,257-test source `d9b8851e` predates consent;
only the later integrated run above qualifies `f87e5900` mapped source.

The build driver uses offline Gradle, JDK21, two workers, explicit unit-test
cleaning, native x86_64/ARM64 cross-builds and the input-process profile. Gradle
records `testDebugUnitTest` executed, not UP-TO-DATE. Its separate251B controller
Java deprecation note is retained; it is not owner stderr. ARM64 packaging is
not ARM64 execution. Python is3.14.7; Android build tools are35.0.0.

## Source and artifact attribution

Integrated host/build maps both contain759 exact inputs, including five SQL
migrations. SHA256 of the97,498B map:
`20d0f10b5d208dcb18f56ad774b9ebc0c6fd090de4d7e6265e799721d1e33dce`.
Independent readback matched every integrated host entry to the exact Git blob
at `f87e5900`, without normalizing line endings.

| Fixed package | APK bytes | SHA256 |
|---|---:|---|
| `org.locallore.app.draftprocessverify` | 24,555,960 | `4c39700d64c3efaf874c48aad038a68d8cff2dbfb55cd4bdf00824d413d66002` |
| `org.locallore.app.draftprocessverify.test` | 2,797,406 | `399fb66dd9bbf694eac87a2410268c2b40d94fdaa574d10cda15b29fb4f717e2` |
| `org.locallore.app.draftprocesscontroller` | 54,201 | `805187cb0f28a48bfd304fdd507f5b8c8ef8bddd2fffa901ef6a9e69eae5cd96` |

Product/test APKs are new. Prior native10/broad89/UI/lifecycle records keep
their original source and APK attribution; compilation does not rerun them.

## Android execution gate

Actual native10 and retained-archive2 execution are blocked for this build.
Both isolated guest preparations refused `host_commit_capacity` at the final
resource recheck. Their original client records and stdout show that SDK
AVD creation completed first; no prepared receipt was published, no guest
booted, and no install/instrumentation ran. Both record known cleanup/closure
and `prepared_created:false`. An earlier progress comment incorrectly described
the first refusal as preceding SDK work; the original records establish this
more precise boundary.
A single read-only diagnostic during compilation found4,305,334,272B available
commit against the unchanged6,442,450,944B standard-guest requirement. This is
separate from physical RAM; the standard guest remains2GiB/two CPU, with4GiB
physical-memory floor. No requirement was lowered. After the build owner exited,
one fresh isolated preparation reached the same final commit refusal. That
distinct attempt is preserved, with no favorable polling or third attempt.
No failed/used fixture is adopted. SDK child stderr was counted by the existing
prepare helper but not retained raw; no reconstruction is claimed.

## Private preservation and limits

Raw evidence stays in the protected C: evidence directory. Sanitized findings,
original fixtures and executable checks are committed; private diagnostics,
device identifiers, stories and model weights are not uploaded.

The immediate verified recovery has130 exact files/3,897,766B, including original
RED and failed preparation records. ZIP1,407,316B SHA256
`039c577c2bff3786f09538bb98d0d86ddbb38f21b4fbf7a5d4b99ffcf45becc2`;
index45,554B SHA256
`d65844a62a286e8e00e00f2541d6b411c42abd859b4170bfbfca0e99486a5567`.
Every original/copy/ZIP member was read back. Live build/host runs and guest
payloads were excluded from that seal. Consent's independent64-file index SHA
is `a29327d24c2ff40b710b3260f3710038466cb59d7b2ad4ed4a1d5d9c9b8b2fee`.

The separate terminal gate recovery has88 exact files/28,141,357B: completed
build/APKs/reports, integrated host, server pin and named read-only observations.
ZIP17,855,806B SHA256
`454e9b2a4ee57307e6a9d855e31d0f1907ac87cb240af7629c5d1d2e3ca9d8c8`;
index30,167B SHA256
`87f385a55831f1e81c7e119e256094a137f4b1f7879d9d2eb636f37eba3aaf54`.
Originals, copies and every ZIP member agree; the earlier130-file seal remains
unchanged. Guest payloads and the then-active second preparation are excluded.

A complete Git-history bundle through `f87e5900` verifies with Git:
11,426,991B/SHA256
`701820adf01fddc50ed536bed4d7ad6b732b072ccb472575714e2dd97639daec`.
An independent stream read confirms its bytes/hash; it did not repeat Git
verification. Original human build/cache folders remain untouched.

Both selected unrelated emulator native identities were observed live and
unchanged before this packet; the existing server is pinned without starting
or replacing it. Final postflight remains required. No unrelated emulator stop,
global ADB lifecycle, settings change, merge or release occurred.

No phone/model/thermal/performance, saved-task OS-death, joined app-adapter drain,
forensic-erasure or full hidden-world equality claim follows. Eligible native
view comparisons in the chooser are source-pinned test assertions, not separate
raw canonical sidecars. Physical-phone gates retain their prior availability/
fresh-admission blocker; no phone/model operation was attempted in this packet.
