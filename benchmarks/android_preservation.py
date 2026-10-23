"""Bounded preservation observations; no transport, inference or canonical authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy

CHECKS = ("model_metadata", "cache_metadata", "prior_canonical", "guarded_canonical",
          "traced_canonical", "phase_journal", "storage", "inventory")
OBSERVATIONS = {"matched", "mismatched", "unavailable"}


def collect(checks, verify_boundary, clients_known, retain):
    """Run fixed independent read-only checks through trusted bounded adapters.

    verify_boundary freshly checks selected APK/UID/root and process absence.
    clients_known is a pure, non-dispatching ownership predicate. Each check
    must retain raw bytes before interpretation and verify any additional owner
    it reads. retain durably writes only its bounded host checkpoint, without
    hidden device operations. The caller owns deadlines and adapter admission.
    A mismatch never becomes a pass; uncertain safety stops all later checks.
    """
    report = {"version": 1, "scope": "android_preservation_collection", "status": "input_refused",
              "checks": [{"check": name, "status": "not_run", "boundary_verified": False} for name in CHECKS],
              "clients_cleaned": False, "boundary_verified": False, "retention_complete": False,
              "collection_complete": False, "preservation_verified": False, "stop_reason": "input"}
    if (type(checks) is not dict or set(checks) != set(CHECKS)
            or not all(callable(checks[name]) for name in CHECKS)
            or not all(callable(callback) for callback in (verify_boundary, clients_known, retain))):
        return report
    # Bind all validated callbacks before a sink/check can mutate the caller's dict.
    callbacks = tuple(checks[name] for name in CHECKS)
    report.update(status="collecting", stop_reason="none")
    ownership = True

    def known():
        nonlocal ownership
        if ownership:
            try:
                ownership = clients_known() is True
            except Exception:
                ownership = False
        report["clients_cleaned"] = ownership
        if not ownership:
            report["boundary_verified"] = False
        return ownership

    def halt(reason):
        report.update(status="stopped", boundary_verified=False, preservation_verified=False)
        if report["stop_reason"] == "none":
            report["stop_reason"] = reason

    def checkpoint():
        was_known = known()
        if not was_known:
            halt("ownership_unknown")
        # Even stopped observations may be written to an owned host-only sink.
        # No checkpoint can publish a provisional preservation success.
        try:
            retain(copy.deepcopy(report))
        except Exception:
            report["retention_complete"] = False
            halt("retention_failed")
            known()
            return False
        report["retention_complete"] = True
        if not known() and was_known:
            # The changed fenced state was not retained; never retry that sink.
            report["retention_complete"] = False
            halt("ownership_unknown")
            return False
        return True

    def boundary():
        if not known():
            halt("ownership_unknown")
            return False
        try:
            verified = verify_boundary() is True
        except Exception:
            verified = False
        if not known():
            halt("ownership_unknown")
            return False
        if not verified:
            halt("boundary_failed")
            return False
        report["boundary_verified"] = True
        return True

    if not checkpoint() or report["status"] == "stopped":
        return report
    for row, callback in zip(report["checks"], callbacks):
        if not boundary():
            checkpoint()
            return report
        try:
            observation = callback()
        except Exception:
            row["status"] = "error"
            halt("check_failed" if known() else "ownership_unknown")
            checkpoint()
            return report
        valid = type(observation) is str and observation in OBSERVATIONS
        row["status"] = observation if valid else "error"
        if not known():
            halt("ownership_unknown")
            checkpoint()
            return report
        if not valid:
            halt("invalid_check")
            checkpoint()
            return report
        if not boundary():
            checkpoint()
            return report
        row["boundary_verified"] = True
        if row["check"] == CHECKS[-1]:
            report.update(status="observed", collection_complete=True)
        if not checkpoint():
            return report
    report["preservation_verified"] = (report["collection_complete"] and report["clients_cleaned"]
        and report["boundary_verified"] and report["retention_complete"]
        and all(row["status"] == "matched" and row["boundary_verified"] for row in report["checks"]))
    return report
