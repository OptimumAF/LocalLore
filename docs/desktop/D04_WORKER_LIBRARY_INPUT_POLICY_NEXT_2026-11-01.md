# Worker library inputs: next facts and policy decision

Refs #25 D04.01/.02/.04, supporting #31 D09.03 and #21.
**Source-only proposal; no new inspection, selfcheck or run authority exists.**
The [actual diagnostic record](D04_WORKER_LIBRARY_DIAGNOSTIC_VERIFICATION_2026-11-01.md)
retains all three spent children and the unqualified result. This plan does not
change `library_inputs.mjs`, its original 85 predicates, or its 112-case result.

## Facts established and still missing

| First refusal | Rows | Established | Missing numeric facts |
| --- | --- | --- | --- |
| `coff_sections_total` | 4 | First/b aggregate counts 71623 or 65576 exceeded 65536 | Refused member's declared section count and header layout; final archive totals remain unknown |
| `coff_relocation_pointer` | 10 | Zero count with nonzero pointer reached this guard | Exact pointer/count/flags and whether the pointer is within that member |
| `directive_encoding` | 3 | Strict encoding subset refused | Byte classes, first rejected byte value/offset, BOM and trailing-NUL facts |
| `coff_machine` | 2 | Existing AMD64 guard refused | Actual machine values and bounded header classification |

These are first refusals, not a survey of every later incompatibility. They do
not prove corrupt SDK files, safe padding, architecture-neutral members or a
complete/default-library/selected-link closure.

## Proposed single data-only packet

Freeze exactly the 19 refused slots from the retained, hash-bound 32-input
snapshot: same aliases, input paths/bytes/digests and saved member/section
locations. No replacement cohort, recursive DEFAULTLIB lookup or additional
member selection. New public rows use slot numbers, never paths or names.
Use one future fixed Node metadata child under a fixed Node parent and bounded
PowerShell supervisor, with synthetic selfchecks before any real-input opens.
An unsuccessful selfcheck permits no real-input reads. The
[concrete reviewed admission proposal](D04_WORKER_MEMBER_FACTS_ADMISSION_2026-11-01.md)
owns exact sources, process counts, budgets, output and the new decision.

Reuse the existing authority/source/old-proof/STOP/START/physical-path checks,
held read-only handles, identity checks and two complete bounded hashing scans.
First run the unchanged hash-pinned Buffer helper on the held bytes and require
the original refusal/site/context to match. That existing helper scans archive
framing and prefix objects/sections under its unchanged limits; it is separate
from the new numeric extraction and is not a second aggregate validator.
Then extract new header facts only at the saved first-refusal locations;
validate archive/body and integer ranges before every read. New header
extraction is at most 60+56+40 bytes per slot. Do not traverse later members or
sections, truncate/patch input, or reset counters to evade the existing bound.
For the three encoding rows only, count the saved directive section's bytes
in bounded chunks, at most the unchanged 1MiB bound per section. Do not decode
or emit its text, tokenize directives, repair input, or load/execute a library.

Rows record common slot/site, zero-based member index/header offset, member
bytes, candidate layout, machine and declared section count. Section-count
rows add saved aggregate and explicitly derived prior count; subtraction must
be safe/nonnegative and is not an independently scanned prefix count.
Relocation rows add section index, raw offset/bytes, relocation and line
pointers/counts, flags and a zero-width pointer-in-member boolean. That boolean
does not validate relocations or make a nonzero unused pointer acceptable.
Encoding rows add section index/raw range, BOM presence, disjoint counts of
printable ASCII/NUL/tab/CR/LF/other control/DEL/high bytes, first rejected value
and offset, and trailing-NUL count. Counts cover raw section bytes; the first
rejection follows the helper's optional-BOM rule. No excerpts, symbol/member
names, byte arrays, code-page guess or UTF-8-validity claim enters the report.
Member header offsets are archive-absolute; raw/relocation/line pointers are
member-relative. First-rejection offsets are raw-section-relative and include
initial BOM bytes in that coordinate, with search starting at3 when present.

Frozen coordinator/selfcheck source is41815B in memory; the separate reviewed
21896B supervisor is retained under the existing cap, unexecuted. Earlier
32/35KiB source estimates were exceeded as guards and parent startup capture
were preserved. No owner cap was increased; the complete packet needs a new
decision under the linked measured admission plan.
Provisional output: exactly 19 category-specific rows, at most 768 UTF-8 bytes
each, total snapshot at most 16KiB. A closed row can use at most 23 keys of at
most 16 ASCII characters, non-null uint32/boolean values, one fixed site of at most
24 characters and one layout enum of at most 12. The conservative compact row
bound is 712 bytes; 19*768+1024 envelope bytes+LF = 15617 < 16384. This is static
schema reasoning, not measured source/output. Excess fails without truncation.
Root owns the actual full-cap forecast, stream/deadline/terminal reserves and
exclusive receipts after concrete source exists; no cap increase is granted.

## Standards and decision alternatives

Microsoft's [PE/COFF section fields](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#section-table-section-headers)
specify a zero relocation pointer when there are no relocations. Keep that
refusal; local linker tolerance is not a standards-backed exception. Numeric
facts may justify seeking producer documentation or a different qualified
dependency set, not silently accepting/clearing a mismatched field.
The [directive format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#the-drectve-section-object-only)
distinguishes ANSI from BOM-marked UTF-8. A control or high byte is not yet
proof of padding, text validity or harmlessness. Any later supported encoding
needs exact rules and adversarial tests, preserving malformed-input refusal.
The [machine table](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#machine-types)
defines UNKNOWN as 0 and AMD64 as 0x8664; no observed value is assumed here.
Even a zero value would not prove the member contains no consequential input.

Retain the original 65536 aggregate ceiling. Options remain: keep these inputs
unsupported; choose separately qualified inputs; or later contract a distinct,
explicitly resourced metadata policy with independent FIRST. Never reset the
counter per member, omit members, infer final totals from a first refusal, or
label the present strict scanner compatible by raising its constant.

Required synthetic groups cover truncated/misbound headers and ranges; both
COFF layouts/import discrimination; saved-location/roster/hash mismatch;
zero-count pointer contradictions including out-of-range values; aggregate
count crossing without continuation; BOM/control/high-byte/NUL classifications;
safe arithmetic/null rejection; exact encoded row/snapshot caps and sticky failure.
All are prospective and unrun. A fresh owner decision and full admission are
required for the one real-input child; all prior grants remain spent. Every
result keeps qualified/closureComplete/linkQualification false. No policy fix,
compiler/link/MT, worker/model/app/device execution or B2 adoption follows.
