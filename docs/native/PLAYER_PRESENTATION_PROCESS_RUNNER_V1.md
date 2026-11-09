# Guarded presentation-process runner V1

B44. Refs #14 (M10.02), #13 (M09.06), #307 (supporting M09.04).
This host-only packet connects the separately built [V3 process proof](PLAYER_PRESENTATION_PROCESS_V3.md)
to the finite owned-emulator machinery. It grants no emulator, retirement,
phone, model, ADB or merge authority. Implementation, synthetic host tests,
closed build replay, Android execution and milestone acceptance stay separate.

## Fixed authority

The source chooses `owned-emulator-presentation-process-v1`,
`sdk-presentation-process-v1`, `presentation-process-socket-proof-v1`, client9,
`sdk-session-v9.json` and `owned-presentation-process-boot-claim-v1.json`.
The concrete owner/client/verifier cannot accept a caller-selected profile,
owner class, verifier, package, root, shell, method or model. The source-only
prospective guest is
`D:/Dev/Experiments/LocalLore/2026-11-01-presentation-process-target-v1/avd-v1`.
Defining that path does not prepare it or reserve capacity.

The admitted artifact set is exactly `build`, `product_apk`, `test_apk`,
`controller_apk`. The product is `org.locallore.app.presentationprocessverify`,
its test package adds `.test`, and the external controller is
`org.locallore.app.presentationprocesscontroller`. The test APK is installed
and checked as build identity evidence; this profile invokes no JUnit method.
The two compiled B43 instrumentation tests remain separately unrun.

There is one durable `presentation_process` claim, created before dispatch.
Its exact command has fourteen arguments:

```text
am instrument -w -r -e case restore_player_presentation
  -e run_id RUN16 -e product_sha256 PRODUCT_SHA256
  org.locallore.app.presentationprocesscontroller/org.locallore.presentationprocessverify.PresentationProcessRestoreInstrumentation
```

`RUN16` is the first sixteen characters of the validated outer hex32 run ID.
The product hash comes from the admission. There is no stdin, retry, alternate
case, method selector or fallback after a spent claim, including in another SDK
session. A structurally valid command for another run or hash still refuses.

The operation allowlist covers boot/API/ABI/emulator properties, current user,
three package filters/paths, three fixed APK transfers/hashes/installs, the one
external command and three fixed probe reads. It does not inherit general
`run-as`, force-stop, pidof, screen, process-memory, model, tar or JUnit authority.
Every transfer must use the corresponding admitted artifact bytes.

## Product build and launcher source are distinct

`presentation_process_build.py` fixes product source
`6302cb45b0a4397ee1313cc7b21e3d8cfe8f8fc8` in the preserved B43 product worktree.
It never retags the old SDK8 build or treats a later launcher head as that
product. Its source-fixed data graph rechecks:

- The clean frozen Git head, exact tracked path roster and all 2,537 raw hashes;
  identical before/after source maps and unchanged shared consumer bytes.
- The public request, actual child/start joins, seven opaque tool/helper pins,
  known finite owner/worker/capture closure, original stdout/stderr sizes and
  successful stop-on-failure public result. Signing values are never read.
- Four exact public command headers, actual critical Gradle tasks, both Rust JNI
  ABI build markers and three successful product/pair/controller audit bodies.
- Forty-eight original JVM XML files, 417 unique passing cases including all six
  new proof methods, zero failures/errors/skips, and the original lint warnings.
- Three original APK hashes/packages and three closed bounded static signer
  records/raw outputs, each one signer with the same certificate.

The guard does not run Java, SDKs, a build, apksigner or the private launcher.
Only bounded read-only Git source queries run. Input files and source head are
checked again before returning. Importing the module performs no I/O.

`create_manifest()` creates only its fixed, create-only host manifest. A caller
cannot select another output, product root, verifier or mode. The manifest has
exactly `version`, `scope`, `product_source`, `public_execution`, `apks`;
scope is `presentation-process-build-v1`. Each APK entry has exactly `binding`,
`package`, `certificate_sha256`. `verify_frozen_product(artifacts)` provides
the artifacts-only pre-prepare guard; `verify_current(admission)` additionally
validates SDK9 admission/source authority. Parent, worker and live-observer
constructors check this graph before native work. A manifest is not launch
permission. Portable synthetic tests patch only source-fixed data to an isolated
coherent file-backed Git fixture, while retaining the real verdict code.

## Ordered acquisition and replay

The controller budget is 1,200 seconds; boot is bounded to120 seconds,
transfers/installs to120, and the sole external command to180 (the APK case has
its own120-second fence). Original stream/proof/socket/resource limits remain.
Successful command count is `Nboot + 38`, where `1 <= Nboot <= 61`:

1. Boot polls ending in1, three properties and current user0.
2. All three packages absent; transfer, hash and install each exact APK.
3. Installed UID, base-APK path and hash for all three roles, with distinct UIDs.
4. The once-only external controller and its bounded quiet result frame.
5. Exactly three original `created`, `saved`, `commands` probe leaves.
6. Repeat all installed UID/path/hash checks; identities and bytes must match.

Probe commands are exact source-built `run-as PRODUCT --user 0 sh -c SCRIPT`
vectors. The fixed script derives its own numeric application UID10000..99999;
each fixed parent is an owned non-symlink directory. The fixed leaf is an owned,
non-symlink regular file with one link and size1..4096 before reading. There is
no caller UID or path selector. The actual raw proof UID must also join the
qualified installed product UID through the V3 parser. Directory link counts
are not required to equal one.

The seventeen-key result preserves request/session/setup, installed-before,
one execution record, three SDK record/raw bindings, parsed evidence,
installed-after, command count, outcome/phase/reason, observer closure,
`feature_acceptance: false`, elapsed time, version and scope. It preserves
partial attempts and closes its own observers/capture on failure.

`verify_controller_result` replays every contiguous SDK client/proof/claim,
consumes exact phase order/labels/argv/stdin/deadlines, rejects extra commands,
and joins the original frame and three raw leaves with the real V3
`validate_result`. Its five expected fields come from admitted run/hash,
installed product/controller UIDs and the common build certificate. No duplicated
or relabelled probe evidence substitutes for raw acquisition. The top-level
output roster is closed, and the parsed sidecar must equal the real verdict.

## Lifecycle and acceptance

Shared SDK4–8 owner/client/contract/verifier bytes are unchanged. A separately
tested retirement whitelist adds only SDK8 and SDK9 identifiers; it retains all
fifteen cleanup predicates, source/proof joins, exact-image authorization,
held-handle checks and finalization. It executes no retirement by itself.

Future preparation/boot/closure must still use the current guarded entry paths
and [shared storage ledger](../runtime/android/RECEIPT_AVD_STORAGE.md): at most
two unretired roots,64GiB admission,40GiB per preparing/live guest. Test success
does not establish owned guest/private-service cleanup; qualified cleanup does
not retire images. Unknown cleanup stays charged. No alternate registry,
fresh-root retry, timeout expansion or weakening of failed tests is permitted.

Actual saved-task/process-death execution, the two component instrumentation
cases, phone/ARM64/model performance, broad accessibility/reliability and full
milestone/release acceptance remain required separately. Previous UI results
and B43 compilation cannot qualify SDK9 runtime execution.
