/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Real adapters and owners, synthetic transport. Native tests own eligibility and cursor proofs. */
@OptIn(ExperimentalCoroutinesApi::class)
class RelationshipFocusBrowseTest {
    private val story = SavedStory("reed-quay", "main", "Reed Quay", 12)
    private val other = story.copy(story = "other-quay", title = "Other Quay")
    private val context = StoryRecordContext(story, 12)
    private val upper = StoryRecordRelationshipTarget("Mira")
    private val lower = StoryRecordRelationshipTarget("mira")
    private val prefix = StoryRecordRelationshipTarget("mira-east")
    private val next = "2:8:${"c".repeat(64)}"
    private val dimensions = listOf("respect", "trust", "obligation")

    private fun query(target: StoryRecordRelationshipTarget? = null) =
        StoryRecordQuery(context, StoryRecordSection.RELATIONSHIPS, relationshipTarget = target)

    private fun reference(ctx: StoryRecordContext) =
        StoryRecordScopedEvent(StoryRecordScope(ctx.story.story, "ancestor"), 2)

    private fun row(target: String, dimension: String = "trust", value: Any = -7,
                    from: String = "player", storyId: String = story.story) =
        JSONObject().put("kind", "relationship").put("key", "relationship:$target:$dimension")
            .put("from", from).put("to", target).put("dimension", dimension).put("value", value)
            .put("origin", "canonical_field").put("source", JSONObject().put("kind", "scoped_event")
                .put("value", JSONObject().put("original_scope", JSONObject()
                    .put("story", storyId).put("branch", "ancestor")).put("sequence", 2)))

    private fun data(q: StoryRecordQuery, rows: List<JSONObject>, total: Int = rows.size,
                     cursor: String? = null) = JSONObject().put("version", q.version)
        .put("scope", JSONObject().put("story", q.context.story.story).put("branch", q.context.story.branch))
        .put("head", q.context.revision).put("revision", q.context.revision).put("story_time", 50)
        .put("observer", JSONObject().put("kind", "player")).put("privacy", "player_visible")
        .put("status", "supported").put("view", q.section.wire).put("total", total)
        .put("rows", JSONArray(rows)).put("next_cursor", cursor ?: JSONObject.NULL)
        .put("unsupported", JSONArray())

    private fun rejected(q: StoryRecordQuery, response: JSONObject) {
        try {
            StoryRecordWire.decode(response, q)
            fail("An invalid relationship response must reject the whole page")
        } catch (failure: StoryRecordFailure) {
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem)
            assertFalse(failure.message.orEmpty().contains("PRIVATE_RELATIONSHIP_69"))
        }
    }

    private fun answer(q: StoryRecordQuery): StoryRecordPage {
        val source = reference(q.context)
        if (q.section == StoryRecordSection.HISTORY && q.search.startsWith("\"event\":")) {
            return StoryRecordPage(q, 50, 1, listOf(StoryRecordEntry("observed-event-2", "Event #2",
                "An accepted relationship change was witnessed.", StoryRecordOrigin.RECORDED_OBSERVATION,
                event = StoryRecordEvent(2, "relationship-turn", 40, source.originalScope),
                scopedEventSources = listOf(source))), null)
        }
        if (q.section != StoryRecordSection.RELATIONSHIPS)
            return StoryRecordPage(q, 50, 0, emptyList(), null)
        // A focused target has the engine's three supported dimensions. ALL spans pages.
        val targets = q.relationshipTarget?.let { listOf(it) } ?: listOf(upper, lower, prefix)
        val all = targets.flatMap { target -> dimensions.mapIndexed { index, dimension ->
            row(target.id, dimension, index - 1, storyId = q.context.story.story)
        } }
        val offset = if (q.cursor == null) 0 else 8
        val selected = all.drop(offset).take(8)
        val cursor = if (offset + selected.size < all.size) next else null
        return StoryRecordWire.decode(data(q, selected, all.size, cursor), q)
    }

    @Test fun focusUsesTheTypedNativeOperationAndPreservesCaseWithoutChangingOrdinarySearch() {
        for (target in listOf(upper, lower, prefix, StoryRecordRelationshipTarget("A_9-x"))) {
            val q = query(target)
            val command = StoryRecordWire.command("retained-session", q)
            assertEquals(setOf("op", "session", "query", "target"), command.keys().asSequence().toSet())
            assertEquals("inspection_relationship_focus", command.getString("op"))
            assertEquals("retained-session", command.getString("session"))
            assertEquals(target.id, command.getString("target"))
            val wire = command.getJSONObject("query")
            assertEquals("", wire.getString("search"))
            assertEquals("relationships", wire.getString("view"))
            assertEquals(2, wire.getInt("version"))
            assertEquals(12L, wire.getLong("expected_head"))
            assertEquals("player", wire.getJSONObject("observer").getString("kind"))
            assertEquals(setOf("version", "scope", "expected_head", "at_revision", "observer", "view",
                "limit", "search", "cursor"), wire.keys().asSequence().toSet())
        }
        val text = "MIRA sea-wall 海"
        val ordinary = StoryRecordWire.command("s", query().copy(search = text))
        assertEquals("inspection_query", ordinary.getString("op"))
        assertFalse(ordinary.has("target"))
        assertEquals(text, ordinary.getJSONObject("query").getString("search"))
        assertEquals("inspection_query", StoryRecordWire.command("s", query().copy(version = 1)).getString("op"))
    }

    @Test fun malformedTargetsAndUnsupportedCombinationsCannotBecomeAnotherQuery() {
        val invalid = listOf("", "x".repeat(65), "mira ", "mira/hidden", "mira\"", "é", "mira\n")
            .map { query(StoryRecordRelationshipTarget(it)) } +
            listOf(query(upper).copy(version = 1), query(upper).copy(search = "Mira"),
                query(upper).copy(promiseFilter = StoryRecordPromiseFilter.OPEN)) +
            StoryRecordSection.entries.filter { it != StoryRecordSection.RELATIONSHIPS }
                .map { query(upper).copy(section = it) }
        for (q in invalid) {
            try {
                StoryRecordWire.command("s", q)
                fail("Unsupported focus must not silently dispatch a generic or privileged query")
            } catch (failure: StoryRecordFailure) {
                assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem)
            }
            rejected(q, data(q, emptyList()))
        }
    }

    @Test fun typedTargetsRetainNativeCaseValuesAndOriginalEvidenceWithoutInventingAProfile() {
        val q = query()
        val original = data(q, listOf(row("Mira"), row("mira"), row("mira-east")))
        val before = original.toString()
        val entries = StoryRecordWire.decode(original, q).entries
        assertEquals(listOf(upper, lower, prefix), entries.map { it.relationshipTarget })
        assertEquals(listOf("Mira · trust", "mira · trust", "mira-east · trust"), entries.map { it.title })
        for (entry in entries) {
            assertEquals("-7", entry.text)
            assertEquals(StoryRecordOrigin.CANONICAL_FIELD, entry.origin)
            assertEquals(listOf(reference(context)), entry.scopedEventSources)
            assertTrue(entry.eventSources.isEmpty())
            assertNull(entry.event)
            assertNull(entry.promiseStatus)
            assertFalse(entry.text.contains("name"))
        }
        assertEquals(before, original.toString())
        assertNull(StoryRecordEntry("field", "Mira", "trust", StoryRecordOrigin.CANONICAL_FIELD).relationshipTarget)
    }

    @Test fun wrongCasePrivateActorMalformedValueOrSourceRejectsTheWholeFocusedPage() {
        val q = query(upper)
        for (target in listOf("mira", "Mira-east", "PRIVATE_RELATIONSHIP_69"))
            rejected(q, data(q, listOf(row("Mira", "respect"), row(target))))
        rejected(q, data(q, listOf(row("Mira", from = "mira"))))
        rejected(q, data(q, listOf(row("Mira").put("origin", "subjective_belief"))))
        rejected(q, data(q, listOf(row("Mira", value = 32768))))
        rejected(q, data(q, listOf(row("Mira", value = "12"))))
        rejected(q, data(q, listOf(row("Mira", storyId = "foreign-story"))))
        rejected(q, data(q, listOf(row("Mira").put("dimension", "secret-motivation"))))
        rejected(q, data(q, listOf(row("Mira"))).put("privacy", "private_character"))
        rejected(q, data(q, listOf(row("Mira"))).put("observer", JSONObject().put("kind", "omniscient")))
        for (bad in listOf<Any>("", "x".repeat(65), "mira/secret", true, JSONObject.NULL))
            rejected(query(), data(query(), listOf(row("Mira").put("to", bad))))
    }

    @Test fun selectingALaterAllPageEntryRequestsAllThreeNativeDimensionsFromPageOne() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; answer(q) }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
        assertEquals(9, controller.state.value.total)
        assertEquals(8, controller.state.value.entries.size)
        controller.next(); advanceUntilIdle()
        val last = controller.state.value.entries.single()
        assertEquals(prefix, last.relationshipTarget)
        assertEquals(next, controller.state.value.cursor)
        controller.focusRelationship(last); advanceUntilIdle()
        assertEquals(prefix, calls.last().relationshipTarget)
        assertNull(calls.last().cursor)
        assertEquals("", calls.last().search)
        assertEquals(3, controller.state.value.total)
        assertEquals(3, controller.state.value.entries.size)
        assertTrue(controller.state.value.entries.all { it.relationshipTarget == prefix })
        assertEquals(setOf("mira-east · respect", "mira-east · trust", "mira-east · obligation"),
            controller.state.value.entries.map { it.title }.toSet())
        assertNull(controller.state.value.nextCursor)
        controller.first(); advanceUntilIdle()
        assertEquals(prefix, calls.last().relationshipTarget)
        assertNull(calls.last().cursor)
        controller.dispose()
    }

    @Test fun explicitAllFreeSearchAndSectionChangesClearFocusInsteadOfCombiningFilters() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; answer(q) }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
        controller.search("mira"); advanceUntilIdle()
        controller.focusRelationship(controller.state.value.entries.first()); advanceUntilIdle()
        assertEquals("", calls.last().search)
        assertEquals(upper, controller.state.value.relationshipTarget)
        controller.allRelationships(); advanceUntilIdle()
        assertNull(calls.last().relationshipTarget)
        assertEquals("", calls.last().search)
        assertEquals(9, controller.state.value.total)
        controller.focusRelationship(controller.state.value.entries.first()); advanceUntilIdle()
        controller.search("MIRA"); advanceUntilIdle()
        assertNull(calls.last().relationshipTarget)
        assertEquals("MIRA", calls.last().search)
        controller.focusRelationship(controller.state.value.entries.first()); advanceUntilIdle()
        controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
        assertNull(calls.last().relationshipTarget)
        assertEquals(StoryRecordSection.KNOWLEDGE, calls.last().section)
        controller.dispose()
    }

    @Test fun retryAndInheritedEvidenceBackKeepTheFocusedNativePage() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        var failNext = false
        val controller = StoryRecordController({ q ->
            calls += q
            if (failNext) { failNext = false; throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE) }
            answer(q)
        }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
        failNext = true
        controller.focusRelationship(controller.state.value.entries.first()); advanceUntilIdle()
        assertEquals(upper, controller.state.value.relationshipTarget)
        assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
        controller.retry(); advanceUntilIdle()
        assertEquals(upper, calls.last().relationshipTarget)
        val before = controller.state.value
        controller.openScopedEvent(reference(context)); advanceUntilIdle()
        assertEquals(StoryRecordSection.HISTORY, calls.last().section)
        assertNull(calls.last().relationshipTarget)
        assertEquals(reference(context).originalScope, controller.state.value.eventDetail!!.entry!!.event!!.originalScope)
        val reads = calls.size
        controller.back(); advanceUntilIdle()
        assertEquals(reads, calls.size)
        assertEquals(before, controller.state.value)
        assertEquals(upper, controller.state.value.relationshipTarget)
        controller.dispose()
    }

    @Test fun copiedForgedAndEarlierPageEntriesCannotAcquireFocusAuthority() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; answer(q) }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
        val current = controller.state.value
        val entry = current.entries.first()
        for (forged in listOf(entry.copy(), entry.copy(relationshipTarget = lower),
            entry.copy(key = "unseen", relationshipTarget = StoryRecordRelationshipTarget("hidden")),
            StoryRecordEntry("plain", "Mira", "respect", StoryRecordOrigin.CANONICAL_FIELD))) {
            val count = calls.size
            controller.focusRelationship(forged); advanceUntilIdle()
            assertEquals(count, calls.size)
            assertSame(current, controller.state.value)
        }
        controller.next(); advanceUntilIdle()
        val later = controller.state.value
        val count = calls.size
        controller.focusRelationship(entry); advanceUntilIdle()
        assertEquals(count, calls.size)
        assertSame(later, controller.state.value)
        controller.focusRelationship(later.entries.single()); advanceUntilIdle()
        assertEquals(prefix, controller.state.value.relationshipTarget)
        controller.dispose()
    }

    @Test fun typedReaderWrongTargetsAndFocusDuringEvidenceCannotReplaceTheCurrentView() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        var poison = true
        val controller = StoryRecordController({ q ->
            calls += q
            if (poison && q.relationshipTarget != null) {
                StoryRecordPage(q, 50, 1, listOf(StoryRecordEntry("wrong-target", "Mira · trust", "7",
                    StoryRecordOrigin.CANONICAL_FIELD, relationshipTarget = lower)), null)
            } else answer(q)
        }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
        controller.focusRelationship(controller.state.value.entries.first()); advanceUntilIdle()
        assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
        assertTrue(controller.state.value.entries.isEmpty())
        assertEquals(0, controller.state.value.total)
        poison = false; controller.retry(); advanceUntilIdle()
        val entry = controller.state.value.entries.first()
        controller.openScopedEvent(reference(context)); advanceUntilIdle()
        val detail = controller.state.value
        val count = calls.size
        controller.focusRelationship(entry); controller.allRelationships(); advanceUntilIdle()
        assertSame(detail, controller.state.value)
        assertEquals(count, calls.size)
        controller.dispose()
    }

    @Test fun loadingAndNoncooperativeFocusReadCannotRetargetANewerBranch() = runTest {
        val release = CompletableDeferred<Unit>()
        val calls = mutableListOf<StoryRecordQuery>()
        var hold = false
        val controller = StoryRecordController({ q ->
            calls += q
            if (hold) { hold = false; withContext(NonCancellable) { release.await() } }
            answer(q)
        }, this)
        try {
            controller.open(context); advanceUntilIdle()
            controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
            val old = controller.state.value.entries.first()
            hold = true; controller.focusRelationship(old); runCurrent()
            assertTrue(controller.state.value.loading)
            val count = calls.size
            controller.focusRelationship(old); controller.allRelationships(); runCurrent()
            assertEquals(count, calls.size)
            controller.dismiss(); controller.open(context.copy(story = story.copy(branch = "child"))); runCurrent()
            controller.select(StoryRecordSection.RELATIONSHIPS); runCurrent()
            val lowerEntry = controller.state.value.entries.first { it.relationshipTarget == lower }
            controller.focusRelationship(lowerEntry); runCurrent()
            val current = controller.state.value
            assertEquals("child", current.context!!.story.branch)
            assertEquals(lower, current.relationshipTarget)
            release.complete(Unit); advanceUntilIdle()
            assertSame(current, controller.state.value)
        } finally { release.complete(Unit); controller.dispose() }
    }

    @Test fun noncooperativeReadCompletingAfterDisposalCannotReopenTheRelationshipView() = runTest {
        val release = CompletableDeferred<Unit>()
        var hold = false
        val controller = StoryRecordController({ q ->
            if (hold) { hold = false; withContext(NonCancellable) { release.await() } }
            answer(q)
        }, this)
        try {
            controller.open(context); advanceUntilIdle()
            controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
            val entry = controller.state.value.entries.first()
            hold = true; controller.focusRelationship(entry); runCurrent()
            controller.dispose()
            val disposed = controller.state.value
            release.complete(Unit); advanceUntilIdle()
            controller.focusRelationship(entry); controller.allRelationships(); advanceUntilIdle()
            assertSame(disposed, controller.state.value)
            assertFalse(disposed.visible)
        } finally { release.complete(Unit); controller.dispose() }
    }

    private inner class Gateway : DemoGateway {
        override val durable = true
        override val storyRecords = true
        var selected = story
        val calls = mutableListOf<StoryRecordQuery>()
        var responses = 0
        var commits = 0
        var closes = 0
        private fun saved() = SavedSnapshot(selected.revision, "You", emptyList(),
            "D:/synthetic/relationship-focus", 1, listOf(story, other), selected)
        override suspend fun initialize() = saved()
        override suspend fun snapshot() = saved()
        override suspend fun recoverSaved() = saved()
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { selected = story; return saved() }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage { calls += query; return answer(query) }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            responses++; return DemoResult.Rejected("Unsupported")
        }
        override fun commit(result: DemoResult): DemoResult { commits++; return result }
        override fun close() { closes++ }
    }

    @Test fun renderedCopyEarlierPageAndOtherStoryCallbacksStayQuietWhileFreshFocusWorks() = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        val store = ViewModelStore()
        try {
            val gateway = Gateway()
            val model = ShellViewModel(gateway).also { store.put("relationships", it) }
            advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
            model.recordSection(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
            val old = model.storyRecord.value
            val entry = old.entries.first()
            val count = gateway.calls.size
            model.focusRecordRelationship(entry, old.copy()); advanceUntilIdle()
            model.focusRecordRelationship(entry.copy(), old); advanceUntilIdle()
            assertSame(old, model.storyRecord.value)
            assertEquals(count, gateway.calls.size)
            val retained = { model.focusRecordRelationship(entry, old) }
            model.nextRecordPage(); advanceUntilIdle()
            val later = model.storyRecord.value
            val laterReads = gateway.calls.size
            retained(); advanceUntilIdle()
            assertSame(later, model.storyRecord.value)
            assertEquals(laterReads, gateway.calls.size)
            model.focusRecordRelationship(later.entries.single(), later); advanceUntilIdle()
            assertEquals(prefix, model.storyRecord.value.relationshipTarget)
            val focused = model.storyRecord.value
            val retainedClear = { model.allRecordRelationships(focused) }
            model.resume(other); advanceUntilIdle()
            model.openStoryRecord(); advanceUntilIdle(); model.recordSection(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
            val foreign = model.storyRecord.value
            val foreignReads = gateway.calls.size
            retained(); retainedClear(); advanceUntilIdle()
            assertSame(foreign, model.storyRecord.value)
            assertEquals(foreignReads, gateway.calls.size)
            assertEquals(0, gateway.responses); assertEquals(0, gateway.commits)
        } finally { store.clear(); Dispatchers.resetMain() }
    }

    @Test fun closeEqualValuedReopenAndViewModelDisposalRejectRetainedFocusAndClearActions() = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        val store = ViewModelStore()
        try {
            val gateway = Gateway()
            val model = ShellViewModel(gateway).also { store.put("relationships", it) }
            advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
            model.recordSection(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
            val old = model.storyRecord.value
            val retained = { model.focusRecordRelationship(old.entries.first(), old) }
            model.closeStoryRecord(); advanceUntilIdle()
            val closed = model.storyRecord.value
            val count = gateway.calls.size
            retained(); advanceUntilIdle()
            assertSame(closed, model.storyRecord.value)
            assertEquals(count, gateway.calls.size)
            model.openStoryRecord(); advanceUntilIdle(); model.recordSection(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
            val reopened = model.storyRecord.value
            assertEquals(old, reopened); assertNotSame(old, reopened)
            val reopenedReads = gateway.calls.size
            retained(); advanceUntilIdle()
            assertSame(reopened, model.storyRecord.value)
            assertEquals(reopenedReads, gateway.calls.size)
            model.focusRecordRelationship(reopened.entries.first(), reopened); advanceUntilIdle()
            val focused = model.storyRecord.value
            val retainedClear = { model.allRecordRelationships(focused) }
            store.clear()
            val disposed = model.storyRecord.value
            retainedClear(); model.focusRecordRelationship(focused.entries.first()); model.allRecordRelationships()
            advanceUntilIdle()
            assertSame(disposed, model.storyRecord.value)
            assertEquals(1, gateway.closes)
            assertEquals(0, gateway.responses); assertEquals(0, gateway.commits)
        } finally { store.clear(); Dispatchers.resetMain() }
    }
}
