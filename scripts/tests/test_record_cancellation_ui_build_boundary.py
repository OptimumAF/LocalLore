"""Attempted-observation oracles independent of safe error normalization."""
import copy
import unittest
from unittest.mock import Mock, patch

from benchmarks import record_cancellation_ui_build as b


class NoObservationBoundaryTests(unittest.TestCase):
    def test_invalid_roles_cannot_construct_a_reader_or_call_the_fixed_loader(self):
        for value in (None, False, [], {}, {"build": {}},
                      {"build": {}, "product_apk": {}, "test_apk": {}, "model": {}}):
            reader = Mock(side_effect=AssertionError("Reader must not be constructed"))
            loader = Mock(side_effect=AssertionError("Loader must not be called"))
            with self.subTest(value=repr(value)), patch.object(b, "_Reader", reader), \
                    patch.object(b, "_load_baseline", loader):
                with self.assertRaises(b.BuildRefused):
                    b.verify_frozen_product(value)
                reader.assert_not_called()
                loader.assert_not_called()

    def test_foreign_roles_cannot_attempt_any_artifact_read_or_json_read(self):
        def pin(path):
            return dict(path=path, bytes=1, sha256="0" * 64)
        # These nonexistent paths are never opened. Only the role comparison
        # layer receives this minimal synthetic loader response.
        base = dict(roots=dict(manifest="D:/Synthetic/B111/manifest.json"), apks=dict(
            product_apk=pin("D:/Synthetic/B111/product.apk"),
            test_apk=pin("D:/Synthetic/B111/tests.apk")))
        for role in ("build", "product_apk", "test_apk"):
            artifacts = dict(copy.deepcopy(base["apks"]), build=pin(base["roots"]["manifest"]))
            artifacts[role] = pin("C:/PRIVATE-B111-FORBIDDEN/" + role)
            reader = Mock()
            reader.read.side_effect = AssertionError("Foreign read attempt")
            reader.json.side_effect = AssertionError("Foreign JSON read attempt")
            constructor = Mock(return_value=reader)
            loader = Mock(return_value=copy.deepcopy(base))
            with self.subTest(role=role), patch.object(b, "_Reader", constructor), \
                    patch.object(b, "_load_baseline", loader):
                with self.assertRaises(b.BuildRefused):
                    b.verify_frozen_product(artifacts)
                constructor.assert_called_once_with()
                loader.assert_called_once_with(reader)
                reader.read.assert_not_called()
                reader.json.assert_not_called()
                reader.final.assert_not_called()
