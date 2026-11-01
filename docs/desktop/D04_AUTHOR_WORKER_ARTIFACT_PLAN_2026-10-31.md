# B2 experimental worker artifact: source-only admission plan

Refs #25 D04.01/.02/.04, #31 D09.03/.05 and #21. Based on accepted
PR308/main `760a5d4b16a8abc47e08154c1ef7686995d4aa7b`.
Root owns only this document on `docs/b2-worker-build-admission-v1` in the
existing checkout. **No B2 compiler, configure, linker, worker, model or app has
run. This is not an execution grant, artifact qualification or production adoption.**

[B1](D04_AUTHOR_WORKER_CODE_VERIFICATION_2026-10-31.md) passes90 independent
validator cases and both actual translation-unit syntax modes. Its three phases
are spent. The separately named experimental target and unconsumed profile-v2
exist; no new packaged worker identity exists. The next prerequisite is an
actual artifact with truthful source, dependency, tool and manifest provenance.

## Current measured constraint and selected route

Root's read-only inventory of the preserved first clean-build directory found
213 files/318498733B: seven static libraries162065362B,134 objects146692225B,
five executables8601600B and the remaining build metadata. This is an observed
historical directory, not a measurement or exact forecast of a new build.
Current aggregate target12356228504B leaves198719368B below the original
12554947872B ceiling. The historical directory exceeds that remaining allowance
by119779365B. A comparable full fresh build cannot be admitted on this evidence.
No old cache, library, source, log or failed output will be removed to make room.

The proposed route compiles current experimental `main.cpp` and links it against
the seven already qualified, immutable dependency archives. It does not copy
their162MB, recompile upstream code, run CMake configure/Ninja in an old cache,
or alter the normal packaged artifact. Independent source feasibility review
found no `/GL` or `/LTCG` requirement in the recorded compile/link recipe.

Use two separately named output directories under the SAME existing charged
target, one fixed source basename and explicit new object/executable/journal
paths. Only those new directories receive compiler/linker/resource/manifest/PDB
side outputs. No hardlink or symlink substitutes for an ordinary retained file.
Fresh source, process, storage, tool, environment and dependency admission must
precede execution; failed output stays charged and retained with no auto-retry.

This can establish the new executable identity and, if two actual outputs match,
a targeted compile/link comparison using reused dependencies. It does **not**
establish a new clean rebuild of all dependencies, a CMake target build, inference,
quality, packaging adoption, offline OS behavior or full D09 reproducibility.
Those requirements remain open. The previous clean comparison keeps its original
source and tool attribution; it is not relabeled as experimental qualification.

## Existing dependency evidence, freshly checked

The preserved `worker-repro-clean-09` comparison records two clean paths, `first`
and `b`, at llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`. Their manifests,
compiler journals, build rules, upstream input manifests and old worker bytes
remain unchanged. The current approved normal worker is6014464B,
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`.
It remains the default staging/ModelManager pin.

Root freshly hashed the following actual ordinary files in BOTH preserved
clean-build directories. All seven pairs match in size and SHA256. These are
new read-only observations, not claims that old reports already attested these
individual archive hashes. Equal old worker executables alone would not prove
archive equality.

| Archive relative to each clean-build directory | Bytes | SHA256 |
| --- | --- | --- |
| `llama/common/llama-common.lib` |92584312 | `c7c27fc522e4c8d6a4d1438fa351189827537b6b7a47cc2cd6a49b70724f81fd` |
| `llama/src/llama.lib` |49295154 | `849236bff2ddfd074f2ff9c37f73558f78490489f308c3561a4913580d7fb1fa` |
| `llama/ggml/src/ggml.lib` |627544 | `67fba428133edde90ade740bcc1b674c14bebb902f996b8af3625417c6de90f4` |
| `llama/ggml/src/ggml-cpu.lib` |3594184 | `2a00d70a240f5ddd2cc66bac0186b4b2a359c3acaa2b469e0899d756f6cb90a6` |
| `llama/ggml/src/ggml-base.lib` |5863830 | `68b1874bf587385c633531e084a112047272561a48df73fb10363576b01503b1` |
| `llama/common/llama-common-base.lib` |86742 | `8eadfcb42dd51614b43e7e365c34fbe7bca6348bec8a4f12507cc556f493caae` |
| `llama/vendor/cpp-httplib/cpp-httplib.lib` |10013596 | `dbdddbf9b7f806ce2fef92a75f432b21fe56520526554d91136b5e4a6f6506dc` |

Before a candidate build, verify these same pins, full upstream source/input
identity and ordinary-file containment again. Recheck afterward. Refuse a
changed/missing/reparse dependency; do not silently choose a different archive
set. The future Stage must bind the old comparison/manifests/journals alongside
these fresh pins and the current worker source/header/profile identities.
No recorded path or command string becomes execution authority.

## Closed compiler and manifest-link recipe

The future coordinator must construct fixed argv from reviewed constants,
not execute a command loaded from an old manifest. It must pin the installed
compiler/linker, Developer Shell and MT tools, and bind the historical driver
source/recipe used to derive the new fixed tool steps.
Use the same x64 MSVC14.34.31933/SDK10.0.19041.0 environment as the preserved
recipe, initialized only process-locally. Reject flag, Git, link-repro, compiler
and toolchain redirects before/after setup. Hash-bound INCLUDE/LIB/LIBPATH and
tool selection must agree with the closed admission.

Compile the current source from its physical D: worker directory with literal
`main.cpp`, `/TP`, `-DGGML_USE_CPU`, `/DWIN32`, `/D_WINDOWS`, `/EHsc`, `/O2`,
`/Ob2`, `/DNDEBUG`, `-MD`, `/Brepro`, `/experimental:deterministic`, C++17,
the recorded include roots and `/showIncludes`. Add the fixed experimental
definition `LOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1`.
Map both slash forms of the current worker, frozen upstream and each new output
directory to the same three existing virtual path identities. Explicit `/Fo`
and `/Fd` paths must remain in the new directory. Do not invoke the old generated
launcher: its source/output/journal roots are frozen to the historical build.

Preserve the recorded nonincremental manifest semantics through explicit tool
steps. The link uses the new object, explicit new output/import-library/PDB/
intermediate paths, `/version:0.0`, `/machine:x64`, `/INCREMENTAL:NO`,
`/subsystem:console` and `/Brepro`. Use the seven archives in the table's order,
then exactly kernel32, user32, gdi32, winspool, shell32, ole32, oleaut32, uuid,
comdlg32 and advapi32 SDK libraries. No inherited response file, unspecified
search path or generic shell command is accepted by the coordinator.

Those ten explicit arguments are not the complete effective library closure.
Object/archive DEFAULTLIB directives and the dynamic CRT also select SDK/CRT
libraries. The future recipe must bind their allowed resolved physical paths,
sizes and bytes and refuse unexpected resolution. Hashing LIB/LIBPATH strings
alone is not library-byte identity. Preserve the effective defaults; do not add
`/NODEFAULTLIB` or replacement libraries to force a smaller closure. That closure
collector is not yet implemented or qualified, and remains a launch prerequisite.
The newer `/LINKREPROFULLPATHRSP` option is not a solution for the pinned17.4
toolset: Microsoft documents its introduction in17.11. No upgrade is authorized.
[Microsoft option documentation](https://learn.microsoft.com/en-us/cpp/build/reference/link-repro-full-path-rsp?view=msvc-170).

The old Ninja rule's wrapper is evidence, not permission to run its `cmd.exe`
string. Primary-source inspection found the CMake3.22.1 driver accumulates tool
diagnostics internally before emitting them; an outer pipe cap would not bound
that buffer. For its nonincremental/no-user-manifest branch, it appends
`/MANIFEST` and `/MANIFESTFILE:<candidate>.manifest` to the link, then runs MT with
`/nologo /manifest <candidate>.manifest /outputresource:<candidate>;#1`.
That last value is ONE literal argv element. No RC step occurs in this branch.
[Pinned CMake source](https://raw.githubusercontent.com/Kitware/CMake/v3.22.1/Source/cmcmd.cxx),
`RunCommand`, `Parse`, `LinkNonIncremental` and `RunMT`.

The proposed coordinator therefore invokes these exact effective link/MT steps
directly, with individually bounded pipes and ordinary exit0 required for each.
This is an explicitly new closed build recipe; no CMake execution is claimed.
Do not add incremental mode, user manifests, `/notify_update`, `/MANIFEST:NO`,
or an unreviewed `/MANIFEST:EMBED` substitution. Preserve the linked pre-embed PE
as an ordinary exclusive copy before MT mutates the new candidate, and retain
both. Bound child closure and output explicitly; do not claim OS process-tree
containment if the observer cannot establish it.
Require the generated manifest to exist and bind its bytes before MT; no empty
input fallback. Record the pre-embed hash, exclusive-copy equality and final
post-embed hash. Only this planned mutation of a NEW candidate is allowed;
failed/partly embedded output remains retained and unpublishable.

Old evidence includes historical C: compatibility/TEMP paths. They remain
historical. Future cwd, source, output and TEMP/TMP must be physically D:; no old
C: project path is executed, recreated or adopted as a cache setting.

## Prospective packet and resource decision

Propose exactly six build children: compile/link/MT candidate A, then compile/
link/MT candidate B. A reads the frozen `first` upstream/archives; B reads frozen
`b`, with both complete input identities verified. Their freshly equal archives
are still reused dependencies, not two new dependency builds. No worker
executable runs. Compare retained ordinary object and final post-embed PE
bytes after both complete, preserve any mismatch and refuse an identity claim
that exceeds the measured comparison. Do not normalize/touch binaries to force
equality. Keep both candidates, objects, journals, diagnostics and side outputs.

The proposed target-growth forecast is64MiB, within the unchanged aggregate:
12356228504+67108864=12423337368B, leaving131610504B below the original ceiling.
This forecasts all retained new products and compiler/linker side outputs,
including failed ones; it is not an enforced filesystem quota. Checks before
and after each finite child detect excess and stop, without deleting anything.
Installed global tools/cache remain untouched.

No hard cap change is approved for B2. The current metadata cap is1441792B;
B1's actual final main receipt leaves metadata1381352B. A full compiler-output
reserve plus the new source/Stage cannot fit that remainder. Source preparation
must fit the existing cap before a concrete extension is presented.

For a future reviewed coordinator, propose at most36KiB source and12KiB Stage,
1KiB actual-decision,2KiB admission and768B START. Compile stdout/stderr caps
65536/4096B require the existing full `6*bytes+8192` reserve425984B. A first-child
ceiling forecast is therefore1860328B from the unchanged B2 checkpoint1381352B.
Use a whole-packet retained-record forecast384KiB, including source, metadata,
encoded/decoded log charges and failed records. Whole-record plus another full
compiler reserve forecasts1381352+393216+425984=2200552B.

Only after the actual guard source, Stage projection and independent review,
a possible decision would raise retained metadata1408→2176KiB (+768KiB), giving
2228224B and27672B margin for that conservative whole-packet/full-compiler
forecast. This is a proposal, not permission or actual admission. The original
4GiB target ceiling,64MiB group,724MiB joint, old576KiB records,8MiB fixtures,
all prior records and the B1 checkpoint/forecast remain unchanged. Fresh actual
full reserves and ownership observations are still mandatory before every child.

No new run is approved, scheduled or inferred from the full goal continuing.
The actual source size, tool/input hashes, fixture/proof bindings, link caps,
finite timeouts, output roster and stop/cleanup rules must be frozen and reviewed
before an owner sees a concrete execution decision. No automatic retry, extra
root, cap reset, evidence deletion or relabeling can make this fit.

The coordinator must also define and charge retained compiler temporary output
and descendant resource/manifest files; setting TEMP/TMP to D: alone is not a
storage bound. Unknown ownership or an incomplete output roster refuses launch.

## Artifact identity is not Author authority

If the six build children and comparison eventually pass, bind the NEW actual
candidate artifact hash to the immutable experimental manifest and source/tool/
dependency recipe. The manifest raw-file hash and Rust's sorted semantic JSON
digest are distinct; do not invent either or relabel the legacy global getter.
No candidate is automatically copied over the approved normal worker.

Actual worker protocol/model qualification and fixed packaged adoption are
separate, still unadmitted steps. Only an explicitly qualified owner-selecting
constructor may later mint private production Author capability, on the SAME
existing LocalRuntime/SharedRuntime/RuntimeProvider. Caller-supplied hashes,
profile text, role text, public booleans or a foreign owner token cannot grant it.
Default/arbitrary-expected-hash constructors stay Disabled. Preserve startup
failure ownership, singleton reservation, cancellation and cleanup throughout.

No new canonical state, persistence, schema validator, model backend or memory
implementation belongs here. Host validation/review/create/retry and observer
filtering stay authoritative. The original-story consumer waits for this actual
capability. B34/Eval descriptor ownership and B35/B36/Android/lock work remain
separate; no old tuple or report is rewritten. No app/model/device/OS run,
download, release or settings change is included in this artifact proposal.
