"""Read and replay story-deletion records through the existing owned verifier.

The caller supplies its source-admitted contract and independently observed
caller binding. This module has no live entry point or cleanup authority.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import re

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import android_process_verification_v4 as shared
from benchmarks import cross_owner_deletion_ui_binding as binding
from benchmarks import cross_owner_deletion_ui_replay as journey
from benchmarks import owned_target_contract as core

SESSION_SECONDS = 1200
_KIND = binding.INSTRUMENTATIONS[0][0]
_INSTALLED = ("package", "package-path", "package-hash") * 2
_LABELS = (
    "boot", "property", "property", "property", "user",
    "package-absent", "package-absent",
    "apk-stage", "staged-hash", "install", "apk-stage", "staged-hash", "install",
    *_INSTALLED, _KIND, *_INSTALLED,
)
_DEADLINES_MS = {"apk-stage": 120_000, "install": 120_000, _KIND: 90_000}


def _profile(contract):
    expected = {
        "APP": binding.APP, "TEST": binding.TEST, "MODEL_MATERIAL": False,
        "INSTRUMENTATIONS": binding.INSTRUMENTATIONS, "CLAIM_KINDS": (_KIND,),
        "ARTIFACT_KEYS": frozenset(binding.artifact_bindings()),
    }
    for field, wanted in expected.items():
        core._need(core._same(getattr(contract, field, None), wanted), "capability")
    filename = getattr(contract, "SESSION_FILE", None)
    core._need(type(filename) is str and re.fullmatch(r"sdk-session-v[1-9][0-9]{0,3}\.json", filename)
               is not None, "binding")
    return filename


def read_command(reader, row, index, label):
    """Read one qualified command with the fixed ordinal, deadline and byte limits."""
    core._int(index, 1, journey.COMMAND_COUNT, "binding")
    core._int(row["index"], index, index, "binding")
    core._int(row["effective_deadline_ms"], 1, _DEADLINES_MS.get(label, 15_000), "budget")
    core._need(label == _LABELS[index - 1] and row["label"] == label
               and row["client_qualified"] is True and row["status"] == "completed"
               and core._same(row["returncode"], 0), "observation")
    limit = evidence.MAX_BYTES if label == _KIND else journey._MAX_REPLY
    return {
        "argv": row["operation"]["argv"], "stdin": row["operation"]["stdin"],
        "stdout": reader._raw(row["stdout"], cap=limit), "stderr": reader._raw(row["stderr"], cap=limit),
        "returncode": row["returncode"],
    }


def verify_capture(contract, admission_binding, running_binding, session_binding, expected_caller):
    """Qualify recorded commands and check their exact sequence without running them."""
    try:
        filename = _profile(contract)
        reader = shared._Verifier(contract)
        admission = contract.validate_admission(reader._json(admission_binding))
        root = Path(admission["root"])
        output = root / "controller-v1"
        running = contract.validate_running(reader._at(running_binding, root / "running-v1.json"),
                                            admission, admission_binding)
        session = contract.validate_session(reader._at(session_binding, output / filename), admission)
        for field, wanted in (("admission", admission_binding), ("running", running_binding),
                              ("caller", expected_caller), ("descriptor", running),
                              ("seconds", SESSION_SECONDS)):
            core._need(core._same(session[field], wanted), "binding")

        contract.revalidate_inputs(admission)
        pins = admission["artifacts"]
        binding.verify_artifacts(pins)
        rows = reader.require_current_clients(output, journey.COMMAND_COUNT, session_binding, admission)
        core._need(type(rows) is list and len(rows) == journey.COMMAND_COUNT == len(_LABELS), "binding")

        tape = [read_command(reader, row, index, label)
                for index, (row, label) in enumerate(zip(rows, _LABELS), 1)]
        return journey.replay(tape, pins)
    except core.TargetRefused:
        raise
    except (OSError, KeyError, TypeError, ValueError, RuntimeError):
        raise core.TargetRefused("binding") from None
