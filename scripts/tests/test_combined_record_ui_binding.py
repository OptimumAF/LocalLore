"""Synthetic adversaries for the fixed Record UI cohort and its APK receipts."""
import copy
import hashlib
import json
from pathlib import PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import combined_record_ui_binding as binding
from benchmarks import owned_target_contract as core


APP = "org.locallore.app.archiveverify"
TEST = APP + ".test"
RUNNER = TEST + "/androidx.test.runner.AndroidJUnitRunner"
SIGNER = "17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564"
APP_RECEIPT = {
    "bytes": 28012684,
    "sha256": "4554f954c61113c51da1585328ca5001a74ec905814574eabf96cff39b8d419e",
}
TEST_RECEIPT = {
    "bytes": 2321874,
    "sha256": "0fd3f9eb264f9a1229efbe5516f9173ae7c122463ba4590b31bc8709fba6e56a",
}
CANARY = "PRIVATE_fixture_9374"

_METHOD_GROUPS = (
    ("StoryRecordCancellationScreenTest", (
        "cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor",
        "cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens",
        "obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords",
        "oldDetailCancellationAfterBackCannotFinishTheReplacementDetail",
        "disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks",
    )),
    ("ui.StoryRecordActionScopeScreenTest", (
        "retainedSearchNextAndCloseCannotRetargetAnotherStoryOrBranchAndFreshControlsStillWork",
        "equalValuedReopenAndLaterPagesRejectOldButtonsWithoutResettingTheCurrentDialogue",
        "retainedListAndEventRetryBackAndSourceActionsCannotAffectFreshDetailsOrReopenedRecords",
    )),
    ("StoryRecordLargeTextTest", ("narrowRecordReflowsAtDoubleTextSizeAndKeepsActionsReachable",)),
    ("StoryRecordPageScrollTest", (
        "nextAndFirstStartAtTheTopOfTheirRenderedPage",
        "changingSectionAppliedSearchOrContextStartsAtTheTop",
        "openingAnEventAndGoingBackRestoresTheSamePageOffset",
    )),
)
SELECTORS = tuple(("org.locallore.app." + klass, method)
                  for klass, methods in _METHOD_GROUPS for method in methods)


def _stdout(klass, method, end_code=0):
    statuses = "".join(
        f"INSTRUMENTATION_STATUS: class={klass}\n"
        f"INSTRUMENTATION_STATUS: test={method}\n"
        "INSTRUMENTATION_STATUS: current=1\n"
        "INSTRUMENTATION_STATUS: numtests=1\n"
        f"INSTRUMENTATION_STATUS_CODE: {code}\n"
        for code in (1, end_code)
    )
    return (statuses + "INSTRUMENTATION_RESULT: stream=\n\nTime: 0.01\n\nOK (1 test)\n\n"
            "INSTRUMENTATION_CODE: -1\n").encode("utf-8")


class CombinedRecordUiBindingTests(unittest.TestCase):
    def setUp(self):
        self.pins = binding.artifact_bindings()
        self.audit = {
            "status": "passed",
            "package": APP,
            "test_package": TEST,
            "test_permissions": ["android.permission.REORDER_TASKS"],
            "certificate_sha256": SIGNER,
            "app": dict(APP_RECEIPT),
            "test": dict(TEST_RECEIPT),
        }
        self.summary = {
            "tests": 442,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "suites": 53,
            "cancellation_jvm": [
                "currentPageCancellationAndExactCursorRetryKeepTheAcceptedShellUnchanged",
                "obsoleteCancellationAfterCloseAndDisposalCannotFinishOrReviveAnotherRead",
                "scopedDetailCancellationAndRetryKeepTheCurrentChildLensAndOriginalEventTuple",
            ],
            "qualified_selectors": [klass + "#" + method for klass, method in SELECTORS],
            "lint": [
                {"id": "GradleDependency", "severity": "Warning"},
                {"id": "AutoboxingStateCreation", "severity": "Hint"},
            ],
        }

    def reader(self, *, audit=None, summary=None):
        records = {
            "audit-pair-25ab2e9a-v1.log": self.audit if audit is None else audit,
            "host-verification-25ab2e9a-v1.json": self.summary if summary is None else summary,
        }

        def read(pin, *, cap):
            self.assertEqual(cap, pin["bytes"])
            filename = PureWindowsPath(pin["path"]).name
            if filename in records:
                record = records[filename]
                return record if type(record) is bytes else json.dumps(record).encode("utf-8")
            self.assertIn(pin, (self.pins["product_apk"], self.pins["test_apk"]))
            return b"synthetic APK body"

        return patch.object(binding.files, "_bound", side_effect=read)

    def test_approved_roles_and_receipts_are_read_with_exact_byte_caps(self):
        self.assertEqual(set(self.pins), {"build", "product_apk", "test_apk"})
        with self.reader() as read:
            self.assertIsNone(binding.verify_artifacts(self.pins))
        reads = [PureWindowsPath(call.args[0]["path"]).name for call in read.call_args_list]
        self.assertCountEqual(reads, ["audit-pair-25ab2e9a-v1.log", "host-verification-25ab2e9a-v1.json",
                                     "app-debug.apk", "app-debug-androidTest.apk"])

    def test_caller_edits_cannot_change_the_fixed_nested_pins(self):
        received = binding.artifact_bindings()
        received["build"]["path"] = CANARY
        received["product_apk"].clear()
        received.pop("test_apk")
        self.assertEqual(binding.artifact_bindings(), self.pins)

    def test_changed_roles_paths_hashes_and_numeric_aliases_refuse_before_reads(self):
        variants = []
        for key, value in (("path", CANARY), ("sha256", "0" * 64),
                           ("bytes", float(self.pins["build"]["bytes"]))):
            changed = copy.deepcopy(self.pins)
            changed["build"][key] = value
            variants.append(changed)
        variants += [dict(self.pins, unknown=self.pins["build"]),
                     dict(self.pins, product_apk=self.pins["test_apk"]),
                     {key: value for key, value in self.pins.items() if key != "build"},
                     list(self.pins.items())]
        with patch.object(binding.files, "_bound") as read:
            for index, candidate in enumerate(variants):
                with self.subTest(variant=index), self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                    binding.verify_artifacts(candidate)
            read.assert_not_called()

    def test_audit_must_join_packages_signer_permissions_and_both_apk_receipts(self):
        for key, value in (
            ("status", "failed"), ("package", "org.locallore.app"), ("test_package", "org.locallore.app.test"),
            ("certificate_sha256", "0" * 64), ("test_permissions", ["android.permission.INTERNET"]),
            ("app", TEST_RECEIPT), ("test", dict(TEST_RECEIPT, bytes=float(TEST_RECEIPT["bytes"]))),
        ):
            with self.subTest(field=key), self.reader(audit=dict(self.audit, **{key: value})), \
                    self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                binding.verify_artifacts(self.pins)

    def test_host_receipt_must_report_exact_ordered_roster_and_qualified_counts(self):
        selectors = self.summary["qualified_selectors"]
        for key, value in (
            ("tests", 441), ("suites", 52), ("failures", 1), ("errors", 1), ("skipped", False),
            ("qualified_selectors", selectors[:-1]), ("qualified_selectors", selectors[::-1]),
            ("qualified_selectors", selectors[:-1] + selectors[:1]),
        ):
            with self.subTest(field=key), self.reader(summary=dict(self.summary, **{key: value})), \
                    self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                binding.verify_artifacts(self.pins)

    def test_strict_json_refuses_duplicate_keys_malformed_bytes_and_nonfinite_values(self):
        duplicate = json.dumps(self.audit).encode("utf-8").replace(b"{", b'{"status":"passed",', 1)
        for variant in (duplicate, b"\xff", b'{"status":NaN}'):
            with self.subTest(variant=variant), self.reader(audit=variant), \
                    self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                binding.verify_artifacts(self.pins)

    def test_file_reader_failure_is_reported_without_private_context(self):
        with patch.object(binding.files, "_bound", side_effect=OSError(CANARY)), \
                self.assertRaisesRegex(core.TargetRefused, "^binding$"):
            binding.verify_artifacts(self.pins)

    def test_all_twelve_ordered_selectors_return_exact_fresh_shell_argv(self):
        self.assertEqual(tuple((klass, method) for _, klass, method in binding.INSTRUMENTATIONS), SELECTORS)
        self.assertEqual(len({kind for kind, _, _ in binding.INSTRUMENTATIONS}), 12)
        for kind, klass, method in binding.INSTRUMENTATIONS:
            with self.subTest(kind=kind):
                expected = ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method, RUNNER]
                actual = binding.instrumentation_argv(kind)
                self.assertEqual(actual, expected)
                actual.append(CANARY)
                self.assertEqual(binding.instrumentation_argv(kind), expected)

    def test_unlisted_kind_cannot_supply_a_selector_or_choose_a_result_parser(self):
        klass, method = SELECTORS[0]
        for kind in (CANARY, klass + "#" + method, None, False, [CANARY]):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.instrumentation_argv(kind)
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.validate_result(kind, _stdout(klass, method))

    def test_complete_result_for_each_kind_is_attributed_to_that_exact_method(self):
        for kind, klass, method in binding.INSTRUMENTATIONS:
            raw = _stdout(klass, method)
            with self.subTest(kind=kind):
                self.assertEqual(binding.validate_result(kind, raw), {
                    "class": klass, "methods": [method], "method_count": 1,
                    "stdout_sha256": hashlib.sha256(raw).hexdigest(), "passed": True,
                })

    def test_truncated_forged_skipped_and_other_selected_results_are_refused(self):
        kind, klass, method = binding.INSTRUMENTATIONS[0]
        other_klass, other_method = SELECTORS[1]
        correct = _stdout(klass, method)
        forged = correct[correct.index(b"INSTRUMENTATION_RESULT:"):]
        for raw in (correct[:-3], forged, _stdout(klass, method, end_code=-3),
                    _stdout(other_klass, other_method), _stdout(CANARY, method)):
            with self.subTest(raw=raw), self.assertRaisesRegex(evidence.EvidenceRefused, "^instrumentation_refused$"):
                binding.validate_result(kind, raw)


if __name__ == "__main__":
    unittest.main()
