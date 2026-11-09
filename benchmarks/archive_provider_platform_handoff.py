"""Bind the SDK26 activation grant, one-use claim and owner handoff.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
import time

from benchmarks import archive_provider_platform_admission as candidate
from benchmarks import archive_provider_platform_preparation as prep
from benchmarks import owned_archive_provider_platform as owned
from benchmarks import receipt_avd_environment as env

AUTHORITY = candidate.OUT / "activation-authority-v1.json"
ATTEMPT = candidate.OUT / "activation-claim-v1.json"
AUTHORITY_SCOPE = "sdk26-activate-prepared-archive-provider-platform-v1"
HANDOFF_SCOPE = "sdk26-archive-provider-platform-boot-handoff-v1"
NS = 1_000_000_000
LAUNCH_TAIL_SECONDS = 1220


def read_approval(authority_pin, candidate_pin):
    """Read one explicit activation-only approval for these exact reviewed bytes."""
    approved = env.decode_json(prep._bound(authority_pin, AUTHORITY, 16_384))
    owned._obj(approved, ("version", "scope", "candidate", "proposal", "admission", "ledger",
                          "approval_reference", "allow_sdk_prepare", "allow_one_boot",
                          "allow_model", "allow_retirement"), "authority")
    reference = approved["approval_reference"]
    env.require(owned._same(approved["version"], 1) and approved["scope"] == AUTHORITY_SCOPE
                and owned._same(approved["candidate"], candidate_pin)
                and type(reference) is str and 0 < len(reference) <= 256 and reference == reference.strip()
                and all(32 <= ord(char) <= 126 for char in reference)
                and approved["allow_sdk_prepare"] is False and approved["allow_one_boot"] is True
                and approved["allow_model"] is False and approved["allow_retirement"] is False, "authority")
    ledger_pin = approved["ledger"]
    owned.binding(ledger_pin, max_bytes=16 * 1024**2)
    env.require(ledger_pin["path"] == str(prep.LEDGER), "ledger")
    reviewed = candidate._read_candidate(candidate_pin, ledger_pin)
    env.require(owned._same(reviewed["admission"], approved["admission"])
                and owned._same(reviewed["proposal"], approved["proposal"]), "authority")
    env.require(prep._bound(approved["proposal"], candidate.PROPOSAL, 65_536)
                == candidate._review_bytes(approved["admission"], ledger_pin), "authority")
    return approved


def claim_value(authority_pin, candidate_pin):
    return dict(version=1, scope=AUTHORITY_SCOPE, authority=authority_pin,
                candidate=candidate_pin, no_retry=True)


def _claim_matches(attempt_pin, authority_pin, candidate_pin):
    claim = env.decode_json(prep._bound(attempt_pin, ATTEMPT, 16_384))
    env.require(owned._same(claim, claim_value(authority_pin, candidate_pin)), "attempt")


def materialize_run_authorization(authority_pin, candidate_pin, attempt_pin):
    """Publish only the already bound authorization for a spent activation claim."""
    approved = read_approval(authority_pin, candidate_pin)
    _claim_matches(attempt_pin, authority_pin, candidate_pin)
    admission = candidate.verify_candidate(candidate_pin, approved["ledger"])
    guest = admission["guest"]
    auth = candidate._authorization(guest["proposal"])
    expected = candidate._pin_for_bytes(candidate.RUN_AUTHORITY, env.encoded(auth))
    env.require(owned._same(guest["authorization"], expected), "authorization")
    pins = (authority_pin, candidate_pin, attempt_pin, approved["ledger"], approved["proposal"],
            approved["admission"], guest["proposal"])
    for pin in pins:
        env.check_binding(pin)
    result = prep._save(candidate.RUN_AUTHORITY, auth)
    env.require(owned._same(result, expected), "authorization")
    owned.revalidate_inputs(admission)
    for pin in (*pins, result):
        env.check_binding(pin)
    return result


def check_window(began_ns, until_ns, *, minimum_seconds=0):
    now = time.monotonic_ns()
    env.require(type(began_ns) is int and type(until_ns) is int
                and 0 < began_ns <= now < until_ns <= began_ns + env.REAL_MAX_SECONDS * NS
                and until_ns - now > minimum_seconds * NS, "deadline")


def verify_boot(admission_pin, admission, handoff_pin):
    """Replay the handoff files before a live supervisor/ancestry check."""
    admission = owned.validate_admission(admission)
    handoff = env.decode_json(prep._bound(handoff_pin, candidate.HANDOFF))
    owned._obj(handoff, ("version", "scope", "authority", "attempt", "candidate", "admission",
                         "supervisor", "began_ns", "until_ns"), "handoff")
    env.require(owned._same(handoff["version"], 1) and handoff["scope"] == HANDOFF_SCOPE
                and owned._same(handoff["admission"], admission_pin), "handoff")
    owned._process(handoff["supervisor"])
    env.require(handoff["supervisor"]["executable"] == admission["python"]["executable"]["path"], "identity")
    window = (handoff["began_ns"], handoff["until_ns"])
    check_window(*window, minimum_seconds=LAUNCH_TAIL_SECONDS)

    authority_pin, attempt_pin, candidate_pin = (handoff["authority"], handoff["attempt"], handoff["candidate"])
    approved = read_approval(authority_pin, candidate_pin)
    _claim_matches(attempt_pin, authority_pin, candidate_pin)
    env.require(owned._same(approved["admission"], admission_pin)
                and owned._same(admission, candidate._verify_candidate(candidate_pin, approved["ledger"])),
                "admission")
    guest = admission["guest"]
    auth = env.decode_json(prep._bound(guest["authorization"], candidate.RUN_AUTHORITY, 4096))
    env.check_authorization(auth, "run", guest["proposal"]["sha256"], run_scope=owned.PROTOCOL)
    owned.revalidate_inputs(admission)

    review = candidate._read_candidate(candidate_pin, approved["ledger"])
    run = env.decode_json(prep._bound(guest["proposal"], candidate.RUN))
    proof = env.decode_json(prep._bound(review["preparation"], prep.RESULT))
    launch_inputs = (
        candidate_pin, approved["proposal"], review["plan"], review["preparation"],
        guest["proposal"], guest["authorization"], run["prepare_proposal"], run["prepared"],
        run["prepare_result"], proof["authority"], proof["claim"], proof["authorization"],
        *proof["evidence"].values(),
    )
    for pin in (handoff_pin, authority_pin, attempt_pin, admission_pin, approved["ledger"], *launch_inputs):
        env.check_binding(pin)
    boot_claim = env.safe_path(prep.GUEST / owned.BOOT_CLAIM_FILE, exists=False)
    env.require(not os.path.lexists(boot_claim), "already_used")
    check_window(*window, minimum_seconds=LAUNCH_TAIL_SECONDS)
    return handoff, approved, launch_inputs
