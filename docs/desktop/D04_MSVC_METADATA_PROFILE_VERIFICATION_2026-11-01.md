# MSVC metadata profile: actual bounded code checks

Refs #25 D04.01/.02/.04 supporting prerequisite, #31 D09.03 and #21.
Source revision `041bd4afa48c669c2e50f87bcd2d9323ae784b42`, PR327, based on
accepted main `f81257bf910a0a82420cbeb20e6e9b4a30e2896b`.
**112/112 legacy cases and94/94 new profile groups passed. Code-only evidence;
no SDK/native/model/app/device execution or compatibility qualification.**

## Actual authority, sources and environment

Owner actually answered `Approve bounded code checks` to
`call_bfb7f00a83f54d88b808ad0669381eba`. The closed
[admission](D04_MSVC_METADATA_PROFILE_CODE_ADMISSION_2026-11-01.md) allowed one
Legacy child, then one Profile child only after exact Legacy pass, complete
Root readback and fresh full reserve. Both finite children are now **SPENT**.
No retry, SDK input read, native build, app/model/device launch, download,
deletion, settings change or limit increase occurred.

The [contract](D04_MSVC_METADATA_PROFILE_CONTRACT_2026-11-01.md) and
[design basis](D04_MSVC_METADATA_PROFILE_PROPOSAL_2026-11-01.md) document the
explicit metadata-only API. Independent FIRST commit
`e55baf58a45061c35ba019c7a235fae879d17682` predates the producer edit. The
module SHA256 remains
`9972c0eb4d8cf936f252b090a8f0794b0d6b5328a2245b8720cdec32d5fafa53`;
old112 test SHA `36ec3c81ec02ad4844b91ff7d0de20dae1c8665dbeef697f98476de4fc2e5022`
is unchanged; new94-group FIRST SHA
`477b31ba971bc4199e5f0915e90fb30715d1f91f5ef4217dc8fdac8523223a38`.
None of these files changed between or after the two checks.

Windows10.0.26300 x64; PowerShell7.6.5; pinned Node24.22.1, executable SHA
`d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`.
Physical chat root:
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37`.
Commands ran from its frozen `source-resource-metrics-review` checkout at
7051d46, with process-local TEMP/TMP `D:/Dev/_Temp`. Helpers/tests live in
`source-desktop-fork-review` on `feat/msvc-library-metadata-profile-v1`.
The seven Node environment overrides were refused. No tool was downloaded.

The retained23104B runner is `b2-msvc-profile-code-check-v1.ps1`, SHA
`d20241c1a40fe644e8ec3c272a7bb8867532b761088d11ac701c3d971c68ea61`.
Its independent source review and zero-error PowerShell source parse preceded
actual authority. Parsing alone was not counted as test execution.

## Commands and actual results

Here `$packet` is the existing physical chat-root child
`author-integration-artifacts/d08-fork-native-20261030-v1`. Exactly once each:

```powershell
& "$packet/b2-msvc-profile-code-check-v1.ps1" -Check legacy
# Complete Root readback and fresh reserve, then:
& "$packet/b2-msvc-profile-code-check-v1.ps1" -Check profile
```

The children execute pinned Node with, respectively,
`source-desktop-fork-review/native/llama-worker/library_inputs_test.mjs` and
`source-desktop-fork-review/native/llama-worker/library_metadata_profile_test.mjs`.
Each command is a fixed captured code check, not a general command interface.
These commands are reproducible entry points, not permission to replay spent
Stages or bypass the experiment's admission rules.

| Actual check | Child PID | Executed/pass/fail | Stopped stopwatch | Complete stdout/stderr | Exit |
| --- | --- | --- | --- | --- | --- |
| Legacy |26204 |112/112/0 |548ms |111B/0B |0 |
| Profile |45980 |94/94/0 |710ms |119B/0B |0 |

Both process records have closed=true, unknown/overflow/timedOut/
killAttempted=false, timeout30000ms, caps stdout2048B/stderr4096B and
processTreeContained=false. No OS process-tree containment is inferred.
The UTC record intervals include capture bookkeeping and are not the stopped
child stopwatch: Legacy21:09:42.5748563Z–21:09:44.4660847Z;
Profile21:10:59.2737454Z–21:11:01.3422897Z, both2026-11-01.
These durations are not SDK parser, model, native, memory or UI measurements.

Root read both actual raw binaries and canonical base64 copies, verified their
lengths/hashes, decoded the exact six-key summaries and checked both record and
raw112/112/0 or94/94/0 values. The empty failed-case arrays and zero stderr are
actual, not assumed from exit0. Owner/Stage/START/runner/source, prior evidence,
global-stop/incomplete-START fences, normal binary and target/runtime accounting
also passed. Profile admission independently bound the complete actual Legacy
proof chain. No source was edited to obtain either pass.

One initial Root Legacy readback preparation refused a wrongly composed path
before reading the program evidence. The corrected parenthesized path list
then read existing records; neither child ran again. The775B Legacy Root review
records readbackPreparationRefusals=1; the775B Profile Root review records0.
The refusal remains in the command history and is not a failed behavioral test.
Independent actual-record/report review found and corrected one wording error:
the old19 refused inputs are four fixed archive inputs plus15 SDK inputs, not
19 SDK inputs. No other concrete record/report inconsistency was found; the
review executed no checks and did not replace Root's hash/raw verification.

## Retained evidence and storage

The same local packet retains owner, both Stages/STARTs, raw stdout/stderr,
process/result records and Root reviews. All prior sources, failures and
observations remain. SHA256 bindings (leaves omit only the shared prefix
`b2-msvc-profile-code-`):

| Retained leaf | SHA256 |
| --- | --- |
| `owner-decision-v1.json` | `85da94c8c7128127fe2503481634ba2b389d2ca0f7560bd77e27a33c96233da6` |
| `legacy-stage-v1.json` | `a09644dff39fbc854e2d3d4dddd5f0375dc7ca0fdd03ee7bf951cbf031fa2412` |
| `legacy-process-v1.json` | `411fbaa50e9e3ce42b537b240d595c7379fc96b9cc4f137289e5cd642703435d` |
| `legacy-result-v1.json` | `a1f52380053666b2cfa4c324c2a16ad04298180b2a0e5e5665eabca4cbdffaa0` |
| `legacy-stdout-v1.bin` | `efdef84711f5033c4f4caef46a30b098bff99ae29770947ee63ca2d6d488143a` |
| `legacy-root-review-v1.json` | `8d6c44ce98c7202fae9600b1bfa62c708751509de75ece468049bf9064bcb5ac` |
| `profile-stage-v1.json` | `d8550c31a1efe59a3914924d96992ad0bb90f0e3f7e0a8dba8c3f124444b2739` |
| `profile-process-v1.json` | `7f1d48a7c5e6c78d10265b71d2b5c42bad39f8a684bbd608b9c123477217672c` |
| `profile-result-v1.json` | `f00438a792af61088b09e6701d6ce047133a284cb856ef745c65c294a3ee702d` |
| `profile-stdout-v1.bin` | `96b7e9573a79ef93a239a21b06a4f5d9f9391867fbe4e4f499a79d670dee9556` |
| `profile-root-review-v1.json` | `8096ca2b612a3d37f4244d80144d47355f03066635111e9864c9ee766d8a766c` |

Both empty stderr hashes are
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Raw/private packet files remain local rather than being uploaded to Git.

Actual owner883B and Legacy Stage442B brought metadata to1648846B;
full38912B first reserve forecast1687758B fit the1703936B cap. After actual
Legacy output and Root review, metadata1652181B; Profile Stage452B brought it
to1652633B, and its fresh full reserve forecast1691545B left12391B. The second
child was admitted from actual retained costs, not simultaneous worst cases.

After both actual Root reviews: metadata1656006B of1703936B, group53857071B
of67108864B, joint736178565B of759169024B. Target12356228504B and runtime
fixtures210B did not grow. Old F physical549989B/logical570664B and browser
41584016B stay unchanged. No cap increased and no prior output was deleted.
The normal unlaunched desktop executable retains SHA
`7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192`.

## Scope and remaining gates

The original strict cases passed unchanged; the new94 groups exercise explicit
selection, exact public shapes, sticky job accounting and three narrow metadata
interpretations against synthetic adversaries. Its one actual256MiB backing
allocation and logical512MiB view charging are synthetic tests, not a measured
peak-memory profile. No filesystem input/read-byte collector was tested.

Engine/Rust, frontend/headless render, native WebView/IPC/render, Android/device,
real SDK compatibility, compiler/link/MT, real worker/model, OS-offline/privacy,
packaging and release checks were not run for this Buffer-only change. This PR
does not touch those implementations or qualify their gates. Existing19 strict
input refusals and all earlier failed/spent records keep their outcomes.

Next runnable work after this code slice is accepted: prepare a separately
reviewed fixed32-input profile collector, retaining strict/profile verdicts and
the job/read budgets. Its real input reads require a separate applicable
decision; this spent code grant permits none. DEFAULTLIB closure and worker
adoption remain later work. Author stays Disabled; full D04/D09, model-quality
and desktop epic acceptance remain open. No desktop control occurred.
