/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.StoryRecordDialog
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Collected production state and actual JNI records; no default app save is opened or reset. */
@RunWith(AndroidJUnit4::class)
class StoryRecordScreenTest {
    @get:Rule val compose = createComposeRule()

    private fun shellTag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun recordTag(name: String) = compose.onNodeWithTag(name).performScrollTo()
    private fun loaded(model: ShellViewModel, predicate: (StoryRecordState) -> Boolean = { true }) {
        compose.waitUntil(8_000) {
            val record = model.storyRecord.value
            record.visible && !record.loading && record.problem == null && predicate(record)
        }
        compose.waitForIdle()
    }
    private fun section(model: ShellViewModel, section: StoryRecordSection) {
        recordTag("story-record-section-${section.wire}").performClick()
        loaded(model) { it.section == section }
        compose.onNodeWithTag("story-record-section-${section.wire}").assertIsSelected()
    }
    private fun search(model: ShellViewModel, text: String) {
        recordTag("story-record-search").performTextReplacement(text)
        recordTag("story-record-search-submit").performClick()
        loaded(model) { it.search == text }
    }
    private fun assertFirstEntryPresentation(state: StoryRecordState) {
        val entry = state.entries.first()
        recordTag("story-record-entry-0")
        val parent = hasAnyAncestor(hasTestTag("story-record-entry-0"))
        compose.onNode(parent and hasText(entry.title, substring = false), useUnmergedTree = true).assertExists()
        compose.onNode(parent and hasText(entry.origin.label, substring = false), useUnmergedTree = true).assertExists()
        val source = if (entry.sources.isEmpty()) "Source \u00B7 none recorded"
            else "Sources \u00B7 ${entry.sources.joinToString(" \u00B7 ")}"
        compose.onNode(parent and hasText(source, substring = false), useUnmergedTree = true).assertExists()
    }

    @Test fun collectedRecordPagesSearchOriginsAndGiftRefreshUseTheAuthoritativeSavedHead() = runBlocking {
        withRecordFixture { fixture ->
            val owner = fixture.owner()
            val model = withContext(Dispatchers.Main) {
                val store = ViewModelStore().also { fixture.stores += it }
                ViewModelProvider(store, object : ViewModelProvider.Factory {
                    @Suppress("UNCHECKED_CAST")
                    override fun <T : ViewModel> create(modelClass: Class<T>): T = ShellViewModel(owner.gateway) as T
                })[ShellViewModel::class.java]
            }
            compose.setContent {
                val state by model.state.collectAsState()
                val record by model.storyRecord.collectAsState()
                LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover, onStoryRecord = model::openStoryRecord) {
                    StoryRecordDialog(record, model::closeStoryRecord, model::recordSection, model::recordSearch,
                        model::nextRecordPage, model::firstRecordPage, model::retryStoryRecord)
                }
            }
            compose.waitUntil(8_000) { !model.state.value.busy && model.state.value.selectedStory != null }
            assertFalse(model.state.value.recoveryRequired)
            assertTrue(model.hasStoryRecords)
            val before = owner.acceptedView()
            val saved = owner.gateway.snapshot()
            val turnCalls = owner.transport.turnCalls.get()
            shellTag("story-record-open").assertIsEnabled().performClick()
            loaded(model)
            compose.onNodeWithTag("story-record-dialog").assertIsDisplayed()
            assertEquals(0L, model.storyRecord.value.context!!.revision)
            assertEquals(8, model.storyRecord.value.entries.size)
            val first = model.storyRecord.value.entries.map { it.key }
            val total = model.storyRecord.value.total
            assertTrue(total > 8)
            assertFirstEntryPresentation(model.storyRecord.value)
            recordTag("story-record-next").assertIsEnabled().performClick()
            loaded(model) { it.cursor != null }
            val second = model.storyRecord.value.entries.map { it.key }
            assertEquals(total, (first + second).toSet().size)
            assertTrue(first.none { it in second })
            recordTag("story-record-next").assertIsNotEnabled()
            recordTag("story-record-first").assertIsEnabled().performClick()
            loaded(model) { it.cursor == null }
            assertEquals(first, model.storyRecord.value.entries.map { it.key })

            search(model, "%' OR 1=1 -- [literal]")
            assertEquals(0, model.storyRecord.value.total)
            recordTag("story-record-empty").assertIsDisplayed()
            compose.onNodeWithTag("story-record-entry-0").assertDoesNotExist()
            search(model, "")
            assertEquals(total, model.storyRecord.value.total)
            section(model, StoryRecordSection.HISTORY)
            assertTrue(model.storyRecord.value.entries.isEmpty())
            recordTag("story-record-empty").assertIsDisplayed()
            section(model, StoryRecordSection.RELATIONSHIPS)
            assertTrue(model.storyRecord.value.entries.isNotEmpty())
            assertFirstEntryPresentation(model.storyRecord.value)
            section(model, StoryRecordSection.KNOWLEDGE)
            assertTrue(model.storyRecord.value.entries.all { it.origin == StoryRecordOrigin.KNOWN_AS_OBSERVED })
            assertFirstEntryPresentation(model.storyRecord.value)
            search(model, "SECRET-TIDE-731") // A seeded fact the player actually knows.
            assertEquals(1, model.storyRecord.value.total)
            assertTrue(model.storyRecord.value.entries.single().text.contains("SECRET-TIDE-731"))
            search(model, "")
            val knowledge = model.storyRecord.value.entries
            compose.onNodeWithTag("story-record-close").performClick()
            compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
            assertTrue("Browsing changed accepted canonical data", before == owner.acceptedView())
            assertTrue("Browsing changed the saved presentation", saved == owner.gateway.snapshot())
            assertEquals("Browsing dispatched a turn or inference preparation", turnCalls, owner.transport.turnCalls.get())

            shellTag("story-record-open").performClick()
            loaded(model)
            section(model, StoryRecordSection.KNOWLEDGE)
            assertEquals(knowledge, model.storyRecord.value.entries)
            compose.onNodeWithTag("story-record-close").performClick()
            shellTag("give-potion").performClick()
            compose.waitUntil(8_000) { !model.state.value.busy && model.state.value.revision == 1L }
            assertFalse(model.state.value.recoveryRequired)
            assertEquals("Not in your inventory", model.state.value.potionOwner)
            assertEquals(2, model.state.value.messages.size)
            val accepted = owner.acceptedView()
            shellTag("story-record-open").performClick()
            loaded(model) { it.context?.revision == 1L }
            assertEquals(100L, model.storyRecord.value.storyTime)
            section(model, StoryRecordSection.HISTORY)
            val originalScope = JSONObject(accepted).getJSONArray("receipts").getJSONObject(0)
                .getJSONObject("request").getJSONObject("scope")
            val reference = StoryRecordScopedEvent(StoryRecordScope(originalScope.getString("story"),
                originalScope.getString("branch")), 1)
            assertTrue(model.storyRecord.value.entries.any {
                it.origin == StoryRecordOrigin.RECORDED_MESSAGE && it.scopedEventSources == listOf(reference) &&
                    it.eventSources.isEmpty() && it.sources == listOf(
                        "Event #1 · ${reference.originalScope.story} / ${reference.originalScope.branch}")
            })
            assertFirstEntryPresentation(model.storyRecord.value)
            compose.onNodeWithTag("story-record-close").performClick()
            assertTrue("Refreshed browsing changed accepted receipts", accepted == owner.acceptedView())
            // Retained UI callbacks must be fenced when the owning ViewModel is disposed.
            compose.runOnIdle { fixture.stores.forEach { it.clear() } }
            val disposed = model.storyRecord.value
            compose.runOnIdle {
                model.openStoryRecord(); model.recordSection(StoryRecordSection.PROGRESSION)
                model.recordSearch("retained callback"); model.nextRecordPage(); model.retryStoryRecord()
            }
            compose.waitForIdle()
            assertEquals(disposed, model.storyRecord.value)
        }
    }
}
