"""Read-only readiness check for the corrected, frozen SDK23 reuse proposal.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import owned_saved_library_status as owner
from benchmarks import saved_library_status_handoff as handoff
from benchmarks import saved_library_status_resume_handoff as resume

SCOPE = "sdk23-resume-readiness-audit-v1"
FROZEN_SOURCE = Path("D:/Worktrees/LocalLore-saved-library-resume-supervisor-v1")
FROZEN_HEAD = "636c91ed7e6d95b05973af7cba9a05288df3210b"
CORRECTED = Path("D:/Dev/Experiments/LocalLore/2026-11-09-saved-library-resume-approved-v1/PROPOSED_OPERATION_CORRECTED.md")
ORIGINAL_SHA256 = "588a65ffa5e20700afbe9695a07786e097cc307b5d50d5ce4e4c446feeba8d9f"
EXPECTED = dict(proposal_sha256="b65fe22e3292322c639826e4d7f13046142f8409a87d939a07dec5a25c0767a1",
                plan_sha256="845bc374d1cbfbb7e1c326aa7c949e6869c96968a081af1398ac8caf1a8647f2",
                manifest_sha256="a7d428bae24756548cd2693dc72c74906c595f053691a793c22ae5deb6446b5f",
                ledger_sha256="100b7ec47460acc27acde614f6e6fd590fca8e6528ff12cc9add3c771f60e2a1")
RECORDS_BYTES = 256 * 1024**2


class ReadinessRefused(RuntimeError):
    pass


def _require(condition, reason):
    if not condition:
        raise ReadinessRefused(reason)


def _proposal_head(text):
    rows = re.findall(r" at `([^\r\n`]+)` in `([^\r\n`]+)`\.", text)
    _require(len(rows) == 1 and re.fullmatch("[0-9a-f]{40}", rows[0][0]) is not None,
             "proposal_source")
    return rows[0]


def _sealed_inputs():
    env = handoff.env
    env.safe_path(FROZEN_SOURCE, directory=True)
    protected = (resume.AUTHORITY, resume.ATTEMPT_ROOT, resume.HANDOFF, resume.OWNED_ROOT,
                 handoff.GUEST / owner.BOOT_CLAIM_FILE,
                 handoff.GUEST / "guest-storage-closure-v1.json",
                 handoff.LEDGER.with_name("admission.lock"))
    _require(not any(os.path.lexists(path) for path in protected), "already_used")
    corrected = env.binding(CORRECTED)
    original = env.binding(resume.PROPOSAL)
    _require(corrected["sha256"] == EXPECTED["proposal_sha256"] and original["sha256"] == ORIGINAL_SHA256,
             "proposal_digest")
    text = handoff.files._bound(corrected, cap=65536).decode("utf-8")
    head, source_path = _proposal_head(text)
    local = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=FROZEN_SOURCE,
                                    text=True, timeout=15).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=FROZEN_SOURCE,
                                     text=True, timeout=15)
    _require(head == local == FROZEN_HEAD and source_path == FROZEN_SOURCE.as_posix() and not status,
             "proposal_source")

    plan_pin, plan = handoff.read(resume.PLAN, 131072)
    manifest, _ = handoff.read(resume.review.MANIFEST)
    ledger, entry = handoff.ledger_entry(handoff.GUEST)
    for label, name, pin in (("Plan SHA-256", "plan_sha256", plan_pin),
                             ("Manifest SHA-256", "manifest_sha256", manifest),
                             ("Ledger SHA-256", "ledger_sha256", ledger)):
        _require(pin["sha256"] == EXPECTED[name] and
                 [line for line in text.splitlines() if line.startswith(label)] == [label + " " + pin["sha256"]],
                 "input_digest")
    _require(plan["source_root"] == str(FROZEN_SOURCE)
             and owner._same(plan["evidence"]["manifest"], manifest)
             and owner._same(plan["evidence"]["ledger"], ledger), "input_digest")
    historical = handoff.at(plan["original_run"], handoff.RUN, cap=handoff.STORAGE_CAP)
    floors = env.root_free_min(str(handoff.GUEST))
    _require(owner._same(historical["host_free_min"], floors)
             and historical["paths"]["root"] == str(handoff.GUEST), "disk_floors")
    resume.review._check_ledger_entry(entry, historical["prepare_proposal"]["sha256"])
    for pin in (corrected, original, plan_pin, manifest, ledger, plan["original_run"]):
        env.check_binding(pin)
    _require(not any(os.path.lexists(path) for path in protected), "already_used")
    return dict(source_head=head, floors=floors, **EXPECTED)


def _free_bytes():
    return {drive: shutil.disk_usage(drive + "\\").free for drive in ("C:", "D:")}


_CHILD = """import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from benchmarks import saved_library_status_resume_operation as operation
h = operation.handoff
r = operation.resume
expected = h.env.decode_json(sys.stdin.buffer.read())
try:
    manifest, _ = h.read(r.review.MANIFEST)
    ledger, _ = h.read(h.LEDGER, h.STORAGE_CAP)
    pin, saved = h.read(r.PLAN, 131072)
    h.env.require((manifest["sha256"], ledger["sha256"], pin["sha256"]) ==
                  (expected["manifest_sha256"], expected["ledger_sha256"], expected["plan_sha256"]), "binding")
    plan = r.inspect_plan(manifest, ledger)
    h.env.require(operation._same(plan, saved), "plan")
    r._check_plan(plan)
    facts = operation.preflight(plan)
    h.env.require(facts["ports_free"] is True and operation._same(facts["ledger"], ledger), "binding")
    result = dict(status="ready", reason=None, resources=facts["resources"])
except (OSError, RuntimeError, ValueError, TypeError, KeyError) as error:
    result = dict(status="refused", reason=operation._reason(error))
sys.stdout.buffer.write(h.env.encoded(result))
"""


def _full_preflight(sealed):
    pin, plan = handoff.read(resume.PLAN, 131072)
    _require(pin["sha256"] == sealed["plan_sha256"], "input_digest")
    executable = plan["python"]["executable"]
    _require(Path(executable["path"]) == Path(sys.executable), "python")
    handoff.env.check_binding(executable)
    result = subprocess.run([executable["path"], "-I", "-S", "-B", "-c", _CHILD],
                            cwd=FROZEN_SOURCE, input=handoff.env.encoded(sealed), capture_output=True,
                            timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    _require(result.returncode == 0 and result.stderr == b"" and len(result.stdout) <= 65536,
             "preflight_child")
    row = handoff.env.decode_json(result.stdout)
    _require(type(row) is dict and (
        (set(row) == {"status", "reason", "resources"} and row["status"] == "ready" and
         row["reason"] is None and type(row["resources"]) is dict) or
        (set(row) == {"status", "reason"} and row["status"] == "refused" and
         type(row["reason"]) is str and re.fullmatch("[a-z_]{1,64}", row["reason"]) is not None)
    ), "preflight_child")
    return row


def inspect():
    """Report current readiness without minting authority or consuming an attempt."""
    sealed = _sealed_inputs()
    result = dict(version=1, scope=SCOPE, status="refused", reason="host_disk_capacity",
                  execution_authorized=False, preflight=None)
    result.update({key: value for key, value in sealed.items() if key != "floors"})
    required = dict(sealed["floors"])
    required["D:"] += RECORDS_BYTES

    def capacity():
        free = _free_bytes()
        shortfall = {drive: max(0, required[drive] - free[drive]) for drive in required}
        result.update(free_bytes=free, required_bytes=required, shortfall_bytes=shortfall)
        return not any(shortfall.values())

    if not capacity():
        return result
    checked = _full_preflight(sealed)
    _require(owner._same(_sealed_inputs(), sealed), "seal_changed")
    result["preflight"] = checked
    if capacity():
        result.update(status=checked["status"], reason=checked["reason"])
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        _require(args == [], "arguments")
        result = inspect()
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        reason = str(error) if type(error) is ReadinessRefused else "inspection_refused"
        result = dict(version=1, scope=SCOPE, status="refused", reason=reason, execution_authorized=False)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
