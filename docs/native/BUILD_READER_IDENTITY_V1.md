# Guarded build identity and final planning observations

M10.02 `RECORD_CANCELLATION_UI_OPERATION_READINESS` prerequisites, supporting
M09.04/M09.06. Implemented for review; no milestone acceptance or run authority.

The fixed SDK18 input refresh exposed two independent guard defects. This packet
fixes those defects in source. It leaves the old frozen profile and planning
records intact. Incorporating the fixes into a source-coherent profile remains
necessary before a new fixed inspection or exact operation proposal can qualify.

## File identity differs from directory metadata

`benchmarks/diagnostic_ui_build.py` supplies the reader also used by the record
cancellation build attestor. It previously compared the same six fields for a
declared file and all ancestor directories: device, inode, mode, size, modified
time and link count. An actual inspection refused when a report directory's
observed size changed from 0 to 20,480, with the other five fields equal.

Python defines `st_size` as byte size for regular files and symbolic links;
it does not define directory byte size as directory-content identity.
[Official Python documentation](https://docs.python.org/3.14/library/os.html#os.stat_result).
This observation does not establish an OS-level cause or prove the absence of
all concurrent activity.

The new stamp excludes size only when the observed object is a directory.
Device, inode, full mode/type, modified time and link count remain compared.
Symlink and reparse rejection still occurs before the stamp is returned.
Regular-file size remains exact. Bound-file path/open/identity/content checks,
cache conservation, final real byte rehashes and all budgets are unchanged.
No configurable bypass, alternate reader factory or new public API is added.
A directory replaced by a file still changes type and fails conservation.

## Late inspection changes must refuse

`scripts/record_cancellation_ui_prepare_inputs.py` already compared ledger and
capacity before its final source observations. An original toy-ledger test shows
that the final activation observation could change the ledger afterward and
still allow a final inspection result.

The inspector now compares the ledger and capacity again after those observations
and before publishing the frozen handoff. A changed ledger short-circuits before
the next capacity observation. It retains partial files as evidence and raises
the existing finite refusal. No failure cleanup or success repair is added.

These are unlocked point-in-time observations. They do not hold writers, promise
future freshness, reserve capacity or replace the later locked admission and
operation checks. Inspection data never grants human authority.

## Frozen generations and next integration

The attempted refresh relocated the inspector to a new private generation for
actual file-only inspection. Both attempts refused at the old frozen build reader
before planning output. Their exact source, workers and errors are retained.
The final source restores the original B113 output-generation constant and adds
only the late-observation guard. Both contracts and both operation bodies are
unchanged. Four proposed generation tests remain private and unrun; they are not
published as passing tests or wired to invented fresh pins.

The corrected current-source public build verifier does verify the original
saved manifest and APK pair without changing them. This is separate from the
old immutable SDK18 profile, which still loads its old reader. Do not patch that
frozen source, inject the new reader into its namespace, retag its old handoff,
or infer approval from a capacity preview.

Next runnable M10.02 host task: publish/freeze a coherent profile containing the
corrected reader, then regenerate current-ledger inputs and review the exact
outer-operation proposal. Preparation and boot still require fresh locked
admission and separate explicit approval. No new runtime/model/SDK dependency,
product, Kotlin/Rust authority or gameplay behavior changes here.
