"""Fixed original synthetic transfer contract; no IO, subprocess or CLI.

Commands are descriptions only. A parsed metadata proof does not establish the
caller's process ownership, command provenance or transfer success.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib

BLOCK_BYTES = 1_048_576
SOURCE_BYTES = 1_073_741_824
MODES = ("CAT", "DD_1M", "SHELL_CAT")
ROOT = "no_backup/receipt-transfer-probe-v1"
APP = "org.locallore.app.modelvolumeverify"
SOURCE_SHA256 = "93b6ba41cf54e72a26ab955cdf953420847be6229f592ea79770362c91558c3f"
OWNER = ROOT + "/owner-v1.txt"
OWNER_CONTENT = b"locallore-receipt-transfer-probe-v1\n"
OWNER_SHA256 = "975d00eb0b06f353553de54b15ddfb3edc2a81ac5880009379f3e2b654574068"
MAX_PROOF_BYTES = 1024
BINARY_PAYLOAD = bytes(range(256)) * 3
BINARY_SHA256 = "f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363"
_BINARY_LEAF = ROOT + "/binary-v1.bin"
_PREFIX = "LC_ALL=C; export LC_ALL; umask 077; set -C; "


class TransferContractRefused(ValueError):
    def __init__(self):
        super().__init__("transfer_contract_invalid")


def _require(condition):
    if not condition:
        raise TransferContractRefused()


def _uid(value):
    _require(type(value) is int and 10000 <= value <= (1 << 31) - 1)
    return str(value)


def _leaf(mode):
    _require(type(mode) is str and mode in MODES)
    return ROOT + {"CAT": "/cat.bin", "DD_1M": "/dd-1m.bin", "SHELL_CAT": "/shell-cat.bin"}[mode]


def fixture_block():
    """Allocate one immutable original 1MiB block, never a complete 1GiB source."""
    return hashlib.shake_256(b"LocalLore original transfer fixture v1\n").digest(BLOCK_BYTES)


def _directory(path, uid):
    return ("test -d " + path + " && test ! -L " + path +
            " && test \"$(stat -c %u " + path + ")\" -eq " + uid)


def _regular(path, uid):
    return ("test -f " + path + " && test ! -L " + path +
            " && test \"$(stat -c %u " + path + ")\" -eq " + uid +
            " && test \"$(stat -c %h " + path + ")\" -eq 1")


def _guard(uid):
    return ("test \"$(id -u)\" -eq " + uid + " && " + _directory("no_backup", uid) + " && " +
            _directory(ROOT, uid) + " && " + _regular(OWNER, uid) +
            " && test \"$(stat -c %s " + OWNER + ")\" -eq " + str(len(OWNER_CONTENT)) +
            " && test \"$(sha256sum " + OWNER + ")\" = '" + OWNER_SHA256 + "  " + OWNER + "'")


def _command(script):
    return ("run-as", APP, "sh", "-c", _PREFIX + script)


def create_command(uid):
    """Exclusively create this root and marker; preserve every prior destination."""
    uid = _uid(uid)
    script = "test \"$(id -u)\" -eq " + uid
    script += " && if test -e no_backup || test -L no_backup; then " + _directory("no_backup", uid)
    script += "; else mkdir no_backup; fi && " + _directory("no_backup", uid)
    script += " && test ! -e " + ROOT + " && test ! -L " + ROOT + " && mkdir " + ROOT
    script += " && " + _directory(ROOT, uid)
    script += " && printf '%s\\n' 'locallore-receipt-transfer-probe-v1' > " + OWNER
    script += " && " + _guard(uid)
    return _command(script)


def write_command(uid, mode):
    """One fixed stdin-to-new-file command; noclobber applies to redirection."""
    uid, leaf = _uid(uid), _leaf(mode)
    command = "dd bs=1048576" if mode == "DD_1M" else "cat"
    return _command(_guard(uid) + " && test ! -e " + leaf + " && test ! -L " + leaf +
                    " && " + command + " > " + leaf)


def proof_command(uid, mode):
    """Return only UID|SIZE and exact sha256sum output for the fixed regular leaf."""
    uid, leaf = _uid(uid), _leaf(mode)
    return _command(_guard(uid) + " && " + _regular(leaf, uid) +
                    " && stat -c '%u|%s' " + leaf + " && sha256sum " + leaf)


def parse_proof(raw, uid, mode):
    """Decode the exact fixed two-line metadata, not command/remote-exit authority."""
    uid_text, leaf = _uid(uid), _leaf(mode)
    _require(type(raw) is bytes and 0 < len(raw) <= MAX_PROOF_BYTES)
    expected = (uid_text + "|" + str(SOURCE_BYTES) + "\n" + SOURCE_SHA256 + "  " + leaf + "\n").encode("ascii")
    _require(raw == expected or raw == expected.replace(b"\n", b"\r\n"))
    return {"version": 1, "mode": mode, "bytes": SOURCE_BYTES, "sha256": SOURCE_SHA256, "uid": uid}


def binary_write_command(uid):
    """Fixed tiny binary gate only; transport mapping remains coordinator-owned."""
    uid = _uid(uid)
    return _command(_guard(uid) + " && test ! -e " + _BINARY_LEAF + " && test ! -L " + _BINARY_LEAF +
                    " && cat > " + _BINARY_LEAF)


def binary_proof_command(uid):
    uid = _uid(uid)
    return _command(_guard(uid) + " && " + _regular(_BINARY_LEAF, uid) +
                    " && stat -c '%u|%s' " + _BINARY_LEAF + " && sha256sum " + _BINARY_LEAF)


def parse_binary_proof(raw, uid):
    """Only the fixed 768-byte SHELL_BINARY proof; no configurable size or path."""
    uid_text = _uid(uid)
    _require(type(raw) is bytes and 0 < len(raw) <= MAX_PROOF_BYTES)
    expected = (uid_text + "|768\n" + BINARY_SHA256 + "  " + _BINARY_LEAF + "\n").encode("ascii")
    _require(raw == expected or raw == expected.replace(b"\n", b"\r\n"))
    return {"version": 1, "mode": "SHELL_BINARY", "bytes": 768, "sha256": BINARY_SHA256, "uid": uid}
