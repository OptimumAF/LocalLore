# Knowledge UI build-attestation verification

B88, 2026-11-02. Refs #14 (M10.02), supporting #13 (M09.04/M09.05/M09.06).
Supporting implementation is in review. Full tasks remain unchecked pending
broader criteria and owner acceptance; no merge or device acceptance.

This is the fixed build-input prerequisite for a later SDK16 Knowledge profile.
It implements working data-only creation/verification, not a target dispatcher,
admission, recovery authorization or human grant. The next integration must use
the existing guarded owners/storage and its own applicable bounded approval.

## Frozen dependencies and implementation

Tooling stacks on open/unmerged PR #354, `b6cda494`, using a released clean D:
review checkout. The pending operator at its original literal path stays frozen.
Product source is separate: open/unmerged PR #358,
`286c0905613e9bbff2d69796155105339000eceb`, at
`D:\Worktrees\LocalLore-record-query2-fixtures-v1`, with 2,608 raw tracked inputs.
No product code, existing runner, old baseline, dependency or system setting changes.

[`KNOWLEDGE_UI_BUILD_V1.md`](KNOWLEDGE_UI_BUILD_V1.md) defines the two public
interfaces, fixed paths, byte graph and four ordered selectors.
`create_manifest()` returns validated metadata without publishing it.
`verify_frozen_product()` accepts exactly the fixed build/product/test roles,
checks their current bytes and returns a defensive copy. Imports do no I/O.

The new adapter reuses the unchanged `library_ui_build._Reader`: held-stream
identity checks during reads, final file/parent stamp rechecks, ordinary
single-link physical D: files, 120 seconds and 512 MiB read limits. Its older
Cargo alias exceptions are unused. It revalidates fixed Git identity, all raw
product sources, source/copy pairs, exact JVM execution, recorded audits and DEX
proofs with closed keys/types. No caller chooses another profile/path/selector.
Public failures use the existing bounded `BuildRefused` categories.

The reader validates recorded byte evidence and joins; it does not rerun
compilers, signature/ELF/DEX tools or Android. False facts explicitly retain
Android/model/feature-acceptance/fresh-native status and incomplete full-tool,
cache/TEMP and repeated semantic-review provenance.

## Verification actually executed

Builds ran from the physical product checkout; host tests/attestation ran from
`D:\Worktrees\LocalLore-original-input-compose-review-v1`. TEMP/TMP/TMPDIR
were process-local `D:\Dev\_Temp`, with offline D: Cargo/Gradle caches and the
existing installed tools. Every job had a 900-second owned Windows job,
binary capture, complete source archive and unchanged before/after source map.
Output caps were 3 GiB generated, 64 MiB controls and 192 MiB selected recovery.

| Phase | Actual result | Owned elapsed |
|---|---|---:|
| `android-v1` | Build/lint/APK audits pass; JVM task **UP-TO-DATE**, inherited results | 10.860s |
| `jvm-v1` | Forced actual **579 unique JVM / 69 XML, zero failures/errors/skips** | 40.154s |
| `android-v2` | Final ordinary APK builds/lint/audits pass; JVM reuses forced cohort | 35.820s |
| `unit-v1` | Python import setup refuses: zero declared methods, one loader error | 1.572s |
| `unit-v2` | **13 new host methods pass**, no skips/errors/failures | 19.222s |
| `shared-v1` | Same isolated-Python import setup refusal, zero declared methods | 1.623s |
| `shared-v2` | **12 existing shared-reader methods pass**, no skips/errors/failures | 11.359s |
| `actual-v1` | Genuine public creation and verification pass on frozen real inputs | 3.994s |

The new methods ran at `55c512fb0f25440eeb2d136ccec71bc8e92b60f3`;
final executable source is `d143e70cc8c724671786f16a6298a163fc06290b`.
Only a test EOF blank line changed between those heads; full test AST equality
is recorded and independently verified. Shared/actual runs use final `d143e70c`.
README and this report are the only changes after that final verification.

The two import refusals precede declared test execution, not product regression
failures. Explicit private launchers add the fixed repository import root before
loading tests under isolated Python. Original refusals, code and archives remain.
Fixture setup also matches the actual `jvm` preservation mode and uses an owned
D: repository target folder with Windows-only held-reader cases. All 13 methods
execute locally; their original assertion/method bodies remain unchanged.

The forced command used existing Gradle `--rerun-tasks`: all 25 tasks executed.
The native task reinvoked cached Cargo artifacts for both ABIs without new Rust
compilation. Final `android-v2` shows native and JVM tasks up-to-date. None of
these outcomes establishes JNI/ARM64 execution or model behavior. The repeated
579-case snapshots are one distinct cohort, not 1,737 tests.

Reproducible entry points with the same D: temp/cache settings are:

```powershell
python -I -S -B scripts/check.py android --offline
```

For the forced JVM cohort, use the product checkout's Gradle wrapper with
`:app:testDebugUnitTest --rerun-tasks --offline --no-daemon --max-workers=2`.
The isolated host entry helpers are privately preserved; ordinary repository
entry points are `python -m unittest benchmarks.test_knowledge_ui_build` and
`python -m unittest discover -s scripts/tests -p test_library_ui_build.py`.
Synthetic fixtures validate metadata/file boundaries, not APK/runtime semantics.

## APK and compiled-method evidence

Final product: 28,398,622 bytes,
`0b93c6af0772ff6216a0dcbeb2f8b19b1564129f3855336ced7dcafbfca662cd`.
Test: 2,645,072 bytes,
`3241aaff3c42fc6c155f04da40cae88aa54e39cd68c10f7cb5178a0b77a9c5db`.
Both audits pass with the existing signer
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Product permission is exactly the existing signature-protected AndroidX receiver
permission; test permission is exactly `android.permission.REORDER_TASKS`.

File-only DEX analysis, independently reparsed, finds the exact four public
instance JUnit-annotated definitions in one test class in `classes4.dex`, with
459 / 298 / 183 / 745 code units for labels / replaced views / remount / enlarged
text. The class is absent from product. These are real definitions with code,
not string-presence evidence. **Zero of four execute on Android.** They inspect
presentation boundaries; native eligibility and complete journeys remain separate.

The first inspector wrongly equated unstripped generated libraries with APK
entries. Its original script and role-inspection record remain. Corrected proof
separately binds ordinary generated libraries and Gradle's stripped outputs.
APK entries match stripped arm64/x86_64 bytes (8,549,536 / 9,554,216), including
their preserved copies. No native or device boundary was weakened to pass.

## Manifest, preservation and limits

The immutable baseline metadata is 54,428 bytes, SHA256
`1f1ca5c9e00e28e11d2a8f3d3f812fcdb0787c8ac94299b5ef2104a381bd4868`.
It uses chosen LF encoding and a narrow `-text` attribute. Its original CRLF
proposal remains; parsed metadata is identical. No captured raw source or
evidence bytes were normalized. The whitespace findings remain recorded.

Actual creation returned data; the coordinator then explicitly published the
fixed prospective manifest and called the public verifier. The 8,656-byte
manifest hash is
`97037d90a3b738a09054a07d03caf659cb2276774935d0b46535712b31d6f55c`.
It binds the real product head, pair, four selectors and false execution flags.
The adapter did not publish or create authority. Both calls together took
2.432s inside the 3.994s owned job; this is host verification time, not app latency.

Private OUT/REC use `2026-11-02-knowledge-ui-build-v1` beneath
`D:\Dev\Experiments\LocalLore` and `D:\Dev\Recovery\LocalLore`.
All eight original phase records/captures, four complete source archives,
initial APK copies, forced/final reports, both native roles and independent
source/closed/oracle reviews remain. Prior B87 172 current pairs, B86 147
immutable copies and 74 current artifact bindings were verified before reuse.
Final verified copy receipts and claim release are linked from #14.

No emulator/ADB lifecycle, ledger change, model/phone operation, settings change,
other-emulator stop, private upload or merge occurred. PR #354 remains frozen
behind its pending applicable recovery/run approval. Next runnable task:
implement the narrow SDK16 owner/controller profile against this fixed build
contract, then prepare its exact bounded operation. Actual target execution,
accessibility, real inference and full milestone acceptance remain open.
