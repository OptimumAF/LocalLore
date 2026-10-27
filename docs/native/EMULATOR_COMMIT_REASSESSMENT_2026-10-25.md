# Emulator commit requirement reassessment — 2026-10-25

Refs #5 (M01.05 supporting), #9 (M05.05 prerequisite); root claim6404879571,
independent claim6404886678. Source/documentation research from
`020667ddae4246aaa4c64e9dbe531cc8811607f7`; no emulator, device, model, SDK tool,
benchmark or Windows memory API was executed. No other process was stopped and
no OS, pagefile, profile or emulator setting changed.

The18GiB cutoff for an8GiB guest was an invented conservative project policy,
not the emulator's documented requirement. The version-aligned official source
does not establish a need for two simultaneous guest-sized allocations plus2GiB.
Its20% check occurs **after** an allocation fails, rather than before every
allocation. Replacing the ratio is justified by that source distinction, not by
whether a particular host snapshot passes.

## Installed metadata and source correspondence

Permitted read-only metadata inspection of the selected installation found:

- `C:/Users/Avery/AppData/Local/Android/Sdk/emulator/source.properties`:
  revision35.3.12, build12990079, package `emulator`.
- Its `package.xml` revision element independently declares35.3.12.

The initial research assumption that37.2.12 was this packet's selected emulator
was incorrect. That belongs to other project processes and was not inspected or
used. No executable was run, hashed, disassembled or replaced in this review.

Official `platform/external/qemu` branch `emu-35-3-release` resolved to
`2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a` on2026-10-25. Both
[source.properties](https://android.googlesource.com/platform/external/qemu/+/2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a/source.properties)
and [win.source.properties](https://android.googlesource.com/platform/external/qemu/+/2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a/win.source.properties)
declare35.3.12. This is a version-aligned official fork, not proof that build12990079
was compiled from exactly that commit. No authenticated build-ID-to-manifest or
binary-to-source correspondence was established.

As a cross-check, `emu-master-dev` resolved to
`ae9d18d2b6261179fbd57fffec720a04f7bfb053`, whose source revision is35.6.3;
its [Windows allocation routine](https://android.googlesource.com/platform/external/qemu/+/ae9d18d2b6261179fbd57fffec720a04f7bfb053/util/oslib-win32.c)
contains the same diagnostic ordering and1.2 factor. It is not substituted for
the installed version.

## Exact allocation and diagnostic order

The version-aligned [util/oslib-win32.c lines74–135](https://android.googlesource.com/platform/external/qemu/+/2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a/util/oslib-win32.c)
implements this sequence:

1. Request `VirtualAlloc(NULL, size, MEM_COMMIT, PAGE_READWRITE)`.
2. On success, return immediately. There is no headroom precheck here.
3. Only on failure, sample `GetPerformanceInfo`.
4. Derive committed/limit bytes from pages multiplied by `PageSize`.
   Logged MB values divide by1048576, so they are MiB despite the label.
   `Needed` is the failed call's `size`; `Remaining` is limit minus current total.
5. If `1.2 * Needed > Remaining`, emit the insufficient-RAM diagnostic,
   set `insufficientMemMessage`, and return the failed pointer.
6. Otherwise retry the same allocation once. This can still fail.

The unused local `safetyFactor` does not change the literal1.2 comparison.
The sample reflects other allocations already committed by that point, including
unrelated applications and any earlier successful emulator allocations. It is
not a pre-launch baseline. The routine does not establish that its failed
allocation remains committed, or that a successful guest allocation must coexist
with another full-size guest allocation. It also does not preserve the original
`VirtualAlloc` last-error code for this diagnostic.

Microsoft documents that [MEM_COMMIT charges memory before physical pages are touched](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc).
The diagnostic therefore must not be interpreted as a physical-free-RAM test.
The existing system commit reader correctly uses
`(CommitLimit-CommitTotal)*PageSize`, rather than process-specific
`ullAvailPageFile`; see [PERFORMANCE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-performance_information)
and [MEMORYSTATUSEX](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/ns-sysinfoapi-memorystatusex).

## Backing-file failure and fallback

For the non-NUMA PC path, [hw/i386/pc.c lines1351–1357](https://android.googlesource.com/platform/external/qemu/+/2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a/hw/i386/pc.c)
passes `machine->ram_size` to system-memory allocation once. Below/above4GiB
regions are aliases, not two guest allocations.

[numa.c lines453–475](https://android.googlesource.com/platform/external/qemu/+/2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a/numa.c)
first attempts file-backed RAM when `mem_path` exists. If it reports an error,
`mem_prealloc` makes that fatal; otherwise it reports a fallback and calls
anonymous RAM initialization with the **same** `ram_size`.

[exec.c lines1778–1845,2204–2288](https://android.googlesource.com/platform/external/qemu/+/2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a/exec.c)
rounds the requested file RAM size to its page size. It emits the backing-store
mapping message when `qemu_ram_mmap` fails, returns no RAM block, and closes the
failed file descriptor before the caller's fallback. Default anonymous
allocation reaches `qemu_anon_ram_alloc` through `phys_mem_alloc`.

In [util/mmap-alloc.c lines226–254](https://android.googlesource.com/platform/external/qemu/+/2c0f5b1ca0468e8f18e33f7ea6cb573c5a50ab7a/util/mmap-alloc.c),
the Windows path creates a file mapping of `size+align`, then maps its whole
view. Shared mode uses `FILE_MAP_ALL_ACCESS`; private mode uses `FILE_MAP_COPY`.
The mapping handle closes after `MapViewOfFile`, and failure returns `MAP_FAILED`.
This path does not capture `GetLastError` or translate it to `errno`, although
the caller formats an errno-based diagnostic. That message cannot identify the
particular failing Windows API or its cause by itself.

Microsoft specifies [whole-view commit charge for FILE_MAP_COPY](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-mapviewoffile).
That supports accounting for one guest-sized copy-on-write view plus alignment
and other overhead. It does not demonstrate two retained successful guest views
in this failed-file-mapping-to-anonymous-fallback path. Conversely, absence of a
successful returned pointer is not a measurement of every transient OS charge;
no peak/cause claim is made.

The retained log values8184.605MiB remaining and8192MiB needed are consistent
with the later allocation's diagnostic. They do not prove why the preceding
mapping attempt failed. No old target backing file was read to infer that cause.

## Recommended narrow policy

Retire `2*guest+2GiB` as an experimental admission cutoff. Keep the actual
profile, physical-memory floor, disk floors, source pins, owner/lease/one-shot
checks, deadlines and stop-on-uncertainty behavior unchanged.

A source-informed conservative replacement is pre-launch available commit of
`ceil(6*guest_bytes/5)`, calculated with integer arithmetic. This uses the fork's
20% diagnostic margin, with no extra full guest or arbitrary absolute2GiB
reserve. It is approximately2.4GiB for2GiB and9.6GiB for8GiB. Explicitly label it
**project admission policy inspired by a post-failure heuristic**, not the
emulator's mandatory precheck, an exact measured overhead or an allocation
guarantee. A successful allocation can occur below that margin because the
emulator attempts it first; passing the margin can still fail.

If a different overhead margin is selected, state its evidence and policy
separately. Do not reduce guest RAM, change pagefile/settings, stop unrelated
programs, silently relax existing resource fences, or select a threshold merely
because it admits a desired snapshot. Re-sample before the controlled launch;
do not shift time budgets while waiting for capacity.

After a guest is successfully committed, its charge is already in `CommitTotal`.
Requiring another full pre-launch guest allowance during monitoring would count
that future need again. Keep ongoing observations distinct from admission;
any residual reserve requires its own explicit policy. A snapshot reserves
nothing and is subject to concurrent allocation/pagefile changes.

[Android's current Windows troubleshooting guidance](https://developer.android.com/studio/run/emulator-troubleshooting#windows_free_ram_and_commit_charge)
confirms startup accounting for the full guest, but gives no2x+2GiB formula.
It does not establish that a passing host check resolves an earlier mapping
failure. User-authorized bounded execution and actual startup/closure evidence
remain necessary; this research does not perform or approve admission.

## Regression cases for the coordinator

- An8GiB guest and10GiB available commit should not fail the retired18GiB rule;
  less than the chosen20% margin should still refuse under that explicit policy.
- Exact integer ceiling and one-byte-below boundaries;2GiB/8GiB profiles;
  no float rounding or GiB/MiB confusion. Report original observed totals and
  the derived policy requirement, not an invented emulator requirement.
- Invalid/unavailable API, zero page size, total above limit, boolean/noninteger
  counters and arithmetic overflow remain fail-closed.
- A post-start sample whose total increased by one guest should remain an
  observation, not silently demand another startup allocation.
- Preserve the original failed logs and cause-unknown classification; no
  map-backing failure is relabeled solely from later commit statistics.

Validation here: installed package/version metadata reads and official pinned
source/docs inspection only; `git diff --check`. No executable, Windows API,
benchmark, device or model ran. No tests were added/run within this sole-doc
ownership. Coordinator owns implementation, regression checks and actual
authorized launch; task/phone gates remain unchecked.

## Coordinator resolution: explicit single-guest budget

The implementation uses `guest_plus_reserve_v2`: one guest-sized allocation plus
its existing explicit 2 GiB project reserve. Required headroom is therefore
4 GiB for the 2 GiB profile and 10 GiB for the 8 GiB profile. The source review's
20% heuristic would give 9.6 GiB for the latter; the chosen 10 GiB retains a
slightly larger, separately labeled project margin without charging a second
unsubstantiated guest allocation. Neither is the OS's hard minimum or a launch
guarantee. Assessment keys remain unchanged and separately record guest bytes,
reserve bytes and required bytes; the helper source hash identifies the policy.

Historical reports and failed attempts retain their old 6/18 GiB assessment.
Recorded headroom values between the revised 10 GiB budget and old 18 GiB cutoff
are accepted by the revised policy, while below-guest and below-budget controls
remain refused. No physical-RAM floor, guest profile, disk/CPU/ownership/source
check, deadline, system setting or other emulator is changed to obtain a pass.
Fresh parent and worker checks and actual startup observations remain required.
