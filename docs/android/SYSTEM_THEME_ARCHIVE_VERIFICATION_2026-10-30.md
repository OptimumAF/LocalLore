# Updated system theme: archive-profile verification

Date: 2026-10-30. M10.03 supporting qualification of the M09.05 theme slice is
in review. Full criteria and owner acceptance remain open. This follow-up is
stacked on open/unmerged [#289](https://github.com/OptimumAF/LocalLore/pull/289).

The [system-theme implementation](SYSTEM_THEME_VERIFICATION_2026-10-30.md) had
passed the ordinary-package public checker. This packet executes the archive
profile on the same production code, checkpoint
`4d9f6b43bafefba7dc4e73cca532515cc7747d51` / 2,307 tracked raw inputs.
There is no production, test, dependency, profile or audit-policy change.

## Actual public check

```powershell
python scripts/check.py android --archive-verification --offline
```

The actual unmodified script runs the verified Gradle wrapper for both APKs,
all JVM tests and lint, followed by the public product and instrumentation-pair
audits with their archive flag. No private substitute, task exclusion, test
filter, forced rerun, download or target installation was used.

| Actual check | Result |
| --- | --- |
| Both Rust Android targets | Fresh offline builds for x86_64 and arm64-v8a |
| JVM tests | 337 unique cases / 40 XML reports; 0 failures, errors or skips |
| Lint | 0 Error/Fatal; 1 existing `GradleDependency` warning |
| Product APK audit | Passed manifest/backup/resource/ZIP/native policy |
| Instrumentation pair audit | Passed archive package/runner/permission/provider policy and signer pairing |

The public call returns **0 in 237,548 ms**. Its single 900-second process-tree
owner closes in **239,651 ms**, worker exit 0, with complete cleanup/capture,
stdout 10,964 bytes and stderr zero. All 2,307 source inputs and recorded
tool/helper/proof pins remain equal before/after. The fresh build directory
was absent initially; native, JVM, lint and both assembly task lines execute
without cached/up-to-date suffixes. Empty/no-source tasks are not counted as
tests. No corrective run was needed.

The warning is the existing coroutines-Android 1.10.2 versus 1.11.0 update
notice. Tool/dependency versions and lint scope are unchanged from the ordinary
qualification. Existing process-local D: caches/temp and the supported complete
four-property signing override are reused. The existing credential binding
passes before/after; neither fixed D: default-key path is created. No private
key was copied or generated and no global setting changed.

## Exact archive artifacts

| APK | Bytes | SHA-256 |
| --- | ---: | --- |
| `org.locallore.app.archiveverify` | 27,739,772 | `6f3d57354c01f1e7c9e37a3093b0e144074a71f618850e24b46cd253469dccad` |
| `org.locallore.app.archiveverify.test` | 2,210,867 | `0655f8c3522b5bfd33a08abaa14bcf307402b5e5497a067591a6ef8c35401102` |

The verified common public certificate SHA-256 is
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
The test's sole permission is `android.permission.REORDER_TASKS`. Actual SDK
signature verification occurs inside the public pair command; a separate
per-tool trace or independent cryptographic reexecution is not invented.

Independent closed-file review checks command/source/report/request/tool joins,
both ABI release/generated/merged byte chains and stripped/APK members. Native
bytes equal the prior ordinary artifacts; all 372 native inputs are unchanged.
The review finds exactly two public no-argument void JUnit methods of
`SystemThemeTest` in the test DEX, absent from the product. Merged night v8/v27
aliases and compiled resource-table presence are checked at packaging scope.
The light style is unchanged. These UI journeys remain **compiled and packaged,
unrun on Android**. The independent file-only reader passes on its first run;
receipt SHA-256:
`2727d5945a1ee0723331c0e788d41cfeb1e41ff64bc1b5e39c6daa7a81d0b3b2`.

## APK size comparison

The fresh archive pair is smaller than B21's incrementally built ordinary
pair. Independent comparison finds identical ZIP entry rosters (149 product,
122 test) and DEX class/definition-signature rosters (13,375 product, 4,390 test).
Uncompressed member differences are confined to the manifest, resource table
and the profile-bearing BuildConfig DEX. Total uncompressed contents differ
by 160 bytes for the product and 208 for the test.

| APK | File bytes | Referenced compressed payload bytes | Bytes outside current entry spans before signing |
| --- | ---: | ---: | ---: |
| Ordinary product | 28,166,336 | 27,682,673 | 425,028 |
| Fresh archive product | 27,739,772 | 27,682,681 | 0 |
| Ordinary test | 3,319,589 | 2,187,133 | 1,108,734 |
| Fresh archive test | 2,210,867 | 2,187,143 | 0 |

Root's independent physical accounting also includes local headers/extra
fields, each 4,096-byte signing block, and central directory/EOCD; these sum
exactly to all four file sizes. This explains the size difference without
evidence of missing implementation or test classes. The origin of the gaps
was not traced. This is layout/content evidence, not a universal reproducible
build, runtime equivalence, memory or performance claim.

## Preservation and remaining work

Exact executed source contains 2,307 raw members / 32,048,609 bytes,
10,269,195 compressed bytes, SHA-256
`f6fe9160574253ea94461c27398c6fc71ffad2532945aad9293e0a66d0359fb8`.
The phase preservation manifest SHA-256 is
`c37e1a75f111a542b76c7d957eae18fa81f58e61bd91951e8488a9fda717631d`.
Every archive member and original raw source was reread before documentation
changed; Git-normalized blobs do not substitute for executed raw bytes.
Forty-eight APK/report/native copies totaling 70,496,403 bytes are retained.

Original scripts/captures/source/artifacts remain under
`D:\Dev\Experiments\LocalLore\2026-10-30-theme-archive-v1`; generated outputs
remain in the original build worktree. Selected recovery uses the matching
`D:\Dev\Recovery\LocalLore` root; final ticket handoff records seals, bundle
refs and independent readback. The original 8 GiB budget includes two source
trees, generated builds, cache/temp allowance and selected recovery. No prior
source, cache, guest, failed capture or recovery is removed. No exclusive peak
allocation or backup of every ignored/generated byte is claimed.

No Android, phone/emulator, ADB/service, model, traffic, gameplay or accessibility
experiment occurred. Visual/theme switching, screen readers, keyboard/touch,
large fonts, process death, physical/ARM64 execution, real-model performance
and full M09.05/M10.03 acceptance remain separate. No merge or release.

Read-only source review identifies a concrete next M09.03 implementation slice:
scope-aware new-reply presentation, preserving a reader's history position and
offering explicit Latest navigation. Current code has no explicit follow/unread
policy; existing UI tests scroll manually. This is a source gap, not a measured
scrolling/keyboard failure. The next packet should implement and test that
behavior while retaining draft/scope/callback guards; its actual UI/IME tests
still need separately authorized target admission.
