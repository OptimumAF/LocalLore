/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.security.MessageDigest

class PresentationProcessProofTest {
    private fun counts() = presentationProcessOperations.associateWith { 0 }.toMutableMap()
    private fun record(ops: Map<String, Int> = counts(), hint: PlayDraftScope? = PlayDraftScope("story", "main")) =
        presentationProcessRecord("0123456789abcdef", 123, 10001, 7, 2, 90, "command", true, 1, hint, ops)
    private fun refused(action: () -> Unit) {
        try { action(); fail("Expected bounded proof refusal") } catch (_: IllegalArgumentException) { }
    }

    @Test fun presentationAndLegacyAttemptsAreSeparateAndUnknownOperationsRemainVisible() {
        val counts = counts()
        for (operation in listOf("play_presentation_v2", "play_presentation_v2", "play_snapshot", "PRIVATE_UNKNOWN_OPERATION")) {
            val key = checkNotNull(presentationProcessOperationKey(operation)); counts[key] = counts.getValue(key) + 1
        }
        val raw = record(counts); val value = JSONObject(raw.toString(Charsets.UTF_8))
        assertEquals(3, value.getInt("version"))
        assertEquals("locallore_presentation_process_verify_v3", value.getString("scope"))
        val operations = value.getJSONObject("operations")
        assertEquals(presentationProcessOperations.toSet(), operations.keys().asSequence().toSet())
        assertEquals(2, operations.getInt("play_presentation_v2")); assertEquals(1, operations.getInt("play_snapshot"))
        assertEquals(1, operations.getInt("other")); assertFalse(raw.toString(Charsets.UTF_8).contains("PRIVATE_UNKNOWN"))
    }

    @Test fun metadataAndCreationAliasesDoNotHideOtherUnknownAttempts() {
        for (name in listOf("close", "capabilities", "model_status", "story_templates", "authoring_cancel")) {
            assertNull(presentationProcessOperationKey(name))
        }
        for (name in listOf("create_configured", "create_presented", "authoring_create")) {
            assertEquals("create_named", presentationProcessOperationKey(name))
        }
        assertEquals("other", presentationProcessOperationKey("play_presentation_v3"))
        assertEquals("other", presentationProcessOperationKey("fork_mutation"))
        assertEquals("other", presentationProcessOperationKey(""))
    }

    @Test fun exactRuntimeAndScopeDigestFieldsDoNotRetainScopeOrMutableCounters() {
        val operations = counts(); val raw = record(operations); operations["commit"] = 1
        val value = JSONObject(raw.toString(Charsets.UTF_8))
        assertEquals(setOf("version", "scope", "run_id", "pid", "uid", "task_id", "sequence", "process_start_uptime_ms",
            "event", "restored_state", "factory_creations", "hint_present", "hint_sha256", "operations"), value.keys().asSequence().toSet())
        assertEquals(123, value.getInt("pid")); assertEquals(10001, value.getInt("uid")); assertEquals(7, value.getInt("task_id"))
        assertEquals(90L, value.getLong("process_start_uptime_ms")); assertTrue(value.getBoolean("restored_state"))
        assertEquals(1, value.getInt("factory_creations")); assertTrue(value.getBoolean("hint_present"))
        val hash = MessageDigest.getInstance("SHA-256").digest("1\nstory\nmain\n".toByteArray())
            .joinToString("") { "%02x".format(it) }
        assertEquals(hash, value.getString("hint_sha256")); assertFalse(value.has("story")); assertFalse(value.has("branch"))
        assertEquals(0, value.getJSONObject("operations").getInt("commit")); assertTrue(raw.size <= 4096)
    }

    @Test fun invalidOrMissingHintProducesNoScopeDigest() {
        for (scope in listOf(null, PlayDraftScope("INVALID story", "main"))) {
            val value = JSONObject(record(hint = scope).toString(Charsets.UTF_8))
            assertFalse(value.getBoolean("hint_present")); assertTrue(value.isNull("hint_sha256"))
        }
    }

    @Test fun counterShapeAndBoundsCannotBeExpandedByInput() {
        refused { record(counts().apply { remove("play_presentation_v2") }) }
        refused { record(counts().apply { put("unknown", 0) }) }
        refused { record(counts().apply { put("other", -1) }) }
        refused { record(counts().apply { put("play_presentation_v2", 4097) }) }
        val value = JSONObject(record(counts().apply { put("play_presentation_v2", 4096) }).toString(Charsets.UTF_8))
        assertEquals(4096, value.getJSONObject("operations").getInt("play_presentation_v2"))
    }

    @Test fun runtimeIdentityAndRunBoundsRejectMalformedProofInputs() {
        refused { presentationProcessRecord("BAD", 123, 10001, 7, 2, 90, "command", true, 1, null, counts()) }
        refused { presentationProcessRecord("0123456789abcdef", 0, 10001, 7, 2, 90, "command", true, 1, null, counts()) }
        refused { presentationProcessRecord("0123456789abcdef", 123, 9999, 7, 2, 90, "command", true, 1, null, counts()) }
        refused { presentationProcessRecord("0123456789abcdef", 123, 10001, -1, 2, 90, "command", true, 1, null, counts()) }
        refused { presentationProcessRecord("0123456789abcdef", 123, 10001, 7, 65537, 90, "command", true, 1, null, counts()) }
        refused { presentationProcessRecord("0123456789abcdef", 123, 10001, 7, 2, 90, "unknown", true, 1, null, counts()) }
        refused { presentationProcessRecord("0123456789abcdef", 123, 10001, 7, 2, 90, "command", true, 17, null, counts()) }
    }
}
