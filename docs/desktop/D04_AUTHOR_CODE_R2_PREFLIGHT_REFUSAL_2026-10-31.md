# Author R2: approved, blocked before admission

Refs #25 D04.02, #9 and draft PR301. The owner directly replied **approved** to
the pending one-corrected-baseline question on October 31, 2026. This permits
one corrected code baseline and remaining code checks only after a valid result;
all hard caps, retention and no-app/no-automatic-retry restrictions remain.
The local decision records the direct reply, without inventing a missing tool
question identifier. It and the R2 Stage were created exclusively.

## Exact preparation and refusal

Root rechecked all37 retained fixture fingerprints, including the additional10
empty roots from the failed first baseline, and the preserved8,210,944-byte
unit executable with SHA256
`6063b167cbd8366edddcf777a210fe6c06e4a14cbe8bf20fdfc2a6017351da5e`.
The reviewed coordinator/admission hashes remained unchanged. Actual metadata
was1,196,222B; admission/START plus the full106,496B child reserve forecast
1,307,838B, fitting the unchanged1,310,720B limit by2,882B.

From the physical D: source checkout, with process-local TEMP/TMP set to
`D:/Dev/_Temp`, Root invoked once:

```powershell
& '../author-integration-artifacts/d08-fork-native-20261030-v1/author-r2-admit.ps1' -Phase baseline
```

The invocation exited1 at line34: `Get-CimInstance Win32_Process` returned
`Unspecified error`. This precedes admission creation and runner invocation.
Read-only checks confirmed that R2 admission, START, PASS and STOP files are all
absent. No corrected baseline test child or app launched. The original invalid
baseline and unknown ownership history remain unchanged.

The533-byte local `author-r2-pre-admission-refusal.json` preserves the refusal;
its cost remains charged. No existing record or marker was rewritten or removed.

## Read-only diagnosis and evidence boundary

The actual shell is PowerShell7.6.5 from the installed Codex runtime, on Windows
10.0.26300 x64, with CimCmdlets7.0.0. The Winmgmt service is running. A separate
read-only schema diagnostic also failed:

```powershell
Get-CimClass -Namespace root/cimv2 -ClassName Win32_Process -ErrorAction Stop
```

It returned `Microsoft.Management.Infrastructure.CimException`, error identifier
`HRESULT 0x80004005,Microsoft.Management.Infrastructure.CimCmdlets.GetCimClassCommand`,
native error1 and HResult-2146233088. This establishes that the required process
inventory is unavailable through this shell; it does not establish a root cause
or prove that no owned process currently exists. No Windows service, permission,
module, application, global cache or security setting was changed.

Independent source review confirmed that no baseline execution was consumed.
However, the frozen plan makes any further failed check terminal and does not
explicitly exclude pre-admission environment refusals. Root therefore has not
automatically invoked admission again. No fallback process list, manual zero
count or substitute closure proof is allowed.

Next: resolve process-inventory availability and explicitly dispose of this
pre-admission refusal under the frozen contract before another admission attempt.
That attempt must use unchanged guards, fresh successful process observations
and full actual storage admission. Author Phase2 remains on hold until complete
valid16-case behavioral RED and Root raw-log review. No corrected test result,
Author implementation, app/native IPC/render, model, Android/device, OS/network
qualification, merge or release is claimed. D04 and the desktop epic remain open.
