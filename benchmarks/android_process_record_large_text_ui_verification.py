"""Replay only the Story Record large-text profile's existing v4 proof format.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import android_process_verification_v4 as shared
from benchmarks import owned_record_large_text_ui_contract as contract

_REPLAY = shared._Verifier(contract)

verify_proof = _REPLAY.verify_proof
verify_client_record = _REPLAY.verify_client_record
require_current_clients = _REPLAY.require_current_clients
verify_guest_inputs = _REPLAY.verify_guest_inputs
verify_owned_target_result = _REPLAY.verify_owned_target_result
