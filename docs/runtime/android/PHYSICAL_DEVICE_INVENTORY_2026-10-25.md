# Physical device capability inventory, 2026-10-25

Refs #5 (M01.01), coordinator claim 6404879571 and inventory claim 6404891543.
The user offered a connected Android device. This is a read-only capability
inventory, not application, ARM64 runtime, model or performance qualification.

The existing ADB server's executable, process identity and listening port were
verified before selection and again before and after targeted reads. Inventory
returned three emulator-prefixed entries and three other entries. The latter
were not three proven phones: two network entries advertised an emulator model.
The coordinator selected the single non-network Samsung entry as alias **P**;
all five other entries remained unprobed. P reported `ro.kernel.qemu=0`.

| Observation | P |
| --- | --- |
| Manufacturer / model | Samsung / SM-S918U1 |
| Android / API / security patch | 16 / 36 / 2026-09-05 |
| SoC / board | QTI SM8550 / kalama |
| Advertised ABIs | arm64-v8a, armeabi-v7a, armeabi |
| Page size | 4,096 bytes |
| Kernel-visible RAM | 11,581,173,760 bytes, approximately 10.79 GiB |
| Available RAM at inspection | 3,311,497,216 bytes, approximately 3.08 GiB |
| Userdata capacity / available | 495,498,260,480 / 293,887,492,096 bytes |
| Shared-storage available | 293,887,492,096 bytes |
| Power / battery | USB powered; 91/100 |
| Battery temperature | 30.9°C, service field 309 |
| Thermal service | Readable; reported status 0 |
| Fixed LocalLore package/process checks | 33 names; none installed, no matching process |

The two requested storage views reported identical capacities; they are not
credited as independent or additive space. Battery temperature uses Android's
[tenths-of-Celsius health field](https://android.googlesource.com/platform/hardware/interfaces/+/master/health/aidl/android/hardware/health/HealthInfo.aidl).
Thermal and available-memory observations are transient, with no sustained-load
or allocation guarantee. Available memory was below 4 GiB; no existing model
admission gate was waived and no inference was attempted.

Three attempts are retained. The first selected a nonexistent host helper and
stopped before server/device work (`spawn_failed`, cleanup flag false, 1 ms).
The second verified the server and enumerated devices, then refused ambiguous
selection with known cleanup and zero targeted calls. The corrected third
attempt completed 21 bounded host commands, including 17 targeted read-only calls,
all returning 0 with known cleanup. Across attempts there are 24 command records:
23 completed with known cleanup and the original prelaunch failure. Every command
had a 15-second deadline and 131,072-byte combined output cap. All retained stdout
sizes and SHA256 bindings were independently reread.

The private seal binds 59 selected files / 73,974 bytes; index 11,520 bytes,
SHA256 `d87d2f6306ccb5553f4e59c4b7282b5a9cd284fe1cd2cf6370ae2d7433833685`.
Final inventory source SHA256:
`528b63751791fae223988c39e2c0cc6379112a3178aa75f4254b351a79073dcc`.
Serials, device paths, process IDs, exact argv and raw diagnostics remain private.

No APK installation, removal, launch or force-stop; model copy/read/inference;
app-data access; server lifecycle; device setting; or OS change occurred. A
separately admitted, isolated, non-model app/JNI test can be planned next using
fresh identity, package absence, storage, power and ownership checks. This
inventory supplies no passing app tests or milestone acceptance.
