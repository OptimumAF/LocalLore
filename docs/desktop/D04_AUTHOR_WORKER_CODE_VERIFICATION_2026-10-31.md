# D04 B1 worker admission code verification, 2026-10-31

Refs #25 D04.02/.04, #9, #21 and PR308. The unchanged independent validator
passes all90 cases, and the actual worker translation unit passes two syntax
checks. **No new worker executable was linked or launched. Production Author
access remains Disabled; original-story UI and full D04 remain incomplete.**

This implements the [frozen B1 contract](D04_AUTHOR_WORKER_ADMISSION_CONTRACT_2026-10-31.md)
after the [bounded admission plan](D04_AUTHOR_WORKER_CODE_ADMISSION_2026-10-31.md).
That plan's pending-decision text records its preapproval state. The owner later
explicitly approved ONLY metadata1344→1408KiB and the bounded B1 code checks,
keeping all other limits and prior output. Local actual-decision and Stage
records bind that direct user message; no unavailable question-call ID is invented.

## Source and behavior

Accepted base is PR301/main `3cea6a53caed58794075070e5a9adb7cf70eb45d`.
Independent FIRST `470bb46b` was integrated as `7216fa67`; old-behavior extraction
`b31bfe14` as `d4c9f613`. The actual baseline used PR308 head
`0b9baf8ba4e5316b9b0b9b020f50c865e98a74ca`.
Different-author implementation `114a09ed` was integrated and actually tested at
`85351b6aee601bf332c93b154d00fa231def2579`. Only documentation follows that source.

`worker_generation.h` validates the exact four generation fields and returns
the requested token count plus an operation-local text cap. Legacy/default
admission still accepts only director/narrator1..350 tokens with16384 text bytes.
The explicitly selected experimental policy additionally permits Author1..1024,
an object schema, a nonempty NUL-free prompt up to16384 UTF-8 bytes, and8192 text
bytes. Type/range checks precede narrowing. Play does not acquire Author's prompt
ceiling. Unknown policies, roles and extra fields fail closed.

Main retains model-load error precedence, computes the limits once and captures
them by value in its existing operation. The same limits reach the token loop
and both intermediate/final content checks. The existing ordered schema goes
to the same template and grammar compiler. There is no new canonical validator,
runtime owner, model registry, command authority or mutable last-role setting.

Only the new `locallore-llama-worker-initial-world-v1` EXCLUDE_FROM_ALL target has
the PRIVATE `LOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1` definition. No wire field,
CLI flag, environment variable or editable profile enables that mode at runtime.
The normal target stays legacy. Its accepted packaged bytes are not replaced.

The new self-contained manifest-v2 has the experimental profile ID, closed
director/narrator/author limit map and `source_only_unqualified` status. Other
model/runtime/template/sampling/context/deadline values match the old manifest.
It is unconsumed metadata. Rust's legacy profile/getter, production gates, pins,
ModelManager, Host, Android, locks and Eval descriptors are unchanged.

The reproduction script now copies the required new header, test and manifest.
Its three built targets and compiler-journal assertions remain legacy-only.
It was not executed here. Both worker targets share the `main.cpp` journal key:
experimental qualification must first resolve or separately isolate that evidence
within an admitted aggregate. Building both into one journal is not qualified.

## Actual checks and evidence class

| Check | Actual result | Recorded child time | Complete stdout/stderr |
| --- | --- | --- | --- |
| Old-behavior validator compile | Exit0 |2.456s |28/0B |
| Old-behavior independent FIRST |90 executed,80 passed,10 failed,0 ignored; exit1 |0.449s |220/0B |
| Implementation validator compile | Exit0 |2.250s |28/0B |
| Unchanged FIRST |90 passed,0 failed,0 ignored; exit0 |0.512s |160/0B |
| Actual `main.cpp`, default mode, `/Zs` | Exit0 |2.505s |10/0B |
| Actual `main.cpp`, experimental definition, `/Zs` | Exit0 |2.258s |10/0B |

Baseline failed IDs were P11/P12/P13, T03/T05/T11/T12, C02 and I01/I02:
the actual extracted header still refused Author in both policies. Fixture
construction succeeded (`setup_unrun=false`); all90 finite cases executed.
The complete behavior summary, expected exit1 and normal closure make this RED,
not a missing-header/compiler/setup result. Later predicates in the baseline's
I01/I02 conjunctions were short-circuited; the passing implementation establishes
those remaining copied-limit/interleaving obligations. FIRST stayed byte-identical.
Its original source-only comment records the frozen test's authorship stage.

All six children closed with expected status and complete bounded logs, without
timeout, overflow, kill, unknown closure or forecast miss. Root read every raw
log and rechecked recorded hashes, phase/source bindings and retained products.
Independent baseline and implementation source reviews found no actionable blocker.
Times above are recorded spawn-to-close code-check costs, not inference latency.

The validator is an actual compiled C++ executable exercising the production
header against DOM fixtures. The two `/Zs` checks parse the actual worker source
and generator include in both modes; they produce no worker executable.
They are **not** linked-worker, CMake, raw-protocol, model, native IPC or render
execution. No UI changes or render images are involved in this packet.

## Environment and reproducible commands

Windows x64; installed64-bit Windows PowerShell5.1.26100.9818;
MSVC19.34.31937.0 compiler/14.34.31937.0 linker from toolset14.34.31933;
Windows SDK10.0.19041.0; Node24.22.1 coordinator. The read-only llama.cpp source
was clean at `620d2225cc436ab0b001e3200e590e3b286ef9ab`, with eight directly bound
headers including its existing JSON dependency. No downloads, upgrades, global
environment changes or in-place vendor configuration occurred.

The installed Developer Shell was initialized process-locally with fixed x64,
SDK and toolset arguments. TEMP/TMP and all project output remained physically D:.
The existing aggregate target was reused; baseline and passing `.exe`/`.obj`
files occupy separate fixed names and remain retained. No app build was overwritten.

Root's actual closed coordinator invocations, from the physical source checkout,
were the following three commands, each exactly once after its fresh admission:

```powershell
$env:TEMP='D:/Dev/_Temp'
$env:TMP='D:/Dev/_Temp'
& 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe' -NoProfile -NonInteractive -File '../author-integration-artifacts/d08-fork-native-20261030-v1/b1-admit.ps1' -Phase baseline
& 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe' -NoProfile -NonInteractive -File '../author-integration-artifacts/d08-fork-native-20261030-v1/b1-admit.ps1' -Phase green
& 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe' -NoProfile -NonInteractive -File '../author-integration-artifacts/d08-fork-native-20261030-v1/b1-admit.ps1' -Phase finish
```

Those retained local guards are not a reusable run grant: all three phases are
spent. The coordinator used fixed compiler argv, source/tool/environment digests,
fresh process observations, complete output reserves and exclusive record creation.
Compiler/linker output redirects and Git environment overrides were refused.
Its exact source hashes are in the admission plan; generated records stay local.

For a separately admitted developer reproduction, these are the child argv
templates. Set `$Repo`, `$Vendor` and `$Out` to the physical D: checkout, the
reviewed local vendor copy and an admitted output directory, and use the pinned
compiler environment above. `$Mode` is `baseline` at the baseline revision or
`green` at the implementation revision; retain both products.

```powershell
$Cl='C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.34.31933/bin/Hostx64/x64/cl.exe'
$Base=@('/nologo','/EHsc','/std:c++17','/O2','/MD','/utf-8')
$Includes=@("/I$Repo/native/llama-worker/","/I$Vendor/vendor")
& $Cl @Base @Includes "/Fo$Out/$Mode.obj" "/Fe$Out/$Mode.exe" "$Repo/native/llama-worker/worker_generation_test.cpp"
& "$Out/$Mode.exe"
$SyntaxIncludes=@("/I$Vendor/common","/I$Vendor/include","/I$Vendor/ggml/include","/I$Vendor/src")
& $Cl @Base /Zs @Includes @SyntaxIncludes "$Repo/native/llama-worker/main.cpp"
& $Cl @Base /Zs @Includes @SyntaxIncludes /DLOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1 "$Repo/native/llama-worker/main.cpp"
```

Baseline exit1 requires its complete90-case summary; compilation failure is not
RED. The admitted local coordinator additionally enforced all limits in the plan.
Do not run the historical reproduction/build caches or restart spent phases to
substitute for a fresh admission.

## Retained identities and resource accounting

| Record/input | SHA256 |
| --- | --- |
| Actual owner decision | `33b95b410586061a430c8698890eb19422161fc495fe03721d26749419eb22df` |
| Actual B1 Stage | `59d3b4874d2428955083f73536ef118f91b3a1452d1e89c870de5bbe58aaa98c` |
| Baseline phase | `b312383797b95ffd33794c96a2efe3925d10628aa51e3ba4b90d58b9f866c272` |
| Root baseline review | `9f8aaf96e30dbdefaf41f05dd0fc691647afbf45ceb910c4c6936aab71474ecc` |
| Root source review | `db5dfa410886a0c5fe348f2a769e90917379f26e2df361e97d67d2c3c05ed9eb` |
| Passing phase | `b22439ef85781fabd799ffa46cef2c031d856312260c7217c9c2e593d958e39f` |
| Syntax phase | `920068d161eb9c65eb9ccbd4d2c6086a21e65856a1d1dea985a255f69a1e9026` |
| Root final code review | `bb3e5d39c2669993a7a07b4ba40d320694a2d1060a079d8c831c6d0da90f8baa` |
| Frozen independent test | `4e018d21c7421970406f4672bd4f049911d0cc3664faeb95fc1e69ae6c8400f4` |
| Production admission header | `6b8a1d0de996d81b93cbc58535dac575712e461960d9ae4fd1bc290303423452` |
| New unconsumed manifest | `2abf5fcf191b75de5bbddc5da8d97a0488892d588800b0e1ba2bc5402e1bb11d` |

Retained baseline executable202752B:
`7998d72f17590ff62d1266c3ad48ecfb3ff718e5f8482ac1f1be39d56b143e5a`;
baseline object4842040B:
`f1e9d7a4c9aa09e425a5735cb7afb46c00087f2caa56223c7977ebf8a054736a`.
Passing executable203776B:
`a7b17a232624f4aaa9a5a06da6d80ff09fa4bb3d63b53fb200bc85128e1bcb52`;
passing object4845800B:
`85e417d1fba7b64ee3514db4b5c527b565a9a9b4fa46b2de889d97109418f53f`.

After the1802-byte Root final review, actual retained metadata is1380585B
(cap1441792), B records74131B from the unchanged1306454B checkpoint
(forecast98304), group53581650B (64MiB), joint735903144B (724MiB).
Target12356228504B grew10094368B (forecast16MiB); the original target ceiling
12554947872B remains unchanged. Old records, decoded-source charges, all failures
and all71 runtime fixture roots/210B with exact fingerprints remain preserved.
No new fixture roots were made. Fresh post-check Windows PowerShell CIM observed
503 process rows,0 owned and0 ambiguous; this is not OS process-tree containment.

The normal desktop executable remains unchanged and unlaunched,42246144B,
`7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192`.
The accepted Rust source and frontend identities remained guarded throughout.
No restoration or fresh Rust/frontend/Android check was needed or claimed here.
PR301's earlier test/build results keep their own source attribution.

## Unavailable gates and next work

CMake configure/build, new worker linking, byte reproducibility, raw duplicate-key
and UTF-8 protocol behavior, grammar execution, inference cleanup, model quality,
native UI, Android/device and offline OS qualification were not run by B1.
The existing unloaded-worker protocol test would hit `model_load_failed` before
generation admission, so it is not substituted for these90 cases.
No new worker hash, packaged provenance or production Author capability is minted.

B2 must qualify an actual experimental artifact and resolve its immutable
manifest/profile identity before a fixed packaged constructor can grant access
on the same owned runtime/provider. Arbitrary expected-hash/default constructors
stay Disabled. ModelManager singleton/cleanup ownership and shared Host validation,
review, cancellation, retry and canonical authority remain authoritative.
Eval/new-descriptor work remains with its current owner; old tuples and reports
are not relabeled. Original-story UI follows that capability, not mere provider
presence. Existing D07 human quality remains needs improvement.

The existing medium GLib advisory remains open under the separate
[D09 target-scope report](D09_GLIB_ADVISORY_SCOPE_2026-10-23.md); B1 changes no
dependency or lock. Full D04/D09/desktop acceptance and release readiness are not
established by this source/test slice. No release or settings change occurred.
