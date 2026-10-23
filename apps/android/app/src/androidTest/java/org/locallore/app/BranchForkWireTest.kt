/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual Android JSONObject decoder tests; no JNI/Store execution in this class. */
@RunWith(AndroidJUnit4::class)
class BranchForkWireTest {
    private val input = BranchForkInput(ForkScope("story-a", "main"), "child", 2, 1)
    private fun outcome() = JSONObject().put("version", 1)
        .put("scope", JSONObject().put("story", "story-a").put("branch", "child"))
        .put("parent", JSONObject().put("story", "story-a").put("branch", "main"))
        .put("fork_revision", 1).put("head_revision", 3).put("created", false)
    private fun data() = JSONObject().put("operation", 41).put("phase", "completed").put("cancel_requested", true)
        .put("result", JSONObject().put("kind", "fork").put("outcome", outcome())).put("error", JSONObject.NULL)
    private fun wrap(data: JSONObject) = JSONObject().put("version", 1).put("status", "ok").put("data", data)
        .toString().toByteArray(Charsets.UTF_8)
    private fun rejects(block: () -> Unit) {
        try { block(); fail("Malformed fork control accepted") }
        catch (failure: BranchForkFailure) { assertEquals("Timeline fork could not be confirmed", failure.message) }
    }
    @Test fun actualClosedStatusAcceptsCommittedLateCancelAndPreservesOriginalParent() {
        val result = ForkNativeWire.status(wrap(data()), input)
        assertEquals(BranchForkPhase.COMPLETED, result.phase); assertTrue(result.cancelRequested)
        assertEquals(input.parent, result.outcome!!.parent); assertEquals(3L, result.outcome!!.headRevision)
        assertFalse(result.outcome!!.created)
    }
    @Test fun wrongScopesVersionsKeysTypesAndUnsafeNumbersAreRejected() {
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("operation", 0) }, { it.put("operation", "41") }, { it.put("cancel_requested", "true") },
            { it.put("phase", "invented") }, { it.put("private", "SECRET") },
            { it.getJSONObject("result").getJSONObject("outcome").put("version", 4294967297L) },
            { it.getJSONObject("result").getJSONObject("outcome").put("head_revision", 9007199254740992L) },
            { it.getJSONObject("result").getJSONObject("outcome").put("head_revision", 0) },
            { it.getJSONObject("result").getJSONObject("outcome").put("fork_revision", 0) },
            { it.getJSONObject("result").getJSONObject("outcome").getJSONObject("parent").put("branch", "sibling") },
            { it.getJSONObject("result").getJSONObject("outcome").getJSONObject("scope").put("story", "foreign") })
        for (mutation in mutations) rejects { ForkNativeWire.status(wrap(data().also(mutation)), input) }
    }
    @Test fun duplicateKeysTrailingValuesLenientSyntaxInvalidUtf8AndOversizeFailClosed() {
        val valid = wrap(data()).toString(Charsets.UTF_8)
        rejects { ForkNativeWire.status(valid.replaceFirst("\"version\":1", "\"version\":1,\"version\":1").toByteArray(), input) }
        rejects { ForkNativeWire.status((valid + "{}").toByteArray(), input) }
        rejects { ForkNativeWire.status(valid.replace('"', '\'').toByteArray(), input) }
        rejects { ForkNativeWire.status(byteArrayOf(0xc3.toByte(), 0x28), input) }
        rejects { ForkNativeWire.status(ByteArray(4097) { 32 }, input) }
    }
    @Test fun exactRecoveryRoundTripFutureVersionsAndLookupCannotClaimCreation() {
        val saved = BranchForkRecovery(1, input)
        assertEquals(saved, ForkNativeWire.recovery(ForkNativeWire.recovery(saved)))
        val bytes = ForkNativeWire.recovery(saved).toString(Charsets.UTF_8)
        rejects { ForkNativeWire.recovery(bytes.replaceFirst("\"version\":1", "\"version\":2").toByteArray()) }
        val lookup = JSONObject().put("version", 1).put("kind", "fork_lookup").put("found", true).put("outcome", outcome())
        assertEquals(3L, ForkNativeWire.lookup(wrap(lookup), input).outcome!!.headRevision)
        rejects { ForkNativeWire.lookup(wrap(lookup.put("outcome", outcome().put("created", true))), input) }
        rejects { ForkNativeWire.lookup(wrap(lookup.put("found", false)), input) }
        assertEquals(BranchForkLookup(false, null), ForkNativeWire.lookup(wrap(lookup.put("outcome", JSONObject.NULL)), input))
    }
}
