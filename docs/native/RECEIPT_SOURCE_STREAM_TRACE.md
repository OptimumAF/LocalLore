# Receipt source stream failure observations

The fixed receipt stream worker may emit one optional failure-only line with
prefix `LOCALLORE_RECEIPT_SOURCE_STREAM_V1=` and a closed ASCII JSON object. The
complete line is bounded to 1024 bytes, excluding its newline. Successful output
retains the original six-key JSON object and has no added line. The CLI's generic
exception outcome is unchanged. Observer or output failures cannot replace the
original exception or return status.

The ten fields are `version` (1), `phase`, `expected_bytes`, `source_verified`,
`client_timeout_ms`, `client_returncode`, `client_timed_out`, `source_position`,
`elapsed_ms`, and `time_saturated`. There are no paths, identifiers, command text,
model bytes, exception text, or guest observations. The strict parser rejects
unknown/duplicate fields, invalid types, impossible correlations and oversized
records. The extractor accepts at most one exact prefixed line in a 4096-byte
ASCII capture. It does not classify the legacy outcome.

`phase` is the last entered phase: GATE, SOURCE_OPEN, SOURCE_HASH, CLIENT,
SOURCE_POSTCHECK, LEASE_POSTCHECK, or COMPLETE. Entering a phase does not prove
its completion. `source_verified` records the existing full pre-transfer held-FD
hash and size check; it does not assert that later identity checks passed.
`client_timeout_ms` is the existing client budget rounded up to milliseconds,
at most 150000; zero means the client was not started. Return code and timeout
are mutually exclusive and neither is a guest exit status. A timeout is recorded
only for `subprocess.TimeoutExpired` from the client call.

The optional `source_position` is the host's held-file cursor sampled after the
client returns or raises that timeout. Even a cursor equal to the source length
does not establish bytes received, guest write completion, destination hash,
import, SDK drain, or restart safety. No cursor is sampled by reopening a file.
Monotonic elapsed time saturates at 180000 ms with a sticky saturation flag.

All admission, source integrity, parent identity, one-shot claim, live lease,
capacity, Job ownership and postchecks remain authoritative. The client retains
`timeout = min(150 seconds, parent remaining time - 5 seconds)`.
This trace adds no retry, deadline extension, target adoption, or new
device operation. An uncertain transfer still stops the experiment and requires
the exact host owner to close; a later attempt uses a fresh target and grants.
