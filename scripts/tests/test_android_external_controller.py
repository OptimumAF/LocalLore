"""Synthetic host orchestration only. All SDK/owner observations are mocked."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import android_external_controller as external
from scripts.tests import test_android_process_controller_evidence as controller_fixture
from scripts.tests import test_android_retirement_evidence as retirement_fixture


def deep_fixture(root, case):
    """Original synthetic domain fixture, with real validators and retained bytes."""
    out, guest = root / "out", root / "guest"
    out.mkdir(); guest.mkdir()
    if case in external.RETIRED:
        proof, helpers, sidecars, expected = retirement_fixture.fixture(case == external.CASES[3])
        proof.update(stage="DONE", reason="NONE", checks=200 if case == external.CASES[3] else 139,
                     last_workspace_read="VALID", last_workspace_utf16_length=80)
        # Keep the synthetic entry clocks consistent with actual source ordering.
        for mode, clock in (("load", 150), ("probe", 220), ("retire", 230)):
            body = json.loads(helpers[mode])
            body["started_uptime_ms"] = clock
            helpers[mode] = controller_fixture.encoded(body) + b"\n"
        retirement_fixture.rebind(proof, helpers)
    else:
        proof, expected = controller_fixture.original(case)
        helpers, sidecars = {}, {}
    records = controller_fixture.product_records(proof)
    saved = json.loads(records["saved"])
    saved["sequence"] = proof["terminal_observations"][1]["saved_sequence"]
    records["saved"] = controller_fixture.encoded(saved)
    request = dict(case=case, run_id=expected["run_id"], out=str(out), driver_sha256="e" * 64, inputs=[])
    for key in ("build", "gate", "running", "proposal", "server", "powershell"):
        path = root / (key + ".json")
        path.write_text(json.dumps({"root": str(guest)} if key == "running" else {"synthetic": key}))
        request[key] = str(path)
    request["sdk"] = str(root)
    source = out / "sources-before-v1.json"
    source.write_text("{}")
    request["sources"] = external.environment.binding(source)
    (out / "request-v1.json").write_text(json.dumps(request))
    external.environment.create_json(guest / external.CLAIM, external.claim_value(request))
    uids = {external.driver.APP: expected["product_uid"], external.driver.CONTROL: expected["controller_uid"], external.driver.APP + ".test": 12349}
    blobs = {"controller.stdout": controller_fixture.frame(proof), "fixture": controller_fixture.encoded(proof["fixture"]), **records}
    for mode, raw in helpers.items():
        blobs["helper-" + mode] = raw
        blobs["transport-" + mode] = raw + b"\nLL_RETIRED_HELPER_EXIT_V1=0\n\nLL_PROCESS_EXIT_V1=0\n"
    for leaf, raw in sidecars.items():
        blobs["sidecar-" + leaf[:-5]] = raw
    last = proof["observations"][2]
    blobs["postflight-processes"] = (f"PID UID NAME\n1 0 harmless kernel name\n{last['pid']} {expected['product_uid']} {external.driver.APP}\n").encode()
    for label, raw in blobs.items():
        (out / (label + ".raw")).write_bytes(raw)
    external.environment.create_json(out / "proof-v1.json", proof)
    (out / "clients").mkdir()
    client_count = 0
    for label, raw in blobs.items():
        client_count += 1
        client_label = "controller" if label == "controller.stdout" else label if label == "postflight-processes" else "read-" + label
        stem = out / "clients" / ("command-%04d" % client_count)
        stem.with_suffix(".stdout.bin").write_bytes(raw)
        external.environment.create_json(stem.with_suffix(".json"), dict(version=1,index=client_count,label=client_label,
            status="completed",returncode=0,cleanup_complete=True,stdout_bytes=len(raw),stdout_sha256=hashlib.sha256(raw).hexdigest(),stderr_bytes=0))
    binding = lambda label: external.environment.binding(out / (label + ".raw"))
    record = dict(version=1,case=case,run_id=request["run_id"],expected=expected,uids=uids,clients=client_count,
        clients_clean=True,reused_installation=False,claim=external.environment.binding(guest / external.CLAIM),
        controller=binding("controller.stdout"),proof=external.environment.binding(out / "proof-v1.json"),
        records={k: binding(k) for k in records}, fixture=binding("fixture"),
        helpers={k: binding("helper-" + k) for k in helpers},transports={k: binding("transport-" + k) for k in helpers},
        sidecars={k: binding("sidecar-" + k[:-5]) for k in sidecars},postflight=binding("postflight-processes"))
    external.environment.create_json(out / "external-v1.json", record)
    gate = dict(request, running=str(root / "old-running.json"), proposal=str(root / "old-proposal.json"))
    return SimpleNamespace(out=out, guest=guest, request=request, gate=gate, expected=expected, record=record, proof=proof)


class DeepExecutionTests(unittest.TestCase):
    def validate(self, fixture):
        # Artifact/lease admission is separately tested; no process observation.
        # The controller, product, helper/sidecar, fixture and client validators
        # are all real here, not replaced by a passed-label mock.
        with patch.object(external, "admit"), patch.object(external.driver, "qualified_build", return_value={}), \
             patch.object(external, "qualified_gate", return_value=fixture.gate), \
             patch.object(external, "expected_pins", return_value=fixture.expected):
            return external.validate_execution(fixture.request, fixture.out)

    def test_all_four_complete_original_evidence_sets_pass_real_deep_validators(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                f = deep_fixture(Path(temporary), case)
                self.assertEqual(self.validate(f), f.record)

    def test_changed_raw_or_client_copy_cannot_retain_passed_summary(self):
        for kind in ("raw", "copy", "proof", "fixture"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                f = deep_fixture(Path(temporary), external.CASES[0])
                if kind == "copy":
                    (f.out / "clients/command-0001.stdout.bin").write_bytes(b"changed")
                elif kind == "proof":
                    (f.out / "proof-v1.json").write_text(json.dumps(dict(f.proof, process_deaths=1)))
                elif kind == "fixture":
                    # Even rebinding a locally edited fixture cannot change the
                    # original authoritative fixture in the captured proof.
                    raw = dict(f.proof["fixture"], controller_uid=True)
                    (f.out / "fixture.raw").write_bytes(controller_fixture.encoded(raw))
                    f.record["fixture"] = external.environment.binding(f.out / "fixture.raw")
                    (f.out / "external-v1.json").write_text(json.dumps(f.record))
                else:
                    (f.out / "controller.stdout.raw").write_bytes(b"changed")
                with self.assertRaises(RuntimeError):
                    self.validate(f)

    def test_rebound_retained_sidecar_and_claim_are_semantically_refused(self):
        for kind in ("sidecar", "claim"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                f = deep_fixture(Path(temporary), external.CASES[3])
                if kind == "sidecar":
                    leaf = external.SIDECARS[0]
                    path = f.out / ("sidecar-" + leaf[:-5] + ".raw")
                    data = json.loads(path.read_bytes())
                    data["views"]["retained"]["revision"] = 99
                    path.write_bytes(retirement_fixture.canonical(data))
                    f.record["sidecars"][leaf] = external.environment.binding(path)
                else:
                    path = f.guest / external.CLAIM
                    data = json.loads(path.read_bytes()); data["run_id"] = "f" * 16
                    path.write_text(json.dumps(data))
                    f.record["claim"] = external.environment.binding(path)
                (f.out / "external-v1.json").write_text(json.dumps(f.record))
                with self.assertRaises(RuntimeError):
                    self.validate(f)

    def test_postflight_binds_pid_uid_name_and_both_old_processes_absent(self):
        proof, expected = controller_fixture.original()
        uids = {external.driver.APP: expected["product_uid"]}
        good = f"PID UID NAME\n203 {expected['product_uid']} {external.driver.APP}\n".encode()
        external.validate_postflight(good, proof, uids)
        for raw in (good.replace(b"203 ", b"204 "), good.replace(str(expected["product_uid"]).encode(), b"12346"),
                    good.replace(external.driver.APP.encode(), b"disguised"), good + b"201 0 old PID recycled\n",
                    good + f"204 {expected['product_uid']} helper\n".encode(), good + b"203 0 duplicate pid\n"):
            with self.assertRaises(external.ExternalRefused):
                external.validate_postflight(raw, proof, uids)

    def test_worker_claim_is_burned_before_session_and_cannot_replay_in_new_out(self):
        with tempfile.TemporaryDirectory() as temporary:
            f = deep_fixture(Path(temporary), external.CASES[0])
            (f.guest / external.CLAIM).unlink()  # Remove only this test's own setup marker before its first worker.
            live = SimpleNamespace(descriptor={"root": str(f.guest)}, check=lambda: None)
            with patch.object(external, "admit"), patch.object(external.driver, "qualified_build", return_value={}), \
                 patch.object(external, "qualified_gate", return_value=f.gate), \
                 patch.object(external.environment, "open_live_owner", return_value=live), \
                 patch.object(external, "Session", side_effect=external.ExternalRefused("synthetic_stop")) as session:
                with self.assertRaises(external.ExternalRefused):
                    external.worker(f.request, f.out)
                self.assertTrue((f.guest / external.CLAIM).is_file())
                other = Path(temporary) / "other-out"; other.mkdir()
                replay = dict(f.request, out=str(other))
                (other / "request-v1.json").write_text(json.dumps(replay))
                with self.assertRaises(FileExistsError):
                    external.worker(replay, other)
                self.assertEqual(session.call_count, 1)

    def test_invalid_clean_controller_collects_missing_raws_before_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            f = deep_fixture(Path(temporary), external.CASES[3])
            # This test owns and removes only its setup outputs, never guest data.
            run = Path(temporary) / "new-out"; run.mkdir()
            request = dict(f.request, out=str(run))
            (run / "request-v1.json").write_text(json.dumps(request))
            (f.guest / external.CLAIM).unlink()
            labels = []
            class CleanSession:
                def __init__(self, *_):
                    self.capture = SimpleNamespace(clean=True, count=0, check_server=lambda: None)
                def check(self): pass
                def user_zero(self): pass
                def adb(self, operation, label, *args, **kwargs):
                    labels.append(label)
                    return b"INSTRUMENTATION_CODE: 0\n" if label == "controller" else external.MISSING
                def shell(self, operation, label, *args, **kwargs):
                    labels.append(label)
                    return b"PID UID NAME\n"
            live = SimpleNamespace(descriptor={"root": str(f.guest)}, check=lambda: None)
            with patch.object(external, "admit"), patch.object(external.driver, "qualified_build", return_value={}), \
                 patch.object(external, "qualified_gate", return_value=f.gate), \
                 patch.object(external.environment, "open_live_owner", return_value=live), \
                 patch.object(external, "Session", CleanSession), patch.object(external, "install_or_verify", return_value=f.record["uids"]), \
                 patch.object(external, "check_processes"), patch.object(external, "expected_pins", return_value=f.expected):
                with self.assertRaises(RuntimeError):
                    external.worker(request, run)
            self.assertEqual(labels[0], "controller")
            self.assertEqual(labels[-1], "postflight-processes")
            self.assertEqual(sum(label.startswith("read-") for label in labels), 14)
            self.assertEqual((run / "created.raw").read_bytes(), external.MISSING)
            self.assertEqual((run / "sidecar-retire-after-v1.raw").read_bytes(), external.MISSING)
            self.assertFalse((run / "external-v1.json").exists())

    def test_sdk_uncertainty_never_dispatches_diagnostic_reads(self):
        with tempfile.TemporaryDirectory() as temporary:
            f = deep_fixture(Path(temporary), external.CASES[3])
            run = Path(temporary) / "new-out"; run.mkdir()
            request = dict(f.request, out=str(run))
            (run / "request-v1.json").write_text(json.dumps(request))
            (f.guest / external.CLAIM).unlink()
            fake = SimpleNamespace(user_zero=lambda: None,
                adb=lambda *a, **k: (_ for _ in ()).throw(external.ExternalRefused("synthetic_sdk_unknown")))
            live = SimpleNamespace(descriptor={"root": str(f.guest)}, check=lambda: None)
            with patch.object(external, "admit"), patch.object(external.driver, "qualified_build", return_value={}), \
                 patch.object(external, "qualified_gate", return_value=f.gate), \
                 patch.object(external.environment, "open_live_owner", return_value=live), \
                 patch.object(external, "Session", return_value=fake), \
                 patch.object(external, "install_or_verify", return_value=f.record["uids"]), \
                 patch.object(external, "check_processes"), patch.object(external, "expected_pins", return_value=f.expected), \
                 patch.object(external, "collect_blob") as collect:
                with self.assertRaises(external.ExternalRefused):
                    external.worker(request, run)
                collect.assert_not_called()
            self.assertFalse((run / "postflight-processes.raw").exists())

    def test_known_owner_invalid_external_records_are_retained_as_failed(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "new"
            request = {key: temporary for key in external.FIELDS}
            request.update(out=str(out),case=external.CASES[0],run_id="0123456789abcdef")
            raw = (external.WORKER_LINE + "\n").encode()
            owner = dict(status="child_exited",worker_returncode=0,cleanup_complete=True,output_capture_complete=True,
                         elapsed_ms=1,stdout_bytes=len(raw),stderr_bytes=0)
            order = []
            original_create = external.environment.create_json
            def create(path, value):
                order.append(Path(path).name)
                return original_create(path, value)
            def supervise(*args):
                (out / "owner-stdout-v1.bin").write_bytes(raw)
                (out / "owner-stderr-v1.bin").write_bytes(b"")
                return owner
            def invalid(*_):
                self.assertIn("owner-result-v1.json", order)
                raise external.ExternalRefused("synthetic_bad_proof")
            with patch.object(external, "bindings", return_value=[]), patch.object(external, "admit"), \
                 patch.object(external.driver, "source_map", return_value={}), \
                 patch.object(external.environment, "supervise", side_effect=supervise), \
                 patch.object(external.environment, "create_json", side_effect=create), \
                 patch.object(external, "validate_execution", side_effect=invalid):
                with self.assertRaises(external.ExternalRefused):
                    external.supervise(request)
            value = json.loads((out / "result-v1.json").read_bytes())
            self.assertFalse(value["passed"])
            self.assertTrue(value["validation_refused"])


class ExternalControllerTests(unittest.TestCase):
    def test_all_case_dispatches_are_create_only_pinned_and_bounded(self):
        for case in external.CASES:
            expected = controller_fixture.pins(case)
            request = dict(case=case, run_id=expected["run_id"])
            operation = external.controller_operation(request, expected)
            self.assertEqual(operation[:7], ["exec-out", "am", "instrument", "--user", "0", "-w", "-r"])
            self.assertEqual(operation[-1], external.driver.CONTROL + "/org.locallore.processverify.ProcessRestoreInstrumentation")
            self.assertIn("create", operation)
            self.assertNotIn("reuse", operation)
            self.assertEqual("fixture_test_sha256" in operation, case in external.RETIRED)

    def test_read_script_has_owner_no_link_and_positive_bounded_fixed_leaf_guards(self):
        body = external.read_script("no_backup/process-verify-v1/0123456789abcdef/saved.json", 12345, 4096)
        self.assertIn("test $(id -u) -eq 12345", body)
        self.assertIn("test ! -L no_backup/process-verify-v1", body)
        self.assertIn("-le 4096", body)
        self.assertIn("-gt 0", body)
        for path in ("/arbitrary", "no_backup/../foreign", "no_backup/./foreign", "no_backup//foreign", "no_backup/file;other"):
            with self.assertRaises(external.ExternalRefused):
                external.read_script(path, 12345, 4096)
        for uid, cap in ((True, 4096), (9999, 4096), (12345, 262145), (12345, True)):
            with self.assertRaises(external.ExternalRefused):
                external.read_script("no_backup/fixed.json", uid, cap)

    def test_transport_requires_exact_original_json_lf_and_both_zero_footers(self):
        bodies = {mode: b'{"synthetic":true}\n' for mode in ("load", "probe", "retire")}
        suffix = b"\nLL_RETIRED_HELPER_EXIT_V1=0\n\nLL_PROCESS_EXIT_V1=0\n"
        wires = {mode: body + suffix for mode, body in bodies.items()}
        external.helper_transports(bodies, wires)
        for changed in (dict(wires, retire=wires["retire"].replace(b"EXIT_V1=0", b"EXIT_V1=1", 1)),
                        dict(wires, retire=wires["retire"] + b"chatter\n"), dict(wires, probe=wires["probe"].replace(b"\n", b"\r\n"))):
            with self.assertRaises(external.ExternalRefused):
                external.helper_transports(bodies, changed)

    def test_host_claim_is_create_only_and_case_independent_per_guest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / external.CLAIM
            external.environment.create_json(path, {"case": external.CASES[0]})
            with self.assertRaises(FileExistsError):
                external.environment.create_json(path, {"case": external.CASES[3]})
            self.assertEqual(json.loads(path.read_bytes()), {"case": external.CASES[0]})

    def test_same_guest_reuse_requires_both_lease_paths_and_same_server_pin(self):
        request = dict(running="running", proposal="proposal", sdk="sdk", powershell="ps", server="current")
        gate = dict(request, server="gate")
        with patch.object(external.environment, "read_json", return_value={"pid": 1}):
            self.assertTrue(external.reuse_installation(request, gate))
            self.assertFalse(external.reuse_installation(request, dict(gate, running="other", proposal="other")))
            with self.assertRaises(external.ExternalRefused):
                external.reuse_installation(request, dict(gate, running="other"))
        with patch.object(external.environment, "read_json", side_effect=[{"pid": 1}, {"pid": 2}]):
            with self.assertRaises(external.ExternalRefused):
                external.reuse_installation(request, gate)

    def test_qualified_gate_does_not_trust_passed_label(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result-v1.json"
            path.write_text(json.dumps({"version": 1, "phase": "components", "passed": True}))
            with self.assertRaises(external.ExternalRefused):
                external.qualified_gate(path, path)

    def test_qualified_ten_method_gate_replays_runner_rosters_and_exact_client_copies(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "clients").mkdir()
            results = []
            for index, (name, methods) in enumerate(zip(external.driver.CLASSES, external.driver.EXPECTED_METHODS)):
                cls = "org.locallore.app." + name
                lines = []
                for ordinal, method in enumerate(methods, 1):
                    for status in (1, 0):
                        lines += ["INSTRUMENTATION_STATUS: class=" + cls, "INSTRUMENTATION_STATUS: test=" + method,
                            "INSTRUMENTATION_STATUS: current=" + str(ordinal), "INSTRUMENTATION_STATUS: numtests=" + str(len(methods)),
                            "INSTRUMENTATION_STATUS_CODE: " + str(status)]
                lines += ["INSTRUMENTATION_RESULT: stream=", "Time: 0.1", "", "OK (" + str(len(methods)) + " tests)", "", "INSTRUMENTATION_CODE: -1", ""]
                raw = "\n".join(lines).encode()
                (out / (name + ".stdout.raw")).write_bytes(raw)
                results.append({"class": cls, "methods": list(methods), "method_count": len(methods), "passed": True,
                                "stdout_sha256": hashlib.sha256(raw).hexdigest()})
                stem = out / "clients" / ("command-%04d" % (index + 1))
                stem.with_suffix(".stdout.bin").write_bytes(raw)
                external.environment.create_json(stem.with_suffix(".json"), dict(version=1,index=index + 1,label="instrument-" + str(index),
                    status="completed",returncode=0,cleanup_complete=True,stdout_bytes=len(raw),stdout_sha256=hashlib.sha256(raw).hexdigest(),stderr_bytes=0))
            source = {"synthetic": "source-sha"}
            for leaf in ("sources-before-v1.json", "sources-after-v1.json"):
                external.environment.create_json(out / leaf, source)
            request = dict(phase="components",out=str(out),build=str(out / "build-result-v1.json"),inputs=[],
                           sources=external.environment.binding(out / "sources-before-v1.json"))
            external.environment.create_json(out / "request-v1.json", request)
            worker_raw = b"worker_completed\n"
            owner = dict(status="child_exited",worker_returncode=0,cleanup_complete=True,output_capture_complete=True,
                         elapsed_ms=1,stdout_bytes=len(worker_raw),stderr_bytes=0)
            external.environment.create_json(out / "owner-result-v1.json", owner)
            (out / "owner-stdout-v1.bin").write_bytes(worker_raw); (out / "owner-stderr-v1.bin").write_bytes(b"")
            components = dict(version=1,results=results,clients=3,clients_clean=True,method_count=10,external_controller_case_executed=False)
            external.environment.create_json(out / "components-v1.json", components)
            record = dict(version=1,phase="components",passed=True,owner=owner,
                **{key: external.environment.binding(out / leaf) for key, leaf in
                   (("owner_record", "owner-result-v1.json"), ("request", "request-v1.json"), ("sources_before", "sources-before-v1.json"),
                    ("sources_after", "sources-after-v1.json"), ("components", "components-v1.json"))})
            external.environment.create_json(out / "result-v1.json", record)
            with patch.object(external.driver, "admit_worker"), patch.object(external.driver, "input_bindings", return_value=[]), \
                 patch.object(external.driver, "source_map", return_value=source):
                self.assertEqual(external.qualified_gate(out / "result-v1.json", request["build"]), request)
                stem = out / "clients/command-0001"
                changed = b"synthetic other client bytes"
                stem.with_suffix(".stdout.bin").write_bytes(changed)
                metadata = json.loads(stem.with_suffix(".json").read_bytes())
                metadata.update(stdout_bytes=len(changed),stdout_sha256=hashlib.sha256(changed).hexdigest())
                stem.with_suffix(".json").write_text(json.dumps(metadata))
                with self.assertRaises(external.ExternalRefused):
                    external.qualified_gate(out / "result-v1.json", request["build"])

    def test_json_comparison_distinguishes_bool_integer_and_array_order(self):
        self.assertTrue(external.same_json({"a": [1, True]}, {"a": [1, True]}))
        self.assertFalse(external.same_json({"head": 0}, {"head": False}))
        self.assertFalse(external.same_json([1, 2], [2, 1]))

    def test_session_owner_failure_is_sticky_without_further_client(self):
        session = external.Session.__new__(external.Session)
        session.request, session.sources, session.failed = {}, {}, False
        session.live = SimpleNamespace(check=lambda: (_ for _ in ()).throw(RuntimeError("private")))
        session.capture = SimpleNamespace(clean=True, adb=lambda *a: self.fail("SDK dispatched"))
        with self.assertRaises(external.ExternalRefused):
            session.adb(["get-state"], "state")
        self.assertTrue(session.failed)
        self.assertFalse(session.capture.clean)
        with self.assertRaises(external.ExternalRefused):
            session.check()

    def test_bound_blob_checks_physical_size_before_hash_or_load(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "blob"
            path.write_bytes(b"more-than-declared")
            with patch.object(external.environment, "check_binding") as check:
                with self.assertRaises(external.ExternalRefused):
                    external.bound_bytes({"path": str(path), "bytes": 1, "sha256": "a" * 64}, path, 4096)
                check.assert_not_called()

    def test_client_records_and_exact_copy_correspondence_are_revalidated(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "clients").mkdir()
            body = b"original synthetic raw"
            stem = out / "clients/command-0001"
            stem.with_suffix(".stdout.bin").write_bytes(body)
            record = dict(version=1, index=1, label="controller", status="completed", returncode=0, cleanup_complete=True,
                          stdout_bytes=len(body), stdout_sha256=hashlib.sha256(body).hexdigest(), stderr_bytes=0)
            stem.with_suffix(".json").write_text(json.dumps(record))
            external.validate_clients(out, 1, {"controller": body})
            for changes in ({"returncode": False}, {"cleanup_complete": False}, {"stdout_sha256": "a" * 64}, {"index": True}):
                stem.with_suffix(".json").write_text(json.dumps(dict(record, **changes)))
                with self.assertRaises(external.ExternalRefused):
                    external.validate_clients(out, 1, {"controller": body})

    def test_parse_packages_rejects_duplicates_unrelated_or_non_numeric_shape(self):
        package = external.driver.APP
        self.assertEqual(external.parse_packages(("package:" + package + " uid:12345\n").encode()), {package: 12345})
        for raw in (b"package:x uid:True\n", b"package:x uid:9999\n", b"package:x uid:12345\npackage:x uid:12345\n"):
            with self.assertRaises(external.ExternalRefused):
                external.parse_packages(raw)

    def test_no_adoption_of_packages_without_same_guest_gate(self):
        package = external.driver.APP
        session = SimpleNamespace(shell=lambda *a, **k: ("package:" + package + " uid:12345\n").encode(),
                                  adb=lambda *a, **k: self.fail("install dispatched"))
        with self.assertRaises(external.ExternalRefused):
            external.install_or_verify(session, {"apks": []}, False)

    def test_barrier_rejects_bad_request_before_worker_or_sdk(self):
        for data in (b"", b"x" * 4097, b"path\v" + b"a" * 64 + b"\n", b"path\n" + b"a" * 64):
            with patch.object(sys, "argv", ["driver", "_worker"]), patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data))), \
                 patch.object(external, "worker") as worker:
                with self.assertRaises(external.ExternalRefused):
                    external.main()
                worker.assert_not_called()

    def test_worker_request_sha_and_source_admission_precede_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "request-v1.json"
            path.write_text(json.dumps({"out": temporary}))
            data = (str(path) + "\n" + "a" * 64 + "\n").encode()
            with patch.object(sys, "argv", ["driver", "_worker"]), patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data))), \
                 patch.object(external, "worker") as worker:
                with self.assertRaises(external.environment.EnvironmentRefused):
                    external.main()
                worker.assert_not_called()

    def test_forward_slash_absolute_worker_output_matches_same_parent_and_other_parent_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            path = out / "request-v1.json"
            for actual_out, valid in ((out.as_posix(), True), ((out / "other").as_posix(), False)):
                path.write_text(json.dumps({"out": actual_out}))
                data = (str(path) + "\n" + external.environment.digest(path) + "\n").encode()
                with patch.object(sys, "argv", ["driver", "_worker"]), \
                     patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data))), \
                     patch.object(sys, "stdout", io.StringIO()), patch.object(external, "admit"), \
                     patch.object(external, "worker") as worker:
                    if valid:
                        self.assertEqual(external.main(), 0)
                        worker.assert_called_once_with({"out": actual_out}, out)
                    else:
                        with self.assertRaises(external.ExternalRefused):
                            external.main()
                        worker.assert_not_called()

    def test_unknown_outer_cleanup_retains_owner_before_any_dependent_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "new"
            request = {key: temporary for key in external.FIELDS}
            request.update(out=str(out), case=external.CASES[0], run_id="0123456789abcdef")
            owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=False,
                         output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
            with patch.object(external, "bindings", return_value=[]), patch.object(external, "admit"), \
                 patch.object(external.driver, "source_map", return_value={}), \
                 patch.object(external.environment, "supervise", return_value=owner), \
                 patch.object(external, "validate_execution") as validate:
                with self.assertRaises(external.ExternalRefused):
                    external.supervise(request)
                validate.assert_not_called()
            self.assertEqual(json.loads((out / "owner-result-v1.json").read_bytes()), owner)
            self.assertFalse(json.loads((out / "result-v1.json").read_bytes())["passed"])
            self.assertFalse((out / "sources-after-v1.json").exists())

    def test_isolated_cli_help_is_inert(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(Path(external.__file__)), "--help"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b"")
        self.assertIn(b"--case", result.stdout)


if __name__ == "__main__":
    unittest.main()
