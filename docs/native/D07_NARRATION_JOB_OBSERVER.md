# D07 held process observation for local narration comparisons

Refs #29 (D07.03, D07.04), supporting #25 (D04.04, D04.06).

The [A3 comparison](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6747007761)
stopped on `OwnedImage` after observing the exact probe and worker. Its
retained terminal lists known closure for both held processes and no
comparison report. The failed query lacks a process identity and Win32
error number. Its cause remains unconfirmed and A3 remains failed.

The benchmark observer accepts an already owned Windows Job, the fixed
probe PID from the launcher and the pinned probe and worker image paths.
It confirms Job membership, creation time, image and live state on each
required process handle. It retains one probe and one worker until their
exit codes and handle closure are known. A missing required identity,
wrong image for a required role, second identified worker, live or
uncertain image failure, or uncertain cleanup refuses qualification.

After both required identities are positively established, an image
query failure for a distinct Job member gets at most 50 ms to signal on
its held handle. A confirmed exit records the PID, creation time, Win32
image-query error and exit code in a separate bounded list of at most 16
entries. It earns no probe or worker credit. A refusal keeps the
Win32 error and exact held PID and creation time for local diagnosis. This is an observation
category for a later run, rather than a classification of the original
A3 failure. The [Win32 process termination contract](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process)
defines the signal used for exit confirmation.

The later comparison launcher still needs its own exact source and
artifact pins, a fresh approved run, the existing time and storage
checks, complete shared Job/output closure, and all ten report and
control comparisons. During that run, the supervisor holds the launcher
process handle, confirms its identity in the marker, and samples on
each poll after the fixed probe PID is available. Return false from the
sampling callback to keep it active after both roles are observed.
Finalize after the shared Job closes. Capture the numeric image error
and held identity before passing a refusal to the shared supervisor.
On failure, close retained handles and preserve the original refusal
and available terminal evidence.

## Host verification

From the physical D: checkout:

```powershell
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP
python -B -m unittest -v scripts.tests.test_narration_process_observer
```

Synthetic fault tests inject missing or changed identity, a confirmed
transient exit, a live image failure, and incomplete cleanup. The Windows
case runs only two short inert Python processes under the existing
supervisor and exercises the real Win32 Job, image, wait and close APIs.
It uses an existing windowless interpreter and retains bounded synthetic
Job and observer terminal records in the printed physical D: directory.
The transient image failure is injected in the fault tests.

On Windows x64 10.0.26300.0, Python 3.14.7 and PowerShell 7.6.9,
the command above plus `scripts.tests.test_windows_job_close` passed
43 tests in 1.048 seconds. These were 14 fault cases, one actual
Windows Job fixture and 28 existing Job cleanup cases. Both inert
processes exited zero and the shared Job terminal reported 1,019 ms,
empty output and known cleanup. The retained four-file fixture is 524
bytes. The observer proof SHA-256 is
`0e4b7c51321bed5095ee6fbe7ebf1e034c66cd7e555843bc66b3648b8dfc6dec`.
This evidence leaves the candidate comparison and human quality review
open.
