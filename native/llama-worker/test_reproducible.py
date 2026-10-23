"""Local MSVC clean-path worker comparison; no models, downloads or staging.

Run in the already provisioned x64 MSVC development environment. Outputs must be
new task-owned directories. The upstream checkout is only read, locally cloned
twice, and never configured in place. All evidence remains local by default.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

UPSTREAM = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
FILES = (
    "CMakeLists.txt", "main.cpp", "generate.inc", "schema_order.h",
    "schema_order_test.cpp", "worker_launch.h", "worker_launch_test.cpp",
    "test_protocol.py", "test_reproducible.py",
)
VIRTUAL = "X:/locallore"
BAD_OPTION = ("D9002", "D9007", "LNK4044", "unknown option", "unrecognized option", "option ignored")
MAX_LOG = 16 * 1024 * 1024


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run(command, cwd, log, *, env=None, timeout=1200, expected=0):
    started = time.monotonic()
    with log.open("wb") as output:
        output.write((json.dumps([str(x) for x in command], ensure_ascii=True) + "\n").encode())
        output.flush()
        result = subprocess.run([str(x) for x in command], cwd=cwd, env=env,
                                stdout=output, stderr=subprocess.STDOUT,
                                timeout=timeout, check=False)
    if log.stat().st_size > MAX_LOG:
        raise RuntimeError("local log exceeds evidence budget: " + log.name)
    text = log.read_text(encoding="utf-8", errors="replace")
    if result.returncode != expected or any(x.lower() in text.lower() for x in BAD_OPTION):
        raise RuntimeError("command failed or ignored option: " + log.name)
    return {"command": [str(x) for x in command], "log": log.name,
            "return_code": result.returncode, "sha256": digest(log),
            "seconds": round(time.monotonic() - started, 3)}, text


def git_text(git, directory, *args):
    return subprocess.check_output([git, "-C", str(directory), *args],
                                   timeout=30).decode("utf-8").strip()


def inventory(git, directory):
    names = subprocess.check_output([git, "-C", str(directory), "ls-files", "-z"], timeout=30)
    rows = {}
    for raw in names.split(b"\0"):
        if not raw:
            continue
        name = raw.decode("utf-8")
        path = directory / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(directory):
            raise RuntimeError("nonordinary tracked source")
        rows[name] = {"bytes": path.stat().st_size, "sha256": digest(path)}
        if len(rows) > 20000:
            raise RuntimeError("source inventory too large")
    return rows


def probe(root, cl, lib, label):
    """Compile both languages and execute a tiny __FILE__ mapping oracle."""
    directories = {key: root / (key + " source") for key in ("worker", "llama", "build")}
    for directory in directories.values():
        directory.mkdir(parents=True)
    c = directories["llama"] / "probe.c"
    cpp = directories["worker"] / "probe.cpp"
    header = directories["build"] / "generated.h"
    c.write_text('const char *c_file(void) { return __FILE__; }\n', encoding="utf-8")
    header.write_text('const char *header_file(void) { return __FILE__; }\n', encoding="utf-8")
    cpp.write_text('#include <stdio.h>\nextern "C" const char *c_file(void);\n'
                   '#include "' + header.as_posix() + '"\n'
                   'int main() { puts(c_file()); puts(__FILE__); puts(header_file()); }\n', encoding="utf-8")
    mappings = ["/pathmap:" + prefix + "=" + VIRTUAL.replace("/", "\\") + "\\" + key
                for key, directory in directories.items() for prefix in (directory.as_posix(), str(directory))]
    # Upstream's unity sources already compile with /utf-8. It is also required
    # to read the UTF-8 absolute Unicode #include in this corresponding probe.
    common = ["/nologo", "/Bv", "/utf-8", "/Brepro", "/experimental:deterministic", *mappings,
              "/I" + str(directories["build"]), "/O2", "/DNDEBUG"]
    steps = []
    for filename, output in ((c, root / "c.obj"), (cpp, root / "cpp.obj")):
        step, _ = run([cl, *common, "/c", filename, "/Fo" + str(output)], root,
                      root / (filename.suffix[1:] + "-compile.log"))
        steps.append(step)
    step, _ = run([lib, "/nologo", "/Brepro", "/OUT:" + str(root / "probe.lib"), root / "c.obj"],
                  root, root / "archive.log")
    steps.append(step)
    step, _ = run([cl, "/nologo", root / "cpp.obj", root / "probe.lib",
                   "/Fe" + str(root / "probe.exe"), "/link", "/Brepro", "/INCREMENTAL:NO"],
                  root, root / "link.log")
    steps.append(step)
    step, text = run([root / "probe.exe"], root, root / "run.log", timeout=5)
    steps.append(step)
    actual = text.splitlines()[1:]
    expected = [VIRTUAL + "/llama/probe.c", VIRTUAL + "/worker/probe.cpp", VIRTUAL + "/build/generated.h"]
    if [x.replace("\\", "/") for x in actual] != expected:
        raise RuntimeError("__FILE__ mapping not applied: " + label)
    return {"label": label, "mapped_files": actual, "steps": steps}


def verify_launcher(cmake, tools, root, build, worker, steps):
    launcher = build / "worker-compiler-launcher.cmake"
    names = ("main.cpp", "schema_order_test.cpp", "worker_launch_test.cpp")
    directory = build / "worker-compiler-invocations"
    if {x.name for x in directory.iterdir()} != {name + ".json" for name in names}:
        raise RuntimeError("fixed compiler invocation inventory")
    invocations = {}
    for name in names:
        record = json.loads((directory / (name + ".json")).read_text(encoding="utf-8"))
        args = record["arguments"]
        if (Path(record["compiler"]) != Path(tools["cl"]) or Path(record["cwd"]) != worker
                or record["source"] != name or args.count(name) != 1 or record["exit_code"] != "0"
                or "/Brepro" not in args or "/experimental:deterministic" not in args
                or sum(x.startswith("/pathmap:") for x in args) != 6):
            raise RuntimeError("fixed compiler authority/source invocation")
        for prefix in ("/Fo", "/Fd"):
            outputs = [x[len(prefix):] for x in args if x.startswith(prefix)]
            if len(outputs) != 1 or not Path(outputs[0]).is_relative_to(build):
                raise RuntimeError("compiler output confinement")
        invocations[name] = record
    base = list(invocations["worker_launch_test.cpp"]["arguments"])
    source = str(worker / "worker_launch_test.cpp")
    base[base.index("worker_launch_test.cpp")] = source
    object_index = next(i for i, x in enumerate(base) if x.startswith("/Fo"))
    pdb_index = next(i for i, x in enumerate(base) if x.startswith("/Fd"))
    tests = []
    tests.append(("wrong-compiler", sys.executable, list(base)))
    changed = list(base)
    changed[changed.index(source)] = str(worker / "unapproved.cpp")
    tests.append(("wrong-source", tools["cl"], changed))
    changed = list(base)
    changed[object_index] = "/Fo" + str(worker / "rejected.obj")
    tests.append(("escaped-object", tools["cl"], changed))
    changed = list(base)
    changed[pdb_index] = "/Fd" + str(worker / "rejected.pdb")
    tests.append(("escaped-pdb", tools["cl"], changed))
    tests.append(("duplicate-source", tools["cl"], base + [source]))
    tests.append(("duplicate-object", tools["cl"], base + ["/Fo" + str(build / "rejected.obj")]))
    tests.append(("response-file", tools["cl"], base + ["@relative.rsp"]))
    tests.append(("unknown-output", tools["cl"], base + ["/Fe" + str(build / "rejected.exe")]))
    before = {name: digest(directory / (name + ".json")) for name in names}
    for label, compiler, args in tests:
        step, _ = run([cmake, "-P", launcher, "--", compiler, *args], build,
                      root / ("reject-" + label + ".log"), timeout=15, expected=1)
        steps.append(step)
    if before != {name: digest(directory / (name + ".json")) for name in names}:
        raise RuntimeError("rejected invocation overwrote actual compiler evidence")
    return {"sha256": digest(launcher), "resolved_invocations": invocations,
            "invocation_sha256": before, "rejected_cases": [x[0] for x in tests]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--cmake", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("this qualification is Windows/MSVC only")
    source = Path(__file__).resolve().parent
    upstream = args.upstream.resolve(strict=True)
    cmake = args.cmake.resolve(strict=True)
    ninja = cmake.with_name("ninja.exe")
    output = args.output.absolute()
    if output.is_relative_to(source) or output.is_relative_to(upstream):
        parser.error("output must be outside both source inputs")
    # No existing output/cache can become a supposedly clean comparison.
    output.mkdir(parents=True, exist_ok=False)
    evidence = {"status": "failed", "models_loaded": False, "staged": False,
                "upstream_commit": UPSTREAM, "probe_only": args.probe_only,
                "python_version": sys.version}
    try:
        tools = {}
        for name in ("git", "cl", "link", "lib", "dumpbin", "rc", "mt"):
            found = shutil.which(name + ".exe")
            if not found:
                raise RuntimeError("missing provisioned tool: " + name)
            tools[name] = str(Path(found).resolve())
        for name, path in {**tools, "cmake": str(cmake), "ninja": str(ninja),
                           "python": sys.executable}.items():
            evidence.setdefault("tools", {})[name] = {"path": path, "sha256": digest(Path(path))}
        # Refuse ambient flag/compiler/cache overrides; record trusted SDK paths.
        for name in ("CL", "_CL_", "LINK", "_LINK_", "CFLAGS", "CXXFLAGS", "LDFLAGS",
                     "CC", "CXX", "CMAKE_TOOLCHAIN_FILE", "CMAKE_GENERATOR", "NINJA_STATUS"):
            if os.environ.get(name):
                raise RuntimeError("ambient build override: " + name)
        evidence["environment"] = {name: os.environ.get(name) for name in
                                   ("VCToolsVersion", "WindowsSDKVersion", "VSCMD_ARG_TGT_ARCH",
                                    "INCLUDE", "LIB", "LIBPATH", "TEMP", "TMP")}
        if os.environ.get("VSCMD_ARG_TGT_ARCH") != "x64":
            raise RuntimeError("provisioned x64 development environment required")
        if git_text(tools["git"], upstream, "rev-parse", "HEAD") != UPSTREAM:
            raise RuntimeError("unreviewed upstream commit")
        if git_text(tools["git"], upstream, "status", "--porcelain", "--untracked-files=no"):
            raise RuntimeError("modified upstream tracked sources")
        evidence["worker_source"] = {name: digest(source / name) for name in FILES}
        evidence["worker_source_revision"] = git_text(tools["git"], source, "rev-parse", "HEAD")
        evidence["worker_source_dirty"] = bool(git_text(tools["git"], source, "status", "--porcelain"))
        evidence["probes"] = [probe(output / "probe-a", tools["cl"], tools["lib"], "ASCII"),
                              probe(output / "probe space \u0394", tools["cl"], tools["lib"], "Unicode")]
        if args.probe_only:
            evidence["status"] = "probes_passed_not_a_worker_comparison"
            return
        runs = []
        # This existing CMake/Ninja stack failed full Greek and Latin-1 builds.
        # Direct compiler probes still exercise Greek; the complete comparison
        # qualifies only these independent ASCII roots with space child paths.
        for label in ("first", "b"):
            root = output / label
            root.mkdir()
            local = root / "llama source"
            steps = []
            step, _ = run([tools["git"], "clone", "--no-hardlinks", "--no-checkout", "--", upstream, local],
                          root, root / "clone.log")
            steps.append(step)
            step, _ = run([tools["git"], "-C", local, "checkout", "--detach", UPSTREAM],
                          root, root / "checkout.log")
            steps.append(step)
            if git_text(tools["git"], local, "rev-parse", "HEAD") != UPSTREAM:
                raise RuntimeError("local source clone identity")
            if git_text(tools["git"], local, "status", "--porcelain", "--untracked-files=no"):
                raise RuntimeError("local source checkout is incomplete or modified")
            inputs = inventory(tools["git"], local)
            save(root / "upstream-inputs.json", inputs)
            worker = root / "worker source"
            worker.mkdir()
            for name in FILES:
                shutil.copyfile(source / name, worker / name)
            build = root / "clean build"
            temp = root / "temp"
            temp.mkdir()
            env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
            step, _ = run([cmake, "-S", worker, "-B", build, "-G", "Ninja",
                           "-DCMAKE_MAKE_PROGRAM=" + str(ninja), "-DLLAMA_SOURCE_DIR=" + str(local),
                           "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"],
                          root, root / "configure.log", env=env)
            steps.append(step)
            step, _ = run([cmake, "--build", build, "--target", "locallore-llama-worker",
                           "locallore-schema-order-test", "locallore-worker-launch-test", "--parallel", "4"],
                          root, root / "build.log", env=env)
            steps.append(step)
            exe = build / "locallore-llama-worker.exe"
            first_bytes = exe.read_bytes()
            targets = [cmake, "--build", build, "--target", "locallore-llama-worker",
                       "locallore-schema-order-test", "locallore-worker-launch-test", "--parallel", "4"]
            step, text = run(targets, root, root / "no-op-build.log", env=env)
            steps.append(step)
            if "no work to do" not in text:
                raise RuntimeError("Ninja dependency no-op check")
            # Only this owned copied header's timestamp changes; bytes stay exact.
            os.utime(worker / "worker_launch.h", None)
            step, text = run(targets, root, root / "header-rebuild.log", env=env)
            steps.append(step)
            if "main.cpp.obj" not in text or "worker_launch_test.cpp.obj" not in text:
                raise RuntimeError("Ninja header dependencies lost by compiler launcher")
            if first_bytes != exe.read_bytes():
                raise RuntimeError("owned header rebuild changed exact worker bytes")
            launcher_info = verify_launcher(cmake, tools, root, build, worker, steps)
            for target in ("locallore-schema-order-test.exe", "locallore-worker-launch-test.exe"):
                step, _ = run([build / target], root, root / (target + ".log"), env=env, timeout=15)
                steps.append(step)
            step, _ = run([sys.executable, worker / "test_protocol.py", exe], root,
                          root / "protocol.log", env=env, timeout=60)
            steps.append(step)
            for kind in ("headers", "dependents"):
                step, _ = run([tools["dumpbin"], "/" + kind, exe], root, root / (kind + ".log"), timeout=30)
                steps.append(step)
            info = build / "llama/common/build-info.cpp"
            build_info = info.read_text(encoding="utf-8")
            if 'LLAMA_BUILD_NUMBER = 1;' not in build_info or 'LLAMA_COMMIT = "620d222";' not in build_info:
                raise RuntimeError("informational source metadata is not pinned")
            commands = json.loads((build / "compile_commands.json").read_text(encoding="utf-8"))
            if not commands or not all("/Brepro" in x["command"] and "/experimental:deterministic" in x["command"]
                                       and x["command"].count("/pathmap:") == 6 for x in commands):
                raise RuntimeError("deterministic flags missing from actual compile commands")
            binary = exe.read_bytes()
            for directory in (worker, local, build):
                for path in (str(directory), directory.as_posix()):
                    if any(path.encode(encoding) in binary for encoding in ("utf-8", "utf-16-le")):
                        raise RuntimeError("physical source/build path remains in PE")
            run_info = {"label": label, "root": str(root), "steps": steps,
                        "upstream_inputs_sha256": digest(root / "upstream-inputs.json"),
                        "worker": {"path": str(exe), "bytes": exe.stat().st_size, "sha256": digest(exe)},
                        "build_info": build_info, "compile_command_count": len(commands),
                        "physical_source_build_paths_absent": True,
                        "compiler_launcher": launcher_info, "ninja_dependencies_verified": True,
                        "compile_commands_sha256": digest(build / "compile_commands.json"),
                        "cache_sha256": digest(build / "CMakeCache.txt")}
            save(root / "manifest.json", run_info)
            if {p.name for p in worker.iterdir()} != set(FILES):
                raise RuntimeError("compiler wrote into copied source directory")
            if evidence["worker_source"] != {name: digest(worker / name) for name in FILES}:
                raise RuntimeError("compiler modified copied worker source bytes")
            runs.append(run_info)
            evidence["runs"] = runs
            save(output / "comparison.json", evidence)
        if runs[0]["upstream_inputs_sha256"] != runs[1]["upstream_inputs_sha256"]:
            raise RuntimeError("upstream input bytes differ")
        if runs[0]["worker"]["sha256"] != runs[1]["worker"]["sha256"]:
            raise RuntimeError("actual worker bytes differ; no normalization permitted")
        if Path(runs[0]["worker"]["path"]).read_bytes() != Path(runs[1]["worker"]["path"]).read_bytes():
            raise RuntimeError("actual byte comparison differs")
        if evidence["worker_source"] != {name: digest(source / name) for name in FILES}:
            raise RuntimeError("worker sources changed during comparison")
        evidence["actual_pe_bytes_equal"] = True
        evidence["status"] = "passed_same_tools_two_clean_paths"
    except BaseException as error:
        evidence["failure"] = str(error)
        raise
    finally:
        save(output / "comparison.json", evidence)
        print(json.dumps({"status": evidence["status"], "evidence": str(output / "comparison.json")}))


if __name__ == "__main__":
    main()
