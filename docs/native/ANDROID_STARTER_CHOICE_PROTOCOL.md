# Fixed original starter chooser checks — v1

Supporting M09.02/M09.06. This phase exercises the new chooser independently
of the original creation19, broad89, native10 and external restart controls.
The [catalog contract](STORY_STARTER_CATALOG_V1.md) owns the interface.

The versioned entry point is:

```powershell
python -I -B benchmarks/android_process_verification.py starter-choice --out "$evidence/starter-choice-v1" --sdk "$sdk" --powershell "$powershell" --build "$evidence/build-v1/result-v1.json" --proposal "$runProposal" --running "$runningReceipt" --server "$serverPin"
```

Use the existing source-bound offline build and fresh owned standard emulator
admission protocols. All three packages must be absent. The existing server
must have a current pin; old process identities and an interrupted preparation
are not admission. This command neither starts a server nor adopts another
application's fixture. There is no arbitrary class or method selector.

The fixed roster contains three methods from `StoryTemplateChoiceWireTest`,
three from `StoryTemplateChoiceDialogTest`, and one from
`StoryTemplateChoiceMainActivityTest`. The driver derives the exact method names
from its frozen constants and checks the actual source roster before SDK use.
Wire tests cover catalog/preview bounds and coherence. Compose tests cover
selection, retained callbacks and invalidated consent. The MainActivity case
uses real UI/JNI creation, Cancel, two distinct profiles and ordinary Activity
close/reopen. It is not an OS-death, real-model or joined native-drain proof.

Each class dispatch remains bounded to180 seconds and262144 output bytes; the
session is850 seconds and outer owner900. Existing guest limits are unchanged.
Both worker and parent validate original runner frames, exact seven-method
completion, source/build/APK/owned-lease bindings and the full contiguous
measured-SDK2 JSON/stdout pairs. Skips, extra/missing methods, foreign classes,
partial output, unknown cleanup and historical timingless current records refuse.
The phase passes only after parent qualification of both `starter_choice-v1.json`
and the terminal owner/result records; a worker record alone is insufficient.

Compilation and source-only host adversaries do not execute these Android
methods. See the [dated report](ANDROID_STARTER_CHOICE_2026-10-26.md) for actual
status; earlier source/APK results retain their own attribution.
