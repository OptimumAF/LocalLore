/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.view.KeyEvent
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.atomic.AtomicReference
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.StoryRecordDialog

/** Real collected screen/dialog in an owned synthetic workspace; no MainActivity/default save. */
@RunWith(AndroidJUnit4::class)
class EventSourceScreenTest {
    @get:Rule val compose = createComposeRule()

    private fun shellTag(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        return compose.onNodeWithTag(tag)
    }
    private fun recordTag(tag: String) = compose.onNodeWithTag(tag).performScrollTo()
    private fun loaded(model: ShellViewModel, predicate: (StoryRecordState) -> Boolean = { true }) {
        compose.waitUntil(8_000) {
            val state = model.storyRecord.value
            state.visible && !state.loading && state.problem == null && predicate(state)
        }
        compose.waitForIdle()
    }
    private fun search(model: ShellViewModel, text: String) {
        recordTag("story-record-search").performTextReplacement(text)
        recordTag("story-record-search-submit").performClick()
        loaded(model) { it.search == text }
    }
    private fun history(model: ShellViewModel) {
        recordTag("story-record-section-history").performClick()
        loaded(model) { it.section == StoryRecordSection.HISTORY }
    }
    private fun scopedSearch(reference: StoryRecordScopedEvent) =
        "\"event\":{\"sequence\":${reference.sequence},\"scope\":{\"story\":\"${reference.originalScope.story}\",\"branch\":\"${reference.originalScope.branch}\"}"
    private fun detail(model: ShellViewModel, reference: StoryRecordScopedEvent) {
        val sequence = reference.sequence
        loaded(model) { it.eventDetail?.let { detail -> detail.reference == sequence && !detail.loading } == true }
        val detail = model.storyRecord.value.eventDetail!!
        assertNull(detail.problem)
        val entry = checkNotNull(detail.entry)
        val event = checkNotNull(entry.event)
        assertEquals(sequence, event.sequence)
        assertEquals(reference, detail.scopedReference)
        assertEquals(reference.originalScope, event.originalScope)
        compose.onNodeWithTag("story-event-detail").assertIsDisplayed()
        compose.onNodeWithTag("story-record-content").assertDoesNotExist()
        compose.onNodeWithText("Frozen accepted head \u00B7 ${model.storyRecord.value.context!!.revision}").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Event story time \u00B7 ${event.storyTime}").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Turn \u00B7 ${event.turn}").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(entry.origin.label).performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("story-event-back").assertIsEnabled()
        compose.onNodeWithTag("story-record-close").assertIsEnabled()
    }

    @Test fun sourceButtonsRestoreSearchedSecondPageAndFenceLinksAcrossSavedStories() = runBlocking {
        withRecordFixture { fixture ->
            val owner = fixture.owner()
            seedEventScenes(owner)
            repeat(3) { index ->
                owner.commitIntent(JSONObject().put("kind", "dialogue").put("value", JSONObject()
                    .put("text", "SYNTHETIC pier record $index; quoted \"sequence\":1, Sources Event #999")
                    .put("audience", JSONArray().put("oren"))))
            }
            val saved = owner.gateway.snapshot()
            assertEquals(7L, saved.revision)
            val accepted = owner.acceptedView()
            val turnCalls = owner.transport.turnCalls.get()
            val model = eventModel(fixture, owner)
            val renderedEventClick = AtomicReference<((StoryRecordScopedEvent) -> Unit)?>(null)
            compose.setContent {
                val state by model.state.collectAsState()
                val records by model.storyRecord.collectAsState()
                val renderedRecordContext = records.context
                val openEvent: (StoryRecordScopedEvent) -> Unit = { reference -> model.openScopedRecordEvent(reference, renderedRecordContext) }
                SideEffect { renderedEventClick.set(openEvent) }
                LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover, onStoryRecord = model::openStoryRecord) {
                    StoryRecordDialog(records, model::closeStoryRecord, model::recordSection, model::recordSearch,
                        model::nextRecordPage, model::firstRecordPage, model::retryStoryRecord,
                        onEvent = { sequence -> model.openRecordEvent(sequence, renderedRecordContext) },
                        onScopedEvent = openEvent,
                        onEventBack = model::backToStoryRecord,
                        onEventRetry = model::retryRecordEvent)
                }
            }
            compose.waitUntil(8_000) { !model.state.value.busy && model.state.value.selectedStory != null }
            assertFalse(model.state.value.recoveryRequired)
            shellTag("story-record-open").performClick()
            loaded(model)
            history(model)
            search(model, "recorded") // Literal match against the actual engine row origins.
            assertTrue(model.storyRecord.value.total > 8)
            recordTag("story-record-next").assertIsEnabled().performClick()
            loaded(model) { it.cursor != null }
            val page = model.storyRecord.value
            assertEquals("recorded", page.search)
            assertTrue(page.entries.isNotEmpty())
            val index = page.entries.indexOfFirst { it.scopedEventSources.isNotEmpty() }
            assertTrue(index >= 0)
            val source = page.entries[index].scopedEventSources.first()
            val oldRenderedClick = checkNotNull(renderedEventClick.get())
            assertTrue(source.sequence in 1..saved.revision)
            assertTrue(page.entries.all { it.eventSources.isEmpty() && it.scopedEventSources.none { reference -> reference.sequence == 999L } })
            compose.onAllNodes(hasText("Open event #999", substring = true)).assertCountEquals(0)
            recordTag("story-record-scoped-source-$index-0").assertTextEquals(
                "Open event #${source.sequence} · ${source.originalScope.story} / ${source.originalScope.branch}").performClick()
            detail(model, source)
            val canonicalDetail = owner.gateway.readStoryRecord(StoryRecordQuery(
                StoryRecordContext(checkNotNull(saved.selected), saved.revision), StoryRecordSection.HISTORY, scopedSearch(source)))
            assertEquals(canonicalDetail.entries.single(), model.storyRecord.value.eventDetail!!.entry)
            InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
            loaded(model) { it.eventDetail == null }
            assertEquals("Platform Back changed page, search, cursor or entries", page, model.storyRecord.value)
            recordTag("story-record-search").assert(hasText("recorded"))
            compose.onNodeWithTag("story-record-section-history").assertIsSelected()
            recordTag("story-record-scoped-source-$index-0").performClick()
            detail(model, source)
            compose.onNodeWithTag("story-event-back").performClick()
            loaded(model) { it.eventDetail == null }
            assertEquals("Explicit Back changed the searched page", page, model.storyRecord.value)
            recordTag("story-record-scoped-source-$index-0").performClick()
            detail(model, source)
            compose.onNodeWithTag("story-record-close").performClick()
            compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
            assertTrue("Source browsing changed accepted data", accepted == owner.acceptedView())
            assertEquals("Source browsing dispatched gameplay/inference", turnCalls, owner.transport.turnCalls.get())

            shellTag("reset-demo").performClick() // A fresh story only inside this synthetic root.
            compose.waitUntil(8_000) {
                !model.state.value.busy && model.state.value.selectedStory?.story != checkNotNull(saved.selected).story
            }
            assertFalse(model.state.value.recoveryRequired)
            assertEquals(0L, model.state.value.revision)
            val other = owner.acceptedView()
            shellTag("story-record-open").performClick()
            loaded(model)
            history(model)
            recordTag("story-record-empty").assertIsDisplayed()
            compose.onNodeWithTag("story-record-scoped-source-$index-0").assertDoesNotExist()
            val empty = model.storyRecord.value
            compose.runOnIdle {
                model.openRecordEvent(source.sequence) // A scalar remains inert.
                model.openScopedRecordEvent(source, page.context); model.retryRecordEvent()
            }
            compose.waitForIdle()
            assertEquals("Old-story source callback attached to the new story", empty, model.storyRecord.value)
            assertTrue(other == owner.acceptedView())
            compose.onNodeWithTag("story-record-close").performClick()

            // Give the second story its own same-numbered event and a current page grant.
            // An old render must still carry its original context, not read a live delegate.
            repeat(source.sequence.toInt()) {
                owner.commitIntent(JSONObject().put("kind", "actions").put("value", JSONArray()
                    .put(JSONObject().put("op", "wait").put("ticks", 1))))
            }
            compose.runOnIdle { model.recover() }
            compose.waitUntil(8_000) { !model.state.value.busy && model.state.value.revision == source.sequence }
            val otherAccepted = owner.acceptedView()
            val finalTurnCalls = owner.transport.turnCalls.get()
            shellTag("story-record-open").performClick(); loaded(model); history(model)
            val selected = checkNotNull(model.state.value.selectedStory)
            val expectedCurrent = StoryRecordScopedEvent(StoryRecordScope(selected.story, selected.branch), source.sequence)
            search(model, scopedSearch(expectedCurrent))
            val currentReference = model.storyRecord.value.entries.single().scopedEventSources.single()
            assertEquals(expectedCurrent, currentReference)
            assertTrue(model.storyRecord.value.entries.single().eventSources.isEmpty())
            val currentPage = model.storyRecord.value
            compose.runOnIdle { oldRenderedClick(currentReference) }
            compose.waitForIdle()
            assertNull("Retained rendered callback borrowed a same-numbered event from another story",
                model.storyRecord.value.eventDetail)
            assertEquals(currentPage, model.storyRecord.value)
            compose.runOnIdle { checkNotNull(renderedEventClick.get())(currentReference) }
            detail(model, currentReference)
            assertTrue(otherAccepted == owner.acceptedView())
            assertEquals(finalTurnCalls, owner.transport.turnCalls.get())
            compose.onNodeWithTag("story-record-close").performClick()
            shellTag("saved-library").performClick()
            compose.onNodeWithText("${checkNotNull(saved.selected).title} \u00B7 ${checkNotNull(saved.selected).story} \u00B7 revision ${saved.revision}").performClick()
            compose.waitUntil(8_000) {
                !model.state.value.busy && model.state.value.selectedStory?.story == checkNotNull(saved.selected).story
            }
            assertEquals(saved.revision, model.state.value.revision)
            shellTag("story-record-open").performClick()
            loaded(model) { it.context?.story?.story == checkNotNull(saved.selected).story }
            history(model)
            val original = checkNotNull(saved.selected)
            search(model, scopedSearch(StoryRecordScopedEvent(StoryRecordScope(original.story, original.branch), 1)))
            assertEquals(1, model.storyRecord.value.total)
            assertEquals(StoryRecordOrigin.RECORDED_OBSERVATION, model.storyRecord.value.entries.single().origin)
            val originalReference = model.storyRecord.value.entries.single().scopedEventSources.single()
            recordTag("story-record-scoped-source-0-0").performClick()
            detail(model, originalReference)
            assertTrue(model.storyRecord.value.eventDetail!!.entry!!.text.contains("mira"))
            compose.onNodeWithTag("story-record-close").performClick()
            assertTrue("Resuming and browsing changed old-story canon", accepted == owner.acceptedView())
            assertEquals("Navigation across stories dispatched gameplay/inference", finalTurnCalls, owner.transport.turnCalls.get())
        }
    }
}
