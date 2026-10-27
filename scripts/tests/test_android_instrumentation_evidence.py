"""Original synthetic runner/source adversaries; no ADB or runtime/device calls."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import android_instrumentation_evidence as evidence

CLASS = "org.locallore.app.OriginalEvidenceTest"
METHODS = ["firstOriginal", "secondOriginal"]
CANARY = "PRIVATE_path_story_UID_token_9374"


def bundle(method, ordinal, code, *, cls=CLASS, count=2, metadata=True, extra=(), stream=""):
    fields = [("class", cls), ("test", method)]
    if metadata:
        fields += [("current", str(ordinal)), ("numtests", str(count)), ("id", "AndroidJUnitRunner")]
    fields += [("stream", stream)] + list(extra)
    return "\n".join("INSTRUMENTATION_STATUS: " + key + "=" + value for key, value in fields) + \
        "\nINSTRUMENTATION_STATUS_CODE: " + str(code) + "\n"


def ending(count=2):
    noun = "test" if count == 1 else "tests"
    return f"INSTRUMENTATION_RESULT: stream=\n\nTime: 1.234\n\nOK ({count} {noun})\n\nINSTRUMENTATION_CODE: -1\n"


def run(methods=METHODS, *, metadata=True):
    return ("".join(bundle(method, i, 1, count=len(methods), metadata=metadata,
                           stream="\n" + CLASS + ":") +
                    bundle(method, i, 0, count=len(methods), metadata=metadata, stream=".")
                    for i, method in enumerate(methods, 1)) + ending(len(methods))).encode()


class InstrumentationEvidenceTests(unittest.TestCase):
    def parse(self, raw, methods=METHODS, cls=CLASS):
        return evidence.validate_instrumentation(raw, cls, list(methods))

    def refused(self, raw, **kwargs):
        with self.assertRaises(evidence.EvidenceRefused) as raised:
            self.parse(raw, **kwargs)
        self.assertEqual(str(raised.exception), "instrumentation_refused")
        self.assertNotIn(CANARY, str(raised.exception))

    def test_standard_android_runner_bundles_and_exact_public_shape(self):
        raw = run()
        result = self.parse(raw)
        self.assertEqual(result, {"class": CLASS, "methods": METHODS, "method_count": 2,
            "stdout_sha256": hashlib.sha256(raw).hexdigest(), "passed": True})

    def test_crlf_blank_framing_preserves_original_hash(self):
        raw = run().replace(b"\n", b"\r\n\r\n")
        self.assertEqual(self.parse(raw)["stdout_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(self.parse(raw)["stdout_sha256"], self.parse(run())["stdout_sha256"])

    def test_single_test_and_optional_metadata_are_supported(self):
        result = self.parse(run(METHODS[:1], metadata=False), methods=METHODS[:1])
        self.assertEqual(result["method_count"], 1)

    def test_runner_order_can_differ_from_source_roster(self):
        self.assertEqual(self.parse(run(METHODS[::-1]))["methods"], METHODS)

    def test_result_does_not_alias_or_mutate_caller_roster(self):
        methods = list(METHODS)
        result = evidence.validate_instrumentation(run(), CLASS, methods)
        result["methods"].clear()
        self.assertEqual(methods, METHODS)

    def test_wrong_class_in_either_half_of_pair_refuses(self):
        for count in (1, 2):
            with self.subTest(count=count):
                self.refused(run().replace(CLASS.encode(), ("private." + CANARY).encode(), count))

    def test_duplicate_method_cannot_replace_missing_method(self):
        self.refused(run([METHODS[0], METHODS[0]]))

    def test_pass_without_start_or_start_without_pass_refuses(self):
        self.refused((bundle(METHODS[0], 1, 0, count=1) + ending(1)).encode(), methods=METHODS[:1])
        self.refused((bundle(METHODS[0], 1, 1, count=1) + ending(1)).encode(), methods=METHODS[:1])

    def test_crossed_or_overlapping_method_pairs_refuse(self):
        self.refused((bundle(METHODS[0], 1, 1) + bundle(METHODS[1], 1, 0) + ending()).encode())
        self.refused((bundle(METHODS[0], 1, 1) + bundle(METHODS[1], 1, 1) + ending()).encode())

    def test_unknown_method_and_mixed_class_rosters_refuse(self):
        self.refused(run().replace(METHODS[1].encode(), CANARY.encode()))
        self.refused(run().replace(CLASS.encode(), b"org.locallore.app.OtherTest", 1))

    def test_skip_failure_error_and_unknown_statuses_cannot_pass_forged_ok(self):
        for code in (b"-1", b"-2", b"-3", b"-4", b"2", b"00", b"0 "):
            with self.subTest(code=code):
                self.refused(run().replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: " + code, 1))

    def test_duplicate_or_unknown_status_keys_refuse(self):
        for field in ("test=" + METHODS[0], "class=" + CLASS, "current=1", "stream=.", "private=" + CANARY):
            with self.subTest(field=field):
                self.refused(run().replace(b"INSTRUMENTATION_STATUS_CODE: 1", ("INSTRUMENTATION_STATUS: " + field +
                    "\nINSTRUMENTATION_STATUS_CODE: 1").encode(), 1))

    def test_stack_even_with_pass_and_multiline_stack_cannot_claim_success(self):
        extra = (("stack", "java.lang.AssertionError: " + CANARY + "\n at synthetic.Test.run(Test.kt:1)"),)
        self.refused((bundle(METHODS[0], 1, 1, count=1) +
            bundle(METHODS[0], 1, 0, count=1, extra=extra) + ending(1)).encode(), methods=METHODS[:1])

    def test_current_numtests_and_runner_id_must_be_consistent(self):
        for old, new in ((b"current=1", b"current=2"), (b"current=2", b"current=1"),
                         (b"current=1", b"current=01"), (b"numtests=2", b"numtests=1"),
                         (b"numtests=2", b"numtests=True"), (b"id=AndroidJUnitRunner", b"id=Other")):
            with self.subTest(new=new):
                self.refused(run().replace(old, new, 1))

    def test_misleading_ok_in_status_stream_is_not_final_summary(self):
        raw = (bundle(METHODS[0], 1, 1, count=1, stream="\nTime: 1\nOK (1 test)") +
            bundle(METHODS[0], 1, 0, count=1)).encode()
        self.refused(raw, methods=METHODS[:1])
        for forged in (b"FAILURES!!! OK (2 tests)", b"prefix OK (2 tests)", b"OK (2 tests) suffix"):
            self.refused(run().replace(b"OK (2 tests)", forged))

    def test_duplicate_terminal_result_or_footer_refuses(self):
        self.refused(run() + ending().encode())
        self.refused(run() + b"INSTRUMENTATION_CODE: -1\n")
        self.refused(run().replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_RESULT: stream=\nINSTRUMENTATION_CODE: -1"))

    def test_shortmsg_abort_unknown_trailing_and_post_final_status_refuse(self):
        for tail in (b"unknown trailing " + CANARY.encode() + b"\n", b"INSTRUMENTATION_FAILED: aborted\n",
                     b"INSTRUMENTATION_RESULT: shortMsg=Process crashed.\n", bundle(METHODS[0], 1, 1).encode()):
            self.refused(run() + tail)
        self.refused(run().replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_RESULT: shortMsg=crashed\nINSTRUMENTATION_CODE: -1"))

    def test_early_or_incomplete_terminal_and_wrong_summary_count_refuse(self):
        self.refused(ending().encode())
        self.refused(run()[:-1])
        self.refused(run().replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: 0"))
        self.refused(run().replace(b"OK (2 tests)", b"OK (1 test)"))
        self.refused(run().replace(b"Time: 1.234", b"Time: NaN"))

    def test_input_bounds_types_utf8_and_framing_refuse_without_private_echo(self):
        for raw in (b"", b"x" * (evidence.MAX_BYTES + 1), b"\xff\n", b"\x00\n", run().replace(b"Time:", b"\vTime:"),
                    run().replace(b"Time:", b"\fTime:"), run().replace(b"Time:", b"\rTime:")):
            self.refused(raw)
        for methods in ([], ["x", "x"], [True], [CANARY + "\n"], tuple(METHODS)):
            with self.assertRaises(evidence.EvidenceRefused):
                evidence.validate_instrumentation(run(), CLASS, methods)
        for cls in ("", True, CANARY + "\n", "org." + "x" * 256):
            with self.assertRaises(evidence.EvidenceRefused):
                evidence.validate_instrumentation(run(), cls, list(METHODS))


class SourceRosterTests(unittest.TestCase):
    def roster(self, content):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "OriginalTest.kt"
            source.write_bytes(content if isinstance(content, bytes) else content.encode())
            return evidence.test_roster(source)

    def test_actual_repository_declaration_style_and_source_order(self):
        self.assertEqual(self.roster("""package original
            @Test fun secondOriginal(): Unit = runBlocking { }
            @org.junit.Test
            public fun firstOriginal() { }
        """), METHODS[::-1])

    def test_comments_nested_comments_strings_raw_strings_and_chars_are_not_tests(self):
        self.assertEqual(self.roster('''
            // @Test fun falseLine() {}
            /* outer /* @Test fun falseNested() {} */ comment */
            val quoted = "@Test fun falseString() {}"
            val raw = """@Test fun falseRaw() {}"""
            val character = '\\''
            @Test /* comment */ fun firstOriginal() { val text = "\\\"" }
        '''), METHODS[:1])

    def test_annotation_arguments_and_multiline_declaration(self):
        self.assertEqual(self.roster("@Test(timeout = 1_000)\nfun\nfirstOriginal(\n) {}"), METHODS[:1])

    def test_intervening_android_annotation_is_roster_metadata_not_skip_credit(self):
        self.assertEqual(self.roster("@Test @SdkSuppress(minSdkVersion = 29)\nfun firstOriginal() {}"), METHODS[:1])

    def test_current_app_source_rosters_include_all_declared_plain_junit_methods(self):
        source = Path(__file__).resolve().parents[2] / "apps/android/app/src/androidTest/java/org/locallore/app"
        expected = {
            "RetainedParentFallbackNativeTest": ["parentRetirementFallsBackOnceAndPreservesOriginalGrandchildReceipts",
                "cachedParentReadyIsClosedWhileRetainedChildReadyCommitsExactlyOnce"],
            "RetainedParentFixtureInstrumentedTest": ["loadModeFindsRetainedParentWorkerWithoutOpeningWorkspace",
                "wrongUidOrFixedRetainedArgumentsRefuseBeforeNativeAccess", "wrongApkHashRefusesRetainedParentWorkerBeforeNativeAccess",
                "alternateNativeDirectoryCannotReplaceRetainedParentApkPath"],
            "BranchForkNativeIntegrationTest": ["sameOwnerNativeForkThenReopenLookupPreservesOriginalAndNeverCreatesMissing",
                "registrationCancellationConsentAndClosedOwnerAreActualNativeFences"],
            "DiagnosticWriterTest": ["actualContentResolverWritesExactFrozenBytesTruncatesAndCloses",
                "invalidSchemesAndOversizedPayloadsAreRejectedBeforeProviderAccess", "exactMaximumByteCountIsAccepted",
                "providerErrorsAndNullDescriptorsFailWithoutLeakingOwnedResources", "outputFailureStillClosesTheOpenedDescriptor",
                "mainDispatcherRemainsResponsiveWhileRemoteOpenIsPendingAndCancellationReleasesIt",
                "repeatedWritesDoNotLeaveDescriptorsOwnedByTheWriter",
                "synchronousLocalCancellationListenerRunsOffMainAndHoldsTheSingleExportSlot"],
        }
        for name, methods in expected.items():
            with self.subTest(name=name):
                self.assertEqual(evidence.test_roster(source / (name + ".kt")), methods)

    def test_empty_duplicate_and_unsupported_declarations_refuse(self):
        for source in ("// @Test fun fake() {}", "@Test fun repeated() {}\n@Test fun repeated() {}",
                       "@Test fun `display name`() {}", "@Test val notFunction = 1", "@Test fun argument(x: Int) {}",
                       "@Test(", 'val raw = """unterminated', "/* unterminated", 'val x = "unterminated'):
            with self.subTest(source=source), self.assertRaises(evidence.EvidenceRefused) as raised:
                self.roster(source)
            self.assertEqual(str(raised.exception), "roster_refused")

    def test_source_bounds_bad_encoding_missing_path_and_method_count(self):
        for source in (b"\xff", b"\x00", b"x" * (evidence.MAX_SOURCE_BYTES + 1),
                       "\n".join(f"@Test fun method{i}() {{}}" for i in range(evidence.MAX_METHODS + 1))):
            with self.assertRaises(evidence.EvidenceRefused):
                self.roster(source)
        with self.assertRaises(evidence.EvidenceRefused) as raised:
            evidence.test_roster(Path(CANARY) / "missing.kt")
        self.assertEqual(str(raised.exception), "roster_refused")


if __name__ == "__main__":
    unittest.main()
