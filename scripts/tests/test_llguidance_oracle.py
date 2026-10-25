"""Stdlib fake-API grammar-oracle tests; never import llguidance or native code.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import redirect_stdout
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[2] / "benchmarks/llguidance_oracle.py"
SPEC = importlib.util.spec_from_file_location("llg_oracle_under_test", PATH)
o = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(o)
SCHEMA = '{"type":"object","properties":{"public":{"type":"integer"}},"required":["public"],"additionalProperties":false}'
GOOD = '{"public":1}'


def corpus():
    return {"version": 1, "scope": o.SCOPE, "cases": [{"id": "public-case", "schema_json": SCHEMA,
        "positives": [{"id": "set-1", "json": GOOD}],
        "negatives": [{"id": "malformed", "json": "{!"}, {"id": "incomplete", "json": '{"public":'}]}],
        "refusals": [{"id": "no-listener", "error": "ClarificationRequired", "provider_calls": 0, "canon_unchanged": True}]}


def encoded(value): return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class FakeMatcher:
    def __init__(self, backend, accepted):
        self.backend, self.accepted = backend, tuple(accepted)
        self.prefix = b""; self.ready = False; self.stopped = False; self.error = False
        self.reason = "NotStopped"

    def is_error(self): return self.error
    def stop_reason(self): return self.reason
    def is_stopped(self): return self.stopped

    def compute_bitmask(self):
        self.backend.events.append(("mask", len(self.prefix)))
        if self.backend.fault == "throw-mask": raise RuntimeError("PRIVATE_CANARY")
        mask = bytearray(36)
        for accepted in self.accepted:
            if accepted.startswith(self.prefix):
                token = 261 if accepted == self.prefix else accepted[len(self.prefix)]
                mask[token//8] |= 1 << (token%8)
        self.ready = True
        if self.backend.fault == "mask-error": self.error = True
        if self.backend.fault == "resource-stop": self.reason = "LexerTooComplex"
        if self.backend.fault == "wrong-mask": return b"x"
        if self.backend.fault == "eos-mismatch": mask[261//8] &= ~(1 << (261%8))
        return bytes(mask)

    def consume_token(self, token):
        if not self.ready: raise AssertionError("mask_must_precede_consume")
        self.backend.events.append(("consume", token)); self.ready = False
        if self.backend.fault == "false-consume": return False
        if token == 261:
            if self.backend.fault == "false-eos": return False
            self.stopped = self.backend.fault != "unstopped-eos"; self.reason = "EndOfSentence"
        else: self.prefix += bytes([token])
        return True

    def is_accepting(self): return self.prefix in self.accepted


class FakeBackend:
    native = False
    vocab_size = 262
    eos_token = 261

    def __init__(self, fault=None, accepted=None):
        self.fault = fault; self.events = []; self.compiles = []
        self.accepted = (GOOD.encode(),) if accepted is None else accepted

    def compile(self, schema):
        self.compiles.append(schema)
        if self.fault == "throw-compile": raise RuntimeError("PRIVATE_CANARY")
        if schema == o.UNSUPPORTED_SCHEMA: return "unsupported" if self.fault == "unsupported-accepted" else None
        if schema == o.BASIC_SCHEMA: return "basic"
        if self.fault == "case-compile": return None
        return "case"

    def matcher(self, grammar):
        if self.fault == "throw-matcher": raise ValueError("PRIVATE_CANARY")
        accepted = (b'{"x":1}',) if grammar == "basic" else self.accepted
        if self.fault == "control-reject" and grammar == "basic": accepted = (b"other",)
        return FakeMatcher(self, accepted)


class OracleTests(unittest.TestCase):
    def refuses(self, raw):
        with self.assertRaises(o.OracleFailure) as caught: o.validate_corpus(raw)
        self.assertEqual(caught.exception.reason, "corpus_invalid")
        self.assertNotIn("PRIVATE_CANARY", str(caught.exception))

    def test_module_import_has_no_file_metadata_or_native_actions(self):
        spec = importlib.util.spec_from_file_location("llg_oracle_inert", PATH)
        fresh = importlib.util.module_from_spec(spec)
        with patch.object(Path, "open", side_effect=AssertionError("unexpected_file")), \
             patch.object(o.importlib.metadata, "distribution", side_effect=AssertionError("unexpected_metadata")), \
             patch.object(o.importlib, "import_module", side_effect=AssertionError("unexpected_native")):
            spec.loader.exec_module(fresh)
        self.assertEqual(fresh.SCOPE, o.SCOPE)

    def test_exact_corpus_preserves_schema_order_and_malformed_negative_bytes(self):
        value = corpus(); value["cases"][0]["schema_json"] = '{ "enum": ["b","a"], "type":"string" }'
        self.assertEqual(o.validate_corpus(encoded(value)), value)
        self.assertEqual(o.validate_corpus(encoded(value))["cases"][0]["negatives"][0]["json"], "{!")

    def test_closed_shapes_bool_types_refusals_and_private_fields(self):
        changes = []
        for key, bad in (("version", True), ("scope", "PRIVATE_CANARY"), ("cases", []), ("refusals", {}), ("prompt", "PRIVATE_CANARY")):
            value = corpus(); value[key] = bad; changes.append(value)
        for key in corpus():
            value = corpus(); del value[key]; changes.append(value)
        for key, bad in (("schema_json", True), ("schema_json", "[]"), ("positives", []), ("negatives", None),
                ("id", "PRIVATE_CANARY"), ("private_path", "PRIVATE_CANARY")):
            value = corpus(); value["cases"][0][key] = bad; changes.append(value)
        for key, bad in (("json", True), ("json", ""), ("path", "PRIVATE_CANARY"), ("id", "../private")):
            value = corpus(); value["cases"][0]["positives"][0][key] = bad; changes.append(value)
        for key, bad in (("error", "PRIVATE_CANARY"), ("provider_calls", True), ("provider_calls", 1), ("canon_unchanged", False), ("cause", "PRIVATE_CANARY")):
            value = corpus(); value["refusals"][0][key] = bad; changes.append(value)
        for value in changes: self.refuses(encoded(value))

    def test_duplicate_ids_json_keys_nonfinite_utf8_and_nested_schema_refuse(self):
        for section in ("cases", "refusals"):
            value = corpus(); value[section].append(copy.deepcopy(value[section][0])); self.refuses(encoded(value))
        value = corpus(); value["cases"][0]["negatives"][0]["id"] = "set-1"; self.refuses(encoded(value))
        value = corpus(); value["cases"][0]["schema_json"] = '{"type":"object","type":"string"}'; self.refuses(encoded(value))
        for raw in (encoded(corpus()).replace(b'"version":1', b'"version":1,"version":1'),
                encoded(corpus()).replace(b'"version":1', b'"version":NaN'), b"\xff", b"", "notbytes"):
            self.refuses(raw)
        value = corpus(); value["cases"][0]["positives"][0]["json"] = "\ud800"; self.refuses(json.dumps(value).encode())

    def test_input_case_schema_sample_and_aggregate_caps(self):
        self.refuses(b" "*(o.MAX_INPUT+1))
        value = corpus(); value["cases"] = [dict(copy.deepcopy(value["cases"][0]), id="case-"+str(i)) for i in range(17)]; self.refuses(encoded(value))
        value = corpus(); value["cases"][0]["schema_json"] = " "*(o.MAX_TEXT+1); self.refuses(encoded(value))
        value = corpus(); value["cases"][0]["positives"][0]["json"] = "x"*(o.MAX_TEXT+1); self.refuses(encoded(value))
        value = corpus(); value["cases"][0]["positives"] = [{"id":"set-"+str(i),"json":"x"} for i in range(255)]
        self.refuses(encoded(value))
        value["cases"][0]["positives"] = value["cases"][0]["positives"][:254]
        self.assertEqual(len(o.validate_corpus(encoded(value))["cases"][0]["positives"]),254)

    def test_mask_before_every_byte_and_masked_eos_after_full_acceptance(self):
        backend = FakeBackend(); result = o.evaluate_sample(backend,"case",GOOD.encode())
        self.assertTrue(result["accepted"]); self.assertEqual(result["outcome"],"COMPLETE")
        self.assertEqual(backend.events[-2:],[("mask",len(GOOD)),("consume",261)])
        for index, event in enumerate(backend.events):
            if event[0] == "consume": self.assertEqual(backend.events[index-1][0],"mask")

    def test_illegal_byte_is_not_consumed_and_incomplete_prefix_is_not_complete(self):
        backend = FakeBackend(); result = o.evaluate_sample(backend,"case",b'{!')
        self.assertEqual(result,{"accepted":False,"outcome":"BYTE_MASK","checked_bytes":1})
        self.assertNotIn(("consume",ord("!")),backend.events)
        backend = FakeBackend(); result = o.evaluate_sample(backend,"case",b'{"public":')
        self.assertEqual(result["outcome"],"INCOMPLETE"); self.assertNotIn(("consume",261),backend.events)

    def test_utf8_sample_is_consumed_by_bytes_without_special_or_ff_calls(self):
        data = '{"text":"é🦉"}'.encode("utf-8"); backend = FakeBackend(accepted=(data,))
        result = o.evaluate_sample(backend,"case",data)
        self.assertEqual(result["checked_bytes"],len(data)); self.assertTrue(result["accepted"])
        self.assertEqual([v for k,v in backend.events if k=="consume"],list(data)+[261])
        with self.assertRaises(o.OracleFailure):o.evaluate_sample(backend,"case",b"\xff")

    def test_bad_mask_resource_error_or_false_consume_is_fatal_not_negative(self):
        for fault in ("wrong-mask","mask-error","resource-stop","false-consume","throw-mask","throw-matcher"):
            with self.subTest(fault=fault),self.assertRaises(o.OracleFailure) as caught:
                o.evaluate_sample(FakeBackend(fault),"case",GOOD.encode())
            self.assertIn(caught.exception.reason,("backend_state","backend_mask","backend_runtime"))
        for fault in ("eos-mismatch","false-eos","unstopped-eos"):
            with self.subTest(fault=fault),self.assertRaises(o.OracleFailure):o.evaluate_sample(FakeBackend(fault),"case",GOOD.encode())

    def test_static_controls_and_case_compile_errors_are_separate(self):
        for fault, expected in (("control-reject","control_acceptance"),("unsupported-accepted","unsupported_control"),
                ("case-compile","case_compile"),("throw-compile","backend_runtime")):
            with self.subTest(fault=fault),self.assertRaises(o.OracleFailure) as caught:o.run_oracle(encoded(corpus()),FakeBackend(fault))
            self.assertEqual(caught.exception.reason,expected)
        backend = FakeBackend(); report = o.run_oracle(encoded(corpus()),backend)
        self.assertEqual(backend.compiles,[o.BASIC_SCHEMA,o.UNSUPPORTED_SCHEMA,SCHEMA])
        self.assertTrue(all(report["controls"].values()))

    def test_matching_mismatch_and_privacy_metadata_only_reports(self):
        value = corpus(); value["cases"][0]["schema_json"] = '{"const":"PRIVATE_CANARY"}'
        value["cases"][0]["positives"][0]["json"] = '"PRIVATE_CANARY"'
        report = o.run_oracle(encoded(value),FakeBackend(accepted=(b'"PRIVATE_CANARY"',)))
        self.assertEqual(report["status"],"passed");self.assertFalse(report["native"])
        self.assertNotIn("PRIVATE_CANARY",json.dumps(report));self.assertNotIn("public-case",json.dumps(report))
        value["cases"][0]["negatives"][0]["json"] = '"PRIVATE_CANARY"'
        report = o.run_oracle(encoded(value),FakeBackend(accepted=(b'"PRIVATE_CANARY"',)))
        self.assertEqual(report["status"],"mismatch")
        with patch.object(o,"MAX_REPORT",1),self.assertRaises(o.OracleFailure) as caught:o.run_oracle(encoded(corpus()),FakeBackend())
        self.assertEqual(caught.exception.reason,"report_limit")

    def test_cli_validates_input_before_factory_and_never_echoes_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/"corpus.json";p.write_bytes(b"PRIVATE_CANARY")
            for argv in (["--corpus",str(p),"--module-root",directory],["--PRIVATE_CANARY","secret"]):
                output = io.StringIO()
                with redirect_stdout(output),patch.object(o.importlib,"import_module",side_effect=AssertionError("native_forbidden")), \
                     patch.object(o.importlib.metadata,"version",side_effect=AssertionError("metadata_forbidden")):
                    factory = unittest.mock.Mock(side_effect=AssertionError("factory_forbidden"))
                    self.assertEqual(o.main(argv,backend_factory=factory),2);factory.assert_not_called()
                self.assertNotIn("PRIVATE_CANARY",output.getvalue());self.assertNotIn(directory,output.getvalue())
                self.assertEqual(json.loads(output.getvalue())["status"],"failed")

    def test_cli_success_mismatch_and_private_runtime_error_have_fixed_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"corpus.json";p.write_bytes(encoded(corpus()))
            for backend, code, status in ((FakeBackend(),0,"passed"),(FakeBackend(accepted=(b"different",)),1,"mismatch"),
                    (FakeBackend("throw-mask"),2,"failed")):
                output=io.StringIO()
                with redirect_stdout(output):self.assertEqual(o.main(["--corpus",str(p),"--module-root",directory],backend_factory=lambda _:backend),code)
                self.assertEqual(json.loads(output.getvalue())["status"],status);self.assertNotIn("PRIVATE_CANARY",output.getvalue())

    def test_native_adapter_verifies_version_root_and_reserved_byte_tokenizer_without_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();events=[]
            tokenizer=SimpleNamespace(vocab_size=262,eos_token=261,decode_bytes=lambda tokens:bytes(tokens),is_special_token=lambda token:token in (255,261))
            class Matcher:
                @staticmethod
                def grammar_from_json_schema(schema):events.append("wrapper");return "bad" if schema=="bad" else "grammar"
                @staticmethod
                def validate_grammar(grammar,tok,**kwargs):events.append("validate");return "unsupported" if grammar=="bad" else ""
                def __new__(cls,*args,**kwargs):events.append(("matcher",kwargs));return object.__new__(cls)
            module=SimpleNamespace(__file__=str(root/"llguidance/__init__.py"),LLMatcher=Matcher,
                LLTokenizer=lambda name,**kwargs:events.append((name,kwargs)) or tokenizer,
                LLParserLimits=lambda **kwargs:events.append(("limits",kwargs)) or object())
            dist=SimpleNamespace(version="1.3.0",locate_file=lambda _:root)
            def imported(name):
                self.assertEqual(name,"llguidance")
                sys.modules["llguidance._lib"]=SimpleNamespace(__file__=str(root/"llguidance/_lib.pyd"));return module
            with patch.object(o.sys,"path",list(sys.path)),patch.dict(sys.modules), \
                 patch.object(o.importlib.metadata,"distribution",return_value=dist),patch.object(o.importlib.metadata,"version",return_value="1.3.0"), \
                 patch.object(o.importlib,"import_module",side_effect=imported):
                backend=o.NativeBackend(root);self.assertTrue(backend.native)
                self.assertEqual(backend.compile(SCHEMA),"grammar");backend.matcher("grammar")
                self.assertIn(("byte",{"slices":[]}),events);self.assertIn(("limits",{"verbose_errors":False}),events)
                self.assertLess(events.index("wrapper"),events.index("validate"))
                self.assertIsNone(backend.compile("bad"))

    def test_native_adapter_refuses_preloaded_or_wrong_metadata_before_native_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            with patch.dict(sys.modules,{"llguidance":SimpleNamespace()}),patch.object(o.importlib,"import_module") as imported:
                with self.assertRaises(o.OracleFailure) as caught:o.NativeBackend(root)
                self.assertEqual(caught.exception.reason,"dependency_state");imported.assert_not_called()
            with patch.object(o.sys,"path",list(sys.path)),patch.object(o.importlib.metadata,"distribution",return_value=SimpleNamespace(version="9",locate_file=lambda _:root)), \
                 patch.object(o.importlib.metadata,"version",return_value="9"),patch.object(o.importlib,"import_module") as imported:
                with self.assertRaises(o.OracleFailure) as caught:o.NativeBackend(root)
                self.assertEqual(caught.exception.reason,"dependency_version");imported.assert_not_called()


if __name__ == "__main__": unittest.main()
