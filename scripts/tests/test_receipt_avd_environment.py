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
        # Old disk/physical-memory/CPU tests must never depend on live commit headroom.
        self.commit_snapshot = {"version": 1, "commit_total_bytes": 16 * env.GIB,
                                "commit_limit_bytes": 64 * env.GIB, "available_commit_bytes": 48 * env.GIB}
        self.commit_patch = mock.patch.object(env.commit_capacity, "read_commit", return_value=self.commit_snapshot)
        self.commit_reader = self.commit_patch.start()
        self.addCleanup(self.commit_patch.stop)

    def tearDown(self):
        self.token_patch.stop()
        self.tmp.cleanup()

    def expected_commit_record(self, memory_mib, snapshot=None):
        snapshot = self.commit_snapshot if snapshot is None else snapshot
        # The two admitted guest profiles have fixed6GiB/18GiB commit gates.
        return dict(snapshot, guest_memory_bytes=memory_mib * 1024 * 1024,
                    required_commit_bytes={2048: 6 * env.GIB, 8192: 18 * env.GIB}[memory_mib],
                    reserve_bytes=2 * env.GIB)

    def healthy_resources(self, *, physical=32 * 1024 ** 3, free=100 * 1024 ** 3, cpus=16):
        from contextlib import ExitStack
        stack = ExitStack()
        def memory(pointer):
            pointer._obj.available = physical
            return 1
        stack.enter_context(mock.patch.object(env.ctypes.windll.kernel32, "GlobalMemoryStatusEx", side_effect=memory))
        stack.enter_context(mock.patch.object(env.shutil, "disk_usage", return_value=type("Disk", (), {"free": free})()))
        stack.enter_context(mock.patch.object(env.os, "cpu_count", return_value=cpus))
        return stack

    def test_commit_gate_accepts_exact_fixed_margin_and_refuses_one_byte_short(self):
        for guest_mib, required in ((2048, 6 * env.GIB), (8192, 18 * env.GIB)):
            value = dict(self.proposal(), memory_mib=guest_mib,
                         host_available_memory_min=(4 if guest_mib == 2048 else 12) * env.GIB)
            for available in (required, required - 1):
                snapshot = {"version": 1, "commit_total_bytes": 64 * env.GIB - available,
                            "commit_limit_bytes": 64 * env.GIB, "available_commit_bytes": available}
                with self.subTest(guest_mib=guest_mib, available=available), self.healthy_resources(), \
                     mock.patch.object(env.commit_capacity, "read_commit", return_value=snapshot) as read:
                    if available < required:
                        with self.assertRaisesRegex(env.EnvironmentRefused, "^host_commit_capacity$"):
                            env.resource_facts(value)
                    else:
                        facts = env.resource_facts(value)
                        self.assertEqual(facts["commit_capacity"], self.expected_commit_record(guest_mib, snapshot))
                        self.assertEqual(facts["available_memory"], 32 * env.GIB)
                    read.assert_called_once_with()

    def test_commit_shortfall_is_independent_of_abundant_physical_ram_disk_and_cpu(self):
        value = dict(self.proposal(), memory_mib=8192, host_available_memory_min=12 * env.GIB, cores=4)
        # Synthetic round values reproduce the causal admission distinction,
        # without asserting the earlier emulator's exact allocation requirement.
        snapshot = {"version": 1, "commit_total_bytes": 58 * env.GIB,
                    "commit_limit_bytes": 72 * env.GIB, "available_commit_bytes": 14 * env.GIB}
        with self.healthy_resources(physical=31 * env.GIB), \
             mock.patch.object(env.commit_capacity, "read_commit", return_value=snapshot):
            with self.assertRaisesRegex(env.EnvironmentRefused, "^host_commit_capacity$"):
                env.resource_facts(value)

    def test_bad_commit_snapshot_maps_to_unavailable_without_raw_values(self):
        original = dict(self.commit_snapshot)
        malformed = [None, {}, dict(original, version=True), dict(original, available_commit_bytes=True),
                     dict(original, commit_total_bytes=-1), dict(original, commit_limit_bytes=16 * env.GIB - 1),
                     dict(original, available_commit_bytes=48 * env.GIB - 1), dict(original, private="not-public")]
        for snapshot in malformed:
            with self.subTest(snapshot=snapshot), self.healthy_resources(), \
                 mock.patch.object(env.commit_capacity, "read_commit", return_value=snapshot):
                with self.assertRaisesRegex(env.EnvironmentRefused, "^host_commit_unavailable$"):
                    env.resource_facts(self.proposal())

    def test_commit_observer_refusals_keep_fixed_environment_categories(self):
        for reason, expected in (("commit_unavailable", "host_commit_unavailable"),
                                 ("commit_invalid", "host_commit_unavailable"),
                                 ("commit_capacity", "host_commit_capacity")):
            with self.subTest(reason=reason), self.healthy_resources(), mock.patch.object(
                    env.commit_capacity, "read_commit", side_effect=env.commit_capacity.HostCommitRefused(reason)):
                with self.assertRaisesRegex(env.EnvironmentRefused, "^" + expected + "$"):
                    env.resource_facts(self.proposal())

    def test_earlier_cpu_disk_and_physical_memory_refusals_do_not_query_commit(self):
        value = dict(self.proposal(), memory_mib=8192, host_available_memory_min=12 * env.GIB, cores=4)
        for changes, code in (({"cpus": 7}, "host_cpu_capacity"),
                              ({"physical": 12 * env.GIB - 1}, "host_capacity"),
                              ({"free": 16 * env.GIB - 1}, "host_capacity")):
            with self.subTest(code=code, changes=changes), self.healthy_resources(**changes), \
                 mock.patch.object(env.commit_capacity, "read_commit", side_effect=AssertionError("Earlier gate queried commit")) as read:
                with self.assertRaisesRegex(env.EnvironmentRefused, "^" + code + "$"):
                    env.resource_facts(value)
                read.assert_not_called()

    def test_commit_refusal_prevents_parent_prepare_root_and_child(self):
        value = dict(self.proposal(), memory_mib=8192, host_available_memory_min=12 * env.GIB, cores=4)
        proposal, authorization = self.files(value)
        snapshot = {"version": 1, "commit_total_bytes": 64 * env.GIB - 1,
                    "commit_limit_bytes": 64 * env.GIB, "available_commit_bytes": 1}
        with self.healthy_resources(), mock.patch.object(env.commit_capacity, "read_commit", return_value=snapshot), \
             mock.patch.object(env.host, "run_process") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^host_commit_capacity$"):
                env.prepare(proposal, authorization)
            child.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_commit_refusal_prevents_parent_run_start_ports_and_worker(self):
        _, proposal, authorization = self.prepared_run(four_core_candidate=True)
        snapshot = {"version": 1, "commit_total_bytes": 64 * env.GIB - 1,
                    "commit_limit_bytes": 64 * env.GIB, "available_commit_bytes": 1}
        with self.healthy_resources(), mock.patch.object(env.commit_capacity, "read_commit", return_value=snapshot), \
             mock.patch.object(env, "ports_free") as ports, mock.patch.object(env, "supervise") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^host_commit_capacity$"):
                env.run(proposal, authorization)
            ports.assert_not_called(); child.assert_not_called()
        self.assertFalse((self.root / "run-start-v1.json").exists())

    def test_commit_loss_after_parent_admission_stops_both_worker_profiles_before_claim(self):
        for mode, phase in (("_prepare-worker", "prepare"), ("_run-worker", "run")):
            for guest_mib, cores in ((2048, 2), (8192, 4)):
                with self.subTest(mode=mode, guest_mib=guest_mib):
                    value = dict(self.proposal(phase), memory_mib=guest_mib, cores=cores,
                                 host_available_memory_min=(4 if guest_mib == 2048 else 12) * env.GIB)
                    if phase == "run":
                        value.update(prepare_proposal={}, prepared={}, prepare_result={}, max_seconds=1200 if guest_mib == 2048 else 1800)
                    proposal, authorization = self.files(value, phase + "-commit-" + str(guest_mib) + ".json")
                    with self.healthy_resources():
                        self.assertEqual(env.resource_facts(value)["commit_capacity"], self.expected_commit_record(guest_mib))
                    self.root.mkdir(exist_ok=True)
                    identity = {"pid": 123, "creation_filetime": 456, "executable": sys.executable}
                    start = self.root / (phase + "-start-v1.json")
                    start.write_bytes(env.encoded({"proposal_sha256": env.digest(proposal), "owner": identity}))
                    request = env.encoded({"proposal": str(proposal), "proposal_sha256": env.digest(proposal), "authorization": str(authorization)})
                    short = {"version": 1, "commit_total_bytes": 64 * env.GIB - 1,
                             "commit_limit_bytes": 64 * env.GIB, "available_commit_bytes": 1}
                    with self.healthy_resources(), mock.patch.object(env.commit_capacity, "read_commit", return_value=short), \
                         mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(request))), \
                         mock.patch.object(env, "process_identity", return_value=identity), \
                         mock.patch.object(env.subprocess, "run") as prepare, mock.patch.object(env.subprocess, "Popen") as launch:
                        with self.assertRaisesRegex(env.EnvironmentRefused, "^host_commit_capacity$"):
                            env.worker(mode)
                        prepare.assert_not_called(); launch.assert_not_called()
                    self.assertFalse((self.root / (phase + "-worker-claimed-v1.json")).exists())

    def proposal(self, phase="prepare"):
        # No dependency on actual installed SDK or credentials in any host test.
        files = [Path(env.__file__).resolve(), Path(env.host.__file__).resolve(), Path(env.commit_capacity.__file__).resolve()]
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
                 "host_free_min": {"C:": (40 if self.root.drive.upper() == "C:" else 16) * env.GIB, "D:": 40 * env.GIB},
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

    def prepared_run(self, real_candidate=False, four_core_candidate=False):
        prepare = self.proposal()
        if real_candidate or four_core_candidate:
            prepare.update(memory_mib=8192, host_available_memory_min=12 * env.GIB)
        if four_core_candidate:
            prepare["cores"] = 4
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

    def c_root(self):
        scratch = tempfile.TemporaryDirectory(prefix="receipt-c-root-test-", dir=Path(os.environ["LOCALAPPDATA"]) / "Temp")
        self.addCleanup(scratch.cleanup)
        parent = Path(scratch.name).resolve()
        self.assertEqual(parent.drive.upper(), "C:")
        return parent / "new-avd"

    def test_explicit_c_plan_binds_stronger_floors_without_changing_d_plan(self):
        fixture = self.proposal()
        files = [Path(item["path"]) for item in fixture["bindings"]]
        c_root = self.c_root()
        with mock.patch.object(env, "installation_files", return_value=files), mock.patch.object(
                env, "old_registry_snapshot", return_value=fixture["old_avd"]):
            d_plan = env.plan_prepare(self.root, self.sdk, self.java, self.base / "d-drive-plan.json")
            c_plan = env.plan_prepare(c_root, self.sdk, self.java, self.base / "c-drive-plan.json", real_candidate=True)
        expected_d = dict(fixture, bindings=sorted(fixture["bindings"], key=lambda item: Path(item["path"])))
        self.assertEqual(d_plan, expected_d)
        self.assertEqual(env.encoded(d_plan), env.encoded(expected_d))
        self.assertEqual(c_plan, dict(d_plan, paths=env.paths(c_root),
            host_free_min={"C:": 40 * env.GIB, "D:": 40 * env.GIB},
            memory_mib=8192, host_available_memory_min=12 * env.GIB))
        env.validate_proposal(c_plan, "prepare")
        self.assertFalse(c_root.exists())
        self.assertFalse(self.root.exists())
        self.assertFalse(c_plan["allow_environment_calls"])
        self.assertTrue(c_plan["root_go_pending"])

    def test_root_drive_and_floor_pair_are_closed_in_prepare_and_run(self):
        c_root = self.c_root()
        for phase in ("prepare", "run"):
            original = self.proposal(phase)
            if phase == "run":
                original.update(prepare_proposal={}, prepared={}, prepare_result={}, max_seconds=1200)
            for root, expected in ((self.root, {"C:": 16 * env.GIB, "D:": 40 * env.GIB}),
                                   (c_root, {"C:": 40 * env.GIB, "D:": 40 * env.GIB})):
                valid = dict(original, paths=env.paths(root), host_free_min=expected)
                env.validate_proposal(valid, phase)
                wrong = ({"C:": 16 * env.GIB, "D:": 40 * env.GIB} if root.drive.upper() == "C:" else
                         {"C:": 40 * env.GIB, "D:": 40 * env.GIB})
                for floors in (wrong, dict(expected, **{"C:": expected["C:"] - 1}),
                               dict(expected, **{"D:": 40 * env.GIB - 1}),
                               dict(expected, **{"D:": True}), dict(expected, **{"C:": float(expected["C:"])}),
                               dict(expected, **{"E:": 40 * env.GIB})):
                    with self.subTest(phase=phase, root=root.drive, floors=floors), self.assertRaises(env.EnvironmentRefused):
                        env.validate_proposal(dict(valid, host_free_min=floors), phase)

    def test_other_drives_relative_and_boolean_roots_refuse_before_sdk_inputs(self):
        for root in ("E:/receipt-c-root-refusal", "C:relative", "relative", True, False, None):
            with self.subTest(root=root), mock.patch.object(env, "installation_files") as inputs:
                with self.assertRaises(env.EnvironmentRefused):
                    env.plan_prepare(root, self.sdk, self.java, self.base / "never-drive-plan.json")
                inputs.assert_not_called()
                self.assertFalse((self.base / "never-drive-plan.json").exists())
        value = self.proposal()
        for root in (True, None, "E:/receipt-c-root-refusal", "relative", "C:relative"):
            invalid = dict(value["paths"], root=root)
            with self.subTest(proposal_root=root), self.assertRaises(env.EnvironmentRefused):
                env.validate_proposal(dict(value, paths=invalid), "prepare")

    def test_c_root_preexisting_and_symlink_metadata_refuse_without_adoption(self):
        root = self.c_root()
        root.mkdir()
        sentinel = root / "preserve-original.txt"
        sentinel.write_bytes(b"Original refusal fixture, no AVD")
        with mock.patch.object(env, "installation_files") as inputs:
            with self.assertRaisesRegex(env.EnvironmentRefused, "target_exists"):
                env.plan_prepare(root, self.sdk, self.java, self.base / "preexisting-c.json")
        inputs.assert_not_called()
        self.assertEqual(list(root.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b"Original refusal fixture, no AVD")
        fresh = self.c_root()
        original_lstat = Path.lstat
        original_is_symlink = Path.is_symlink
        def lstat(path, *args, **kwargs):
            if path == fresh:
                return type("LinkMetadata", (), {"st_mode": 0o120777, "st_file_attributes": 0})()
            return original_lstat(path, *args, **kwargs)
        def is_symlink(path):
            # Newer pathlib can use os.path.islink without calling Path.lstat.
            # Model both observations of this synthetic link without creating one.
            return path == fresh or original_is_symlink(path)
        with mock.patch.object(Path, "lstat", new=lstat), \
                mock.patch.object(Path, "is_symlink", new=is_symlink), \
                mock.patch.object(env, "installation_files") as inputs:
            with self.assertRaisesRegex(env.EnvironmentRefused, "unsafe_path"):
                env.plan_prepare(fresh, self.sdk, self.java, self.base / "linked-c.json")
        inputs.assert_not_called()
        self.assertFalse(fresh.exists())
        self.assertFalse((self.base / "linked-c.json").exists())

    def test_c_root_path_shape_cannot_escape_its_explicit_root(self):
        value = self.proposal()
        root = self.c_root()
        value.update(paths=env.paths(root), host_free_min={"C:": 40 * env.GIB, "D:": 40 * env.GIB})
        for key in ("content", "registry", "android", "emulator_home", "tmp"):
            wrong = dict(value["paths"], **{key: str(self.base / "foreign-owned-test-path")})
            with self.subTest(key=key), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_proposal"):
                env.validate_proposal(dict(value, paths=wrong), "prepare")
        with self.assertRaises(env.EnvironmentRefused):
            env.validate_proposal(dict(value, paths=dict(value["paths"], extra=str(root / "extra"))), "prepare")

    def test_c_root_capacity_keeps_both_40gib_reserves(self):
        value = self.proposal()
        value.update(paths=env.paths(self.c_root()), host_free_min={"C:": 40 * env.GIB, "D:": 40 * env.GIB},
                     memory_mib=8192, host_available_memory_min=12 * env.GIB)
        def memory(pointer):
            pointer._obj.available = 12 * env.GIB
            return 1
        for c_free, d_free in ((40 * env.GIB, 40 * env.GIB), (40 * env.GIB - 1, 100 * env.GIB),
                               (100 * env.GIB, 40 * env.GIB - 1)):
            available = {"C:": c_free, "D:": d_free}
            with self.subTest(c_free=c_free, d_free=d_free), mock.patch.object(
                    env.ctypes.windll.kernel32, "GlobalMemoryStatusEx", side_effect=memory), mock.patch.object(
                    env.shutil, "disk_usage", side_effect=lambda drive: type("Disk", (), {"free": available[drive[:2]]})()):
                if min(c_free, d_free) < 40 * env.GIB:
                    with self.assertRaisesRegex(env.EnvironmentRefused, "host_capacity"):
                        env.resource_facts(value)
                else:
                    self.assertEqual(env.resource_facts(value)["free_bytes"], available)

    def test_c_run_preserves_floor_binding_owner_window_and_refuses_replay(self):
        self.root = self.c_root()
        run, _, _ = self.prepared_run(real_candidate=True)
        planned = env.plan_run(run["prepare_proposal"]["path"], run["prepared"]["path"], self.base / "c-run-plan.json")
        self.assertEqual(planned, dict(run, max_seconds=1800))
        env.validate_proposal(planned, "run")
        env.verify_prepared(planned)
        wrong = dict(planned, paths=env.paths(self.base / "different-d-root"),
                     host_free_min={"C:": 16 * env.GIB, "D:": 40 * env.GIB})
        env.validate_proposal(wrong, "run")
        with self.assertRaisesRegex(env.EnvironmentRefused, "prepared_changed"):
            env.verify_prepared(wrong)
        proposal, authorization = self.files(planned, "c-run-used.json")
        sentinel = self.root / "run-start-v1.json"
        sentinel.write_bytes(b"Original consumed run, preserve")
        with mock.patch.object(env, "resource_facts", return_value={}), mock.patch.object(env, "ports_free"), mock.patch.object(env, "supervise") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "target_used"):
                env.run(proposal, authorization)
        child.assert_not_called()
        self.assertEqual(sentinel.read_bytes(), b"Original consumed run, preserve")

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
                plan.assert_called_once_with("root", "sdk", "java", "output", real_candidate=expected,
                                             four_core_candidate=False)

    def test_real_run_retains_profile_and_refuses_downgrade_from_bound_prepare(self):
        run, _, _ = self.prepared_run(real_candidate=True)
        env.validate_proposal(run, "run")
        env.verify_prepared(run)
        changed = dict(run, memory_mib=2048, host_available_memory_min=4 * env.GIB)
        env.validate_proposal(changed, "run")  # Valid synthetic pair, wrong admitted environment.
        with self.assertRaisesRegex(env.EnvironmentRefused, "prepared_changed"):
            env.verify_prepared(changed)

    def test_four_core_plan_changes_only_cores_from_explicit_real_profile(self):
        fixture = self.proposal()
        files = [Path(item["path"]) for item in fixture["bindings"]]
        with mock.patch.object(env, "installation_files", return_value=files), mock.patch.object(
                env, "old_registry_snapshot", return_value=fixture["old_avd"]):
            old = env.plan_prepare(self.root, self.sdk, self.java, self.base / "old-two.json")
            real = env.plan_prepare(self.root, self.sdk, self.java, self.base / "real-two.json", real_candidate=True)
            four = env.plan_prepare(self.root, self.sdk, self.java, self.base / "real-four.json",
                                    real_candidate=True, four_core_candidate=True)
        self.assertEqual(old, dict(fixture, bindings=sorted(fixture["bindings"], key=lambda item: Path(item["path"]))))
        self.assertEqual(real, dict(old, memory_mib=8192, host_available_memory_min=12 * env.GIB))
        self.assertEqual(env.encoded(four), env.encoded(dict(real, cores=4)))
        self.assertEqual(set(four), set(old))
        env.validate_proposal(four, "prepare")
        self.assertFalse(four["allow_environment_calls"])
        self.assertTrue(four["root_go_pending"])
        self.assertFalse(self.root.exists())

    def test_four_core_option_requires_exact_booleans_and_real_before_inputs(self):
        for real, four in ((False, True), (0, True), (1, True), (None, True),
                           (True, None), (True, 0), (True, 1), (True, 4), (True, "four")):
            with self.subTest(real=real, four=four), mock.patch.object(env, "installation_files") as inputs:
                with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_profile"):
                    env.plan_prepare(self.root, self.sdk, self.java, self.base / "never-four.json",
                                     real_candidate=real, four_core_candidate=four)
                inputs.assert_not_called()
                self.assertFalse((self.base / "never-four.json").exists())
                self.assertFalse(self.root.exists())

    def test_four_core_validator_binds_exact_typed_memory_cpu_profile_in_both_phases(self):
        for phase in ("prepare", "run"):
            original = self.proposal(phase)
            if phase == "run":
                original.update(prepare_proposal={}, prepared={}, prepare_result={}, max_seconds=1800)
            four = dict(original, memory_mib=8192, host_available_memory_min=12 * env.GIB, cores=4)
            env.validate_proposal(four, phase)
            for changes in ({"memory_mib": 2048, "host_available_memory_min": 4 * env.GIB},
                            {"memory_mib": 4096}, {"host_available_memory_min": 12 * env.GIB - 1},
                            {"host_available_memory_min": 4 * env.GIB}, {"four_core_candidate": True}):
                with self.subTest(phase=phase, changes=changes), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_proposal"):
                    env.validate_proposal(dict(four, **changes), phase)
            for cores in (True, False, None, "4", 2.0, 4.0, 0, 1, 3, 5, 8):
                with self.subTest(phase=phase, cores=cores), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_proposal"):
                    env.validate_proposal(dict(four, cores=cores), phase)

    def test_four_core_config_and_argv_agree_without_other_profile_changes(self):
        two = dict(self.proposal(), memory_mib=8192, host_available_memory_min=12 * env.GIB)
        four = dict(two, cores=4)
        content = Path(four["paths"]["content"])
        two_config = env.ini(env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG,
            self.generated_registry(content), content, 8192, 2))
        four_config = env.ini(env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG,
            self.generated_registry(content), content, 8192, 4))
        self.assertEqual(four_config, dict(two_config, **{"hw.cpu.ncore": "4"}))
        before, after = env.emulator_command(two), env.emulator_command(four)
        expected = list(before); expected[expected.index("-cores") + 1] = "4"
        self.assertEqual(after, expected)
        self.assertEqual(env.prepare_command(two), env.prepare_command(four))
        self.assertEqual(four_config["disk.dataPartition.size"], "12G")
        self.assertEqual(four_config["sdcard.size"], "8192M")
        self.assertNotIn("-partition-size", after)
        for memory, cores in ((2048, 4), (4096, 4), (True, 4), (8192, True), (8192, 4.0), (8192, 3)):
            with self.subTest(memory=memory, cores=cores), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_profile"):
                env.normalize_generated_config(ACTUAL_CMDLINE_11_CONFIG, self.generated_registry(content), content, memory, cores)
        with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_profile"):
            env.emulator_command(dict(four, cores=3))

    def test_four_core_host_cpu_floor_refuses_unknown_and_records_logical_metadata(self):
        four = dict(self.proposal(), memory_mib=8192, host_available_memory_min=12 * env.GIB, cores=4)
        def memory(pointer):
            pointer._obj.available = 12 * env.GIB
            return 1
        for count in (None, True, False, 0, -1, 4, 7, 8.0, "8", 8, 12):
            with self.subTest(count=count), mock.patch.object(env.os, "cpu_count", return_value=count), mock.patch.object(
                    env.ctypes.windll.kernel32, "GlobalMemoryStatusEx", side_effect=memory), mock.patch.object(
                    env.shutil, "disk_usage", return_value=type("Disk", (), {"free": 40 * env.GIB})()):
                if type(count) is int and count >= 8:
                    self.assertEqual(env.resource_facts(four), {"free_bytes": {"C:": 40 * env.GIB, "D:": 40 * env.GIB},
                        "available_memory": 12 * env.GIB, "logical_cpus": count,
                        "commit_capacity": self.expected_commit_record(8192)})
                else:
                    with self.assertRaisesRegex(env.EnvironmentRefused, "host_cpu_capacity"):
                        env.resource_facts(four)

    def test_two_core_profiles_do_not_query_host_cpu_and_add_only_commit_metadata(self):
        value = self.proposal()
        for memory_mib, floor in ((2048, 4 * env.GIB), (8192, 12 * env.GIB)):
            value.update(memory_mib=memory_mib, host_available_memory_min=floor)
            def memory(pointer):
                pointer._obj.available = floor
                return 1
            with mock.patch.object(env.os, "cpu_count", side_effect=AssertionError("Old profile queried CPUs")) as query, mock.patch.object(
                    env.ctypes.windll.kernel32, "GlobalMemoryStatusEx", side_effect=memory), mock.patch.object(
                    env.shutil, "disk_usage", return_value=type("Disk", (), {"free": 40 * env.GIB})()):
                self.assertEqual(env.resource_facts(value), {"free_bytes": {"C:": 40 * env.GIB, "D:": 40 * env.GIB},
                                                            "available_memory": floor,
                                                            "commit_capacity": self.expected_commit_record(memory_mib)})
                query.assert_not_called()

    def test_four_core_low_cpu_refuses_parent_prepare_before_root_or_child(self):
        four = dict(self.proposal(), memory_mib=8192, host_available_memory_min=12 * env.GIB, cores=4)
        proposal, authorization = self.files(four)
        with mock.patch.object(env.os, "cpu_count", return_value=7), mock.patch.object(env.host, "run_process") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "host_cpu_capacity"):
                env.prepare(proposal, authorization)
        child.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_four_core_low_cpu_refuses_parent_run_without_consuming_start(self):
        _, proposal, authorization = self.prepared_run(four_core_candidate=True)
        with mock.patch.object(env.os, "cpu_count", return_value=None), mock.patch.object(env, "supervise") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "host_cpu_capacity"):
                env.run(proposal, authorization)
        child.assert_not_called()
        self.assertFalse((self.root / "run-start-v1.json").exists())

    def test_four_core_worker_rechecks_cpu_after_parent_admission_before_sdk_spawn(self):
        for mode, phase in (("_prepare-worker", "prepare"), ("_run-worker", "run")):
            with self.subTest(mode=mode):
                value = dict(self.proposal(phase), memory_mib=8192, host_available_memory_min=12 * env.GIB, cores=4)
                if phase == "run":
                    value.update(prepare_proposal={}, prepared={}, prepare_result={}, max_seconds=1800)
                proposal, authorization = self.files(value, phase + "-cpu.json")
                self.root.mkdir(exist_ok=True)
                identity = {"pid": 123, "creation_filetime": 456, "executable": sys.executable}
                env.create_json(self.root / (phase + "-start-v1.json"), {"proposal_sha256": env.digest(proposal), "owner": identity})
                request = env.encoded({"proposal": str(proposal), "proposal_sha256": env.digest(proposal), "authorization": str(authorization)})
                with mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(request))), mock.patch.object(
                        env, "process_identity", return_value=identity), mock.patch.object(env.os, "cpu_count", return_value=7) as query, mock.patch.object(
                        env.subprocess, "run") as prepare, mock.patch.object(env.subprocess, "Popen") as launch:
                    with self.assertRaisesRegex(env.EnvironmentRefused, "host_cpu_capacity"):
                        env.worker(mode)
                query.assert_called_once_with()
                prepare.assert_not_called(); launch.assert_not_called()
                self.assertFalse((self.root / (phase + "-worker-claimed-v1.json")).exists())

    def test_four_core_worker_cpu_admission_precedes_mocked_sdk_dispatch(self):
        value = dict(self.proposal(), memory_mib=8192, host_available_memory_min=12 * env.GIB, cores=4)
        proposal, authorization = self.files(value)
        self.root.mkdir()
        identity = {"pid": 123, "creation_filetime": 456, "executable": sys.executable}
        env.create_json(self.root / "prepare-start-v1.json", {"proposal_sha256": env.digest(proposal), "owner": identity})
        request = env.encoded({"proposal": str(proposal), "proposal_sha256": env.digest(proposal), "authorization": str(authorization)})
        observations = []
        def cpu():
            observations.append("cpu")
            return 8
        def memory(pointer):
            pointer._obj.available = 12 * env.GIB
            return 1
        def dispatch(command, **kwargs):
            self.assertEqual(observations, ["cpu"])
            self.assertTrue((self.root / "prepare-worker-claimed-v1.json").exists())
            self.assertEqual(command, env.prepare_command(value))
            observations.append("mocked_sdk")
            return type("Completed", (), {"returncode": 0})()
        with mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(request))), mock.patch.object(
                env, "process_identity", return_value=identity), mock.patch.object(env.os, "cpu_count", side_effect=cpu), mock.patch.object(
                env.ctypes.windll.kernel32, "GlobalMemoryStatusEx", side_effect=memory), mock.patch.object(
                env.shutil, "disk_usage", return_value=type("Disk", (), {"free": 40 * env.GIB})()), mock.patch.object(
                env.subprocess, "run", side_effect=dispatch) as child:
            self.assertEqual(env.worker("_prepare-worker"), 0)
        child.assert_called_once()
        self.assertEqual(observations, ["cpu", "mocked_sdk"])

    def test_four_core_run_cannot_replay_a_different_core_prepare_or_mutable_config(self):
        run, _, _ = self.prepared_run(four_core_candidate=True)
        env.verify_prepared(run)
        changed = dict(run, cores=2)
        env.validate_proposal(changed, "run")
        with self.assertRaisesRegex(env.EnvironmentRefused, "prepared_changed"):
            env.verify_prepared(changed)
        config = Path(run["paths"]["content"]) / "config.ini"
        config.write_bytes(b"hw.cpu.ncore=2\n")
        with self.assertRaisesRegex(env.EnvironmentRefused, "binding_changed"):
            env.verify_prepared(run)

    def test_four_core_cli_requires_real_and_plan_prepare_without_other_dispatch(self):
        for phase in ("plan-prepare", "prepare", "plan-run", "run", "_prepare-worker", "_run-worker"):
            for real in (False, True):
                if phase == "plan-prepare" and real:
                    continue
                arguments = [phase, "--four-core-candidate"] + (["--real-model-candidate"] if real else [])
                with self.subTest(phase=phase, real=real), mock.patch.object(env, "plan_prepare") as plan, mock.patch.object(
                        env, "prepare") as prepare, mock.patch.object(env, "plan_run") as planned, mock.patch.object(
                        env, "run") as run, mock.patch.object(env, "worker") as worker, mock.patch.object(sys, "stdout", new=io.StringIO()):
                    self.assertEqual(env.main(arguments), 2)
                    for operation in (plan, prepare, planned, run, worker):
                        operation.assert_not_called()
        with mock.patch.object(env, "plan_prepare") as plan:
            self.assertEqual(env.main(["plan-prepare", "--root", "root", "--sdk", "sdk", "--java-home", "java",
                                      "--output", "output", "--real-model-candidate", "--four-core-candidate"]), 0)
            plan.assert_called_once_with("root", "sdk", "java", "output", real_candidate=True, four_core_candidate=True)

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

    def test_synthetic_default_owner_window_remains_1200_with_disabled_shape(self):
        original, _, _ = self.prepared_run()
        result = env.plan_run(original["prepare_proposal"]["path"], original["prepared"]["path"],
                              self.base / "synthetic-window.json")
        self.assertEqual(result, original)
        self.assertEqual(env.MAX_SECONDS, 1200)
        self.assertFalse(result["allow_environment_calls"])
        self.assertTrue(result["root_go_pending"])

    def test_real_default_owner_window_is_1800_without_new_proposal_fields(self):
        original, _, _ = self.prepared_run(real_candidate=True)
        result = env.plan_run(original["prepare_proposal"]["path"], original["prepared"]["path"],
                              self.base / "real-window.json")
        self.assertEqual(result, dict(original, max_seconds=1800))
        self.assertEqual(set(result), set(original))
        self.assertFalse(result["allow_environment_calls"])
        self.assertTrue(result["root_go_pending"])
        env.validate_proposal(result, "run")

    def check_explicit_windows(self, real_candidate):
        original, _, _ = self.prepared_run(real_candidate=real_candidate)
        ceiling = 1800 if real_candidate else 1200
        for index, budget in enumerate((1, 12, 1200, ceiling)):
            output = self.base / ("explicit-window-%d-%d.json" % (index, budget))
            result = env.plan_run(original["prepare_proposal"]["path"], original["prepared"]["path"], output,
                                  max_seconds=budget)
            self.assertEqual(result, dict(original, max_seconds=budget))
            env.validate_proposal(result, "run")

    def test_synthetic_explicit_shorter_windows_and_ceiling_remain_available(self):
        self.check_explicit_windows(False)

    def test_real_explicit_shorter_windows_and_ceiling_remain_available(self):
        self.check_explicit_windows(True)

    def test_owner_window_validator_is_typed_and_profile_specific(self):
        real, _, _ = self.prepared_run(real_candidate=True)
        synthetic = dict(real, memory_mib=2048, host_available_memory_min=4 * env.GIB)
        for value, ceiling in ((synthetic, 1200), (real, 1800)):
            for budget in (0, -1, ceiling + 1, True, 12.0, "12", None):
                with self.subTest(memory=value["memory_mib"], budget=budget):
                    with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_budget"):
                        env.validate_proposal(dict(value, max_seconds=budget), "run")
        with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_budget"):
            env.validate_proposal(dict(synthetic, max_seconds=1800), "run")
        env.validate_proposal(dict(real, max_seconds=1800), "run")

    def test_plan_run_refuses_invalid_explicit_real_windows_without_output(self):
        original, _, _ = self.prepared_run(real_candidate=True)
        for index, budget in enumerate((0, -1, 1801, True, 12.0, "12")):
            output = self.base / ("refused-window-%d.json" % index)
            with self.subTest(budget=budget), self.assertRaisesRegex(env.EnvironmentRefused, "invalid_budget"):
                env.plan_run(original["prepare_proposal"]["path"], original["prepared"]["path"], output,
                             max_seconds=budget)
            self.assertFalse(output.exists())

    def test_plan_run_cannot_give_synthetic_profile_real_owner_window(self):
        original, _, _ = self.prepared_run()
        output = self.base / "refused-cross-profile-window.json"
        with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_budget"):
            env.plan_run(original["prepare_proposal"]["path"], original["prepared"]["path"], output,
                         max_seconds=1800)
        self.assertFalse(output.exists())

    def test_supervisor_absolute_ceiling_is_1800_and_refuses_before_child_or_evidence(self):
        for budget in (0, -1, 1801, True, 1800.0, "1800"):
            with self.subTest(budget=budget), mock.patch.object(env.subprocess, "Popen") as child:
                with self.assertRaisesRegex(env.EnvironmentRefused, "invalid_budget"):
                    env.supervise(["must-not-spawn"], b"barrier", self.root, budget, lambda _: True)
                child.assert_not_called()
                self.assertFalse(self.root.exists())
        self.root.mkdir()
        with mock.patch.object(env.subprocess, "Popen", side_effect=OSError("Synthetic spawn refusal")) as child:
            result = env.supervise(["synthetic-child-only"], b"barrier", self.root, 1800, lambda _: True)
        child.assert_called_once()
        self.assertEqual(result["status"], "owner_failed")
        self.assertFalse(result["cleanup_complete"])
        self.assertEqual(set(p.name for p in self.root.iterdir()), set(env.LiveOutput.names))

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
