# Archive import permission and passive reader fix

Refs #12 (M08.04/M08.06), #13 (M09.06), #14 (M10.02; supporting M10.03).
This follow-up is stacked on unmerged presentation PR #223 at `cf6d47d5`.
No merge is authorized; full task criteria and checkboxes remain unchanged.

## Original failures and changes

The preceding current850 retained-archive run executes both tests and fails
both assertions. Its [original report and verified private recovery](ANDROID_STORY_PRESENTATION_2026-10-27.md#subsequent-choice-pass-and-retained-archive-failures)
remain unchanged. The first observes WRITE permission on its selected import
URI. The second observes a rejected native resume, without its error category.

MainActivity now imports one openable content copy using the existing AndroidX
GetContent API and exact three MIME types. Consent, captured resolver, bounded
read, cancellation and native archive validation/commit remain unchanged.
The [platform's OpenDocument contract](https://developer.android.com/reference/android/content/Intent#ACTION_OPEN_DOCUMENT)
grants document read/write access; this app needs only one read. No new runtime,
dependency, storage permission or persisted grant is introduced.

The passive fixture previously resumed all catalog scopes through one native
Host, accumulating sessions beyond its four-session limit. Its rejection code
was not retained, so SessionLimit is a source-backed explanation rather than a
captured error label. Each passive branch snapshot now owns a dedicated Host
inside `use`; the catalog reader allocates no sessions. Shared `view` stays
unchanged because it can borrow an active gateway session. Engine limits stay
unchanged. Bounded operation/error diagnostics replace the uninformative status
assertion without dumping complete replies.

Both original methods and all canonical/receipt/revision/permission comparisons
remain. Added assertions check GET_CONTENT, OPENABLE, exact MIME filters and no
requested write/persistable/prefix flags. The actual negative source WRITE
assertion must still pass through DocumentsUI. Both methods run together, with
enough cumulative eligible scopes to exercise the original reader issue.

Android author commit `42a6d5e7` is integrated as `c5981788`. Root and an
independent adversarial reviewer inspect the three-file diff; no concrete source
defect is found. Source review and static checks do not establish runtime success.

## Verification status

Draft [PR #224](https://github.com/OptimumAF/LocalLore/pull/224) is open and
unmerged. Executed source is `14abdace`; later documentation does not change its
850 compiled inputs. Each check captures its own unchanged before/after map;
host checks cover1,968 tracked files. Rust1.93.1, Python3.14.7, JDK21,
Gradle8.11.1, AGP8.10.1, existing AndroidX Activity1.10.1, NDK29.0.14206865 and
API35 pins remain unchanged. All commands use the existing offline dependencies.

| Actual check | Result | Owned elapsed |
|---|---|---|
| Core Rust, all features | 434 passed /4 ignored | 68,487ms0 |
| Storage Rust, all features | 239 passed /6 ignored | 389,547ms0 |
| Workspace Rust, development fixtures | 162 passed /1 ignored | 112,399ms0 |
| Python host suite | 1,493 run,0 failures/errors/skips | 159,549ms0 |
| Desktop frontend/format | Passed | 26,060ms0 |
| Strict Clippy,3 packages/all targets/all features | Passed | 8,452ms0 |
| Unified Android build | Passed;282 JVM tests/33 suites | 113,523ms0 |
| Lints/artifact audits | 0 errors/3 existing warnings;11 audits | Included in build |
| Fresh native component phase | All10 methods/3 classes passed | 262,093ms0 |
| Fresh retained-archive phase | Both methods passed; JUnit36.935s | 242,660ms0 |

All owned checks retain complete capture/cleanup. The Rust total is835 passed,
11 ignored,0 failed; ignored cases are not claimed as executed. The native gate
and archive phase use separate fresh, standard API35 Google APIs/x86_64 guests,
2GiB/two CPUs, in new dedicated D: directories. C: retains the metadata and
recoveries. Existing drive-aware free-space, RAM/commit floors,900s phase/850s
SDK/180s class/1,200s guest bounds and fixed rosters remain unchanged.

The existing driver commands are:

```text
python -I -B benchmarks/android_process_verification.py build --out <new-build> --sdk <sdk> --java <jdk21>
python -I -B benchmarks/android_process_verification.py components --out <new-native> --sdk <sdk> --powershell <powershell> --build <new-build>/result-v1.json --proposal <native-run> --running <native-running> --server <server>
python -I -B benchmarks/android_process_verification.py retained-archive --out <new-archive> --sdk <sdk> --powershell <powershell> --build <new-build>/result-v1.json --proposal <archive-run> --running <archive-running> --server <server>
```

Only Root executes environment/device work. Fresh admission deep-replays all
six host gates and the build before its new read-only emulator inventory and
existing-server observation. The captured protected inventory is0; this is not
an inherited count or an all-time process-absence claim. The server matches the
prior pin. Neither guest is reused for the next phase: the existing driver
requires all3 verification packages absent before installation. Archive
preparation additionally requires the completed current native gate, measured
SDK2 clients and its exact known requested guest closure. No uninstall bypass
or lower acceptance threshold is introduced.

Native has93 complete measured SDK2 pairs (30 SDK/63 observers); archive has81
(26 SDK/55 observers). Corrected file-only readback checks every original raw
capture, exact roster, source map, APK binding, observer server identity and
observer brackets around every SDK call. A review catches a gap in an
unexecuted recovery draft, which omitted those last observer checks; v2 restores
them before execution. The original draft is retained as defective unexecuted
source, not an observed runtime failure or evidence of a wrong server.

Both retained methods execute together. The successful run keeps the source
READ grant, denies its WRITE grant, denies unread fixture access, and takes no
persisted grant. Exact retained-parent export bytes and original receipts
survive import; the retired parent's ID stays reserved. Child-only continuation
reaches revision3, keeps the first two receipts, spends the potion once and
rejects reuse. Future/malformed/conflicting archives and explicit cancellation
preserve all earlier story metadata, branch catalogs and eligible canonical
views. The passive reader fix permits the cumulative catalog scan without
changing the engine session cap or closing a borrowed gateway session.

Root requests each exact proposal-bound STOP only after the phase terminates
with known client capture/cleanup. Both stop helpers and original owned guest
handles terminate0. Native/archive guest records retain requested closure,
worker1, known cleanup/capture/closure and no guest-flush claim at291,226ms and
271,075ms respectively. One final read-only postflight checks both exact
closures/stops/proposals, fresh inventory/raw bindings and the unchanged
existing server, with0 new device calls/no lifecycle action. The existing
server remains running. No unrelated emulator is stopped or system setting
changed.

## Artifact bindings and preservation

Compiled map:850 entries/109862 bytes, SHA256
`f177463c365f536914263ed2b254f6d2c81d0b516d7ee593e53e6fae8b6a7f62`.
APKs are copied and audited before installation:

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Product | 32849224 | `098d801fc75c41b65609ab2a6ca47d54429c805ab4ab973050b77a8273d661b4` |
| Instrumentation | 3140634 | `b9e7dc86ee8f50514f43f0afea05ddba32e3cbc585f36a53776f0ea67881ba9b` |
| Controller | 55073 | `6ea09f4c5105d62e61498d2bebc05de52ce597e30b9681e4975a323b36ef7693` |

Before editing, the original failed UI packet is preserved and independently
replayed:442 originals/copies/ZIP members,1,367,175 bytes,0 missing/mismatch.
Its hashes and explicit `qualified=false` scope remain in the preceding report.

Fresh host/build recovery retains183 originals/copies/ZIP members,40,970,134
bytes, including all3 APKs; independent replay finds0 missing/mismatch.
Index64885-byte SHA256:
`f643a5de2b71c5a93f7a8b4ac26d75d18b36748110ea63870e213dfaaec03089`.
ZIP19938224-byte SHA256:
`631b0bd62e5d295b3454990670440d095425333575b1a98418cff80704b54557`.

The successful runtime recovery retains433 bounded metadata/helper/raw files,
1,522,215 bytes, with exact originals/copies/ZIP verification. Independent
file-only deep replay passes in5.927s with0 missing/mismatch, including both
raw rosters, every measured SDK2 capture/server bracket, current source/build,
requested guest closures and final postflight. It copies the new host/build and
original failed indices as references and rechecks their artifacts without
duplicating payloads. Index140904-byte SHA256:
`37e29a7921b2f1f2ce781100edcc9278a634c6fd9deb332f564220c86e0f3a22`.
ZIP505192-byte SHA256:
`daa0ad71efdd601427bcdb3b992ce9d1ff3db397557eb1d96f1fd8223e51d40a`.
All recoveries are create-only on C:. No existing D: file is moved/deleted;
model/save/card payloads and private raw diagnostics are not uploaded to GitHub.

## Status and limits

M08.04/M08.06/M09.06/M10.02 supporting fix is locally verified and in review;
full milestone criteria/checklists and owner acceptance remain unchanged.
Scripted API35/x86_64 tests do not qualify physical devices, ARM64 execution,
model quality/performance, hostile providers, external OS-death or production
joined drain. Product adapter close remains asynchronous; dedicated test-reader
close does not establish that separate gate. Current-source broad89, creation19
and custom-presentation8 are not rerun by this focused packet; parent reports
retain their exact source attribution. The latest complete native/archive
device-list captures establish the admitted SDK emulator for each run; no
physical-phone result or absolute phone-absence claim follows.

The next runnable implementation remains M09.02 bounded original premise and
character authoring behind native validation/review. Outstanding accessibility,
current-source lifecycle and device/model qualification remain separate gates.
Original failed evidence stays failed. No dependency, server lifecycle,
permission administration, release, private upload or merge occurs.
