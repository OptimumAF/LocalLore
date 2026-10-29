"""Explicit SDK3 client with fresh, owned held-server proofs around dispatch.

Importing this module performs no observation or acquisition. The legacy SDK2
constructor, observer and capture path are never called. Saved records require
the source-admitted parent runtime's independent worker/command verification.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import copy
import hashlib
import math
import os
from pathlib import Path
import re
import shlex
import time

from benchmarks import adb_held_socket_probe as held_probe
from benchmarks import android_process_client as legacy
from benchmarks import android_process_verification_v3 as verification
from benchmarks import receipt_avd_environment as environment
from benchmarks import runtime_spike as host
from benchmarks import windows_tcp_control as output_control

ClientRefused = legacy.ClientRefused


def _need(value, reason="client_guard"):
    legacy._require(value, reason)


def _label(value):
    _need(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_-]{0,47}",value) is not None)


class HeldServerSdkCapture:
    """One finite, fail-stop SDK owner; no implicit legacy observer fallback."""

    def __init__(self, directory, seconds, adb, powershell, admission_binding, launcher_pin=None):
        self.clean = False
        self._failed = True
        self.count = 0
        self._target = None
        self._target_id = None
        self._check_index = 0
        self._external_index = 0
        self._external = None
        self._last_acquired = None
        self._last_time = None
        try:
            legacy._integer(seconds)
            self.until = self._now()+seconds
            self._deadline_limit = self.until
            self.directory = output_control.validate_output(str(directory))
            _need(self.directory.name == "clients")
            parent = self.directory.parent
            self._session_path = output_control.validate_output(str(parent/"sdk-session-v3.json"))
            self._proofs = output_control.validate_output(str(parent/"server-proofs-v3"))
            held_probe._set_temporary()
            self.adb_path, self.powershell = Path(adb), Path(powershell)
            self._adb_file = legacy._file_pin(self.adb_path)
            self._powershell_file = legacy._file_pin(self.powershell)
            _need(type(admission_binding) is dict and set(admission_binding) == {"path","bytes","sha256"})
            bound, admitted = held_probe._load_admission(admission_binding["path"],admission_binding["sha256"])
            _need(held_probe._same(bound,admission_binding))
            owner = legacy._process(environment.process_identity(os.getpid()))
            launcher = None if launcher_pin is None else legacy._process(launcher_pin)
            session = dict(version=1,protocol=verification.SDK_PROTOCOL,
                server_admission=bound,admission=admitted,
                sdk_sources=verification.sdk_source_bindings(),held_sources=held_probe._source_bindings(),
                python=verification.python_bindings(),adb=environment.binding(self.adb_path),
                powershell=environment.binding(self.powershell),owner=owner,launcher=launcher)
            self._session = verification.validate_session(session)
            _need(held_probe._same(self._session,session) and
                  legacy._same_executable(admitted["server"]["executable"],str(self.adb_path)) and
                  self._adb_file[1] == admitted["adb_file"]["sha256"])
            self.directory.mkdir(exist_ok=False)
            self._proofs.mkdir(exist_ok=False)
            self._directory_id = self._directory_identity(self.directory)
            self._proofs_id = self._directory_identity(self._proofs)
            self._parent_id = self._directory_identity(parent)
            environment.create_json(self._session_path,self._session)
            self._session_binding = environment.binding(self._session_path)
            self._failed = False
            self.clean = True
            self._guard()
        except BaseException:
            self._poison()
            raise ClientRefused("client_guard") from None

    @property
    def session(self):
        return copy.deepcopy(self._session)

    @property
    def session_binding(self):
        return copy.deepcopy(self._session_binding)

    @property
    def target(self):
        return copy.deepcopy(self._target)

    @target.setter
    def target(self, value):
        try:
            self._guard()
            if value is None:
                _need(self._target is None)
                return
            _need(type(value) is dict and set(value) == {"transport_id"})
            target = legacy._integer(value["transport_id"])
            _need(self._target_id is None or target == self._target_id)
            self._target_id = target
            self._target = {"transport_id":target}
        except BaseException:
            self._poison()
            raise ClientRefused("client_guard") from None

    def _poison(self):
        self.clean = False
        self._failed = True

    def _now(self):
        now = time.monotonic()
        _need(type(now) in (int,float) and math.isfinite(now) and
              (self._last_time is None or now >= self._last_time),"client_deadline")
        self._last_time = now
        return now

    @staticmethod
    def _directory_identity(path):
        info = legacy._plain(path,directory=True).lstat()
        return info.st_dev,info.st_ino

    def _directory_guard(self):
        _need(self._directory_identity(self.directory) == self._directory_id and
              self._directory_identity(self._proofs) == self._proofs_id and
              self._directory_identity(self.directory.parent) == self._parent_id,"persistence_failed")

    def _guard(self):
        _need(self.clean is True and self._failed is False,"client_closed")
        _need(type(self.until) in (int,float) and math.isfinite(self.until) and
              self.until <= self._deadline_limit and self._now() < self.until,"client_deadline")
        self._directory_guard()
        environment.check_binding(self._session_binding)
        _need(held_probe._same(self._session["sdk_sources"],verification.sdk_source_bindings()) and
              held_probe._same(self._session["held_sources"],held_probe._source_bindings()) and
              held_probe._same(self._session["python"],verification.python_bindings()),"source_changed")
        for row in self._session["sdk_sources"]+self._session["held_sources"]:
            environment.check_binding(row)
        for key in ("server_admission","adb","powershell"):
            environment.check_binding(self._session[key])
        _need(legacy._file_pin(self.adb_path) == self._adb_file and
              legacy._file_pin(self.powershell) == self._powershell_file,"server_changed")
        _need(held_probe._same(legacy._process(environment.process_identity(os.getpid())),self._session["owner"]),"caller_changed")
        launcher = self._session["launcher"]
        if launcher is not None:
            _need(held_probe._same(legacy._process(environment.process_identity(launcher["pid"])),launcher),"launcher_changed")
        _need(self._now() < self.until,"client_deadline")

    def _command(self, command):
        _need(command != legacy._server_command(self.powershell))
        verification.validate_command(copy.deepcopy(command),str(self.adb_path),self._target_id)
        return True

    def _prove(self, kind, index, phase, label, command=None):
        self._last_acquired = None
        self._guard()
        context = dict(kind=kind,index=index,phase=phase,label=label,
            command_sha256=None if command is None else verification.command_digest(copy.deepcopy(command)),
            transport_id=self._target_id)
        name = "check-%04d" % index if kind == "check" else "%s-%04d-%s" % (kind,index,phase)
        seconds = math.floor(min(45,self.until-self._now()))
        _need(seconds > 0,"client_deadline")
        binding = copy.deepcopy(verification.acquire_owned_server_bundle(
            self._proofs/name,self.session_binding,copy.deepcopy(context),seconds))
        self._last_acquired = copy.deepcopy(binding)
        _need(verification.verify_owned_server_bundle(copy.deepcopy(binding),self.session,copy.deepcopy(context)) is True,"server_changed")
        self._guard()
        _need(self._target_id == context["transport_id"],"target_changed")
        return copy.deepcopy(binding)

    def check_server(self):
        try:
            _need(self._external is None)
            self._check_index += 1
            return self._prove("check",self._check_index,"check","check-server")
        except BaseException:
            self._poison()
            raise ClientRefused("server_changed") from None

    def prove_external(self, command, label, phase, index):
        try:
            self._guard()
            _label(label)
            legacy._integer(index)
            _need(type(phase) is str and phase in ("before","after") and self._target_id is not None)
            self._command(command)
            context = (index,label,verification.command_digest(copy.deepcopy(command)),self._target_id)
            if phase == "before":
                _need(self._external is None and index > self._external_index)
                binding = self._prove("external",index,phase,label,command)
                self._external_index = index
                self._external = context
            else:
                _need(self._external == context)
                binding = self._prove("external",index,phase,label,command)
                self._external = None
            return binding
        except BaseException:
            self._poison()
            raise ClientRefused("server_changed") from None

    def _write_stdout(self, stem, raw):
        self._directory_guard()
        path = stem.with_suffix(".stdout.bin")
        environment.safe_path(path,exists=False)
        with path.open("xb") as sink:
            remaining = memoryview(raw)
            while remaining:
                count = sink.write(remaining)
                _need(type(count) is int and 0 < count <= len(remaining),"persistence_failed")
                remaining = remaining[count:]
            sink.flush()
            os.fsync(sink.fileno())
        self._directory_guard()

    def _persist_record(self, result, command, label, stem, effective_ms, before, after, qualified):
        self._directory_guard()
        record = dict(version=3,index=self.count,label=label,status=result.status,returncode=result.returncode,
            cleanup_complete=result.cleanup_complete,stdout_bytes=len(result.stdout),
            stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),stderr_bytes=result.stderr_bytes,
            elapsed_ms=result.elapsed_ms,effective_deadline_ms=effective_ms,protocol=verification.SDK_PROTOCOL,
            client_qualified=qualified,
            server_admission=copy.deepcopy(self._session["server_admission"]),server_before=before,server_after=after,
            transport_id=self._target_id,command_sha256=verification.command_digest(copy.deepcopy(command)),argv=copy.deepcopy(command))
        _need(verification.client_record_shape_v3(record) is True,"persistence_failed")
        environment.create_json(stem.with_suffix(".json"),record)
        self._directory_guard()

    def capture(self, command, label, seconds=15, cap=131072, *, full_budget=False):
        try:
            self._guard()
            _need(self._external is None)
            _label(label)
            legacy._seconds(seconds)
            legacy._integer(cap,high=legacy.MAX_CAPTURE)
            _need(type(full_budget) is bool)
            self._command(command)
            command = copy.deepcopy(command)
            index = self.count+1
            before = self._prove("command",index,"before",label,command)
            self._guard()
            self._command(command)
            remaining = self.until-self._now()
            _need(remaining > 0 and (not full_budget or remaining >= seconds),"client_deadline")
            effective = min(seconds,remaining)
            effective_ms = math.ceil(effective*1000)
            self.count = index
            stem = self.directory/("command-%04d" % index)
            trusted = True
            dispatched_command = copy.deepcopy(command)
            try:
                result = legacy._result(host.run_process(dispatched_command,request=b"",deadline=effective,max_output=cap),cap)
            except BaseException:
                # No trusted owner measurement exists; do not infer terminal
                # cleanup, zero elapsed time or a safely available post-proof.
                result = host.ProcessResult("spawn_failed",None,cleanup_complete=False)
                trusted = False
            # Preserve a trusted returned result even if the runner changed
            # its supplied argv. Such a command cannot qualify or acquire a
            # post-proof for an intent that is now uncertain.
            command_unchanged = held_probe._same(dispatched_command,command)
            self._write_stdout(stem,result.stdout)
            after, post_verified = None, False
            if trusted and command_unchanged and result.cleanup_complete is True:
                try:
                    after = self._prove("command",index,"after",label,command)
                    post_verified = True
                except BaseException:
                    after = copy.deepcopy(self._last_acquired)
            qualified = False
            try:
                legacy._completed(result)
                _need(post_verified,"server_changed")
                self._guard()
                qualified = True
            except BaseException:
                pass
            # The command's result remains truthful even if a later proof or
            # final guard refused. Qualification is a separate, closed flag.
            self._persist_record(result,command,label,stem,effective_ms,before,after,qualified)
            _need(qualified,"capture_failed")
            return result.stdout
        except BaseException:
            self._poison()
            raise ClientRefused("capture_failed") from None

    def adb(self, operation, label, seconds=15, cap=131072, *, full_budget=False):
        try:
            _need(self._target_id is not None and type(operation) is list and bool(operation))
            return self.capture([str(self.adb_path),"-H","127.0.0.1","-P","5037","-t",str(self._target_id),*operation],
                label,seconds,cap,full_budget=full_budget)
        except BaseException:
            self._poison()
            raise ClientRefused("capture_failed") from None

    def shell(self, op, label, seconds=15, cap=131072, *, full_budget=False):
        try:
            _need(type(op) is list and bool(op) and all(type(x) is str and "\x00" not in x for x in op))
            return self.adb(["shell",shlex.join(op)],label,seconds,cap,full_budget=full_budget)
        except BaseException:
            self._poison()
            raise ClientRefused("capture_failed") from None
