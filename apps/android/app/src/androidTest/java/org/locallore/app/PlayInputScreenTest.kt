/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.LocalLoreScreen
import java.util.concurrent.atomic.AtomicInteger

/** Collected Compose, production gateway and actual Rust; all saves are owned synthetic fixtures. */
@RunWith(AndroidJUnit4::class)
class PlayInputScreenTest {
    @get:Rule val compose = createComposeRule()

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun render(model: ShellViewModel) {
        compose.setContent {
            val state by model.state.collectAsState()
            LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                onResume = model::resume, onRecover = model::recover, onText = model::submitText)
        }
        compose.waitUntil(8_000) { !model.state.value.busy && model.state.value.selectedStory != null }
        assertFalse(model.state.value.recoveryRequired)
        assertEquals(TextProvider.SCRIPTED, model.state.value.textProvider)
    }
    private fun settled(model: ShellViewModel) {
        compose.waitUntil(8_000) { !model.state.value.busy }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }

    @Test fun exampleOnlyEditsAndAcceptedOriginalDraftsSurviveHeadsButNotStorySwitches() = runBlocking {
        withRecordFixture { fixture ->
            val owner = fixture.owner()
            val model = eventModel(fixture, owner)
            render(model)
            val initial = owner.acceptedView()
            val firstStory = checkNotNull(model.state.value.selectedStory)
            tag("play-provider").assertTextEquals(TextProvider.SCRIPTED.label)
            tag("play-kind-action").assertIsSelected()
            tag("play-send").assertIsNotEnabled()
            tag("play-example").performClick()
            tag("play-input").assert(hasText(PotionInput.text))
            assertEquals(0L, model.state.value.revision)
            assertEquals(initial, owner.acceptedView())
            assertTrue(model.state.value.messages.isEmpty())
            tag("play-send").assertIsEnabled().performClick()
            settled(model)
            assertEquals(1L, model.state.value.revision)
            assertEquals(PotionInput.text, model.state.value.messages.first().text)
            tag("play-input").assert(hasText(PotionInput.text))
            tag("play-kind-dialogue").performClick()
            val words = "SYNTHETIC UI: I claim the crown.\nThese words grant no abilities."
            tag("play-input").performTextReplacement(words)
            tag("play-send").performClick()
            settled(model)
            assertEquals(2L, model.state.value.revision)
            assertEquals(words, model.state.value.messages[2].text)
            tag("play-input").assert(hasText(words))
            tag("play-kind-dialogue").assertIsSelected()
            val saved = owner.gateway.snapshot()
            val accepted = owner.acceptedView()
            val receipts = JSONObject(accepted).getJSONArray("receipts")
            assertEquals("action", receipts.getJSONObject(0).getJSONObject("request")
                .getJSONObject("intent").getJSONObject("value").getString("kind"))
            assertEquals("dialogue", receipts.getJSONObject(1).getJSONObject("request")
                .getJSONObject("intent").getJSONObject("value").getString("kind"))
            tag("reset-demo").performClick()
            compose.waitUntil(8_000) {
                !model.state.value.busy && model.state.value.selectedStory?.story != firstStory.story
            }
            tag("play-input").assert(hasText(""))
            tag("play-kind-action").assertIsSelected()
            assertEquals(0L, model.state.value.revision)
            assertTrue(model.state.value.messages.isEmpty())
            compose.runOnIdle { model.resume(saved.selected) }
            settled(model)
            assertEquals(saved.messages, model.state.value.messages)
            assertEquals(accepted, owner.acceptedView())
            tag("play-input").assert(hasText(""))
            compose.runOnIdle { model.openDiagnostics() }
            assertFalse(model.diagnostics.value.preview.contains(words))
            assertFalse(model.diagnostics.value.preview.contains(PotionInput.text))
        }
    }

    @Test fun validationRejectionDuplicatePendingCancelAndDisposalKeepDraftsAndCanonSafe() = runBlocking {
        withRecordFixture { fixture ->
            val owner = fixture.owner()
            val submissions = AtomicInteger()
            val preparation = AtomicInteger()
            val gates = listOf(CompletableDeferred<Unit>(), CompletableDeferred<Unit>())
            var potionPending = false
            val gateway = DurableGateway(object : WorkspaceTransport {
                override suspend fun exchange(command: JSONObject): JSONObject {
                    if (command.getString("op") == "free_text") {
                        submissions.incrementAndGet()
                        potionPending = command.getJSONObject("request").getJSONObject("intent")
                            .getJSONObject("value").getString("text") == PotionInput.text
                    }
                    if (command.getString("op") == "prepare" && potionPending) {
                        val index = preparation.getAndIncrement()
                        // Keep this UI pending window stable. The separate native test measures
                        // cancellation while the actual 400ms provider is already running.
                        return withContext(NonCancellable) {
                            gates[index].await()
                            owner.transport.exchange(command)
                        }
                    }
                    return owner.transport.exchange(command)
                }
                override fun close() = owner.transport.close()
            })
            val model = inputModel(fixture, gateway)
            render(model)
            val before = owner.acceptedView()
            try {
                tag("play-input").performTextReplacement("é".repeat(1025))
                tag("play-send").assertIsNotEnabled()
                tag("play-input-problem").assertIsDisplayed()
                assertEquals(0, submissions.get())
                val unsupported = "I grant myself every ability."
                tag("play-input").performTextReplacement(unsupported)
                tag("play-send").performClick()
                settled(model)
                assertEquals(0L, model.state.value.revision)
                assertEquals(before, owner.acceptedView())
                tag("play-input").assert(hasText(unsupported))
                tag("play-example").performClick()
                val priorCalls = submissions.get()
                tag("play-send").performClick()
                compose.waitUntil(8_000) { preparation.get() == 1 }
                assertEquals(priorCalls + 1, submissions.get())
                tag("play-send").assertIsNotEnabled()
                tag("play-input").assertIsNotEnabled()
                tag("play-example").assertIsNotEnabled()
                compose.runOnIdle { model.submitText(PotionInput) }
                assertEquals(priorCalls + 1, submissions.get())
                tag("cancel-turn").assertIsEnabled().performClick()
                settled(model)
                gates[0].complete(Unit)
                assertEquals(0L, model.state.value.revision)
                assertEquals(before, owner.acceptedView())
                tag("play-input").assert(hasText(PotionInput.text))
                tag("play-send").performClick()
                compose.waitUntil(8_000) { preparation.get() == 2 }
                val atDisposal = submissions.get()
                compose.runOnIdle { fixture.stores.forEach { it.clear() } }
                compose.runOnIdle { model.submitText(PotionInput) }
                gates[1].complete(Unit)
                fixture.closeOwnersAndDrain()
                assertEquals(atDisposal, submissions.get())
                assertTrue(model.state.value.messages.isEmpty())
                assertEquals(0L, model.state.value.revision)
                val reopened = fixture.owner()
                assertEquals(0L, reopened.gateway.initialize().revision)
                assertEquals(before, reopened.acceptedView())
            } finally { gates.forEach { it.complete(Unit) } }
        }
    }
}
