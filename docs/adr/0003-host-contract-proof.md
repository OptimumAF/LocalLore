# ADR-0003 — A bounded host proof before native integration

Status: proposed for owner review, implemented on the first implementation branch.
Date: 2026-10-22. Tasks: M02.01–M02.06, M03.01, M03.04; supports M01 preparation.

## Observation and decision

The clean e3551b2 repository contained only specifications. Rust 1.93.1 is
available; read-only discovery found two authorized Android emulators and no
physical phone. Native runtime/model load, mobile/FFI and device results cannot
be inferred from this environment. The first-session assignment explicitly
authorizes executable contracts and a small host fake-provider harness.

Use one Rust crate for the real typed boundaries and pure in-memory engine,
with strict versioned proposals and engine-created accepted receipts. Split
state from inference inside the crate rather than introduce unused crates,
SQLite migrations, JNI or a production runtime before their prerequisites.
Pin serialization dependencies and compiler; run the host without weights or
network calls. Separate runtime research supplies exact official source pins
without choosing a backend.

The host requires explicit clarified actions and exact safe narration. This
keeps the authority boundary executable without pretending to solve arbitrary
semantic validation. Current truth is immutable trusted seed; beliefs/statements
are separate. Branch proofs use validated in-memory completed-turn prefixes.
Replay verifies stored v1 outcomes against deterministic resolution, without
generation; durable outcome reducers and migrations remain M04.

## Alternatives and consequences

Documentation-only contracts would not expose atomicity, boundary or knowledge
mistakes. A large mobile shell or immediate runtime binding would add unmeasured
dependencies before stable interfaces. Independent implementations of shared
types would risk incompatible meanings of truth, scope and agency.

This decision changes execution order inside the authorized packet, not product,
privacy, license, governance or release scope. Preserve all existing task IDs.
M03.01/M03.04 can be reviewed locally while M03's Android/FFI/CI exit gate stays
open. M01 physical gates stay blocked. Future free-text interpretation, narrator
quality, storage faults and full branch replay/import need their own evidence.

## Validation

`docs/IMPLEMENTATION_EVIDENCE.md` records actual commands and independent review.
The v1 contract lists invariant fixtures and explicit limitations. No release,
merge, repository access or Actions-setting change follows from this ADR.
