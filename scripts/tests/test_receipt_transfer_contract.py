"""Original synthetic command/proof tests; never execute shell or transfers.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import importlib.util
from pathlib import Path
import shlex
import sys
import types
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("transfer_contract_under_test",
    Path(__file__).resolve().parents[2] / "benchmarks/receipt_transfer_contract.py")
c = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(c)
UID = 12345
PRIVATE = "ORIGINAL_PRIVATE_TRANSFER_CANARY"


def leaf(mode):
    return c.ROOT + {"CAT": "/cat.bin", "DD_1M": "/dd-1m.bin", "SHELL_CAT": "/shell-cat.bin"}[mode]


def proof(mode="CAT", uid=UID, ending="\n"):
    return (str(uid) + "|1073741824" + ending + c.SOURCE_SHA256 + "  " + leaf(mode) + ending).encode("ascii")


def binary_proof(uid=UID, ending="\n"):
    return (str(uid) + "|768" + ending + c.BINARY_SHA256 + "  " + c.ROOT + "/binary-v1.bin" + ending).encode("ascii")


class HostileUid:
    def __str__(self): raise AssertionError(PRIVATE)
    def __repr__(self): raise AssertionError(PRIVATE)


class TransferContractTest(unittest.TestCase):
    def refuses(self, block):
        with self.assertRaises(c.TransferContractRefused) as caught:
            block()
        self.assertEqual("transfer_contract_invalid", str(caught.exception)); self.assertIsNone(caught.exception.__context__)
        self.assertNotIn(PRIVATE, str(caught.exception))

    def test_constants_pin_original_fixture_and_no_caller_source_selector(self):
        self.assertEqual((1048576, 1073741824, ("CAT", "DD_1M", "SHELL_CAT")), (c.BLOCK_BYTES, c.SOURCE_BYTES, c.MODES))
        self.assertEqual("no_backup/receipt-transfer-probe-v1", c.ROOT)
        self.assertEqual("org.locallore.app.modelvolumeverify", c.APP)
        self.assertEqual("93b6ba41cf54e72a26ab955cdf953420847be6229f592ea79770362c91558c3f", c.SOURCE_SHA256)
        self.assertEqual(1024, c.MAX_PROOF_BYTES); self.assertEqual(1024, c.SOURCE_BYTES // c.BLOCK_BYTES)

    def test_fixture_allocates_only_one_immutable_block_with_exact_seed(self):
        block = c.fixture_block()
        self.assertIs(type(block), bytes); self.assertEqual(c.BLOCK_BYTES, len(block))
        self.assertEqual("6e2c24fce7a46663078ec8a09baf1b92980e6cd886f32414302b5811ec89f60b", hashlib.sha256(block).hexdigest())
        with self.assertRaises(TypeError): block[0] = 1
        class Shake:
            def digest(self, size):
                self_test.assertEqual(1048576, size)
                return b"tiny explicit unit seam"
        self_test = self
        with patch.object(c.hashlib, "shake_256", return_value=Shake()) as observed:
            self.assertEqual(b"tiny explicit unit seam", c.fixture_block())
        observed.assert_called_once_with(b"LocalLore original transfer fixture v1\n")

    def test_uid_bounds_and_all_invalid_types_refuse_before_formatting(self):
        for uid in [10000, (1 << 31) - 1]:
            for command in [c.create_command(uid), c.write_command(uid, "CAT"), c.proof_command(uid, "DD_1M"),
                            c.binary_write_command(uid), c.binary_proof_command(uid)]:
                self.assertIn('test "$(id -u)" -eq ' + str(uid), command[-1])
            self.assertEqual(uid, c.parse_proof(proof(uid=uid), uid, "CAT")["uid"])
            self.assertEqual(uid, c.parse_binary_proof(binary_proof(uid), uid)["uid"])
        for uid in [True, False, None, 9999, 1 << 31, -1, 10000.0, "10000", "10000;id", [], {}, HostileUid()]:
            for make in [lambda: c.create_command(uid), lambda: c.write_command(uid, "CAT"),
                         lambda: c.proof_command(uid, "CAT"), lambda: c.parse_proof(proof(), uid, "CAT"),
                         lambda: c.binary_write_command(uid), lambda: c.binary_proof_command(uid),
                         lambda: c.parse_binary_proof(binary_proof(), uid)]:
                self.refuses(make)

    def test_mode_is_exact_closed_string_not_shell_or_path_input(self):
        class Mode(str): pass
        for mode in [None, True, 1, [], {}, b"CAT", "cat", "DD", "SHELL_BINARY", "", "DD_1M;id", "../cat.bin", "CAT\n", Mode("CAT")]:
            self.refuses(lambda: c.write_command(UID, mode)); self.refuses(lambda: c.proof_command(UID, mode))
            self.refuses(lambda: c.parse_proof(proof(), UID, mode))

    def test_fixed_run_as_tuple_locale_umask_and_noclobber_on_every_command(self):
        commands = [c.create_command(UID), c.binary_write_command(UID), c.binary_proof_command(UID)] + \
            [make(UID, mode) for mode in c.MODES for make in [c.write_command, c.proof_command]]
        for command in commands:
            self.assertIs(type(command), tuple); self.assertEqual(5, len(command))
            self.assertEqual(("run-as", c.APP, "sh", "-c"), command[:4])
            self.assertTrue(command[-1].startswith("LC_ALL=C; export LC_ALL; umask 077; set -C; "))
            self.assertNotIn(">|", command[-1]); self.assertNotIn("set +C", command[-1])
            words = shlex.split(command[-1])
            for forbidden in ["rm", "mv", "chmod", "chown", "touch", "truncate", "cp", "tee", "ln", "mkfifo", "sudo", "su", "pm", "am"]:
                self.assertNotIn(forbidden, words)

    def test_create_checks_parent_and_exclusively_creates_only_root_and_marker(self):
        script = c.create_command(UID)[-1]
        self.assertIn("if test -e no_backup || test -L no_backup; then ", script)
        self.assertIn("else mkdir no_backup; fi", script)
        self.assertIn("test ! -e " + c.ROOT + " && test ! -L " + c.ROOT + " && mkdir " + c.ROOT, script)
        self.assertNotIn("mkdir -p", script)
        self.assertIn("printf '%s\\n' 'locallore-receipt-transfer-probe-v1' > " + c.OWNER, script)
        self.assertLess(script.index('test "$(id -u)"'), script.index("mkdir no_backup"))
        self.assertLess(script.index("set -C"), script.index("printf"))
        self.assertNotIn("cat.bin", script); self.assertNotIn("dd-1m.bin", script)
        self.assertNotIn("binary-v1.bin", script)

    def test_marker_is_exact_bounded_owned_regular_and_hardlink_free(self):
        self.assertEqual(c.ROOT + "/owner-v1.txt", c.OWNER)
        self.assertEqual(b"locallore-receipt-transfer-probe-v1\n", c.OWNER_CONTENT)
        self.assertEqual(36, len(c.OWNER_CONTENT)); self.assertEqual(c.OWNER_SHA256, hashlib.sha256(c.OWNER_CONTENT).hexdigest())
        for mode in c.MODES:
            for make in [c.write_command, c.proof_command]:
                script = make(UID, mode)[-1]
                for directory in ["no_backup", c.ROOT]:
                    self.assertIn("test -d " + directory + " && test ! -L " + directory, script)
                    self.assertIn('test "$(stat -c %u ' + directory + ')" -eq 12345', script)
                self.assertIn("test -f " + c.OWNER + " && test ! -L " + c.OWNER, script)
                self.assertIn('test "$(stat -c %u ' + c.OWNER + ')" -eq 12345', script)
                self.assertIn('test "$(stat -c %h ' + c.OWNER + ')" -eq 1', script)
                self.assertIn('test "$(stat -c %s ' + c.OWNER + ')" -eq 36', script)
                self.assertIn('test "$(sha256sum ' + c.OWNER + ')" = \'' + c.OWNER_SHA256 + "  " + c.OWNER + "'", script)
        for tampered in [c.OWNER_CONTENT[:-1], c.OWNER_CONTENT[:-1] + b"\0", c.OWNER_CONTENT + b"\n", b"foreign\n"]:
            self.assertNotEqual(c.OWNER_SHA256, hashlib.sha256(tampered).hexdigest())

    def test_modes_share_guards_and_only_fixed_stdin_copy_primitive_changes(self):
        cat, dd = c.write_command(UID, "CAT")[-1], c.write_command(UID, "DD_1M")[-1]
        self.assertTrue(cat.endswith(" && cat > " + leaf("CAT")))
        self.assertTrue(dd.endswith(" && dd bs=1048576 > " + leaf("DD_1M")))
        self.assertEqual(cat, dd.replace("dd-1m.bin", "cat.bin").replace("dd bs=1048576", "cat"))
        shell_cat = c.write_command(UID, "SHELL_CAT")[-1]
        self.assertEqual(cat, shell_cat.replace("shell-cat.bin", "cat.bin"))
        for mode, script in [("CAT", cat), ("DD_1M", dd), ("SHELL_CAT", shell_cat)]:
            self.assertIn("test ! -e " + leaf(mode) + " && test ! -L " + leaf(mode), script)
            self.assertEqual(1, script.count(" > "))
            for fragment in [" if=", " of=", " count=", " iflag=", " conv=", " oflag="]:
                self.assertNotIn(fragment, script)

    def test_proof_command_is_metadata_only_for_exact_regular_uid_and_fixed_leaf(self):
        for mode in c.MODES:
            script, path = c.proof_command(UID, mode)[-1], leaf(mode)
            self.assertTrue(script.endswith(" && stat -c '%u|%s' " + path + " && sha256sum " + path))
            self.assertIn("test -f " + path + " && test ! -L " + path, script)
            self.assertIn('test "$(stat -c %u ' + path + ')" -eq 12345', script)
            self.assertIn('test "$(stat -c %h ' + path + ')" -eq 1', script)
            self.assertNotIn("cat ", script); self.assertNotIn("dd ", script); self.assertNotIn(" > ", script)

    def test_exact_two_lines_lf_or_crlf_return_only_fixed_metadata(self):
        for mode in c.MODES:
            for ending in ["\n", "\r\n"]:
                result = c.parse_proof(proof(mode, ending=ending), UID, mode)
                self.assertEqual({"version": 1, "mode": mode, "bytes": c.SOURCE_BYTES, "sha256": c.SOURCE_SHA256, "uid": UID}, result)
                self.assertNotIn("success", result); self.assertNotIn("remote_exit_status_known", result)
                self.assertNotIn("destination_verified", result)

    def test_cross_mode_uid_size_digest_and_paths_are_never_adopted(self):
        raw = proof()
        self.refuses(lambda: c.parse_proof(raw, UID, "DD_1M")); self.refuses(lambda: c.parse_proof(raw, UID + 1, "CAT"))
        self.refuses(lambda: c.parse_proof(raw, UID, "SHELL_CAT"))
        for changed in [raw.replace(b"1073741824", b"1073741823"), raw.replace(b"1073741824", b"1073741825"),
                        raw.replace(c.SOURCE_SHA256.encode(), b"0" * 64), raw.replace(c.SOURCE_SHA256.encode(), c.SOURCE_SHA256.upper().encode()),
                        raw.replace(leaf("CAT").encode(), ("./" + leaf("CAT")).encode()),
                        raw.replace(leaf("CAT").encode(), ("/data/user/0/foreign/" + leaf("CAT")).encode()),
                        raw.replace(leaf("CAT").encode(), (c.ROOT + "/../cat.bin").encode()),
                        raw.replace(b"  " + leaf("CAT").encode(), b" *" + leaf("CAT").encode())]:
            self.refuses(lambda: c.parse_proof(changed, UID, "CAT"))

    def test_extra_duplicate_malformed_framing_and_non_ascii_refuse(self):
        raw = proof(); first, second, _ = raw.split(b"\n")
        for changed in [b"", raw[:-1], b" " + raw, raw + b"\n", raw + raw, first + b"\n" + first + b"\n" + second + b"\n",
                        raw.replace(b"\n", b"\r\n", 1), raw.replace(b"\n", b"\r\r\n"), raw.replace(b"\n", b"\v"),
                        raw.replace(b"|", b":"), raw.replace(b"12345", b"012345"), raw.replace(b"12345", b"+12345"),
                        raw.replace(b"1073741824", b"1.073741824e9"), raw.replace(b"  ", b" "), raw + b"PRIVATE=canary\n",
                        raw + "雪".encode(), b"x" * 1025]:
            self.refuses(lambda: c.parse_proof(changed, UID, "CAT"))
        for invalid in [None, True, 1, raw.decode(), bytearray(raw), memoryview(raw)]:
            self.refuses(lambda: c.parse_proof(invalid, UID, "CAT"))

    def test_fixed_binary_payload_includes_every_byte_without_text_translation(self):
        self.assertIs(type(c.BINARY_PAYLOAD), bytes); self.assertEqual(768, len(c.BINARY_PAYLOAD))
        self.assertEqual(bytes(range(256)) * 3, c.BINARY_PAYLOAD)
        self.assertEqual("f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363", c.BINARY_SHA256)
        self.assertEqual(c.BINARY_SHA256, hashlib.sha256(c.BINARY_PAYLOAD).hexdigest())
        for value in [0, 10, 13, 26, 255]: self.assertEqual(3, c.BINARY_PAYLOAD.count(bytes([value])))
        for translated in [c.BINARY_PAYLOAD.replace(b"\n", b"\r\n"), c.BINARY_PAYLOAD.replace(b"\r", b""),
                           c.BINARY_PAYLOAD.split(b"\x1a")[0], c.BINARY_PAYLOAD.replace(b"\0", b"")]:
            self.assertNotEqual(c.BINARY_SHA256, hashlib.sha256(translated).hexdigest())

    def test_binary_command_uses_same_owner_guards_and_own_exclusive_leaf(self):
        path = c.ROOT + "/binary-v1.bin"
        script = c.binary_write_command(UID)[-1]
        self.assertEqual(c.write_command(UID, "CAT")[-1].replace("cat.bin", "binary-v1.bin"), script)
        self.assertIn("test ! -e " + path + " && test ! -L " + path, script)
        self.assertTrue(script.endswith(" && cat > " + path))
        self.assertEqual(c.proof_command(UID, "CAT")[-1].replace("cat.bin", "binary-v1.bin"), c.binary_proof_command(UID)[-1])

    def test_binary_proof_only_accepts_fixed_768_digest_uid_and_path(self):
        for ending in ["\n", "\r\n"]:
            self.assertEqual({"version": 1, "mode": "SHELL_BINARY", "bytes": 768, "sha256": c.BINARY_SHA256, "uid": UID},
                             c.parse_binary_proof(binary_proof(ending=ending), UID))
        raw = binary_proof()
        for invalid in [proof(), raw[:-1], raw + raw, raw.replace(b"|768", b"|767"), raw.replace(b"|768", b"|769"),
                        raw.replace(b"|768", b"|1073741824"), raw.replace(b"binary-v1.bin", b"cat.bin"),
                        raw.replace(c.BINARY_SHA256.encode(), c.SOURCE_SHA256.encode()), raw.replace(b"12345", b"12346"),
                        raw.replace(b"\n", b"\r\n", 1), raw + b"\n", b"x" * 1025, None, True, raw.decode()]:
            self.refuses(lambda: c.parse_binary_proof(invalid, UID))
        for mode in c.MODES: self.refuses(lambda: c.parse_proof(raw, UID, mode))

    def test_module_import_has_no_io_no_fixture_hashing_and_no_cli(self):
        code = SPEC.loader.get_code(SPEC.name)
        probe = types.ModuleType("transfer_contract_inert_probe")
        with patch("builtins.open", side_effect=AssertionError(PRIVATE)), patch.object(Path, "open", side_effect=AssertionError(PRIVATE)), \
             patch.object(hashlib, "shake_256", side_effect=AssertionError("Fixture allocated at import")):
            exec(code, probe.__dict__)
        for name in ["main", "Path", "open", "subprocess", "os", "sys"]:
            self.assertFalse(hasattr(probe, name))


if __name__ == "__main__":
    unittest.main()
