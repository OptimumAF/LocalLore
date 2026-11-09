# D04 Windows candidate A compiler Job owner v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This private development source is the native launch side of the candidate A
compile observation. It has no CLI, app command, network endpoint or build
target. A future admitted owner must link it, validate the JavaScript offer
and persist the actual evidence. The header requires the explicit
`LOCALLORE_COMPILE_JOB_V1_TEST_OWNER` definition on Windows x64.

## Request

Construct `locallore::compile_job_v1::Request` in the private host from the
already accepted candidate A recipe. Pass its exact candidate A argument
vector, compiler, worker directory, upstream directory, output directory,
approved Windows directory, ordered PATH and INCLUDE, and private temp
directory. Use forward slashes and uppercase drive letters. The header
reconstructs the v1 compile arguments independently and refuses a mismatch
before touching the OS. It has one fixed tool leaf, working directory,
source leaf, candidate and stage. There is no shell, response file,
environment override switch, configurable timer, retry or alternate tool.

The child receives a new sorted Unicode environment containing INCLUDE,
PATH, SYSTEMROOT, TEMP, TMP and WINDIR only. The latter two Windows
directory variables agree, and TEMP and TMP name the same private D:
directory. There is no inherited CL or _CL_ option injection. A future
owner must prove that this exact environment, tool/DLL cohort, include
search, source, headers and private output/temp identities are valid and
unchanged, and that external compiler writers are excluded. This header
checks lexical values. It does not hold those paths or files open or
validate their contents. No public input may supply a request.

The compile recipe contains /Fd and /FS but no /Zi, /ZI or /MP. Microsoft's
[/FS documentation](https://learn.microsoft.com/en-us/cpp/build/reference/fs-force-synchronous-pdb-writes)
describes routing debug PDB writes through MSPDBSRV. A successful Job check
can never establish closure for an existing external service. Require an
independent fresh exclusion of outside compiler writers before granting
writer authority, and refuse any evidence of an external writer. Do not
kill an unrelated service or inspect another build's artifacts.

## Process and capture

Use one unnamed kill-on-close Job with no breakaway flags.
[JOB_LIST and HANDLE_LIST](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute)
are both passed at process creation, with only the three standard handles
inherited. A suspended creation must report actual Job membership before
the primary thread can run. There is no assign-after-create fallback.
The closed stdin writer gives immediate EOF. The read ends of the two
local, first-instance byte pipes are noninheritable and use PIPE_NOWAIT.
The connector checks that the actual client belongs to the current owner
process before passing its write handle to the child. No secondary reader
or detached thread is needed.

Capture raw bytes into fixed 65,536-byte stdout and 4,096-byte stderr
buffers, plus at most one probe byte per stream to detect overflow.
Observe cancellation and the 120,000 ms execution deadline even when
output is busy. After termination, allow one shared 5,000 ms observation
window for the direct process, Job and pipes. Never reset a deadline for
progress, a second stream or a later failure. On cancellation, timeout,
overflow or I/O failure, request termination of the owned Job. A failed
membership check also permits terminating only the still-suspended
direct process. An unexpectedly live Job at the end of drain is
terminated and reported as unsettled. An unproven descendant, exit,
pipe EOF or handle close keeps the receipt in quarantine. If overflow
prevents observing EOF, closing the local read handle still cannot
substitute for EOF proof. The native timings are measurements. The
outer deadline must account for OS calls and scheduler delay.

## Receipt binding

`launch(request, cancelled)` returns `Result` with the observed PID,
exit, Job count, EOFs, close facts, bounded captures, stop and elapsed
time. The cancel flag is a trusted atomic boolean. Call exactly once
after the spent grant and the before-check. On refusal before a real
PID, retain the native result separately without inventing a process
record. Measure and retain the captured byte counts and hashes from
the actual returned prefixes. Convert the DWORD exit bit pattern to
the existing signed process receipt, without treating numeric 259
as live when the handle is known signaled.

`closed()` requires the direct process signal, exit and explicit handle
close. `job_and_pipes_closed()` requires positive actual membership,
observed Job zero, both pipe EOFs, and all owned handle closes. It is a
necessary native fact for the separate writer receipt, along with
`closed()`, clean I/O and independent exclusion of external writers.
Keep the existing direct process receipt's `processTreeContained:false`.
Timeout, cancellation, overflow and any kill attempt remain refusal
evidence even after known closure. The bridge must retain actual
observations on failures and must never clamp a receipt into a deadline
or infer positive closure from closing the kill-on-close Job.

Source review and Git checks do not exercise Win32. Future separately
admitted tests need actual creation-time membership, inheritable-handle
isolation, binary stream fidelity, zero and nonzero exit, cancellation,
timeout, overflow, pipe EOF, active descendants, close refusal, and a
trusted native runner. A separate fresh admission is required for actual
candidate A CL. LINK, MT, artifact adoption, worker/model launches and
desktop qualification remain outside this slice.
