# Android receipt capacity settlement — 2026-10-24

This M05.05 prerequisite and M01.05 supporting packet prepares one fresh,
read-only observation of the existing B emulator. It uses the unchanged closed
recovery profile at `be8efa84b22a812a12ae3056fc8fef061a6880d0`: current package,
UID, process, volume and capacity facts; the exact six historical v1 receipt
proof files; and absence of the fresh v2 proof root. It performs no package
update, instrumentation, cleanup, force-stop, lifecycle management or model
operation. Candidate-directory absence is not remeasured.

The disabled proposal binds 47 inputs / 87,409,219 bytes, SHA-256
`eae5d2c9fe45ba33287e449f207670bc717b270b6513b332d71d7a8bf45f35e1`.
Its controller SHA-256 is
`a4a2f86ec71b1891a14f36a799cf254b5bbbb85e208022952f36983c01aec5c5`.
The expected 35 installed APK hashes and UIDs come from the preceding sealed
recovery final facts and match the original post-update snapshot. All prior
failure, artifact and evidence namespaces remain preserved.

No tests were rerun for this report-only packet. Bound historical provenance
includes the 471 passing repository script tests and 22 passing mocked
controller tests after the staging reserve change, plus the earlier 20 passing
recovery controller tests. Those host checks do not qualify Android PROCESS.
The original live cohort remains three passes and one PROCESS failure; the
corrected v2 cohort requires its own fresh admission.

The unchanged userdata floor is 1,207,959,552 bytes. Incoming corrected APKs total
76,755,379 bytes, requiring at least 1,284,714,931 bytes before installer overhead.
That necessary reserve does not prove sufficient installer capacity. Actual
settlement completed once after independent review and fresh central admission.
The original execution finished with return code zero, known owned cleanup,
8,562 ms, 290 stdout bytes SHA-256
`0152daed5d2879aeb69990e6e4ea1178628b533bf42df5da1f0bc77952e9858d`
and zero stderr bytes. All 29 client records have terminal success, known
cleanup and verified retained raw stdout hashes. There were zero installs and
zero instrumentation commands.

All 35 APK hashes and UIDs matched before and after the reads. Owned and passive
process counts were both actually zero. The six historical v1 proof files
validated ACCEPT, CANCELLATION and REFUSAL with one consistent recorded parent
identity; PROCESS remained absent. The fresh v2 proof root was absent. These
reads neither rerun the historical tests nor establish a current candidate-path
assertion.

Final available userdata was **1,223,847,936 bytes**, leaving **15,888,384 bytes**
above the unchanged floor. The incoming pair therefore remains **60,866,995
bytes short** of the necessary reserve before installer overhead. B remains
blocked for the corrected full cohort. No install, cleanup or automatic retry
followed this observation. A larger isolated target needs its own separately
reviewed preparation, identity and fresh qualification admission; old B data
must remain preserved.

All 47 admitted input bindings were rehashed and archived byte-for-byte,
87,409,219 bytes, archive index SHA-256
`cb6fa4a1b7a3263a3b9460cae458c35e92840ae608c9134e1605da488730b26f`.
The create-only settlement closure inventory contains 120 files / 87,538,206
bytes, SHA-256
`31417777affa16cafada6bb49280661c0138e968e126df875db838c25ec5516a`.
Raw device identities and diagnostics remain private. This report changes no
controller, fixture, runtime or model code. No physical-phone, ARM64, 16 KiB,
power-loss, real-model, privacy or full M05.05/M01.05 acceptance is inferred.
