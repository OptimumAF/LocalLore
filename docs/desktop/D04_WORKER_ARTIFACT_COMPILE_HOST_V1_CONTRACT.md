# D04 one-use Windows compiler host v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This private bridge connects the candidate A observation to the Windows
Job launcher. It does not install a binary or create an application
command. An independently admitted outer owner must build and pin the
helper, own its process and pipes, and implement the evidence ports.
The helper is a Windows x64 development source behind the existing
`LOCALLORE_COMPILE_JOB_V1_TEST_OWNER` build definition.

## Standalone helper build

The `native/llama-worker/compile-host` project builds only
`locallore-compile-host-v1.exe`. It uses a Windows MSVC x64 Release
configuration with Ninja and has no worker, llama.cpp, app or install
target. The build selects the static MSVC release runtime and the
translation unit refuses a dynamic or debug runtime. This reduces the
helper's dependency on side-by-side runtime files. Actual imported
Windows DLLs, activation-context redirection, transitive imports and
any runtime loads still need their own evidence.
[CMake static runtime property](https://cmake.org/cmake/help/v3.22/prop_tgt/MSVC_RUNTIME_LIBRARY.html)

Only after a separate build admission, run from the exact reviewed
physical D: checkout using the admitted MSVC x64 environment. The
admission supplies the exact CMake executable and a fresh dedicated D:
build root outside the worker sources and normal build. It must bind
Ninja, the compiler, linker, SDK and resource/manifest tools, and
reserve the complete configure, compiler-probe and build outputs.
The CMake path checks do not establish physical storage or grant
authority. Use the approved versions and process-local environment.

```powershell
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP
$source = Join-Path (Get-Location).Path 'native/llama-worker/compile-host'
& $approvedCMake -S $source -B $approvedHelperBuildRoot -G Ninja '-DCMAKE_BUILD_TYPE=Release'
if ($LASTEXITCODE -ne 0) { throw 'Compile helper configuration failed' }
& $approvedCMake --build $approvedHelperBuildRoot --target locallore-compile-host-v1 --parallel 1 --verbose
if ($LASTEXITCODE -ne 0) { throw 'Compile helper build failed' }
```

Verify the actual compiler and link arguments, the x64 PE and its exact
bytes and hash before considering it for the helper pin. Inspect normal
and delay imports with the admitted PE inspection tool. Retain the exact
scope and report before any separate loader run. A PE import listing
alone cannot prove which files the Windows loader actually resolves.
The held helper path and loader admission remain required. There has
been no configuration, build, import inspection or execution of this
target in this source slice.
[Microsoft PE import listing](https://learn.microsoft.com/en-us/cpp/build/reference/imports-dumpbin?view=msvc-170)

## Frames

The helper accepts no arguments. Its standard input and output are
private pipes. All integers are little endian. The request starts with
eight ASCII bytes `LLCLV1\r\n` and a u32 body length capped at 65,536. The
body starts with the nonzero 32-byte binding, followed by 39 strings.
Each string has a u16 UTF-8 byte length and strict UTF-8 bytes. Strings
are compiler, worker directory, upstream directory, candidate A
output directory, Windows directory, PATH, INCLUDE, private temp, and
the 31 exact compile arguments. Reject trailing bytes within the body.
The binding is SHA-256 of compact context JSON followed by the exact
length-prefixed strings. The adapter retains and checks the hash of the
entire request independently. The helper echoes the binding and does not
authenticate a caller. The dedicated outer owner controls the private pipe.

The helper reads the request in at most 5,000 ms, polling pipe availability
on its single thread. Once the frame is complete, an extra byte, disconnect
or pipe error requests cancellation. Keep the input pipe open and quiet
during ordinary execution. Cancel an incomplete frame by closing input,
without inserting bytes into the unfinished request. The native Job launcher polls the same stop
condition through setup, execution and cleanup. The outer owner must
drain output, positively observe helper exit and closure of its three parent pipe handles,
and retain partial evidence if the helper is interrupted. The whole
outer attempt has its own bounded allowance before it may be admitted.
The helper relies on the owner to drain its synchronous reply writes.
A reader that stops consuming is a transport failure.

The reply is `LLCLR1\r\n`, the echoed 32-byte binding, u32 stop, PID,
native error, exit bits, active Job count and flags, u64 elapsed ms,
u32 stdout length and stderr length, then exactly those two raw byte
prefixes. The header is 80 bytes. Maximum reply is 69,712 bytes.
Stop values in order are none, request, cancelled, deadline, setup,
I/O, overflow and drain. Flags in bit order are exit known, Job count
known, membership, resumed, direct signaled, kill attempted, kill
failed, I/O error, process handle closed, all handles closed, stdout
overflow, stderr overflow, stdout EOF and stderr EOF. Unknown numeric
facts are encoded as zero with their known flag clear. A helper error
without a frame is a transport failure. The helper emits no diagnostics
to stderr. A framed native refusal still returns its measured facts.

## Port

`createWorkerArtifactCompileHostV1({config,authority,environment,hostHash,ports})`
returns the single `launch` method for #408. Config and authority are
the same accepted recipe and authority used by #408. Environment is
exactly `{windows,path,include,temp}`. Host hash pins the admitted
helper image. One valid offer consumes the method before any I/O.
An extra call or changed context, candidate, command, policy or
signal shape refuses. Valid context includes the spent grant digest.

Trusted private ports are `authorize, transport, retain, excludeWriters`.
Structured proof replies are canonical compact JSON, bounded to 4,096 bytes.
The adapter binds every proof to the current request and context. A
successful call shape cannot establish that a port actually performed I/O.
The enclosing owner must establish the behavior of each port.

- Authorize receives the frozen scope `{context,requestHash,hostHash}`.
  Return exactly `{kind:'compile_host_authorized_v1',scope,spend,start,writerPolicy}`.
  Spend binds the already durably spent grant and the atomically consumed
  launch offer for this one call. The adapter does not spend a new grant. Start binds #408's durably acknowledged START and writerPolicy
  binds the fresh external-writer exclusion policy and preflight.
- Transport receives `{scope,authorization,request,signal}`, where
  authorization is the hash of the exact accepted authorize wire bytes. Use only
  the already pinned helper. Preserve one attempt, bounded output,
  and observed process/pipe closure. Verify the hash of the actual bytes
  offered to stdin immediately against the authorized request hash.
  Retain the actual sent length and hash or partial-send state with the
  owner observation. Use null for unknown send facts. Return exact own data
  `{image,observation,pid,closed,stdinClosed,stdoutClosed,stderrClosed,exitCode,sentBytes,sentHash,response,stderr}`.
  Image and observation bind the actual launch and retained owner
  observations, response and stderr are raw buffers, each bounded
  before return. The transport owner preserves partials even if it
  returns malformed data or throws. A successful frame requires pinned image, positive helper
  and three pipe closures, an actual helper PID distinct from the compiler,
  exit zero, empty stderr and an exact completed send.
- Retain receives `{record,request,response,stderr}`. The record
  binds hashes, lengths, helper facts, authorization and scope.
  Exclusively retain and read back the exact bytes of all three
  buffers and the record, even on transport refusal. Return exactly
  `{kind:'compile_host_retained_v1',recordHash,stored:true}` only
  after successful retention. The adapter neither overwrites nor
  creates any path of its own.
- ExcludeWriters receives `{scope,authorization,writerPolicy,recordHash}`.
  Return exactly `{kind:'compile_host_writers_excluded_v1',scope,
  authorization,writerPolicy,recordHash,postflight}` only on a
  fresh independently retained exclusion of outside writers for the
  admitted policy and actual capture. A lookup of live processes after
  CL exits does not prove exclusion across the launch. The proof must
  cover the pinned tool/DLL and no-debug environment, admitted
  directories and any applicable external-service risk.

An intact frame can supply a direct process receipt even when writer
closure is unknown. Positive writer closure requires successful
transport/retention, native direct signal and exit, Job zero with
membership, both EOFs, known handle closes, clean I/O, and the
external-writer proof. Deadline and drain stops remain timed out.
Other native refusals remain refusals, including a cancellation that
arrives independently of the observation's AbortSignal. A valid
nonzero exit remains a real process result. Never clamp elapsed time,
substitute EOF for an empty pipe, or fabricate a PID for a pre-launch
refusal. A malformed, late, incomplete or unretained result cannot
unlock object inspection. #408 conservatively quarantines when no
valid process receipt can be made.

No code, helper, compiler or fixture was executed in this source
slice. Native framing/EOF/cancellation, exact build provenance,
helper supervision, real retention and external-writer exclusion
must be independently verified before a compiler attempt.
