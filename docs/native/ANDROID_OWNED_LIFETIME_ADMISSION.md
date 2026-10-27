# Admit external checks only while their fixed budget still fits

Supporting M10.02 and M09.06. This host-tool check changes no gameplay,
runtime/model dependency, lease ceiling, SDK deadline or proof format.

The prior retained-parent collection started late in an already-running
20-minute guest lease. Its controller completed, but the fixed owner expired
before the original retirement and canonical sidecars were collected. The
overall result stays failed. A controller pass cannot replace those bytes.

The external session now names its existing SDK session budget as
`SESSION_SECONDS = 1100`. After the existing live-owner, profile and source
checks, and before constructing `SdkCapture` or observing the server, it
requires at least that many seconds before the recorded `deadline_epoch`.
The measured current wall time and deadline must be finite numbers. Equality
is admitted; a smaller remainder refuses with `owned_lifetime`.

This is an admission check at one instant, not a lifetime reservation or a
guarantee about clock drift, later work or product behavior. Existing continuous
ownership/source checks and the separate monotonic SDK budget still apply.
Neither the descriptor nor the owner's deadline is modified. The original
case-independent fixture claim is burned before the session is constructed;
a refused or failed guest must not be adopted or retried.

Prepare and build before launching the guest. Dispatch promptly once the exact
running descriptor is available. A completed current native10 gate remains a
prerequisite, but it can come from its own closed, source-identical guest.
An external case then uses another fresh owned guest with all three packages
absent. Same-installation continuation still needs the full remaining budget;
completion of native10 does not waive it. The fixed 1200-second standard guest
ceiling and 1100-second client-session budget are unchanged.

This rule applies to new dispatch. Historical evidence replay does not construct
a live session and is unchanged. Earlier fully collected root results remain
valid within their original source and runtime scope, even where their initial
remaining lifetime would not satisfy this new admission rule.

Original mocked host tests exercise the real session constructor and prove
late refusal before capture construction, sufficient-lifetime dispatch with
the same budget, boundary/type handling and unchanged claim ordering. Their
execution and actual SDK2 lifecycle results belong in the dated verification
report; authored tests or a source review alone establish no Android result.
