"""Seal SDK25's spent prepared-run authority to the bounded owner hierarchy.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
import time

from benchmarks import archive_roundtrip_admission as admission
from benchmarks import archive_roundtrip_lifecycle as lifecycle
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_target_owner as shared
from benchmarks import receipt_avd_environment as env
from benchmarks import windows_tcp_control as output_control

HANDOFF = admission.CONTROL / "boot-handoff-v1.json"
SCOPE = "sdk25-archive-roundtrip-boot-handoff-v1"
HANDOFF_ENV = "LOCALLORE_ARCHIVE_ROUNDTRIP_HANDOFF_SHA256"
MAX_SECONDS = 1800
LAUNCH_TAIL = 1240
NS = 1_000_000_000


def _need(condition, reason):
    admission._need(condition, reason)


def _same(left, right):
    return contract._same(left, right)


def check_window(record, *, launching=False):
    began, until = record["began_ns"], record["until_ns"]
    now = time.monotonic_ns()
    _need(type(began) is int and type(until) is int and
          0 < began <= now < until <= began + MAX_SECONDS * NS, "deadline")
    if launching:
        _need(until - now >= LAUNCH_TAIL * NS, "deadline")


def _supervisor_identity():
    api = shared._ProcessApi()
    handles = shared.primitives.ProcessHandles(api)
    try:
        pid = os.getpid()
        _, identity = handles.add(pid)
        _need(pid in api.current_job_pids(), "identity")
        handles.guard()
        return identity
    finally:
        _need(handles.close() is True, "identity")


def write(authority_pin, attempt_pin, *, began_ns, until_ns):
    """Publish one handoff from inside an already owned supervisor job."""
    path = output_control.validate_output(str(HANDOFF))
    record = dict(version=1, scope=SCOPE, authority=authority_pin, attempt=attempt_pin,
                  began_ns=began_ns, until_ns=until_ns)
    check_window(record, launching=True)
    context = admission.verify_spent(authority_pin, attempt_pin)
    record["admission"] = context["admission_pin"]
    record["supervisor"] = _supervisor_identity()
    _need(record["supervisor"]["executable"] == context["admission"]["python"]["executable"]["path"],
          "identity")
    check_window(record, launching=True)
    env.create_json(path, record)
    pin, retained = lifecycle._read(path, admission.AUTHORITY_CAP)
    _need(_same(retained, record), "handoff")
    return pin


def _lineage(record, parent):
    supervisor = record["supervisor"]
    api = shared._ProcessApi()
    handles = shared.primitives.ProcessHandles(api)
    try:
        handles.add(supervisor["pid"], supervisor)
        job_pids = set(api.current_job_pids())
        _need(os.getpid() in job_pids, "identity")
        if parent is None:
            _need(os.getppid() == supervisor["pid"] and supervisor["pid"] in job_pids, "identity")
        else:
            parent_handle, _ = handles.add(parent["pid"], parent)
            _need(os.getppid() == parent["pid"] and
                  api.parent_pid(parent_handle) == supervisor["pid"], "identity")
        handles.guard()
    finally:
        _need(handles.close() is True, "identity")


def live(pin, record, *, parent=None):
    """Recheck the inherited authority, current ancestry and launch window."""
    _need(pin["sha256"] == os.environ.get(HANDOFF_ENV) and
          _same(lifecycle._at(pin, HANDOFF, admission.AUTHORITY_CAP), record), "handoff")
    _lineage(record, parent)
    for binding in (pin, record["authority"], record["attempt"], record["admission"]):
        env.check_binding(binding)
    check_window(record, launching=True)


def verify_boot(admission_pin, admitted, *, parent=None):
    """Check the fixed handoff and exact prepared context before owner dispatch."""
    pin, record = lifecycle._read(HANDOFF, admission.AUTHORITY_CAP)
    contract._obj(record, ("version", "scope", "authority", "attempt", "admission",
                           "supervisor", "began_ns", "until_ns"), "binding")
    _need(_same(record["version"], 1) and record["scope"] == SCOPE and
          _same(record["admission"], admission_pin) and
          pin["sha256"] == os.environ.get(HANDOFF_ENV), "handoff")
    contract._process(record["supervisor"])
    _need(record["supervisor"]["executable"] == admitted["python"]["executable"]["path"],
          "identity")
    live(pin, record, parent=parent)
    context = admission.verify_spent(record["authority"], record["attempt"],
                                     owner_created=parent is not None)
    _need(_same(context["admission_pin"], admission_pin) and _same(context["admission"], admitted),
          "admission")
    live(pin, record, parent=parent)
    return pin, record, context
