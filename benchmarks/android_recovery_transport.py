"""Fixed, read-only stopped-session capture; never opens SQLite or invokes inference.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import base64
import binascii
import hashlib
import re
import shlex

PACKAGE = "org.locallore.runtimebench.litert.cacheprobe"
NAMES = ("stories.sqlite3", "stories.sqlite3-wal", "stories.sqlite3-shm", "stories.sqlite3-journal")
MAX_FILE = 131072
MAX_WIRE = ((MAX_FILE + 2) // 3) * 4
OWNER = b"locallore-explicit-cache-probe-v1\n"
OWNER_SHA256 = hashlib.sha256(OWNER).hexdigest()
BINARY_CONTROL = bytes(range(256)) + b"\x00\r\n~.\n"
STAT_FORMAT = "%F|%s|%u|%g|%a|%d|%i|%Y|%Z"
STATUSES = {"completed", "cancelled", "timeout", "output_limit", "spawn_failed", "cleanup_failed"}


class RecoveryFailure(Exception):
    """Fixed category only; never includes remote bytes, paths or exception text."""
    def __init__(self, category, clients_cleaned):
        super().__init__(category)
        self.category = category
        self.__clients_cleaned = clients_cleaned is True

    @property
    def clients_cleaned(self):
        return self.__clients_cleaned


class ReadOnlyRecovery:
    """Caller owns APK identity, stopped-process and fresh storage pre/post gates.

    Device.raw must use the existing bounded byte-pipe runner and its sticky
    clients_cleaned flag. raw_sink must synchronously retain exact available
    stdout or raise, and must perform no hidden device calls. Facts are private.
    """
    def __init__(self, device, session, raw_sink):
        if type(session) is not str or re.fullmatch(r"[a-f0-9]{32}", session) is None or not callable(raw_sink):
            raise RecoveryFailure("invalid_arguments", getattr(device, "clients_cleaned", None) is True)
        self.__device, self.__raw_sink = device, raw_sink
        self.__directory = "no_backup/locallore-cache-probe-v1-" + session
        self.__poisoned = False
        self.__clients_cleaned = getattr(device, "clients_cleaned", None) is True
        self.__qualified = False
        self.__sequence = 0
        self._facts = None

    @property
    def device(self):
        return self.__device

    @property
    def raw_sink(self):
        return self.__raw_sink

    @property
    def directory(self):
        return self.__directory

    @property
    def poisoned(self):
        return self.__poisoned

    @property
    def clients_cleaned(self):
        return self.__clients_cleaned

    @property
    def qualified(self):
        return self.__qualified

    @property
    def sequence(self):
        return self.__sequence

    def _fail(self, category):
        self.__poisoned = True
        raise RecoveryFailure(category, self.clients_cleaned)

    def _known(self):
        self.__clients_cleaned &= getattr(self.device, "clients_cleaned", None) is True
        if self.poisoned:
            self._fail("recovery_poisoned")
        if not self.clients_cleaned:
            self._fail("client_cleanup_unknown")

    def _exchange(self, phase, arguments, limit, expected_code=0, file_output=False):
        self._known()
        self.__sequence += 1
        stage = f"{self.sequence:03d}_{phase}"
        try:
            # Only a 128 KiB file's Base64 expansion needs the already-supported
            # 256 KiB combined runner cap. All other operations keep its default.
            options = {"max_output": 262144} if file_output else {}
            result = self.device.raw(arguments, deadline=20, **options)
        except Exception as error:
            self.__clients_cleaned &= getattr(error, "command_cleaned", None) is True
            self.__clients_cleaned &= getattr(self.device, "clients_cleaned", None) is True
            # No result bytes exist; still retain the failed command's empty observation.
            try:
                self.raw_sink(stage, b"", {"status": "call_failed", "returncode": None,
                    "cleanup_complete": self.clients_cleaned, "stdout_bytes": 0,
                    "stdout_sha256": hashlib.sha256(b"").hexdigest(), "stderr_bytes": None})
            except Exception:
                self.__clients_cleaned &= getattr(self.device, "clients_cleaned", None) is True
                self._fail("raw_sink_failed")
            self.__clients_cleaned &= getattr(self.device, "clients_cleaned", None) is True
            self._fail("device_call_failed")
        raw = getattr(result, "stdout", None)
        status = getattr(result, "status", None)
        code = getattr(result, "returncode", None)
        stderr = getattr(result, "stderr_bytes", None)
        cleaned = getattr(result, "cleanup_complete", None) is True
        self.__clients_cleaned &= cleaned and getattr(self.device, "clients_cleaned", None) is True
        safe = {"status": status if type(status) is str and status in STATUSES else "invalid_result",
            "returncode": code if type(code) is int and 0 <= code <= 255 else None,
            "cleanup_complete": self.clients_cleaned,
            "stdout_bytes": len(raw) if type(raw) is bytes else None,
            "stdout_sha256": hashlib.sha256(raw).hexdigest() if type(raw) is bytes else None,
            "stderr_bytes": stderr if type(stderr) is int and 0 <= stderr <= (262144 if file_output else MAX_FILE) else None}
        try:
            self.raw_sink(stage, raw if type(raw) is bytes else b"", safe)
        except Exception:
            self.__clients_cleaned &= getattr(self.device, "clients_cleaned", None) is True
            self._fail("raw_sink_failed")
        # Sink callbacks can also reveal unknown transport ownership. Never admit
        # output or dispatch a following command until that fence is rechecked.
        self._known()
        if (type(raw) is not bytes or len(raw) > limit or status != "completed"
                or type(code) is not int or code != expected_code or type(stderr) is not int or stderr != 0):
            self._fail("command_failed")
        return raw

    def _command(self, script):
        # Device.raw inserts -T. Shell joins argv without quoting; join exactly
        # once here. Unlike exec-out, do not prequote the sh -c script argv.
        return ["shell", "-e", "none", shlex.join(["run-as", PACKAGE, "/system/bin/sh", "-c", script])]

    def qualify(self):
        self._known()
        if self.qualified:
            self._fail("already_qualified")
        features = self._exchange("features", ["features"], 4096)
        token = rb"[a-zA-Z0-9_\-]+"
        if re.fullmatch(token + rb"(?:," + token + rb")*\r?\n?", features):
            names = features.rstrip(b"\r\n").split(b",")
        elif re.fullmatch(token + rb"(?:\r?\n" + token + rb")*\r?\n?", features):
            names = features.splitlines()
        else:
            self._fail("features_invalid")
        if b"shell_v2" not in names or len(names) != len(set(names)) or b"" in names:
            self._fail("shell_v2_required")
        if self._exchange("exit_control", self._command("exit 37"), 0, expected_code=37) != b"":
            self._fail("exit_control_failed")
        escaped = "".join("\\0%03o" % byte for byte in BINARY_CONTROL)
        script = "printf '%b' " + shlex.quote(escaped) + " | base64 -w 0"
        wire = self._exchange("binary_control", self._command(script), 4096)
        raw = self._decode_wire(wire, len(BINARY_CONTROL))
        if raw != BINARY_CONTROL:
            self._fail("binary_control_failed")
        self.__qualified = True
        return {"version": 1, "status": "qualified", "shell_v2": True, "remote_exit_verified": True,
            "binary_control_bytes": len(raw), "binary_control_sha256": hashlib.sha256(raw).hexdigest(),
            "clients_cleaned": True}

    def _decode_wire(self, wire, expected_bytes):
        if len(wire) > ((expected_bytes + 2) // 3) * 4:
            self._fail("base64_invalid")
        try:
            raw = base64.b64decode(wire, validate=True)
        except (ValueError, binascii.Error):
            self._fail("base64_invalid")
        if base64.b64encode(raw) != wire:
            self._fail("base64_invalid")
        if len(raw) != expected_bytes:
            self._fail("decoded_size_mismatch")
        return raw

    def _ready(self):
        self._known()
        if not self.qualified:
            self._fail("qualification_required")

    def _guards(self):
        q = shlex.quote(self.directory)
        marker = shlex.quote(self.directory + "/owner-v1")
        # No command substitution on marker bytes: size + full SHA bind the
        # exact newline-terminated owner, not a shell-normalized text value.
        return (f"q={q}; m={marker}; [ -d no_backup ] && [ ! -L no_backup ] || exit 71; "
            '[ -d "$q" ] && [ ! -L "$q" ] || exit 71; '
            '[ -f "$m" ] && [ ! -L "$m" ] || exit 71; '
            '[ "$(stat -c %s "$m")" = 34 ] || exit 71; '
            f'[ "$(sha256sum "$m")" = "{OWNER_SHA256}  $m" ] || exit 71; ')

    @staticmethod
    def _bounded_file():
        return ('[ -f "$f" ] && [ ! -L "$f" ] || exit 72; '
            's=$(stat -c %s "$f") || exit 72; case "$s" in ""|*[!0-9]*) exit 72;; esac; '
            f'[ "$s" -le {MAX_FILE} ] || exit 72; ')

    def facts(self):
        self._ready()
        script = self._guards()
        for label, path in (("base", "no_backup"), ("session", self.directory), ("owner", self.directory + "/owner-v1")):
            script += f"printf '%s|' PATH {label}; stat -c {shlex.quote(STAT_FORMAT)} {shlex.quote(path)} || exit 72; "
        script += f'printf "HASH|owner|"; sha256sum "$m" || exit 72; '
        for name in NAMES:
            script += f'f={shlex.quote(self.directory + "/" + name)}; '
            script += ('if [ -e "$f" ]; then ' + self._bounded_file()
                + f"printf '%s|' FILE {name}; stat -c {shlex.quote(STAT_FORMAT)} \"$f\" || exit 72; "
                + f'printf "HASH|{name}|"; sha256sum "$f" || exit 72; '
                + f'else [ ! -L "$f" ] || exit 72; printf "ABSENT|{name}\\n"; fi; ')
        raw = self._exchange("facts", self._command(script), 8192)
        try:
            facts = self._parse_facts(raw)
        except (ValueError, UnicodeError, IndexError, OverflowError, StopIteration):
            self._fail("facts_invalid")
        if self._facts is not None and facts != self._facts:
            self._fail("facts_changed")
        self._facts = facts
        return {**facts, "files": {name: {**row, "metadata": list(row["metadata"])} for name, row in facts["files"].items()},
            "absent": list(facts["absent"]), "directories": {name: list(row) for name, row in facts["directories"].items()},
            "owner": {**facts["owner"], "metadata": list(facts["owner"]["metadata"])}}

    def _parse_facts(self, raw):
        # Metadata is ASCII text only. Accept uniform LF or CRLF after raw
        # retention; never apply newline conversion to a binary/Base64 payload.
        if b"\r" in raw:
            normalized = raw.replace(b"\r\n", b"\n")
            if b"\r" in normalized or normalized.replace(b"\n", b"\r\n") != raw:
                raise ValueError("framing")
            raw = normalized
        text = raw.decode("ascii")
        if not text.endswith("\n") or "\x00" in text:
            raise ValueError("framing")
        # splitlines() also treats VT/FF/record separators as line endings.
        # Only the already-validated LF delimiter is part of this protocol.
        lines = iter(text[:-1].split("\n"))

        def stat(line, prefix, kind):
            fields = line.split("|")
            kinds = {"regular file", "regular empty file"} if kind == "regular file" else {kind}
            if fields[:2] != prefix or len(fields) != 11 or fields[2] not in kinds:
                raise ValueError("metadata")
            if fields[2] == "regular empty file" and fields[3] != "0":
                raise ValueError("empty_metadata")
            values = fields[3:]
            for index, value in enumerate(values):
                expression = r"[0-7]{3,7}" if index == 3 else (r"-?(?:0|[1-9][0-9]{0,18})" if index >= 6 else r"(?:0|[1-9][0-9]{0,19})")
                if re.fullmatch(expression, value) is None or not -(2**63) <= int(value) < 2**64:
                    raise ValueError("numeric_metadata")
            if int(values[4]) <= 0 or int(values[5]) <= 0:
                raise ValueError("identity")
            return fields[2:]

        def hashed(line, name, path):
            prefix = f"HASH|{name}|"
            if not line.startswith(prefix):
                raise ValueError("hash")
            digest, separator, observed = line[len(prefix):].partition("  ")
            if separator != "  " or observed != path or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("hash_identity")
            return digest

        directories = {"base": stat(next(lines), ["PATH", "base"], "directory"),
            "session": stat(next(lines), ["PATH", "session"], "directory")}
        owner = stat(next(lines), ["PATH", "owner"], "regular file")
        owner_hash = hashed(next(lines), "owner", self.directory + "/owner-v1")
        if owner[1] != "34" or owner_hash != OWNER_SHA256:
            raise ValueError("owner")
        files, absent = {}, []
        for name in NAMES:
            line = next(lines)
            if line == "ABSENT|" + name:
                absent.append(name)
                continue
            metadata = stat(line, ["FILE", name], "regular file")
            size = int(metadata[1])
            if not 0 <= size <= MAX_FILE:
                raise ValueError("size")
            digest = hashed(next(lines), name, self.directory + "/" + name)
            files[name] = {"bytes": size, "sha256": digest, "metadata": metadata}
        if next(lines, None) is not None or NAMES[0] not in files:
            raise ValueError("inventory")
        return {"files": files, "absent": absent, "directories": directories,
            "owner": {"bytes": 34, "sha256": owner_hash, "metadata": owner}}

    def read_file(self, name, expected_bytes, expected_sha256):
        self._ready()
        if (type(name) is not str or name not in NAMES or type(expected_bytes) is not int
                or not 0 <= expected_bytes <= MAX_FILE or type(expected_sha256) is not str
                or re.fullmatch(r"[a-f0-9]{64}", expected_sha256) is None):
            self._fail("invalid_file_request")
        if (self._facts is None or name not in self._facts["files"]
                or self._facts["files"][name]["bytes"] != expected_bytes
                or self._facts["files"][name]["sha256"] != expected_sha256):
            self._fail("facts_required")
        script = self._guards() + f'f={shlex.quote(self.directory + "/" + name)}; '
        # A direct encoder invocation preserves read failures in its exit code.
        # Never pipe cat into an encoder, which could conceal the reader's exit.
        script += self._bounded_file() + 'base64 -w 0 "$f"'
        wire = self._exchange("file_" + str(NAMES.index(name)), self._command(script), MAX_WIRE, file_output=True)
        raw = self._decode_wire(wire, expected_bytes)
        if len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != expected_sha256:
            self._fail("file_mismatch")
        if name == NAMES[0] and not raw.startswith(b"SQLite format 3\x00"):
            self._fail("sqlite_header_invalid")
        return raw
