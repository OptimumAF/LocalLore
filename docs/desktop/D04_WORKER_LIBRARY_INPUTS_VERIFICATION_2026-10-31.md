# Build-time library inspector: synthetic verification

Refs #25 D04.01/.02/.04 and #31 D09.03 supporting work. This is a small
build-time metadata tool supporting the [B2 artifact plan](D04_AUTHOR_WORKER_ARTIFACT_PLAN_2026-10-31.md).
**85 synthetic Node cases pass. Actual library compatibility, a resolved
SDK/CRT input set and a candidate worker remain unverified.**

Producer source `79b4e8bad4fc17459ae5b9c710317d6547c2a2f5` is integrated and
actually tested at `f51f8563eab63a772987ccb197ea4f10f4fa51c0`, based on accepted
PR308/main760a5d4b. Only two new build-tool files implement this slice:
`native/llama-worker/library_inputs.mjs` and `library_inputs_test.mjs`.
Their combined physical UTF-8 source is19145B. No application/runtime/engine,
dependency, lock, packaged pin, Android or Eval interface changes.

## Interface and supported subset

`inspectLibraryInputs(Buffer)` returns object/import counts, deduplicated parsed
directive tokens and normalized default-library names. It has no filesystem,
environment, process or network access; extracted directives are never executed.
It conservatively inspects ALL ordinary archive members, not the members a
future linker actually selects. Returned unknown options are data; a future
caller must apply its closed policy and bind resolved library bytes.

The supported subset is ordinary AMD64 COFF, SDK-defined BIGOBJ and short-import
headers, plus Microsoft archive framing. It checks header/table/raw/relocation/
line/symbol/string ranges and nonempty overlap, the BIGOBJ identity, import
flags and EXPORTAS strings, section-name aliases, archive longname entry starts
and even newline padding. Known archive symbol-index payloads are envelope
checked only; they are not interpreted as symbol-selection authority.

Directive parsing is deliberately ASCII-only, with an optional UTF-8 BOM;
controls and unsupported encodings refuse. Quoting/backslash handling preserves
parsed tokens. LIBPATH/NODEFAULTLIB and path-bearing DEFAULTLIB names refuse.
Unknown ordinary members/layouts refuse instead of disappearing from the input
inventory. PE images, GNU archives, anonymous CLR/LTCG objects and relocation
overflow encodings are outside this supported subset.

The file/member ceiling is strictly below256MiB; aggregate sections, members,
longnames and tokens are bounded at65536; directive bytes at1MiB and metadata
names at4096 bytes. The tests use small in-memory adversarial fixtures, at most
about2.7MiB, and do **not** allocate a256MiB or65536-member boundary fixture.
This is neither a complete PE/COFF conformance validator nor a linker simulator.
Layouts were checked against installed SDK10.0.19041.0 `winnt.h` and Microsoft's
[PE/COFF specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).

## Actual Node-only check

Producer-authored tests cover S01–S18, R01–R30, D01–D16, A01–A13 and B01–B08.
Independent source review inspected the binary bounds, aliases, quote rules,
import distinctions and synthetic assertions before Root execution. This is
not an independent FIRST/RED experiment or engine/model evidence.

The actual child command was the existing pinned Node24.22.1 executable plus
`native/llama-worker/library_inputs_test.mjs`, from the physical D: checkout.
Its fixed summary is85 executed/85 passed/0 failed; exit0,0.142s recorded
spawn-to-close time, complete109-byte stdout and empty stderr. There was no
timeout, overflow, kill or unknown closure. This measures code checks, not
inference or native application performance.

A separately admitted developer can reproduce the synthetic check from the
repository root with the already provisioned Node24.22.1:

```powershell
$env:TEMP='D:/Dev/_Temp'
$env:TMP='D:/Dev/_Temp'
node native/llama-worker/library_inputs_test.mjs
```

Root used a closed local coordinator with1024/2048B stdout/stderr caps,30s child
deadline, one kill/5s drain, complete26624B output reserve, exact source/tool
pins and exclusive records. Node preload, path, debug, coverage, compile-cache
and warning-file redirects were refused before parent startup. Global stops,
prior evidence, normal native bytes, target and fixture growth were checked.
Critical failures latch the global refusal; an incomplete START without a valid
settled result is fatal for future coordinators of the same evidence packet.

The first coordinator refused before Stage read/START/test spawn because Root
compared a Windows-normalized cwd with an unnormalized forward-slash literal.
Original source10375B, Stage548B and the563B refusal record remain immutable.
No case ran in that attempt. Corrected V2 normalizes both operands and binds
the original refusal/source/Stage and absent V1 execution markers. Independent
review also caught and restored a historical-root spelling change in the
unexecuted V2 draft before its Stage was created; no second namespace was made.
The corrected runner is10998B and its actual Stage700B. The85 test assertions
were unchanged. Their original UNRUN comment records frozen authorship stage.

Root read the complete actual logs and checked the process/result and source
hashes. The accepted normal desktop binary remained unchanged/unlaunched;
target12356228504B and runtime fixtures210B did not grow. All old output remains.
Before the final346-byte result, metadata1406470B/group53607535B/joint735929029B
were within the unchanged1441792B/64MiB/724MiB limits. After that result,
metadata1406816B; later Root review metadata is separately charged.

| Local proof/input | SHA256 |
| --- | --- |
| Inspector module | `b7e2310c2fa4b56b6987c98bc6504d9781fd6f9900d32fd9307e1277ad48196e` |
| Synthetic test | `93f6a09a021c6a5361803b9ce2537d6ada4ffd3aaf14e363a072af6e2b123f68` |
| V1 pre-admission refusal | `cef3301df40c3d6671bf6dda55e674d30caf51d960995bd89376286c61db7398` |
| Corrected runner | `e0cdfcc97af01ffa91ab3ef8452f821f12b1e6ec81dc71c9b3482c9c7aa78540` |
| Actual V2 Stage | `0124586863f03e916058dc5c682be160acce2ebea6dfa235bd93f506a82497e3` |
| Actual child record | `8eaebeee68840a3bdf45e9eb27c3248ccdae903bb0b03adaaec8c570998e4a76` |
| Passing settled result | `931ed361afc514296f6c19989a6422662734216bfc909fa10733dcc07c898e6d` |
| Root raw-log/source review | `dc80f9e634a164285ac92a1c11c18d495b9b2773ec3b40fee175ce5715cd9603` |

## Remaining work

The filesystem/search-root collector must bind actual SDK/CRT/default-library
paths and bytes, account for cwd lookup before LIB, and refuse unexpected
resolution. Inspecting all members gives a conservative superset, never exact
selected-member evidence. After a valid input record and reviewed artifact
coordinator, a freshly admitted compile/link/MT packet can establish candidate
identity. None has run here. Full build, model/worker/application execution,
native rendering, Android/device, quality and production Author adoption remain
separate. The original target ceiling and all other storage limits are unchanged.
