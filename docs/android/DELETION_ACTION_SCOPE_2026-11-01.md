# Story and timeline deletion controls belong to the displayed view

B72, 2026-11-01. Refs #13 (M09.06; supporting M09.03/M09.05), #14 (M10.02).
Supporting implementation is in review; full criteria remain unchecked pending
owner acceptance and broader qualification. Based on open/unmerged PR #341 at
`3aab242676fad1df89adf3252d3e04093cace40a`.

## Reproduced boundary and fix

Old Close/Cancel callbacks could affect another story/timeline deletion view or
interrupt a newer noncooperative commit. Existing exact preview-object checks
did not bind Confirm to its rendered page. Slow controller/VM flow collectors
also missed a genuinely equal busy view after close, actual drain and reopen.
The tests use pending previews and monotonic tokens, not repeated native grants.

Both controllers add scoped Confirm/Cancel/Close overloads requiring the exact
current visible state and a live owner before existing logic. Eleven publication
sites per controller wrap the actual current state in identity StoryDeletionFrame
or BranchDeletionFrame. VM forwards those streams; Main collects frames and
captures plain states for every dialog callback. Three narrow referential button
keys per dialog retire old clickable nodes while retaining dialog/scroll state.
Existing DTO equality and unscoped compatibility APIs remain unchanged.

Native preview counts, root refusal, retained ancestry, one-shot consumption,
late capability revocation, joined closing and uncertain-commit acknowledgements
stay intact. Kotlin adds no deletion policy. No canonical event, Rust/JNI/native
protocol, storage schema, observer, gameplay, dependency, SDK, runtime or model
choice changes. All gateways in new tests are synthetic; no live story is deleted.

## Independent source and execution

Root reuses `D:/Worktrees/locallore-record-actions-ui-v1` on
`fix/m09-deletion-action-scope-v1`, owning controllers, VM/Main, dialogs, UI tests,
integration/docs/execution. Separate writer worktrees:

- Story: `locallore-record-actions-flow-v1`, `test/m09-story-deletion-scope-v1`,
  original commit `16942b35`, only StoryDeletionScopeTest.kt.
- Branch: `locallore-player-profile-ui-v1`, `test/m09-branch-deletion-scope-v1`,
  original commit `7a5fc559`, only BranchDeletionScopeTest.kt.

An independent reviewer authors no product/test code. Claims are released at
handoff; Root retains coordination. The original seven-case files remain byte-
identical across all phases: SHA256
`966dc4167aa6ec7e79b412c52048848ebcc02eb0026606f4f5beef2316ce968e`
and `662c3bca72872df3c61aca1c93476e9c23c5765ba9c75af6fcc9c5ae9616d1ce`.
Reflective scoped-overload/flow lookup falls back to old paths on unchanged
production, permitting behavioral FIRST rather than compile/missing-API failure.

All phases have 900-second Windows Job owners, actual child identity/start
barriers, complete raw capture, verified cleanup and matching raw source maps.
Existing Rust1.93.1/JDK21/Android tools and locked dependencies are reused offline;
TEMP/TMP/TMPDIR, caches and outputs remain on D:. Source edits use explicit UTF8;
independent review confirms all preexisting non-ASCII text unchanged.

Targeted command from the repository root:

```text
apps/android/gradlew.bat -p apps/android --offline --no-daemon --max-workers=2 :app:testDebugUnitTest --tests org.locallore.app.StoryDeletionScopeTest --tests org.locallore.app.BranchDeletionScopeTest
```

| Actual phase / code | Result |
| --- | --- |
| FIRST `cb88cd789ada91c622ccfb5ba332f4e752451e02`; production identical to #341 | **14 executed: 11 AssertionErrors, three controls pass**, zero errors/skips. Story7:6fail/1pass; Branch7:5fail/2pass. Owner14,599ms. |
| Same command, `04cbb3e6ce71d55a5be9db1bf272012276b1bb4b` | **Same14 GREEN**, zero failures/errors/skips; owner19,447ms. |
| `python -I -S -B scripts/check.py android --offline`, same `04cbb3e6` | **519 unique JVM/64 XML**, including all14 unchanged new cases, zero failures/errors/skips. Lint zero errors/one existing warning/one hint; both public APK audits pass. Owner44,870ms. |
| `git diff --check` | Pass before publication. |

Full gate executes15 of81 tasks,66 up-to-date. Rust build is UP-TO-DATE, using
unchanged native outputs whose release/deps two-link aliases, generated/merged,
stripped and packaged bytes are revalidated. No fresh native compilation or
native/ARM64 execution claim. No exclusion, clean, install or device task is used.
Two immutable ZIPs preserve FIRST2,586 and fixed2,587 raw sources; GREEN/full
share one. Final documentation changes only README and this report.

The fourteen cases exercise copied/prior/current-DTO views, cross-story/branch
controls, held noncooperative previews/commits, disposal, root/retained metadata,
one-shot consent and joined uncertain closing. Four controller/VM flow cases
pause real collection through close/drain/library refresh/reselection/reopen,
then require the exact current busy owner. Three old positive controls remain
green before and after the fix; they do not establish native deletion behavior.

Two new real-controller Compose journeys collect identity frames, retain actual
Confirm/Cancel/Close semantics, switch to another story/branch and require old
actions to stay quiet while fresh one-shot consent works. Synthetic tokens are
monotonic. Concrete runtime-JUnit bodies (199 units each) are present only in the
test APK. **UNRUN on Android**; source/DEX is not rendered/touch/accessibility,
JNI, native ancestry/deletion or physical-device evidence.

## Artifacts, reviews and preservation

| Final APK | Bytes | SHA256 |
| --- | ---: | --- |
| org.locallore.app | 28,360,221 | `386adfc3468850abd1864a06b09058763312dd71691dcb074a37d69a061eb933` |
| org.locallore.app.test | 2,531,397 | `2df1f77b49cb8b483090629074e7a257f93ab30159bf6b4d4607333714091430` |

Recorded common signer:
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Four packaged native libraries pass16KiB ELF/ZIP checks; test permission remains
only REORDER_TASKS. No semantic signing audit is repeated by evidence readers.

Captures: `D:/Dev/Experiments/LocalLore/2026-11-01-deletion-action-scope-v1`;
selected recovery uses the matching `D:/Dev/Recovery/LocalLore` path.
Closed evidence44,878B SHA256
`4114e1ef68412db5006bd61defffe49ff2a6334902975a2c9487faff4356564b`.
Final tested ZIP11,426,281B SHA256
`de8dd897fb543a9bfa07827a2f42b954f711b7fba23792f7c9a769e073f7b35a`.
FIRST/GREEN each preserve two new JUnit reports; inherited lint/APK/native data
retain B71 attribution rather than new targeted qualification. All65 full-build
reports (64JUnit+lint) and four APK/native copies53,710,514B are preserved before
any future regeneration. B71's67 prior original/copy bindings were verified
before reuse; its immutable copies retain history while working paths regenerate.

No-overlap source review reports no findings (12,062B, SHA256
`fa57a0965978b20658fc30f5f189978ed25c17d3672151e71446c2bccc81ea0a`).
Independent closed review joins all three phase chains, two ZIPs, unchanged
oracles, historical/current reports and artifacts, native chains and compiled
UI definitions: `closed-reader-v2.json`,30,444B SHA256
`bcf954f0978b5959003e856f4043e5a6990d2cb75f79ab2139b6b6bbbb73696a`,
terminal0 in3.384s, no findings or authorship overlap. V1 completed joins but
exited1 because its32,382B result exceeded the30KiB output limit after writing;
its passed:true data alone is not terminal qualification. Original script/result
remain frozen. V2 drops duplicate failure-message text, preserves class/method/
type and pinned full XML/v1, and checks the same budget before publication.
No product/test/boundary change or test rerun fixes that reader setup error.

Final reconstruction uses the tested ZIP plus exactly two documentation overlays.
Controls stay below64MiB and selected recovery below256MiB; generated output is
sampled every two seconds and at terminal below3GiB (final661,586,051B). This is
not a filesystem quota, global-cache/TEMP peak bound or full build-tree backup.
All failed/versioned captures remain; ordinary scratch is not silently included
in selected recovery.

## Open gates and next step

M09.06 supporting fix and M10.02 host evidence are in review; full criteria remain
unchecked. After this host packet, the owner authorizes the exact separate SDK14
retirement and nineteen-test run using frozen #338/#337 sources and B66 APKs.
That grant excludes this new B72 pair and its two UI methods. Execute only its
reviewed scope after fresh guarded storage/memory/port/ownership checks; do not
substitute newer products or infer SDK13 authority. No emulator/ADB/phone/ledger/
settings/model operation, live player deletion, unrelated stop, private upload,
merge or release occurs in B72. Physical/model/ARM64/accessibility/causal OS-death
and full milestone acceptance remain separate.
