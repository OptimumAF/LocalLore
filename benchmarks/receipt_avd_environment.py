"""Opt-in, create-only receipt-test AVD. No imports create files or invoke SDK tools.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0

The supervisor remains the owner until explicit stop/expiry; running is not booted.
All identifiers/paths in receipts are private local evidence, not public diagnostics.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import sys
import threading
import time

try:
    from benchmarks import runtime_spike as host
except ModuleNotFoundError:
    import runtime_spike as host

NAME = "locallore_receipt_api35_v1"
PORT = 5592
PACKAGE = "system-images;android-35;google_apis;x86_64"
MAX_SECONDS = 1200
MAX_OUTPUT = 262144
GIB = 1024 ** 3
BARRIER = b"receipt-avd-owner-v1\n"


class EnvironmentRefused(RuntimeError):
    """Only fixed reason codes escape to callers; no credential/provider errors."""


def require(condition, reason):
    if not condition:
        raise EnvironmentRefused(reason)


def safe_path(value, exists=True, directory=False):
    p = Path(value)
    require(p.is_absolute() and str(p) == os.path.abspath(str(p)), "unsafe_path")
    for part in [p] + list(p.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            require(not stat.S_ISLNK(info.st_mode) and
                    not getattr(info, "st_file_attributes", 0) & 0x400, "unsafe_path")
    if exists:
        require(p.exists() and (p.is_dir() if directory else p.is_file()), "missing_path")
    return p


def digest(path):
    p = safe_path(path)
    h = hashlib.sha256()
    with p.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def binding(path):
    p = safe_path(path)
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": digest(p)}


def check_binding(item):
    require(set(item) == {"path", "bytes", "sha256"} and type(item["path"]) is str and
            type(item["bytes"]) is int and item["bytes"] >= 0 and type(item["sha256"]) is str and
            re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) and binding(item["path"]) == item,
            "binding_changed")


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def create_json(path, value):
    p = safe_path(path, exists=False)
    data = encoded(value)
    with p.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(data).hexdigest()


def read_json(path, cap=4 * 1024 * 1024):
    p = safe_path(path)
    require(0 < p.stat().st_size <= cap, "invalid_json")
    return decode_json(p.read_bytes())


def decode_json(data):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "invalid_json")
            value[key] = item
        return value
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda _: require(False, "invalid_json"))
    except (ValueError, UnicodeError, TypeError):
        raise EnvironmentRefused("invalid_json") from None


def read_bound_json(path, expected):
    p = safe_path(path)
    require(0 < p.stat().st_size <= 4 * 1024 * 1024, "invalid_json")
    data = p.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected, "proposal_changed")
    return decode_json(data)


def paths(root):
    root = safe_path(root, exists=False)
    return {"root": str(root), "content": str(root / "content" / (NAME + ".avd")),
            "registry": str(root / "avd"), "android": str(root / "android"),
            "emulator_home": str(root / "emulator"), "tmp": str(root / "tmp")}


def token_path():
    require(os.name == "nt", "windows_required")
    # Match the installed emulator's CSIDL_PROFILE resolution, not USERPROFILE.
    buffer = ctypes.create_unicode_buffer(32768)
    require(ctypes.windll.shell32.SHGetFolderPathW(None, 40, None, 0, buffer) == 0,
            "profile_unavailable")
    return str(Path(buffer.value) / ".emulator_console_auth_token")


def token_binding(path):
    item = binding(path)
    require(0 < item["bytes"] <= 4096, "console_token_unavailable")
    return item  # Contents never leave the hashing stream or get copied/logged.


def old_registry_snapshot():
    """Bounded metadata only: default registry INIs and their config.ini, never disks."""
    root = Path(token_path()).parent / ".android" / "avd"
    safe_path(root, exists=False)
    if not root.exists():
        return {"registry": str(root), "exists": False, "names": [], "files": []}
    safe_path(root, directory=True)
    entries = sorted(root.glob("*.ini"))
    require(len(entries) <= 128, "old_registry_unbounded")
    files = []
    for p in entries:
        safe_path(p)
        require(p.stat().st_size <= 65536, "old_registry_unbounded")
        files.append(binding(p))
        value = ini(p.read_bytes())
        require("path" in value, "old_registry_invalid")
        config = safe_path(Path(value["path"]) / "config.ini")
        require(config.stat().st_size <= 262144, "old_registry_unbounded")
        files.append(binding(config))
    return {"registry": str(root), "exists": True, "names": [p.name for p in entries], "files": files}


def check_external_state(proposal):
    require(token_binding(proposal["token"]["path"]) == proposal["token"], "console_token_changed")
    require(old_registry_snapshot() == proposal["old_avd"], "old_registry_changed")


def scoped_env(proposal):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(
        ("ANDROID_", "JAVA_", "AVDMANAGER_", "HF_", "HUGGING_FACE_", "LLAMA_ARG_"))
        and k.upper() not in {"_JAVA_OPTIONS", "JDK_JAVA_OPTIONS"}}
    p = proposal["paths"]
    env.update(ANDROID_AVD_HOME=p["registry"], ANDROID_USER_HOME=p["android"],
               ANDROID_EMULATOR_HOME=p["emulator_home"], ANDROID_HOME=proposal["sdk"],
               ANDROID_SDK_ROOT=proposal["sdk"], JAVA_HOME=proposal["java_home"],
               TEMP=p["tmp"], TMP=p["tmp"])
    return env


def tree_files(root):
    root = safe_path(root, directory=True)
    result = []
    for p in sorted(root.rglob("*")):
        safe_path(p, directory=p.is_dir())
        if p.is_file():
            result.append(p)
    return result


def installation_files(sdk, java):
    sdk, java = Path(sdk), Path(java)
    files = [Path(__file__).resolve(), Path(host.__file__).resolve()]
    for folder in (sdk / "emulator", sdk / "cmdline-tools/latest",
                   sdk / "system-images/android-35/google_apis/x86_64", java,
                   sdk / "licenses", sdk / "platform-tools"):
        files.extend(tree_files(folder))
    return sorted(set(files))


def verify_installation(proposal):
    require({x["path"] for x in proposal["bindings"]} ==
            {str(p) for p in installation_files(proposal["sdk"], proposal["java_home"])}, "binding_set_changed")
    for item in proposal["bindings"]:
        check_binding(item)


def plan_prepare(root, sdk, java_home, output):
    require(os.name == "nt", "windows_required")
    p = paths(root)
    require(Path(root).drive.upper() == "D:" and not Path(root).exists(), "target_exists")
    sdk = safe_path(sdk, directory=True)
    java = safe_path(java_home, directory=True)
    image = sdk / "system-images/android-35/google_apis/x86_64"
    require((image / "data/empty_data_disk").is_file(), "factory_image_unsupported")
    files = installation_files(sdk, java)
    proposal = {"version": 1, "phase": "prepare", "avd_name": NAME,
                "serial": "emulator-%d" % PORT, "console_port": PORT,
                "sdk": str(sdk), "java_home": str(java), "paths": p,
                "adb_path": str(sdk / "platform-tools/adb.exe"),
                "token": token_binding(token_path()),
                "old_avd": old_registry_snapshot(),
                "bindings": [binding(x) for x in sorted(set(files))],
                "userdata_mib": 12288, "sdcard_mib": 8192,
                "memory_mib": 2048, "cores": 2,
                "host_free_min": {"C:": 16 * GIB, "D:": 40 * GIB},
                "host_available_memory_min": 4 * GIB,
                "allow_environment_calls": False, "root_go_pending": True}
    create_json(output, proposal)
    return proposal


def validate_proposal(proposal, phase):
    common = {"version", "phase", "avd_name", "serial", "console_port", "sdk", "java_home",
              "paths", "adb_path", "token", "old_avd", "bindings", "userdata_mib", "sdcard_mib",
              "memory_mib", "cores", "host_free_min", "host_available_memory_min",
              "allow_environment_calls", "root_go_pending"}
    extra = {"prepare_proposal", "prepared", "prepare_result", "max_seconds"} if phase == "run" else set()
    require(set(proposal) == common | extra and type(proposal["version"]) is int and proposal["version"] == 1 and
            proposal["phase"] == phase and proposal["avd_name"] == NAME and
            proposal["serial"] == "emulator-5592" and proposal["console_port"] == PORT and
            proposal["userdata_mib"] == 12288 and proposal["sdcard_mib"] == 8192 and
            proposal["memory_mib"] == 2048 and proposal["cores"] == 2 and
            proposal["allow_environment_calls"] is False and proposal["root_go_pending"] is True,
            "invalid_proposal")
    require(proposal["paths"] == paths(proposal["paths"]["root"]) and
            Path(proposal["paths"]["root"]).drive.upper() == "D:", "invalid_proposal")
    require(proposal["adb_path"] == str(Path(proposal["sdk"]) / "platform-tools/adb.exe"),
            "invalid_proposal")
    require(proposal["token"]["path"] == token_path(), "console_token_unavailable")
    require(proposal["host_free_min"] == {"C:": 16 * GIB, "D:": 40 * GIB} and
            proposal["host_available_memory_min"] == 4 * GIB, "invalid_proposal")
    items = proposal["bindings"]
    require(isinstance(items, list) and len({x["path"] for x in items}) == len(items), "invalid_proposal")
    required = {str(Path(__file__).resolve()), str(Path(host.__file__).resolve()), proposal["adb_path"],
                str(Path(proposal["sdk"]) / "emulator/emulator.exe"),
                str(Path(proposal["sdk"]) / "cmdline-tools/latest/bin/avdmanager.bat"),
                str(Path(proposal["sdk"]) / "system-images/android-35/google_apis/x86_64/data/empty_data_disk")}
    require(required <= {x["path"] for x in items}, "invalid_proposal")
    if phase == "run":
        require(type(proposal["max_seconds"]) is int and 0 < proposal["max_seconds"] <= MAX_SECONDS,
                "invalid_budget")


def authorize(proposal_path, authorization_path, phase):
    proposal = read_json(proposal_path)
    validate_proposal(proposal, phase)
    auth = read_json(authorization_path, 4096)
    check_authorization(auth, phase, digest(proposal_path))
    verify_installation(proposal)
    check_external_state(proposal)
    return proposal


def check_authorization(auth, phase, proposal_sha):
    require(auth == {"version": 1, "phase": phase, "proposal_sha256": proposal_sha,
                     "allow_environment_calls": True, "root_go_pending": False} and
            type(auth["version"]) is int and auth["allow_environment_calls"] is True and
            auth["root_go_pending"] is False, "not_authorized")


def resource_facts(proposal):
    require(os.name == "nt", "windows_required")
    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in ("total", "available", "page_total", "page_available",
                                                   "virtual_total", "virtual_available", "extended")]
    memory = Memory(); memory.length = ctypes.sizeof(memory)
    require(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)), "memory_unavailable")
    disks = {drive: shutil.disk_usage(drive + "\\").free for drive in proposal["host_free_min"]}
    require(all(disks[d] >= n for d, n in proposal["host_free_min"].items()) and
            memory.available >= proposal["host_available_memory_min"], "host_capacity")
    return {"free_bytes": disks, "available_memory": memory.available}


def ports_free():
    sockets = []
    try:
        for port in (PORT, PORT + 1):
            for family, address in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
                s = socket.socket(family, socket.SOCK_STREAM)
                sockets.append(s)
                if os.name == "nt":
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                if family == socket.AF_INET6:
                    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                s.bind((address, port))
    except OSError:
        raise EnvironmentRefused("ports_unavailable") from None
    finally:
        for s in sockets:
            s.close()


def prepare_command(proposal):
    # Direct java avoids cmd.exe interpolation and Java option injection.
    sdk = Path(proposal["sdk"])
    return [str(Path(proposal["java_home"]) / "bin/java.exe"),
            "-Dcom.android.sdkmanager.toolsdir=" + str(sdk / "cmdline-tools/latest"),
            "-cp", str(sdk / "cmdline-tools/latest/lib/avdmanager-classpath.jar"),
            "com.android.sdklib.tool.AvdManagerCli", "create", "avd", "-n", NAME,
            "-k", PACKAGE, "-p", proposal["paths"]["content"], "-c", "8192M"]


def emulator_command(proposal):
    sdk, content = Path(proposal["sdk"]), Path(proposal["paths"]["content"])
    return [str(sdk / "emulator/emulator.exe"), "-avd", NAME, "-sysdir",
            str(sdk / "system-images/android-35/google_apis/x86_64"), "-datadir", str(content),
            "-data", str(content / "userdata-qemu.img"), "-sdcard", str(content / "sdcard.img"),
            "-memory", "2048", "-cores", "2", "-ports", "5592,5593",
            "-no-window", "-no-audio", "-no-boot-anim", "-no-snapshot", "-no-snapshot-save",
            "-no-metrics", "-accel", "on", "-gpu", "swiftshader_indirect"]


def ini(data):
    result = {}
    for line in data.decode("utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        require("=" in line, "invalid_config")
        key, value = line.split("=", 1)
        require(key not in result, "invalid_config")
        result[key] = value
    return result


def normalize_generated_config(original, registry_bytes, content):
    """Only the known installed CLI profile, confined to this newly created AVD."""
    require(len(original) <= 262144 and len(registry_bytes) <= 65536, "invalid_config")
    values, registry = ini(original), ini(registry_bytes)
    require(registry == {"avd.ini.encoding": "UTF-8", "path": str(content), "target": "android-35"},
            "invalid_registry")
    require(values.get("abi.type") == "x86_64" and values.get("hw.cpu.arch") == "x86_64" and
            values.get("tag.id") == "google_apis" and values.get("avd.ini.encoding") == "UTF-8" and
            values.get("image.sysdir.1", "").replace("\\", "/") ==
            "system-images/android-35/google_apis/x86_64/", "invalid_config")
    require(values.get("AvdId") in (None, NAME) and
            all(values.get(key) in ("<build>", NAME) for key in ("avd.id", "avd.name")), "invalid_config")
    require(values.get("disk.dataPartition.path") in ("<temp>", str(content / "userdata-qemu.img")) and
            values.get("disk.dataPartition.initPath", "") == "" and
            values.get("disk.cachePartition.path") in (None, "<temp>", str(content / "cache.img")) and
            values.get("sdcard.path") in (None, str(content / "sdcard.img")), "invalid_config")
    values.update({"AvdId": NAME, "avd.id": NAME, "avd.name": NAME,
                   "disk.dataPartition.path": str(content / "userdata-qemu.img"),
                   "disk.dataPartition.size": "12G", "disk.cachePartition.path": str(content / "cache.img"),
                   "hw.ramSize": "2048", "hw.cpu.ncore": "2", "hw.sdCard": "yes",
                   "sdcard.path": str(content / "sdcard.img"), "sdcard.size": "8192M",
                   "fastboot.forceColdBoot": "yes", "fastboot.forceFastBoot": "no",
                   "fastboot.forceChosenSnapshotBoot": "no", "firstboot.bootFromDownloadableSnapshot": "no",
                   "firstboot.bootFromLocalSnapshot": "no", "firstboot.saveToLocalSnapshot": "no"})
    return "".join(k + "=" + values[k] + "\n" for k in sorted(values)).encode("utf-8")


def prepare(proposal_path, authorization_path):
    admitted_sha = digest(proposal_path)
    proposal = authorize(proposal_path, authorization_path, "prepare")
    require(digest(proposal_path) == admitted_sha, "proposal_changed")
    root = Path(proposal["paths"]["root"])
    require(not root.exists(), "target_exists")
    facts = resource_facts(proposal)
    # Every path below belongs exclusively to this newly created target.
    root.mkdir()
    create_json(root / "prepare-start-v1.json", {"proposal_sha256": admitted_sha, "facts": facts,
                                               "owner": process_identity(os.getpid())})
    pending = None; failure = None; closure = False
    try:
        pending = prepare_contents(proposal, proposal_path, authorization_path, admitted_sha)
    except BaseException as error:
        failure = error
    try:
        require(digest(proposal_path) == admitted_sha, "proposal_changed")
        verify_installation(proposal)
        check_external_state(proposal)
        closure = True
    except BaseException as error:
        if failure is None:
            failure = error
    if failure is None:
        create_json(root / "prepared-v1.json", pending)
    client = root / "prepare-client-v1.json"
    known = client.exists() and read_json(client).get("cleanup_complete") is True
    create_json(root / "prepare-result-v1.json", {"version": 1, "proposal_sha256": admitted_sha,
                "status": "completed" if failure is None else "refused", "closure_verified": closure,
                "child_cleanup_complete": known, "prepared_created": failure is None})
    if failure is not None:
        raise failure
    return pending


def prepare_contents(proposal, proposal_path, authorization_path, admitted_sha):
    root = Path(proposal["paths"]["root"])
    for name in ("registry", "android", "emulator_home", "tmp"):
        Path(proposal["paths"][name]).mkdir()
    (root / "content").mkdir()
    result = host.run_process([sys.executable, "-B", str(Path(__file__).resolve()), "_prepare-worker"],
                              request=encoded({"proposal": str(Path(proposal_path).resolve()),
                                               "proposal_sha256": admitted_sha,
                                               "authorization": str(Path(authorization_path).resolve())}),
                              deadline=180, max_output=MAX_OUTPUT)
    with (root / "prepare-stdout-v1.bin").open("xb") as stream:
        stream.write(result.stdout); stream.flush(); os.fsync(stream.fileno())
    create_json(root / "prepare-client-v1.json", {"status": result.status, "returncode": result.returncode,
                "cleanup_complete": result.cleanup_complete, "elapsed_ms": result.elapsed_ms,
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(), "stderr_bytes": result.stderr_bytes})
    require(result.status == "completed" and result.returncode == 0 and result.cleanup_complete,
            "prepare_failed")
    content = safe_path(proposal["paths"]["content"], directory=True)
    config = safe_path(content / "config.ini")
    original = config.read_bytes()
    registry = safe_path(Path(proposal["paths"]["registry"]) / (NAME + ".ini"))
    normalized = normalize_generated_config(original, registry.read_bytes(), content)
    require(not safe_path(content / "userdata-qemu.img", exists=False).exists() and
            8 * GIB <= safe_path(content / "sdcard.img").stat().st_size <= 8 * GIB + 1024 * 1024,
            "invalid_initial_disks")
    with (content / "config.created.ini").open("xb") as stream:
        stream.write(original); stream.flush(); os.fsync(stream.fileno())
    # The only replacement write is this freshly generated config, with its original retained.
    with config.open("wb") as stream:
        stream.write(normalized)
        stream.flush(); os.fsync(stream.fileno())
    prepared = {"version": 1, "proposal_sha256": admitted_sha, "avd_name": NAME,
                "immutable": [binding(config), binding(registry), binding(content / "config.created.ini")],
                "initial_sdcard": binding(content / "sdcard.img"), "userdata_absent": True,
                "guest_boot_verified": False, "facts": resource_facts(proposal)}
    return prepared


def plan_run(prepare_proposal, prepared_path, output, max_seconds=MAX_SECONDS):
    source = read_json(prepare_proposal)
    validate_proposal(source, "prepare")
    prepared = read_json(prepared_path)
    require(prepared["proposal_sha256"] == digest(prepare_proposal) and
            str(Path(prepared_path)) == str(Path(source["paths"]["root"]) / "prepared-v1.json"),
            "prepared_changed")
    proposal = dict(source)
    proposal.update(phase="run", prepare_proposal=binding(prepare_proposal),
                    prepared=binding(prepared_path),
                    prepare_result=binding(Path(source["paths"]["root"]) / "prepare-result-v1.json"),
                    max_seconds=max_seconds)
    validate_proposal(proposal, "run")
    verify_prepared(proposal, initial=True)
    create_json(output, proposal)
    return proposal


def process_identity(pid):
    require(os.name == "nt" and type(pid) is int and pid > 0, "process_unavailable")
    from ctypes import wintypes as w
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]; k.OpenProcess.restype = w.HANDLE
    k.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
    k.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
    k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
    k.CloseHandle.argtypes = [w.HANDLE]
    handle = k.OpenProcess(0x1000, False, pid)
    require(bool(handle), "process_unavailable")
    try:
        times = [w.FILETIME() for _ in range(4)]; code = w.DWORD()
        buffer = ctypes.create_unicode_buffer(32768); length = w.DWORD(len(buffer))
        require(k.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)) and
                k.GetExitCodeProcess(handle, ctypes.byref(code)) and code.value == 259 and
                k.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)), "process_unavailable")
        return {"pid": pid, "creation_filetime": (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
                "executable": buffer.value}
    finally:
        k.CloseHandle(handle)


def verify_prepared(proposal, initial=False):
    check_binding(proposal["prepare_proposal"]); check_binding(proposal["prepared"])
    check_binding(proposal["prepare_result"])
    original = read_json(proposal["prepare_proposal"]["path"])
    validate_proposal(original, "prepare")
    require({k: v for k, v in proposal.items() if k not in
             {"phase", "prepare_proposal", "prepared", "prepare_result", "max_seconds"}} ==
            {k: v for k, v in original.items() if k != "phase"}, "prepared_changed")
    prepared = read_json(proposal["prepared"]["path"])
    root = Path(proposal["paths"]["root"])
    content = Path(proposal["paths"]["content"])
    require(proposal["prepare_result"]["path"] == str(root / "prepare-result-v1.json") and
            read_json(proposal["prepare_result"]["path"]) ==
            {"version": 1, "proposal_sha256": proposal["prepare_proposal"]["sha256"], "status": "completed",
             "closure_verified": True, "child_cleanup_complete": True, "prepared_created": True},
            "prepared_changed")
    require(set(prepared) == {"version", "proposal_sha256", "avd_name", "immutable", "initial_sdcard",
                              "userdata_absent", "guest_boot_verified", "facts"} and
            prepared["version"] == 1 and prepared["avd_name"] == NAME and
            prepared["userdata_absent"] is True and prepared["guest_boot_verified"] is False and
            prepared["proposal_sha256"] == proposal["prepare_proposal"]["sha256"] and
            proposal["prepared"]["path"] == str(root / "prepared-v1.json") and
            {x["path"] for x in prepared["immutable"]} ==
            {str(content / "config.ini"), str(content / "config.created.ini"),
             str(Path(proposal["paths"]["registry"]) / (NAME + ".ini"))} and
            len(prepared["immutable"]) == 3 and
            prepared["initial_sdcard"]["path"] == str(content / "sdcard.img"), "prepared_changed")
    for item in prepared["immutable"]:
        check_binding(item)
    if initial:
        check_binding(prepared["initial_sdcard"])
        require(not (Path(proposal["paths"]["content"]) / "userdata-qemu.img").exists(), "target_used")
    return prepared


class LiveOwnerLease:
    def __init__(self, proposal_path, running_path, expected_running_sha256):
        self.proposal_path, self.running_path = str(proposal_path), str(running_path)
        require(digest(running_path) == expected_running_sha256, "descriptor_changed")
        self.running_sha = expected_running_sha256
        self.proposal_sha = digest(proposal_path)
        self.proposal = read_json(proposal_path)
        validate_proposal(self.proposal, "run")
        verify_installation(self.proposal)
        check_external_state(self.proposal)
        self._descriptor = read_json(running_path, 16384)
        self.check()

    @property
    def descriptor(self):
        return json.loads(json.dumps(self._descriptor))

    def check(self):
        try:
            self._check()
        except EnvironmentRefused:
            raise
        except (OSError, ValueError, KeyError, TypeError):
            raise EnvironmentRefused("invalid_owner") from None

    def _check(self):
        p, d = self.proposal, self._descriptor
        require(digest(self.proposal_path) == self.proposal_sha and digest(self.running_path) == self.running_sha,
                "descriptor_changed")
        require(set(d) == {"version", "proposal_sha256", "prepared_sha256", "avd_name", "serial",
                          "console_port", "adb_path", "root", "content", "registry", "owner", "worker",
                          "launcher", "started_epoch", "deadline_epoch", "guest_boot_verified"} and
                d["version"] == 1 and d["proposal_sha256"] == self.proposal_sha and
                d["prepared_sha256"] == p["prepared"]["sha256"] and d["avd_name"] == NAME and
                d["serial"] == p["serial"] and d["console_port"] == PORT and
                d["adb_path"] == p["adb_path"] and d["guest_boot_verified"] is False and
                all(d[k] == p["paths"][k] for k in ("root", "content", "registry")), "invalid_descriptor")
        require(type(d["started_epoch"]) in (int, float) and type(d["deadline_epoch"]) in (int, float) and
                0 < d["deadline_epoch"] - d["started_epoch"] <= p["max_seconds"] and
                d["started_epoch"] <= time.time() < d["deadline_epoch"], "owner_expired")
        root = Path(d["root"])
        require(str(Path(self.running_path)) == str(root / "running-v1.json") and
                not (root / "stop-v1.json").exists() and not (root / "owner-result-v1.json").exists(),
                "owner_stopped")
        verify_prepared(p)
        for name in ("owner", "worker", "launcher"):
            require(process_identity(d[name]["pid"]) == d[name], "owner_lost")
        require(d["owner"]["executable"].lower() == str(Path(sys.executable)).lower() and
                d["worker"]["executable"].lower() == str(Path(sys.executable)).lower() and
                d["launcher"]["executable"].lower() == str(Path(p["sdk"]) / "emulator/emulator.exe").lower(),
                "owner_lost")


def open_live_owner(proposal_path, running_path, expected_running_sha256):
    try:
        return LiveOwnerLease(proposal_path, running_path, expected_running_sha256)
    except EnvironmentRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError):
        raise EnvironmentRefused("invalid_owner") from None


def supervise(command, request, root, seconds, on_started, stop_proposal_sha256=None):
    """Barrier child is assigned before request. Ordinary exit also kills descendants."""
    require(os.name == "nt" and type(seconds) is int and 0 < seconds <= MAX_SECONDS and
            len(request) <= 131072, "invalid_budget")
    child = None; job = None; readers = []; chunks = [bytearray(), bytearray()]
    overflow = threading.Event(); lock = threading.Lock(); status = "spawn_failed"; cleaned = False
    started = time.monotonic()
    try:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 bufsize=0, creationflags=subprocess.CREATE_NO_WINDOW)
        job = host.WindowsJob(child.pid)
        def drain(stream, channel):
            try:
                while True:
                    data = stream.read(4096)
                    if not data:
                        break
                    with lock:
                        left = MAX_OUTPUT - sum(map(len, chunks))
                        chunks[channel].extend(data[:max(0, left)])
                        if len(data) > left:
                            overflow.set(); break
            except (OSError, ValueError):
                pass
        for index, stream in enumerate((child.stdout, child.stderr)):
            t = threading.Thread(target=drain, args=(stream, index), daemon=True)
            readers.append(t); t.start()
        child.stdin.write(request); child.stdin.close()
        status = "running"; announced = False
        while True:
            if overflow.is_set():
                status = "output_limit"; break
            if time.monotonic() - started >= seconds:
                status = "expired"; break
            if child.poll() is not None:
                status = "child_exited"; break
            if not announced:
                announced = on_started(child)
            stop = root / "stop-v1.json"
            if stop.exists():
                require(type(stop_proposal_sha256) is str and read_json(stop, 4096) ==
                        {"version": 1, "proposal_sha256": stop_proposal_sha256, "action": "stop"},
                        "invalid_stop")
                status = "stop_requested"; break
            time.sleep(.05)
    except KeyboardInterrupt:
        status = "cancelled"
    except (EnvironmentRefused, OSError, ValueError, KeyError, TypeError):
        status = "owner_failed"
    finally:
        if child is not None:
            if job is not None:
                cleaned = job.close()
            else:
                child.kill(); cleaned = True  # Barrier has not been released.
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cleaned = False
            for t in readers:
                t.join(timeout=2)
            cleaned = cleaned and not any(t.is_alive() for t in readers)
            if cleaned:
                for stream in (child.stdin, child.stdout, child.stderr):
                    stream.close()
        for index, name in enumerate(("owner-stdout-v1.bin", "owner-stderr-v1.bin")):
            with (root / name).open("xb") as stream:
                stream.write(chunks[index]); stream.flush(); os.fsync(stream.fileno())
    return {"status": status, "cleanup_complete": cleaned,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "worker_returncode": child.returncode if child else None,
            "stdout_bytes": len(chunks[0]), "stderr_bytes": len(chunks[1])}


def run(proposal_path, authorization_path):
    admitted_sha = digest(proposal_path)
    proposal = authorize(proposal_path, authorization_path, "run")
    require(digest(proposal_path) == admitted_sha, "proposal_changed")
    verify_prepared(proposal, initial=True)
    facts = resource_facts(proposal); ports_free()
    root = Path(proposal["paths"]["root"])
    require(not any((root / name).exists() for name in
                    ("run-start-v1.json", "running-v1.json", "worker-start-v1.json", "stop-v1.json", "owner-result-v1.json")),
            "target_used")
    create_json(root / "run-start-v1.json", {"proposal_sha256": admitted_sha, "facts": facts,
                                           "owner": process_identity(os.getpid())})
    started_epoch = time.time(); owner = process_identity(os.getpid())
    def announce(child):
        worker_path = root / "worker-start-v1.json"
        if not worker_path.exists():
            return False
        # Worker receipt is published after launcher spawn; retry only partially written local JSON.
        try:
            worker = read_json(worker_path, 4096)
        except EnvironmentRefused:
            return False
        require(worker["worker"] == process_identity(child.pid) and
                worker["proposal_sha256"] == admitted_sha and digest(proposal_path) == admitted_sha, "worker_changed")
        d = {"version": 1, "proposal_sha256": admitted_sha,
             "prepared_sha256": proposal["prepared"]["sha256"], "avd_name": NAME,
             "serial": proposal["serial"], "console_port": PORT, "adb_path": proposal["adb_path"],
             "root": str(root), "content": proposal["paths"]["content"],
             "registry": proposal["paths"]["registry"], "owner": owner,
             "worker": worker["worker"], "launcher": worker["launcher"],
             "started_epoch": started_epoch, "deadline_epoch": started_epoch + proposal["max_seconds"],
             "guest_boot_verified": False}
        create_json(root / "running-v1.json", d)
        print(json.dumps({"running": True, "guest_boot_verified": False}), flush=True)
        return True
    result = supervise([sys.executable, "-B", str(Path(__file__).resolve()), "_run-worker"],
                       encoded({"proposal": str(Path(proposal_path).resolve()), "proposal_sha256": admitted_sha,
                                "authorization": str(Path(authorization_path).resolve())}), root,
                       proposal["max_seconds"], announce, admitted_sha)
    result["proposal_sha256"] = admitted_sha
    result["guest_flush_claimed"] = False
    result["closure_verified"] = False
    try:
        if result["status"] == "stop_requested":
            require(read_json(root / "stop-v1.json", 4096) ==
                    {"version": 1, "proposal_sha256": admitted_sha, "action": "stop"}, "invalid_stop")
        # Closure rehash happens only after every owned descendant is known terminal.
        require(result["cleanup_complete"], "cleanup_unknown")
        require(digest(proposal_path) == admitted_sha, "proposal_changed")
        verify_installation(proposal)
        check_external_state(proposal)
        verify_prepared(proposal)
        result["closure_verified"] = True
    except (EnvironmentRefused, OSError, ValueError, KeyError, TypeError):
        result["status"] = "closure_failed"
    create_json(root / "owner-result-v1.json", result)
    return result


def worker(mode):
    # stdin is the only release barrier; no SDK launch before parent job assignment.
    raw = sys.stdin.buffer.read(131073)
    require(0 < len(raw) <= 131072, "invalid_request")
    request = decode_json(raw)
    require(set(request) == {"proposal", "proposal_sha256", "authorization"}, "invalid_request")
    proposal = read_bound_json(request["proposal"], request["proposal_sha256"])
    phase = "prepare" if mode == "_prepare-worker" else "run"
    validate_proposal(proposal, phase)
    check_authorization(read_json(request["authorization"], 4096), phase, request["proposal_sha256"])
    root = Path(proposal["paths"]["root"])
    start = read_json(root / (phase + "-start-v1.json"), 8192)
    require(start["proposal_sha256"] == request["proposal_sha256"] and
            process_identity(start["owner"]["pid"]) == start["owner"], "owner_lost")
    create_json(root / (phase + "-worker-claimed-v1.json"),
                {"proposal_sha256": request["proposal_sha256"], "worker": process_identity(os.getpid())})
    if mode == "_prepare-worker":
        return subprocess.run(prepare_command(proposal), input=b"no\n",
                              env=scoped_env(proposal)).returncode
    child = subprocess.Popen(emulator_command(proposal), stdin=subprocess.DEVNULL, env=scoped_env(proposal),
                             creationflags=subprocess.CREATE_NO_WINDOW)
    create_json(root / "worker-start-v1.json", {"proposal_sha256": request["proposal_sha256"],
                "worker": process_identity(os.getpid()), "launcher": process_identity(child.pid)})
    # Do not return when launcher exits: an exited launcher is loss, never detached success.
    while child.poll() is None:
        time.sleep(.1)
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("plan-prepare", "prepare", "plan-run", "run",
                                          "_prepare-worker", "_run-worker"))
    for name in ("proposal", "authorization", "root", "sdk", "java-home", "output", "prepared"):
        parser.add_argument("--" + name)
    args = parser.parse_args(argv)
    try:
        if args.phase.startswith("_"):
            return worker(args.phase)
        if args.phase == "plan-prepare":
            plan_prepare(args.root, args.sdk, args.java_home, args.output)
        elif args.phase == "prepare":
            prepare(args.proposal, args.authorization)
        elif args.phase == "plan-run":
            plan_run(args.proposal, args.prepared, args.output)
        else:
            result = run(args.proposal, args.authorization)
            return 0 if (result["status"] == "stop_requested" and result["cleanup_complete"] and
                         result["closure_verified"]) else 2
        return 0
    except EnvironmentRefused as error:
        reason = str(error)
        print(json.dumps({"status": "refused", "reason": reason if re.fullmatch(r"[a-z_]{1,64}", reason)
                          else "invalid_environment"}), flush=True)
        return 2
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"status": "refused"}), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
