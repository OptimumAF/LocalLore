# Host helper failure ownership proof, 2026-10-23

Refs [#8](https://github.com/OptimumAF/LocalLore/issues/8) (M04.04), base
`540dff07e5e09019bd04bcc4ea5ad7dc32cacb1f`.
This extends the [schema3 host calibration](SCHEMA3_CAPACITY_HOST_2026-10-23.md)
with actual bounded child failures. It does not alter production Store/Host/JNI,
schema, dependencies or the qualified17/32-page profiles.

## Actual cases and ownership

The existing relief example accepts an explicit fixed `--helper-fault` selector.
It creates an extra exact owner/fault marker inside its fresh marked synthetic
directory. The Python helper requires that marker and the existing canonical
path, owner and exact-schema3 read-only preflight. Unknown selectors are rejected
before SQL. There is no arbitrary script, SQL or error-message argument.

Every case first performs the **actual14-row fill**, with the15th fixed3,500-byte
zero-BLOB insert returning SQLite Full at32 pages/free0. Only after the connection
closes does the child fsync a bounded create-new readiness marker and execute its
selected fault. The final reports bind that marker to the owner, case and measured
fill profile. The original failure and cleanup outcome have separate categories,
child exit codes, kill requests, kill results and observed terminal/reap states.

| Fixed case | Original observed failure | Actual child ownership | Cleanup |
|---|---|---|---|
| malformed | `helper_json` | Terminal exit0, reaped | Separate child removed14 rows; exact schema restored/free15; terminal exit0, reaped |
| overflow | `helper_output_bound` | Fixed8KiB stdout; kill succeeded; observed terminal exit1/reap | Same exact restoration and terminal/reaped cleanup |
| timeout | `helper_deadline` | Child remained waiting;10-second deadline requested kill, succeeded; observed terminal exit1/reap | Same exact restoration and terminal/reaped cleanup |
| after-fill | `helper_result`, `injected_after_fill` | Terminal exit1, reaped | Same exact restoration and terminal/reaped cleanup |
| cleanup-refusal | `helper_result`, `injected_after_fill` | Terminal exit1, reaped | Distinct `helper_result`/`injected_cleanup_refusal`, terminal exit1/reaped; refused after read-only validation; padding intentionally retained |

Each final case observed **zero later Host dispatches and zero workspace opens**,
with two actual child starts: failed fill and one cleanup attempt. Counters
increment immediately before actual `Host.call`, workspace open and after child
spawn, rather than recording an assumed post-return flag. No failed fill returns
to gameplay or native reopen, including after successful cleanup. The refusal
case leaves its private synthetic database retained with the temporary pad;
there is no claim that its cleanup succeeded.

The4KiB output threshold is observed by polling; it is **not a hard filesystem
quota**. The overflow payload is fixed at8KiB. Overflow/timeout children wait up
to120 seconds so the parent's real kill/reap path is exercised. Parent execution
is bounded to10 seconds and kill-to-terminal observation to2 seconds. A kill
request alone never authorizes cleanup. Missing terminal/reap proof suppresses
all follow-on helpers and native work while preserving the original category.
No actual unkillable/unknown-ownership OS incident occurred: two Rust policy tests
cover that branch, separately from the measured known-reaped process cases.

Fault reports use distinct scope `host_synthetic_helper_fault_v1`, version1;
`passed` means the expected failure/guard was observed, not gameplay acceptance.
The fault cases do not call Rust commit after filling and therefore do not
independently establish a Rust commit-Full result. The unchanged normal accept
and cancel cases were rerun: both passed, including two actual Rust commit-Full
responses, unchanged canon, exact schema restoration, original-key acceptance
or terminal cancellation, and strict reopen. Their parsed version2/schema3 JSON
results exactly matched the prior qualified reports. Relief still issues zero
fresh submits/prepares and uses32 pages, initial17,14 rows and15 free pages after
removal.

## Reproduction and verification

Use a fresh task-owned directory on a roomy volume for `$faultRoot`, its `tmp`
subdirectory, and `$python` as the installed Python executable. Private locations
are redacted; the commands preserve the executed argument sets. Malformed and
overflow used `cargo run`; the remaining final cases used the executable built
by the overflow invocation. Every case directory must be new.

```powershell
$env:TEMP="$faultRoot\tmp"
$env:TMP=$env:TEMP
$env:CARGO_TARGET_DIR="$faultRoot\cap32-target"
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=32'
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline -- --directory "$faultRoot\malformed-final" --python $python --helper-fault malformed
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline -- --directory "$faultRoot\overflow-final" --python $python --helper-fault overflow
& "$faultRoot\cap32-target\debug\examples\capacity_relief_probe.exe" --directory "$faultRoot\timeout-final" --python $python --helper-fault timeout
& "$faultRoot\cap32-target\debug\examples\capacity_relief_probe.exe" --directory "$faultRoot\after-fill-final" --python $python --helper-fault after-fill
& "$faultRoot\cap32-target\debug\examples\capacity_relief_probe.exe" --directory "$faultRoot\cleanup-refusal-final" --python $python --helper-fault cleanup-refusal
& "$faultRoot\cap32-target\debug\examples\capacity_relief_probe.exe" --directory "$faultRoot\malformed-owner-metadata-final" --python $python --helper-fault malformed
& "$faultRoot\cap32-target\debug\examples\capacity_relief_probe.exe" --directory "$faultRoot\normal-accept-final" --python $python
& "$faultRoot\cap32-target\debug\examples\capacity_relief_probe.exe" --directory "$faultRoot\normal-cancel-final" --python $python --cancel
cargo +1.93.1 test -p locallore-workspace --example capacity_relief_probe --locked --offline
python -B -m unittest discover -s scripts/tests -p test_capacity_padding_probe.py -v
cargo +1.93.1 clippy -p locallore-workspace --all-targets --locked --offline -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
```

Final verification: all five fixed faults, both normal regressions,31 Python
guards, two Rust ownership-policy tests, strict Clippy, formatting and whitespace
checks passed. New guards bind fault authorization to its exact additional marker,
refuse unrelated removal/old-schema bypasses, and prove cleanup refusal uses
read-only validation without dropping padding. The first compile failed on the
wrapper error type and closure type inference; both were corrected before any
child launched. The first successful malformed run preceded explicit successful
cleanup-owner metadata; its final repeat verified that addition. All attempts
were retained. No partition ENOSPC, mid-SQLite-transaction kill, device, model,
ARM64 or phone result is claimed.

## Retained evidence identities

Raw logs and synthetic databases remain private. All13 attempt/check log lengths
and SHA256 values are recorded below; no paths, owner IDs, story payloads or raw
diagnostics are published. The private index also identifies the bounded child
stdout/stderr and readiness artifacts. The overflow child's stdout was8,192
bytes; the timeout child's stdout was empty.

| Evidence ID | Bytes | SHA256 |
|---|---:|---|
| after-fill-final.log | 1030 | `44813d491b43612a2b0445caea8f99fda2e0c0e8ecf88cc8a4a11a2b6b976704` |
| cleanup-refusal-final.log | 833 | `a30034e12c94c2d685c1f89e561fe0b6815c7b5d785a780b17f26b21e3eedd43` |
| clippy-initial.log | 1216 | `d77124172e8b1c5e00b353c01aa2e8591645d1da15004f0a5f74d546624e5938` |
| fmt-final.log | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| malformed-final.log | 1357 | `0c543ba023d84f23ba5dbfedcb44231d9a94388f71de2ce523fefa5309ca9889` |
| malformed-initial.log | 2950 | `976b13cd0f92767402a5ee76d821586d7fef71ea4402708f3db348146851b61d` |
| malformed-owner-metadata-final.log | 1010 | `db713f013f23185f07e544a35400ccb4e750724b2a12362edcee106663aaebdf` |
| normal-accept-final.log | 981 | `a061550b1ee08683a108c747a1dd20b033c1f71825c7bf3995389f308fc2b2f9` |
| normal-cancel-final.log | 1009 | `471491257f55bd9340d207b4040fb9c9b96a619773528de4b4df84811bb38ece` |
| overflow-final.log | 1475 | `7bdbda15d5164715d96d3ff7cb049d71bd96d5573b8eaf9cda8822dd4a3d9bb2` |
| python-final.log | 3477 | `195c953a62b6d7e83194f0a48e57d264bceee4153bbd477be7295dc42533fb9d` |
| rust-policy-final.log | 667 | `6b7cf2aa291e92cefe43641c5a04e2072dea73afe1e62a1a41e5c609f7be85d2` |
| timeout-final.log | 1010 | `2edaa8b01133ce3dd854d77f6f2a4a9b2d54007ceafb1fd1ed6029320481d2e5` |

Private `handoff-index.json` SHA256:
`276ec2d7caf5cead6e9b0630f289b911fa8f0246ed5e1740b267dc2923d53ad7`.
Owner acceptance and integrated Android failure-path qualification remain
separate gates.
