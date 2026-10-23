# Cacheprobe app-domain model verification, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.03/M01.05), claim
`6371399958`. This adds an integrity observation to a new experimental APK; it
does not select a production model, provision weights or run inference. It
requires a newly qualified artifact. The older `50e6e60c...` APK does not expose
this operation and must not be substituted for it.

## Request and result

The explicit instrumentation operation is `verify_model`, with the existing
exact framework `volume_uuid` and a fresh 32-lowercase-hex `session`. It rejects
`play_case` and `profile_base64`. It selects the same mounted, writable,
nonprimary, nonemulated volume and its framework-returned app external-files
directory. The only leaf is `gemma4-e2b.litertlm`; there is no path argument,
search, provisioning or fallback to another package's files.

The terminal `cache_result` keeps the existing volume inventory, `sample`,
`post_sample` and metrics. It adds exactly:

```json
{"model_identity":{"verified":true,"sha256":"<64-lowercase-hex>","bytes":2588147712,"diagnostic":"verified"}}
```

The fixed expected SHA256 is
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Diagnostics are `verified`, `absent`, `mismatch`, `unstable`, `incomplete`,
`not_regular`, `wrong_volume`, `invalid_receipt`, or `read_failed`. A complete
read may retain its actual digest/count on mismatch. Without a complete read,
`sha256` is empty and `bytes` counts consumed bytes, not a claim of a complete
model hash. No path, raw exception, model content or private prose is returned.

Outer `completed` means a clean integrity observation, including an observed
`verified:false`; it does not mean a model matched. A verified callback also
requires the strict coordinator parser's matching sample/post-sample volume
identities and zero engine/conversation counts. The receipt alone is not
permission or sufficient capacity to initialize an SDK engine.

## Read and ownership boundary

`CacheModelIdentity` holds no Android or SDK dependencies. It streams SHA256
through a fixed 65,536-byte buffer and one supplied handle, reads no more than
the expected bytes plus one EOF-check byte, and closes before returning a
receipt. Production expected values are fixed; package-local synthetic tests
can inject small values.

The Android adapter opens `O_RDONLY | O_NOFOLLOW`, uses `lstat` on the exact
pathname and `fstat` on that single descriptor, and compares device, inode,
regular-file type/full mode, size, mtime and ctime before and after reading.
Public nanosecond fields are used under an API 27 guard. API 26 retains the
public seconds-resolution fallback: it has no subsecond metadata-stability
claim. The selected API 35 experiment can exercise the precise path. Atime is
excluded because reading can update it. Volume/device/framework directory
identity is refreshed after the read before a verified receipt is published.

The full digest binds consumed bytes even when metadata is too coarse to
detect every write. These checks detect ordinary replacement/size/metadata
drift; they are not immunity to a hostile OS or same-UID concurrent replacement
after the final observation. The filesystem and app-private ownership boundary
from the existing harness remains unchanged.

Known read failures produce fixed false observations after the descriptor is
closed. If descriptor close is uncertain, no graceful receipt is returned:
the existing instrumentation process-termination path applies. The 90-second
package watchdog remains unchanged. This operation creates no cache/session
file, SDK engine/conversation or Rust workspace. Framework directory APIs may
still create/fix app-owned directories as already documented.

The installed Android API 36 jar and `api-versions.xml` confirmed the called
`Os.open/read/close/lstat/fstat` APIs and the API-27 introduction of precise
`StructStat` timestamps. The official
[StructStat reference](https://developer.android.com/reference/android/system/StructStat)
and [Os reference](https://developer.android.com/reference/android/system/Os)
describe these public APIs. No dependency, runtime or model selection changed.

## Execution template and evidence limits

After separately admitted installation, model provisioning and fresh storage
checks under the coordinator's device lease:

```powershell
adb -s "<explicit-authorized-target>" shell am instrument -w -r -e operation verify_model -e volume_uuid "<framework-UUID>" -e session "<new-32-lowerhex>" org.locallore.runtimebench.litert.cacheprobe/org.locallore.runtimebench.litert.CacheProbeInstrumentation
```

Use the new artifact's actual hash and strict `parse_model_identity` result;
never manufacture a verification callback from an expected hash or JSON file.
No copy/provision command or SDK execution is included here.

At source freeze, 20 actual JVM tests passed: 11 new integrity tests and 9
volume/request tests. Cases include fixed-buffer streaming/EOF, mismatch,
truncation/growth, changed path/FD identity, mode/ctime/subsecond drift, absent
and nonregular stamps, wrong volume, read/open/close failures, and impossible
read counts. A fresh regular-file NOFOLLOW read also passed on the installed
Windows JVM provider. The synthetic stamp tests do not qualify Android syscall
behavior or claim an actual OS symlink attack test. An initial JUnit command
had a class-name typo and failed initialization before any test body; it is
retained separately. Actual APK/JVM/lint qualification and device results are
subsequent evidence; no model was read or SDK/ADB/device action executed by
the author during these source tests.
