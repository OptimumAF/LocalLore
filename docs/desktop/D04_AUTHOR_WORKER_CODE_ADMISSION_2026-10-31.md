# B1 worker admission: proposed bounded code checks

Refs #25 D04.02/.04, #9 and draft PR308. **The source is prepared and reviewed;
no B compiler, validator executable, worker, model or app has run.** The next
execution requires an actual metadata-extension decision and fresh admission.
This document itself grants no new allowance.

## Exact source and evidence classes

The [frozen contract](D04_AUTHOR_WORKER_ADMISSION_CONTRACT_2026-10-31.md) defines
the actual C++17 header interface and future experimental-mode boundary.
Independent FIRST `470bb46b` contains90 unique finite cases in one executable;
production extraction `b31bfe14` keeps both named modes Play-only. They are
integrated at `d4c9f6136d2d442eec8f021ef0460ddce5cd99b0`, with source cross-review
and whitespace checks, but remain uncompiled/unrun. No RED or GREEN is claimed.

FIRST includes the actual production header. It parses realistic unsigned JSON
controls, checks exact requested counts, shape/types/schema/roles, both policy
modes, limits and UTF-8 byte boundaries, copied limits and input immutability.
It emits one fixed JSON summary below1024B, with counts and short failed IDs;
no raw prompts or exception messages. Exit0 means all pass,1 behavioral failure,
2 fixture/setup failure. Missing header/compiler or incomplete capture is setup
or unverified evidence, never behavioral RED.

DOM validation cannot establish raw framing, duplicate-key rejection, grammar,
actual generation, cleanup under inference, model quality or UI behavior.
The old reproduction source-copy roster temporarily omits the new header; that
qualifier is excluded until its separately allocated update. Historical artifacts
and their qualification do not change.

## Closed sequence

1. Baseline: compile the fixed validator test, then require a complete actual
   90-case failure summary and known child closure. Root must read the raw logs
   and record valid behavioral RED before feature implementation.
2. A different author implements experimental admission, the unconsumed manifest
   and fixed target integration. Frozen FIRST stays byte-identical. Root reviews
   exact source/control bindings before GREEN.
3. GREEN: compile a separately retained executable and require90 passed,0 failed,
   0 ignored, no setup failure.
4. Finish: syntax-check the actual worker translation unit in the two fixed
   compile-definition modes. These checks create no worker executable and execute
   no inference. They do not qualify linking, CMake configuration, reproducibility,
   packaged artifacts, model execution or application adoption.

The fixed command builder uses existing MSVC19.34.31937.0 x64 and SDK10.0.19041.0,
process-local Developer Shell initialization and TEMP/TMP `D:/Dev/_Temp`.
The pure executable links the existing JSON interface and standard runtime only.
Compiler source/arguments, output paths and two syntax modes are closed constants,
never commands supplied by a renderer or model. `/Zs` checks syntax without
producing output files; its diagnostics use stdout. [Microsoft documentation](https://learn.microsoft.com/en-us/cpp/build/reference/zs-syntax-check-only?view=msvc-170).

| Child | Timeout | Stdout/stderr caps | Complete pre-child reserve |
| --- | --- | --- | --- |
| Validator compile |120s |4096/1024B |38912B |
| Validator test |30s |2048/512B |23552B |
| Each syntax check |120s |2048/1024B |26624B |

Any unexpected child result, overflow, unknown closure or boundary failure stops
the sequence. The valid old-behavior baseline's exit1 is intentional.
There is one kill attempt and at most5s pipe drain; unknown ownership remains
unknown. No automatic retry, detached replacement or spent phase reuse.

## Guard and provenance preparation

The separate local source pair is36,551B: `b1-code-checks.mjs`24,781B, SHA256
`5325efbbdd96b5692523a6c0d97704475a54aa0159112cc7ca48d1345df2af0e`;
`b1-admit.ps1`11,770B, SHA256
`150a487808edf2fd0dd18b29dae481c44eee6656821b1307be34cf1308b0204f`.
Node24.22.1 syntax check exited0; actual Windows PowerShell5.1 parser reported0
errors. A pure fixed-map digest check matched across PS/Node. These did not
initialize the compiler environment or execute C++.

Independent source review corrected Git worktree/config redirects, linker repro
output redirects, refusal ordering and compiler-path selection before execution.
All Git calls use fixed no-pager/no-optional-lock arguments; only inherited
GIT_PAGER is allowed among nonempty Git variables and is hash-bound. Compiler
flag and repro-output overrides are refused before/after environment setup and
in the coordinator. The standard linker can write a separate repro directory
through its environment; this is why those redirects are blocked. [Microsoft documentation](https://learn.microsoft.com/en-us/cpp/build/reference/linkreprotarget?view=msvc-170).

The actual installed host, compiler/linker, Developer Shell, Git and Node bytes
are pinned; source/tool/environment digests and fresh process observations bind
each admission. Environment values are not logged. No empty process-list fallback.
Syntax/parse/parity/source reviews are preparation evidence; actual VS setup and
compiler include completeness remain unrun.

Use only the verified physical-D read-only vendor copy at pinned llama.cpp
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. An old configured cache recording a
C: compatibility source path is preserved and excluded. There is no vendor
configuration in place, new source clone, download or new target root.
Build products use the fixed `b1-generation-admission-code` subdirectory of the
existing aggregate target, with separate baseline/green objects/executables.
Both remain retained. Shared default/experimental worker build-journal collision
is outside this model-free sequence; neither worker target is built or launched.

## Measured resource proposal

All original A failures, R2 refusal, five completed/spent R3 phases, current and
old binaries, copied source, decoded-source charges and fixtures remain retained.
Current runtime fixture inventory is71 roots/210B; original37 fingerprints plus
the additional34 are bound through old references and the projected new Stage.

The first1,406B preapproval review remains immutable as the historical64KiB-record/
32KiB-extension proposal. The final1,176B review supersedes those forecasts and
binds the source hashes above. It measures metadata1,345,587B including itself.
The actual B checkpoint stays1,306,454B, before these new sources/records;
the original target baseline is never reset.

An in-memory Stage projection is8,905B; its placeholder owner digest was used
only for sizing and was not saved as an actual Stage. Add1,024B actual-decision
reserve,1,536B admission,768B START and38,912B complete compiler reserve:
**1,396,732B**, exceeding current1,376,256B by20,476B.

The proposed decision raises ONLY metadata1344 to1408KiB
(1,376,256 to1,441,792B, plus64KiB). The full first-compiler forecast fits by
45,060B. For the entire baseline/GREEN/syntax sequence, forecast96KiB records
from the unchanged1,306,454B checkpoint:1,404,758B. Adding the complete final
syntax reserve gives1,431,382B, within the proposed cap by10,410B. These are
forecasts, not admission; actual complete reserves are checked before each child.

Target currently measures12,346,134,136B. Whole B build growth is forecast16MiB,
giving12,362,911,352B, below the unchanged original12,554,947,872B ceiling from
8,259,980,576B plus4GiB. Keep64MiB group,724MiB joint,576KiB old physical/logical
records and8MiB fixtures unchanged. No deletion, minification, new target or cap
reset is used to make the packet fit.

Actual B owner decision, Stage, admission, START, compiler and baseline remain
absent. Ordinary model-free checks are within the full assignment; increasing
the explicit hard metadata cap requires the pending actual owner decision.
That decision grants no app, model, packaged-worker, Android/device/emulator,
OS/network qualification, downloads, global setting changes, release or cleanup.
All four native app grants remain spent. Production Author remains Disabled;
B2 artifact/profile adoption, original-story UI, D04 and the epic remain open.
