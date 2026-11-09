# Proposed desktop archive code check

Refs #30 (D08.01/.02/.03/.07), #31 (D09.03/.07), and #440.
This is an unrun proposal for a separate owner decision. It does not
authorize retaining a packet or starting a child.

## Fixed check

Use the clean existing Windows D: review checkout at
`78c4435a3d1f7b8c8acdb5ce4288172ef86b6d4d`. The launcher is reviewed
separately from that test head. One Node process runs the unchanged
`apps/desktop/check-archive-controller.mjs`, then
`apps/desktop/check-archive-v3-selection.mjs` only after the first check
returns successfully and its single bundle passes the roster and size guard.
Both checks use synthetic IPC replies, the actual TypeScript controller and
React server rendering. The selection check invokes actual rendered component
callbacks and reports 13 cases. It does not mount App/main, run Tauri or
WebView2, interact with a file chooser, or exercise Rust/Android IPC.

Use only the installed Node 24.22.1 Windows x64 executable and one installed
esbuild 0.28.2 service. The launcher pins the executables, esbuild JS and
package manifests, the two checker files, and the archive panel. It also pins
the ordinary file rosters of installed React 19.3.1, React DOM 19.3.1 and
Scheduler 0.28.0. The roster digest is SHA-256 over ordinal-sorted UTF-8
`relative/path|bytes|lowercase SHA-256` rows, each with one LF. The launcher
refuses observed dependency shadows on the source path and ignored UI inputs.

The preload maps the two checkers' exact esbuild imports to a fixed build
adapter. The adapter supplies one esbuild
[`nodePaths` directory](https://esbuild.github.io/api/#node-paths) for the
separately installed dependencies, checks the bundle's input list against the
source and three pinned package roots plus the two checker virtual entries,
and refuses oversized output before returning it to the checker for writing.
The selection check's JSX callback observer and assertions remain intact.
The launcher does not accept a command, path, test selector, or install
request. The child environment excludes caller-supplied Node and esbuild
overrides and routes temporary files to the fixed packet scratch directory.
No dependency provisioning or network access is part of the run.

## Retention and admission

Keep every previous output, failure and STOP marker. Use only one new
create-only packet named `d08-archive-440-v1` in the existing D09 frontend
evidence group. Reserve 4 MiB including the launcher and all records, two
bundles of up to 1,792 KiB each, a selection JSON report of up to 16 KiB,
scratch up to 64 KiB, and up to 4 KiB raw per output stream. Earlier D09
bundles for these two checks were 1,527,884 and 1,511,092 bytes, plus a
1,767-byte selection report. Those retained products justify the forecast.
They do not prove the outputs at this test head will fit.

| Scope | Advisory baseline | With full 4 MiB reserve | Existing limit |
| --- | ---: | ---: | ---: |
| D09 frontend evidence group | 40,267,990 B | 44,462,294 B | 64 MiB |
| D09 named aggregate | 622,137,172 B | 626,331,476 B | 640 MiB |
| Cross-track joint evidence | 737,583,378 B | 741,777,682 B | 724 MiB |

The named aggregate retains the historical Selected4 charge of 501,644,653 B,
the D05 charge of 79,500,962 B including escaped files, and 723,567 B of
guarded normal products. The joint baseline carries the last verified D04
joint charge including 31,791 B of conservative carry. The live D04 group
was 55,230,062 B at this source inspection. Measure the actual current named
inventories and charge all growth since the recorded baselines before use.
The launcher refuses a measured group smaller than either reference and
charges positive growth in both groups to its minimum joint count. Fresh
outside review still accounts for changes in all other named roots and carry.
These are advisory figures, not reusable admissions or authority to reclassify
or erase previous evidence. There is no cap increase and no target or fixture
growth reservation.

Before writing anything into the evidence group, obtain one explicit owner
decision for the reviewed launcher and the exact test head. Recheck the
physical D: roots, fixed runtime files, free space, prior failure fences,
current process ownership, absence of this packet name and the full reserves.
The separately reviewed retention step creates only the fixed packet,
`bundle`, `_tmp`, the exact launcher, `owner.json` and `stage.json`.
Verify exact retained-source equality and get independent retained-source and
inventory review before invoking the launcher. The existing D04 and D05
requests remain separate.

`owner.json` binds kind `d08_archive_440_owner_v1`, the actual approval
reference, approved boolean, test head and launcher SHA-256. `stage.json`
binds kind `d08_archive_440_stage_v1`, owner digest, test head, launcher
digest, measured UTC and the three verified baselines before packet retention.
The launcher checks that stage age is at most 120 seconds at start. From the
fixed physical D: checkout, invoke only that retained launcher with no
arguments. The create-new `start.json` marker binds both reviewed records
and the resolver/adapter source hashes before the child starts. Preserve
refusals and all files. No automatic retry or duplicate packet.

The child has 30 seconds plus a bounded five-second closure grace after one
best-effort stop request. Successful evidence requires a known Node exit and
pipe closure, an observed esbuild close, exit 0, both check outcomes, and the
matching closed bundle/report roster with hashes. Missing closure requires
quarantine and independent follow-up. This is cooperative evidence accounting
with a trusted finite toolchain. It does not impose a filesystem quota or
prove process-tree containment. No app, worker, model, SDK, device, desktop
control, settings, download or cleanup is admitted by this proposal.
