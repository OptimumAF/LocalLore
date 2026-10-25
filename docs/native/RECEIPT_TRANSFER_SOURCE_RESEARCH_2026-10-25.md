# Receipt transfer source research — 2026-10-25

Supporting M05.05 prerequisite / M01.05, root claim #9/6404322953;
independent claim #9/6404332614. Source-only research, not a benchmark or runtime
selection. Base: `ecc834369136b5e899a031b43362f94a9f652c9a`.

`dd bs=1048576` is supported by the inspected Android 15 and current Toybox
sources. It is a valid candidate beside plain `cat` with shell-owned redirection.
It does **not** promise full-megabyte writes or a faster transfer. Do not use
`dd of=...` for the create-only sink, or rely on help-listed flags that the parser
does not implement.

## Evidence boundary and source pins

The coordinator's recorded PR #178 attempt timed out after140906ms, with held-FD
host cursor2471362560 of2588147712 bytes after a full source SHA check. This is
host-side progress, not guest bytes, completed writes or an EOF acknowledgement.
No IMPORT/SDK operation was dispatched. That observation does not identify a
buffering, PTY, filesystem or utility mechanism.

Official Gitiles commit metadata and source were read over HTTPS into memory.
No installed executable was run/read/hashed, and no model, target, emulator disk,
SDK installation, cache or previous guest payload was inspected. No benchmark was
executed. No dependency or runtime was selected.

| Repository/ref inspected | Resolved commit | Primary source |
|---|---|---|
| AOSP ADB `refs/heads/main` | `1cf2f017d312f73b3dc53bda85ef2610e35a80e9` | [client](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/client/commandline.cpp), [service routing](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/daemon/services.cpp), [subprocess transport](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/daemon/shell_service.cpp) |
| AOSP ADB `android-platform-15.0.0_r10` | `f8a7480bc3500502d5f12c8fd6d1aecc394a604f` | [Android15 client](https://android.googlesource.com/platform/packages/modules/adb/+/f8a7480bc3500502d5f12c8fd6d1aecc394a604f/client/commandline.cpp) |
| AOSP Toybox `android-15.0.0_r1` | `e1a5a73c328e03e7e8de9090cf04cf8e86340113` | [dd](https://android.googlesource.com/platform/external/toybox/+/e1a5a73c328e03e7e8de9090cf04cf8e86340113/toys/posix/dd.c), [cat](https://android.googlesource.com/platform/external/toybox/+/e1a5a73c328e03e7e8de9090cf04cf8e86340113/toys/posix/cat.c) |
| AOSP Toybox `refs/heads/main` | `59a869a838cfadbf6bc41cb400471ca9d2cae9b5` | [dd](https://android.googlesource.com/platform/external/toybox/+/59a869a838cfadbf6bc41cb400471ca9d2cae9b5/toys/posix/dd.c), [cat](https://android.googlesource.com/platform/external/toybox/+/59a869a838cfadbf6bc41cb400471ca9d2cae9b5/toys/posix/cat.c) |
| AOSP mksh `android-15.0.0_r1` | `695e5e51cdab62910f8d12a7becc74d6c11bd726` | [redirection](https://android.googlesource.com/platform/external/mksh/+/695e5e51cdab62910f8d12a7becc74d6c11bd726/src/exec.c), [Android shell build](https://android.googlesource.com/platform/external/mksh/+/695e5e51cdab62910f8d12a7becc74d6c11bd726/Android.bp) |

These are source pins, not installed-binary provenance. API35 or a utility name
alone does not prove an image contains these exact sources/build options. A
future admitted probe must retain its existing selected-image/client provenance
and refuse an unavailable command; it must not silently switch transports.

## ADB raw exec-in

At the pinned client, lines392–431 copy stdin using a64KiB buffer, stop on host
read EOF, and switch Windows standard input to binary mode. The write result is
not checked in that loop. Lines1818–1843 construct `exec:`, copy stdin, then
return0 without using the copy function's boolean result or a remote-exit packet.
A known client exit0 is therefore necessary for the proposed proof gate, but
cannot establish destination correctness. Host FD position is not a guest-byte
counter. [Client source](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/client/commandline.cpp).

Daemon `exec:` routing selects raw/no-shell-protocol. The corresponding
`StartSubprocess` compatibility path changes raw/no-protocol to a PTY in raw mode
(lines837–841); it is not a guaranteed pipe directly into the utility. Exit
packets are conditional on a shell-protocol descriptor. These facts neither
explain the recorded timeout nor demonstrate corruption in the installed daemon.
[Routing](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/daemon/services.cpp),
[transport and exit handling](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/daemon/shell_service.cpp).

## Conditional third control: shell protocol, no PTY

Both inspected clients support this fixed argument-vector shape (source proposal
only; none of these commands ran):

```python
prefix = [adb_path, "-H", "127.0.0.1", "-P", "5037", "-s", selected_serial]
feature_argv = prefix + ["features"]
transfer_argv = prefix + ["shell", "-T", "-e", "none", fixed_quoted_run_as_command]
```

The last element must be one command string from the closed command builder,
including the same UID/owner/create-only fences and a separate fixed SHELL_CAT
leaf. The client joins command arguments without adding shell quoting. Do not
use `-n` (closes input), `-x` (disables protocol), or any `-t` option.

In Android15 client lines693–791, `-T` selects raw, `-e none` disables the escape
character, and `shell_v2` is negotiated. Explicit `-T` without that feature
returns1 instead of falling back to PTY. The EOF path sends close-stdin through
the protocol. Exit decoding defaults to255 on unexpected disconnection and
uses the remote exit packet when present. [Android15 client](https://android.googlesource.com/platform/packages/modules/adb/+/f8a7480bc3500502d5f12c8fd6d1aecc394a604f/client/commandline.cpp).
Current and Android15 service parsing select raw plus shell protocol, avoiding the
raw/no-protocol PTY fallback; close-stdin half-closes the raw subprocess input.
[Service parsing](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/daemon/services.cpp),
[stdin/exit protocol handling](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/daemon/shell_service.cpp).
[Android15 service](https://android.googlesource.com/platform/packages/modules/adb/+/f8a7480bc3500502d5f12c8fd6d1aecc394a604f/daemon/services.cpp),
[Android15 transport](https://android.googlesource.com/platform/packages/modules/adb/+/f8a7480bc3500502d5f12c8fd6d1aecc394a604f/daemon/shell_service.cpp).

Require `shell_v2` as an exact selected-transport feature line. The current
`features` CLI emits common features one per line (lines2173–2182), not a comma
list; `host-features` alone does not establish selected-device support. Feature use
requires both the queried set and client-supported set; do not force/fake a
feature with an invented environment variable.
[Feature query](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/client/adb_client.cpp),
[feature intersection](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/transport.cpp).

There is a material Windows binary-input qualification gap. Shell stdin calls
`unix_read_interruptible`, whose non-console branch calls CRT `read`; its source
explicitly permits text translation. Unlike exec-in's copy prologue, the
inspected `RemoteShell` path does not itself select `_O_BINARY`. These flags
therefore establish protocol/no-PTY selection, not a complete Windows binary
guarantee. The exact installed build/CRT startup mode remains unverified.
[Windows stdin implementation, lines2328–2348](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/sysdeps_win32.cpp),
[CRT mode distinction](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/sysdeps.h).

A separately admitted qualification must first establish known nonzero and zero
remote status (for example a fixed exit42 check), then exact size/SHA of an
original tiny binary input containing CR/LF,0x1A,NUL,high bytes and escape-like
text. ASCII-only preflight does not resolve this gap. A binary mismatch refuses
SHELL_CAT; no rewriting/encoding of the original1GiB fixture or silent fallback.
Even after qualification, full independent guest size/SHA and existing budgets
remain required. No remote-status qualification is claimed here.

`TERM` is forwarded into shell service arguments. Use a fixed child environment
that omits it, while retaining existing ADB routing/environment fences. Explicit
host/port/serial arguments must remain. `ADB_COMPRESSION` belongs to push/pull
parsing and is not a documented fix for this stream path. Source inspection
does not authorize changing the existing controller's environment policy.

## Utility behavior

The Android15 build lists both source files and `cat`/`dd` command symlinks.
[Android.bp lines90,98,256,272](https://android.googlesource.com/platform/external/toybox/+/e1a5a73c328e03e7e8de9090cf04cf8e86340113/Android.bp).

Plain `cat` reads up to `sizeof(toybuf)` and writes each returned chunk using
`xwrite`. Its `-u` option instead requests one byte and is excluded from this
comparison. The shared buffer is4096 bytes in the pinned Android15
[main.c](https://android.googlesource.com/platform/external/toybox/+/e1a5a73c328e03e7e8de9090cf04cf8e86340113/main.c).
Read errors set the utility error state; a zero read ends the loop.
[cat implementation](https://android.googlesource.com/platform/external/toybox/+/e1a5a73c328e03e7e8de9090cf04cf8e86340113/toys/posix/cat.c).
`xwrite` requires `writeall` to complete the chunk or exits with error; `writeall`
loops over partial writes, and error reporting sets a nonzero utility exit value.
[xwrap.c lines551–554](https://android.googlesource.com/platform/external/toybox/+/e1a5a73c328e03e7e8de9090cf04cf8e86340113/lib/xwrap.c),
[lib.c error/write helpers](https://android.googlesource.com/platform/external/toybox/+/e1a5a73c328e03e7e8de9090cf04cf8e86340113/lib/lib.c).

The inspected `dd` implementations accept decimal `bs=1048576`; `bs` overrides
both input/output sizes and allocates a1MiB buffer. Short reads pass directly to
output. The loop handles partial writes and retries interrupted reads/writes;
EOF ends input and remaining data is flushed. Without conversions, it does not
pad short reads. Read/write errors terminate with error. Default statistics go
to stderr; `status=none` is implemented. `of=` independently creates/truncates its
file. `fsync` occurs only when explicitly requested. These are source semantics,
not observed buffer sizes, throughput or durability on the target.

Actual flag tables reject `iflag=fullblock`, `conv=excl`, `conv=sparse`,
`conv=nocreat` and `oflag=append` despite some appearing in help/TODO text. Do not
add them. Avoid `conv=sync`/`noerror`: they alter failure/data semantics. These
conclusions hold for both pinned [Android15 dd](https://android.googlesource.com/platform/external/toybox/+/e1a5a73c328e03e7e8de9090cf04cf8e86340113/toys/posix/dd.c)
and [current dd](https://android.googlesource.com/platform/external/toybox/+/59a869a838cfadbf6bc41cb400471ca9d2cae9b5/toys/posix/dd.c).

If a later question specifically requires reblocking, supported separate
`ibs=1048576 obs=1048576` without `bs` buffers input toward full output blocks and
allocates2MiB in these sources. That is a different control, not an instruction
to change the frozen CAT/DD_1M experiment or a performance recommendation.

## Create-only shell boundary

Use the same validated private-directory/UID/owner/absent-file fences for both
fixed commands, with shell `set -C` and `>` opening the sink. The conceptual
payloads are `cat > fixed_sink` and `dd bs=1048576 > fixed_sink`; the coordinator's
closed command builder owns all real names/quoting and any output suppression.
No untrusted argument or arbitrary destination is introduced here.

Pinned mksh's `set -C` `>` branch refuses existing regular files, uses
`O_WRONLY|O_CREAT|O_EXCL` when the path is absent, and has a post-open check for
nonregular-path races. `>|` or disabling noclobber instead enables truncation.
Nonregular destinations are deliberately permitted, so noclobber does not
replace explicit absent/non-symlink checks. It does not pin parent directories
against a hostile same-UID actor. `dd of=fixed_sink` bypasses shell opening and
loses this protection. [exec.c lines1435–1456,1502–1525](https://android.googlesource.com/platform/external/mksh/+/695e5e51cdab62910f8d12a7becc74d6c11bd726/src/exec.c).

## Bounded next probe and limits

The source review finds no invalidity in DD_1M as specified. Preserve the
original deterministic1GiB fixture and two independently qualified create-only
sinks, full source authentication/held-FD mutation checks, parent identity,
lease, one-shot claim, Job ownership and cleanup gates. Retain150s client,
180s parent and existing reserve with no clock shifting. Utility/source buffer
differences motivate a comparison; they establish no speedup.

Only known client success and cleanup permit the independent full guest size
and SHA proof. Require exact equality to the original fixture; raw exec cannot
substitute its exit status for that proof. Size/SHA equality establishes
matching readable contents at observation, not power-loss durability or remote
process-reap provenance. Any timeout, unknown cleanup, unsupported utility,
short/mismatched proof or uncertainty stops dependent work and closes only the
exact host owner. Do not query/retry old quarantined targets, infer guest
progress from host cursor, or proceed to model/import/SDK work.

Validation here: official source/ref inspection and `git diff --check` only.
No transport command, fixture-generation benchmark or device test ran. Root
owns implementation, separately admitted execution and evidence reconciliation;
M05.05/M01.05 acceptance and the physical-device gates remain unchecked.
