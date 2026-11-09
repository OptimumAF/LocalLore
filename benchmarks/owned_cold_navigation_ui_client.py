"""Owned v4 observation and capture for the fixed cold-navigation profile.

The observer can attach only to an already owned target. This module has
no launcher or entry point for preparing or starting a target.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_verification_v4 as verification
from benchmarks import owned_cold_navigation_ui_contract as contract
from benchmarks import owned_target_owner as mechanisms

_REPLAY = verification._Verifier(contract)
_LABEL = "cold_navigation"


def replay_client_record(binding, session, admission, *, expected_stdout=None):
    """Require the v4 client, socket and claim proofs before interpreting JUnit."""
    row = _REPLAY.verify_client_record(binding, session, admission)
    contract._need(row["label"] == _LABEL, "command")
    stdout = _REPLAY._raw(row["stdout"], cap=evidence.MAX_BYTES)
    stderr = _REPLAY._raw(row["stderr"], cap=evidence.MAX_BYTES)
    if expected_stdout is not None:
        contract._need(contract._same(stdout, expected_stdout), "binding")
    return contract.replay_instrumentation(
        row["operation"], admission, row["returncode"], stdout, stderr,
    )


class LiveOwnedColdNavigationUiTarget(mechanisms._LiveOwnedTarget):
    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedColdNavigationUiTarget, "owner_type")
        admission_binding = copy.deepcopy(admission_binding)
        running_binding = copy.deepcopy(running_binding)
        admission = contract.validate_admission(mechanisms._read_json(admission_binding, _contract=contract))
        contract.verify_artifacts(admission["artifacts"])
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        return contract

    @property
    def _verification(self):
        return _REPLAY


class OwnedColdNavigationUiSdkCapture(wire._OwnedTargetSdkCapture):
    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedColdNavigationUiSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        return contract

    @property
    def _verification(self):
        return _REPLAY

    @property
    def _expected_lease_class(self):
        return LiveOwnedColdNavigationUiTarget

    def run_cold_navigation(self):
        wire._need(type(self) is OwnedColdNavigationUiSdkCapture, "client_type")
        try:
            stdout = self.shell(contract.instrumentation_argv(), _LABEL, seconds=120,
                                cap=evidence.MAX_BYTES, full_budget=True)
            binding = _REPLAY._pin(self.directory / f"command-{self.count:04d}.json")
            result = replay_client_record(binding, self.session, self._admission, expected_stdout=stdout)
            return {"client": binding, "instrumentation": result}
        except Exception:
            self._poison()
            raise wire.ClientRefused("cold_navigation") from None
