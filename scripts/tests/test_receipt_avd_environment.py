"""Host-only adversarial tests. No Android SDK or emulator is executed.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from benchmarks import receipt_avd_environment as env

# Exact 3201-byte generated profile from the stopped prepare; no device/model data.
# SHA256 5774eccd6c920ec3157a7a43710620645284c7e064a9f06933915f12d05aa6ac
ACTUAL_CMDLINE_11_CONFIG = br"""
PlayStore.enabled=no
abi.type=x86_64
avd.id=<build>
avd.ini.encoding=UTF-8
avd.name=<build>
disk.cachePartition=yes
disk.cachePartition.size=66MB
disk.dataPartition.path=<temp>
disk.dataPartition.size=800M
disk.systemPartition.size=0
disk.vendorPartition.size=0
fastboot.forceChosenSnapshotBoot=no
fastboot.forceColdBoot=no
fastboot.forceFastBoot=yes
firstboot.bootFromDownloadableSnapshot=yes
firstboot.bootFromLocalSnapshot=yes
firstboot.saveToLocalSnapshot=yes
hw.accelerometer=yes
hw.accelerometer_uncalibrated=yes
hw.arc=no
hw.arc.autologin=no
hw.audioInput=yes
hw.audioOutput=yes
hw.battery=yes
hw.camera.back=emulated
hw.camera.front=none
hw.cpu.arch=x86_64
hw.cpu.ncore=4
hw.dPad=yes
hw.display1.density=0
hw.display1.flag=0
hw.display1.height=0
hw.display1.width=0
hw.display1.xOffset=-1
hw.display1.yOffset=-1
hw.display2.density=0
hw.display2.flag=0
hw.display2.height=0
hw.display2.width=0
hw.display2.xOffset=-1
hw.display2.yOffset=-1
hw.display3.density=0
hw.display3.flag=0
hw.display3.height=0
hw.display3.width=0
hw.display3.xOffset=-1
hw.display3.yOffset=-1
hw.displayRegion.0.1.height=0
hw.displayRegion.0.1.width=0
hw.displayRegion.0.1.xOffset=-1
hw.displayRegion.0.1.yOffset=-1
hw.displayRegion.0.2.height=0
hw.displayRegion.0.2.width=0
hw.displayRegion.0.2.xOffset=-1
hw.displayRegion.0.2.yOffset=-1
hw.displayRegion.0.3.height=0
hw.displayRegion.0.3.width=0
hw.displayRegion.0.3.xOffset=-1
hw.displayRegion.0.3.yOffset=-1
hw.gltransport=pipe
hw.gltransport.asg.dataRingSize=32768
hw.gltransport.asg.writeBufferSize=1048576
hw.gltransport.asg.writeStepSize=4096
hw.gltransport.drawFlushInterval=800
hw.gps=yes
hw.gpu.enabled=no
hw.gpu.mode=auto
hw.gsmModem=yes
hw.gyroscope=yes
hw.hotplug_multi_display=no
hw.initialOrientation=portrait
hw.keyboard=no
hw.keyboard.charmap=qwerty2
hw.keyboard.lid=yes
hw.lcd.backlight=yes
hw.lcd.circular=false
hw.lcd.density=160
hw.lcd.depth=16
hw.lcd.height=640
hw.lcd.vsync=60
hw.lcd.width=320
hw.mainKeys=yes
hw.multi_display_window=no
hw.ramSize=96M
hw.rotaryInput=no
hw.screen=multi-touch
hw.sdCard=yes
hw.sensor.hinge=no
hw.sensor.hinge.count=0
hw.sensor.hinge.fold_to_displayRegion.0.1_at_posture=1
hw.sensor.hinge.resizable.config=1
hw.sensor.hinge.sub_type=0
hw.sensor.hinge.type=0
hw.sensor.roll=no
hw.sensor.roll.count=0
hw.sensor.roll.resize_to_displayRegion.0.1_at_posture=6
hw.sensor.roll.resize_to_displayRegion.0.2_at_posture=6
hw.sensor.roll.resize_to_displayRegion.0.3_at_posture=6
hw.sensors.gyroscope_uncalibrated=yes
hw.sensors.heart_rate=no
hw.sensors.humidity=yes
hw.sensors.light=yes
hw.sensors.magnetic_field=yes
hw.sensors.magnetic_field_uncalibrated=yes
hw.sensors.orientation=yes
hw.sensors.pressure=yes
hw.sensors.proximity=yes
hw.sensors.rgbclight=no
hw.sensors.temperature=yes
hw.sensors.wrist_tilt=no
hw.trackBall=yes
hw.useext4=yes
image.sysdir.1=system-images\android-35\google_apis\x86_64\
kernel.newDeviceNaming=autodetect
kernel.supportsYaffs2=autodetect
runtime.network.latency=none
runtime.network.speed=full
sdcard.size=512 MB
showDeviceFrame=yes
tag.display=Google APIs
tag.id=google_apis
test.delayAdbTillBootComplete=0
test.monitorAdb=0
test.quitAfterBootTimeOut=-1
userdata.useQcow2=no
vm.heapSize=64M

""".strip(b"\n") + b"\n"


@unittest.skipUnless(os.name == "nt", "Windows-only AVD environment ownership")
class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="receipt-avd-host-test-", dir="D:/" if os.name == "nt" else None)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "new-avd"
        self.sdk = self.base / "sdk"
        self.java = self.base / "jdk"
        self.token = self.base / "fake-token"
        self.token.write_bytes(b"test-only-not-an-emulator-credential")
        self.token_patch = mock.patch.object(env, "token_path", return_value=str(self.token))
        self.token_patch.start()

    def tearDown(self):
        self.token_patch.stop()
        self.tmp.cleanup()

    def proposal(self, phase="prepare"):
        # No dependency on actual installed SDK or credentials in any host test.
        files = [Path(env.__file__).resolve(), Path(env.host.__file__).resolve()]
        self.java.mkdir(exist_ok=True)
        (self.sdk / "licenses").mkdir(parents=True, exist_ok=True)
        for relative in ("platform-tools/adb.exe", "emulator/emulator.exe",
                         "cmdline-tools/latest/bin/avdmanager.bat",
                         "system-images/android-35/google_apis/x86_64/data/empty_data_disk"):
            path = self.sdk / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fake SDK fixture")
            files.append(path)
        value = {"version": 1, "phase": phase, "avd_name": env.NAME,
                 "serial": "emulator-5592", "console_port": 5592, "sdk": str(self.sdk),
                 "java_home": str(self.java), "paths": env.paths(self.root),
                 "adb_path": str(self.sdk / "platform-tools/adb.exe"),
                 "token": env.token_binding(self.token), "old_avd": env.old_registry_snapshot(),
                 "bindings": [env.binding(x) for x in files],
                 "userdata_mib": 12288, "sdcard_mib": 8192, "memory_mib": 2048, "cores": 2,
                 "host_free_min": {"C:": 16 * env.GIB, "D:": 40 * env.GIB},
                 "host_available_memory_min": 4 * env.GIB,
                 "allow_environment_calls": False, "root_go_pending": True}
        return value

    def files(self, value, name="proposal.json", authorized=True):
        proposal = self.base / name
        env.create_json(proposal, value)
        auth = self.base / (name + ".auth")
        env.create_json(auth, {"version": 1, "phase": value["phase"],
                             "proposal_sha256": env.digest(proposal),
                             "allow_environment_calls": authorized, "root_go_pending": not authorized})
        return proposal, auth

    def prepared_run(self, real_candidate=False):
        prepare = self.proposal()
        if real_candidate:
            prepare.update(memory_mib=8192, host_available_memory_min=12 * env.GIB)
        initial, _ = self.files(prepare, "prepare.json")
        self.root.mkdir()
        content = Path(prepare["paths"]["content"])
        content.mkdir(parents=True)
        registry = Path(prepare["paths"]["registry"])
        registry.mkdir()
        immutable = []
        for path in (content / "config.ini", content / "config.created.ini", registry / (env.NAME + ".ini")):
            path.write_bytes(b"fixed fixture config")
            immutable.append(env.binding(path))
        sd = content / "sdcard.img"
        sd.write_bytes(b"initial guest disk fixture")
        record = {"version": 1, "proposal_sha256": env.digest(initial), "avd_name": env.NAME,
                  "immutable": immutable, "initial_sdcard": env.binding(sd), "userdata_absent": True,
                  "guest_boot_verified": False, "facts": {}}
        receipt = self.root / "prepared-v1.json"
        env.create_json(receipt, record)
        closure = self.root / "prepare-result-v1.json"
        env.create_json(closure, {"version": 1, "proposal_sha256": env.digest(initial), "status": "completed",
                                 "closure_verified": True, "child_cleanup_complete": True, "prepared_created": True})
        run = dict(prepare, phase="run", prepare_proposal=env.binding(initial),
                   prepared=env.binding(receipt), prepare_result=env.binding(closure), max_seconds=1200)
        proposal, auth = self.files(run, "run.json")
        return run, proposal, auth

    def descriptor(self, run, proposal):
        now = time.time()
        identity = {"pid": 100, "creation_filetime": 200, "executable": sys.executable}
        return {"version": 1, "proposal_sha256": env.digest(proposal),
                "prepared_sha256": run["prepared"]["sha256"], "avd_name": env.NAME,
                "serial": run["serial"], "console_port": env.PORT, "adb_path": run["adb_path"],
                "root": str(self.root), "content": run["paths"]["content"], "registry": run["paths"]["registry"],
                "owner": identity, "worker": dict(identity, pid=101),
                "launcher": dict(identity, pid=102, executable=str(self.sdk / "emulator/emulator.exe")),
                "started_epoch": now - 1, "deadline_epoch": now + 1198, "guest_boot_verified": False}

    def lease(self, change=None):
        run, proposal, auth = self.prepared_run()
        descriptor = self.descriptor(run, proposal)
        if change:
            change(descriptor)
        path = self.root / "running-v1.json"
        env.create_json(path, descriptor)
        mapping = {x["pid"]: x for x in (descriptor["owner"], descriptor["worker"], descriptor["launcher"])}
        with mock.patch.object(env, "process_identity", side_effect=lambda pid: mapping[pid]):
            lease = env.open_live_owner(proposal, path, env.digest(path))
        return lease, mapping

    def test_unauthorized_prepare_has_no_files_or_sdk_child(self):
        p, a = self.files(self.proposal(), authorized=False)
        with mock.patch.object(env.host, "run_process") as child, self.assertRaisesRegex(env.EnvironmentRefused, "not_authorized"):
            env.prepare(p, a)
        child.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_wrong_phase_authorization_is_rejected_before_mutation(self):
        value = self.proposal()
        p, a = self.files(value)
        auth = env.read_json(a); auth["phase"] = "run"; a.write_bytes(env.encoded(auth))
        with self.assertRaisesRegex(env.EnvironmentRefused, "not_authorized"):
            env.prepare(p, a)
        self.assertFalse(self.root.exists())

    def test_boolean_authorization_fields_not_integer_substitutes(self):
        p, a = self.files(self.proposal())
        auth = env.read_json(a); auth["allow_environment_calls"] = 1; a.write_bytes(env.encoded(auth))
        with self.assertRaisesRegex(env.EnvironmentRefused, "not_authorized"):
            env.prepare(p, a)
        self.assertFalse(self.root.exists())

    def test_binding_drift_precedes_target_creation(self):
        value = self.proposal(); p, a = self.files(value)
        Path(value["adb_path"]).write_bytes(b"replaced")
        with self.assertRaisesRegex(env.EnvironmentRefused, "binding_changed"):
            env.prepare(p, a)
        self.assertFalse(self.root.exists())

    def test_missing_source_binding_rejected(self):
        value = self.proposal(); value["bindings"] = value["bindings"][1:]
        with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_proposal"):
            env.validate_proposal(value, "prepare")

    def test_existing_target_not_overwritten(self):
        p, a = self.files(self.proposal()); self.root.mkdir()
        sentinel = self.root / "sentinel"; sentinel.write_bytes(b"preserve")
        with mock.patch.object(env.host, "run_process") as child, self.assertRaisesRegex(env.EnvironmentRefused, "target_exists"):
            env.prepare(p, a)
        child.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b"preserve")

    def test_low_host_capacity_precedes_creation(self):
        p, a = self.files(self.proposal())
        with mock.patch.object(env, "resource_facts", side_effect=env.EnvironmentRefused("host_capacity")), self.assertRaises(env.EnvironmentRefused):
            env.prepare(p, a)
        self.assertFalse(self.root.exists())

    def test_plan_real_candidate_changes_only_closed_memory_pair(self):
        fixture = self.proposal()
        files = [Path(item["path"]) for item in fixture["bindings"]]
        with mock.patch.object(env, "installation_files", return_value=files), mock.patch.object(
                env, "old_registry_snapshot", return_value=fixture["old_avd"]):
            default = env.plan_prepare(self.root, self.sdk, self.java, self.base / "default-plan.json")
            real = env.plan_prepare(self.root, self.sdk, self.java, self.base / "real-plan.json", real_candidate=True)
        self.assertEqual(set(default), set(fixture))
        self.assertEqual(default["memory_mib"], 2048)
        self.assertEqual(default["host_available_memory_min"], 4 * env.GIB)
        self.assertEqual(real, dict(default, memory_mib=8192, host_available_memory_min=12 * env.GIB))
        for value in (default, real):
            env.validate_proposal(value, "prepare")
            self.assertFalse(value["allow_environment_calls"])
            self.assertTrue(value["root_go_pending"])
        self.assertFalse(self.root.exists())

    def test_plan_profile_argument_refuses_non_boolean_before_inputs_or_mutation(self):
        for argument in (None, 0, 1, "real", 8192):
            with self.subTest(argument=argument), mock.patch.object(env, "installation_files") as inputs:
                with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_profile"):
                    env.plan_prepare(self.root, self.sdk, self.java, self.base / "never.json", real_candidate=argument)
                inputs.assert_not_called()
                self.assertFalse(self.root.exists())
                self.assertFalse((self.base / "never.json").exists())

    def test_validator_accepts_only_exact_integer_profile_pairs_in_both_phases(self):
        for phase in ("prepare", "run"):
            value = self.proposal(phase)
            if phase == "run":
                value.update(prepare_proposal={}, prepared={}, prepare_result={}, max_seconds=1200)
            for memory, floor in ((2048, 4 * env.GIB), (8192, 12 * env.GIB)):
                env.validate_proposal(dict(value, memory_mib=memory, host_available_memory_min=floor), phase)
            for memory, floor in ((8192, 4 * env.GIB), (2048, 12 * env.GIB), (4096, 8 * env.GIB),
                                  (8192, 12 * env.GIB - 1), (8192.0, 12 * env.GIB),
                                  (8192, float(12 * env.GIB)), (True, 4 * env.GIB)):
                with self.subTest(phase=phase, memory=memory, floor=floor):
                    with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_proposal"):
                        env.validate_proposal(dict(value, memory_mib=memory, host_available_memory_min=floor), phase)

    def test_real_profile_config_and_launcher_use_same_ram_without_disk_changes(self):
        default = self.proposal()
        real = dict(default, memory_mib=8192, host_available_memory_min=12 * env.GIB)
        content = Path(real["paths"]["content"])
        original = env.ini(env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG,
                                                          self.generated_registry(content), content))
        upgraded = env.ini(env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG,
                                  self.generated_registry(content), content, real["memory_mib"]))
        self.assertEqual(upgraded, dict(original, **{"hw.ramSize": "8192"}))
        self.assertEqual(upgraded["disk.dataPartition.size"], "12G")
        self.assertEqual(upgraded["sdcard.size"], "8192M")
        before, after = env.emulator_command(default), env.emulator_command(real)
        expected = list(before); expected[expected.index("-memory") + 1] = "8192"
        self.assertEqual(after, expected)
        self.assertEqual(env.prepare_command(real), env.prepare_command(default))
        self.assertEqual(after[after.index("-cores") + 1], "2")
        self.assertNotIn("-partition-size", after)
        for bad in (4096, True, 8192.0, "8192"):
            with self.subTest(bad=bad), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_profile"):
                env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG, self.generated_registry(content), content, bad)

    def test_profile_memory_floor_accepts_exact_threshold_and_refuses_one_byte_short(self):
        value = self.proposal()
        for memory_mib, minimum in ((2048, 4 * env.GIB), (8192, 12 * env.GIB)):
            value.update(memory_mib=memory_mib, host_available_memory_min=minimum)
            for available in (minimum, minimum - 1):
                def memory_status(pointer):
                    pointer._obj.available = available
                    return 1
                with self.subTest(memory=memory_mib, available=available), mock.patch.object(
                        env.ctypes.windll.kernel32, "GlobalMemoryStatusEx", side_effect=memory_status), mock.patch.object(
                        env.shutil, "disk_usage", return_value=type("Disk", (), {"free": 40 * env.GIB})()):
                    if available < minimum:
                        with self.assertRaisesRegex(env.EnvironmentRefused, "host_capacity"):
                            env.resource_facts(value)
                    else:
                        self.assertEqual(env.resource_facts(value)["available_memory"], minimum)

    def test_real_profile_memory_shortfall_prevents_prepare_creation_or_child(self):
        value = self.proposal()
        value.update(memory_mib=8192, host_available_memory_min=12 * env.GIB)
        proposal, authorization = self.files(value)
        def memory_status(pointer):
            pointer._obj.available = 12 * env.GIB - 1
            return 1
        with mock.patch.object(env.ctypes.windll.kernel32, "GlobalMemoryStatusEx", side_effect=memory_status), mock.patch.object(
                env.shutil, "disk_usage", return_value=type("Disk", (), {"free": 40 * env.GIB})()), mock.patch.object(
                env.host, "run_process") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "host_capacity"):
                env.prepare(proposal, authorization)
        child.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_real_profile_flag_is_plan_prepare_only_before_other_dispatch(self):
        for phase in ("prepare", "plan-run", "run", "_prepare-worker", "_run-worker"):
            with self.subTest(phase=phase), mock.patch.object(env, "prepare") as prepare, mock.patch.object(
                    env, "plan_run") as plan, mock.patch.object(env, "run") as run, mock.patch.object(
                    env, "worker") as worker, mock.patch.object(sys, "stdout", new=io.StringIO()):
                self.assertEqual(env.main([phase, "--real-model-candidate"]), 2)
                for operation in (prepare, plan, run, worker):
                    operation.assert_not_called()

    def test_plan_prepare_cli_selects_explicit_or_default_profile(self):
        for flags, expected in (([], False), (["--real-model-candidate"], True)):
            with self.subTest(expected=expected), mock.patch.object(env, "plan_prepare") as plan:
                self.assertEqual(env.main(["plan-prepare", "--root", "root", "--sdk", "sdk",
                    "--java-home", "java", "--output", "output"] + flags), 0)
                plan.assert_called_once_with("root", "sdk", "java", "output", real_candidate=expected)

    def test_real_run_retains_profile_and_refuses_downgrade_from_bound_prepare(self):
        run, _, _ = self.prepared_run(real_candidate=True)
        env.validate_proposal(run, "run")
        env.verify_prepared(run)
        changed = dict(run, memory_mib=2048, host_available_memory_min=4 * env.GIB)
        env.validate_proposal(changed, "run")  # Valid synthetic pair, wrong admitted environment.
        with self.assertRaisesRegex(env.EnvironmentRefused, "prepared_changed"):
            env.verify_prepared(changed)

    def test_token_drift_precedes_creation(self):
        p, a = self.files(self.proposal()); self.token.write_bytes(b"changed")
        with self.assertRaisesRegex(env.EnvironmentRefused, "console_token_changed"):
            env.prepare(p, a)
        self.assertFalse(self.root.exists())

    def test_duplicate_json_rejected(self):
        path = self.base / "duplicate.json"; path.write_bytes(b'{"phase":"run","phase":"prepare"}')
        with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_json"):
            env.read_json(path)

    def test_create_json_never_replaces(self):
        path = self.base / "receipt"; env.create_json(path, {"first": True})
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            env.create_json(path, {"first": False})
        self.assertEqual(path.read_bytes(), original)

    def test_config_duplicate_keys_refused(self):
        with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_config"):
            env.ini(b"path=first\npath=second\n")

    def generated_registry(self, content):
        return ("avd.ini.encoding=UTF-8\npath=" + str(content) + "\ntarget=android-35\n").encode("utf-8")

    def test_actual_cmdline_11_profile_replays_exact_retained_bytes(self):
        self.assertEqual(len(ACTUAL_CMDLINE_11_CONFIG), 3201)
        self.assertEqual(hashlib.sha256(ACTUAL_CMDLINE_11_CONFIG).hexdigest(),
                         "5774eccd6c920ec3157a7a43710620645284c7e064a9f06933915f12d05aa6ac")
        values = env.ini(ACTUAL_CMDLINE_11_CONFIG)
        self.assertNotIn("AvdId", values)
        self.assertEqual(values["avd.id"], "<build>")
        self.assertEqual(values["sdcard.size"], "512 MB")

    def test_actual_profile_normalizes_only_fresh_confined_identity_and_paths(self):
        content = self.root / "content" / (env.NAME + ".avd")
        before = env.ini(ACTUAL_CMDLINE_11_CONFIG)
        result = env.ini(env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG,
                                                       self.generated_registry(content), content))
        for key in ("AvdId", "avd.id", "avd.name"):
            self.assertEqual(result[key], env.NAME)
        self.assertEqual(result["disk.dataPartition.path"], str(content / "userdata-qemu.img"))
        self.assertEqual(result["disk.cachePartition.path"], str(content / "cache.img"))
        self.assertEqual(result["sdcard.path"], str(content / "sdcard.img"))
        self.assertEqual(result["sdcard.size"], "8192M")
        self.assertEqual(result["disk.dataPartition.size"], "12G")
        self.assertEqual(result["hw.ramSize"], "2048")
        self.assertEqual(result["hw.cpu.ncore"], "2")
        self.assertEqual(result["hw.lcd.height"], before["hw.lcd.height"])
        for key in ("firstboot.bootFromDownloadableSnapshot", "firstboot.bootFromLocalSnapshot",
                    "firstboot.saveToLocalSnapshot", "fastboot.forceFastBoot", "fastboot.forceChosenSnapshotBoot"):
            self.assertEqual(result[key], "no")
        self.assertEqual(result["fastboot.forceColdBoot"], "yes")

    def test_large_userdata_uses_config_without_windows_capped_partition_option(self):
        value = self.proposal()
        content = Path(value["paths"]["content"])
        command = env.emulator_command(value)
        normalized = env.ini(env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG,
                                                             self.generated_registry(content), content))
        self.assertEqual(normalized["disk.dataPartition.size"], "12G")
        self.assertEqual(value["userdata_mib"] * 1024 * 1024, 12 * env.GIB)
        self.assertEqual(command[command.index("-data") + 1], normalized["disk.dataPartition.path"])
        self.assertNotIn("-partition-size", command)
        self.assertNotIn("-partition_size", command)
        self.assertNotIn("12288", command)

    def changed_profile(self, **changes):
        values = env.ini(ACTUAL_CMDLINE_11_CONFIG)
        values.update(changes)
        return "".join(k + "=" + v + "\n" for k, v in values.items()).encode("utf-8")

    def test_generated_foreign_identity_never_normalized_into_ownership(self):
        content = self.root / "content" / (env.NAME + ".avd")
        for key in ("AvdId", "avd.id", "avd.name"):
            with self.subTest(key=key), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_config"):
                env.normalize_generated_config(self.changed_profile(**{key: "other-avd"}),
                                               self.generated_registry(content), content)

    def test_generated_wrong_image_arch_tag_refused(self):
        content = self.root / "content" / (env.NAME + ".avd")
        for key, value in (("abi.type", "arm64-v8a"), ("hw.cpu.arch", "arm64"),
                           ("tag.id", "google_apis_playstore"), ("image.sysdir.1", "system-images/android-34/google_apis/x86_64/")):
            with self.subTest(key=key), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_config"):
                env.normalize_generated_config(self.changed_profile(**{key: value}),
                                               self.generated_registry(content), content)

    def test_generated_foreign_or_initial_disk_path_refused(self):
        content = self.root / "content" / (env.NAME + ".avd")
        for key in ("disk.dataPartition.path", "disk.dataPartition.initPath", "disk.cachePartition.path", "sdcard.path"):
            with self.subTest(key=key), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_config"):
                env.normalize_generated_config(self.changed_profile(**{key: "D:\\old-avd\\old.img"}),
                                               self.generated_registry(content), content)

    def test_generated_registry_wrong_root_target_or_extra_field_refused(self):
        content = self.root / "content" / (env.NAME + ".avd")
        original = env.ini(self.generated_registry(content))
        for changes in ({"path": str(self.base / "other")}, {"target": "android-34"},
                        {"path.rel": "old-relative"}, {"avd.ini.encoding": "UTF-16"}):
            values = dict(original, **changes)
            raw = "".join(k + "=" + v + "\n" for k, v in values.items()).encode("utf-8")
            with self.subTest(changes=changes), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_registry"):
                env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG, raw, content)

    def test_cli_has_no_destructive_or_auth_disabling_flags(self):
        value = self.proposal(); command = env.emulator_command(value)
        self.assertIn("-no-metrics", command)
        self.assertIn("-no-snapshot", command)
        self.assertTrue({"-wipe-data", "-read-only", "-skip-adb-auth", "-grpc", "-f"}.isdisjoint(command))
        creation = env.prepare_command(value)
        self.assertNotIn("-f", creation)
        self.assertEqual(creation[-2:], ["-c", "8192M"])
        self.assertNotIn("cmd.exe", " ".join(creation))

    def test_child_environment_isolated_and_java_injection_removed(self):
        value = self.proposal()
        with mock.patch.dict(os.environ, {"JAVA_OPTS": "bad", "_JAVA_OPTIONS": "bad", "JDK_JAVA_OPTIONS": "bad",
                                         "ANDROID_AVD_HOME": "old", "AVDMANAGER_OPTS": "bad"}):
            scoped = env.scoped_env(value)
        for key in ("JAVA_OPTS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "AVDMANAGER_OPTS"):
            self.assertNotIn(key, scoped)
        self.assertEqual(scoped["ANDROID_AVD_HOME"], value["paths"]["registry"])
        self.assertEqual(scoped["TEMP"], value["paths"]["tmp"])

    def test_run_budget_rejects_zero_and_over_1200(self):
        run, _, _ = self.prepared_run()
        for budget in (0, 1201, True, 1.5):
            run["max_seconds"] = budget
            with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_budget"):
                env.validate_proposal(run, "run")

    def test_initial_disks_verified_before_launch(self):
        run, p, a = self.prepared_run()
        (Path(run["paths"]["content"]) / "sdcard.img").write_bytes(b"guest changed too soon")
        with mock.patch.object(env, "supervise") as child, self.assertRaisesRegex(env.EnvironmentRefused, "binding_changed"):
            env.run(p, a)
        child.assert_not_called()

    def test_live_open_accepts_guest_mutable_disk_changes(self):
        run, p, _ = self.prepared_run()
        content = Path(run["paths"]["content"])
        (content / "sdcard.img").write_bytes(b"legitimate guest writes")
        (content / "userdata-qemu.img").write_bytes(b"new ext4 fixture")
        descriptor = self.descriptor(run, p)
        path = self.root / "running-v1.json"; env.create_json(path, descriptor)
        identities = {descriptor[x]["pid"]: descriptor[x] for x in ("owner", "worker", "launcher")}
        with mock.patch.object(env, "process_identity", side_effect=lambda pid: identities[pid]):
            lease = env.open_live_owner(p, path, env.digest(path))
            self.assertIsNone(lease.check())

    def test_live_check_does_not_rehash_sdk(self):
        lease, identities = self.lease()
        original = env.check_binding
        seen = []
        def record(item):
            seen.append(item["path"]); original(item)
        with mock.patch.object(env, "process_identity", side_effect=lambda pid: identities[pid]), mock.patch.object(env, "check_binding", side_effect=record):
            lease.check()
        self.assertFalse(any(path.startswith(str(self.sdk)) for path in seen))
        self.assertNotIn(str(Path(lease.descriptor["content"]) / "sdcard.img"), seen)

    def test_live_owner_pid_reuse_refused(self):
        lease, identities = self.lease()
        identities[100] = dict(identities[100], creation_filetime=999)
        with mock.patch.object(env, "process_identity", side_effect=lambda pid: identities[pid]), self.assertRaisesRegex(env.EnvironmentRefused, "owner_lost"):
            lease.check()

    def test_live_owner_expiry_refused(self):
        lease, identities = self.lease()
        with mock.patch.object(env.time, "time", return_value=lease.descriptor["deadline_epoch"]), self.assertRaisesRegex(env.EnvironmentRefused, "owner_expired"):
            lease.check()

    def test_stop_and_result_each_revoke_lease(self):
        lease, identities = self.lease()
        for name in ("stop-v1.json", "owner-result-v1.json"):
            path = self.root / name; path.write_bytes(b"{}")
            with self.assertRaisesRegex(env.EnvironmentRefused, "owner_stopped"):
                lease.check()
            path.unlink()  # Host fixture only, never an emulator namespace.

    def test_descriptor_changed_refused(self):
        lease, _ = self.lease()
        Path(lease.running_path).write_bytes(b"{}")
        with self.assertRaisesRegex(env.EnvironmentRefused, "descriptor_changed"):
            lease.check()

    def test_config_drift_refuses_live_owner(self):
        lease, _ = self.lease()
        (Path(lease.descriptor["content"]) / "config.ini").write_bytes(b"changed")
        with self.assertRaisesRegex(env.EnvironmentRefused, "binding_changed"):
            lease.check()

    def test_run_cannot_mix_another_prepared_root(self):
        run, p, a = self.prepared_run()
        original = env.read_json(run["prepare_proposal"]["path"])
        original["paths"] = env.paths(self.base / "other-root")
        source = Path(run["prepare_proposal"]["path"])
        source.write_bytes(env.encoded(original))
        run["prepare_proposal"] = env.binding(source)
        record_path = Path(run["prepared"]["path"])
        record = env.read_json(record_path); record["proposal_sha256"] = env.digest(source)
        record_path.write_bytes(env.encoded(record)); run["prepared"] = env.binding(record_path)
        with self.assertRaisesRegex(env.EnvironmentRefused, "prepared_changed"):
            env.verify_prepared(run)

    def test_prepared_cannot_omit_or_redirect_config(self):
        run, _, _ = self.prepared_run()
        receipt = Path(run["prepared"]["path"])
        value = env.read_json(receipt); value["immutable"].pop()
        receipt.write_bytes(env.encoded(value)); run["prepared"] = env.binding(receipt)
        with self.assertRaisesRegex(env.EnvironmentRefused, "prepared_changed"):
            env.verify_prepared(run)

    def test_added_sdk_file_invalidates_installation_set(self):
        p, a = self.files(self.proposal())
        (self.sdk / "emulator/extra.dll").write_bytes(b"unbound")
        with self.assertRaisesRegex(env.EnvironmentRefused, "binding_set_changed"):
            env.prepare(p, a)
        self.assertFalse(self.root.exists())

    def test_default_old_registry_drift_precedes_new_mutation(self):
        value = self.proposal(); p, a = self.files(value)
        registry = self.base / ".android/avd"; registry.mkdir(parents=True)
        # Even newly appearing registry metadata invalidates the prior absence proof.
        with self.assertRaisesRegex(env.EnvironmentRefused, "old_registry_changed"):
            env.prepare(p, a)
        self.assertFalse(self.root.exists())

    def test_consumed_run_never_launches_again(self):
        run, p, a = self.prepared_run()
        (self.root / "run-start-v1.json").write_bytes(b"preserve original attempt")
        with mock.patch.object(env, "resource_facts", return_value={}), mock.patch.object(env, "ports_free"), mock.patch.object(env, "supervise") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "target_used"):
                env.run(p, a)
        child.assert_not_called()

    def test_boolean_version_not_integer_version(self):
        value = self.proposal(); value["version"] = True
        with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_proposal"):
            env.validate_proposal(value, "prepare")

    def test_wrong_serial_in_descriptor_refused(self):
        with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_descriptor"):
            self.lease(lambda d: d.update(serial="emulator-5554"))

    def test_ports_conflict_refuses_before_launch(self):
        with mock.patch.object(env.socket, "socket") as factory:
            factory.return_value.bind.side_effect = OSError("busy")
            with self.assertRaisesRegex(env.EnvironmentRefused, "ports_unavailable"):
                env.ports_free()
        factory.return_value.close.assert_called_once()

    def test_sdk_prepare_worker_barrier_before_any_child(self):
        with mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(b"{}"))):
            with mock.patch.object(env.subprocess, "run") as child, self.assertRaises(env.EnvironmentRefused):
                env.worker("_prepare-worker")
        child.assert_not_called()

    def test_worker_changed_proposal_at_barrier_has_zero_sdk_launches(self):
        p, a = self.files(self.proposal())
        expected = env.digest(p)
        changed = env.read_json(p); changed["java_home"] = str(self.base / "other-java")
        p.write_bytes(env.encoded(changed))
        request = env.encoded({"proposal": str(p), "proposal_sha256": expected, "authorization": str(a)})
        with mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(request))), mock.patch.object(env.subprocess, "run") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "proposal_changed"):
                env.worker("_prepare-worker")
        child.assert_not_called()

    def test_internal_worker_requires_real_matching_authorization(self):
        p, a = self.files(self.proposal(), authorized=False)
        request = env.encoded({"proposal": str(p), "proposal_sha256": env.digest(p), "authorization": str(a)})
        with mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(request))), mock.patch.object(env.subprocess, "run") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "not_authorized"):
                env.worker("_prepare-worker")
        child.assert_not_called()

    def test_internal_worker_cannot_replay_consumed_claim(self):
        value = self.proposal(); p, a = self.files(value)
        self.root.mkdir()
        identity = {"pid": 123, "creation_filetime": 456, "executable": sys.executable}
        env.create_json(self.root / "prepare-start-v1.json", {"proposal_sha256": env.digest(p), "owner": identity})
        env.create_json(self.root / "prepare-worker-claimed-v1.json", {"already": "consumed"})
        request = env.encoded({"proposal": str(p), "proposal_sha256": env.digest(p), "authorization": str(a)})
        with mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(request))), mock.patch.object(env, "process_identity", return_value=identity), mock.patch.object(env.subprocess, "run") as child:
            with self.assertRaises(FileExistsError):
                env.worker("_prepare-worker")
        child.assert_not_called()

    def test_failed_sdk_child_has_failure_closure_and_retained_raw(self):
        p, a = self.files(self.proposal())
        failed = env.host.ProcessResult("completed", 10, b"private failed-tool output", 2, 1, True)
        with mock.patch.object(env, "resource_facts", return_value={}), mock.patch.object(env.host, "run_process", return_value=failed):
            with self.assertRaisesRegex(env.EnvironmentRefused, "prepare_failed"):
                env.prepare(p, a)
        result = env.read_json(self.root / "prepare-result-v1.json")
        self.assertEqual(result["status"], "refused")
        self.assertTrue(result["child_cleanup_complete"])
        self.assertTrue(result["closure_verified"])
        self.assertFalse(result["prepared_created"])
        self.assertEqual((self.root / "prepare-stdout-v1.bin").read_bytes(), failed.stdout)

    def test_invalid_generated_config_still_closes_and_preserves(self):
        value = self.proposal(); p, a = self.files(value)
        def fake_sdk(*args, **kwargs):
            content = Path(value["paths"]["content"]); content.mkdir()
            (content / "config.ini").write_bytes(b"AvdId=wrong\n")
            (Path(value["paths"]["registry"]) / (env.NAME + ".ini")).write_bytes(self.generated_registry(content))
            return env.host.ProcessResult("completed", 10, b"created", 0, 0, True)
        with mock.patch.object(env, "resource_facts", return_value={}), mock.patch.object(env.host, "run_process", side_effect=fake_sdk):
            with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_config"):
                env.prepare(p, a)
        self.assertEqual((Path(value["paths"]["content"]) / "config.ini").read_bytes(), b"AvdId=wrong\n")
        result = env.read_json(self.root / "prepare-result-v1.json")
        self.assertTrue(result["closure_verified"])
        self.assertFalse(result["prepared_created"])

    def generated_sdk_fixture(self, value, existing_userdata=False):
        content = Path(value["paths"]["content"]); content.mkdir()
        (content / "config.ini").write_bytes(ACTUAL_CMDLINE_11_CONFIG)
        (content / "sdcard.img").write_bytes(b"too small")
        (Path(value["paths"]["registry"]) / (env.NAME + ".ini")).write_bytes(self.generated_registry(content))
        if existing_userdata:
            # Isolate userdata refusal: SD must independently satisfy admission.
            # Set a sparse host-test file, without an 8GiB allocation or SDK tool.
            import ctypes
            import msvcrt
            from ctypes import wintypes
            with (content / "sdcard.img").open("wb") as stream:
                kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
                    wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
                kernel.DeviceIoControl.restype = wintypes.BOOL
                returned = wintypes.DWORD()
                self.assertTrue(kernel.DeviceIoControl(msvcrt.get_osfhandle(stream.fileno()),
                    0x900C4, None, 0, None, 0, ctypes.byref(returned), None))  # FSCTL_SET_SPARSE
                stream.truncate(8 * env.GIB)
            (content / "userdata-qemu.img").write_bytes(b"must not adopt")
        return env.host.ProcessResult("completed", 10, b"created", 0, 0, True)

    def test_generated_tiny_sd_refuses_before_rewriting_valid_profile(self):
        value = self.proposal(); p, a = self.files(value)
        with mock.patch.object(env, "resource_facts", return_value={}), mock.patch.object(env.host, "run_process", side_effect=lambda *args, **kw: self.generated_sdk_fixture(value)):
            with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_initial_disks"):
                env.prepare(p, a)
        content = Path(value["paths"]["content"])
        self.assertEqual((content / "config.ini").read_bytes(), ACTUAL_CMDLINE_11_CONFIG)
        self.assertFalse((content / "config.created.ini").exists())
        self.assertEqual((content / "sdcard.img").read_bytes(), b"too small")

    def test_generated_existing_userdata_refuses_without_adoption(self):
        value = self.proposal(); p, a = self.files(value)
        with mock.patch.object(env, "resource_facts", return_value={}), mock.patch.object(env.host, "run_process", side_effect=lambda *args, **kw: self.generated_sdk_fixture(value, existing_userdata=True)):
            with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_initial_disks"):
                env.prepare(p, a)
        content = Path(value["paths"]["content"])
        self.assertEqual((content / "sdcard.img").stat().st_size, 8 * env.GIB)
        self.assertEqual((content / "userdata-qemu.img").read_bytes(), b"must not adopt")
        self.assertEqual((content / "config.ini").read_bytes(), ACTUAL_CMDLINE_11_CONFIG)
        self.assertFalse((content / "config.created.ini").exists())

    def test_failed_child_cannot_hide_token_drift_in_closure(self):
        p, a = self.files(self.proposal())
        def fake_sdk(*args, **kwargs):
            self.token.write_bytes(b"changed during failed SDK child")
            return env.host.ProcessResult("completed", 10, b"failed", 0, 1, True)
        with mock.patch.object(env, "resource_facts", return_value={}), mock.patch.object(env.host, "run_process", side_effect=fake_sdk):
            with self.assertRaisesRegex(env.EnvironmentRefused, "prepare_failed"):
                env.prepare(p, a)
        self.assertFalse(env.read_json(self.root / "prepare-result-v1.json")["closure_verified"])

    def test_outer_budget_does_not_relax_runtime_helper(self):
        cancel = threading.Event(); cancel.set()
        result = env.host.run_process(["must-not-spawn"], cancel=cancel, deadline=180, max_output=env.MAX_OUTPUT)
        self.assertEqual(result.status, "cancelled")
        with self.assertRaisesRegex(ValueError, "invalid_process_budget"):
            env.host.run_process(["must-not-spawn"], cancel=cancel, deadline=1200)

    def test_main_exit_propagates_refusal_and_completed_status(self):
        with mock.patch.object(env, "run", return_value={"status": "expired", "cleanup_complete": True, "closure_verified": True}):
            self.assertEqual(env.main(["run", "--proposal", "p", "--authorization", "a"]), 2)
        with mock.patch.object(env, "run", return_value={"status": "stop_requested", "cleanup_complete": True, "closure_verified": True}):
            self.assertEqual(env.main(["run", "--proposal", "p", "--authorization", "a"]), 0)
        with mock.patch.object(env, "run", side_effect=env.EnvironmentRefused("not_authorized")):
            self.assertEqual(env.main(["run", "--proposal", "p", "--authorization", "a"]), 2)

    @unittest.skipUnless(os.name == "nt", "Windows job qualification")
    def test_owned_job_closes_grandchild_after_launcher_exit(self):
        self.root.mkdir()
        pid_path = self.root / "grandchild.pid"
        worker = self.base / "fake-worker.py"
        worker.write_text("import subprocess,sys,time\nfrom pathlib import Path\n"
                          "sys.stdin.buffer.read()\n"
                          "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
                          "Path(sys.argv[1]).write_text(str(child.pid))\n"
                          "time.sleep(.2)\n", encoding="utf-8")
        result = env.supervise([sys.executable, "-B", str(worker), str(pid_path)], b"barrier\n", self.root, 5,
                               lambda child: True)
        self.assertEqual(result["status"], "child_exited")
        self.assertTrue(result["cleanup_complete"])
        pid = int(pid_path.read_text())
        with self.assertRaises(env.EnvironmentRefused):
            env.process_identity(pid)

    @unittest.skipUnless(os.name == "nt", "Windows job qualification")
    def test_owned_job_expiry_kills_live_worker_and_descendant(self):
        self.root.mkdir()
        pid_path = self.root / "grandchild.pid"
        worker = self.base / "holding-worker.py"
        worker.write_text("import subprocess,sys,time\nfrom pathlib import Path\n"
                          "sys.stdin.buffer.read()\n"
                          "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
                          "Path(sys.argv[1]).write_text(str(child.pid))\n"
                          "time.sleep(60)\n", encoding="utf-8")
        result = env.supervise([sys.executable, "-B", str(worker), str(pid_path)], b"barrier\n", self.root, 1,
                               lambda child: True)
        self.assertEqual(result["status"], "expired")
        self.assertTrue(result["cleanup_complete"])
        with self.assertRaises(env.EnvironmentRefused):
            env.process_identity(int(pid_path.read_text()))

    @unittest.skipUnless(os.name == "nt", "Windows job qualification")
    def test_malformed_stop_fails_and_still_drains_owned_child(self):
        self.root.mkdir()
        worker = self.base / "holding.py"
        worker.write_text("import sys,time;sys.stdin.buffer.read();time.sleep(60)", encoding="utf-8")
        (self.root / "stop-v1.json").write_bytes(b'{"action":"different"}')
        result = env.supervise([sys.executable, "-B", str(worker)], b"barrier\n", self.root, 5,
                               lambda child: True, "a" * 64)
        self.assertEqual(result["status"], "owner_failed")
        self.assertTrue(result["cleanup_complete"])

    @unittest.skipUnless(os.name == "nt", "Windows job qualification")
    def test_exact_stop_is_only_ordinary_completion(self):
        self.root.mkdir()
        worker = self.base / "holding.py"
        worker.write_text("import sys,time;sys.stdin.buffer.read();time.sleep(60)", encoding="utf-8")
        env.create_json(self.root / "stop-v1.json", {"version": 1, "proposal_sha256": "a" * 64, "action": "stop"})
        result = env.supervise([sys.executable, "-B", str(worker)], b"barrier\n", self.root, 5,
                               lambda child: True, "a" * 64)
        self.assertEqual(result["status"], "stop_requested")
        self.assertTrue(result["cleanup_complete"])


if __name__ == "__main__":
    unittest.main()
