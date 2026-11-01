# Transcript navigation: archive-profile verification

Date: 2026-10-30. M10.03 supporting qualification of M09.03 is in review.
Full milestone criteria and owner acceptance remain open. This packet is based
on open/unmerged [PR #292](https://github.com/OptimumAF/LocalLore/pull/292),
`371d61a59194f37b1f6d5697be0a4983f17928e6` / 2,313 tracked raw inputs.
Production code, tests, dependencies, profiles and audit policy are unchanged.
The [ordinary-profile implementation evidence](TRANSCRIPT_NAVIGATION_VERIFICATION_2026-10-30.md)
retains its exact source and result attribution.

## Actual public check

```powershell
python scripts/check.py android --archive-verification --offline
```

The unchanged public runner executes verified Gradle assembly of both APKs,
all JVM tests and lint, followed by the public archive product and
instrumentation-pair audits. No private substitute, filter, task exclusion,
forced rerun, download, installation or instrumented execution was used.

| Check | Actual result |
| --- | --- |
| JVM suite | 345 unique cases / 41 XML reports; 0 failures, errors or skips |
| Lint | 0 Error/Fatal; existing GradleDependency warning and AutoboxingStateCreation hint |
| Native builds | Fresh offline x86_64 and arm64-v8a builds |
| Product/pair public audits | Both pass the isolated archive policies |
| Transcript/theme journeys | Four transcript and two theme methods compiled/packaged test-only; unrun |

The public call returns **0 in 235,823 ms**. Its one 900-second process-tree
owner closes in **237,973 ms**, worker exit 0, with complete cleanup/capture,
stdout 11,044 bytes and stderr zero. All 2,313 raw source inputs and recorded
tool/helper/signing proof pins remain equal before/after. The build directory
was absent initially; critical native, JVM, lint and assembly task lines execute
without cached/up-to-date suffixes. No corrective build was needed.

Existing process-local D: caches/temp and the reviewed complete signing override
were reused. The original credential was read in place; neither fixed D: default
key appeared. No key, dependency, SDK or global setting changed. The warning
concerns existing coroutines 1.10.2 versus 1.11.0; the hint concerns the existing
boxed gesture counter introduced in #292. Tool versions remain those documented
in the preceding ordinary/theme checks.

## Artifacts and independent review

| APK | Bytes | SHA-256 |
| --- | ---: | --- |
| org.locallore.app.archiveverify | 27,756,156 | `b152ddea01363fc622a286dab3d59386739a997c5cb77a14d97851ec166ab192` |
| org.locallore.app.archiveverify.test | 2,220,071 | `0b58ff22bc0d51585fc695e20d2ce303a7e8d38fb621ee61464ba14cc3a5db70` |

Actual public pair verification establishes the matching certificate
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
The test's sole permission is android.permission.REORDER_TASKS. A separate
signature-tool execution is not invented for the file-only review.

Independent closed-file review passes in **4,416 ms**, checking actual command,
report, source/tool, source-ZIP and artifact-copy joins. The exact eight new JVM
cases pass again. Four transcript and two theme public no-argument JUnit method
definitions occur only in test DEX; this is compiled evidence, not UI execution.
All 372 native inputs are unchanged from the preceding checks. Both native
release/generated/merged chains join; stripped JNI/APK bytes match B23 ordinary
and B22 archive for both ABIs. Neither ABI is executed by this packet.

Comparison to B23 ordinary artifacts finds equal ZIP member rosters (149 app,
122 test) and equal DEX class/method rosters (13,398 app classes, 4,411 test).
Differing uncompressed members are AndroidManifest.xml, resources.arsc and
classes3.dex in the app / classes4.dex in tests. This does not establish DEX
code-body or runtime equivalence or explain physical ZIP size differences.
Review receipt SHA-256:
`6054c26016b7c2aa14bc40b445fff2010a2064643da99724e8ffaeea19093b69`.

## Preservation, limits and next work

Before docs changed, all 2,313 executed raw files / 32,093,461 bytes were preserved
and read back in a 10,286,017-byte source ZIP, SHA-256
`376f65bc468edda28614f7e0053a2e0699715d2a14b10c55f30bcad2bd59e1d1`.
Fifty-one selected APK/report/native copies total 93,062,639 bytes.
Preserved-build manifest SHA-256:
`25a5761643781ea61075ba4fb7ed440516c63baf52b82b6efb1a84b206d41442`.

Originals stay at `D:\Dev\Experiments\LocalLore\2026-10-30-transcript-archive-v1`.
Final ticket handoff records selected recovery, independent readback and complete
two-branch bundle seals at the matching `D:\Dev\Recovery\LocalLore` root.
The original 8 GiB packet budget includes two source trees, generated build,
selected recovery and cache/temp allowances; the pre-build conservative bound
was 6,506,643,747 bytes. This is not an exclusive peak or OS quota claim.
Previous worktrees, generated builds, caches, failures, guests and recovery remain
in place. Selected recovery is not every ignored byte.

The owner chose to continue without the phone. No phone, ADB/service, emulator,
model, traffic, system-setting, merge or release action occurred. Real scrolling,
gesture races, IME, accessibility, recreation/full Android journeys, physical
performance, ARM64 execution and model/story quality remain unverified.

The [source-based next-task assessment](https://github.com/OptimumAF/LocalLore/issues/13#issuecomment-6531357220)
identifies a runnable code prerequisite: a fixed model-free archive-UI profile
through the existing guarded owner/client, with an exact ten-method cohort
(four transcript, two theme, two layout and two Rust-backed PlayInput cases).
The current SDK4/5 contracts admit only AUTHOR/model selectors. Legacy schemas,
model requirements, source/build/ownership/closure guards must remain strict.
PlayInput's cancellation window is deliberately gated before native preparation;
cancellation while the actual provider is running remains a separate test.

Target execution also needs separate capacity disposition and fresh approval:
the read-only shared ledger records two closed unretired roots, already filling
the two-root limit. This is a ledger observation, not fresh closure/disk proof.
No registry, guest or boot marker was changed. Full tasks remain unchecked.
