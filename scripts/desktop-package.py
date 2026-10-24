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
WORKER_SHA = "b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434"
NODE_VERSION = "v24.22.1"
NPM_VERSION = "11.19.1"
RUNTIME_COMMIT = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
SOURCE_PATHS = ["apps/desktop", "crates", "native/llama-worker", "Cargo.toml",
                "Cargo.lock", "rust-toolchain.toml", "LICENSE", "licenses/desktop", ".gitattributes"]
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
The MPL-selected upstream source archives are included in SOURCES/MPL/*.crate
(standard gzip-compressed tar archives). NOTICES/MPL-sources.json identifies
their exact versions/checksums and MPL-2.0 terms. They are public source code,
not models or saves; the app does not extract or execute them. The scoped
material inventory remains pending independent review and distribution approval.
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


LICENSE_SCOPE = "windows-x64-normal-developer-folder-component-notices-v1"
CATALOG_PATH = "licenses/desktop/catalog-v1.json"


def relative_name(value: str) -> str:
    if not isinstance(value, str) or any(
        part in {"", ".", ".."} or not re.fullmatch(r"[A-Za-z0-9_. +()-]+", part)
        for part in value.split("/")
    ):
        raise ValueError("Invalid license material path")
    return value


def license_catalog() -> tuple[dict, str]:
    raw = ordinary(ROOT / CATALOG_PATH, 2 * 1024 * 1024)
    catalog = json.loads(raw)
    if (not isinstance(catalog, dict) or
            catalog.get("schema") != "locallore-desktop-license-catalog-v1" or
            catalog.get("scope") != LICENSE_SCOPE or
            catalog.get("target") != "x86_64-pc-windows-msvc" or
            catalog.get("worker_sha256") != WORKER_SHA or
            catalog.get("runtime_commit") != RUNTIME_COMMIT or
            catalog.get("review_complete") is not False or
            catalog.get("distribution_approved") is not False):
        raise ValueError("Unsupported license catalog")
    if not 1 <= len(catalog.get("packages", [])) <= 512:
        raise ValueError("License catalog package budget")
    if not 0 <= len(catalog.get("mpl_sources", [])) <= 5:
        raise ValueError("License source archive count")
    if not 0 < catalog.get("source_archives_byte_cap", 0) <= 262144:
        raise ValueError("License source archive budget")
    if not 0 < catalog.get("source_archives_each_byte_cap", 0) <= 131072:
        raise ValueError("License source archive budget")
    if (len(catalog.get("frontend", [])) > 16 or len(catalog.get("additional_notices", [])) > 64 or
            len(catalog.get("verified_cached_inputs", [])) > 16 or
            not isinstance(catalog.get("remaining_gaps"), list) or
            len(catalog["remaining_gaps"]) > 16 or
            any(not isinstance(s, str) or len(s) > 512 for s in catalog["remaining_gaps"])):
        raise ValueError("License catalog component budget")
    try:
        expected_license_materials(catalog)  # Validate identities/paths before reading sources.
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed license catalog") from error
    return catalog, sha(raw)


def package_identity(package: dict, checksum: str | None) -> dict:
    return {"name": package["name"], "version": package["version"],
            "source": package["source"], "checksum": checksum,
            "license": package["license"]}


def notice_inventory(catalog: dict) -> list[dict]:
    return [{"name": p["name"], "version": p["version"], "license": p["license"],
             "checksum": p["checksum"], "local_source": p["source"] is None,
             "notice_files": [notice["output"] for notice in p["notices"]]}
            for p in catalog["packages"]]


def mpl_source_index(catalog: dict) -> bytes:
    return encode({"schema": "locallore-desktop-mpl-source-index-v1", "license": "MPL-2.0",
                   "license_member": "NOTICES/MPL-2.0.txt",
                   "format": "Original upstream .crate gzip-compressed tar source archives; no extraction by this app.",
                   "sources": catalog["mpl_sources"]})


def expected_license_materials(catalog: dict) -> dict[str, dict]:
    result = {}

    def add(record):
        name = relative_name(record["output"])
        if name in {"NOTICES/rust-inventory.json", "NOTICES/MPL-sources.json", "NOTICES/license-audit.json"}:
            raise ValueError("Reserved generated license material")
        digest, size = record["sha256"], record["bytes"]
        if not re.fullmatch(r"[0-9a-f]{64}", digest) or not 0 < size <= 1024 * 1024:
            raise ValueError("Invalid license material identity")
        if name != "LICENSE" and not name.startswith(("NOTICES/", "SOURCES/MPL/")):
            raise ValueError("Invalid license output namespace")
        value = {"sha256": digest, "bytes": size}
        if name in result and result[name] != value:
            raise ValueError("Conflicting license material identity")
        result[name] = value

    identities, sources = set(), set()
    combined_obligations = {
        "BSD-3-Clause AND MIT": ({"BSD-3-Clause"}, {"MIT"}),
        "Apache-2.0 AND MIT": ({"Apache-2.0"}, {"MIT"}),
        "(MIT OR Apache-2.0) AND Unicode-3.0": ({"MIT", "Apache-2.0"}, {"Unicode-3.0"}),
    }
    for package in catalog["packages"]:
        identity = (package["name"], package["version"], package["source"])
        if identity in identities or not package.get("notices") or len(package["notices"]) > 32:
            raise ValueError("Duplicate or uncovered license package")
        identities.add(identity)
        if package["source"] is not None and not re.fullmatch(r"[0-9a-f]{64}", package["checksum"] or ""):
            raise ValueError("Invalid license crate checksum")
        if " AND " in package["license"]:
            terms = {term for notice in package["notices"] for term in notice.get("license_terms", [])}
            groups = combined_obligations.get(package["license"])
            if groups is None or any(not terms.intersection(group) for group in groups):
                raise ValueError("Incomplete or unreviewed AND license coverage")
        # The catalog preserves every reviewed license text, including all AND
        # operands; no heuristic chooses one side of a combined expression.
        for notice in package["notices"]:
            if notice["output"].startswith("SOURCES/"):
                raise ValueError("Invalid license notice namespace")
            add(notice)
    for notice in catalog["additional_notices"] + catalog["frontend"]:
        if not notice["output"].startswith("NOTICES/"):
            raise ValueError("Invalid component notice namespace")
        add(notice)
    archive_bytes = 0
    for archive in catalog["mpl_sources"]:
        package = next((p for p in catalog["packages"] if
                        (p["name"], p["version"]) == (archive["name"], archive["version"])), None)
        output = f"SOURCES/MPL/{archive['name']}-{archive['version']}.crate"
        if (package is None or package["license"] != "MPL-2.0" or
                archive["sha256"] != package["checksum"] or archive["output"] != output or
                output in sources or archive["bytes"] > catalog["source_archives_each_byte_cap"]):
            raise ValueError("Invalid MPL source archive identity")
        sources.add(output)
        archive_bytes += archive["bytes"]
        add(archive)
    mpl = {(p["name"], p["version"]) for p in catalog["packages"] if p["license"] == "MPL-2.0"}
    if mpl != {(p["name"], p["version"]) for p in catalog["mpl_sources"]} or archive_bytes > catalog["source_archives_byte_cap"]:
        raise ValueError("Incomplete or oversized MPL source coverage")
    if mpl and "NOTICES/MPL-2.0.txt" not in result:
        raise ValueError("Missing MPL source license text")
    inventory = encode(notice_inventory(catalog))
    result["NOTICES/rust-inventory.json"] = {"sha256": sha(inventory), "bytes": len(inventory)}
    index = mpl_source_index(catalog)
    result["NOTICES/MPL-sources.json"] = {"sha256": sha(index), "bytes": len(index)}
    if len(result) > 1024 or sum(item["bytes"] for item in result.values()) > 16 * 1024 * 1024:
        raise ValueError("License material aggregate budget")
    return result


def scope_audit(catalog: dict, catalog_sha256: str) -> dict:
    materials = expected_license_materials(catalog)
    return {"schema": "locallore-desktop-license-scope-audit-v1", "scope": LICENSE_SCOPE,
            "catalog_sha256": catalog_sha256, "target": catalog["target"],
            "worker_sha256": catalog["worker_sha256"], "runtime_commit": catalog["runtime_commit"],
            "runtime_profile_sha256": catalog["runtime_profile_sha256"],
            "selected_graph_sha256": catalog["selected_graph_sha256"],
            "registry_packages": catalog["registry_count"], "local_packages": catalog["local_count"],
            "frontend_packages": len(catalog["frontend"]),
            "required_material_members": len(materials),
            "required_materials_sha256": sha(encode(materials)),
            "source_archives": len(catalog["mpl_sources"]),
            "source_archive_bytes": sum(p["bytes"] for p in catalog["mpl_sources"]),
            "coverage_complete": True, "review_complete": False,
            "distribution_approved": False, "remaining_gaps": catalog["remaining_gaps"],
            "coverage_meaning": "All exact catalog material bytes included; not legal or release approval.",
            "rust_inventory_format": 2}


def collect_license_materials(meta: dict) -> tuple[dict[str, bytes], list[dict], dict]:
    """Collect only the exact reviewed normal Windows graph; no fetching/extraction."""
    try:
        import tomllib
    except ModuleNotFoundError as error:
        raise ValueError("Use the pinned Python 3.14.9 package tool") from error
    catalog, catalog_digest = license_catalog()
    workspace = Path(meta["workspace_root"]).resolve()
    if workspace not in {ROOT.resolve(), (ROOT / "apps/desktop/src-tauri").resolve()}:
        raise ValueError("Unexpected license lock owner")
    lock = tomllib.loads(ordinary(workspace / "Cargo.lock", 2 * 1024 * 1024).decode())
    checksums = {(p["name"], p["version"], p.get("source")): p.get("checksum") for p in lock["package"]}
    nodes = {node["id"]: node for node in meta["resolve"]["nodes"]}
    selected, pending = set(), [meta["resolve"]["root"]]
    while pending:
        current = pending.pop()
        if current in selected:
            continue
        if current not in nodes or len(selected) >= 512:
            raise ValueError("Invalid or oversized license graph")
        selected.add(current)
        pending.extend(dep["pkg"] for dep in nodes[current]["deps"])
    try:
        packages = sorted((p for p in meta["packages"] if p["id"] in selected),
                          key=lambda p: (p["name"], p["version"]))
        actual = [package_identity(p, checksums.get((p["name"], p["version"], p["source"]))) for p in packages]
    except (KeyError, TypeError) as error:
        raise ValueError("Malformed license dependency graph") from error
    expected = [package_identity(p, p["checksum"]) for p in catalog["packages"]]
    if (actual != expected or sha(encode(actual)) != catalog["selected_graph_sha256"] or
            sum(p["source"] is not None for p in actual) != catalog["registry_count"] or
            sum(p["source"] is None for p in actual) != catalog["local_count"]):
        raise ValueError("Unreviewed license dependency graph/version/checksum/expression")
    directories = {(p["name"], p["version"]): Path(p["manifest_path"]).parent for p in packages}
    if sha(ordinary(ROOT / "apps/desktop/package-lock.json", 2 * 1024 * 1024)) != catalog["frontend_lock_sha256"]:
        raise ValueError("Unreviewed frontend dependency lock")
    files = {}

    def put(record, data):
        if sha(data) != record["sha256"] or len(data) != record["bytes"]:
            raise ValueError("Changed or missing required license material")
        if record["output"] in files and files[record["output"]] != data:
            raise ValueError("Conflicting collected license material")
        files[record["output"]] = data

    def notice(record, directory=None):
        relative = relative_name(record["path"])
        if record["origin"] == "crate" and directory is not None:
            source = directory / relative
        elif record["origin"] == "resource" and relative.startswith("texts/"):
            source = ROOT / "licenses/desktop" / relative
        elif record["origin"] == "project" and relative in {"LICENSE", "native/llama-worker/NOTICE"}:
            source = ROOT / relative
        else:
            raise ValueError("Unreviewed license material origin")
        put(record, ordinary(source, 1024 * 1024))

    for package in catalog["packages"]:
        for record in package["notices"]:
            notice(record, directories[(package["name"], package["version"])])
    for record in catalog["additional_notices"]:
        notice(record)
    for record in catalog["frontend"]:
        # This explicit provisioned dependency junction is resolved, as in the
        # original packager. No other reparse input is accepted by ordinary().
        directory = (ROOT / "apps/desktop/node_modules" / record["name"]).resolve()
        package = json.loads(ordinary(directory / "package.json", 65536))
        if (package.get("name"), package.get("version"), package.get("license")) != (
                record["name"], record["version"], record["license"]):
            raise ValueError("Unreviewed frontend license identity")
        put(record, ordinary(directory / "LICENSE", 65536))
    for record in catalog["verified_cached_inputs"]:
        source = directories[(record["name"], record["version"])] / relative_name(record["path"])
        data = ordinary(source, 16 * 1024 * 1024)
        if len(data) != record["bytes"] or sha(data) != record["sha256"]:
            raise ValueError("Changed embedded native input")
    for record in catalog["mpl_sources"]:
        directory = directories[(record["name"], record["version"])]
        archive = directory.parents[2] / "cache" / directory.parent.name / f"{record['name']}-{record['version']}.crate"
        put(record, ordinary(archive, catalog["source_archives_each_byte_cap"]))
    inventory = notice_inventory(catalog)
    files["NOTICES/rust-inventory.json"] = encode(inventory)
    files["NOTICES/MPL-sources.json"] = mpl_source_index(catalog)
    report = scope_audit(catalog, catalog_digest)
    files["NOTICES/license-audit.json"] = encode(report)
    return files, inventory, report


def rust_notices(env: dict) -> tuple[dict[str, bytes], list[dict], dict]:
    raw = subprocess.check_output([
        "cargo", "+1.93.1", "metadata", "--manifest-path", "apps/desktop/src-tauri/Cargo.toml",
        "--locked", "--offline", "--no-default-features", "--format-version", "1",
        "--filter-platform", "x86_64-pc-windows-msvc"], cwd=ROOT, env=env)
    return collect_license_materials(json.loads(raw))


def validate_scope_audit(files: dict[str, bytes], manifest: dict, *, required: bool = False) -> str:
    report = manifest.get("license_scope_audit")
    if manifest.get("license_audit_complete", False) is not False:
        raise ValueError("License review/approval remains pending")
    if report is None:
        if required or "NOTICES/license-audit.json" in files or any(p.startswith("SOURCES/") for p in files):
            raise ValueError("Missing scoped license audit")
        return "legacy_unreviewed"
    catalog, digest = license_catalog()
    if report != scope_audit(catalog, digest) or files.get("NOTICES/license-audit.json") != encode(report):
        raise ValueError("Untrusted scoped license audit")
    if sha(files["runtime/profile-v1.json"]) != catalog["runtime_profile_sha256"]:
        raise ValueError("Unreviewed scoped runtime profile")
    materials = expected_license_materials(catalog)
    permitted = set(materials) | {"NOTICES/license-audit.json"}
    if any(name.startswith(("NOTICES/", "SOURCES/")) and name not in permitted for name in files):
        raise ValueError("Unreviewed audited package material")
    for name, expected in materials.items():
        if name not in files or {"sha256": sha(files[name]), "bytes": len(files[name])} != expected:
            raise ValueError("Missing or changed audited license material")
    return "catalog_materials_verified_review_pending"


def validate_files(files: dict[str, bytes], *, require_license_audit: bool = False) -> None:
    fixed = {"LocalLore Desktop.exe", "runtime/locallore-llama-worker.exe",
             "runtime/profile-v1.json", "LICENSE", "README.txt", "build-manifest.json"}
    if not fixed.issubset(files):
        raise ValueError("Missing package member")
    if len(files) > 2048 or sum(map(len, files.values())) > 256 * 1024 * 1024:
        raise ValueError("Package budget")
    source_catalog = license_catalog()[0] if any(p.startswith("SOURCES/") for p in files) else None
    source_names = {p["output"] for p in source_catalog["mpl_sources"]} if source_catalog else set()
    source_total = 0
    for name, data in files.items():
        parts = name.split("/")
        if (name not in fixed and not name.startswith("NOTICES/") and name not in source_names) or any(
            p in {"", ".", ".."} or not re.fullmatch(r"[A-Za-z0-9_. +()-]+", p)
            for p in parts
        ):
            raise ValueError("Unexpected package member")
        if name.startswith("NOTICES/") and (len(data) > 1024 * 1024 or b"\0" in data):
            raise ValueError("Invalid notice")
        if name in source_names:
            source_total += len(data)
            if len(data) > source_catalog["source_archives_each_byte_cap"] or source_total > source_catalog["source_archives_byte_cap"]:
                raise ValueError("MPL source archive budget")
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
    validate_scope_audit(files, manifest, required=require_license_audit)


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
            "source_commit": json.loads(files["build-manifest.json"])["source_commit"],
            "license_scope_status": validate_scope_audit(files, json.loads(files["build-manifest.json"]))}


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
                "CARGO_ENCODED_RUSTFLAGS": f"--remap-path-prefix={ROOT}=/locallore-source",
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
    notices, _rust_inventory, license_report = rust_notices(env)
    for name, data in notices.items():
        if name in files and files[name] != data:
            raise ValueError("Generated notice differs from reviewed catalog")
        files[name] = data
    manifest = {"kind": "unsigned-windows-x64-developer-folder-v1", "source_commit": commit,
                "packager_sha256": sha(ordinary(Path(__file__).resolve(), 1024 * 1024)),
                "source_inputs_sha256": inputs, "node": node, "npm": npm,
                "node_options": env.get("NODE_OPTIONS", ""),
                "rust": rust,
                "cargo_profile": "dev; debug=0; incremental=0; no-default-features; final-link=/Brepro",
                "source_path_mapping": "all-rustc; source-root=/locallore-source",
                "target": "x86_64-pc-windows-msvc", "dev_harness": False,
                "model_weights_included": False, "worker_sha256": WORKER_SHA,
                "runtime_commit": RUNTIME_COMMIT, "installer_qualified": False,
                "license_audit_complete": False,
                "license_scope_audit": license_report,
                "license_limit": "Exact scoped catalog materials and five MPL source archives included; independent review and distribution approval remain pending.",
                "files": {name: {"sha256": sha(data), "bytes": len(data)}
                          for name, data in files.items()}}
    files["build-manifest.json"] = encode(manifest)
    validate_files(files, require_license_audit=True)
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
