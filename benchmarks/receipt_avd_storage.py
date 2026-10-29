"""Durable, fail-closed receipt AVD admission and evidence-aware retirement plans.

No import performs IO; no function deletes guest files or runs an SDK.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

GIB = 1024 ** 3
DEFAULT_REGISTRY = Path("D:/Dev/_Migration/LocalLore-AVD-Storage")
MAX_GUESTS = 2
BUDGET_BYTES = 64 * GIB
RESERVATION_BYTES = 40 * GIB
CONTENT = "content/locallore_receipt_api35_v1.avd/"
DISPOSABLE = frozenset(CONTENT + name for name in (
    "sdcard.img", "sdcard.img.qcow2", "userdata-qemu.img", "userdata-qemu.img.qcow2",
    "cache.img", "cache.img.qcow2", "encryptionkey.img", "encryptionkey.img.qcow2",
    "snapshots/default_boot/ram.img"))
STATES = frozenset(("preparing", "prepared", "retained", "closed", "retired"))
ADAPTER_PROOFS = ("admission", "owner_result", "worker_result", "after")


class StorageRefused(RuntimeError):
    """A stable local reason code, without private paths."""


def require(condition, reason):
    if not condition:
        raise StorageRefused(reason)


def safe_path(value, exists=False, directory=False):
    p = Path(value)
    require(p.is_absolute() and p.drive.upper() == "D:" and
            str(p) == os.path.abspath(str(p)) and
            all(":" not in part for part in p.parts[1:]), "unsafe_path")
    for item in [p] + list(p.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and
                not getattr(info, "st_file_attributes", 0) & 0x400, "linked_path")
        require(stat.S_ISDIR(info.st_mode) or
                (stat.S_ISREG(info.st_mode) and info.st_nlink == 1), "linked_or_special_file")
        require(item == p or stat.S_ISDIR(info.st_mode), "unsafe_path")
    if exists:
        require(p.is_dir() if directory else p.is_file(), "missing_path")
    return p


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def read_json(path):
    p = safe_path(path, exists=True)
    require(0 < p.stat().st_size <= 16 * 1024 * 1024, "invalid_json")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "invalid_json")
            result[key] = value
        return result
    try:
        return json.loads(p.read_bytes().decode("utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda _: require(False, "invalid_json"))
    except (ValueError, UnicodeError, TypeError):
        raise StorageRefused("invalid_json") from None


def binding(path):
    p = safe_path(path, exists=True)
    h = hashlib.sha256()
    with p.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": h.hexdigest()}


def check_binding(value):
    require(type(value) is dict and set(value) == {"path", "bytes", "sha256"} and
            type(value["path"]) is str and type(value["bytes"]) is int and
            value["bytes"] >= 0 and type(value["sha256"]) is str and
            re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is not None,
            "invalid_binding")
    require(binding(value["path"]) == value, "binding_changed")


def _contains(parent, child):
    return parent == child or parent in child.parents


def _atomic_write(path, value):
    safe_path(path)
    pending = path.parent / ("pending-" + uuid.uuid4().hex + ".json")
    try:
        with pending.open("xb") as stream:
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
        safe_path(path)
        os.replace(str(pending), str(path))
    finally:
        if pending.exists():
            safe_path(pending, exists=True).unlink()


def _validate(ledger, registry):
    require(type(ledger) is dict and set(ledger) == {"version", "max_guests", "budget_bytes", "reservation_bytes", "entries"}
            and type(ledger["version"]) is int and ledger["version"] == 1 and
            type(ledger["max_guests"]) is int and ledger["max_guests"] == MAX_GUESTS and
            ledger["budget_bytes"] == BUDGET_BYTES and ledger["reservation_bytes"] == RESERVATION_BYTES
            and type(ledger["entries"]) is list and len(ledger["entries"]) <= 10000, "invalid_ledger")
    roots = []
    for entry in ledger["entries"]:
        require(type(entry) is dict and set(entry) == {"root", "proposal_sha256", "state", "reserved_bytes", "closure", "retirement", "retirement_receipt"}
                and type(entry["root"]) is str and type(entry["state"]) is str and
                entry["state"] in STATES and type(entry["proposal_sha256"]) is str and
                re.fullmatch(r"[0-9a-f]{64}", entry["proposal_sha256"]) is not None and
                type(entry["reserved_bytes"]) is int and entry["reserved_bytes"] >= 0,
                "invalid_ledger")
        root = safe_path(entry["root"])
        require(not any(_contains(old, root) or _contains(root, old) for old in roots), "overlapping_roots")
        roots.append(root)
        require(entry["state"] == "preparing" or root.is_dir(), "tracked_root_missing")
        require(not root.exists() or root.is_dir(), "invalid_guest_root")
        if entry["state"] in ("closed", "retired"):
            require(type(entry["closure"]) is dict, "invalid_ledger")
            check_binding(entry["closure"])
            _closed(read_json(entry["closure"]["path"]), entry["proposal_sha256"])
        else:
            require(entry["reserved_bytes"] == RESERVATION_BYTES and entry["closure"] is None and
                    entry["retirement"] is None, "invalid_ledger")
        if entry["state"] == "retired":
            require(type(entry["retirement_receipt"]) is dict and
                    entry["retirement_receipt"].get("path") == str(_tombstone_path(registry, root)),
                    "invalid_retirement_tombstone")
            _verify_retired(entry)
        else:
            require(entry["retirement_receipt"] is None, "invalid_ledger")
    active = [entry for entry in ledger["entries"] if entry["state"] != "retired"]
    require(len(active) <= MAX_GUESTS, "storage_capacity_exceeded")


def _charge(entry):
    if entry["state"] == "retired":
        _verify_retired(entry)
        root = Path(entry["root"])
        paths = list(_files(root).values())
        manifest = entry["retirement"]["evidence_manifest"]
        paths.extend(Path(item["binding"]["path"]) for item in read_json(manifest["path"])["files"])
        paths.extend((Path(manifest["path"]), Path(entry["retirement_receipt"]["path"])))
        paths.extend(_closed(read_json(entry["closure"]["path"]), entry["proposal_sha256"]))
        paths.append(Path(entry["closure"]["path"]))
        return _logical_bytes(paths)
    if entry["state"] != "closed":
        return RESERVATION_BYTES
    check_binding(entry["closure"])
    proofs = _closed(read_json(entry["closure"]["path"]), entry["proposal_sha256"])
    # Re-observe closed roots: external additions cannot silently make admission cheaper.
    paths = list(_files(Path(entry["root"])).values()) + proofs + [Path(entry["closure"]["path"])]
    return max(entry["reserved_bytes"], _logical_bytes(paths))


def _logical_bytes(paths):
    # Identical declared paths count once, including proofs within a guest root.
    unique = {str(path).casefold(): path for path in paths}
    return sum(path.stat().st_size for path in unique.values())


def _initialize_registry(registry):
    if registry.exists():
        return
    safe_path(registry.parent, exists=True, directory=True)
    staging = registry.parent / ("." + registry.name + "-initialize-" + uuid.uuid4().hex)
    staging.mkdir()
    initial_ledger = staging / "ledger-v1.json"
    try:
        _atomic_write(initial_ledger, {"version": 1, "max_guests": MAX_GUESTS, "budget_bytes": BUDGET_BYTES,
                                      "reservation_bytes": RESERVATION_BYTES, "entries": []})
        try:
            # Windows rename is atomic and refuses any existing destination. Publish
            # only after the complete initial ledger is forced; never publish an
            # empty registry that another first admission could mistake for corruption.
            os.rename(str(staging), str(registry))
        except FileExistsError:
            pass  # Another initializer won; its ledger is checked under the lock.
    finally:
        if staging.exists():
            # Only this invocation's exact staging files, never a registry or tree.
            if initial_ledger.exists():
                safe_path(initial_ledger, exists=True).unlink()
            safe_path(staging, exists=True, directory=True).rmdir()


@contextmanager
def _locked(registry):
    registry = safe_path(registry)
    _initialize_registry(registry)
    safe_path(registry, exists=True, directory=True)
    lock = registry / "admission.lock"
    try:
        descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise StorageRefused("registry_locked") from None
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded({"pid": os.getpid(), "nonce": uuid.uuid4().hex}))
            stream.flush()
            os.fsync(stream.fileno())
        path = registry / "ledger-v1.json"
        require(path.exists(), "ledger_missing")
        ledger = read_json(path)
        _validate(ledger, registry)
        yield ledger
    finally:
        safe_path(lock, exists=True).unlink()


def _entry(ledger, root):
    root = safe_path(root)
    entries = [entry for entry in ledger["entries"] if Path(entry["root"]) == root]
    require(len(entries) == 1, "untracked_root")
    return entries[0]


def reserve_prepare(root, proposal_sha256, registry=DEFAULT_REGISTRY):
    """Durably reserve before root mkdir or SDK calls; failure never auto-releases."""
    root, registry = safe_path(root), safe_path(registry)
    require(not root.exists(), "target_exists")
    require(not _contains(root, registry) and not _contains(registry, root), "overlapping_roots")
    require(type(proposal_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", proposal_sha256), "invalid_proposal_digest")
    with _locked(registry) as ledger:
        require(not root.exists(), "target_exists")
        require(not any(_contains(Path(e["root"]), root) or _contains(root, Path(e["root"]))
                        for e in ledger["entries"]), "root_already_tracked")
        active = [e for e in ledger["entries"] if e["state"] != "retired"]
        require(len(active) < MAX_GUESTS and
                sum(_charge(e) for e in ledger["entries"]) + RESERVATION_BYTES <= BUDGET_BYTES,
                "storage_capacity_exceeded")
        entry = {"root": str(root), "proposal_sha256": proposal_sha256, "state": "preparing",
                 "reserved_bytes": RESERVATION_BYTES, "closure": None, "retirement": None,
                 "retirement_receipt": None}
        ledger["entries"].append(entry)
        _validate(ledger, registry)
        _atomic_write(registry / "ledger-v1.json", ledger)
        return dict(entry)


def record_state(root, state, registry=DEFAULT_REGISTRY, proposal_sha256=None):
    """Retain all reservations; call retained before dispatching any guest run."""
    require(state in ("prepared", "retained"), "invalid_transition")
    require(proposal_sha256 is None or (type(proposal_sha256) is str and
            re.fullmatch(r"[0-9a-f]{64}", proposal_sha256)), "invalid_proposal_digest")
    registry = safe_path(registry)
    with _locked(registry) as ledger:
        entry = _entry(ledger, root)
        require(entry["state"] != "retired", "invalid_transition")
        safe_path(root, exists=True, directory=True)
        require(sum(_charge(e) for e in ledger["entries"] if e is not entry) + RESERVATION_BYTES <= BUDGET_BYTES,
                "storage_capacity_exceeded")
        entry.update(state=state, reserved_bytes=RESERVATION_BYTES, closure=None, retirement=None)
        if proposal_sha256 is not None:
            entry["proposal_sha256"] = proposal_sha256
        _atomic_write(registry / "ledger-v1.json", ledger)


def _closed(closure, proposal_sha256):
    require(type(closure) is dict and closure.get("proposal_sha256") == proposal_sha256 and
            closure.get("closure_verified") is True and
            (closure.get("cleanup_complete") is True or
             ("cleanup_complete" not in closure and closure.get("child_cleanup_complete") is True)),
            "closure_unverified")
    if any(key in closure for key in ADAPTER_PROOFS):
        require(all(key in closure for key in ADAPTER_PROOFS), "closure_proofs_incomplete")
        for key in ADAPTER_PROOFS:
            check_binding(closure[key])
        return [Path(closure[key]["path"]) for key in ADAPTER_PROOFS]
    return []


def record_closed(root, closure_path, registry=DEFAULT_REGISTRY):
    registry = safe_path(registry)
    with _locked(registry) as ledger:
        entry = _entry(ledger, root)
        require(entry["state"] != "retired", "invalid_transition")
        safe_path(root, exists=True, directory=True)
        closure = binding(closure_path)
        proofs = _closed(read_json(closure_path), entry["proposal_sha256"])
        check_binding(closure)
        measured = _logical_bytes(list(_files(Path(root)).values()) + proofs + [Path(closure_path)])
        # Only the first verified closure releases the live reservation. Replaying
        # closure after external truncation is not evidence of retirement.
        if entry["state"] == "closed":
            measured = max(entry["reserved_bytes"], measured)
        entry.update(state="closed", reserved_bytes=measured, closure=closure, retirement=None)
        _atomic_write(registry / "ledger-v1.json", ledger)


def _files(root):
    root = safe_path(root, exists=True, directory=True)
    result = {}
    # os.walk without following links; validate every directory before descending.
    def unreadable(_error):
        raise StorageRefused("guest_tree_unreadable")
    for parent, folders, files in os.walk(str(root), followlinks=False, onerror=unreadable):
        safe_path(parent, exists=True, directory=True)
        for folder in folders:
            safe_path(Path(parent) / folder, exists=True, directory=True)
        for name in files:
            path = safe_path(Path(parent) / name, exists=True)
            relative = path.relative_to(root).as_posix()
            require(not (name.lower().endswith((".img", ".qcow2")) and relative not in DISPOSABLE),
                    "unknown_guest_image")
            result[relative] = path
            require(len(result) <= 20000, "guest_tree_unbounded")
    return result


def _evidence(root, manifest_path, preserved, closure):
    manifest_path = safe_path(manifest_path, exists=True)
    require(not _contains(root, manifest_path), "evidence_inside_guest")
    manifest = read_json(manifest_path)
    require(type(manifest) is dict and set(manifest) == {"version", "root", "complete", "files"} and
            manifest["version"] == 1 and manifest["root"] == str(root) and manifest["complete"] is True and
            type(manifest["files"]) is list and 0 < len(manifest["files"]) <= 20000, "invalid_manifest")
    copies = {}
    for item in manifest["files"]:
        require(type(item) is dict and set(item) == {"relative", "binding"} and
                type(item["relative"]) is str and item["relative"] not in copies and
                item["relative"] in preserved, "incomplete_evidence")
        check_binding(item["binding"])
        require(not _contains(root, Path(item["binding"]["path"])), "evidence_inside_guest")
        original = binding(preserved[item["relative"]])
        require(all(original[k] == item["binding"][k] for k in ("bytes", "sha256")), "evidence_changed")
        copies[item["relative"]] = item["binding"]
    require(set(copies) == set(preserved), "incomplete_evidence")
    check_binding(closure)
    require(any(str(path) == closure["path"] for path in preserved.values()), "closure_not_preserved")
    return binding(manifest_path)


def _plan(root, manifest_path, entry):
    require(entry["state"] == "closed", "guest_not_closed")
    check_binding(entry["closure"])
    _closed(read_json(entry["closure"]["path"]), entry["proposal_sha256"])
    files = _files(root)
    images = {key: path for key, path in files.items() if key in DISPOSABLE}
    preserved = {key: path for key, path in files.items() if key not in DISPOSABLE}
    require(images, "no_disposable_images")
    manifest = _evidence(root, manifest_path, preserved, entry["closure"])
    return {"version": 1, "action": "retire_disposable_images_only", "root": str(root),
            "proposal_sha256": entry["proposal_sha256"], "evidence_manifest": manifest,
            "closure": entry["closure"],
            "remove": [binding(images[key]) for key in sorted(images)],
            "preserve": [binding(preserved[key]) for key in sorted(preserved)]}


def plan_retirement(root, evidence_manifest_path, registry=DEFAULT_REGISTRY):
    """Dry-run only. Review and separately authorize an exact host file operation."""
    root = safe_path(root, exists=True, directory=True)
    registry = safe_path(registry)
    with _locked(registry) as ledger:
        entry = _entry(ledger, root)
        plan = _plan(root, evidence_manifest_path, entry)
        # Pin the exact dry-run roster so a fabricated finalization cannot free capacity.
        entry["retirement"] = plan
        _atomic_write(registry / "ledger-v1.json", ledger)
        return plan


def record_retired(root, reviewed_plan, registry=DEFAULT_REGISTRY):
    """Acknowledge an externally performed reviewed retirement; deletes no guests.

    Must receive the unchanged plan made before that explicit host operation.
    Partial deletion, added images, changed evidence or preserved files refuse.
    """
    root, registry = safe_path(root, exists=True, directory=True), safe_path(registry)
    with _locked(registry) as ledger:
        entry = _entry(ledger, root)
        require(entry["state"] == "closed", "guest_not_closed")
        require(reviewed_plan == entry["retirement"], "retirement_plan_changed")
        _verify_retirement_result(entry)
        tombstone = _tombstone_path(registry, root)
        receipt = {"version": 1, "root": str(root), "retirement": reviewed_plan}
        if tombstone.exists():
            # A crash after receipt publication may leave a closed ledger entry.
            require(read_json(tombstone) == receipt, "retirement_tombstone_changed")
        else:
            with tombstone.open("xb") as stream:
                stream.write(encoded(receipt))
                stream.flush()
                os.fsync(stream.fileno())
        entry.update(state="retired", retirement_receipt=binding(tombstone))
        _verify_retired(entry)
        _atomic_write(registry / "ledger-v1.json", ledger)


def _tombstone_path(registry, root):
    key = hashlib.sha256(str(root).casefold().encode("utf-8")).hexdigest()
    return Path(registry) / ("retired-" + key + ".json")


def _verify_retirement_result(entry):
    root = safe_path(entry["root"], exists=True, directory=True)
    plan = entry["retirement"]
    require(type(plan) is dict and set(plan) == {
        "version", "action", "root", "proposal_sha256", "evidence_manifest", "closure", "remove", "preserve"}
        and type(plan["version"]) is int and plan["version"] == 1
        and plan["action"] == "retire_disposable_images_only"
        and plan["root"] == str(root) and plan["proposal_sha256"] == entry["proposal_sha256"]
        and plan["closure"] == entry["closure"] and type(plan["remove"]) is list and plan["remove"]
        and type(plan["preserve"]) is list, "invalid_retirement_plan")
    check_binding(entry["closure"])
    _closed(read_json(entry["closure"]["path"]), entry["proposal_sha256"])
    check_binding(plan["evidence_manifest"])
    files = _files(root)
    require(not any(key in DISPOSABLE for key in files), "images_remain")
    removed_paths = set()
    for item in plan["remove"]:
        require(type(item) is dict and set(item) == {"path", "bytes", "sha256"} and
                type(item["path"]) is str and type(item["bytes"]) is int and item["bytes"] >= 0 and
                type(item["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]),
                "invalid_retirement_plan")
        path = safe_path(item["path"])
        require(_contains(root, path) and path.relative_to(root).as_posix() in DISPOSABLE and not path.exists(),
                "images_remain")
        require(str(path) not in removed_paths, "invalid_retirement_plan")
        removed_paths.add(str(path))
    preserved_paths = set()
    for item in plan["preserve"]:
        check_binding(item)
        require(item["path"] not in preserved_paths, "invalid_retirement_plan")
        preserved_paths.add(item["path"])
    require({str(path) for path in files.values()} == preserved_paths, "preserved_files_changed")
    _evidence(root, plan["evidence_manifest"]["path"], files, entry["closure"])


def _verify_retired(entry):
    _verify_retirement_result(entry)
    check_binding(entry["retirement_receipt"])
    require(read_json(entry["retirement_receipt"]["path"]) ==
            {"version": 1, "root": entry["root"], "retirement": entry["retirement"]},
            "retirement_tombstone_changed")
