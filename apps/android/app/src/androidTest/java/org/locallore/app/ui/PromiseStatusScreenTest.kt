/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModelStore
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.*

/** Actual controls/controller with a synthetic typed reader; not native eligibility proof. */
class PromiseStatusScreenTest {
    @get:Rule val compose = createComposeRule()
    private val active = mutableStateOf<ShellViewModel?>(null)
    private val stores = mutableListOf<ViewModelStore>()

    @After fun closeModels() {
        if (stores.isNotEmpty()) compose.runOnIdle {
            active.value = null
            stores.forEach { it.clear() }
        }
    }

    private data class Harness(val model: ShellViewModel, val gateway: PromiseGateway)

    private fun show(): Harness {
        compose.setContent {
            active.value?.let { model ->
                val frame by model.storyRecordFrames.collectAsState()
                val rendered = frame.state
                StoryRecordDialog(rendered,
                    { model.closeStoryRecord(rendered) },
                    { section -> model.recordSection(section, rendered) },
                    { text -> model.recordSearch(text, rendered) },
                    { model.nextRecordPage(rendered) },
                    { model.firstRecordPage(rendered) },
                    { model.retryStoryRecord(rendered) },
                    onScopedEvent = { reference -> model.openScopedRecordEvent(reference, rendered) },
                    onEventBack = { model.backToStoryRecord(rendered) },
                    onEventRetry = { model.retryRecordEvent(rendered) },
                    onPromiseFilter = { filter -> model.recordPromiseFilter(filter, rendered) })
            }
        }
        val gateway = PromiseGateway()
        val model = compose.runOnIdle {
            val store = ViewModelStore().also { stores += it }
            ShellViewModel(gateway).also { store.put("promise-status", it); active.value = it }
        }
        settled(model, A)
        return Harness(model, gateway)
    }

    private fun settled(model: ShellViewModel, story: SavedStory) {
        compose.waitUntil(8_000) { !model.state.value.busy && model.state.value.selectedStory == story }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }

    private fun loaded(model: ShellViewModel, predicate: (StoryRecordState) -> Boolean = { true }) {
        compose.waitUntil(8_000) {
            val state = model.storyRecord.value
            state.visible && !state.loading && state.problem == null && predicate(state)
        }
        compose.waitForIdle()
    }

    private fun control(tag: String) = compose.onNodeWithTag(tag).performScrollTo()
    private fun status(filter: StoryRecordPromiseFilter) =
        control("story-record-promise-status-${filter.name.lowercase()}")

    private fun openPromises(model: ShellViewModel) {
        compose.runOnIdle { model.openStoryRecord() }
        loaded(model)
        compose.onNodeWithTag("story-record-promise-status-open").assertDoesNotExist()
        control("story-record-section-promises").performClick()
        loaded(model) { it.section == StoryRecordSection.PROMISES }
        status(StoryRecordPromiseFilter.ALL).assertIsSelected()
    }

    private fun close() {
        compose.onNodeWithTag("story-record-close").performClick()
        compose.waitForIdle()
        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
    }

    @Test fun statusPagingAndEvidenceBackKeepTheNativePresetWhileTextSearchReturnsToAll() {
        val h = show()
        openPromises(h.model)
        control("story-record-search").performTextReplacement("Unsubmitted lookup")
        status(StoryRecordPromiseFilter.OPEN).performClick()
        loaded(h.model) { it.promiseFilter == StoryRecordPromiseFilter.OPEN && it.entries.size == 8 }
        status(StoryRecordPromiseFilter.OPEN).assertIsSelected()
        control("story-record-search").assert(hasText(""))
        assertEquals(9, h.model.storyRecord.value.total)
        assertTrue(h.model.storyRecord.value.entries.all { it.promiseStatus == StoryRecordPromiseStatus.OPEN })
        control("story-record-next").performClick()
        loaded(h.model) { it.cursor == SECOND_PAGE }
        assertEquals(StoryRecordPromiseFilter.OPEN, h.gateway.reads.last().promiseFilter)
        assertEquals(9, h.model.storyRecord.value.total)
        assertEquals(1, h.model.storyRecord.value.entries.size)
        control("story-record-scoped-source-0-0").performClick()
        loaded(h.model) { it.eventDetail?.entry != null }
        compose.onNodeWithText("Synthetic witnessed promise event").assertExists()
        compose.onNodeWithTag("story-event-back").performClick()
        loaded(h.model) { it.eventDetail == null && it.cursor == SECOND_PAGE }
        status(StoryRecordPromiseFilter.OPEN).assertIsSelected()
        assertEquals(9, h.model.storyRecord.value.total)
        control("story-record-search").performTextReplacement("open workshop")
        control("story-record-search-submit").performClick()
        loaded(h.model) { it.search == "open workshop" && it.promiseFilter == StoryRecordPromiseFilter.ALL }
        status(StoryRecordPromiseFilter.ALL).assertIsSelected()
        assertNull(h.gateway.reads.last().cursor)
        assertEquals(1, h.model.storyRecord.value.total)
        assertEquals(StoryRecordPromiseStatus.FULFILLED, h.model.storyRecord.value.entries.single().promiseStatus)
        control("story-record-entry-0")
        compose.onNodeWithText("Status · Fulfilled\nDeliver to the open workshop").assertExists()
        close()
        compose.runOnIdle {
            assertEquals(0, h.gateway.gameplayCalls)
            assertEquals(snapshot(A), h.gateway.saved)
        }
    }

    @Test fun retainedPresetCannotRetargetLaterStatusEqualReopenOrAnotherStory() {
        val h = show()
        openPromises(h.model)
        val oldOpen = checkNotNull(status(StoryRecordPromiseFilter.OPEN).assertIsEnabled()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        status(StoryRecordPromiseFilter.OVERDUE).performClick()
        loaded(h.model) { it.promiseFilter == StoryRecordPromiseFilter.OVERDUE }
        status(StoryRecordPromiseFilter.OVERDUE).assertIsSelected()
        val overdue = h.model.storyRecord.value
        assertEquals(StoryRecordPromiseStatus.OVERDUE, overdue.entries.single().promiseStatus)
        quiet(h, overdue, oldOpen)
        close()
        openPromises(h.model)
        quiet(h, h.model.storyRecord.value, oldOpen)
        close()
        compose.runOnIdle { h.model.resume(B) }
        settled(h.model, B)
        openPromises(h.model)
        quiet(h, h.model.storyRecord.value, oldOpen)
        status(StoryRecordPromiseFilter.OPEN).performClick()
        loaded(h.model) { it.promiseFilter == StoryRecordPromiseFilter.OPEN }
        assertEquals(B.story, h.gateway.reads.last().context.story.story)
        status(StoryRecordPromiseFilter.ALL).performClick()
        loaded(h.model) { it.promiseFilter == StoryRecordPromiseFilter.ALL }
        assertEquals("", h.gateway.reads.last().search)
        assertNull(h.gateway.reads.last().cursor)
        close()
        compose.runOnIdle {
            assertEquals(0, h.gateway.gameplayCalls)
            assertEquals(snapshot(B), h.gateway.saved)
        }
    }

    private fun quiet(h: Harness, expected: StoryRecordState, action: () -> Boolean) {
        val reads = compose.runOnIdle { h.gateway.reads.toList() }
        compose.runOnIdle { action() }
        compose.waitForIdle()
        compose.runOnIdle {
            assertSame(expected, h.model.storyRecord.value)
            assertEquals(reads, h.gateway.reads)
            assertEquals(0, h.gateway.gameplayCalls)
        }
    }

    private class PromiseGateway : DemoGateway {
        override val durable = true
        override val storyRecords = true
        val reads = mutableListOf<StoryRecordQuery>()
        var saved = snapshot(A)
        var gameplayCalls = 0
        override suspend fun initialize() = saved
        override suspend fun snapshot() = saved
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot = snapshot(story).also { saved = it }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplayCalls++; return DemoResult.Rejected("Synthetic reader only")
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult { gameplayCalls++; return result }
        override fun cancel() { gameplayCalls++ }
        override fun reset() { gameplayCalls++ }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
            reads += query
            val ref = StoryRecordScopedEvent(StoryRecordScope(query.context.story.story, "main"), 1)
            if (query.section == StoryRecordSection.HISTORY) return StoryRecordPage(query, 10, 1,
                listOf(StoryRecordEntry("witnessed-event", "Event #1", "Synthetic witnessed promise event",
                    StoryRecordOrigin.RECORDED_OBSERVATION, event = StoryRecordEvent(1, "synthetic-turn", 10, ref.originalScope),
                    scopedEventSources = listOf(ref))), null)
            if (query.section != StoryRecordSection.PROMISES) return StoryRecordPage(query, 10, 0, emptyList(), null)
            val status = when (query.promiseFilter) {
                StoryRecordPromiseFilter.OPEN -> StoryRecordPromiseStatus.OPEN
                StoryRecordPromiseFilter.OVERDUE -> StoryRecordPromiseStatus.OVERDUE
                StoryRecordPromiseFilter.ALL -> StoryRecordPromiseStatus.FULFILLED
            }
            val firstOpen = query.promiseFilter == StoryRecordPromiseFilter.OPEN && query.cursor == null
            val count = if (firstOpen) 8 else 1
            val total = if (query.promiseFilter == StoryRecordPromiseFilter.OPEN) 9 else 1
            val entries = (0 until count).map { index -> StoryRecordEntry("promise-${query.cursor}-$index",
                "Promise · synthetic-$index", "Status · ${status.label}\nDeliver to the open workshop",
                StoryRecordOrigin.DERIVED_COMPARISON, scopedEventSources = listOf(ref), promiseStatus = status) }
            return StoryRecordPage(query, 10, total, entries, if (firstOpen) SECOND_PAGE else null)
        }
    }

    private companion object {
        val A = SavedStory("promise-ui-a", "main", "SCRIPTED promise A", 4)
        val B = SavedStory("promise-ui-b", "main", "SCRIPTED promise B", 4)
        const val SECOND_PAGE = "synthetic-promise-page-2"
        fun snapshot(story: SavedStory) = SavedSnapshot(4, "You", emptyList(), "synthetic-database", 1,
            listOf(A, B), story, rulesProfile = "fantasy_v1", textProvider = TextProvider.SCRIPTED)
    }
}
