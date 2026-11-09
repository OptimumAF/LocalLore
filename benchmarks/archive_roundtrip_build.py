"""Read-only admission inputs for the fixed Windows/Android archive cohort.

No device, socket, subprocess, or output file is opened by this module.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from benchmarks import receipt_avd_environment as environment

BUILD_SOURCE = "702239815c711993535a26d134053ae9a3c906bd"
SCOPE = "archive-roundtrip-inputs-v1"

# Verified APK custody and Windows fixture evidence on #30. Paths are relative
# to the two local evidence roots. No historical SQLite files are admitted.
_APK_ARTIFACTS = {
    "build": ("apk-custody.json", 1532,
              "5931d0251deb651504919dd99a08c2880ea9e30ade354f0dd0740bfd72cfe47e"),
    "product_apk": ("locallore-archiveverify-debug.apk", 28_162_648,
                    "cb889427eef0fd567586f41ddb01bf38cf2b36ef35b6a86335448269dc56235c"),
    "test_apk": ("locallore-archiveverify-debug-androidTest.apk", 2_550_602,
                 "e4f47c7596589b69b4b5c9b9ea8fc0936e239aeb8219efe12ad0c53a130d93cb"),
}
_WINDOWS_ARTIFACTS = {
    "fixture_executable": ("target/debug/examples/platform_roundtrip.exe", 13_088_256,
                           "d7525dc36c9f5e35e0222f1b0c5f2c87001b21c93680419724bd878e0565276e"),
    "fixture_preflight": ("fixture-check/result.json", 99,
                          "7184becb1d7c9ca19052abc1262aab5441fadbab2b33e31566d8a4dfb6f1bda8"),
    "expectations": ("current-fixtures/expectations.json", 18_291,
                     "537f7555bd564ebe106e6aac65e8c00520130aedb8d5ee2b60605e9c216c88b5"),
    "windows_origin": ("current-fixtures/windows-origin.json", 7_064,
                       "f5fa9bb00881bb759383e86639cc9254fe1fb00a6ee28ec802ec4ae9924111a0"),
    "windows_continued": ("current-fixtures/windows-continued.json", 7_890,
                          "70d23694bc66d136522e62efb459044e2cf6e545e2e0e44d0c290b2871838c6f"),
}
ARTIFACT_KEYS = frozenset(_APK_ARTIFACTS | _WINDOWS_ARTIFACTS)


class BuildRefused(ValueError):
    """A fixed category suitable for a bounded verification record."""


def _need(condition, category):
    if not condition:
        raise BuildRefused(category)


def _safe_path(value, *, directory=False):
    try:
        return environment.safe_path(value, directory=directory)
    except environment.EnvironmentRefused:
        raise BuildRefused("path") from None


def _root(value):
    path = Path(value)
    _need(path.is_absolute() and path.drive.upper() == "D:" and
          ".android" not in {part.casefold() for part in path.parts}, "root")
    # Normalize NTFS short names only after refusing reparse ancestors.
    canonical = _safe_path(path, directory=True).resolve(strict=True)
    _need(canonical.drive.upper() == "D:" and
          ".android" not in {part.casefold() for part in canonical.parts}, "root")
    return _safe_path(canonical, directory=True)


def _identity(info):
    # Windows pathname and handle views can disagree on permissions and ctime.
    return (info.st_dev, info.st_ino, info.st_size, stat.S_IFMT(info.st_mode), info.st_nlink,
            info.st_mtime_ns, getattr(info, "st_birthtime_ns", None))


def _stamp(info):
    return (*_identity(info), info.st_mode, info.st_ctime_ns, getattr(info, "st_file_attributes", 0))


def _verify_file(binding):
    path = _safe_path(binding["path"])
    before = path.lstat()
    expected_size = binding["bytes"]
    _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
          before.st_size == expected_size, "file")
    stamp = _stamp(before)
    digest = hashlib.sha256()
    with path.open("rb", buffering=0) as stream:
        opened = os.fstat(stream.fileno())
        _need(_identity(opened) == _identity(before), "identity")
        held_stamp = _stamp(opened)
        remaining = expected_size
        while remaining:
            block = stream.read(min(remaining, 1024 * 1024))
            _need(block, "size")
            digest.update(block)
            remaining -= len(block)
        _need(stream.read(1) == b"", "size")
        _need(_stamp(os.fstat(stream.fileno())) == held_stamp, "identity")
    _need(_stamp(_safe_path(path).lstat()) == stamp, "identity")
    _need(digest.hexdigest() == binding["sha256"], "digest")


def _expected(apk_root, windows_root):
    roots = (_root(apk_root), _root(windows_root))
    _need(not roots[0].is_relative_to(roots[1]) and
          not roots[1].is_relative_to(roots[0]), "root")
    return {
        role: dict(path=str(root / relative), bytes=size, sha256=digest)
        for root, roster in zip(roots, (_APK_ARTIFACTS, _WINDOWS_ARTIFACTS), strict=True)
        for role, (relative, size, digest) in roster.items()
    }


def collect(apk_root, windows_root):
    """Check the two evidence roots and return only the fixed owner artifacts."""
    expected = _expected(apk_root, windows_root)
    for binding in expected.values():
        _verify_file(binding)
    return expected


def verify_current(admission):
    """Match the owner artifact roster and recheck live bytes before owner start."""
    _need(type(admission) is dict and type(admission.get("artifacts")) is dict, "binding")
    artifacts = admission["artifacts"]
    _need(set(artifacts) == ARTIFACT_KEYS and all(
        type(value) is dict and set(value) == {"path", "bytes", "sha256"} and
        type(value["path"]) is str and type(value["bytes"]) is int and
        type(value["sha256"]) is str for value in artifacts.values()), "binding")
    apk_root = Path(artifacts["build"]["path"]).parent
    windows_root = Path(artifacts["fixture_preflight"]["path"]).parent.parent
    expected = _expected(apk_root, windows_root)
    _need(artifacts == expected, "binding")
    for binding in expected.values():
        _verify_file(binding)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk-root", required=True, type=Path)
    parser.add_argument("--windows-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        artifacts = collect(args.apk_root, args.windows_root)
    except BuildRefused as failure:
        print("Archive input refusal: " + str(failure), file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print("Archive input refusal: path or file", file=sys.stderr)
        return 1
    print(json.dumps(dict(scope=SCOPE, source=BUILD_SOURCE, artifacts=artifacts), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
