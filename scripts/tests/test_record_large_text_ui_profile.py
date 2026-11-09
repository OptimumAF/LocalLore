"""Host-only oracles for the fixed Story Record large-text owner profile."""

from contextlib import redirect_stdout
import copy
from io import StringIO
import json
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_process_record_large_text_ui_verification as verification
from benchmarks import archive_ui_build
from benchmarks import owned_record_large_text_ui_contract as profile
from benchmarks import owned_record_large_text_ui_owner as owner
from scripts.tests import test_owned_target_contract as legacy


APP = "org.locallore.app.archiveverify"
TEST = APP + ".test"
SELECTOR = (
    "org.locallore.app.StoryRecordLargeTextTest"
    "#narrowRecordReflowsAtDoubleTextSizeAndKeepsActionsReachable"
)
RUNNER = TEST + "/androidx.test.runner.AndroidJUnitRunner"
GUEST = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-ui-v1/avd-v1")
ARCHIVE = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-apks-v1")


def expected_artifacts():
    return {
        "build": dict(path=str(ARCHIVE / "artifact-attestation-v1.json"), bytes=1514,
                      sha256="23dd50c9f29bbc03340b14b2d217b9dbc499c01d3bf9ea4c886d42a93a9447a6"),
        "product_apk": dict(path=str(ARCHIVE / "app-debug.apk"), bytes=28012684,
                            sha256="be73e0b4eda34ed3da3173f8c2147802d17b769b638f8cf512f99bd612e8fe12"),
        "test_apk": dict(path=str(ARCHIVE / "app-debug-androidTest.apk"), bytes=2269096,
                         sha256="9544b1a9b8d47bba1c100fd776f676570402de91624238cfccb3531159d5ad15"),
    }


def admission():
    value = legacy.admission()
    value["protocol"] = profile.PROTOCOL
    value["guest"]["root"] = str(GUEST)
    value["artifacts"] = expected_artifacts()
    source_root = PureWindowsPath("D:/Synthetic/LocalLore/benchmarks")
    value["sources"] = [legacy.pin(source_root / name) for name in sorted(profile.SOURCE_NAMES)]
    by_name = {PureWindowsPath(row["path"]).name: row for row in value["sources"]}
    value["server"]["sources"] = [
        copy.deepcopy(by_name[PureWindowsPath(row["path"]).name])
        for row in value["server"]["sources"]
    ]
    return value


class RecordLargeTextUiProfileTests(unittest.TestCase):
    def test_fixed_roster_and_artifact_pins_are_detached(self):
        self.assertEqual((profile.APP, profile.TEST), (APP, TEST))
        self.assertEqual(profile.GUEST_ROOT, GUEST)
        self.assertIs(profile.MODEL_MATERIAL, False)
        self.assertEqual(profile.CLIENT_VERSION, 19)
        self.assertEqual(tuple(profile.CLAIM_KINDS), ("record_large_text",))
        self.assertEqual(tuple(profile.INSTRUMENTATIONS), (("record_large_text", *SELECTOR.split("#")),))
        self.assertEqual(profile.ARTIFACT_KEYS, expected_artifacts().keys())

        pins = profile.artifact_bindings()
        self.assertEqual(pins, expected_artifacts())
        pins["product_apk"]["path"] = "D:/Synthetic/another.apk"
        pins.pop("build")
        self.assertEqual(profile.artifact_bindings(), expected_artifacts())

    def test_exact_file_pins_are_read_once_with_byte_caps(self):
        pins = expected_artifacts()
        with patch.object(archive_ui_build, "_bound", return_value=b"checked") as reader:
            profile.verify_artifacts(pins)
        self.assertEqual(reader.call_count, 3)
        self.assertCountEqual([entry.args[0] for entry in reader.call_args_list], pins.values())
        for entry in reader.call_args_list:
            self.assertEqual(entry.kwargs.get("cap"), entry.args[0]["bytes"])
        self.assertEqual(pins, expected_artifacts())

    def test_untrusted_artifact_metadata_refuses_before_any_read(self):
        wrong = expected_artifacts()
        wrong["test_apk"]["path"] = "D:/Synthetic/app-debug-androidTest.apk"
        malformed_path = expected_artifacts()
        malformed_path["test_apk"]["path"] = None
        wrong_drive = expected_artifacts()
        wrong_drive["product_apk"]["path"] = r"C:\Synthetic\app-debug.apk"
        altered = expected_artifacts()
        altered["build"]["sha256"] = "0" * 64
        swapped = expected_artifacts()
        swapped["test_apk"], swapped["product_apk"] = swapped["product_apk"], swapped["test_apk"]
        coerced = expected_artifacts()
        coerced["test_apk"]["bytes"] = float(coerced["test_apk"]["bytes"])
        extra = dict(expected_artifacts(), model=legacy.admission()["artifacts"]["model"])
        partial = expected_artifacts()
        partial.pop("build")
        with patch.object(archive_ui_build, "_bound") as reader:
            for label, pins in (("path", wrong), ("malformed-path", malformed_path),
                                ("wrong-drive", wrong_drive), ("hash", altered), ("roles", swapped),
                                ("numeric-type", coerced), ("model", extra), ("missing", partial)):
                with self.subTest(label=label), self.assertRaisesRegex(profile.TargetRefused, "^binding$"):
                    profile.verify_artifacts(pins)
        reader.assert_not_called()

    def test_reader_refusal_is_redacted_and_interruptions_stop_reads(self):
        pins = expected_artifacts()
        private_error = OSError("private-read-context-should-not-appear")
        with patch.object(archive_ui_build, "_bound", side_effect=private_error) as reader:
            with self.assertRaisesRegex(profile.TargetRefused, "^binding$"):
                profile.verify_artifacts(pins)
        self.assertEqual(reader.call_count, 1)

        for interrupt in (KeyboardInterrupt(), SystemExit(17)):
            with self.subTest(interrupt=type(interrupt).__name__):
                with patch.object(archive_ui_build, "_bound", side_effect=interrupt) as reader:
                    with self.assertRaises(type(interrupt)) as caught:
                        profile.verify_artifacts(pins)
                self.assertIs(caught.exception, interrupt)
                self.assertEqual(reader.call_count, 1)

    def test_parent_entrypoint_checks_frozen_bytes_before_owner_handoff(self):
        mechanisms = owner.mechanisms
        path = PureWindowsPath("D:/Synthetic/LocalLore/admission-v1.json")
        pin = legacy.pin(path)
        value = admission()
        argv = ["--admission", str(path), "--admission-sha256", pin["sha256"]]

        # The public entrypoint and its shared validation stay active. None of
        # the real file, platform, parent-launch or target ports are used.
        with patch.object(mechanisms, "os", SimpleNamespace(name="nt")), \
             patch.object(mechanisms.file_guard, "_existing_D_file", return_value=path), \
             patch.object(mechanisms.file_guard, "_read_bound", return_value=(pin, value)) as input_reader:
            with patch.object(archive_ui_build, "_bound", side_effect=OSError("private-read-context")) as reader, \
                 patch.object(mechanisms, "_parent") as parent, redirect_stdout(StringIO()) as output:
                self.assertEqual(owner.main(argv), 1)
            self.assertEqual(reader.call_count, 1)
            parent.assert_not_called()
            self.assertEqual(json.loads(output.getvalue()), {
                "qualified_target": False, "reason": "binding", "feature_acceptance": False,
            })
            input_reader.assert_called_once_with(path, pin["sha256"], 2 * 1024 * 1024, "admission")

            with patch.object(archive_ui_build, "_bound", return_value=b"checked") as reader:
                def observe_parent(binding, admitted, *, _contract, _verification):
                    self.assertEqual(reader.call_count, 3)
                    self.assertEqual((binding, admitted), (pin, value))
                    self.assertIs(_contract, profile)
                    self.assertIs(_verification, verification)
                    return 0

                with patch.object(mechanisms, "_parent", side_effect=observe_parent) as parent:
                    self.assertEqual(owner.main(argv), 0)
                parent.assert_called_once()

    def test_admission_rejects_other_guests_extra_artifacts_and_wrong_pins_without_read(self):
        value = admission()
        old_guest = copy.deepcopy(value)
        old_guest["guest"]["root"] = "D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-v1/avd-v1"
        wrong_apk = copy.deepcopy(value)
        wrong_apk["artifacts"]["product_apk"]["sha256"] = "1" * 64
        model = copy.deepcopy(value)
        model["artifacts"]["model"] = legacy.admission()["artifacts"]["model"]
        extra_selector = dict(value, selector="other.Class#test")
        observation = Mock(side_effect=AssertionError("unexpected file observation"))
        with patch.object(Path, "open", observation):
            detached = profile.validate_admission(value)
            self.assertEqual(detached, value)
            detached["artifacts"]["build"]["sha256"] = "0" * 64
            self.assertEqual(value["artifacts"], expected_artifacts())
            for label, invalid in (("guest", old_guest), ("apk", wrong_apk), ("model", model),
                                   ("selector", extra_selector)):
                with self.subTest(label=label), self.assertRaises(profile.TargetRefused):
                    profile.validate_admission(invalid)
        observation.assert_not_called()

    def test_only_exact_runner_selector_and_role_bound_stage_commands_are_accepted(self):
        value = admission()
        argv = ["am", "instrument", "-w", "-r", "-e", "class", SELECTOR, RUNNER]
        operation = dict(argv=argv, stdin=None)
        self.assertEqual(profile.validate_operation(operation, value), operation)
        self.assertEqual(profile.instrumentation_kind(argv), "record_large_text")

        stage = ["dd", "of=/data/local/tmp/locallore-product-v1.apk", "bs=65536"]
        product = expected_artifacts()["product_apk"]
        stage_product = dict(argv=stage, stdin=product)
        self.assertEqual(profile.validate_operation(stage_product, value), stage_product)

        forbidden = [
            dict(argv=argv[:-2] + [SELECTOR.split("#")[0], RUNNER], stdin=None),
            dict(argv=argv[:-2] + [SELECTOR + ",foreign.Class#other", RUNNER], stdin=None),
            dict(argv=argv[:-1] + ["org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner"], stdin=None),
            dict(argv=stage, stdin=expected_artifacts()["test_apk"]),
            dict(argv=["am", "force-stop", "--user", "0", APP], stdin=None),
            dict(argv=["pidof", APP], stdin=None),
            dict(argv=["run-as", APP, "--user", "0", "cat", "files/model.task"], stdin=None),
        ]
        for invalid in forbidden:
            with self.subTest(argv=invalid["argv"]), self.assertRaises(profile.TargetRefused):
                profile.validate_operation(invalid, value)


if __name__ == "__main__":
    unittest.main()
