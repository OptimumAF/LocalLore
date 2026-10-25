# Explicit four-core receipt candidate profile

Refs #9 (M05.05 / M01.04 / M01.05 prerequisite). This is an explicit resource
experiment for a fresh isolated emulator, not a runtime qualification or a
promised speedup. The coordinator's preceding v2 observations placed director
creation at 1867 ms, director send-to-DONE at 42175 ms, and narrator creation
entry at 59580 ms after trace construction, near the unchanged 60-second turn
deadline. A snapshot at 60098 ms observed that creation pending for 518 ms.
Trace and turn timers have different origins; exact remaining turn time is not
established. These historical recording points do not
establish a native hang, cause, missing callback, or performance remedy.

## Closed selection and proposal shape

The environment helper adds exactly this optional argument:

```python
plan_prepare(root, sdk, java_home, output,
             real_candidate=False, four_core_candidate=False)
```

Both selectors require actual booleans. `four_core_candidate=True` requires
`real_candidate=True`. The CLI accepts `--four-core-candidate` only together
with `--real-model-candidate` during `plan-prepare`. Every other phase refuses
the flag before dispatch. There is no arbitrary core-count or profile option,
automatic upgrade, drive fallback, existing-target adoption, or mutation at
module import.

The existing version-1 proposal shape remains unchanged. Its existing `cores`,
`memory_mib`, and `host_available_memory_min` fields admit only these exact
integer triples in both prepare and run phases:

| Profile | Guest RAM (MiB) | Host available RAM minimum | Guest cores |
| --- | ---: | ---: | ---: |
| Existing synthetic default | 2048 | 4 GiB | 2 |
| Existing explicit real candidate | 8192 | 12 GiB | 2 |
| New explicit four-core real candidate | 8192 | 12 GiB | 4 |

Booleans, floats, strings, unknown counts, wrong memory/floor combinations, and
extra profile fields are refused. The default two-core proposal fields and
encoded values are unchanged. A four-core plan is a distinct proposal needing
its own exact prepare and run authorization; prior authorization is not reused.

## Host admission and launch binding

Only the four-core profile calls `os.cpu_count()` and requires an actual integer
at least eight. Unknown/`None`, boolean, fractional, string, negative, and
insufficient counts refuse with fixed `host_cpu_capacity` before SDK dispatch.
Successful four-core resource facts add `logical_cpus`; existing two-core facts
remain exactly `free_bytes` and `available_memory`, without a CPU query. Logical
CPU count is sampled host metadata, not physical-core count, idle capacity,
exclusive scheduling, continuous monitoring, or a speedup guarantee.

Parent prepare checks resources before creating the new root; parent run checks
before consuming its run-start receipt or starting the supervisor. The admitted
four-core worker independently rechecks resources after its proposal,
authorization, and live-parent checks and before its claim and SDK dispatch.
Failure preserves any already created evidence and performs no fallback.

Fresh config normalization writes the bound proposal's core count to
`hw.cpu.ncore`; the emulator command uses the same count for its existing
`-cores` option. Only the new 8192-MiB profile permits four. SDK prepare arguments
otherwise remain unchanged. The prepared immutable config hash detects later
edits, and exact prepare/run common-field comparison refuses core-profile drift
even when the changed tuple is independently a valid two-core profile.

Unchanged values include 12 GiB userdata, 8 GiB SD, fixed image/ABI, two-phase
create-only authorization, fresh explicit C or D root, both drive-specific
capacity floors, 12 GiB host available RAM for real profiles, 1800-second real
owner ceiling, original two-core owner behavior, output capture, process/job
ownership, barriers, closure, and replay guards. No model, schema, SDK dependency,
60-second turn, five-second cleanup, candidate/controller phase budget, storage
admission, or uncertainty fence is changed.

## Verification and remaining runtime gates

Host tests use original tiny fake SDK inputs, mocked memory/disk/CPU facts and
mocked transport. They cover old/default plan equality, new selection and CLI
restrictions, exact typed triples in both phases, matching config/argv, CPU
threshold/unknown/type refusals, unchanged two-core fact shape with no CPU query,
parent prepare/run no-child refusals, worker re-admission before mocked dispatch,
and prepared/core/config drift. No SDK, emulator, device or model is run by these
tests. Actual commands/results and retained attempts belong in the ticket
handoff; authored tests alone are not passing execution evidence.

Downstream read-only inspection found the real-candidate controller already
requires 8192 MiB and the 12 GiB RAM floor without an exact two-core assertion.
It still needs separately owned coordination for actual guest four-CPU
verification and the fresh source/proposal/admission bindings. The helper's host
fact does not establish a guest CPU count, readiness, SDK success, accepted turn,
or reopened canonical state. All runtime acceptance remains pending until a
separately reviewed and admitted actual experiment.
