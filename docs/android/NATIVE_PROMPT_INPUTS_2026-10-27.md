# Android native prompt inputs

M03.05, in review under #7. Owner acceptance remains pending.

## Change

`buildRustAndroid` declared Cargo, Rust sources, fixtures and its build scripts
as inputs, but omitted the `prompts` directory. The Rust authoring request
embeds `prompts/initial-world-v1.txt` and
`prompts/initial-world-v1.schema.json`. A change to those files therefore needs
to participate in Gradle's native-task invalidation.

Commit `0f20ea32b1e3cfd9a5663f48019e99be18aa136d` adds one input declaration:

```kotlin
inputs.files(fileTree(nativeRepository.resolve("prompts")))
```

The accompanying `benchmarks/android_native_input_probe.gradle` inspects the
configured `:app:buildRustAndroid` task through Gradle's task-input API. Its
separate inspection task has no dependency on the native build. It emits one
closed JSON marker containing the task, required relative paths, input-file
count and missing paths, then fails if either required authoring file is absent.
The exact probe is 1,460 bytes, SHA256
`f83543d7fac9ae2ee47d73f6e30255270327b1382aa10546911b445a4eff16fa`.

## Executed configured-model proof

The same probe bytes ran against unchanged commit
`4068e5a6ef8c88caa7f97c049f1bd6b683952d9c` and fixed commit
`0f20ea32b1e3cfd9a5663f48019e99be18aa136d`. Each run had a bounded 180-second
owner, captured command output, and full tracked-source and HEAD checks before
and after. All three owners closed with complete cleanup and output capture.

| Attempt | Result | Gradle exit | Owner exit | Configured inputs | Owner elapsed |
| --- | --- | ---: | ---: | --- | ---: |
| Initial RED v1 | Configuration refused before inspection; proof failed | 1 | 1 | No marker | 19,379 ms |
| RED v2, unchanged source | Expected missing-input result | 1 | 0 | 337 files; both required prompts missing | 17,271 ms |
| GREEN v2, fixed source | Both required prompts present | 0 | 0 | 339 files; no missing prompts | 38,162 ms |

The initial attempt selected the input-process verification profile while using
an external project cache. That profile correctly requires its exclusive
`.gradle-input-process` cache, so configuration refused before the probe could
run. Its failed result and raw output remain preserved. V2 uses ordinary default
configuration with no verification-profile flags and separate external caches.

RED v2 and GREEN v2 have zero owner stderr, unchanged full source maps of 2,001
and 2,002 tracked files respectively, and exactly one valid marker each. RED's
nonzero Gradle exit is accepted only together with the exact two missing paths;
a configuration refusal or absent marker does not satisfy the proof.

An independent file-only readback verified 78 binding occurrences across the
three closed attempts, all 15 captured command records, both markers, source-map
equality and recorded owner output sizes, with zero mismatches. These elapsed
times describe owned verification runs, not build or inference performance.

## Reproduction

Use Java 21 and the repository's cached dependencies. From `apps/android`, set
`REPO` to the checkout, `PROBE` to the exact external probe, and `CACHE` to a new
external cache directory for that attempt:

```text
java -classpath REPO/apps/android/gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain --offline --no-daemon --max-workers=2 --console=plain --project-cache-dir CACHE --init-script PROBE -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Pandroid.builder.sdkDownload=false :app:inspectLocalLoreNativePromptInputs
```

The executed runner used the Java 21 executable directly, scrubbed inherited
Java/Gradle option variables, and selected no verification profile. Its external
cache directories were distinct for RED v2 and GREEN v2. The fixed task and
command request no native build, device operation, model inference or download.

## Scope and remaining limits

This establishes a configured task-input gap and verifies its declaration fix.
It does not demonstrate a stale APK or execute a prompt-change incremental
rebuild. Separate current-879 cold-build verification found the corrected
authoring schema embedded in both x86_64 and arm64-v8a libraries in both APK
profiles. This input declaration protects future prompt-change invalidation;
the configured-model proof makes no additional APK or device qualification
claim. Private raw records remain outside public Git. No dependency, system
setting, device lifecycle, merge or release changes are part of this packet.
