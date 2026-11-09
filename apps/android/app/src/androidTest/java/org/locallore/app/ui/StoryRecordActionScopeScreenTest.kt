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

/** Real screen/ViewModel/controller with a synthetic typed reader, not native eligibility evidence. */
class StoryRecordActionScopeScreenTest {
    @get:Rule val compose = createComposeRule()
    private val active = mutableStateOf<ShellViewModel?>(null)
    private val stores = mutableListOf<ViewModelStore>()

    @After fun closeModels() {
        if (stores.isNotEmpty()) compose.runOnIdle {
            active.value = null
            stores.forEach { it.clear() }
        }
    }

    private data class Harness(val model: ShellViewModel, val gateway: RecordGateway)

    private fun show(): Harness {
        // Match MainActivity's plain rendered snapshot, never a delegated getter in a callback.
        compose.setContent {
            active.value?.let { model ->
                val shell by model.state.collectAsState()
                val recordFrame by model.storyRecordFrames.collectAsState()
                val renderedRecordState = recordFrame.state
                val renderedRecordEvent = renderedRecordState.eventDetail
                LocalLoreScreen(shell, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover,
                    onStoryRecord = model::openStoryRecord, onText = model::submitText) {
                    StoryRecordDialog(renderedRecordState,
                        { model.closeStoryRecord(renderedRecordState) },
                        { section -> model.recordSection(section, renderedRecordState) },
                        { text -> model.recordSearch(text, renderedRecordState) },
                        { model.nextRecordPage(renderedRecordState) },
                        { model.firstRecordPage(renderedRecordState) },
                        { model.retryStoryRecord(renderedRecordState) },
                        onEvent = { sequence -> model.openRecordEvent(sequence, renderedRecordState) },
                        onScopedEvent = { reference -> model.openScopedRecordEvent(reference, renderedRecordState) },
                        onEventBack = { renderedRecordEvent?.let { model.backToStoryRecord(it) } },
                        onEventRetry = renderedRecordEvent?.let { detail -> { model.retryRecordEvent(detail) } })
                }
            }
        }
        val gateway = RecordGateway()
        val model = compose.runOnIdle {
            val store = ViewModelStore().also { stores += it }
            ShellViewModel(gateway).also { store.put("record-action-scope", it); active.value = it }
        }
        settled(model)
        return Harness(model, gateway)
    }

    private fun settled(model: ShellViewModel, selected: SavedStory = A) {
        compose.waitUntil(8_000) {
            val s = model.state.value
            !s.busy && s.selectedStory == selected
        }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }
    private fun loaded(model: ShellViewModel, predicate: (StoryRecordState) -> Boolean = { true }) {
        compose.waitUntil(8_000) {
            val s = model.storyRecord.value
            s.visible && !s.loading && s.problem == null && predicate(s)
        }
        compose.waitForIdle()
    }
    private fun shell(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        return compose.onNodeWithTag(tag)
    }
    private fun record(tag: String): SemanticsNodeInteraction {
        val node = compose.onNodeWithTag(tag)
        // Back and Close are pinned below the scrollable content.
        return when (tag) {
            "story-event-back", "story-record-close" -> node
            else -> node.performScrollTo()
        }
    }
    private fun click(tag: String): () -> Boolean = checkNotNull(
        record(tag).assertIsEnabled().fetchSemanticsNode().config[SemanticsActions.OnClick].action)
    private fun open(model: ShellViewModel) {
        shell("story-record-open").assertIsEnabled().performClick()
        loaded(model)
    }
    private fun close() {
        compose.onNodeWithTag("story-record-close").performClick()
        compose.waitForIdle()
        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
    }
    private fun quiet(h: Harness, expected: StoryRecordState, action: () -> Boolean) {
        val before = compose.runOnIdle { Triple(h.gateway.reads.toList(), h.model.state.value, h.gateway.saved) }
        compose.runOnIdle { action() }
        compose.waitForIdle()
        compose.runOnIdle {
            assertSame("A retained action replaced the current record view", expected, h.model.storyRecord.value)
            assertEquals(before.first, h.gateway.reads)
            assertEquals(before.second, h.model.state.value)
            assertEquals(before.third, h.gateway.saved)
            assertTrue(h.gateway.gameplay.isEmpty())
        }
    }
    private fun draft(text: String) {
        shell("play-kind-dialogue").performClick()
        shell("play-input").performTextReplacement(text)
    }
    private fun draftUnchanged(text: String) {
        shell("play-input").assert(hasText(text))
        shell("play-kind-dialogue").assertIsSelected()
    }

    @Test fun retainedSearchNextAndCloseCannotRetargetAnotherStoryOrBranchAndFreshControlsStillWork() {
        val h = show()
        draft("Unsent A café 漢字 🌿")
        open(h.model)
        record("story-record-search").performTextReplacement("Old A lookup café 漢字 🌿")
        val oldSearch = click("story-record-search-submit")
        val oldNext = click("story-record-next")
        val oldClose = click("story-record-close")
        close()
        shell("saved-library").performClick()
        compose.onNodeWithTag("saved-story-${B.story}").performClick()
        settled(h.model, B)
        shell("play-input").assert(hasText(""))
        val bDraft = "Unsent B dialogue\nNo record control may submit this café 🌿."
        draft(bDraft)
        open(h.model)
        val currentB = h.model.storyRecord.value
        for (old in listOf(oldSearch, oldNext, oldClose)) quiet(h, currentB, old)

        record("story-record-search").performTextReplacement("Fresh B lookup")
        val beforeSearch = h.gateway.reads.size
        record("story-record-search-submit").performClick()
        loaded(h.model) { it.search == "Fresh B lookup" }
        assertEquals(beforeSearch + 1, h.gateway.reads.size)
        assertEquals(B.story, h.gateway.reads.last().context.story.story)
        assertEquals("Fresh B lookup", h.gateway.reads.last().search)
        val bSearch = click("story-record-search-submit")
        val bNext = click("story-record-next")
        val bClose = click("story-record-close")
        record("story-record-next").performClick()
        loaded(h.model) { it.cursor == PAGE_2 }
        close()
        draftUnchanged(bDraft)

        val fork = B.copy(branch = "fork")
        compose.runOnIdle { h.model.resume(fork) }
        settled(h.model, fork)
        shell("play-input").assert(hasText(""))
        open(h.model)
        val currentFork = h.model.storyRecord.value
        for (old in listOf(oldSearch, oldNext, oldClose, bSearch, bNext, bClose)) quiet(h, currentFork, old)
        record("story-record-section-history").performClick()
        loaded(h.model) { it.section == StoryRecordSection.HISTORY }
        assertEquals("fork", h.gateway.reads.last().context.story.branch)
        close()
        compose.runOnIdle { assertSame(MESSAGES, h.model.state.value.messages); assertTrue(h.gateway.gameplay.isEmpty()) }
    }

    @Test fun equalValuedReopenAndLaterPagesRejectOldButtonsWithoutResettingTheCurrentDialogue() {
        val h = show()
        val text = "Unsent same-scope café 漢字\nA page is not a turn."
        draft(text)
        open(h.model)
        val first = h.model.storyRecord.value
        val oldClose = click("story-record-close")
        val oldSearch = click("story-record-search-submit")
        val oldNext = click("story-record-next")
        val oldSection = click("story-record-section-knowledge")
        close()
        open(h.model)
        val reopened = h.model.storyRecord.value
        assertEquals(first, reopened)
        assertNotSame(first, reopened)
        for (old in listOf(oldClose, oldSearch, oldNext, oldSection)) quiet(h, reopened, old)
        record("story-record-next").performClick()
        loaded(h.model) { it.cursor == PAGE_2 }
        val second = h.model.storyRecord.value
        quiet(h, second, oldNext) // Context matches, but this button belongs to page one.
        val secondFirst = click("story-record-first")
        val secondNext = click("story-record-next")
        record("story-record-next").performClick()
        loaded(h.model) { it.cursor == PAGE_3 }
        val third = h.model.storyRecord.value
        quiet(h, third, secondFirst)
        quiet(h, third, secondNext)
        record("story-record-next").assertIsNotEnabled()
        record("story-record-first").performClick()
        loaded(h.model) { it.cursor == null }
        assertEquals(first, h.model.storyRecord.value)
        assertNotSame(first, h.model.storyRecord.value)
        quiet(h, h.model.storyRecord.value, oldClose)
        record("story-record-section-relationships").performClick()
        loaded(h.model) { it.section == StoryRecordSection.RELATIONSHIPS }
        assertEquals(StoryRecordSection.RELATIONSHIPS, h.gateway.reads.last().section)
        close()
        draftUnchanged(text)
        compose.runOnIdle { assertSame(MESSAGES, h.model.state.value.messages); assertTrue(h.gateway.gameplay.isEmpty()) }
    }

    @Test fun retainedListAndEventRetryBackAndSourceActionsCannotAffectFreshDetailsOrReopenedRecords() {
        val h = show()
        val text = "Unsent event-inspector dialogue café 🌿"
        draft(text)
        compose.runOnIdle { h.gateway.failListOnce = true }
        shell("story-record-open").performClick()
        compose.waitUntil(8_000) { h.model.storyRecord.value.problem == StoryRecordProblem.UNAVAILABLE }
        compose.waitForIdle()
        val oldListRetry = click("story-record-retry")
        record("story-record-retry").performClick()
        loaded(h.model)
        quiet(h, h.model.storyRecord.value, oldListRetry)
        val oldSource = click("story-record-scoped-source-0-0")
        compose.runOnIdle { h.gateway.failEventOnce = true }
        record("story-record-scoped-source-0-0").performClick()
        compose.waitUntil(8_000) {
            h.model.storyRecord.value.eventDetail?.problem == StoryRecordProblem.EVENT_UNAVAILABLE
        }
        compose.waitForIdle()
        val oldEventRetry = click("story-event-retry")
        val oldBack = click("story-event-back")
        val oldDetailClose = click("story-record-close")
        record("story-event-retry").performClick()
        loaded(h.model) { it.eventDetail?.let { event -> event.entry != null && !event.loading } == true }
        val detail = h.model.storyRecord.value
        val eventDetail = checkNotNull(detail.eventDetail)
        assertEquals(reference(A), eventDetail.scopedReference)
        assertEquals("Synthetic eligible event", eventDetail.entry!!.text)
        for (old in listOf(oldEventRetry, oldDetailClose, oldListRetry)) quiet(h, detail, old)
        // Back still belongs to this open detail after its Retry has settled.
        compose.runOnIdle { oldBack() }
        loaded(h.model) { it.eventDetail == null }
        quiet(h, h.model.storyRecord.value, oldSource)
        record("story-record-scoped-source-0-0").performClick()
        loaded(h.model) { it.eventDetail?.entry != null }
        close()
        open(h.model)
        val reopened = h.model.storyRecord.value
        for (old in listOf(oldEventRetry, oldBack, oldDetailClose, oldListRetry, oldSource)) quiet(h, reopened, old)
        record("story-record-scoped-source-0-0").performClick()
        loaded(h.model) { it.eventDetail?.entry != null }
        quiet(h, h.model.storyRecord.value, oldBack)
        close()
        draftUnchanged(text)
        compose.runOnIdle { assertSame(MESSAGES, h.model.state.value.messages); assertTrue(h.gateway.gameplay.isEmpty()) }
    }

    private class RecordGateway : DemoGateway {
        override val durable = true
        override val storyRecords = true
        val reads = mutableListOf<StoryRecordQuery>()
        val gameplay = mutableListOf<String>()
        var saved = acceptedSnapshot(A)
        var failListOnce = false
        var failEventOnce = false
        override suspend fun initialize() = saved
        override suspend fun snapshot() = saved
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot {
            saved = acceptedSnapshot(story)
            return saved
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplay += "respond"; return DemoResult.Rejected("Fixture")
        }
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
            gameplay += "respond-text"; return DemoResult.Rejected("Fixture")
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult { gameplay += "commit"; return result }
        override fun cancel() { gameplay += "cancel" }
        override fun reset() { gameplay += "reset" }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
            reads += query
            val ref = reference(query.context.story)
            val drill = "\"event\":{\"sequence\":1,\"scope\":{\"story\":\"${ref.originalScope.story}\",\"branch\":\"main\"}"
            if (query.section == StoryRecordSection.HISTORY && query.search == drill) {
                if (failEventOnce) { failEventOnce = false; throw StoryRecordFailure(StoryRecordProblem.EVENT_UNAVAILABLE) }
                return StoryRecordPage(query, 10, 1, listOf(StoryRecordEntry("event-one", "Event #1",
                    "Synthetic eligible event", StoryRecordOrigin.RECORDED_OBSERVATION,
                    sources = listOf("Event #1 · ${ref.originalScope.story} / main"),
                    event = StoryRecordEvent(1, "synthetic-turn", 10, ref.originalScope),
                    scopedEventSources = listOf(ref))), null)
            }
            if (failListOnce) { failListOnce = false; throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE) }
            val next = when (query.cursor) { null -> PAGE_2; PAGE_2 -> PAGE_3; PAGE_3 -> null; else -> error("Fixture cursor") }
            return StoryRecordPage(query, 10, 3, listOf(StoryRecordEntry("row-${query.cursor ?: "first"}",
                "Synthetic visible record", "${query.context.story.story} / ${query.context.story.branch}",
                if (query.section == StoryRecordSection.HISTORY) StoryRecordOrigin.RECORDED_MESSAGE
                else StoryRecordOrigin.CANONICAL_FIELD,
                sources = listOf("Event #1 · ${ref.originalScope.story} / main"), scopedEventSources = listOf(ref))), next)
        }
    }

    private companion object {
        val A = SavedStory("fixture-a", "main", "SCRIPTED A", 4)
        val B = SavedStory("fixture-b", "main", "SCRIPTED B", 4)
        const val PAGE_2 = "synthetic-page-2"
        const val PAGE_3 = "synthetic-page-3"
        val MESSAGES = listOf(SceneMessage(1, "SCRIPTED accepted player input", true),
            SceneMessage(2, "SCRIPTED accepted narration, unchanged by record browsing", false))
        fun reference(story: SavedStory) = StoryRecordScopedEvent(StoryRecordScope(story.story, "main"), 1)
        fun acceptedSnapshot(story: SavedStory) = SavedSnapshot(4, "You", MESSAGES, "synthetic-database-path", 1,
            listOf(A, B), story, rulesProfile = "fantasy_v1", textProvider = TextProvider.SCRIPTED,
            timelines = listOf(SavedTimeline(story.story, "main", null, null, 4, 0),
                SavedTimeline(story.story, "fork", "main", 4, 4, 0)))
    }
}
