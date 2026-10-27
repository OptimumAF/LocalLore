"""Original synthetic current/historical evidence; never SDK or lifecycle execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import android_external_controller as external
from scripts.tests import test_android_external_controller as fixtures
from scripts.tests import test_android_process_controller_evidence as controller


def publish_record(fixture):
    (fixture.out / "external-v1.json").write_bytes(controller.encoded(fixture.record))


def replace_client(fixture, label, raw):
    """Rebind only the one synthetic original client, retaining real validation."""
    matches = []
    for path in sorted((fixture.out / "clients").glob("command-*.json")):
        row = json.loads(path.read_bytes())
        if row["label"] == label:
            matches.append((path, row))
    if len(matches) != 1:
        raise AssertionError("synthetic_client_identity")
    path, row = matches[0]
    path.with_suffix(".stdout.bin").write_bytes(raw)
    row.update(stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest())
    path.write_bytes(controller.encoded(row))


def rebind_proof(fixture, proof):
    raw = controller.frame(proof)
    (fixture.out / "controller.stdout.raw").write_bytes(raw)
    (fixture.out / "proof-v1.json").write_bytes(controller.encoded(proof))
    replace_client(fixture, "controller", raw)
    fixture.record["controller"] = external.environment.binding(fixture.out / "controller.stdout.raw")
    fixture.record["proof"] = external.environment.binding(fixture.out / "proof-v1.json")
    fixture.proof = proof
    publish_record(fixture)


def rebind_product(fixture, leaf, value):
    raw = controller.encoded(value)
    path = fixture.out / (leaf + ".raw")
    path.write_bytes(raw)
    replace_client(fixture, "read-" + leaf, raw)
    fixture.record["records"][leaf] = external.environment.binding(path)
    publish_record(fixture)


def upgrade(fixture):
    proof = copy.deepcopy(fixture.proof)
    proof.update(version=2, scope="locallore_process_controller_v2")
    for index, terminal in enumerate(proof["terminal_observations"]):
        counts = dict(create=0, create_named=2 if index == 0 else 0)
        terminal["saved_creation"] = dict(counts)
        terminal["commands_creation"] = dict(counts)
    rebind_proof(fixture, proof)
    # Explicit synthetic current-client diagnostics, not measured SDK timings.
    # Historical fixtures which do not call upgrade() remain exact v1 rows.
    for path in (fixture.out / "clients").glob("command-*.json"):
        row = json.loads(path.read_bytes())
        row.update(version=2, elapsed_ms=7, effective_deadline_ms=15000)
        path.write_bytes(controller.encoded(row))
    return fixture


class CurrentCreationExecutionTests(unittest.TestCase):
    def validate(self, fixture, current=True):
        # Same boundary mocks as DeepExecutionTests. Controller/product,
        # retirement transports, canonical sidecars and client validators run.
        with patch.object(external, "admit"), patch.object(external.driver, "qualified_build", return_value={}), \
             patch.object(external, "qualified_gate", return_value=fixture.gate), \
             patch.object(external, "expected_pins", return_value=fixture.expected):
            validator = external.validate_current_execution if current else external.validate_execution
            return validator(fixture.request, fixture.out)

    def test_all_four_historical_v1_sets_stay_readable_but_cannot_qualify_current(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                fixture = fixtures.deep_fixture(Path(temporary), case, record_version=2)
                self.assertEqual(fixture.proof["version"], 1)
                self.assertEqual(self.validate(fixture, current=False), fixture.record)
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_all_four_fully_rebound_v2_sets_pass_current_real_deep_validation(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                fixture = upgrade(fixtures.deep_fixture(Path(temporary), case, record_version=2))
                self.assertLessEqual(len(controller.frame(fixture.proof)), 4160)
                self.assertLessEqual(len(controller.encoded(fixture.proof)), 4096)
                self.assertEqual(self.validate(fixture, current=False), fixture.record)
                self.assertEqual(self.validate(fixture), fixture.record)

    def test_stale_raw_proof_client_copy_or_metadata_cannot_borrow_v2_summary(self):
        for kind in ("raw", "proof", "client_copy", "client_metadata"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                fixture = upgrade(fixtures.deep_fixture(Path(temporary), external.CASES[0]))
                self.assertEqual(self.validate(fixture), fixture.record)
                if kind == "raw":
                    (fixture.out / "controller.stdout.raw").write_bytes(b"stale")
                elif kind == "proof":
                    proof = copy.deepcopy(fixture.proof)
                    proof["version"] = 1
                    (fixture.out / "proof-v1.json").write_bytes(controller.encoded(proof))
                else:
                    path = fixture.out / "clients/command-0001.json"
                    self.assertEqual(json.loads(path.read_bytes())["label"], "controller")
                    if kind == "client_copy":
                        path.with_suffix(".stdout.bin").write_bytes(b"stale")
                    else:
                        row = json.loads(path.read_bytes())
                        row["stdout_sha256"] = "f" * 64
                        path.write_bytes(controller.encoded(row))
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_fully_rebound_missing_malformed_or_aliased_creation_maps_refuse(self):
        variants = (None, {}, {"create": 0}, {"create": False, "create_named": 2},
                    {"create": 0, "create_named": 2.0}, {"create": -1, "create_named": 2},
                    {"create": 0, "create_named": 4097}, {"create": 2, "create_named": 0},
                    {"create": 0, "create_named": 2, "private_extra": "synthetic_canary"})
        for terminal_index in (0, 1):
            for channel in ("saved_creation", "commands_creation"):
                for replacement in variants:
                    with self.subTest(terminal=terminal_index, channel=channel, replacement=replacement), \
                         tempfile.TemporaryDirectory() as temporary:
                        fixture = upgrade(fixtures.deep_fixture(Path(temporary), external.CASES[0]))
                        proof = copy.deepcopy(fixture.proof)
                        if replacement is None:
                            del proof["terminal_observations"][terminal_index][channel]
                        else:
                            proof["terminal_observations"][terminal_index][channel] = copy.deepcopy(replacement)
                        rebind_proof(fixture, proof)
                        with self.assertRaises(RuntimeError):
                            self.validate(fixture)

    def test_fully_rebound_saved_commands_disagreement_and_second_process_creation_refuse(self):
        for terminal_index, channel, counts in ((0, "commands_creation", dict(create=0, create_named=1)),
                                                (0, "saved_creation", dict(create=1, create_named=2)),
                                                (1, "commands_creation", dict(create=0, create_named=1)),
                                                (1, "saved_creation", dict(create=1, create_named=0))):
            with self.subTest(terminal=terminal_index, channel=channel), tempfile.TemporaryDirectory() as temporary:
                fixture = upgrade(fixtures.deep_fixture(Path(temporary), external.CASES[0]))
                proof = copy.deepcopy(fixture.proof)
                proof["terminal_observations"][terminal_index][channel] = counts
                rebind_proof(fixture, proof)
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_current_v2_cannot_downgrade_all_or_one_product_record_to_v1(self):
        for leaves in (("created", "saved", "commands"), ("created",), ("saved",), ("commands",)):
            with self.subTest(leaves=leaves), tempfile.TemporaryDirectory() as temporary:
                fixture = upgrade(fixtures.deep_fixture(Path(temporary), external.CASES[0]))
                for leaf in leaves:
                    value = json.loads((fixture.out / (leaf + ".raw")).read_bytes())
                    value.update(version=1, scope="locallore_process_verify_v1")
                    del value["operations"]["story_template"]
                    del value["operations"]["create_named"]
                    rebind_product(fixture, leaf, value)
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_rebound_new_process_creation_attempts_refuse_without_canonical_inference(self):
        for leaf, operation in (("created", "create"), ("created", "create_named"),
                                ("commands", "create_named"),
                                ("saved", "create_named")):
            with self.subTest(leaf=leaf, operation=operation), tempfile.TemporaryDirectory() as temporary:
                fixture = upgrade(fixtures.deep_fixture(Path(temporary), external.CASES[0]))
                value = json.loads((fixture.out / (leaf + ".raw")).read_bytes())
                value["operations"][operation] = 1
                rebind_product(fixture, leaf, value)
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_read_only_preview_counter_is_not_aliased_to_creation_or_gameplay(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = upgrade(fixtures.deep_fixture(Path(temporary), external.CASES[0]))
            value = json.loads((fixture.out / "commands.raw").read_bytes())
            value["operations"]["story_template"] = 1
            rebind_product(fixture, "commands", value)
            self.assertEqual(self.validate(fixture), fixture.record)
            # Ordinary monotonic counter consistency still applies. A preview
            # observation cannot disappear between created and commands.
            earlier = json.loads((fixture.out / "created.raw").read_bytes())
            earlier["operations"]["story_template"] = 2
            rebind_product(fixture, "created", earlier)
            with self.assertRaises(RuntimeError):
                self.validate(fixture)

    def test_current_version_scope_pair_and_fixed_case_still_refuse_when_fully_rebound(self):
        for changes in ({"version": True}, {"version": 2.0}, {"scope": "locallore_process_controller_v1"},
                        {"case": "synthetic_foreign_case"}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as temporary:
                fixture = upgrade(fixtures.deep_fixture(Path(temporary), external.CASES[0]))
                proof = copy.deepcopy(fixture.proof)
                proof.update(changes)
                rebind_proof(fixture, proof)
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_source_only_fixed_worker_and_parent_use_current_guard_after_closed_decoder(self):
        # Static wiring evidence only: not a worker, SDK or process-death run.
        tree = ast.parse(Path(external.__file__).read_text(encoding="utf-8"))
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}

        def calls(function, name):
            return sorted((node for node in ast.walk(function) if isinstance(node, ast.Call)
                           and ((isinstance(node.func, ast.Name) and node.func.id == name)
                                or (isinstance(node.func, ast.Attribute) and node.func.attr == name))),
                          key=lambda node: (node.lineno, node.col_offset))

        wrapper = functions["validate_current_execution"]
        self.assertEqual([a.arg for a in wrapper.args.args], ["request", "out"])
        self.assertIsNone(wrapper.args.vararg)
        self.assertIsNone(wrapper.args.kwarg)
        self.assertEqual(wrapper.args.defaults, [])
        historical = calls(wrapper, "validate_execution")
        bound = calls(wrapper, "bound_json")
        guard = calls(wrapper, "_require_current_proof")
        self.assertEqual((len(historical), len(bound), len(guard)), (1, 1, 1))
        self.assertLess(historical[0].lineno, bound[0].lineno)
        self.assertLess(bound[0].lineno, guard[0].lineno)
        parent = functions["supervise"]
        self.assertEqual(len(calls(parent, "validate_current_execution")), 1)
        self.assertEqual(calls(parent, "validate_execution"), [])
        worker = functions["worker"]
        decoded = calls(worker, "validate_controller_result")
        guarded = calls(worker, "_require_current_proof")
        self.assertEqual((len(decoded), len(guarded)), (1, 1))
        proof_writes = [node for node in calls(worker, "create_json")
                        if any(isinstance(part, ast.Constant) and part.value == "proof-v1.json"
                               for part in ast.walk(node.args[0]))]
        self.assertEqual(len(proof_writes), 1)
        self.assertLess(decoded[0].lineno, guarded[0].lineno)
        self.assertLess(guarded[0].lineno, proof_writes[0].lineno)


if __name__ == "__main__":
    unittest.main()
