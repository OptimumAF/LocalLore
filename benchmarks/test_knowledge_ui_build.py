"""Tiny coherent byte graphs, never Android/JVM/DEX/ELF execution evidence.

All file operations stay in one owned D: TemporaryDirectory. Only the literal
baseline identity is translated to its private fixture; no real fixed-profile
file can be opened. The production guarded Reader still checks every byte.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import knowledge_ui_build as b
from benchmarks import library_ui_build as shared


def enc(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def digest(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def pin(path):
    return dict(path=str(path), **digest(path.read_bytes()))


class Graph:
    def __init__(self):
        fixture_parent = Path(__file__).resolve().parents[1] / "target/b88-test-fixtures"
        fixture_parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="locallore-b88-", dir=fixture_parent)
        self.home = Path(self.temp.name)
        assert self.home.drive.upper() == "D:" and self.home.resolve() == self.home
        self.allowed = set()
        self.instances = []
        self.git_calls = []
        self.git_hook = None
        self.read_hook = None
        self.final_hook = None
        self.root, self.out, self.rec = (self.home / name for name in ("product", "capture", "recovery"))
        self.baseline = self.home / "private-baseline.json"
        self.fixed = copy.deepcopy(b._FIXED)
        self.fixed.update(root=str(self.root), capture=str(self.out), recovery=str(self.rec),
            manifest=str(self.home / "fixed-manifest.json"), source_count=4)
        self.build = self.root / "apps/android/app/build"
        self.source_names = ["README.md", "crates/synthetic/lib.rs",
            "apps/android/app/src/androidTest/java/org/locallore/app/ui/KnowledgeRecordFilterScreenTest.kt",
            "fixtures/synthetic.json"]
        rows = []
        for name in self.source_names:
            p = self.put(self.root / name, ("Opaque synthetic source " + name).encode())
            rows.append(dict(p, path=name))
        self.before = dict(head=self.fixed["head"], files=rows)
        self.after = copy.deepcopy(self.before)
        self.archive = self.put(self.out / ("source-" + self.fixed["head"] + ".zip"), b"opaque pinned source ZIP")
        self.fixed["apks"] = {
            "product_apk": self.put(self.build / "outputs/apk/debug/app-debug.apk", b"opaque synthetic product APK"),
            "test_apk": self.put(self.build / "outputs/apk/androidTest/debug/app-debug-androidTest.apk", b"opaque synthetic test APK")}
        self.fixed["native"] = {abi: self.put(self.build / "generated/rustJniLibs" / abi / "liblocallore_android.so",
            ("unstripped generated library " + abi).encode()) for abi in ("arm64-v8a", "x86_64")}
        self.audit = copy.deepcopy(b._RECORDED_AUDIT)
        assert self.audit["product_permissions"] == ["org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"]
        assert self.audit["test_permissions"] == ["android.permission.REORDER_TASKS"]
        with patch.object(b, "_FIXED", self.fixed):
            self.paths = b._paths()
        self.cases = [dict(suite="Synthetic.Suite" + str(i % 69), name="case" + str(i),
            failure=[], errors=0, skipped=0) for i in range(579)]
        self.bindings, self.jvm_pairs = [], []
        for i in range(69):
            source = self.put(self.build / "test-results/testDebugUnitTest" / ("TEST-Suite" + str(i) + ".xml"),
                ("opaque recorded XML " + str(i)).encode())
            data = Path(source["path"]).read_bytes()
            self.bindings.append(dict(source=source, copy=self.put(self.out / "android-v2/reports" /
                Path(source["path"]).name, data)))
            self.jvm_pairs.append(dict(source=source, copy=self.put(self.out / "jvm-v1/reports" /
                Path(source["path"]).name, data)))
        extra = ["reports/lint-results-debug.xml", "outputs/apk/debug/app-debug.apk",
            "outputs/apk/androidTest/debug/app-debug-androidTest.apk",
            "generated/rustJniLibs/arm64-v8a/liblocallore_android.so",
            "generated/rustJniLibs/x86_64/liblocallore_android.so"]
        for suffix in extra:
            path = self.build / suffix
            if path not in self.allowed:
                self.put(path, b"opaque recorded lint")
            self.bindings.append(dict(source=pin(path), copy=self.put(self.rec / "android-v2" /
                suffix.replace("/", "__"), path.read_bytes())))
        self.reports = dict(version=1, mode="android", files=self.bindings, cases=self.cases,
            tests=579, unique=579, failures=0, errors=0, skipped=0)
        self.jvm_reports = dict(version=1, mode="jvm", files=self.jvm_pairs,
            cases=copy.deepcopy(self.cases), tests=579, unique=579, failures=0, errors=0, skipped=0)
        package = dict(status="passed", permissions=self.audit["product_permissions"],
            libraries=self.audit["libraries"])
        pair = dict(status="passed", package=self.audit["package"], test_package=self.audit["test_package"],
            certificate_sha256=self.audit["certificate_sha256"], test_permissions=self.audit["test_permissions"],
            app={k:self.fixed["apks"]["product_apk"][k] for k in ("bytes","sha256")},
            test={k:self.fixed["apks"]["test_apk"][k] for k in ("bytes","sha256")})
        self.stdout = b"BUILD SUCCESSFUL\n81 actionable tasks: 10 executed, 71 up-to-date\n" + enc(package) + enc(pair)
        self.jvm_stdout = b"> Task :app:testDebugUnitTest\nBUILD SUCCESSFUL\n25 actionable tasks: 25 executed\n"
        self.stderr = b""
        self.jvm_stderr = b""
        self.records = self.phase_records(False)
        self.jvm_records = self.phase_records(True)
        self.dex = dict(version=1, scope="knowledge-ui-dex-evidence-v1",
            product_apk=copy.deepcopy(self.fixed["apks"]["product_apk"]),
            test_apk=copy.deepcopy(self.fixed["apks"]["test_apk"]),
            class_descriptor="Lorg/locallore/app/ui/KnowledgeRecordFilterScreenTest;",
            product_class_present=False, test_class_definitions=1,
            methods=[dict(method=name, code_units=units, runtime_junit=True, public_instance=True,
                dex_entry="classes4.dex") for name,units in sorted(zip([row[2] for row in b.ROSTER], [459,298,183,745]))],
            native_entries={}, packaged_native={},
            script=self.put(self.out / "inspect-dex-v1.py", b"opaque recorded parser; never execute"),
            android_runtime_executed=False, model_material=False)
        for abi in ("arm64-v8a", "x86_64"):
            source = self.put(self.build / "intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib" /
                abi / "liblocallore_android.so", ("stripped packaged library " + abi).encode())
            saved = self.put(self.rec / "packaged-native-v1" / abi / "liblocallore_android.so",
                Path(source["path"]).read_bytes())
            self.dex["native_entries"][abi] = {k:source[k] for k in ("bytes","sha256")}
            self.dex["packaged_native"][abi] = dict(source=source, copy=saved)
            assert source["sha256"] != self.fixed["native"][abi]["sha256"]
        self.jvm = dict(version=1, scope="knowledge-ui-jvm-execution-v1", head=self.fixed["head"],
            source_count=4, evidence={}, report_bindings=self.jvm_pairs,
            tests=579, suites=69, unique=579, failures=0, errors=0, skipped=0, actual_task_executed=True)
        self.base = dict(version=1, scope="knowledge-ui-build-baseline-v1",
            product=dict(root=self.fixed["root"], head=self.fixed["head"], source_count=4,
                source_encoding=b.SOURCE_ENCODING, source_before={}, source_after={}, source_archive=self.archive),
            evidence={}, artifacts=copy.deepcopy(self.fixed["apks"]), native=copy.deepcopy(self.fixed["native"]),
            bindings=self.bindings, facts=dict(copy.deepcopy(b._FACTS), package_audit=copy.deepcopy(self.audit)),
            instrumentations=copy.deepcopy(b.ROSTER))
        self.refresh()

    def put(self, path, raw):
        assert self.home == path or self.home in path.parents
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.allowed.add(path)
        return pin(path)

    def phase_paths(self, jvm):
        if not jvm:
            return {key:value for key,value in self.paths.items() if key not in ("jvm_execution","dex")}
        phase = self.out / "jvm-v1"
        return dict(request=phase/"request-v1.json", owner=phase/"owner-result-v1.json",
            terminal=phase/"terminal-v1.json", command_terminal=phase/"command-terminal-v1.json",
            stdout=phase/"owner-stdout-v1.bin", stderr=phase/"owner-stderr-v1.bin",
            actual_child=phase/"actual-child-v1.json", command_child=phase/"command-child-v1.json",
            source_before=phase/"source-before-v1.json", source_after=phase/"source-after-v1.json",
            report_preservation=phase/"report-preservation-v1.json",
            helper=self.out/"run-forced-jvm-v1.py", source_archive=Path(self.archive["path"]))

    def phase_records(self, jvm):
        paths = self.phase_paths(jvm)
        helper = self.put(paths["helper"], b"opaque supervised helper, never execute")
        parent = dict(pid=11, creation_filetime=101, executable="C:/Synthetic/python.exe")
        command = ([str(self.root/"apps/android/gradlew.bat"), "-p", "apps/android", "--offline",
            "--no-daemon", "--max-workers=2", "--rerun-tasks", ":app:testDebugUnitTest"] if jvm
            else [parent["executable"], "-I","-S","-B","scripts/check.py","android","--offline"])
        request = dict(command=command, cwd=str(self.root), head=self.fixed["head"],
            helper={k:helper[k] for k in ("bytes","sha256")}, source_archive=self.archive,
            environment={key:("D:/Dev/_Temp" if key in ("TEMP","TMP","TMPDIR") else "Synthetic") for key in b._ENV_KEYS},
            owner=parent, seconds=900, generated_limit_bytes=3*1024**3, controls_limit_bytes=64*1024**2)
        owner = dict(status="child_exited", cleanup_complete=True, elapsed_ms=100,
            worker_returncode=0, stdout_bytes=0, stderr_bytes=0, output_capture_complete=True)
        return dict(request=request, owner=owner,
            terminal=dict(passed=True, owner=copy.deepcopy(owner), source_equal=True, faults=[],
                samples=[dict(generated_bytes=100,controls_bytes=100)],
                final_meter=dict(generated_bytes=100,controls_bytes=100),
                source_count=4, source_archive=self.archive),
            command_terminal=dict(returncode=0, elapsed_ms=90),
            actual_child=dict(identity=dict(parent,pid=12,creation_filetime=102), helper=copy.deepcopy(request["helper"])),
            command_child=dict(identity=dict(parent,pid=13,creation_filetime=103), command=copy.deepcopy(command)))

    def refresh(self):
        for label in ("before","after"):
            self.base["product"]["source_"+label] = self.put(self.out/"android-v2"/("source-"+label+"-v1.json"),
                enc(self.before if label == "before" else self.after))
        for jvm in (False, True):
            paths = self.phase_paths(jvm)
            records = self.jvm_records if jvm else self.records
            stdout = self.jvm_stdout if jvm else self.stdout
            stderr = self.jvm_stderr if jvm else self.stderr
            records["owner"]["stdout_bytes"] = len(stdout)
            records["owner"]["stderr_bytes"] = len(stderr)
            records["terminal"]["owner"] = copy.deepcopy(records["owner"])
            evidence = {}
            for role,path in paths.items():
                if role == "stdout": evidence[role] = self.put(path, stdout)
                elif role == "stderr": evidence[role] = self.put(path, stderr)
                elif role in ("helper","source_archive"): evidence[role] = pin(path)
                elif role == "source_before": evidence[role] = self.put(path, enc(self.before))
                elif role == "source_after": evidence[role] = self.put(path, enc(self.after))
                elif role in ("reports","report_preservation"):
                    evidence[role] = self.put(path, enc(self.jvm_reports if jvm else self.reports))
                else: evidence[role] = self.put(path, enc(records[role]))
            if jvm: self.jvm["evidence"] = evidence
            else: self.base["evidence"] = evidence
        self.base["evidence"]["jvm_execution"] = self.put(self.paths["jvm_execution"], enc(self.jvm))
        self.base["evidence"]["dex"] = self.put(self.paths["dex"], enc(self.dex))
        self.seal()

    def seal(self, raw=None):
        self.seal_pin = self.put(self.baseline, enc(self.base) if raw is None else raw)

    def git(self, args):
        self.git_calls.append(tuple(args))
        if self.git_hook:
            override = self.git_hook(args)
            if override is not None:
                return override
        if args == ["rev-parse","HEAD"]:
            return (self.fixed["head"]+"\n").encode()
        if args == ["status","--porcelain","--untracked-files=all"]:
            return b""
        assert args == ["ls-files","-z"]
        return ("\0".join(self.source_names)+"\0").encode()

    def __enter__(self):
        graph = self
        class Reader(shared._Reader):
            def __init__(self):
                super().__init__()
                self.finals = 0
                graph.instances.append(self)
            def read(self, bound, **kwargs):
                requested = bound["path"]
                if requested == str(b.BASELINE_PATH):
                    bound = dict(bound, path=str(graph.baseline))
                path = Path(bound["path"])
                assert path in graph.allowed, "Attempted unadmitted real-profile file access"
                assert kwargs.get("cargo", False) is False, "Cargo aliases must never be admitted"
                result = super().read(bound, **kwargs)
                if graph.read_hook:
                    graph.read_hook(requested)
                return result
            def final(self):
                self.finals += 1
                if graph.final_hook:
                    graph.final_hook(self.finals)
                return super().final()
        self.stack = ExitStack()
        for key,value in (("_FIXED",self.fixed),("_RECORDED_AUDIT",self.audit),
            ("BASELINE_BYTES",self.seal_pin["bytes"]),("BASELINE_SHA256",self.seal_pin["sha256"]),
            ("_Reader",Reader),("_git",self.git)):
            self.stack.enter_context(patch.object(b,key,value))
        return self

    def __exit__(self, *args):
        try:
            return self.stack.__exit__(*args)
        finally:
            self.temp.cleanup()

    def publish(self):
        result = b.create_manifest()
        build = self.put(Path(self.fixed["manifest"]), enc(result))
        return result, dict(build=build, **copy.deepcopy(self.fixed["apks"]))


@unittest.skipUnless(os.name == 'nt', 'D-only held-stream byte fixtures')
class KnowledgeBuildTests(unittest.TestCase):
    def refused(self, action, category=None):
        with self.assertRaises(b.BuildRefused) as raised:
            action()
        text = str(raised.exception)
        self.assertRegex(text, r"^[a-z_]{1,64}$")
        self.assertNotIn("SYNTHETIC_PRIVATE_SENTINEL", text)
        if category is not None:
            self.assertEqual(text, category)

    def test_positive_data_only_graph_and_defensive_manifest_copy(self):
        with Graph() as g:
            before = sorted(str(p) for p in g.home.rglob("*") if p.is_file())
            manifest = b.create_manifest()
            self.assertEqual(before, sorted(str(p) for p in g.home.rglob("*") if p.is_file()))
            self.assertFalse(Path(g.fixed["manifest"]).exists())
            self.assertEqual(set(manifest), {"version","scope","mode","product","artifacts",
                "current_native_bindings","evidence","facts","instrumentations"})
            self.assertEqual(manifest["mode"], "fixed-b88-byte-attestation-v1")
            self.assertFalse(manifest["facts"]["android_runtime_executed"])
            self.assertFalse(manifest["facts"]["model_material"])
            self.assertEqual(manifest["instrumentations"], b.ROSTER)
            manifest["facts"]["feature_acceptance"] = True
            self.assertFalse(b.create_manifest()["facts"]["feature_acceptance"])
            expected, artifacts = g.publish()
            returned = b.verify_frozen_product(artifacts)
            self.assertEqual(expected, returned)
            returned["product"]["head"] = "wrong"
            self.assertEqual(expected, b.verify_frozen_product(artifacts))
            self.assertGreaterEqual(g.instances[-1].finals, 2)

    def test_public_roles_cannot_add_model_or_retarget_a_copied_manifest(self):
        with Graph() as g:
            _, valid = g.publish()
            for role in ("build","product_apk","test_apk"):
                bad = copy.deepcopy(valid); bad.pop(role)
                self.refused(lambda bad=bad:b.verify_frozen_product(bad))
            for extra in ("model","probe","admission"):
                bad = copy.deepcopy(valid); bad[extra] = copy.deepcopy(valid["test_apk"])
                self.refused(lambda bad=bad:b.verify_frozen_product(bad))
            copied = g.put(g.home/"copied-manifest.json", Path(valid["build"]["path"]).read_bytes())
            bad = dict(valid, build=copied)
            count = len(g.instances)
            self.refused(lambda:b.verify_frozen_product(bad), "binding_path")
            self.assertEqual(count, len(g.instances))
            swapped = dict(valid, product_apk=valid["test_apk"], test_apk=valid["product_apk"])
            self.refused(lambda:b.verify_frozen_product(swapped), "artifacts")

    def test_baseline_remains_literal_when_reader_file_is_copied_and_import_is_io_free(self):
        self.assertEqual(Path("D:/Worktrees/LocalLore-original-input-compose-review-v1/benchmarks/knowledge_ui_build_baseline.json"),
            b.BASELINE_PATH)
        source = Path(b.__file__).read_bytes()
        namespace = dict(__name__="benchmarks._knowledge_import_probe", __package__="benchmarks",
            __file__="D:/Dev/_Temp/copied-reader/knowledge_ui_build.py")
        with ExitStack() as stack:
            for target,name in ((Path,"open"),(Path,"stat"),(Path,"lstat"),(Path,"mkdir"),
                (subprocess,"run"),(subprocess,"Popen"),(os,"system")):
                stack.enter_context(patch.object(target,name,side_effect=AssertionError("Import performed I/O")))
            exec(compile(source,namespace["__file__"],"exec"),namespace)
        self.assertEqual(b.BASELINE_PATH, namespace["BASELINE_PATH"])
        self.assertFalse("verify_current" in namespace)
        self.assertIs(shared._Reader, namespace["_Reader"])

    def test_manifest_profile_types_and_runtime_claims_cannot_be_coherently_resealed(self):
        mutations = [
            lambda m:m.update(mode="fixed-b80-byte-attestation-v1"),
            lambda m:m.update(version=True),
            lambda m:m["product"].update(root="D:/Other/product"),
            lambda m:m["instrumentations"].reverse(),
            lambda m:m["facts"].update(android_runtime_executed=True),
            lambda m:m["facts"].update(model_material=True),
            lambda m:m.update(admission={"approved":True}),
        ]
        with Graph() as g:
            expected, artifacts = g.publish()
            for mutation in mutations:
                wrong = copy.deepcopy(expected); mutation(wrong)
                bad = dict(artifacts, build=g.put(Path(g.fixed["manifest"]),enc(wrong)))
                self.refused(lambda bad=bad:b.verify_frozen_product(bad),"manifest")
            g.put(Path(g.fixed["manifest"]),enc(expected))

    def test_baseline_closed_keys_types_source_counts_and_fixed_roster_refuse(self):
        mutations = [
            lambda v:v.update(version=True),
            lambda v:v["product"].update(source_count=True),
            lambda v:v["product"].update(head="1"*40),
            lambda v:v["product"].update(source_encoding="normalized LF"),
            lambda v:v["instrumentations"].append(copy.deepcopy(v["instrumentations"][0])),
            lambda v:v["facts"].update(jvm_cases=True),
            lambda v:v.update(optional_profile="caller-selected"),
        ]
        for mutation in mutations:
            g=Graph(); mutation(g.base); g.seal()
            with g: self.refused(b.create_manifest)

    def test_audit_missing_extra_network_or_wrong_test_permissions_reach_audit_guard(self):
        wrong_product = [[], ["org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION","android.permission.INTERNET"],
            ["android.permission.INTERNET"]]
        for wrong in wrong_product:
            g=Graph(); lines=g.stdout.decode().splitlines(); package=json.loads(lines[-2])
            package["permissions"]=wrong; g.stdout=("\n".join(lines[:-2])+"\n").encode()+enc(package)+enc(json.loads(lines[-1]))
            g.refresh()
            with g:self.refused(b.create_manifest,"audit")
        g=Graph(); lines=g.stdout.decode().splitlines(); pair=json.loads(lines[-1]);pair["test_permissions"]=[]
        g.stdout=("\n".join(lines[:-1])+"\n").encode()+enc(pair);g.refresh()
        with g:self.refused(b.create_manifest,"audit")

    def test_owner_identity_commands_cleanup_and_exact_integer_types_refuse(self):
        mutations = [
            lambda g:g.records["owner"].update(cleanup_complete=False),
            lambda g:g.records["owner"].update(output_capture_complete=False),
            lambda g:g.records["owner"].update(worker_returncode=False),
            lambda g:g.records["command_terminal"].update(returncode=7),
            lambda g:g.records["actual_child"]["identity"].update(pid=g.records["request"]["owner"]["pid"]),
            lambda g:g.records["request"]["command"].append("--caller-selected"),
            lambda g:g.records["terminal"]["samples"][0].update(generated_bytes=3*1024**3+1),
        ]
        for mutation in mutations:
            g=Graph();mutation(g);g.refresh()
            with g:self.refused(b.create_manifest)

    def test_current_source_closure_maps_archive_and_immutable_copies_are_all_bound(self):
        for role in ("source","archive","copy","native","apk"):
            with Graph() as g:
                path = {"source":g.root/g.source_names[0], "archive":Path(g.archive["path"]),
                    "copy":Path(g.bindings[0]["copy"]["path"]), "native":Path(g.fixed["native"]["x86_64"]["path"]),
                    "apk":Path(g.fixed["apks"]["product_apk"]["path"])}[role]
                old=path.read_bytes();path.write_bytes(bytes([old[0]^1])+old[1:])
                self.refused(b.create_manifest)
        for change in ("dirty","head","roster"):
            with Graph() as g:
                g.git_hook = lambda args,change=change: (b"?? SYNTHETIC_PRIVATE_SENTINEL\n" if change=="dirty" and args[0]=="status"
                    else b"f"*40+b"\n" if change=="head" and args[0]=="rev-parse"
                    else b"wrong\0" if change=="roster" and args[0]=="ls-files" else None)
                self.refused(b.create_manifest)
        g=Graph();g.after["files"][0]["sha256"]="0"*64;g.refresh()
        with g:self.refused(b.create_manifest,"source_changed")

    def test_fresh_jvm_proof_cannot_borrow_cached_execution_or_a_different_case_set(self):
        for change in ("cached","flag","cases","copy"):
            g=Graph()
            if change=="cached":g.jvm_stdout=g.jvm_stdout.replace(b"> Task :app:testDebugUnitTest\n",
                b"> Task :app:testDebugUnitTest UP-TO-DATE\n")
            elif change=="flag":g.jvm["actual_task_executed"]=False
            elif change=="cases":g.jvm_reports["cases"][0]["name"]="different-case"
            else:g.jvm_pairs[0]["copy"]=g.jvm_pairs[1]["copy"]
            g.refresh()
            with g:self.refused(b.create_manifest)

    def test_recorded_dex_definitions_and_packaged_native_cannot_be_string_presence_only(self):
        for change in ("product","definition","junit","public","empty","name","native","script"):
            g=Graph()
            if change=="product":g.dex["product_class_present"]=True
            elif change=="definition":g.dex["test_class_definitions"]=True
            elif change=="junit":g.dex["methods"][0]["runtime_junit"]=False
            elif change=="public":g.dex["methods"][0]["public_instance"]=False
            elif change=="empty":g.dex["methods"][0]["code_units"]=0
            elif change=="name":g.dex["methods"][0]["method"]=g.dex["methods"][1]["method"]
            elif change=="native":g.dex["native_entries"]["x86_64"]={k:g.fixed["native"]["x86_64"][k] for k in ("bytes","sha256")}
            else:g.dex["script"]=g.put(g.home/"other-parser.py",b"opaque other parser")
            g.refresh()
            with g:self.refused(b.create_manifest)

    def test_ordinary_native_hardlinks_never_receive_shared_cargo_alias_privileges(self):
        with Graph() as g:
            native=Path(g.fixed["native"]["x86_64"]["path"])
            os.link(native,g.home/"unadmitted-native-alias.so")
            self.refused(b.create_manifest,"file")

    def test_final_guards_detect_changes_after_semantic_validation_in_both_public_interfaces(self):
        with Graph() as g:
            target=Path(g.fixed["apks"]["product_apk"]["path"]);old=target.read_bytes()
            g.final_hook=lambda count: target.write_bytes(bytes([old[0]^1])+old[1:]) if count==1 else None
            self.refused(b.create_manifest)
            self.assertEqual(1,g.instances[-1].finals)
        with Graph() as g:
            _,artifacts=g.publish();target=Path(g.fixed["native"]["x86_64"]["path"]);old=target.read_bytes()
            g.final_hook=lambda count: target.write_bytes(bytes([old[0]^1])+old[1:]) if count==2 else None
            self.refused(lambda:b.verify_frozen_product(artifacts))
            self.assertEqual(2,g.instances[-1].finals)

    def test_duplicate_json_nonfinite_oversized_and_private_io_errors_fail_bounded(self):
        for raw in (b'{"version":1,"version":1}',b'{"version":NaN}',b"\xff"):
            g=Graph();g.seal(raw)
            with g:self.refused(b.create_manifest)
        g=Graph();g.seal(b" "*(2*1024**2+1))
        with g:self.refused(b.create_manifest,"size")
        with Graph() as g:
            def fail(_):
                raise OSError("SYNTHETIC_PRIVATE_SENTINEL")
            g.read_hook=fail
            self.refused(b.create_manifest,"build")


if __name__ == "__main__":
    unittest.main()

