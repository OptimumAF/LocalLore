# SDK14 current Story Record UI host verification

B67, 2026-11-01. Refs #14 (M10.02), supporting #13 (M09.04/M09.06).
Supporting source/host qualification is in review; full criteria stay unchecked.
Based on open/unmerged #335 `4cae8fa627862682f666a728159f8520948f7192`.
Product #337 `97d07f89`, its APKs and all58 reports remain unchanged.

## Actual execution and source

All successful host execution used clean
`7e32a553ddcb9ea98457b605b718f0bfa73b094d`,2,631 raw tracked inputs,
at `D:/Worktrees/locallore-record-controls-ui-core-v1`. Later changes are only
README and these two documents. Process-local TEMP/TMP/TMPDIR are
`D:/Dev/_Temp`. Installed Python3.14 and existing locked tools are reused;
no dependency, SDK, model or runtime is introduced/upgraded. No Android build
or tests are rerun, so existing generated reports/APKs are not replaced.

| Command / procedure | Actual result |
| --- | --- |
| First isolated host launcher, `python -I -S -B -m unittest` with the ten selected module names | Exit1,766ms owner. Ten import-loader errors because isolated Python omits the repository path; **zero actual test methods executed**. Original streams, source ZIP/maps and terminal capture retained. Not a behavioral FIRST result. |
| Corrected isolated launcher adds only the fixed D: source root before `unittest.main(module=None)`; same ten module names, verbose | **135 distinct methods PASS**,56new +79existing, zero failures/errors/skips. unittest248.131s; Windows Job owner249.199s, known cleanup and complete0-byte stdout/29,829-byte stderr. All2,631 sources unchanged before/after; preexisting fixture files unchanged. |
| Actual fixed product `record_controls_ui_build.create_manifest()`, create-only publication, then `verify_frozen_product(artifacts)` | Both genuine byte-graph checks and exact manifest replay PASS. Worker3,408ms/owner3,901ms; zero stdout/stderr, known cleanup/capture. No admission or target authority created. |
| Current nineteen DEX/source/native-chain file readback v2 | PASS987ms (1.291s command including preparation),19 exact current definitions; identical recovery copy. No SDK, native execution, build, signer or ELF audit repeated. |
| `git diff --check` | Pass before publication. |

The common host cohort is exactly:

```
scripts.tests.test_record_controls_ui_profile
scripts.tests.test_record_controls_ui_build
scripts.tests.test_record_controls_ui_controller
scripts.tests.test_record_controls_ui_activation
scripts.tests.test_profile_ui_profile
scripts.tests.test_profile_ui_build
scripts.tests.test_profile_ui_controller
scripts.tests.test_profile_ui_activation
scripts.tests.test_android_instrumentation_evidence
scripts.tests.test_presentation_process_runner_retirement
```

The corrected child command uses isolated Python with this explicit bootstrap:

```python
import sys, unittest
sys.path.insert(0, sys.argv.pop(1))  # fixed D: source root argument
unittest.main(module=None)
```

Host tests use explicitly synthetic D: byte/proof/process observations. The
controller/activation fixture mocks the native/SDK/build boundary; its tiny files
are not APKs. Separate builder tamper tests use real tiny byte graphs with explicit
private baseline/Git seams, not fabricated semantic acceptance. The genuine
product graph is checked separately as above. No fake result qualifies Android.

## Coverage and independent findings

Fifteen authority tests cover exact19 operations and24-source closure, import
purity, SDK13 retag refusal, concrete owner/client types and old-lease refusal,
build rejection before target construction, caller/claim/proof identity and all
fifteen retained metadata cleanup fields. Fifteen build tests cover the actual
B66 source/producer schema,58report pairs/479 recorded cases,109+8 recovery pairs,
raw newline/oracle/overlay drift, recorded body bounds, exact native aliases,
APK/source/control changes, held-stream identity/final checks and preservation
of the B65 missing-XML limitation.

Fifteen controller and eleven activation tests cover the full19-method graph,
44 clients with one boot observation, each new method's failure cutoff, missing/
extra/reordered/skipped/duplicate claims or methods, borrowed caller/proof,
partial capture, real JUnit framing, byte caps, deadline identity, startup barrier,
atomic stop-spent behavior and sticky unknown cleanup. Three independent directory
oracles accept exactly19 method files and refuse missing19 or extra20.

Independent review caught an inherited `range(1,15)` in the new controller's
closed-file roster before execution. The corrected fixed19 boundary and the
three new oracles pass in the common cohort. The erroneous source commit remains
in Git; no pre-fix test execution or behavioral RED is claimed. Nonowned controller
and build reviews find no remaining concrete blocker; reviewer authorship overlap
is disclosed and is not owner acceptance.

The first readback v1 used the initially reused SDK13 source path and passes973ms;
it remains with that attribution. Before host tests, Root isolates SDK14 in the
new physical D: worktree and restores the original SDK13 root clean to4cae8fa6.
Its managed-worktree API request fails because the allowed workspace parent is
not a repository; normal Git worktree creation preserves both branches and all
registrations. The v2 readback then pins the new source path with unchanged
product bytes. The one-time reader-preparation helper emits two Python invalid-
escape SyntaxWarnings; preparation/readback still exits0. Original helper/output
attribution remains. No gate is waived.

## Exact artifacts and retained evidence

Current manifest:15,977bytes, SHA256
`2fce6b6cfcbbe4c7887b124ec3cf14fde52d893d6d5199a8b1493ddb69cde96f`.
Fixed baseline:16,380bytes, SHA256
`2bcfa9dee3e8314e8fc24a10b9adec0481a31c165073c9bed9d6e54f138dc5fa`.
Current19 readback v2:21,673bytes, SHA256
`1a4f856d9c74627ee870c0a65eb6562cb43d8f4f7039338f7d7bbb41ad216e97`.

| Frozen APK | Bytes | SHA-256 |
| --- | ---: | --- |
| org.locallore.app | 28,329,835 | `05813d21eb261fc694bd48485d5a5cb656206334577e4cdd543f703b558d66ad` |
| org.locallore.app.test | 2,456,353 | `07d29a26ecf49060b7affc18b72d656559533fd947fffc42f88c53de71a3050a` |

Their recorded common signer is
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Recorded479JVM/58XML, four distinct native host cases, lint/APK audits and the
prior generated-XML preservation gap retain their original B66 attribution;
none is a new build result in B67. Nineteen concrete runtime-JUnit bodies have
130,406,568,664,553,800,451,642,490,857,395,859,1227,881,538,342,426,544,337
code units. All remain unrun on Android by this profile.

Controls/captures are under
`D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-harness-v1` and
selected recovery under the matching `D:/Dev/Recovery/LocalLore` root. Two-second
sampling plus final checks keep controls30,019,904bytes<64MiB and synthetic
fixture roots54,696,687bytes<256MiB at host completion. The fixture measurement
includes earlier fixed SDK13 fixture bases, initially12,360,024bytes; all
preexisting files are hashed before/after and unchanged. New cases use unique
folders and remain retained. This is a sampled budget, not a filesystem quota,
all-machine peak, global cache/TEMP inventory or complete generated backup.
Final documentation/source reconstruction uses the tested ZIP plus three small
overlays, without a third full source ZIP or duplicate APK/model copies.

## Ownership, boundaries and next task

Root owns integration, the additive shared retirement metadata protocol, docs,
execution and preservation. Agent A owns four new authority/owner/client/proof
adapters and fifteen tests in separate `locallore-profile-ui-contract-v1`.
Agent B owns controller/activation and tests in separate
`locallore-profile-ui-controller-v1`. Agent C owns builder/baseline/tests in
separate `locallore-profile-ui-build-v1`. All use distinct new branches.
All writer/review claims are released at final handoff. Source on the new Root
fits its64MiB budget; previous branches and original source roots remain.

M10.02 supporting host work is in review. M09.06/current-Android execution
remains blocked on matching authority and fresh guarded admission. No guest,
runtime, run-control input, authorization or admission is created here. The old
SDK13 proposal/source/APKs remain frozen and separate; no old grant is reused.
No emulator/ADB/phone discovery or lifecycle, ledger/preview/retirement, model
copy/import/inference, settings/shared-service/other-emulator action, private
upload, release or merge occurs. The shared storage guard, caps and unknown-
cleanup behavior remain active. Physical/ARM64/model/story/accessibility/causal
process-death/full-journey/release acceptance remains separate.

Next runnable task: read-only capacity/evidence preparation and an exact SDK14
run proposal for owner review. A future boot or deletion still requires its
matching approval; source/host tests alone grant neither.
