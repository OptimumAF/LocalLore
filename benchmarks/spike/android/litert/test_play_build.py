"""Opt-in build isolation tests; these do not execute a runtime or Android binary."""
from pathlib import Path
import unittest
from unittest.mock import patch
import play_build


class PlayBuildTests(unittest.TestCase):
    def test_capacity_fault_compiler_macros_cannot_leak_from_parent_environment(self):
        with patch.dict(play_build.os.environ, {"LIBSQLITE3_FLAGS": "-DSQLITE_MAX_PAGE_COUNT=1"}):
            _, env = play_build.native_command("x86_64-linux-android", Path("out"), Path("linker"), Path("ndk"))
        self.assertNotIn("LIBSQLITE3_FLAGS", env)

    def test_both_abis_explicitly_enable_only_the_experiment_and_keep_offline_pins(self):
        for target in play_build.TARGETS.values():
            argv, env = play_build.native_command(target, Path("output with spaces"), Path("linker"), Path("NDK's folder"))
            self.assertIn("--offline", argv)
            self.assertIn("--locked", argv)
            self.assertIn("+1.93.1", argv)
            self.assertEqual(argv[argv.index("--features") + 1], "play-probe")
            self.assertEqual(argv[argv.index("--target") + 1], target)
            self.assertEqual(env["LOCALLORE_ANDROID_CLANG"], str(Path("NDK's folder/bin/clang.exe")))
            self.assertIn("--target=" + target + "26", env["CFLAGS_" + target])
            self.assertIn("max-page-size=16384", env["CARGO_ENCODED_RUSTFLAGS"])
            self.assertIn('"--sysroot=', env["CFLAGS_" + target])


if __name__ == "__main__":
    unittest.main()
