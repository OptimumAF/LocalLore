"""Fixed, model-free archive transfer policy over the shared owned target.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
from pathlib import PureWindowsPath
import re

from benchmarks import archive_roundtrip_build as build
from benchmarks import owned_target_contract as core

PROTOCOL = "owned-emulator-archive-roundtrip-v1"
RUN_SCOPE = PROTOCOL
APP = "org.locallore.app.archiveverify"
TEST = APP + ".test"
SELECTOR = "org.locallore.app.ArchivePlatformRoundTripTest#platformRoundTrip"
RUNNER = TEST + "/androidx.test.runner.AndroidJUnitRunner"
OUTBOUND = "archive_outbound"
RETURN = "archive_return"
RETURN_WRITE = "archive_return_write"
TRANSFER_OUTPUT = "archive-transfer-v1"
BRIDGE_DIRECTORY = "windows-continuation-v1"
GUEST_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/desktop-archive-roundtrip-v1/avd-v1")
ARTIFACT_KEYS = build.ARTIFACT_KEYS
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | {
    "archive_roundtrip_build.py", "owned_archive_roundtrip_contract.py",
    "owned_archive_roundtrip_owner.py", "owned_archive_roundtrip_client.py",
    "archive_roundtrip_outbound.py", "android_instrumentation_evidence.py",
    "archive_roundtrip_bridge.py", "archive_roundtrip_return.py", "archive_ui_build.py",
    "archive_roundtrip_final.py", "archive_roundtrip_lifecycle.py", "archive_roundtrip_admission.py",
    "archive_roundtrip_handoff.py", "archive_roundtrip_supervisor.py", "archive_roundtrip_prepare.py",
})
ROLES = ("product_apk", "test_apk")
FILES = ("owner-v1", "windows-return.json", "windows-continued.json", "android-origin.json")
RETURN_FILES = ("android-return.json", "android-final.json")
MARKER = b"locallore-platform-roundtrip-v1"
MAX_BYTES = 128 * 1024

# Only a syntactically valid fixed argv is a possible instrumentation claim.
# validate_operation additionally binds its run to the current admission.
_INSTRUMENT_PREFIX = ["am", "instrument", "-w", "-r", "-e", "class", SELECTOR,
                      "-e", "platform_phase"]


class _ArchiveContract(core._Contract):
    def validate_admission(self, value):
        admission = super().validate_admission(value)
        try:
            build.validate_bindings(admission["artifacts"])
        except build.BuildRefused:
            raise core.TargetRefused("binding") from None
        return admission

    def validate_client_record(self, value, session):
        record = super().validate_client_record(value, session)
        core._need(record["stdout"]["bytes"] + record["stderr"]["bytes"] <= MAX_BYTES, "capture")
        return record

    def _run(self, admission):
        return "transfer-" + self.validate_admission(admission)["run_id"]

    def outbound_argv(self, admission):
        return [*_INSTRUMENT_PREFIX, "outbound", "-e", "platform_run", self._run(admission), RUNNER]

    def return_argv(self, admission):
        return [*_INSTRUMENT_PREFIX, "return", "-e", "platform_run", self._run(admission), RUNNER]

    def instrumentation_kind(self, argv):
        core._need(type(argv) is list and len(argv) == 14 and argv[:9] == _INSTRUMENT_PREFIX
                   and argv[9] in ("outbound", "return") and argv[10:12] == ["-e", "platform_run"]
                   and type(argv[12]) is str and re.fullmatch("transfer-[0-9a-f]{32}", argv[12])
                   and argv[13] == RUNNER, "command")
        return OUTBOUND if argv[9] == "outbound" else RETURN

    def staged_path(self, admission, role):
        core._need(type(role) is str and role in ROLES, "command")
        package = "product" if role == "product_apk" else "test"
        return "/data/local/tmp/locallore-archive-" + self._run(admission) + "-" + package + ".apk"

    def stage_argv(self, admission, role):
        path = self.staged_path(admission, role)
        return ["sh", "-c", "umask 022 && set -C && test ! -e " + path +
                " && test ! -L " + path + " && cat > " + path]

    def install_argv(self, admission, role):
        # Android's default install can replace an existing package. -R refuses it.
        return ["pm", "install", "-R", "-t", "--user", "0", self.staged_path(admission, role)]

    def _regular(self, file):
        return ["test ! -L " + file, "test -f " + file,
                'test "$(stat -c %u ' + file + ')" = "$u"',
                'test "$(stat -c %h ' + file + ')" = 1']

    def _private_guards(self, directory):
        marker = directory + "/owner-v1"
        guards = ['u=$(id -u)', 'case "$u" in ""|*[!0-9]*) exit 1;; esac',
                  'test "$u" -ge 10000', 'test "$u" -le 99999']
        for parent in ("no_backup", "no_backup/platform-roundtrip", directory):
            guards += ["test ! -L " + parent, "test -d " + parent,
                       'test "$(stat -c %u ' + parent + ')" = "$u"']
        guards += self._regular(marker)
        marker_hash = hashlib.sha256(MARKER).hexdigest()
        guards += ['test "$(stat -c %s ' + marker + ')" = ' + str(len(MARKER)),
                   'test "$(sha256sum ' + marker + ')" = "' + marker_hash + '  ' + marker + '"']
        return guards

    def read_argv(self, admission, leaf):
        core._need(type(leaf) is str and leaf in FILES + RETURN_FILES, "command")
        directory = "no_backup/platform-roundtrip/" + self._run(admission)
        path = directory + "/" + leaf
        guards = self._private_guards(directory)
        if leaf != "owner-v1":
            guards += self._regular(path)
            guards += ['s=$(stat -c %s ' + path + ')', 'case "$s" in ""|*[!0-9]*) exit 1;; esac',
                       'test "$s" -gt 0', 'test "$s" -le ' + str(MAX_BYTES)]
        # The client caps the whole capture at MAX_BYTES. The extra byte lets
        # it refuse growth after stat instead of accepting a truncated prefix.
        guards.append("head -c " + str(MAX_BYTES + 1) + " " + path)
        return ["run-as", APP, "--user", "0", "sh", "-c", " && ".join(guards)]

    def return_write_argv(self, admission):
        directory = "no_backup/platform-roundtrip/" + self._run(admission)
        path = directory + "/android-return.json"
        guards = self._private_guards(directory)
        guards += ["umask 077", "set -C", "test ! -e " + path, "test ! -L " + path, "cat > " + path]
        return ["run-as", APP, "--user", "0", "sh", "-c", " && ".join(guards)]

    def return_kind(self, argv, admission):
        if argv == self.return_argv(admission):
            return RETURN
        if argv == self.return_write_argv(admission):
            return RETURN_WRITE
        if any(argv == self.read_argv(admission, leaf) for leaf in RETURN_FILES):
            return "archive_return_read"
        return None

    def validate_operation(self, value, admission):
        a = self.validate_admission(admission)
        core._obj(value, ("argv", "stdin"), "command")
        argv = value["argv"]
        core._need(type(argv) is list and 1 <= len(argv) <= 64 and all(
            type(word) is str and word.isascii() and 0 < len(word) <= 8192
            and not any(ord(c) < 32 for c in word) for word in argv), "command")
        if argv[:1] == ["getprop"] or argv == ["am", "get-current-user"] or argv[:1] == ["cmd"]:
            return super().validate_operation(value, a)
        if argv[:1] == ["sha256sum"] and len(argv) == 2 and argv[1].startswith("/data/app/"):
            return super().validate_operation(value, a)
        for role in ROLES:
            if argv == self.stage_argv(a, role):
                core._need(core._same(value["stdin"], a["artifacts"][role]), "command")
                return copy.deepcopy(value)
            if argv in (self.install_argv(a, role), ["sha256sum", self.staged_path(a, role)]):
                core._need(value["stdin"] is None, "command")
                return copy.deepcopy(value)
        kind = self.return_kind(argv, a) if argv[:1] in (["am"], ["run-as"]) else None
        if kind == RETURN_WRITE:
            source = value["stdin"]
            self.binding(source, max_bytes=MAX_BYTES)
            expected = (PureWindowsPath(a["root"]) / TRANSFER_OUTPUT / BRIDGE_DIRECTORY
                        / "windows" / "android-return.json")
            core._need(PureWindowsPath(source["path"]) == expected and source["bytes"] > 0, "binding")
            return copy.deepcopy(value)
        if kind is not None or argv == self.outbound_argv(a) or any(
                argv == self.read_argv(a, leaf) for leaf in FILES):
            core._need(value["stdin"] is None, "command")
            return copy.deepcopy(value)
        raise core.TargetRefused("command")


PROFILE = _ArchiveContract(core.ContractProfile(
    PROTOCOL, "sdk-archive-roundtrip-v1", "archive-roundtrip-socket-proof-v1",
    GUEST_ROOT, SOURCE_NAMES, 25, "sdk-session-v25.json",
    "owned_archive_roundtrip_owner.py", "owned-archive-roundtrip-boot-claim-v1.json",
    (), ARTIFACT_KEYS, (OUTBOUND, RETURN_WRITE, RETURN), APP=APP, TEST=TEST, MODEL_MATERIAL=False,
))

# The guarded worker, live observer, wire and closed replay use one profile.
for _name in ("PORT", "REQUEST_KEYS", "WORKER_KEYS", "CLEANUP_KEYS",
              "TargetRefused", "_need", "_obj", "_int", "_path", "_process", "_same"):
    globals()[_name] = getattr(core, _name)
for _name in ("SDK_PROTOCOL", "PROOF_PROTOCOL", "CLIENT_VERSION", "SESSION_FILE",
              "OWNER_SCRIPT", "BOOT_CLAIM_FILE", "CLAIM_KINDS"):
    globals()[_name] = getattr(PROFILE.profile, _name)
for _name in (
    "binding", "_rows", "check_stop", "validate_admission", "validate_running",
    "validate_session", "validate_operation", "operation_digest", "validate_observation",
    "validate_guest_job", "validate_guest_observation", "validate_guest_prefix",
    "validate_proof", "validate_query_bundle", "validate_ready", "validate_claim",
    "validate_client_record", "source_bindings", "revalidate_inputs", "device_status", "device_transport",
    "instrumentation_kind", "claim_record", "outbound_argv", "staged_path", "stage_argv",
    "install_argv", "read_argv", "return_argv", "return_write_argv", "return_kind",
):
    globals()[_name] = getattr(PROFILE, _name)
del _name
