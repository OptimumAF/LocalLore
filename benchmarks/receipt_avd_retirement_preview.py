"""Read-only exact-image preview; only the explicit new report is written.

No import performs project IO, process, SDK, registry or guest operations.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).parents[1]))
from benchmarks import receipt_avd_storage as storage


def _output(path, root, registry, ledger=None):
    path = storage.safe_path(path)
    storage.safe_path(path.parent, exists=True, directory=True)
    storage.require(not os.path.lexists(path), "preview_output_exists")
    roots = [root, registry]
    if ledger is not None:
        roots.extend(storage.safe_path(entry["root"]) for entry in ledger["entries"])
    storage.require(not any(storage._contains(parent, path) for parent in roots),
                    "unsafe_preview_output")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--evidence-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        root = storage.safe_path(args.root, exists=True, directory=True)
        registry = storage.safe_path(storage.DEFAULT_REGISTRY, exists=True, directory=True)
        output = _output(args.output, root, registry)
        preview = storage.preview_retirement(root, args.evidence_manifest, registry=registry)
        storage.check_binding(preview["ledger_binding"])
        ledger = storage.read_json(preview["ledger_binding"]["path"])
        _output(output, root, registry, ledger)
        storage.check_binding(preview["ledger_binding"])
        with output.open("xb") as stream:
            stream.write(storage.encoded(preview))
        storage.check_binding(preview["ledger_binding"])
        storage.require(not os.path.lexists(registry / "admission.lock"), "registry_locked")
        print(json.dumps(storage.binding(output)))
        return 0
    except (storage.StorageRefused, OSError, ValueError, KeyError, TypeError):
        # A partial report remains evidence. Never repair or remove inputs/output.
        print("Retirement preview refused", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
