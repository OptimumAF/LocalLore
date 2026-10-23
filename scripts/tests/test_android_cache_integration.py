"""Compose the real cache decoder/controller against synthetic transports only.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import unittest
from unittest.mock import Mock

import test_android_cache_control as lifecycle
import test_android_cache_result as protocol

control = lifecycle.control


class CacheIntegrationTests(unittest.TestCase):
    def invoke(self, packet, identity=None, post=None, cleaned=True):
        def transport(device, event, _):
            if event == "play":
                return lifecycle.response(packet, cleaned=cleaned)
        device = lifecycle.FakeDevice(transport)
        retained = []
        measure = Mock(side_effect=[lifecycle.sample(), post or lifecycle.sample()])
        receipt = protocol.identity() if identity is None else identity
        result = control.run_control(device, control.APK_SHA256, "gift", protocol.UUID, measure,
            lambda: control.cache_result.parse_model_identity(protocol.raw(receipt), protocol.UUID), retained.append)
        self.assertEqual(retained, [packet] if device.launches else [])
        return result, device, measure

    def test_real_decoder_authorizes_only_complete_synthetic_gift_proof(self):
        result, device, measure = self.invoke(protocol.raw())
        self.assertTrue(result["check_passed"])
        self.assertEqual(result["result"], protocol.fixture.value())
        self.assertEqual((device.launches, device.stops, measure.call_count), (1, 3, 2))

    def test_real_outer_post_error_retains_real_validated_commit(self):
        value = protocol.value(); value.update(status="error", error="volume_changed")
        del value["post_sample"]
        result, _, _ = self.invoke(protocol.raw(value))
        self.assertEqual(result["result"]["receipts_after"], 1)
        self.assertEqual(result["worker_error"], "volume_changed")
        self.assertFalse(result["storage_samples_valid"])
        self.assertFalse(result["check_passed"])

    def test_model_claim_with_wrong_full_digest_never_reaches_play(self):
        identity = protocol.identity(); identity["model_identity"]["sha256"] = "a" * 64
        result, device, _ = self.invoke(protocol.raw(), identity)
        self.assertFalse(result["model_verified"])
        self.assertEqual(device.launches, 0)
        self.assertIsNone(result["result"])

    def test_valid_receipt_survives_unknown_transport_without_more_device_or_post_reads(self):
        result, device, measure = self.invoke(protocol.raw(), cleaned=False)
        self.assertEqual(result["result"], protocol.fixture.value())
        self.assertFalse(result["check_passed"])
        self.assertFalse(result["clients_cleaned"])
        self.assertEqual((device.stops, measure.call_count), (2, 1))
        self.assertEqual(device.events[-1], "play")


if __name__ == "__main__":
    unittest.main()
