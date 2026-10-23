#!/usr/bin/env python3
"""Compare two clean Windows normal developer packages; never launch app/models.

Use already provisioned reviewed tools/dependencies and a clean committed checker.
Outputs/worktrees are retained, including failures. No install, fetch or cleanup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE = 128 * 1024 * 1024
MAX_TREE = 512 * 1024 * 1024
MAX_FILES = 20000
TOOLCHAIN = "+1.93.1"
ENV_KEYS = ("PATH", "INCLUDE", "LIB", "LIBPATH", "VCToolsVersion",
            "WindowsSDKVersion", "VSCMD_ARG_TGT_ARCH", "NODE_OPTIONS", "RUST_LOG")
OVERRIDES = ("TAURI_CONFIG", "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC_WRAPPER",
             "RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_RUSTFLAGS", "CARGO_BUILD_TARGET",
             "CC", "CXX", "CFLAGS", "CXXFLAGS", "CL", "_CL_", "LINK")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def ordinary(path: Path, cap: int = MAX_FILE) -> bytes:
    for parent in (path, *path.parents):
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Reparse input: {parent.name}")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > cap:
        raise ValueError(f"Invalid ordinary file: {path.name}")
    return path.read_bytes()


def fingerprint(path: Path, cap: int = MAX_FILE) -> dict:
    data = ordinary(path, cap)
    return {"sha256": sha(data), "bytes": len(data)}


def tool_identity(path: Path) -> dict:
    resolved = path.resolve(strict=True)
    if resolved != path.absolute() and not (
        path.name.lower() in {"cargo.exe", "rustc.exe"}
        and resolved.name.lower() == "rustup.exe"
        and resolved.parent == path.parent
    ):
        raise ValueError("Unexpected tool indirection")
    return {"path": str(path), "resolved_path": str(resolved), **fingerprint(resolved)}


def tree_inventory(root: Path) -> dict:
    if not root.is_dir():
        raise ValueError("Missing input tree")
    result, size = {}, 0
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            candidate = Path(parent) / name
            info = candidate.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("Reparse tree member")
        for name in sorted(files):
            path = Path(parent) / name
            item = fingerprint(path)
            result[path.relative_to(root).as_posix()] = item
            size += item["bytes"]
            if len(result) > MAX_FILES or size > MAX_TREE:
                raise ValueError("Input tree budget")
    return dict(sorted(result.items()))


def command(args: list[str], cwd: Path, env: dict | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, env=env, check=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    if len(result.stdout.encode()) > 16 * 1024 * 1024:
        raise ValueError("Command response budget")
    return result.stdout.strip()


def clean_source(root: Path, commit: str) -> dict:
    if command(["git", "rev-parse", "HEAD"], root) != commit:
        raise ValueError("Source revision drift")
    if command(["git", "status", "--porcelain", "--untracked-files=all"], root):
        raise ValueError("Source must be committed and clean")
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    return {name: fingerprint(root / name) for name in sorted(names) if name}


def dependency_inventory(root: Path, lock: dict) -> dict:
    inventory = tree_inventory(root)
    installed = json.loads(ordinary(root / ".package-lock.json", 4 * 1024 * 1024))
    actual_packages = installed.get("packages", {})
    expected = lock["packages"]
    if not actual_packages:
        raise ValueError("Missing installed lock inventory")
    versions = {}
    for name, metadata in actual_packages.items():
        if not name.startswith("node_modules/") or name not in expected:
            raise ValueError("Unexpected installed dependency")
        wanted = expected[name]
        for field in ("version", "integrity", "resolved"):
            if metadata.get(field) != wanted.get(field):
                raise ValueError("Installed lock differs from source lock")
        relative = name.removeprefix("node_modules/")
        package = json.loads(ordinary(root / relative / "package.json", 1024 * 1024))
        if package.get("version") != wanted.get("version"):
            raise ValueError("Installed package version differs")
        versions[name] = wanted["version"]
    for name, metadata in expected.items():
        if name and name not in actual_packages and not metadata.get("optional"):
            raise ValueError("Missing nonoptional dependency")
    return {"files": inventory, "versions": versions,
            "verification": "installed lock fields and package versions; file hashes bind supplied tree, not registry authenticity"}


def tool_inventory(args: argparse.Namespace, env: dict) -> dict:
    paths = {"node": args.node, "npm_cli": args.npm_cli, "python": Path(sys.executable)}
    for name in ("git", "cargo", "rustc", "cl", "link", "lib", "rc", "mt", "dumpbin"):
        found = shutil.which(name, path=env["PATH"])
        if not found:
            raise ValueError(f"Missing build tool: {name}")
        paths[name] = Path(found)
    files = {name: tool_identity(path) for name, path in paths.items()}
    versions = {
        "node": command([str(args.node), "--version"], ROOT, env),
        "npm": command([str(args.node), str(args.npm_cli), "--version"], ROOT, env),
        "python": sys.version,
        "rust": command(["rustc", TOOLCHAIN, "-vV"], ROOT, env),
        "cargo": command(["cargo", TOOLCHAIN, "--version", "--verbose"], ROOT, env),
        "git": command(["git", "--version"], ROOT, env),
        "esbuild": command([str(args.node), str(args.dependencies / "esbuild/bin/esbuild"),
                            "--version"], ROOT, env),
    }
    # Invoke no source/compiler workload: /? identifies the actual installed tools.
    for name in ("cl", "link", "lib", "rc", "mt", "dumpbin"):
        result = subprocess.run([str(paths[name]), "/?"], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, env=env, check=False)
        versions[name] = {"exit": result.returncode, "banner": result.stdout[:4096].decode("utf-8", "replace")}
    if versions["node"] != "v24.22.1" or versions["npm"] != "11.19.1" or sys.version_info[:3] != (3, 14, 9):
        raise ValueError("Use pinned Node24.22.1/npm11.19.1/Python3.14.9")
    if "host: x86_64-pc-windows-msvc" not in versions["rust"]:
        raise ValueError("Expected Windows x64 MSVC Rust host")
    # rustup proxy hashes alone do not identify the selected compiler/stdlib.
    sysroot = Path(command(["rustc", TOOLCHAIN, "--print", "sysroot"], ROOT, env))
    selected_rust = {p.name: {"path": str(p), **fingerprint(p, MAX_TREE)}
                     for p in (sysroot / "bin").iterdir() if p.is_file() and p.suffix.lower() in {".exe", ".dll"}}
    configs = {}
    for directory in {ROOT, *ROOT.parents, Path(os.environ.get("CARGO_HOME", Path.home() / ".cargo"))}:
        for path in (directory / ".cargo/config", directory / ".cargo/config.toml",
                     directory / "config.toml" if directory.name == ".cargo" else directory / ".cargo/unused-config-placeholder"):
            if path.is_file():
                configs[str(path)] = fingerprint(path)
    return {"files": files, "versions": versions, "selected_rust": selected_rust,
            "cargo_config_hashes": configs, "environment": {k: env.get(k, "") for k in ENV_KEYS}}


def pe_inventory(data: bytes) -> dict:
    if len(data) < 64 or data[:2] != b"MZ":
        raise ValueError("Invalid PE")
    start = struct.unpack_from("<I", data, 0x3C)[0]
    if start + 24 > len(data) or data[start:start + 4] != b"PE\0\0":
        raise ValueError("Invalid PE header")
    machine, count, timestamp, _, _, optional, flags = struct.unpack_from("<HHIIIHH", data, start + 4)
    section_start = start + 24 + optional
    if count > 96 or section_start + count * 40 > len(data):
        raise ValueError("Invalid PE sections")
    sections = []
    for offset in range(section_start, section_start + count * 40, 40):
        name, virtual_size, address, size, raw = struct.unpack_from("<8sIIII", data, offset)
        if raw + size > len(data):
            raise ValueError("Invalid PE section range")
        sections.append({"name": name.rstrip(b"\0").decode("ascii", "replace"),
                         "virtual_size": virtual_size, "virtual_address": address,
                         "raw_offset": raw, "raw_bytes": size,
                         "sha256": sha(data[raw:raw + size])})
    return {"machine": machine, "timestamp_or_brepro_hash": timestamp,
            "characteristics": flags, "sections": sections}


def compare_bytes(left: bytes, right: bytes) -> dict:
    first = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), None)
    if first is None and len(left) != len(right):
        first = min(len(left), len(right))
    return {"equal": left == right, "first_different_offset": first,
            "left": {"bytes": len(left), "sha256": sha(left)},
            "right": {"bytes": len(right), "sha256": sha(right)}}


def zip_inventory(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as archive:
        if len(archive.infolist()) > 2048:
            raise ValueError("Archive count budget")
        result = []
        total = 0
        for entry in archive.infolist():
            total += entry.file_size
            if total > 256 * 1024 * 1024:
                raise ValueError("Archive bytes budget")
            row = {key: getattr(entry, key) for key in (
                "filename", "date_time", "compress_type", "flag_bits", "create_system",
                "create_version", "extract_version", "reserved", "volume", "internal_attr",
                "external_attr", "header_offset", "CRC", "compress_size", "file_size")}
            row.update(extra_hex=entry.extra.hex(), comment_hex=entry.comment.hex(),
                       sha256=sha(archive.read(entry)))
            result.append(row)
        return result


def compare_packages(left: Path, right: Path) -> dict:
    left_zip, right_zip = left.with_suffix(".zip"), right.with_suffix(".zip")
    a, b = zip_inventory(left_zip), zip_inventory(right_zip)
    a_by_name, b_by_name = {e["filename"]: e for e in a}, {e["filename"]: e for e in b}
    changed = [name for name in sorted(a_by_name.keys() | b_by_name.keys())
               if a_by_name.get(name) != b_by_name.get(name)]
    executable = compare_bytes(ordinary(left / "LocalLore Desktop.exe"), ordinary(right / "LocalLore Desktop.exe"))
    archive = compare_bytes(ordinary(left_zip), ordinary(right_zip))
    folder_a, folder_b = tree_inventory(left), tree_inventory(right)
    return {"equal": executable["equal"] and archive["equal"] and a == b and folder_a == folder_b,
            "executable": executable, "archive": archive, "zip_metadata_and_member_order_equal": a == b,
            "changed_zip_members_or_metadata": changed, "folder_inventory_equal": folder_a == folder_b,
            "left_pe": pe_inventory(ordinary(left / "LocalLore Desktop.exe")),
            "right_pe": pe_inventory(ordinary(right / "LocalLore Desktop.exe")),
            "left_zip_members": a, "right_zip_members": b}


def validate_destination(output: Path, inputs: list[Path]) -> None:
    if not output.is_absolute() or output.exists():
        raise ValueError("Choose a new absolute output directory")
    for parent in output.parents:
        if parent.exists() and (parent.is_symlink() or getattr(parent.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Reparse output ancestor")
    for source in inputs:
        if output.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(output.resolve()):
            raise ValueError("Output overlaps inputs")
    if any(ord(c) > 127 for c in str(output)):
        raise ValueError("This cohort supports ASCII/space build paths only")


def write_new(path: Path, value: object) -> None:
    data = encode(value)
    if len(data) > 16 * 1024 * 1024:
        raise ValueError("Evidence budget")
    with path.open("xb") as handle:
        handle.write(data)


def build_one(source: Path, directory: Path, args: argparse.Namespace, tools: dict,
              source_files: dict, dependencies: dict, env: dict) -> dict:
    directory.mkdir()
    target, temporary = directory / "native target", directory / "private temp"
    target.mkdir()
    temporary.mkdir()
    shutil.copytree(args.dependencies, source / "apps/desktop/node_modules")
    if tree_inventory(source / "apps/desktop/node_modules") != dependencies["files"]:
        raise ValueError("Dependency copy differs")
    local_env = {**env, "TEMP": str(temporary), "TMP": str(temporary)}
    package = directory / "normal developer folder"
    argv = [sys.executable, "-X", "utf8", str(source / "scripts/desktop-package.py"), "build",
            "--node", str(args.node), "--npm-cli", str(args.npm_cli),
            "--target-dir", str(target), "--worker", str(args.worker), "--output", str(package)]
    started = time.monotonic()
    with (directory / "build.log").open("xb") as log:
        result = subprocess.run(argv, cwd=source, env=local_env, stdout=log,
                                stderr=subprocess.STDOUT, check=False)
    manifest = {"source": str(source), "target_initially_empty": True,
                "no_reused_object_archive_or_target_cache": True,
                "argv": argv, "exit": result.returncode,
                "elapsed_ms": int((time.monotonic() - started) * 1000),
                "tools": tools, "source_files": source_files,
                "dependency_files_sha256": sha(encode(dependencies["files"])),
                "packager_sha256": fingerprint(source / "scripts/desktop-package.py"),
                "build_log": fingerprint(directory / "build.log")}
    if result.returncode:
        write_new(directory / "manifest.json", manifest)
        raise ValueError("Normal package build failed; see retained build.log")
    manifest["verify"] = json.loads(command([sys.executable, "-X", "utf8",
        str(source / "scripts/desktop-package.py"), "verify", str(package.with_suffix(".zip"))], source, local_env))
    manifest["normal_frontend"] = tree_inventory(source / "apps/desktop/dist")
    if not manifest["normal_frontend"].get("app.js", {}).get("bytes"):
        raise ValueError("Missing normal frontend")
    manifest["source_after"] = clean_source(source, args.source_commit)
    if manifest["source_after"] != source_files:
        raise ValueError("Source drift during build")
    if tree_inventory(source / "apps/desktop/node_modules") != dependencies["files"]:
        raise ValueError("Dependency drift during build")
    manifest["pe"] = pe_inventory(ordinary(package / "LocalLore Desktop.exe"))
    packaged_manifest = json.loads(ordinary(package / "build-manifest.json", 2 * 1024 * 1024))
    selected_dependencies = json.loads(ordinary(package / "NOTICES/rust-inventory.json", 2 * 1024 * 1024))
    manifest["license_and_target_audit"] = {
        "license_audit_complete": packaged_manifest["license_audit_complete"],
        "selected_rust_packages": selected_dependencies,
        "selected_glib": [item for item in selected_dependencies if item["name"] == "glib"],
        "scope": "actual packager Windows-selected graph/notices; no advisory fix or dismissal; native/embedded license audit remains open",
    }
    manifest["pe_imports"] = command([tools["files"]["dumpbin"]["path"], "/imports",
                                     str(package / "LocalLore Desktop.exe")], source, local_env)
    write_new(directory / "manifest.json", manifest)
    return manifest


def run(args: argparse.Namespace) -> dict:
    if sys.platform != "win32" or not re.fullmatch(r"[0-9a-f]{40}", args.source_commit):
        raise ValueError("Windows x64 and exact lowercase source SHA required")
    for key in OVERRIDES:
        if os.environ.get(key):
            raise ValueError(f"Remove build override: {key}")
    for name in ("node", "npm_cli", "dependencies", "worker", "output"):
        setattr(args, name, getattr(args, name).absolute())
    validate_destination(args.output, [ROOT, args.dependencies, args.worker, args.node, args.npm_cli])
    worker = ordinary(args.worker, 16 * 1024 * 1024)
    if sha(worker) != "b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434":
        raise ValueError("UnapprovedWorker")
    checker_commit = command(["git", "rev-parse", "HEAD"], ROOT)
    checker_files = clean_source(ROOT, checker_commit)
    env = {**os.environ, "PATH": str(args.node.parent) + os.pathsep + os.environ["PATH"],
           "CARGO_PROFILE_DEV_DEBUG": "0", "CARGO_PROFILE_TEST_DEBUG": "0",
           "CARGO_INCREMENTAL": "0", "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD": "1"}
    tools = tool_inventory(args, env)
    # Source lock is read from the frozen tree, not the external checker's revision.
    lock = json.loads(subprocess.check_output(["git", "show", f"{args.source_commit}:apps/desktop/package-lock.json"], cwd=ROOT))
    dependencies = dependency_inventory(args.dependencies, lock)
    args.output.mkdir(parents=True)
    report = {"version": 1, "status": "incomplete", "source_commit": args.source_commit,
              "checker_commit": checker_commit, "checker_files": checker_files,
              "checker_sha256": fingerprint(Path(__file__)), "worker_sha256": sha(worker),
              "models_read_or_loaded": False, "application_launched": False,
              "qualification": "same installed tools, two clean ASCII/space source/target paths only",
              "normalizer": "none; every packaged member including manifest participates",
              "noncomparable_evidence": "external manifests/log paths/elapsed times are not packaged",
              "tools": tools, "dependencies": dependencies, "builds": []}
    try:
        for label in ("first source", "second longer source"):
            source = args.output / label / "source tree"
            source.parent.mkdir()
            command(["git", "worktree", "add", "--detach", str(source), args.source_commit], ROOT)
            source_files = clean_source(source, args.source_commit)
            if report["builds"] and source_files != report["builds"][0]["source_files"]:
                raise ValueError("Clean source inventories differ")
            manifest = build_one(source, source.parent / "independent build", args,
                                 tools, source_files, dependencies, env)
            report["builds"].append(manifest)
        a, b = [Path(build["source"]).parent / "independent build/normal developer folder" for build in report["builds"]]
        report["comparison"] = compare_packages(a, b)
        report["normal_frontend_equal"] = report["builds"][0]["normal_frontend"] == report["builds"][1]["normal_frontend"]
        report["tools_after"] = tool_inventory(args, env)
        if report["tools_after"] != tools or dependency_inventory(args.dependencies, lock) != dependencies:
            raise ValueError("Tool or supplied dependency drift")
        if ordinary(args.worker) != worker or clean_source(ROOT, checker_commit) != checker_files:
            raise ValueError("Worker or checker source drift")
        report["status"] = "passed_two_clean_paths" if report["comparison"]["equal"] and report["normal_frontend_equal"] else "failed_bytes_differ"
    except (ValueError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        report["status"] = "failed_build_or_precondition"
        report["failure"] = str(error)[:2048]
        raise
    finally:
        write_new(args.output / "comparison.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    for name in ("node", "npm-cli", "dependencies", "worker", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    report = run(parser.parse_args())
    print(json.dumps({"status": report["status"], "models_read_or_loaded": False,
                      "source_commit": report["source_commit"]}, indent=2))
    if report["status"] != "passed_two_clean_paths":
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        raise SystemExit(f"Reproducibility check failed: {error}")
