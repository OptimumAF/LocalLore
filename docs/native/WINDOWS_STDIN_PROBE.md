# Windows regular-file stdin mechanism control

Supporting M01.05/M05.05 under root issue #9 claim6405512050 and PR181.
This host-only control demonstrates the Windows CRT text/binary distinction.
It does not execute the installed ADB client, contact a server/device, or
qualify a shell transport. It introduces no dependency or production change.

Run explicitly on Windows with the existing Python installation:

```powershell
python -m unittest discover -s scripts/tests -p test_windows_stdin_probe.py -v
python benchmarks/windows_stdin_probe.py run
```

The unit suite substitutes the CRT and process runner. It does not run the
actual control automatically. Non-Windows invocation reports unsupported and
launches no child. The actual control loads the OS-provided `ucrtbase.dll` using
System32-only DLL search; it does not identify/hash that installed DLL or infer
which CRT the installed ADB binary uses.

## Fixed experiment and ownership

The original input is exactly `bytes(range(256)) * 3`:768 bytes, SHA256
`f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363`.
One exclusive regular file holds this unchanged input. The parent retains its
open descriptor and checks visible/held descriptor identity (including size and
nanosecond modification time) and full contents
after both controls. No bytes are escaped, encoded, filtered, or replaced.

Each child waits for the existing `runtime_spike.run_process` stdin barrier.
That runner assigns its owned Windows Job before releasing the bounded request.
It retains the existing kill-on-close, deadline, output cap and cleanup proof.
Each control has a10-second child deadline and4096-byte combined output cap.
Only two fixed controls run; no external executable, compiler, ADB command,
network connection, native inference or emulator is required.

After the request pipe reaches EOF, the child uses the **same CRT DLL** to open
the regular file read-only/binary, duplicate it onto CRT descriptor0, verify
all768 original bytes in binary mode, rewind with `_lseeki64`, then explicitly
select `_O_TEXT` or `_O_BINARY`. It calls `_read` to EOF, with at most four1024-byte
reads per verification/measurement and at most768 retained bytes. It closes
each acquired CRT descriptor. The child emits only closed enums, booleans,
numeric counts and hashes. It emits no source bytes, source path, PID, raw
exception, environment or private diagnostics.

The parent credits a result only with client completion/exit0, known Job and
pipe cleanup, zero stderr, a strictly validated worker result, verified source,
known EOF and closed descriptor. It retains mismatches without crediting them.
A wrong/short binary result, malformed JSON, duplicate fields, nonfinite
numbers, unknown cleanup or mutated source cannot produce overall success.
Dispatch stops after a noncompleted, unparsed or unclean client. Overall
`observed` requires both modes, intact source and completed fixture cleanup.
Unknown child closure closes the parent's own descriptor but preserves the
private fixture directory, reports `fixture_retained=true`, and refuses further
dispatch. That flag also remains true when exact file/directory removal cannot
be proved; it discloses no path. Cleanup uses only exact owned file unlink and
directory removal, with no recursive operation.

## Historical observation at930d5ab0 — 2026-10-25

The API `run_probe(runner=traced_existing_run_process)` ran against the actual
Windows CRT. The trace wrapper saved the existing runner's raw stdout without
modifying requests/results. Both children verified the entire original input
before measurement. The parent verified that the source remained unchanged.

| Explicit mode | Observed bytes | Observed SHA256 | EOF/read calls | Client/cleanup |
|---|---:|---|---|---|
| TEXT | 26 | `b858da80d8a57dc546905fd147612ebddd3c9188620405d058f9ee5ab1e6bc52` | true/2 | completed/0/true |
| BINARY | 768 | `f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363` | true/2 | completed/0/true |

Both report `descriptor_closed=true`, `source_verified=true`, zero stderr and
expected size/SHA equality. Elapsed times were181/195ms; these are observations,
not latency requirements or a transfer benchmark. The26-byte output is exactly
the prefix0x00 through0x19, ending before the first Ctrl-Z (0x1A).

Ignored host evidence is retained under `target/windows-stdin-probe-20261025`:

| Record | Bytes | SHA256 |
|---|---:|---|
| `case-01.stdout.bin` | 229 | `5e6ede3e57cc2f3f3bceee0e7e40d7294a3ffdf6c2c7013445b4b21d896ec5fb` |
| `case-02.stdout.bin` | 232 | `d7bca9377be81b5ed77576607a3a63b25af56a281f332d9b38ced82d7f16478e` |
| `result.json` | 2021 | `87cd74f4eb935d6608ccfc94f66aa16f00de266961bd68e697991a4738cd8fd9` |

The result includes identical before/after source SHA256 bindings:

| Source | SHA256 |
|---|---|
| `benchmarks/windows_stdin_probe.py` | `7786fe77070773b2b53d186cd1d3cba68f203730723571ad263534c82de15d40` |
| `benchmarks/runtime_spike.py` | `237ae7a2fcc2469b27f79c4266e2e45f653d4e5b09af7009a4299dee31e73816` |
| `scripts/tests/test_windows_stdin_probe.py` | `1b2980cb6e63816acfa5d7ac3be4dbed9a039464dde3f407844568f2531a2552` |

At930d5ab0,14 mocked tests passed. They covered original hashes, same-CRT ownership,
corrupt sources, descriptor/read/mode/seek failures, bounded endless short
reads, cleanup failure, private exceptions, invalid requests, bad client
metadata, malformed/duplicate/nonfinite output, short binary mismatches,
fixture mutation, spawn failure and explicit unsupported hosts.

## Ownership correction and fresh observation — 2026-10-25

Root review found that the original parent could dispatch BINARY after an
unclean TEXT client. Three new regressions failed on that implementation:
unknown cleanup and spawn failure each dispatched two children instead of one;
identical contents with changed modification time were accepted. The corrected
implementation stops new dispatch, retains partial refusal, requires all two
modes, preserves the fixture on uncertain closure without leaking the parent's
descriptor, and checks modification time as well as identity/size/contents.
The original records above remain historical evidence and were not overwritten.

The corrected17-test suite passes. A fresh actual API control under distinct
ignored namespace `target/windows-stdin-probe-v2-20261025` again observed TEXT26B
and BINARY768B with the exact same respective hashes and raw worker stdout
hashes above. Both source verifications, EOF/read counts, descriptor closures,
client exits, zero stderr and Job/pipe cleanup passed; source unchanged was true
and `fixture_retained=false`. Elapsed times were224/185ms. The public CLI was
also rerun and exited0/observed with the same exact contents, measurements
of214/195ms, and no retained fixture. Timing is not an acceptance
threshold.

The new `result.json` is2046 bytes, SHA256
`1fdf72b167291d72f0f6c8499dc4e8559f6fc547da1a9f8c42c81755d809b9cf`.
Its before/after bindings are identical:

| Source | SHA256 |
|---|---|
| `benchmarks/windows_stdin_probe.py` | `c3c186cd8c9c2152fb2b1cca3e732c1d41a9df4d071512f78bb62369937fde2f` |
| `benchmarks/runtime_spike.py` | `237ae7a2fcc2469b27f79c4266e2e45f653d4e5b09af7009a4299dee31e73816` |
| `scripts/tests/test_windows_stdin_probe.py` | `2b7c4f0f056e5627c8a109c8297e92d815836036c85ff79c6667002d75352bc8` |

Final review additionally marked child closure unproved **before** invoking the
runner, and tested a `RuntimeError` (for example failed reader-thread startup)
alongside `OSError`. Both produce one retained partial refusal without private
exception text. All17 tests still pass. The final-source actual API run is
separately retained under `target/windows-stdin-probe-v3-20261025`:2046-byte
`result.json`, SHA256
`9b15ef9bfb68fdf0c4d1a4d491b6622b552f1117176c44cdd3d3549f39e09f54`.
It again proves the same exact26B/768B hashes and raw stdout hashes, known
EOF/descriptor/Job/pipe closure, unchanged source and no retained fixture
(179/193ms). The final public CLI also passes (180/235ms).
Final before/after source hashes match:

| Source | SHA256 |
|---|---|
| `benchmarks/windows_stdin_probe.py` | `3998c53648eabdd8e55a0636881b3ccba793e13aef4c31bd39ce3313586cb23c` |
| `scripts/tests/test_windows_stdin_probe.py` | `5d188f753a97e052615e46cd8afec79ecabef35d379d7d49d5ea36fbe87c229b` |

The runner source hash is unchanged from the earlier records. These successive
records are bounded host-mechanism checks, not retries against a failed device.

A subsequent review found that uncertainty stopped dispatch/deletion but still
allowed the parent to seek/read/stat the fixture. The new poisoned-postcheck
regression failed on3765b185 at `source.seek(0)`; the whole postcheck now requires
known child closure. Unknown closure leaves `source_unchanged=false`, performs
no dependent seek/read/stat, closes the parent descriptor and preserves the
visible fixture. All18 mocked tests pass. The actual CRT records above retain
their historical source bindings; this later refusal-path correction was not
part of their source freeze. No additional actual control or runtime/device
execution is claimed for this follow-up. Root integration follows closure of
the separately frozen47bb105 owner and requires a later host gate.

## Official source interpretation and limits

At official ADB commit `1cf2f017d312f73b3dc53bda85ef2610e35a80e9`,
[`commandline.cpp`](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/client/commandline.cpp)
lines352–360 explicitly select binary stdin in the copy prologue used by
`exec-in`. The inspected `RemoteShell` path626–693 starts its input thread
without that prologue. Lines530–548 read stdin through
`unix_read_interruptible` and send shell-protocol close-stdin when the read
returns zero or error. `-T`/`-e none` select no PTY/no escape processing; they do
not select a CRT binary input mode.

Pinned [`sysdeps_win32.cpp`](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/sysdeps_win32.cpp)
lines2285–2289 return from console raw setup for nonconsole input; lines2331–2353
use CRT `read` for files/pipes. Microsoft documents that
[`_read`](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/read?view=msvc-170)
treats Ctrl-Z as EOF in text mode, and
[standard streams default to text mode](https://learn.microsoft.com/en-us/cpp/c-runtime-library/text-and-binary-mode-file-i-o?view=msvc-170).
The control uses documented
[`_setmode`](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/setmode?view=msvc-170)
to choose each mode explicitly.

This mechanism predicts the exact26-byte prefix/hash already observed by the
separate shell prerequisite, plus clean EOF and potentially successful remote
`cat` exit. The actual control establishes that prediction on the host CRT.
It does **not** establish the installed ADB binary's source correspondence,
startup CRT mode, executed read path, or the actual cause of that transport's
mismatch. Opening a Python parent descriptor in binary mode alone does not
prove the separately launched child's CRT mode. No synthetic smart-socket
server or installed ADB execution was added to this focused control.

The original shell prerequisite remains failed and the large SHELL_CAT remains
refused. Root owns any evidence-backed transport correction, regression,
separate fresh-target authorization and independent exact binary/large-file
verification. This control does not permit reusing a failed target or lowering
source/owner/lease/hash/one-shot/deadline gates. No model import, inference,
restart, phone compatibility or milestone acceptance is claimed.
