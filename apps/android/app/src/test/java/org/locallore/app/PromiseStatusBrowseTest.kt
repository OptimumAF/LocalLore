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

/** Synthetic transport rows test the real adapter. Rust remains the promise/status authority. */
@OptIn(ExperimentalCoroutinesApi::class)
class PromiseStatusBrowseTest {
    private val story = SavedStory("bell-quay", "main", "Bell Quay", 12)
    private val context = StoryRecordContext(story, 12)
    private val next = "2:8:${"b".repeat(64)}"
    private val inherited = StoryRecordScopedEvent(StoryRecordScope(story.story, "ancestor"), 2)

    private fun query(filter: StoryRecordPromiseFilter = StoryRecordPromiseFilter.ALL) =
        StoryRecordQuery(context, StoryRecordSection.PROMISES, promiseFilter = filter)

    private fun row(id: String, status: String = "open", from: String = "player", to: String = "mira",
                    storyId: String = story.story) =
        JSONObject().put("kind", "promise").put("key", "promise:$id").put("id", id)
            .put("from", from).put("to", to)
            .put("terms", "Keep the open market gate overdue sign; literal \"status\":\"open\" is prose.")
            .put("deadline", "18446744073709551615").put("status", status)
            .put("return_item", JSONObject.NULL).put("origin", "derived_comparison")
            .put("sources", JSONArray().put(JSONObject().put("kind", "scoped_event")
                .put("value", JSONObject().put("original_scope", JSONObject()
                    .put("story", storyId).put("branch", "ancestor")).put("sequence", 2))))

    private fun data(q: StoryRecordQuery, rows: List<JSONObject>, total: Int = rows.size,
                     cursor: String? = null) = JSONObject().put("version", q.version)
        .put("scope", JSONObject().put("story", q.context.story.story).put("branch", q.context.story.branch))
        .put("head", q.context.revision).put("revision", q.context.revision).put("story_time", 100)
        .put("observer", JSONObject().put("kind", "player")).put("privacy", "player_visible")
        .put("status", "supported").put("view", q.section.wire).put("total", total)
        .put("rows", JSONArray(rows)).put("next_cursor", cursor ?: JSONObject.NULL)
        .put("unsupported", JSONArray())

    private fun rejected(q: StoryRecordQuery, response: JSONObject) {
        try {
            StoryRecordWire.decode(response, q)
            fail("Invalid filtered promise response must fail closed")
        } catch (failure: StoryRecordFailure) {
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem)
            assertFalse(failure.message.orEmpty().contains("market gate"))
        }
    }

    private fun status(filter: StoryRecordPromiseFilter) = when (filter) {
        StoryRecordPromiseFilter.ALL, StoryRecordPromiseFilter.OPEN -> "open"
        StoryRecordPromiseFilter.OVERDUE -> "overdue"
    }

    private fun answer(q: StoryRecordQuery): StoryRecordPage {
        if (q.section == StoryRecordSection.HISTORY && q.search.startsWith("\"event\":")) {
            return StoryRecordPage(q, 100, 1, listOf(StoryRecordEntry("event-2", "Event #2",
                "An observed promise was recorded.", StoryRecordOrigin.RECORDED_OBSERVATION,
                event = StoryRecordEvent(2, "observed-turn", 90, inherited.originalScope),
                scopedEventSources = listOf(inherited))), null)
        }
        if (q.section != StoryRecordSection.PROMISES) return StoryRecordPage(q, 100, 0, emptyList(), null)
        val rows = if (q.cursor == null) (0 until 8).map {
            row("${q.promiseFilter.name}-$it", status(q.promiseFilter), storyId = q.context.story.story)
        } else listOf(row("${q.promiseFilter.name}-8", status(q.promiseFilter), storyId = q.context.story.story))
        return StoryRecordWire.decode(data(q, rows, 9, if (q.cursor == null) next else null), q)
    }

    @Test fun presetCommandsUseExactNativeStatusTokensWithoutExposingThemAsTheUserSearch() {
        for ((filter, expected) in listOf(StoryRecordPromiseFilter.ALL to "",
            StoryRecordPromiseFilter.OPEN to "\"status\":\"open\"",
            StoryRecordPromiseFilter.OVERDUE to "\"status\":\"overdue\"")) {
            val q = query(filter)
            val wire = StoryRecordWire.command("retained-session", q).getJSONObject("query")
            assertEquals("", q.search)
            assertEquals(expected, wire.getString("search"))
            assertEquals("promises", wire.getString("view"))
            assertEquals(2, wire.getInt("version"))
            assertEquals(8, wire.getInt("limit"))
            assertEquals(12L, wire.getLong("expected_head"))
            assertEquals("player", wire.getJSONObject("observer").getString("kind"))
            assertEquals(setOf("version", "scope", "expected_head", "at_revision", "observer", "view", "limit", "search", "cursor"),
                wire.keys().asSequence().toSet())
        }
        val literal = "open overdue % '_ 海"
        assertEquals(literal, StoryRecordWire.command("s", query().copy(search = literal))
            .getJSONObject("query").getString("search"))
    }

    @Test fun presetsCannotBeSilentlyCombinedWithFreeTextLegacyQueriesOrAnotherSection() {
        val invalid = listOf(query(StoryRecordPromiseFilter.OPEN).copy(search = "open"),
            query(StoryRecordPromiseFilter.OVERDUE).copy(version = 1)) +
            StoryRecordSection.entries.filter { it != StoryRecordSection.PROMISES }.map {
                query(StoryRecordPromiseFilter.OPEN).copy(section = it)
            }
        for (q in invalid) {
            try {
                StoryRecordWire.command("s", q)
                fail("An unsupported preset must not dispatch a different native query")
            } catch (failure: StoryRecordFailure) {
                assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem)
            }
            rejected(q, data(q, emptyList()))
        }
    }

    @Test fun typedStatusesComeOnlyFromNativeRowsEvenWhenTheTermsAndClockSuggestSomethingElse() {
        for ((wire, expected) in listOf("open" to StoryRecordPromiseStatus.OPEN,
            "overdue" to StoryRecordPromiseStatus.OVERDUE, "fulfilled" to StoryRecordPromiseStatus.FULFILLED)) {
            val original = row("same-metadata", wire).put("deadline", "0")
            val before = original.toString()
            val entry = StoryRecordWire.decode(data(query(), listOf(original)), query()).entries.single()
            assertEquals(expected, entry.promiseStatus)
            assertTrue(entry.text.contains("Status · ${expected.label}"))
            assertTrue(entry.text.contains("Due at story time · 0"))
            assertEquals(before, original.toString())
        }
        val plain = StoryRecordEntry("field", "Status", "Open overdue fulfilled", StoryRecordOrigin.CANONICAL_FIELD)
        assertNull(plain.promiseStatus)
    }

    @Test fun invalidStatusesMismatchedPresetAndPrivatePartiesRefuseTheWholeNativePage() {
        val open = query(StoryRecordPromiseFilter.OPEN)
        for (bad in listOf<Any>("OPEN", "pending", 1, true, JSONObject.NULL))
            rejected(open, data(open, listOf(row("bad").put("status", bad))))
        rejected(open, data(open, listOf(row("looks-open-in-terms", "fulfilled"))))
        rejected(query(StoryRecordPromiseFilter.OVERDUE),
            data(query(StoryRecordPromiseFilter.OVERDUE), listOf(row("not-overdue", "open"))))
        rejected(open, data(open, listOf(row("hidden", from = "mira", to = "oren"))))
        rejected(open, data(open, listOf(row("good"), row("mismatched", "overdue"))))
    }

    @Test fun filteredRowsKeepExactUnsignedDeadlinesAndInheritedEvidenceWithoutFlattening() {
        val q = query(StoryRecordPromiseFilter.OVERDUE)
        val entry = StoryRecordWire.decode(data(q, listOf(row("incoming", "overdue", "mira", "player"))), q)
            .entries.single()
        assertEquals(StoryRecordPromiseStatus.OVERDUE, entry.promiseStatus)
        assertTrue(entry.text.contains("Due at story time · 18446744073709551615"))
        assertEquals(listOf(inherited), entry.scopedEventSources)
        assertTrue(entry.eventSources.isEmpty())
        assertEquals(listOf("Event #2 · bell-quay / ancestor"), entry.sources)
        assertEquals(StoryRecordOrigin.DERIVED_COMPARISON, entry.origin)
    }

    @Test fun presetPagingPreservesNativeCountsAndRestartsFromTheFirstPageOnSelection() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; answer(q) }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.PROMISES); advanceUntilIdle()
        controller.promiseFilter(StoryRecordPromiseFilter.OPEN); advanceUntilIdle()
        assertEquals(9, controller.state.value.total)
        assertEquals(8, controller.state.value.entries.size)
        controller.next(); advanceUntilIdle()
        assertEquals(next, calls.last().cursor)
        assertEquals(StoryRecordPromiseFilter.OPEN, calls.last().promiseFilter)
        assertEquals(1, controller.state.value.entries.size)
        assertEquals(9, controller.state.value.total)
        controller.promiseFilter(StoryRecordPromiseFilter.OVERDUE); advanceUntilIdle()
        assertNull(calls.last().cursor)
        assertEquals(StoryRecordPromiseFilter.OVERDUE, controller.state.value.promiseFilter)
        assertTrue(controller.state.value.entries.all { it.promiseStatus == StoryRecordPromiseStatus.OVERDUE })
        controller.next(); advanceUntilIdle(); controller.first(); advanceUntilIdle()
        assertNull(calls.last().cursor)
        assertEquals(StoryRecordPromiseFilter.OVERDUE, calls.last().promiseFilter)
        assertTrue(calls.all { it.context == context })
        controller.dispose()
    }

    @Test fun freeSearchAndSectionChangesClearThePresetWhilePresetSelectionClearsFreeSearch() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; answer(q) }, this)
        controller.open(context); advanceUntilIdle()
        val reads = calls.size
        controller.promiseFilter(StoryRecordPromiseFilter.OPEN); advanceUntilIdle()
        assertEquals(reads, calls.size)
        controller.select(StoryRecordSection.PROMISES); advanceUntilIdle()
        controller.search("overdue sign 海"); advanceUntilIdle()
        controller.promiseFilter(StoryRecordPromiseFilter.OPEN); advanceUntilIdle()
        assertEquals("", calls.last().search)
        assertEquals(StoryRecordPromiseFilter.OPEN, calls.last().promiseFilter)
        controller.search("open market"); advanceUntilIdle()
        assertEquals("open market", calls.last().search)
        assertEquals(StoryRecordPromiseFilter.ALL, calls.last().promiseFilter)
        controller.promiseFilter(StoryRecordPromiseFilter.OVERDUE); advanceUntilIdle()
        controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
        assertEquals(StoryRecordPromiseFilter.ALL, calls.last().promiseFilter)
        assertEquals("", calls.last().search)
        controller.dispose()
    }

    @Test fun retryAndInheritedEventBackPreserveThePresetPageWithoutAnExtraListRead() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        var failNext = false
        val controller = StoryRecordController({ q ->
            calls += q
            if (failNext) { failNext = false; throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE) }
            answer(q)
        }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.PROMISES); advanceUntilIdle()
        controller.promiseFilter(StoryRecordPromiseFilter.OVERDUE); advanceUntilIdle()
        failNext = true; controller.next(); advanceUntilIdle()
        assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
        controller.retry(); advanceUntilIdle()
        assertEquals(next, calls.last().cursor)
        assertEquals(StoryRecordPromiseFilter.OVERDUE, calls.last().promiseFilter)
        val before = controller.state.value
        controller.openScopedEvent(inherited); advanceUntilIdle()
        assertEquals(StoryRecordSection.HISTORY, calls.last().section)
        assertEquals(StoryRecordPromiseFilter.ALL, calls.last().promiseFilter)
        assertEquals(inherited.originalScope, controller.state.value.eventDetail!!.entry!!.event!!.originalScope)
        val reads = calls.size
        controller.back(); advanceUntilIdle()
        assertEquals(reads, calls.size)
        assertEquals(before, controller.state.value)
        assertEquals(StoryRecordPromiseFilter.OVERDUE, controller.state.value.promiseFilter)
        controller.dispose()
    }

    @Test fun aTypedReaderCannotSmuggleAnotherStatusIntoAFilteredPage() = runTest {
        val controller = StoryRecordController({ q ->
            if (q.section != StoryRecordSection.PROMISES) answer(q)
            else if (q.promiseFilter == StoryRecordPromiseFilter.ALL) answer(q)
            else StoryRecordPage(q, 100, 1, listOf(StoryRecordEntry("wrong-status", "Promise", "Status · Open",
                StoryRecordOrigin.DERIVED_COMPARISON, promiseStatus = StoryRecordPromiseStatus.FULFILLED)), null)
        }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.PROMISES); advanceUntilIdle()
        controller.promiseFilter(StoryRecordPromiseFilter.OPEN); advanceUntilIdle()
        assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
        assertTrue(controller.state.value.entries.isEmpty())
        assertEquals(0, controller.state.value.total)
        controller.dispose()
    }

    @Test fun loadingAndNoncooperativeOldPresetReadsCannotChangeANewerBranchOrItsFilter() = runTest {
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
            controller.select(StoryRecordSection.PROMISES); advanceUntilIdle()
            hold = true; controller.promiseFilter(StoryRecordPromiseFilter.OPEN); runCurrent()
            assertTrue(controller.state.value.loading)
            val count = calls.size
            controller.promiseFilter(StoryRecordPromiseFilter.OVERDUE); runCurrent()
            assertEquals(count, calls.size)
            controller.dismiss(); controller.open(context.copy(story = story.copy(branch = "child"))); runCurrent()
            controller.select(StoryRecordSection.PROMISES); runCurrent()
            controller.promiseFilter(StoryRecordPromiseFilter.OVERDUE); runCurrent()
            val current = controller.state.value
            assertEquals("child", current.context!!.story.branch)
            assertEquals(StoryRecordPromiseFilter.OVERDUE, current.promiseFilter)
            release.complete(Unit); advanceUntilIdle()
            assertSame(current, controller.state.value)
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
            "D:/synthetic/promise-status", 1, listOf(story, story.copy(story = "other")), selected)
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

    @Test fun retainedPresetCallbacksRejectEqualCopiesLaterPagesAndOtherStoryViews() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        val store = ViewModelStore()
        try {
            val gateway = Gateway()
            val model = ShellViewModel(gateway).also { store.put("promises", it) }
            advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
            model.recordSection(StoryRecordSection.PROMISES); advanceUntilIdle()
            val rendered = model.storyRecord.value
            val reads = gateway.calls.size
            model.recordPromiseFilter(StoryRecordPromiseFilter.OPEN, rendered.copy()); advanceUntilIdle()
            assertSame(rendered, model.storyRecord.value)
            assertEquals(reads, gateway.calls.size)
            model.recordPromiseFilter(StoryRecordPromiseFilter.OPEN, rendered); advanceUntilIdle()
            assertEquals(StoryRecordPromiseFilter.OPEN, model.storyRecord.value.promiseFilter)
            model.nextRecordPage(); advanceUntilIdle()
            val currentPage = model.storyRecord.value
            val oldAction = { model.recordPromiseFilter(StoryRecordPromiseFilter.OVERDUE, rendered) }
            val pageReads = gateway.calls.size
            oldAction(); advanceUntilIdle()
            assertSame(currentPage, model.storyRecord.value)
            assertEquals(pageReads, gateway.calls.size)
            model.resume(story.copy(story = "other")); advanceUntilIdle()
            model.openStoryRecord(); advanceUntilIdle(); model.recordSection(StoryRecordSection.PROMISES); advanceUntilIdle()
            val other = model.storyRecord.value
            val otherReads = gateway.calls.size
            oldAction(); advanceUntilIdle()
            assertSame(other, model.storyRecord.value)
            assertEquals(otherReads, gateway.calls.size)
            assertEquals(0, gateway.responses); assertEquals(0, gateway.commits)
        } finally { store.clear(); Dispatchers.resetMain() }
    }

    @Test fun closedReopenedAndDisposedViewsCannotUseRetainedPresetActions() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        val store = ViewModelStore()
        try {
            val gateway = Gateway()
            val model = ShellViewModel(gateway).also { store.put("promises", it) }
            advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
            model.recordSection(StoryRecordSection.PROMISES); advanceUntilIdle()
            val old = model.storyRecord.value
            val retained = { model.recordPromiseFilter(StoryRecordPromiseFilter.OPEN, old) }
            model.closeStoryRecord(); advanceUntilIdle()
            val closed = model.storyRecord.value
            val closedReads = gateway.calls.size
            retained(); advanceUntilIdle()
            assertSame(closed, model.storyRecord.value)
            assertEquals(closedReads, gateway.calls.size)
            model.openStoryRecord(); advanceUntilIdle(); model.recordSection(StoryRecordSection.PROMISES); advanceUntilIdle()
            val reopened = model.storyRecord.value
            assertEquals(old, reopened); assertNotSame(old, reopened)
            val reopenedReads = gateway.calls.size
            retained(); advanceUntilIdle()
            assertSame(reopened, model.storyRecord.value)
            assertEquals(reopenedReads, gateway.calls.size)
            val afterDispose = { model.recordPromiseFilter(StoryRecordPromiseFilter.OVERDUE, reopened) }
            store.clear()
            val disposed = model.storyRecord.value
            afterDispose(); model.recordPromiseFilter(StoryRecordPromiseFilter.OPEN); advanceUntilIdle()
            assertSame(disposed, model.storyRecord.value)
            assertEquals(reopenedReads, gateway.calls.size)
            assertEquals(1, gateway.closes)
            assertEquals(0, gateway.responses); assertEquals(0, gateway.commits)
        } finally { store.clear(); Dispatchers.resetMain() }
    }
}
