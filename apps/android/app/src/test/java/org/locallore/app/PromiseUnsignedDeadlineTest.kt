/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Real wire decoder, with strings surviving Android's otherwise lossy u64 number reader. */
class PromiseUnsignedDeadlineTest {
    private val context = StoryRecordContext(SavedStory("quay", "main", "Synthetic", 1), 1)
    private fun scope() = JSONObject().put("story", "quay").put("branch", "main")
    private fun promise(deadline: Any) = JSONObject().put("kind", "promise").put("key", "promise-one")
        .put("id", "one").put("from", "player").put("to", "mira").put("terms", "Return the key.")
        .put("deadline", deadline).put("status", "open").put("return_item", JSONObject.NULL)
        .put("sources", JSONArray().put(JSONObject().put("kind", "seed").put("value", "seed")))
        .put("origin", "derived_comparison")
    private fun event(deadline: Any) = JSONObject().put("kind", "event").put("key", "event-one")
        .put("origin", "recorded_observation").put("event", JSONObject()
            .put("sequence", 1).put("scope", scope()).put("turn", "promise-turn").put("story_time", 0)
            .put("participants", JSONArray().put("player").put("mira"))
            .put("witnesses", JSONArray().put("player").put("mira"))
            .put("consequence", JSONObject().put("effect", "promised").put("id", "one")
                .put("commitment", JSONObject().put("from", "player").put("to", "mira")
                    .put("terms", "Return the key.").put("deadline", deadline)
                    .put("source", JSONObject().put("kind", "seed").put("value", "seed"))
                    .put("return_item", JSONObject.NULL).put("completed_by", JSONObject.NULL))))
    private fun decode(row: JSONObject, section: StoryRecordSection, version: Int = 2): StoryRecordEntry {
        val query = StoryRecordQuery(context, section, version = version)
        val data = JSONObject().put("version", version).put("scope", scope()).put("head", 1).put("revision", 1)
            .put("story_time", 0).put("observer", JSONObject().put("kind", "player"))
            .put("privacy", "player_visible").put("status", "supported").put("view", section.wire)
            .put("total", 1).put("rows", JSONArray().put(row)).put("next_cursor", JSONObject.NULL)
            .put("unsupported", JSONArray())
        return StoryRecordWire.decode(JSONObject(data.toString()), query).entries.single()
    }

    @Test fun query2CanonicalUnsignedDeadlinesRenderExactlyAndHistoryRemainsNavigable() {
        for (deadline in listOf("0", "120", "9223372036854775807", "9223372036854775808", "18446744073709551615")) {
            val row = promise(deadline); val original = row.toString()
            assertTrue(decode(row, StoryRecordSection.PROMISES).text.contains("Due at story time · $deadline"))
            assertEquals(original, row.toString())
            val history = decode(event(deadline), StoryRecordSection.HISTORY)
            assertEquals("player promised mira: Return the key.", history.text)
            assertEquals(listOf(StoryRecordScopedEvent(StoryRecordScope("quay", "main"), 1)), history.scopedEventSources)
        }
    }

    @Test fun exactLegacySignedIntegersRemainSupportedButAmbiguousNumbersAndBadStringsRefuse() {
        for (deadline in listOf(0L, 120L, Long.MAX_VALUE)) {
            assertTrue(decode(promise(deadline), StoryRecordSection.PROMISES).text.contains("Due at story time · $deadline"))
            assertNotNull(decode(event(deadline), StoryRecordSection.HISTORY))
        }
        val invalid = listOf<Any>("", "00", "0120", "-1", "+1", " 1", "1 ", "1.0", "1e3", "18446744073709551616",
            "999999999999999999999", "١", -1L, 1.5, true, JSONObject.NULL)
        for (deadline in invalid) for ((row, section) in listOf(promise(deadline) to StoryRecordSection.PROMISES,
            event(deadline) to StoryRecordSection.HISTORY)) {
            try { decode(row, section); fail("Invalid unsigned value admitted: $deadline") }
            catch (failure: StoryRecordFailure) { assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem) }
        }
    }

    @Test fun query1HistoryRetainsItsNumericOnlyContract() {
        assertNotNull(decode(event(120L), StoryRecordSection.HISTORY, 1))
        for (deadline in listOf("120", "18446744073709551615")) {
            try { decode(event(deadline), StoryRecordSection.HISTORY, 1); fail("Query1 must retain numeric deadline") }
            catch (failure: StoryRecordFailure) { assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem) }
        }
    }
}
