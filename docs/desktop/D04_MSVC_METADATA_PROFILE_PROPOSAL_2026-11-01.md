# Proposed MSVC library metadata profile

Refs #25 D04.01/.02/.04, supporting #31 D09.03 and #21; claim6561571557.
Historical design basis. A separate source implementation and FIRST suite now
follow the [frozen contract](D04_MSVC_METADATA_PROFILE_CONTRACT_2026-11-01.md);
both remain unrun. This proposal grants no check, profile adoption or new run.
The completed member-facts packet is spent. Its retained JSON reports44/44
selfchecks and19 first-refusal rows; this document reads that record as text,
without re-execution or independent hash verification. Existing strict helper,
112-test bytes, frozen strict source/proofs and failed compatibility verdict
remain unchanged. The new source does not rewrite those historical verdicts.

## Evidence and preferred decision

The four count crossings are8542+63081=71623 and965+64611=65576, each repeated
for first/b; neither is a final archive total. Ten sections have zero relocation
count and nonzero pointer226/224/223 within members498/490/485 bytes. Three
directive sections contain only3/49/3 printable ASCII bytes plus exactly one
final NUL, with no BOM. Two normal COFF members have machine0 and one section.
These facts explain strict guards, not safe linking or absence of later failures.

Prefer an explicitly named **`msvc-library-metadata-v1`** interpretation over
silently changing strict mode. A separate frozen descriptor records version1,
purpose`build_input_metadata_only` and all caps below; its ID/version binds the
documented interpretation rules.
The existing one-argument/default call remains strict, including65536 aggregate
sections. Selection is a closed identifier, never an arbitrary limits object,
environment escape or executable/profile hash supplied as authority. Unknown
identifiers fail closed. Records bind the actual descriptor/source identity.
This profile has no inference-role, model, memory, provider or Author capability.

## Explicit proposed resource policy

| Bound | Proposed metadata profile |
| --- | --- |
| Whole input and individual member | Each strictly less than268435456 bytes, unchanged |
| Sections per member |65536; retain the old implied member bound explicitly |
| Sections per whole input |262144 across ALL members; at most10MiB section-header bytes |
| Sections per fixed32-input job |2097152, at most80MiB header bytes; charge every strict/profile attempt |
| Archive members, longname entries, section/total tokens |65536 each per input, unchanged |
| Aggregate directive bytes |1048576 per input, including BOM/NUL, unchanged |
| Metadata name / DEFAULTLIB name |4096 /255 bytes, unchanged |
| Entry bytes / actual file-read bytes per job |536870912 /1073741824; fixed32 entries, including identical first/b copies |

These are proposed logical work ceilings, not measured memory or OS limits.
The section change is deliberate, versioned and independently tested; it is
not a sufficient-size prediction from the first failures. No reset per member,
counter refund, pruning or automatic increase if more input remains. One held
buffer can feed strict/profile checks; two complete held-handle hashing scans
remain charged as actual I/O. No DEFAULTLIB search or expanded cohort here.
The [source-only API contract](D04_MSVC_METADATA_PROFILE_CONTRACT_2026-11-01.md)
freezes the descriptor, job meter and exact independent test interface.
Other raw ranges, overlap, symbol/string tables, longname offsets, archive
padding, unsupported formats, quote rules and path safety remain strict.

## Narrow interpretation rules and primary precedent

Microsoft's [section fields](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#section-table-section-headers)
require zero pointer when relocations are absent. The proposed profile records
a deliberate compatibility deviation, not conformance: only a non-directive
section with count0, no relocation-overflow flag and a pointer between its
header-table end and member end may have an unused nonzero pointer. Never read
or create a relocation interval from it. Count>0 still requires the complete
bounded relocation table; directive/line-pointer rules stay unchanged. LLVM
21.1.0's [getFirstReloc, lines327–363](https://github.com/llvm/llvm-project/blob/llvmorg-21.1.0/llvm/lib/Object/COFFObjectFile.cpp#L327-L363)
returns no relocation iterator when the count is zero. This is implementation
precedent, not proof that being in-member alone makes a field valid.

Allow machine0 only in the supported normal COFF layout, processing every
section and directive. Report unknown-machine counts; never relabel as AMD64.
Other machine/layout restrictions remain. LLD's pinned
[compatibleMachineType, lines170–183](https://github.com/llvm/llvm-project/blob/llvmorg-21.1.0/lld/COFF/Driver.cpp#L170-L183)
accepts UNKNOWN, but that is no execution, ABI or selected-member proof.

Permit at most ONE final NUL; require a nonempty lexical prefix after any BOM.
The whole preceding view must satisfy the existing ASCII/BOM and closed
quote rules. Count all original bytes, never mutate them. Reject interior or
multiple NULs, NUL inside an unclosed quote, any following byte, other controls
or high bytes. A nonempty whitespace prefix can contain zero options; bareNUL
or BOM-only+NUL is not a nonempty lexical prefix. Do not use C-string truncation
or general trim. LLD retains
[the full section, lines362–366](https://github.com/llvm/llvm-project/blob/llvmorg-21.1.0/lld/COFF/InputFiles.cpp#L362-L366), then
[passes it to the tokenizer, lines761–790](https://github.com/llvm/llvm-project/blob/llvmorg-21.1.0/lld/COFF/DriverUtils.cpp#L761-L790).
Its [Windows tokenizer, lines745–975](https://github.com/llvm/llvm-project/blob/llvmorg-21.1.0/llvm/lib/Support/CommandLine.cpp#L745-L975)
treats NUL as a delimiter outside quotes; quoted handling differs. Our proposal
is narrower. Microsoft documents ANSI/BOM UTF-8, not a general NUL-padding rule.

## Alternatives and acceptance before any build

A separately qualified toolchain-produced inventory is an alternative evidence
basis, not a claim the strict scanner passed. It needs pinned producer/tool
bytes, bounded complete capture, a closed output parser, exact input identities
and explicit treatment of implicit DEFAULTLIB inputs. A selected-member link
trace alone cannot establish all-member metadata or an unselected-input closure.
It introduces new tool execution and qualification; none is approved here.
Freeze independent NEW FIRST cases without editing the old112: default refusal
parity; explicit/unknown profile selection; member/input/job boundary crossings
and no resets; zero/nonzero relocation pointers with flags/ranges/overlap;
machine0 versus other layouts/machines; exact terminal NUL, quoted/interior/
double/hidden-tail adversaries; raw-byte budget at NUL/BOM boundaries; all
DEFAULTLIB/unknown-option/path controls and unchanged success/error contracts.
After source review and fresh applicable admission, run old/new tests and the
fixed32 real-input metadata checks, recording every exception and later refusal.
Do not require all32 to pass by weakening policy. Success remains metadata-only:
closureComplete/linkQualification false, no actual selected-link or PE validation.
Root must forecast concrete source/output/storage/capture before any new child;
all old caps, failures and spent grants stay. B2 artifact/profile/pin adoption,
worker/model/app/device qualification and production Author remain separate;
Author stays Disabled and full D04/D09/epic acceptance remains open.
