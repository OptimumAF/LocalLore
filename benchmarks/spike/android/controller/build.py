"""Explicit offline cross-build of the dependency-free Android process owner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
NDK = "29.0.14206865"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "target/android-runtime/controller")
    args = parser.parse_args()
    ndk = args.sdk.resolve() / "ndk" / NDK
    if f"Pkg.Revision = {NDK}" not in (ndk / "source.properties").read_text():
        parser.error("Unreviewed NDK")
    llvm = ndk / "toolchains/llvm/prebuilt" / ("windows-x86_64" if os.name == "nt" else "linux-x86_64")
    args.output.mkdir(parents=True, exist_ok=True)
    results = {}
    for abi, target in (("x86_64", "x86_64-linux-android"), ("arm64-v8a", "aarch64-linux-android")):
        output = args.output / ("remote-owner-" + abi)
        command = [str(llvm / "bin" / ("clang.exe" if os.name == "nt" else "clang")),
                   "--target=" + target + "28", "--sysroot=" + str(llvm / "sysroot"),
                   "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", "-fPIE", "-pie",
                   "-Wl,-z,max-page-size=16384", str(Path(__file__).with_name("remote_owner.c")), "-o", str(output)]
        subprocess.run(command, check=True)
        results[abi] = {"bytes": output.stat().st_size, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    (args.output / "build.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results))

if __name__ == "__main__":
    main()
