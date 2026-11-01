"""Fixed archive UI closed replay over shared byte-bound verification.

No SDK5 restart schema, native observation or target operation is selected.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_verification_v4 as shared
from benchmarks import owned_ui_contract as contract

_REPLAY = shared._Verifier(contract)


def verify_proof(pin, session, context):
    return _REPLAY.verify_proof(pin, session, context)


def verify_client_record(binding, session, admission):
    return _REPLAY.verify_client_record(binding, session, admission)


def require_current_clients(root, count, session_binding, admission):
    return _REPLAY.require_current_clients(root, count, session_binding, admission)


def verify_guest_inputs(pin, admission, admission_binding):
    return _REPLAY.verify_guest_inputs(pin, admission, admission_binding)


def verify_owned_target_result(binding, admission, admission_binding,
                               request_binding, expected_worker):
    return _REPLAY.verify_owned_target_result(
        binding, admission, admission_binding, request_binding, expected_worker)
