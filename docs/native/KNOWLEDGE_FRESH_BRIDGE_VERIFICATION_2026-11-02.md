# Fresh SDK16 bridge host verification — 2026-11-02

Refs #14 (M10.02), supporting #13 (M09.06). B94 implements the
[fresh preparation-to-run bridge](KNOWLEDGE_FRESH_BRIDGE_V1.md). Supporting
implementation is in review, not accepted milestone completion. No SDK16
preparation, reservation, boot, Android UI, model or phone operation occurred.
Knowledge UI remains **0/4 executed; all four remain unrun**.

The packet stacks on unmerged #365 at
`e7328a966a81720d5b0731fd33cd0f4acf8bf9a7`. Root reused the old clean physical
`D:/Dev/Repositories/LocalLore` checkout on `impl/m10-knowledge-fresh-bridge-v1`;
the old branch and ignored build state remain. The app's managed-worktree tool
refused the nested repository and its non-repository workspace parent before
creating a checkout. Frozen operational sources were not moved or edited.
GitHub Issues retain claims, changes of scope, evidence and handoffs; the retired
Markdown trackers remain compatibility pointers.

## Implemented behavior

Two new scripts supply a pure closed approval/attempt contract and one bounded
fresh-operation bridge. Exact approval, source/helper/Python/APK/proposal/ledger
bindings and advisory capacity checks precede the one-use attempt. Worker
ownership and fresh resource/locked-storage admission are then enforced before
SDK work by the existing owners/preparation. Verified fresh prepared files and ledger state
precede run planning/authorization/admission; the activation input is published
last. The existing SDK16 activation owns the guest, private ADB service, selected
controller and cleanup. Stored joined runtime results and actual closed storage
are required for a passed operation; feature acceptance remains false.

There is no recovery, old-root adoption, retry, retirement, model operation,
caller-selected path/registry/command or second gameplay authority. Rust,
Kotlin, canonical state, runtime/model/SDK versions, production dependencies,
licenses and the two-root/64 GiB/40 GiB storage admission rule are unchanged.
The CLI starts its clock before input/import checks, with a 2,400-second worker
ceiling and the documented bounded-wait/untimed-I/O cleanup tail.

## Actual verification

**219 distinct host methods pass:** final 37 new methods on
`6a5ce7d14426343792b3c6bced5cb2dc24a0ecbf`, plus 182 existing regressions on
`73befec3a8efea7f63021a63f65739483034a87e`. Their shared production/test-fixture
files remain byte-identical in final code. Repeated runs are not additive.
No new failure, error or skip remains in these completed suites.

The new suites contain 14 prepared/input/stage tests, 19 supervisor/worker tests,
two unread-capture tests and two namespace tests. Original independent test
proposals were integrated unchanged. Tiny isolated files retain real shared
proposal/prepared/authorization/storage/history validation; SDK, build, process,
thread and observation ports are explicit fakes. They do not create applicable
human authority or touch the production ledger/guest. Checks include strict
types/scope/flags, stale sources and ledger, malformed prepared receipts, partial
publication/no retry, ordered admission, cancellation, borrowed identities,
barrier release, job-close failures, incomplete readers and joined closure.

The 182-method regression selection covers parent/environment, shared storage,
owned-target storage, Knowledge activation/profile and fresh-root validation.
The existing 8 GiB userdata-adoption test also executes its real Windows sparse
fixture API, retaining every original admission/config/userdata assertion.

All 13 bounded host phases are closed, with exact raw capture byte counts,
known host cleanup and equal before/after maps of the full tracked tree.
This is host process closure, not a native Android teardown qualification.

| Phase | Source | Actual result | Owner ms |
| --- | --- | --- | ---: |
| supervisor-first-v1 | 8dd4996d | 19 ran; 1 failure, 1 error | 1,874 |
| supervisor-v2 | a7d6a4cc | Same 19 pass | 1,785 |
| fresh-first-v1 | 943571f9 | 14 ran; 1 failure, 10 errors including subtests | 8,127 |
| capture-first-v1 | cab28af5 | Two original assertions fail | 1,876 |
| fresh-v2 | 1d3cf351 | Same 14 pass | 9,595 |
| supervisor-v3 | 1d3cf351 | Original 19 plus two capture methods pass | 1,824 |
| regression-v1 | 1d3cf351 | Budget STOP; no suite completion | 4,963 |
| all-v1 | 73befec3 | 35 pass | 10,961 |
| regression-v2 | 73befec3 | 182 pass | 27,526 |
| inputs-v1 | 73befec3 | Actual module-source refusal | 1,928 |
| inputs-v2 | 94cae93b | Actual second namespace check refuses | 2,028 |
| all-v2 | 6a5ce7d1 | Final 37 pass | 10,715 |
| inputs-v3 | 6a5ce7d1 | Real file-only startup/input checks pass | 14,656 |

Actual bounded commands ran from the physical root with process-local
TEMP/TMP/TMPDIR on `D:/Dev/_Temp`. The final selections were:

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-bridge-v1/run-host-v6.py all all-v2
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-bridge-v1/run-host-v3.py regression regression-v2
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-bridge-v1/run-host-v6.py inputs inputs-v3
```

The retained private entry files record exact unittest module rosters, commands,
environment and declared/ran/failed/error/skipped totals. For another host,
the four new reusable suite modules are `scripts.tests.test_knowledge_ui_fresh_bridge`,
`scripts.tests.test_knowledge_ui_fresh_supervisor`,
`scripts.tests.test_knowledge_ui_fresh_unread_capture` and
`scripts.tests.test_knowledge_ui_fresh_imports`; they require the documented
Windows/physical-D test environment. Private host helpers are evidence, not new
production dependencies or portable Android qualification commands.

The real `inputs-v3` run validates the actual API import path and frozen B93
handoff, 28 source bindings, six installed tool bindings, installed Python,
original B88 manifest/APKs and four selectors. No human authority is created or
validated by this authority-less component check. It creates no preparation,
admission, target or ledger transition. The shared ledger stays 42,221 bytes,
SHA256 `84ad23a43f6c4abd6be82164fcec2e4e7b51277f1e250a507af22654be1a7294`.
The ADB private key is not read. The inherited environment check hashes the
console-token binding; it never prints or copies token contents.

## Failures preserved and corrected

- The original fresh proof failed because recovery-history validation required
  a dictionary while a fresh entry correctly has `recovery=None`. The bridge
  now relies on shared storage validation and explicitly refuses recovery for
  this fresh-only operation; shared recovery rules were not weakened.
- The first owner tests exposed a late CLI timer and an exception escaping
  reader-status cleanup. Unchanged tests pass after starting the retained clock
  first and treating unknown reader state as sticky cleanup/capture failure.
- Two supplemental assertions proved that unread stdout/stderr cannot become
  capture-complete by closing empty output files. Both readers must start.
- The original regression guard stopped a growing, nominally sparse dummy SD
  during CRT `truncate`. No suite completion is claimed. The partial file stays
  unchanged at 1,350,832,128 logical bytes. Initial allocated observation was
  1,315,045,376; final pinned allocation is 1,350,832,128. The test now extends
  its newly created sparse file using checked
  [SetFilePointerEx](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfilepointerex)
  and [SetEndOfFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setendoffile),
  then asserts allocation at most 64 KiB with
  [GetCompressedFileSizeW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getcompressedfilesizew).
  No privileged API, system/volume setting, production threshold or literal
  8 GiB assertion changed. Official compatibility was checked before use.
- Actual startup first refused a benchmark namespace widened by operator Root.
  Exact-file contract loading fixes that. The next real check refused a duplicate
  Source prefix on the second frozen API call. The bridge removes only the
  verified first trusted prefix before re-entering the unchanged validator.
  Foreign cached modules still refuse. The two synthetic namespace methods cover
  Root contamination/foreign cache; the genuine final run covers the actual
  unconditional duplicate-prefix behavior that their port does not reproduce.
- First input helper/request entry mismatch and a never-entered diagnostic
  expression remain retained with the failed phase; final entry is correctly
  bound. A coordinator observation-store error and a pre-dispatch tool-call syntax
  refusal did not trigger replay. An initial backup-meter setup compared access
  time and stopped before publication; the corrected pin excludes OS-managed
  access time. The first strict evidence parser rejected three expected fixed
  publication-failure diagnostics inside one passing adversary. Its replacement
  accepts exactly those three markers, not arbitrary output; original helpers
  remain. These are evidence-tool limitations, not additional product test passes.

## Preservation and limits

Private OUT is `D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-bridge-v1`;
REC is its matching `D:/Dev/Recovery/LocalLore` directory. The joined index pins
13 phases and eight Python-only source archives, 3,810 verified members; it is
not a full-tree artifact archive. Full tracked-tree source maps are separate.
Index SHA256 is `5e470b920be5f44cd8a14e1e6baf5394d3faea71cec797f57ff33e87b0633433`.

The failed logical-budget boundary stays failed. Before further work, the ticket
separately declared a 12 GiB logical synthetic extent and 64 MiB NEW physical
allocation, plus the exact retained partial's charge. Controls were raised
prospectively from 32 to 48 MiB for immutable source archives/maps; no controls
failure was waived and no archive was pruned. Final completed-phase observations
were 33,591,105 control bytes and 3,678,878 new allocated synthetic bytes,
plus the retained partial. These are selected observations, not a hard filesystem
quota, full TEMP/cache meter or continuous high-water proof.

The exact synthetic partial has a verified local compressed byte backup:
1,313,129 bytes, SHA256
`d1f3a7448eabf404279fc37d42c6f4108f3e9057ae1e33d38ccb0e5929f17336`.
The single streamed member matches 1,350,832,128 original bytes/SHA256
`696bce2bf54ddc6445a41cb96af91334c4d6548417ce2355e22bbcff495fcacf`.
Original path/identity/mtime remain. No extraction occurred; allocation/layout
restoration is not claimed. Small raw/source/protocol/review records are retained
locally. Private diagnostics, credentials, model weights and real guest images
are not uploaded in this PR.

No Gradle/JVM/Rust/Android build, emulator method, phone, ARM64, real inference,
model quality, touch, accessibility or performance result is created here.
The unchanged B88 artifact provenance keeps its original attribution. Generic
stage failures expose a finite exception category, so some safe gate causes
remain less specific; no cause is invented from that category. Actual fresh
prepare/run ordering and native SDK teardown remain unqualified until a real
approved operation. The earlier SDK15 unrecorded native CloseHandle result is
not repaired by these host checks.

Actual image retirement still awaits the pending exact nine-file approval.
After retirement, fresh admission may still refuse if capacity changes. A
separate exact-source proposal/approval must authorize this bridge's one fresh
preparation and boot; the retirement-only proposal grants neither. Your other
emulator, older model guest, shared ADB and system settings remain untouched.
Nothing is merged, released or accepted by these observations.
