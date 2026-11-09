# D04 one-use Windows compiler host v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This private bridge connects the candidate A observation to the Windows
Job launcher. It does not install a binary or create an application
command. An independently admitted outer owner must build and pin the
helper, own its process and pipes, and implement the evidence ports.
The helper is a Windows x64 development source behind the existing
`LOCALLORE_COMPILE_JOB_V1_TEST_OWNER` build definition.

## Frames

The helper accepts no arguments. Its standard input and output are
private pipes. All integers are little endian. The request starts with
eight ASCII bytes `LLCLV1\r\n` and a u32 body length of 32–65,536. The
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
during ordinary execution. The native Job launcher polls the same stop
condition through setup, execution and cleanup. The outer owner must
drain output, positively observe helper exit and both pipe closures,
and retain partial evidence if the helper is interrupted. The whole
outer attempt has its own bounded allowance before it may be admitted.

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
  Spend binds the durable, atomically consumed authorization for this
  one call. Start binds #408's durably acknowledged START and writerPolicy
  binds the fresh external-writer exclusion policy and preflight.
- Transport receives `{scope,authorization,request,signal}`, where
  authorization is the hash of the accepted authorize record. Use only
  the already pinned helper. Preserve one attempt, bounded output,
  and observed process/pipe closure. Return exact own data
  `{image,observation,closed,stdoutClosed,stderrClosed,exitCode,response,stderr}`.
  Image and observation bind the actual launch and retained owner
  observations, response and stderr are raw buffers, each bounded
  before return. Preserve transport partials even when this call
  throws. A successful frame requires pinned image, positive helper
  and pipe closure, exit zero and empty stderr.
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
