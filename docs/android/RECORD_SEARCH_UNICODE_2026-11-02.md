# Record searches reject malformed Unicode before dispatch

Refs #13 (M09.04, supporting M09.05/M09.06), #14 (supporting M10.02).
Supporting implementation is in review; full task criteria remain unchecked.
This stacks on open/unmerged PR #355 at
`68b231ee6901aed8d52696813a18c3ade4391161`.

## Search boundary

The prior validator measured UTF-8 with replacement encoding. Isolated,
reversed or dangling UTF-16 surrogates could therefore pass validation, reach
the record reader and be placed in a JSON command. Source inspection also
shows the ordinary transport's replacement-encoding path: a malformed search
could be changed or fail later. No actual JNI corruption or Android failure
trace is claimed by these host reproductions.

The shared search validator now rejects more than 256 UTF-16 units or existing
ISO controls, then uses the existing strict `localUtf8` encoder and unchanged
256-byte limit. It catches only `CharacterCodingException`. The encoder uses
REPORT for malformed/unmappable input and creates no inference owner, model,
filesystem operation or project-native call. The length preflight is safe:
every valid Unicode scalar needs at least as many UTF-8 bytes as UTF-16 units.
Encoding work is bounded before allocation; unrelated faults are not relabeled
as bad search text.

Malformed search text produces the existing `BAD_SEARCH` result. The real
controller clears the old page and does not launch its reader. The real wire
builder refuses before constructing a command. This validates presentation
input, not eligibility or gameplay. Rust still owns scope, observer restrictions,
query results, canonical history and all mutations.

Valid supplementary characters, combining sequences, non-Latin text, literal
backslash-u spellings, quotes, spaces, case, percent and underscore are preserved
exactly. Nothing is normalized, trimmed, truncated or substituted. Empty search,
ISO-control rules, versions 1/2, byte budgets, filtering, cursor semantics and
existing generic reader-error behavior remain. Only one production file changes;
the existing encoder, query/transport code, native engine, schemas, dependencies
and controller lifecycle code are unchanged.

## Verification actually executed

Executable/test source: `ae29a602ce5e9b68f50e2caefdf8bc394c0b36b5`.
Later publication changes are documentation only. Physical checkout:
`D:/Worktrees/LocalLore-record-query2-fixtures-v1`. Installed JDK 21.0.4,
CPython 3.14.7, pinned Rust 1.93.1 and existing locked offline dependencies;
TEMP/TMP/TMPDIR are `D:/Dev/_Temp`, with D: cache/output paths. No dependency,
SDK/runtime selection, permission or global setting changes were needed.

Targeted command:

```text
apps/android/gradlew.bat -p apps/android --offline --no-daemon --max-workers=2 :app:testDebugUnitTest --tests org.locallore.app.StoryRecordSearchUnicodeTest
```

Full command:

```text
python -I -S -B scripts/check.py android --offline
```

| Phase | Actual result |
| --- | --- |
| Setup `89a72e95` / `first-v1` | Fixture reverses wire arguments; Kotlin compilation fails, zero new tests run, 10.711 s owned |
| Corrected FIRST `96dd3fe5` / `first-v2` | Nine methods: four AssertionErrors and five preservation positives, zero errors/skips; 12.786 s |
| GREEN `ae29a602` / `green-v1` | Same nine methods pass, 13.588 s |
| Full `ae29a602` / `android-v1` | **566 unique JVM methods / 68 XML, zero failures/errors/skips**, full build/lint and both public APK audits pass; 40.914 s |
| Whitespace check | `git diff --check` passes |

The corrected FIRST, GREEN and full run use the byte-identical 9,383-byte test
file, SHA256 `8adf22d481377c02081b6a26b8e4de32922e41db548e1f0bb62ff63cd4c7baeb`.
The initial session/query argument-order fixture error was corrected separately;
its compiler output and original source remain. Inherited B84 XML is explicitly
not execution evidence for that refused setup. Repeated cohorts are not added
to the distinct test count.

Nine original methods exercise malformed variants at both wire versions;
reader refusal and old-row/cursor/limitation clearing; exact 256-byte ASCII,
two-byte, supplementary and combining boundaries; unchanged literal text and
controls; late non-cooperative old-scope results; disabled/loading/disposed
controls; valid recovery; and unchanged redacted reader failures. Every held
read is released in `finally`. The controller and wire are real; record ports
are synthetic. No Kotlin test is substituted for native or Android execution.

All four host jobs have known cleanup, complete binary capture and unchanged
before/after maps of all 2,600 tracked raw source files. Three distinct full
source ZIPs are retained; GREEN/full share the same archive. Native tasks are
up to date, with unchanged inherited B84 JNI bytes and separately recorded
compilation origin. No new native compilation, ARM64 execution or full Rust
workspace test run is claimed. Lint has zero errors, one existing warning and
one hint. Final raw stdout: 7,421 bytes, SHA256
`c57148b78af50341c7a5ba659dbc8e03ec8596721f5ebf7f7902727424e65d7a`.

| Final artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Ordinary product APK | 28,499,511 | `73f9cc8b02485cf0189b9531e6c211ca9b2ba17fa6e50b248aaf51a62507bc70` |
| Ordinary test APK | 2,452,230 | `066550d1005ed7456ca72917b3959bca88215faaf307f05ebb7b6cfee3e8bc6f` |

The test APK is byte-identical to B84. Existing ordinary package/signature,
permission, backup and JNI packaging audits pass; no new permission is added.

## Preservation, acceptance and next work

OUT is `D:/Dev/Experiments/LocalLore/2026-11-02-record-search-unicode-v1`;
selected recovery uses the matching root under `D:/Dev/Recovery/LocalLore`.
Before reuse, all 213 prior B84 source/control pairs and 72 current artifact/
report bindings matched their existing immutable copies. That branch, failed
captures and full archives remain. B85 retains the compile refusal, meaningful
FIRST, raw/XML/source records and current artifacts. Planned monitored limits:
controls 64 MiB, generated builds 3 GiB, selected recovery 192 MiB; no deletion
or OS quota change. These bounds are separate from the unchanged AVD ledger.

No Android test, IME/touch/TalkBack, phone or real-model check ran in this
packet. No guest preparation/boot, ADB lifecycle, ledger transition, emulator
stop, system setting change, private upload or merge occurred. The inherited
five fork Compose cases remain unrun. PR #354's separate operator, source,
product/APKs and pending exact approval remain frozen; no earlier answer
authorizes these different product bytes. Full M09/M10 acceptance remains open.

The next device action is the separately proposed guarded recovery/UI run,
only after its applicable approval and current admission gates. These JVM
checks do not establish that run or a complete local-model user journey.
