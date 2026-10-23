#!/usr/bin/env python3
"""Build/inspect an unsigned Windows developer folder. Never starts the app/worker.

Provision locked dependencies first. No model downloads, installer, updater,
signing, arbitrary worker hash override, or release publication is provided.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORKER_SHA = "add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87"
NODE_VERSION = "v24.22.1"
NPM_VERSION = "11.19.1"
RUNTIME_COMMIT = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
SOURCE_PATHS = ["apps/desktop", "crates", "native/llama-worker", "Cargo.toml",
                "Cargo.lock", "rust-toolchain.toml", "LICENSE"]
README = """LocalLore unsigned Windows x64 developer folder

This is a local test build, not a qualified installer or public release.
Run LocalLore Desktop.exe manually on Windows x64 with the Microsoft Edge
WebView2 Evergreen Runtime and Visual C++ x64 runtime already installed.
No prerequisite bootstrapper, model weights or model downloader is included.
Use the native model picker to explicitly provision the approved profile listed
in runtime/profile-v1.json. That file is metadata, not a model license grant.
The reviewed CPU worker must remain in runtime/ beside this executable folder.

Missing/corrupt worker/model errors are expected until explicitly provisioned.
The model is experimental; supported English single actions and literal dialogue
have bounded guards. Narrative quality and offline qualification remain pending.
Stories, submitted drafts and selected exports are plaintext private data. OS
backups/clipboard/synced folders and compromised devices are outside app privacy.
Replacing/removing this folder is not an app-data deletion or uninstall tool.
Clean-profile launch, update/uninstall retention, network-denied journeys and
installer/prerequisite behavior require separate qualification. No app or worker
was started by the packaging script. Review NOTICES and build-manifest.json.
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ordinary(path: Path, cap: int) -> bytes:
    # Refuse reparse points in every ancestor, including Windows junctions.
    for part in [path, *path.parents]:
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Reparse input: {part.name}")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > cap:
        raise ValueError(f"Invalid input size/type: {path.name}")
    return path.read_bytes()


def validate_worker(path: Path) -> bytes:
    data = ordinary(path, 16 * 1024 * 1024)
    if not data.startswith(b"MZ") or sha(data) != WORKER_SHA:
        raise ValueError("UnapprovedWorker")
    return data


def run(args: list[str], *, cwd: Path = ROOT, env: dict | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, env=env, check=False,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    print(result.stdout, end="", flush=True)
    result.check_returncode()
    return result.stdout.strip()


def encode(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def source_inventory() -> tuple[str, dict[str, str]]:
    dirty = run(["git", "status", "--porcelain", "--untracked-files=all", "--", *SOURCE_PATHS])
    if dirty:
        raise ValueError("Build inputs must be committed and clean")
    commit = run(["git", "rev-parse", "HEAD"])
    listed = subprocess.check_output(["git", "ls-files", "-z", "--", *SOURCE_PATHS],
                                     cwd=ROOT).decode("utf-8")
    files = {name: sha(ordinary(ROOT / name, 4 * 1024 * 1024))
             for name in listed.split("\0") if name}
    return commit, files


def rust_notices(env: dict) -> tuple[dict[str, bytes], list[dict]]:
    raw = subprocess.check_output([
        "cargo", "+1.93.1", "metadata", "--manifest-path", "apps/desktop/src-tauri/Cargo.toml",
        "--locked", "--offline", "--no-default-features", "--format-version", "1",
        "--filter-platform", "x86_64-pc-windows-msvc"], cwd=ROOT, env=env)
    meta = json.loads(raw)
    nodes = {node["id"]: node for node in meta["resolve"]["nodes"]}
    selected, pending = set(), [meta["resolve"]["root"]]
    while pending:
        current = pending.pop()
        if current in selected:
            continue
        selected.add(current)
        pending.extend(dep["pkg"] for dep in nodes[current]["deps"])
    files, inventory = {}, []
    for pkg in sorted(meta["packages"], key=lambda p: (p["name"], p["version"])):
        if pkg["id"] not in selected:
            continue
        directory = Path(pkg["manifest_path"]).parent
        prefix = f"NOTICES/rust/{pkg['name']}-{pkg['version']}"
        candidates = set()
        if pkg.get("license_file"):
            candidate = (directory / pkg["license_file"]).resolve()
            if candidate.is_relative_to(directory.resolve()):
                candidates.add(candidate)
        for candidate in directory.iterdir():
            if candidate.is_file() and re.match(r"^(licen[sc]e|copying|notice)([._-]|$)", candidate.name, re.I):
                candidates.add(candidate)
            elif candidate.is_dir() and candidate.name.lower() in {"licenses", "licences"}:
                candidates.update(p for p in candidate.rglob("*") if p.is_file())
        texts = []
        for candidate in sorted(candidates):
            relative = candidate.relative_to(directory).as_posix()
            files[f"{prefix}/{relative}"] = ordinary(candidate, 1024 * 1024)
            texts.append(relative)
        inventory.append({"name": pkg["name"], "version": pkg["version"],
                          "license": pkg.get("license"), "notice_files": texts,
                          "local_source": pkg["source"] is None})
    return files, inventory


def validate_files(files: dict[str, bytes]) -> None:
    fixed = {"LocalLore Desktop.exe", "runtime/locallore-llama-worker.exe",
             "runtime/profile-v1.json", "LICENSE", "README.txt", "build-manifest.json"}
    if not fixed.issubset(files):
        raise ValueError("Missing package member")
    if len(files) > 2048 or sum(map(len, files.values())) > 256 * 1024 * 1024:
        raise ValueError("Package budget")
    for name, data in files.items():
        parts = name.split("/")
        if (name not in fixed and not name.startswith("NOTICES/")) or any(
            p in {"", ".", ".."} or not re.fullmatch(r"[A-Za-z0-9_. +()-]+", p)
            for p in parts
        ):
            raise ValueError("Unexpected package member")
        if name.startswith("NOTICES/") and (len(data) > 1024 * 1024 or b"\0" in data):
            raise ValueError("Invalid notice")
    for name, cap in {"build-manifest.json": 2 * 1024 * 1024,
                      "runtime/profile-v1.json": 32768, "README.txt": 65536, "LICENSE": 65536}.items():
        if len(files[name]) > cap:
            raise ValueError("Metadata budget")
    if sha(files["runtime/locallore-llama-worker.exe"]) != WORKER_SHA:
        raise ValueError("UnapprovedWorker")
    if not files["LocalLore Desktop.exe"].startswith(b"MZ"):
        raise ValueError("Invalid native executable")
    profile = json.loads(files["runtime/profile-v1.json"])
    if profile.get("runtime_commit") != RUNTIME_COMMIT or profile.get("downloads") is not False:
        raise ValueError("Unexpected runtime profile")
    manifest = json.loads(files["build-manifest.json"])
    if manifest.get("kind") != "unsigned-windows-x64-developer-folder-v1":
        raise ValueError("Unexpected package kind")
    if manifest.get("model_weights_included") is not False or manifest.get("dev_harness") is not False:
        raise ValueError("Unexpected package policy")
    actual = {name: {"sha256": sha(data), "bytes": len(data)}
              for name, data in files.items() if name != "build-manifest.json"}
    if manifest.get("files") != actual:
        raise ValueError("Package inventory mismatch")


def inspect_archive(path: Path) -> dict:
    if path.stat().st_size > 260 * 1024 * 1024:
        raise ValueError("Archive byte budget")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 2048 or sum(e.file_size for e in entries) > 256 * 1024 * 1024:
            raise ValueError("Archive budget")
        if len({e.filename for e in entries}) != len(entries):
            raise ValueError("Duplicate package member")
        if any(stat.S_ISLNK(e.external_attr >> 16) or e.flag_bits & 1 or
               e.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED} for e in entries):
            raise ValueError("Invalid archive member type")
        files = {e.filename: archive.read(e) for e in entries}
    validate_files(files)
    return {"sha256": sha(path.read_bytes()), "bytes": path.stat().st_size,
            "members": len(files), "worker_sha256": WORKER_SHA,
            "source_commit": json.loads(files["build-manifest.json"])["source_commit"]}


def build(args: argparse.Namespace) -> None:
    if sys.platform != "win32":
        raise ValueError("Only Windows x64 developer builds are supported")
    target, output = args.target_dir.absolute(), args.output.absolute()
    if target.resolve().is_relative_to(ROOT) or output.resolve().is_relative_to(ROOT):
        raise ValueError("Target and output must be outside the source checkout")
    archive = output.with_suffix(".zip")
    if output.exists() or archive.exists():
        raise ValueError("Output already exists; choose a new destination")
    for key in ["TAURI_CONFIG", "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC_WRAPPER",
                "RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_RUSTFLAGS", "CARGO_BUILD_TARGET"]:
        if os.environ.get(key):
            raise ValueError(f"Remove build override: {key}")
    worker = validate_worker(args.worker.absolute())  # Before build or output creation.
    commit, inputs = source_inventory()
    env = os.environ.copy()
    env.update({"PATH": str(args.node.absolute().parent) + os.pathsep + env["PATH"],
                "CARGO_PROFILE_DEV_DEBUG": "0", "CARGO_PROFILE_TEST_DEBUG": "0",
                "CARGO_INCREMENTAL": "0", "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD": "1",
                "CARGO_TARGET_DIR": str(target)})
    # This script is not a dependency provisioner: npm dependencies and Cargo cache
    # must already be available. All subprocesses have argv vectors, never a shell.
    node = run([str(args.node), "--version"], env=env)
    npm = run([str(args.node), str(args.npm_cli), "--version"], env=env)
    if (node, npm) != (NODE_VERSION, NPM_VERSION):
        raise ValueError("Use pinned Node 24.22.1 / npm 11.19.1")
    rust = run(["rustc", "+1.93.1", "-vV"], env=env)
    if "host: x86_64-pc-windows-msvc" not in rust:
        raise ValueError("Use the Windows x64 MSVC Rust host toolchain")
    run([str(args.node), str(args.npm_cli), "--prefix", "apps/desktop", "run", "check"], env=env)
    run(["git", "diff", "--exit-code", "--", "apps/desktop/ui/host.generated.ts"], env=env)
    run(["cargo", "+1.93.1", "rustc", "--manifest-path", "apps/desktop/src-tauri/Cargo.toml",
         "--bin", "locallore-desktop-spike", "--locked", "--offline", "--no-default-features",
         "--target-dir", str(target), "--", "-C", "link-arg=/Brepro"], env=env)
    # Detect source changes during the build; this is source provenance, not publisher authentication.
    after_commit, after_inputs = source_inventory()
    if (commit, inputs) != (after_commit, after_inputs):
        raise ValueError("Build inputs changed during build")
    files = {"LocalLore Desktop.exe": ordinary(target / "debug/locallore-desktop-spike.exe", 128 * 1024 * 1024),
             "runtime/locallore-llama-worker.exe": worker,
             "runtime/profile-v1.json": ordinary(ROOT / "native/llama-worker/profile-v1.json", 32768),
             "LICENSE": ordinary(ROOT / "LICENSE", 32768), "README.txt": README.encode(),
             "NOTICES/llama-worker.txt": ordinary(ROOT / "native/llama-worker/NOTICE", 32768),
             "NOTICES/frontend-bundle.txt": ordinary(ROOT / "apps/desktop/dist/app.js.LEGAL.txt", 65536)}
    for package in ["react", "react-dom", "scheduler"]:
        # npm dependencies may be in an explicitly provisioned node_modules junction.
        directory = (ROOT / "apps/desktop/node_modules" / package).resolve()
        files[f"NOTICES/frontend/{package}-LICENSE.txt"] = ordinary(directory / "LICENSE", 65536)
    notices, rust_inventory = rust_notices(env)
    files.update(notices)
    files["NOTICES/rust-inventory.json"] = encode(rust_inventory)
    manifest = {"kind": "unsigned-windows-x64-developer-folder-v1", "source_commit": commit,
                "packager_sha256": sha(ordinary(Path(__file__).resolve(), 1024 * 1024)),
                "source_inputs_sha256": inputs, "node": node, "npm": npm,
                "node_options": env.get("NODE_OPTIONS", ""),
                "rust": rust,
                "cargo_profile": "dev; debug=0; incremental=0; no-default-features; final-link=/Brepro",
                "target": "x86_64-pc-windows-msvc", "dev_harness": False,
                "model_weights_included": False, "worker_sha256": WORKER_SHA,
                "runtime_commit": RUNTIME_COMMIT, "installer_qualified": False,
                "license_audit_complete": False,
                "license_limit": "Collected available selected-target Rust license texts, frontend and worker notices. Transitive native/embedded license audit remains a distribution gate.",
                "files": {name: {"sha256": sha(data), "bytes": len(data)}
                          for name, data in files.items()}}
    files["build-manifest.json"] = encode(manifest)
    validate_files(files)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4()}"
    staging.mkdir()
    for name, data in files.items():
        destination = staging / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(data)
    os.rename(staging, output)  # Windows nonoverwrite; no recursive cleanup or deletion.
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as package:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            package.writestr(info, data)
    print(json.dumps(inspect_archive(archive), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("build")
    for field in ["node", "npm-cli", "target-dir", "worker", "output"]:
        create.add_argument("--" + field, type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        build(args)
    else:
        print(json.dumps(inspect_archive(args.archive), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        sys.exit(f"Package failed: {error}")
