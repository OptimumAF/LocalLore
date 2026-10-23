/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/** Native-only: no Activity rule, SQL, injected replies, or default application workspace. */
@RunWith(AndroidJUnit4::class)
class EventSourceInstrumentedTest {
    @Before fun noActivityBefore() = assertNoRecordActivities()
    @After fun noActivityAfter() = assertNoRecordActivities()

    @Test fun crossSceneSourcesNavigateToExactAcceptedEventsWithoutNewTurnsAndReopenStrictly() = runBlocking {
        withRecordFixture { fixture ->
            var owner = fixture.owner()
            val saved = seedEventScenes(owner)
            val accepted = owner.acceptedView()
            val receipts = JSONObject(accepted).getJSONArray("receipts")
            assertEquals(3, receipts.length())
            assertEquals(4L, saved.revision) // The last turn has two accepted effects.
            assertEquals(6, saved.messages.size)
            val turnCalls = owner.transport.turnCalls.get()
            val model = eventModel(fixture, owner)
            awaitEventShell(model)
            withContext(Dispatchers.Main) { model.openStoryRecord() }
            val profiles = awaitEventRecord(model)
            val location = profiles.entries.single { it.title == "location" }
            assertEquals("pier", location.text)
            assertEquals(listOf(2L), location.eventSources)
            assertEquals(listOf("Event #2"), location.sources)
            val relationships = owner.gateway.readStoryRecord(StoryRecordQuery(
                StoryRecordContext(checkNotNull(saved.selected), saved.revision), StoryRecordSection.RELATIONSHIPS))
            assertTrue(relationships.entries.isNotEmpty())
            // Giving updates an NPC's incoming obligation; that is not the player's outgoing edge.
            assertTrue(relationships.entries.all { it.origin == StoryRecordOrigin.CANONICAL_FIELD &&
                it.eventSources.isEmpty() && it.sources == listOf("Seed \u00B7 lantern-quay-v1") })
            withContext(Dispatchers.Main) { model.openRecordEvent(2) }
            val moved = awaitEventRecord(model) { it.eventDetail?.let { detail -> !detail.loading } == true }.eventDetail!!
            assertNull(moved.problem)
            assertEquals(2L, moved.reference)
            val movement = checkNotNull(moved.entry)
            assertEquals(StoryRecordOrigin.RECORDED_OBSERVATION, movement.origin)
            assertEquals(StoryRecordEvent(2, receipts.getJSONObject(1).getJSONObject("request").getString("turn"), 100), movement.event)
            assertTrue(movement.text.contains("quay") && movement.text.contains("pier"))
            withContext(Dispatchers.Main) { model.backToStoryRecord() }
            assertEquals(profiles, model.storyRecord.value)
            // An ID that exists in history is still not a grant from this displayed profile page.
            withContext(Dispatchers.Main) { model.openRecordEvent(1); model.openRecordEvent(5) }
            assertEquals(profiles, model.storyRecord.value)
            withContext(Dispatchers.Main) { model.recordSection(StoryRecordSection.HISTORY) }
            val history = awaitEventRecord(model) { it.section == StoryRecordSection.HISTORY }
            val events = history.entries.filter { it.event != null }
            assertEquals(setOf(1L, 2L, 3L, 4L), events.map { it.event!!.sequence }.toSet())
            assertTrue(events.all { it.eventSources == listOf(it.event!!.sequence) && it.event!!.storyTime == 100L })
            val rawEvents = jsonRows(owner.recordData(StoryRecordQuery(
                StoryRecordContext(checkNotNull(saved.selected), saved.revision), StoryRecordSection.HISTORY)))
                .filter { it.getString("kind") == "event" }.map { it.getJSONObject("event") }
                .associateBy { it.getLong("sequence") }
            fun actors(sequence: Long, field: String): Set<String> = rawEvents.getValue(sequence).getJSONArray(field).let { rows ->
                (0 until rows.length()).map { rows.getString(it) }.toSet()
            }
            assertEquals(setOf("player", "mira"), actors(1, "witnesses"))
            assertEquals(setOf("player", "oren"), actors(3, "witnesses"))
            assertEquals(setOf("player"), actors(4, "witnesses")) // Ledger inference does not notify Oren.
            assertEquals(setOf("player", "oren"), actors(4, "participants"))
            val returnedTurn = receipts.getJSONObject(2).getJSONObject("request").getString("turn")
            assertTrue(events.filter { it.event!!.sequence in 3L..4L }.all { it.event!!.turn == returnedTurn })
            assertTrue(history.entries.any { it.origin == StoryRecordOrigin.RECORDED_MESSAGE && it.eventSources == listOf(3L, 4L) })
            withContext(Dispatchers.Main) { model.openRecordEvent(1) }
            val oldScene = awaitEventRecord(model) { it.eventDetail?.loading == false }.eventDetail!!.entry!!
            assertEquals(1L, oldScene.event!!.sequence)
            assertEquals(receipts.getJSONObject(0).getJSONObject("request").getString("turn"), oldScene.event!!.turn)
            assertTrue(oldScene.text.contains("mira") && oldScene.text.contains("potion"))
            withContext(Dispatchers.Main) { model.backToStoryRecord(); model.closeStoryRecord() }
            assertTrue("Event navigation changed accepted state", accepted == owner.acceptedView())
            assertTrue(saved == owner.gateway.snapshot())
            assertEquals("Browsing submitted/prepared/committed gameplay", turnCalls, owner.transport.turnCalls.get())
            fixture.closeOwnersAndDrain()
            owner = fixture.owner()
            assertTrue(saved == owner.gateway.initialize())
            val restored = owner.gateway.readStoryRecord(StoryRecordQuery(StoryRecordContext(checkNotNull(saved.selected), saved.revision), StoryRecordSection.HISTORY))
            assertEquals(history.entries, restored.entries)
            assertTrue("Strict reopen changed receipts", accepted == owner.acceptedView())
        }
    }

    @Test fun playerSourcesCannotGrantNpcFutureBranchOrOtherStoryEvents() = runBlocking {
        withRecordFixture { fixture ->
            var owner = fixture.owner()
            owner.gateway.initialize()
            assertTrue(owner.gateway.commitAsync(owner.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)) is DemoResult.Accepted)
            owner.commitIntent(JSONObject().put("kind", "dialogue").put("value", JSONObject()
                .put("text", "SYNTHETIC quoted text: \"sequence\":1, Sources Event #999")
                .put("audience", JSONArray().put("mira"))))
            owner.commitIntent(JSONObject().put("kind", "actions").put("value", JSONArray()
                .put(JSONObject().put("op", "believe").put("claim_event", 2))))
            val storyA = owner.gateway.snapshot()
            val beforeA = owner.acceptedView()
            val queryA = StoryRecordQuery(StoryRecordContext(checkNotNull(storyA.selected), 3), StoryRecordSection.HISTORY)
            val visible = owner.gateway.readStoryRecord(queryA.copy(search = "\"sequence\":1,"))
            assertEquals(1, visible.entries.size)
            assertEquals(1L, visible.entries.single().event!!.sequence)
            assertEquals(0, owner.gateway.readStoryRecord(queryA.copy(search = "\"sequence\":4,")).total)
            val quoted = owner.gateway.readStoryRecord(queryA.copy(search = "999"))
            assertTrue(quoted.entries.isNotEmpty())
            assertTrue(quoted.entries.all { 999L !in it.eventSources && it.eventSources.all { source -> source in 2L..3L } })
            val claim = owner.gateway.readStoryRecord(queryA.copy(section = StoryRecordSection.KNOWLEDGE, search = "999"))
            assertEquals(listOf(2L), claim.entries.single { it.origin == StoryRecordOrigin.RECORDED_STATEMENT }.eventSources)
            assertEquals(setOf(2L, 3L), claim.entries.single { it.origin == StoryRecordOrigin.SUBJECTIVE_BELIEF }.eventSources.toSet())
            val turnCallsA = owner.transport.turnCalls.get()
            for (observer in listOf(JSONObject().put("kind", "character").put("id", "mira"), JSONObject().put("kind", "omniscient"))) {
                val rejected = owner.transport.exchange(owner.recordCommand(queryA, observer))
                assertEquals("rejected", rejected.getString("status"))
                assertEquals("Forbidden", rejected.getString("error"))
            }
            val future = owner.transport.exchange(owner.recordCommand(queryA.copy(context = queryA.context.copy(revision = 4))))
            assertEquals("rejected", future.getString("status"))
            assertEquals("Stale", future.getString("error"))
            val branch = queryA.copy(context = queryA.context.copy(story = checkNotNull(storyA.selected).copy(branch = "synthetic-other-branch")))
            assertEquals("Scope", owner.transport.exchange(owner.recordCommand(branch)).getString("error"))
            for (privateText in listOf("The tideglass relic is in old-ruins.", "Rowan may possess the tideglass relic.")) {
                val page = owner.gateway.readStoryRecord(queryA.copy(section = StoryRecordSection.KNOWLEDGE, search = privateText))
                assertEquals("Private NPC data contributed a source match", 0, page.total)
                assertTrue(page.entries.isEmpty())
            }
            assertTrue(beforeA == owner.acceptedView())
            assertEquals(turnCallsA, owner.transport.turnCalls.get())
            val model = eventModel(fixture, owner)
            awaitEventShell(model)
            withContext(Dispatchers.Main) { model.openStoryRecord() }
            awaitEventRecord(model)
            withContext(Dispatchers.Main) { model.recordSection(StoryRecordSection.KNOWLEDGE) }
            val knowledge = awaitEventRecord(model) { it.section == StoryRecordSection.KNOWLEDGE }
            assertTrue(knowledge.entries.filter { it.origin == StoryRecordOrigin.CANONICAL_TRUTH }
                .all { it.eventSources.isEmpty() && !it.text.contains("999") })
            withContext(Dispatchers.Main) { model.openRecordEvent(999) }
            assertEquals("Narrative source-like text granted an event", knowledge, model.storyRecord.value)
            val receipts = JSONObject(beforeA).getJSONArray("receipts")
            for (sequence in listOf(2L, 3L)) {
                withContext(Dispatchers.Main) { model.openRecordEvent(sequence) }
                val detail = awaitEventRecord(model) { it.eventDetail?.loading == false }.eventDetail!!
                assertNull(detail.problem)
                val event = checkNotNull(detail.entry)
                assertEquals(StoryRecordOrigin.RECORDED_OBSERVATION, event.origin)
                assertTrue(event.text.contains("999"))
                assertEquals(StoryRecordEvent(sequence, receipts.getJSONObject(sequence.toInt() - 1)
                    .getJSONObject("request").getString("turn"), 100), event.event)
                withContext(Dispatchers.Main) { model.backToStoryRecord() }
                assertEquals(knowledge, model.storyRecord.value)
            }
            assertTrue(beforeA == owner.acceptedView())
            assertEquals(turnCallsA, owner.transport.turnCalls.get())
            withContext(Dispatchers.Main) { model.closeStoryRecord(); model.reset() }
            awaitEventShell(model)
            val storyB = owner.gateway.snapshot()
            assertEquals(0L, storyB.revision)
            assertTrue(checkNotNull(storyA.selected).story != checkNotNull(storyB.selected).story)
            val beforeB = owner.acceptedView()
            try { owner.gateway.readStoryRecord(queryA); fail("Other-story query accepted") }
            catch (failure: StoryRecordFailure) { assertEquals(StoryRecordProblem.STALE, failure.problem) }
            assertEquals("Scope", owner.transport.exchange(owner.recordCommand(queryA)).getString("error"))
            val queryB = StoryRecordQuery(StoryRecordContext(checkNotNull(storyB.selected), 0), StoryRecordSection.HISTORY, "\"sequence\":1,")
            assertEquals(0, owner.gateway.readStoryRecord(queryB).total)
            withContext(Dispatchers.Main) { model.openStoryRecord() }
            val current = awaitEventRecord(model)
            assertTrue(current.entries.all { it.eventSources.isEmpty() })
            withContext(Dispatchers.Main) { model.openRecordEvent(1); model.openRecordEvent(Long.MAX_VALUE) }
            assertEquals(current, model.storyRecord.value)
            assertTrue(beforeB == owner.acceptedView())
            fixture.closeOwnersAndDrain()
            owner = fixture.owner()
            val reopened = owner.gateway.initialize()
            val restored = owner.gateway.resumeSaved(reopened.stories.single { it.story == checkNotNull(storyA.selected).story })
            assertEquals(storyA.revision, restored.revision)
            assertEquals(storyA.messages, restored.messages)
            assertTrue(beforeA == owner.acceptedView())
        }
    }

    @Test fun decoderRequiresValidTypedEvidenceAndEventMetadataAndNeverLinksWithheldEvidence() = runBlocking {
        withRecordFixture { fixture ->
            val owner = fixture.owner()
            val saved = seedEventScenes(owner)
            val query = StoryRecordQuery(StoryRecordContext(checkNotNull(saved.selected), saved.revision), StoryRecordSection.HISTORY)
            val original = owner.recordData(query)
            val decoded = StoryRecordWire.decode(original, query)
            assertEquals(setOf(1L, 2L, 3L, 4L), decoded.entries.mapNotNull { it.event?.sequence }.toSet())
            val accepted = owner.acceptedView()
            val turnCalls = owner.transport.turnCalls.get()
            val eventMutations: List<(JSONObject) -> Unit> = listOf(
                { it.remove("turn") }, { it.put("turn", "") }, { it.put("turn", "X".repeat(65)) },
                { it.put("turn", "PRIVATE-METADATA-CANARY\n") },
                { it.put("sequence", 0) }, { it.put("sequence", saved.revision + 1) }, { it.put("sequence", true) },
                { it.remove("story_time") }, { it.put("story_time", -1) }, { it.put("story_time", 101) },
                { it.getJSONObject("scope").put("branch", "synthetic-other-branch") },
                { it.put("witnesses", JSONArray().put("mira")) },
            )
            for ((index, mutate) in eventMutations.withIndex()) {
                val page = JSONObject(original.toString())
                mutate(jsonRows(page).first { it.getString("kind") == "event" }.getJSONObject("event"))
                assertInvalidEventPage(page, query, index)
            }
            for (remove in listOf(true, false)) {
                val page = JSONObject(original.toString())
                val row = jsonRows(page).first { it.getString("kind") == "event" }
                if (remove) row.remove("event") else row.put("event", JSONObject.NULL)
                assertInvalidEventPage(page, query, 15)
            }
            val duplicate = JSONObject(original.toString())
            val duplicateEvents = jsonRows(duplicate).filter { it.getString("kind") == "event" }
            duplicateEvents[1].getJSONObject("event").put("sequence", duplicateEvents[0].getJSONObject("event").getLong("sequence"))
            assertInvalidEventPage(duplicate, query, 16)
            for ((index, ids) in listOf(JSONArray(), JSONArray().put(1).put(1), JSONArray().put(-1), JSONArray().put(true), JSONArray().put(5)).withIndex()) {
                val page = JSONObject(original.toString())
                jsonRows(page).first { it.getString("kind") == "message" }.put("event_ids", ids)
                assertInvalidEventPage(page, query, 20 + index)
            }
            // Local decoder mutations exercise display safety only; they are not engine evidence.
            val knowledgeQuery = query.copy(section = StoryRecordSection.KNOWLEDGE)
            val knowledge = owner.recordData(knowledgeQuery)
            val seeded = StoryRecordWire.decode(knowledge, knowledgeQuery)
            assertTrue(seeded.entries.all { it.eventSources.isEmpty() && it.event == null })
            val withheld = JSONObject(knowledge.toString())
            jsonRows(withheld).forEach { it.put("sources", JSONArray().put(JSONObject().put("kind", "withheld"))) }
            val safe = StoryRecordWire.decode(withheld, knowledgeQuery)
            assertTrue(safe.entries.all { it.sources == listOf("Evidence withheld") && it.eventSources.isEmpty() && it.event == null })
            val mixed = JSONObject(knowledge.toString())
            jsonRows(mixed).first().put("sources", JSONArray().put(JSONObject().put("kind", "withheld"))
                .put(JSONObject().put("kind", "event").put("value", 1)).put(JSONObject().put("kind", "seed").put("value", "lantern-quay-v1")))
            assertEquals(listOf(1L), StoryRecordWire.decode(mixed, knowledgeQuery).entries.first().eventSources)
            for ((index, source) in listOf(JSONObject().put("kind", "event").put("value", 0),
                JSONObject().put("kind", "event").put("value", 5), JSONObject().put("kind", "event").put("value", "1"),
                JSONObject().put("kind", "unknown").put("value", "PRIVATE-SOURCE-CANARY")).withIndex()) {
                val page = JSONObject(knowledge.toString())
                jsonRows(page).first().put("sources", JSONArray().put(source))
                assertInvalidEventPage(page, knowledgeQuery, 30 + index)
            }
            assertTrue(accepted == owner.acceptedView())
            assertEquals(turnCalls, owner.transport.turnCalls.get())
        }
    }
}

private fun jsonRows(page: JSONObject): List<JSONObject> = page.getJSONArray("rows").let { rows ->
    (0 until rows.length()).map { rows.getJSONObject(it) }
}

private fun assertInvalidEventPage(page: JSONObject, query: StoryRecordQuery, index: Int) {
    try { StoryRecordWire.decode(page, query); fail("Malformed event/source accepted at case $index") }
    catch (failure: StoryRecordFailure) {
        assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem)
        assertEquals("Story record unavailable", failure.message)
    }
}

internal suspend fun seedEventScenes(owner: RecordOwner): SavedSnapshot {
    assertEquals(0L, owner.gateway.initialize().revision)
    assertTrue(owner.gateway.commitAsync(owner.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)) is DemoResult.Accepted)
    owner.commitIntent(JSONObject().put("kind", "actions").put("value", JSONArray().put(JSONObject().put("op", "move").put("to", "pier"))))
    owner.commitIntent(JSONObject().put("kind", "actions").put("value", JSONArray()
        .put(JSONObject().put("op", "give").put("item", "brass-key").put("to", "oren").put("quantity", 1))
        .put(JSONObject().put("op", "complete_promise").put("id", "return-key"))))
    return owner.gateway.snapshot().also { assertEquals(4L, it.revision) }
}

internal suspend fun eventModel(fixture: RecordFixture, owner: RecordOwner): ShellViewModel = withContext(Dispatchers.Main) {
    val store = ViewModelStore().also { fixture.stores += it }
    ViewModelProvider(store, object : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = ShellViewModel(owner.gateway) as T
    })[ShellViewModel::class.java]
}

internal suspend fun awaitEventShell(model: ShellViewModel) = withTimeout(8_000) {
    while (model.state.value.busy || model.state.value.selectedStory == null) delay(5)
    assertFalse(model.state.value.recoveryRequired)
}

internal suspend fun awaitEventRecord(model: ShellViewModel, predicate: (StoryRecordState) -> Boolean = { true }): StoryRecordState = withTimeout(8_000) {
    while (true) {
        val state = model.storyRecord.value
        if (state.visible && !state.loading && state.problem == null && predicate(state)) return@withTimeout state
        delay(5)
    }
    @Suppress("UNREACHABLE_CODE") error("Unreachable")
}
