"""Synthetic metadata safety tests; never native-runtime execution evidence."""

import io
import struct
import unittest
import warnings
import zipfile

import audit


def elf(machine=62, api=26, alignment=16384):
    data = bytearray(1024)
    data[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<H", data, 18, machine)
    struct.pack_into("<Q", data, 32, 64)
    struct.pack_into("<HH", data, 54, 56, 3)
    struct.pack_into("<IIQQQQQQ", data, 64, 1, 5, 0, 0, 0, 1024, 1024, alignment)
    struct.pack_into("<IIQQQQQQ", data, 120, 4, 4, 256, 256, 256, 152, 152, 4)
    struct.pack_into("<IIQQQQQQ", data, 176, 2, 6, 512, 512, 512, 64, 64, 8)
    struct.pack_into("<III", data, 256, 8, 132, 1)
    data[268:276] = b"Android\0"
    struct.pack_into("<I", data, 276, api)
    data[280:284] = b"r29\0"
    data[344:353] = b"14206865\0"
    strings = b"\0libc.so\0"
    data[700:700 + len(strings)] = strings
    for index, entry in enumerate([(5, 700), (10, len(strings)), (1, 1), (0, 0)]):
        struct.pack_into("<qQ", data, 512 + index * 16, *entry)
    return bytes(data)


def aar(abis=("x86_64",), minimum=24, native=None, duplicate=False):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("AndroidManifest.xml", '<manifest xmlns:android="http://schemas.android.com/apk/res/android"><uses-sdk android:minSdkVersion="' + str(minimum) + '"/><application/></manifest>')
        classes = io.BytesIO()
        with zipfile.ZipFile(classes, "w") as jar:
            jar.writestr("Synthetic.class", b"\xca\xfe\xba\xbe\x00\x00\x00\x41")
        archive.writestr("classes.jar", classes.getvalue())
        for name in ("LICENSE", "THIRD_PARTY_NOTICE.txt"):
            archive.writestr(name, b"synthetic")
        for abi in abis:
            archive.writestr("jni/" + abi + "/liblitertlm_jni.so", native or elf(62 if abi == "x86_64" else 183))
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr("classes.jar", b"duplicate")
    return output.getvalue()


class AuditTests(unittest.TestCase):
    def test_native_identity_and_dependencies_are_inspected(self):
        result = audit.elf_info(elf())
        self.assertEqual(result["abi"], "x86_64")
        self.assertEqual(result["android_ident"], {"api": 26, "ndk": "r29", "ndk_build": "14206865"})
        self.assertEqual(result["needed"], ["libc.so"])
        self.assertTrue(result["elf_16k_load_alignment"])

    def test_manifest_is_not_enough_for_native_api_floor(self):
        result = audit.inspect_aar(aar(), "x86_64", 25)
        self.assertEqual(result["manifest_min_sdk"], 24)
        self.assertEqual(result["conservative_api_floor"], 26)
        self.assertEqual(result["artifact_gate"], "blocked_api")
        result = audit.inspect_aar(aar(), "x86_64", 35)
        self.assertEqual(result["artifact_gate"], "eligible_for_runtime_test")
        self.assertFalse(result["runtime_load_verified"])
        self.assertEqual(result["classfile_majors"], [65])

    def test_absent_emulator_abi_cannot_be_claimed_supported(self):
        result = audit.inspect_aar(aar(("arm64-v8a",)), "x86_64", 35)
        self.assertEqual(result["artifact_gate"], "blocked_abi")
        self.assertIsNone(result["conservative_api_floor"])
        self.assertFalse(result["runtime_load_verified"])

    def test_native_path_cannot_disguise_machine(self):
        with self.assertRaisesRegex(audit.AuditError, "native_path_machine_mismatch"):
            audit.inspect_aar(aar(native=elf(machine=183)), "x86_64", 35)

    def test_weak_alignment_never_claims_16k_support(self):
        self.assertFalse(audit.elf_info(elf(alignment=4096))["elf_16k_load_alignment"])

    def test_invalid_binary_and_duplicate_archive_fail_closed(self):
        for data in (b"", b"\x7fELF", elf()[:600]):
            with self.subTest(length=len(data)), self.assertRaises(audit.AuditError):
                audit.elf_info(data)
        with self.assertRaisesRegex(audit.AuditError, "duplicate_zip_entries"):
            audit.inspect_aar(aar(duplicate=True), "x86_64", 35)

    def test_artifact_identity_rejected_before_metadata(self):
        with self.assertRaisesRegex(audit.AuditError, "artifact_identity_mismatch"):
            audit.audit(aar(), b"untrusted", "x86_64", 35)

    def test_target_abi_and_api_strict(self):
        for abi, api in (("armv7", 35), ("x86_64", True), ("x86_64", 0)):
            with self.subTest(abi=abi, api=api), self.assertRaisesRegex(audit.AuditError, "invalid_target"):
                audit.inspect_aar(aar(), abi, api)


if __name__ == "__main__":
    unittest.main()
