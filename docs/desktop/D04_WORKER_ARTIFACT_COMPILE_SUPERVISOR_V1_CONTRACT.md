# D04 private Windows compiler supervisor v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This supervisor supplies the journal for the candidate A observation and the
authorize, transport and retain ports for its native host bridge. It has no
CLI, application command, new build target or automatic retry. Source is
ready for review. Windows behavior remains unverified.

## Admitted parent

Construct `createWorkerArtifactCompileSupervisorV1` with an exact private
profile `{context,hostHash,hostDirectory,evidenceRoot,windows,temp,admission}`.
Context matches the candidate A observation, including its grant and recipe
hashes. The four paths are canonical absolute paths. Project paths are on
physical D:. The executable leaf is fixed to
`locallore-compile-host-v1.exe` under hostDirectory. Admission has five
nonzero digests for actual already-retained observations.

- `job` binds the dedicated pinned Node process already running in a
  native parent-owned, non-breakaway Job. The external owner retains the
  Job through shutdown and positively observes an empty group or records
  unknown closure. There are no other inheritable handles in the process
  beyond the scoped helper transport.
- `spend` binds the durably spent grant for this attempt.
- `writerPolicy` binds independent outside-writer policy and its actual
  fresh preflight. The separate bridge excludeWriters port still needs
  its own fresh independent postflight.
- `namespace` binds already-admitted physical D: roots, parent and
  evidence directory identities, a private exclusive namespace, full
  byte reserves and no reparse or competing writers. The directory
  must already exist. The supervisor never creates a directory.
- `hostLease` binds the external held protection against replacement
  or modification of the selected helper during process creation,
  including its admitted dependency search. Node's named and held
  reads check local identity and drift. They do not enforce Windows
  sharing denial against concurrent replacement.

The exact proof digests are carried in transport evidence. Constructing
the factory does not establish or verify any external proof by itself.
The admission owner enforces the pinned Windows x64 Node binary and
environment and must verify the actual evidence, including relevant
ancestor Jobs, before invoking this source. Do not rely on libuv's
optional Job for descendant coverage. It allows breakaway and can
continue after assignment failure. [Pinned libuv Windows launcher](https://github.com/nodejs/node/blob/v24.22.1/deps/uv/src/win/process.c#L1016)

## Single-use launch and observed closure

Persist a verified START from #408, then one create-only OFFER bound to
that exact START, scope and spent grant. Retain the exact authorized
request before the helper offer. A failure is terminal for the offered
slot. No alternate path or executable is tried.

The supervisor calls the fixed helper directly with zero arguments, no
shell, three private pipes and no window or detachment. Cwd is the
admitted helper directory. The fixed environment covers the Windows
values normally copied by libuv and sets the Node coverage/options
values explicitly. The compiler still receives its own separate
environment from the native launcher. Preflight and postflight each
read at most one complete 8 MiB helper image through a checked file
handle, with an EOF probe. The outer lease remains necessary.

Bound stdout at 69,712 bytes and stderr at 4,096 bytes, retaining prefixes
on overflow. Write the one exact hash-verified frame without closing
stdin. A completed send requires the stream write callback. Cancellation
closes stdin without sending an extra byte into a partial frame. The
native helper receives cooperative cancellation on EOF. If the helper
fails to settle by 132,000 ms, request one kill of that known helper
through its owned child handle. Use a single further 5,000 ms closure
allowance and keep any unknown process in the outer Job's custody.
Overflow and I/O refusal may stop earlier. Late events can preserve
closure observations without clearing refusal. The outer native owner
also applies its own bounded deadline to the whole attempt, including
filesystem calls.

Only actual spawn supplies a PID. Observe matching exit and child-close
events, separate stdin close, and separate stdout/stderr EOF and close.
Destroyed streams alone do not prove EOF. A new boolean `accepted` in
the bridge transport envelope records positive supervisor disposition.
Timeout, overflow, I/O and missing or mismatched closure keep it false
even when actual bytes and some closure facts are known. The bridge
retains the evidence before testing it. Normal exit alone does not
establish compiler writer closure. [Pinned Node child lifecycle](https://nodejs.org/download/release/v24.22.1/docs/api/child_process.html#event-close)

## Retention

Use only these eight create-only leaves in the existing admitted
directory. START, OFFER, transport and CAPTURE are individually capped
at 4,096 bytes. Terminal is capped at 16,384 bytes.

| File | Maximum bytes |
| --- | ---: |
| START.json | 4,096 |
| OFFER.json | 4,096 |
| request.bin | 65,548 |
| response.bin | 69,712 |
| stderr.bin | 4,096 |
| transport.json | 4,096 |
| CAPTURE.json | 4,096 |
| terminal.json | 16,384 |

Total logical content reserve is 172,124 bytes, before external source,
helper build, filesystem allocation and other owner records. This is
a design bound and does not authorize any new evidence cap or run.

A write uses exclusive creation, positional writes, flush, exact held
readback plus EOF, known close and named identity readback. Windows can
finalize write timestamps on close, so record the stable stamp and repeat
exact readback through a new read-only handle after close.
[Windows file timestamps](https://learn.microsoft.com/en-us/windows/win32/sysinfo/file-times)
START and OFFER are verified again before the helper launch. Capture
bytes are retained before the post-launch image check. CAPTURE
additionally reopens and verifies the exact retained request and output
bytes and transport record. Partial files stay in place. A retention
failure never produces a success acknowledgement. Terminal has a
separate fixed slot for failure evidence, including refusal before START.

Before admission, independently verify helper framing and native
binary provenance, send/EOF/close event ordering, cancellation during
send and execution, timeout after a late complete frame, stream
overflow, unknown shutdown, actual create-only/readback behavior and
outside-writer policy. Compiler, worker/model, application, Android
and desktop qualification remain separate.
