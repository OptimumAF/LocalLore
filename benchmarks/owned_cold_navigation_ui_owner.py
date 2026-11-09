"""Fixed guarded owner for one cold-navigation UI attempt.

The entry point consumes an approved handoff and an already prepared guest.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import archive_ui_build as files
from benchmarks import cold_navigation_ui_controller as controller
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_cold_navigation_ui_client as client
from benchmarks import owned_cold_navigation_ui_contract as contract
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

OUT = Path("D:/Dev/Experiments/LocalLore/2026-11-09-cold-navigation-operation-v1")
PLAN = OUT / "plan-v1.json"
PROPOSAL = OUT / "PROPOSED_OPERATION.md"
AUTHORITY = OUT / "human-authority-v1.json"
PREPARE = OUT / "prepare-proposal-v1.json"
ATTEMPT_ROOT = OUT / "attempt-v1"
ATTEMPT = ATTEMPT_ROOT / "claim-v1.json"
HANDOFF = ATTEMPT_ROOT / "boot-handoff-v2.json"
ADMISSION = ATTEMPT_ROOT / "admission-v1.json"
RUN = ATTEMPT_ROOT / "run-proposal-v1.json"
RUN_AUTHORITY = ATTEMPT_ROOT / "run-authorization-v1.json"
OWNED_ROOT = ATTEMPT_ROOT / "owned-v1"
LEDGER = storage.DEFAULT_REGISTRY / "ledger-v1.json"
GUEST = Path(contract.GUEST_ROOT)
OPERATION_SCOPE = "sdk20-prepare-and-one-cold-navigation-run-v1"
PLAN_SCOPE = "sdk20-cold-navigation-plan-v1"
HANDOFF_SCOPE = "cold-navigation-boot-handoff-v2"
HANDOFF_ENV = "LOCALLORE_COLD_NAVIGATION_HANDOFF_SHA256"
NS = 1_000_000_000
SECONDS = 2400
ACTIVATION_SECONDS = 1800
TAIL_SECONDS = 20
OWNER_SECONDS = 1700
_RECORD_CAP = 2 * 1024**2
_STORAGE_CAP = 16 * 1024**2
_need = env.require
_same = contract._same


def _pin(pin, path, cap):
    contract.binding(pin, max_bytes=cap)
    _need(pin["path"] == str(path) and pin["bytes"] > 0, "binding")


def _read(path, cap=_RECORD_CAP):
    raw = files._read(path, cap)
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()), env.decode_json(raw)


def _at(pin, path, cap=_RECORD_CAP):
    _pin(pin, path, cap)
    return env.decode_json(files._bound(pin, cap=cap))


def _ledger(root):
    pin, value = _read(LEDGER, _STORAGE_CAP)
    storage._validate(value, storage.DEFAULT_REGISTRY)
    _need(type(value["version"]) is int and value["version"] == 2, "ledger")
    entry = storage._entry(value, root)
    env.check_binding(pin)
    return pin, entry


def _read_approval(authority_pin):
    authority = _at(authority_pin, AUTHORITY, cap=16384)
    contract._obj(authority, ("version", "scope", "proposal", "plan", "ledger", "approval_reference",
                              "allow_sdk_prepare", "allow_one_boot", "allow_model", "allow_retirement",
                              "max_operation_seconds"), "authority")
    ref = authority["approval_reference"]
    _need(_same(authority["version"], 1) and authority["scope"] == OPERATION_SCOPE
          and type(ref) is str and 0 < len(ref) <= 256 and ref == ref.strip()
          and all(32 <= ord(char) <= 126 for char in ref)
          and authority["allow_sdk_prepare"] is True and authority["allow_one_boot"] is True
          and authority["allow_model"] is False and authority["allow_retirement"] is False
          and _same(authority["max_operation_seconds"], SECONDS), "authority")
    _pin(authority["proposal"], PROPOSAL, 65536)
    _pin(authority["ledger"], LEDGER, _STORAGE_CAP)
    lines = files._bound(authority["proposal"], cap=65536).decode("utf-8").splitlines()
    for label, role in (("Plan SHA-256", "plan"), ("Ledger SHA-256", "ledger")):
        _need([line for line in lines if line.startswith(label)] ==
              [label + " " + authority[role]["sha256"]], "authority")
    plan = _at(authority["plan"], PLAN, cap=131072)
    env.check_binding(authority_pin)
    return authority, plan


def _attempt_record(authority_pin):
    return dict(version=1, scope=OPERATION_SCOPE, authority=authority_pin, no_retry=True)


def _approved_plan(authority_pin, attempt_pin):
    authority, plan = _read_approval(authority_pin)
    _need(_same(_at(attempt_pin, ATTEMPT, cap=16384), _attempt_record(authority_pin)), "attempt")
    return authority, plan


def _prepare_plan(plan):
    contract._obj(plan, ("version", "scope", "source_root", "sources", "python", "artifacts", "prepare",
                         "installed", "execution_authorized", "model_material"), "plan")
    _need(_same(plan["version"], 1) and plan["scope"] == PLAN_SCOPE and plan["source_root"] == str(ROOT)
          and plan["execution_authorized"] is False and plan["model_material"] is False, "plan")
    installed = plan["installed"]
    contract._obj(installed, ("adb", "tools", "emulator", "qemu", "refuser", "refuser_source",
                              "auth_key_path", "capabilities", "source_review", "compatibility"), "installed")
    prepare = _at(plan["prepare"], PREPARE, cap=_STORAGE_CAP)
    env.validate_proposal(prepare, "prepare")
    _need(prepare["paths"]["root"] == str(GUEST) and prepare["adb_path"] == installed["adb"]["path"]
          and _same(prepare["memory_mib"], 8192) and _same(prepare["cores"], 4), "profile")
    return prepare


def _check_plan(plan, admission):
    _prepare_plan(plan)
    _need(all(_same(plan[key], admission[key]) for key in ("sources", "python", "artifacts")), "plan")
    server, guest = admission["server"], admission["guest"]
    installed = {key: server[key] for key in ("adb", "tools", "capabilities", "source_review")}
    installed.update({key: guest[key] for key in ("emulator", "qemu", "refuser", "refuser_source")})
    installed.update(auth_key_path=server["auth_key"], compatibility=admission["compatibility"])
    _need(_same(plan["installed"], installed), "installed")

    proposal = _at(guest["proposal"], RUN, cap=_STORAGE_CAP)
    env.validate_proposal(proposal, "run")
    authorization = _at(guest["authorization"], RUN_AUTHORITY, cap=4096)
    env.check_authorization(authorization, "run", guest["proposal"]["sha256"], run_scope=contract.RUN_SCOPE)
    _need(_same(proposal["prepare_proposal"], plan["prepare"]) and proposal["paths"]["root"] == guest["root"]
          and all(_same(proposal[key], guest[key]) for key in ("memory_mib", "cores", "max_seconds")), "proposal")
    return proposal


def check_bounds(began_ns, until_ns):
    _need(type(began_ns) is int and type(until_ns) is int
          and 0 < began_ns < until_ns <= began_ns + SECONDS * NS, "deadline")


def check_window(began_ns, until_ns):
    check_bounds(began_ns, until_ns)
    now = time.monotonic_ns()
    _need(began_ns <= now < until_ns and until_ns - now <= ACTIVATION_SECONDS * NS, "deadline")
    return now


def check_launch_window(began_ns, until_ns):
    now = check_window(began_ns, until_ns)
    _need(now + (controller.SECONDS + TAIL_SECONDS) * NS < until_ns, "deadline")
    return now


def _identity(pid, expected=None):
    handles = process.ProcessHandles(mechanisms._ProcessApi())
    try:
        return handles.add(pid, expected)[1]
    finally:
        _need(handles.close() is True, "identity")


def _live_supervisor(handoff, parent=None):
    supervisor = handoff["supervisor"]
    api = mechanisms._ProcessApi()
    handles = process.ProcessHandles(api)
    try:
        handles.add(supervisor["pid"], supervisor)
        if parent is None:
            _need(os.getppid() == supervisor["pid"] and
                  {supervisor["pid"], os.getpid()} <= set(api.current_job_pids()), "identity")
        else:
            handle, _ = handles.add(parent["pid"], parent)
            _need(os.getppid() == parent["pid"] and api.parent_pid(handle) == supervisor["pid"], "identity")
        handles.guard()
    finally:
        _need(handles.close() is True, "identity")
    check_window(handoff["began_ns"], handoff["until_ns"])


def _live_boot(handoff, parent=None):
    pin, current = _read(HANDOFF)
    _need(pin["sha256"] == os.environ.get(HANDOFF_ENV) and _same(current, handoff), "handoff")
    _live_supervisor(handoff, parent)
    env.check_binding(pin)
    check_launch_window(handoff["began_ns"], handoff["until_ns"])


def _check_boot_records(admission_pin, admission, authority_pin, attempt_pin, *, initial):
    """Join the operation's spent authority and preparation to the SDK admission."""
    _pin(admission_pin, ADMISSION, _RECORD_CAP)
    admission = contract.validate_admission(admission)
    _need(admission["root"] == str(OWNED_ROOT) and admission["seconds"] == OWNER_SECONDS, "admission")
    authority, plan = _approved_plan(authority_pin, attempt_pin)
    proposal = _check_plan(plan, admission)
    prepared = _at(proposal["prepare_result"], GUEST / "prepare-result-v1.json")
    _need(_same(prepared, dict(version=1, proposal_sha256=plan["prepare"]["sha256"], status="completed",
                               closure_verified=True, child_cleanup_complete=True, prepared_created=True)), "prepared")
    contract.verify_artifacts(admission["artifacts"])
    env.verify_prepared(proposal, initial=initial)
    ledger_pin, entry = _ledger(GUEST)
    _need(entry["state"] == "prepared" and entry["reserved_bytes"] == storage.RESERVATION_BYTES
              and entry["proposal_sha256"] == plan["prepare"]["sha256"]
              and all(entry[key] is None for key in ("closure", "recovery", "retirement")), "prepared")
    _need(not os.path.lexists(GUEST / contract.BOOT_CLAIM_FILE), "already_used")
    env.check_binding(ledger_pin)
    # The authority binds the historical ledger. Preparation must have changed
    # it, so the live ledger is checked separately above.
    for pin in (admission_pin, authority_pin, attempt_pin, authority["proposal"],
                authority["plan"], plan["prepare"], admission["guest"]["proposal"],
                admission["guest"]["authorization"], proposal["prepare_result"]):
        env.check_binding(pin)


def _read_handoff(admission_pin, *, live=True):
    pin, handoff = _read(HANDOFF)
    contract._obj(handoff, ("version", "scope", "authority", "attempt", "admission",
                            "supervisor", "began_ns", "until_ns"), "handoff")
    _need(_same(handoff["version"], 2) and handoff["scope"] == HANDOFF_SCOPE
          and _same(handoff["admission"], admission_pin), "handoff")
    contract._process(handoff["supervisor"])
    check = check_window if live else check_bounds
    check(handoff["began_ns"], handoff["until_ns"])
    return pin, handoff


def _check_boot_handoff(admission_pin, admission):
    pin, handoff = _read_handoff(admission_pin)
    _need(handoff["supervisor"]["executable"] == admission["python"]["executable"]["path"], "identity")
    _check_boot_records(admission_pin, admission, handoff["authority"], handoff["attempt"], initial=True)
    env.check_binding(pin)
    return handoff


class _ColdNavigationTargetRuntime(mechanisms._TargetRuntimeCore):
    def __init__(self, request, request_binding, root):
        _need(type(self) is _ColdNavigationTargetRuntime, "owner_type")
        self._handoff = _check_boot_handoff(request["admission"], request["validated_admission"])
        _live_boot(self._handoff, request["owner"])
        super().__init__(request, request_binding, root)

    def start_server(self):
        _live_boot(self._handoff, self.request["owner"])
        super().start_server()

    def guard(self):
        super().guard()
        window = check_launch_window if self.guest_child is None else check_window
        window(self._handoff["began_ns"], self._handoff["until_ns"])

    def _retain_guest(self):
        _live_boot(self._handoff, self.request["owner"])
        guest = self.admission["guest"]
        env.storage_transition(storage.record_state, Path(guest["root"]), "retained",
            proposal_sha256=guest["proposal"]["sha256"],
            expected_prepare_sha256=self.proposal["prepare_proposal"]["sha256"])

    @property
    def _contract(self):
        return contract

    @property
    def _verification(self):
        return client._REPLAY


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv

    def check_admission(admission):
        pin, value = _read(ADMISSION)
        _need(pin["sha256"] == args[3] and _same(value, admission), "admission")
        _need(not os.path.lexists(OWNED_ROOT), "already_used")
        _live_boot(_check_boot_handoff(pin, value))

    if args != ["_worker"] and not (
        type(args) is list and len(args) == 4 and args[:3] == ["--admission", str(ADMISSION), "--admission-sha256"]
    ):
        return 1
    return mechanisms._main_profile(
        args, _contract=contract, _verification=client._REPLAY,
        _runtime_type=_ColdNavigationTargetRuntime, _admission_check=check_admission,
    )


if __name__ == "__main__":
    raise SystemExit(main())
