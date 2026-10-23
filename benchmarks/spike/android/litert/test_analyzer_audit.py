"""Analyzer false-green regression cases; actual probe evidence is separate."""

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build


class AnalyzerAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.project = self.root / "experiment"
        self.reports = self.project / "app/build/reports"
        self.reports.mkdir(parents=True)
        self.model = self.project / "app/build/model"
        self.model.mkdir()
        self.expected = {"analyzer_version": "32.4.1", "artifacts": [{"coordinate": "synthetic:analyzer:32.4.1", "sha256": "synthetic"}]}
        manifest = self.root / build.ANALYZER_LOCK
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(self.expected))
        self.actual = dict(self.expected, version=1, check_dependencies=True,
                           model_directory="build/model", analysis_did_work=True)
        self.write_actual()
        self.dependencies = self.model / "debug-artifact-dependencies.xml"
        self.dependencies.write_text('<dependencies><dependency name="com.google.ai.edge.litertlm:litertlm-android:0.18.1@aar"/><dependency name="org.jetbrains.kotlin:kotlin-reflect:2.4.0@jar"/><dependency name="org.jetbrains.kotlin:kotlin-stdlib:2.4.0@jar"/></dependencies>')
        (self.reports / "lint-results-debug.xml").write_text('<issues format="6"/>')
        self.addCleanup(patch.stopall)
        patch.object(build, "ROOT", self.root).start()
        patch.object(build, "PROJECT", self.project).start()

    def write_actual(self):
        (self.reports / "analyzer-audit.json").write_text(json.dumps(self.actual))

    def test_verified_dependency_model_and_analyzer_accepts_clean_report(self):
        with patch("sys.stdout", new=io.StringIO()):
            build.analyzer_audit("BUILD SUCCESSFUL\n")

    def test_zero_lint_issues_does_not_override_kotlin_metadata_diagnostic(self):
        with self.assertRaisesRegex(ValueError, "incompatible dependency"):
            build.analyzer_audit("e: SDK was compiled with an incompatible version of Kotlin.\n0 errors, 0 warnings\nBUILD SUCCESSFUL")

    def test_other_kotlin_analysis_error_cannot_pass(self):
        with self.assertRaisesRegex(ValueError, "incompatible dependency"):
            build.analyzer_audit("e: unexpected Kotlin analysis failure\nBUILD SUCCESSFUL")

    def test_different_analyzer_artifact_hash_or_version_is_rejected(self):
        for key, value in (("analyzer_version", "31.10.1"), ("artifacts", [{"sha256": "changed"}])):
            original = self.actual[key]
            self.actual[key] = value; self.write_actual()
            with self.assertRaisesRegex(ValueError, "pinned audit"):
                build.analyzer_audit("")
            self.actual[key] = original

    def test_incomplete_dependency_analysis_cannot_pass(self):
        self.actual["check_dependencies"] = False; self.write_actual()
        with self.assertRaisesRegex(ValueError, "dependency analysis"):
            build.analyzer_audit("")

    def test_missing_sdk_in_analyzed_model_is_rejected(self):
        self.dependencies.write_text('<dependencies/>')
        with self.assertRaisesRegex(ValueError, "exact SDK"):
            build.analyzer_audit("")

    def test_lint_error_is_rejected_even_with_successful_gradle(self):
        (self.reports / "lint-results-debug.xml").write_text('<issues><issue severity="Error"/></issues>')
        with self.assertRaisesRegex(ValueError, "Lint reported an error"):
            build.analyzer_audit("BUILD SUCCESSFUL")

    def test_model_path_cannot_escape_experiment_output(self):
        self.actual["model_directory"] = "../../outside"
        self.write_actual()
        with self.assertRaisesRegex(ValueError, "outside"):
            build.analyzer_audit("")


if __name__ == "__main__":
    unittest.main()
