# Finite SDK constraints: verification, 2026-10-25

Refs #9 (M05.01/M05.02/M05.05), #5 (M01.05 supporting). Root claim
[6400786067](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6400786067).
Implementation05527059, audited receipt APK pin3efe84df, based on090a8694/#173.
This is a locally verified implementation awaiting owner acceptance. It does
not complete M05 or qualify a physical phone.

## Reproduced defect and correction

The pinned LLGuidance1.3.0 depends on derivre0.3.8. Its `JsonQuote`
`Expr::ByteConcat` branch builds a quoted byte prefix and returns it without
appending the mapped tail when that prefix needs escaping. The internal
byte-concat limit is31. Exact primary-source paths and public SDK interface
research are retained in [literal research](LLGUIDANCE_LITERAL_RESEARCH_2026-10-25.md)
and [SDK mask-path research](LITERT_MASK_PATH_RESEARCH_2026-10-25.md).

Actual native observations with the already verified Windows wheel:

| Control | Observed result |
| --- | --- |
| Original quote/backslash/Unicode/newline text,42 raw UTF8 bytes | Full48-byte JSON rejected at13 by all three JSON paths; wrong shortened prefix accepted |
| Bounded minimization,73 evaluations |32 raw UTF8 bytes remain; full38-byte JSON rejected at3 by all three paths; shortened prefix accepted |
|16 threshold controls, two quotes plus25–40 letters | Raw27–31 bytes pass; raw32 fails at3 with only closing-quote token allowed; later lengths fail at the predicted longer prefix |
| Exact whole-serialized-JSON regex | Original and minimized full strings accepted through EOS; shortened strings and trailing suffixes rejected |

The JSON paths are default JSON, default Lark wrapper and explicit Lark
`no_forcing`. The latter is a failed control, not a remedy. A direct consume
failure alone cannot distinguish grammar mismatch from resource failure;
the source omission plus these full/short-language controls provide the
specific defect evidence. They do **not** diagnose the earlier Android
wrapper-declared INTERNAL13, whose ordinary literal is shorter and unescaped.

The development worker selects the pinned public SDK regex response format
only after complete bounded finite-schema translation. Nonfinite/unsupported
schemas use the existing JSON format. No dependency, Rust semantic schema,
generation budget, gameplay authority, prompt, event or storage format changes.
The [protocol](LLGUIDANCE_ORACLE_PROTOCOL.md) specifies limits and reproduction.

## Actual checks

WindowsAMD64, CPython3.9.12, Rust1.93.1, Java21, installed AndroidSDK/API35;
existing pinned LiteRT-LM revisionbda624851d74be34d4e1f7fac1fc4155939539c7.
No model download, native rebuild or dependency introduction in this packet.
All reported process owners below completed0 with known cleanup unless noted.

| Check | Result |
| --- | --- |
| Offline locked Rust tests |361passed across50suites;4 historical capture-only ignores; new2 literal regression tests pass |
| Offline Clippy, warnings denied |PASS |
| Full Python suite |866passed,0failures/errors/skips |
| Targeted8 Python modules after APK repin |PASS, owner34547ms |
| Receipt JVM |512passed,48XML suites,0failures/errors/skips;81031ms |
| Regular JVM |454passed,43XML suites,0failures/errors/skips;74328ms |
| Receipt APP/test assembly |PASS,69797ms |
| Regular APP/test assembly |PASS,55734ms |
| Receipt lint/dependency/analyzer audits |PASS,80985ms;0errors/19warnings |
| Regular lint/dependency/analyzer audits |PASS,58203ms;0errors/9warnings |
| Receipt/regular APK manifest/native audits |PASS,1047/1046ms; no INTERNET permission; six packaged libraries each,16KiB ELF load alignment |
| Receipt/regular APP+test signatures |PASS,672ms each; same debug certificate SHA2561960a64db1dffe2f173f5cb08601bdad30bcf1285a90c9b9928a4d562c1123d1 |
| Actual Kotlin patterns through native regex |215/215samples plus all sanity controls PASS,703ms |
| Current-source literal replay |Observed defect report,484ms,0stderr bytes |

The native finite corpus contains13schemas/215samples:119positive and96negative.
It retains all original8 engine schemas/199samples and three provider-free
refusals, adds five original literal regression cases and one nested truncated
negative. All semantic choices in the engine corpus remain; no known failure
was removed. The Kotlin export8237bytes has SHA256
`d2989fa17c242bf58e7ff902e3267b05d87401a0dbe6abc4de637c6f9a13918e`;
input37029bytes SHA256
`aac94a0ca1de3222a4774dd0a404b44f867d9712e6919c1a4ece553fdc7fc1a2`.
The native report35809bytes SHA256
`02708b00f2da25a0a17068ae6f8170b14109fe3dcb15f3050a0a8d702e9619a5`.
The original JSON mismatch remains documented separately.

Raw JVM XML, command arrays, source captures, bounded process reports,
compiler reports and artifacts remain in private local evidence. The first
JVM attempt512tests/12failures is preserved: Android's unmocked `org.json`
stub caused nine direct failures and three downstream assertions. Replacing
it with already pinned Gson corrected the implementation; the successful
run used actual parsing, not mocks. An initial isolated Python worker import
failure and the initial APK audit missing ANDROID_HOME were retained and
corrected. A collection step targeting a nonexistent regular build directory
was refused, then corrected without claiming another test run.

## Frozen artifacts and source identity

| APK | Bytes | SHA256 |
| --- | ---: | --- |
| Receipt APP |75041504|83797af66672e5bab89e17d53339478eb7c57bee66773c9c72edd13466911a8a|
| Receipt test |2056615|e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d|
| Regular APP |74975720|9ba3e59b2f8d3ed8ae71b3c7601d47c1039b194b9850c443541b4d2118bf5357|
| Regular test |1869719|8c14c03502faee7661b58a6862c5b35e9fec6e6371e40b9c2718daadd56ad1e5|

All six corresponding APP native libraries are byte-identical between variants.
ARM64 packaging is not ARM64 execution. Normalized codec source SHA256
`b89ba9aa332529a629e0f532f5d8e55997eef8f68229665f898eae53010af96f`
is bound into worker source SHA256
`db4d5f18318b7b5d67fbeb33bddee7781ddce7adc41477d9c17808e92c23df27`.
The original schema's425-byte trace field does not report regex payload size.

## Resource housekeeping and remaining gates

Two reversible build-output compression operations preserved every logical
file hash. A later complete code-build archive preserves11305files/8476815696
logical bytes in1900763069archive bytes, SHA256
`0af883ad0f0947b3af071650a5f41b1ae978061b204570a09715d5ba76bf1e0a`.
Archive member readback and a subsequent full source rehash passed. Removal
of the four archived generated directories was rejected before dispatch by
automatic approval review, again after explicit owner permission; the only
reported reason was "blocked by policy". Nothing was deleted or bypassed.
Models, saves, emulator data and earlier evidence remain outside that archive.

The [independent device preparation](FINITE_REGEX_DEVICE_ADMISSION_2026-10-25.md)
records a dated capacity snapshot and a small NTFS experiment. Neither is a
VM, SDK or model result. Fresh source/APK/lease/storage admission, local receipt
import, actual Android inference, canonical gift/dialogue, process restart and
no-inference replay still require a separately observed run. Existing
quarantined targets are not reusable evidence. Physical-phone M01.01, ARM64
execution, model quality, latency tiers and the complete M05 exit gate remain
unqualified. No merge, release or access change is performed by this packet.
