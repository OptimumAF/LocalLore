/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.OriginalStoryDialog

/** Real dialog/controller journeys with a SCRIPTED counting gateway, never JNI/model evidence. */
class OriginalStoryInputDialogTest {
    @get:Rule val compose = createComposeRule()

    private class ScriptedGateway : OriginalStoryGateway {
        var begins = 0; var generates = 0; var reviews = 0; var creates = 0; var cancels = 0
        lateinit var generatedInput: OriginalInput
        var reviewed: OriginalReview? = null
        override suspend fun originalCapabilities() = OriginalCapabilities(true, "scripted")
        override suspend fun beginOriginal(input: OriginalInput): OriginalJob {
            begins++; generatedInput = input.frozen()
            return OriginalJob("scripted-input-job", "a".repeat(64), "scripted")
        }
        override suspend fun generateOriginal(job: String): OriginalGenerated {
            generates++
            val cast = generatedInput.cast.ifEmpty { listOf(OriginalCast("Mira", "A SCRIPTED keeper.")) }
            val actors = (0..cast.size).toList()
            val world = OriginalProposal(listOf(OriginalLocation("Orchard", "A SCRIPTED orchard.")), 0,
                cast.map { OriginalCharacter(it.name, it.description.ifEmpty { "A SCRIPTED keeper." }, 0, actors) },
                emptyList(), List(8) { OriginalFact("SCRIPTED fact $it.", listOf(0), null) },
                List(6) { OriginalBelief(0, "SCRIPTED belief $it.", "uncertain") },
                List(4) { OriginalPossession("Token${it + 1}", "A SCRIPTED token.", 0, null) })
            check(validOriginalDraft(generatedInput, world) && OriginalStoryWire.valid(generatedInput, world))
            return OriginalGenerated(job, generatedInput, world, "scripted")
        }
        override suspend fun reviewOriginal(job: String, input: OriginalInput,
            proposal: OriginalProposal, title: String): OriginalReview {
            reviews++
            return OriginalReview(job, "b".repeat(64), input, proposal, title,
                listOf("SCRIPTED review only; no story has been created.")).also { reviewed = it }
        }
        override suspend fun cancelOriginal(job: String): Boolean { cancels++; return true }
        override suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot {
            creates++
            error("SCRIPTED input journey must never create a canonical story")
        }
    }

    private fun form(port: ScriptedGateway,
        action: (() -> OriginalStoryUiState?, () -> Boolean) -> Unit) {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        val state = mutableStateOf<OriginalStoryUiState?>(null)
        var closed = false
        lateinit var controller: OriginalStoryController
        compose.setContent {
            MaterialTheme {
                state.value?.let { OriginalStoryDialog(it, controller::dismiss, controller::edit,
                    controller::generate, controller::review, controller::confirm, true) }
            }
        }
        compose.runOnIdle {
            controller = OriginalStoryController(port, scope, { state.value = it }, {
                closed = true; state.value = null
            })
            controller.open(OriginalCapabilities(true, "scripted"))
        }
        try { action({ state.value }, { closed }) }
        finally { compose.runOnIdle { controller.dispose(); scope.cancel() } }
    }

    private fun replace(tag: String, value: String) {
        compose.onNodeWithTag(tag).performScrollTo().performTextReplacement(value)
        compose.onNodeWithTag(tag).assert(hasText(value))
    }
    private fun addCast(index: Int, name: String, description: String = "") {
        compose.onNodeWithText("Add cast hint").performScrollTo().assertIsEnabled().performClick()
        replace("original-cast-$index-name", name)
        if (description.isNotEmpty()) replace("original-cast-$index-description", description)
    }
    private fun warning() {
        compose.onNodeWithText("different name for each character", substring = true)
            .performScrollTo().assertIsDisplayed()
    }
    private fun noCalls(port: ScriptedGateway) = compose.runOnIdle {
        assertEquals(0, port.begins); assertEquals(0, port.generates)
        assertEquals(0, port.reviews); assertEquals(0, port.creates); assertEquals(0, port.cancels)
    }
    private fun generated(state: () -> OriginalStoryUiState?) {
        compose.waitUntil(5_000) { compose.runOnIdle { state()?.let { !it.busy && it.proposal != null } == true } }
    }

    @Test fun caseFoldedNamesBlockUiGenerationUntilCorrectedAndInvalidDraftCanCancel() {
        val port = ScriptedGateway()
        form(port) { state, closed ->
            compose.onNodeWithText("synthetic scripted provider", substring = true).performScrollTo().assertIsDisplayed()
            replace("original-premise", "A SCRIPTED artisan visits an orchard.")
            replace("original-player-name", "Iris")
            addCast(0, "iris")
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsNotEnabled()
            warning(); noCalls(port)
            compose.onNodeWithTag("original-create").assertDoesNotExist()

            replace("original-cast-0-name", "Mira")
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsEnabled()
            addCast(1, "mIRa")
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsNotEnabled()
            warning(); noCalls(port)
            replace("original-cast-1-name", "Tovin")
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsEnabled().performClick()
            generated(state)
            compose.runOnIdle {
                assertEquals(1, port.begins); assertEquals(1, port.generates)
                assertEquals(listOf("Mira", "Tovin"), port.generatedInput.cast.map { it.name })
                assertEquals(0, port.reviews); assertEquals(0, port.creates)
                assertNull(checkNotNull(state()).review)
            }
            compose.onNodeWithTag("original-create").assertDoesNotExist()

            // Player Mira now conflicts with the retained input cast Mira; Cancel remains usable.
            replace("original-player-name", "Mira")
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsNotEnabled()
            warning()
            compose.onNodeWithTag("original-cancel").assertIsEnabled().performClick()
            compose.waitUntil(5_000) { compose.runOnIdle { closed() } }
            compose.runOnIdle {
                assertNull(state()); assertEquals(1, port.begins); assertEquals(1, port.generates)
                assertEquals(1, port.cancels); assertEquals(0, port.reviews); assertEquals(0, port.creates)
            }
            compose.onNodeWithTag("original-story-dialog").assertDoesNotExist()
        }
    }

    @Test fun aggregateInputBytesStayVisibleAndBlockUiGenerationUntilShortened() {
        val port = ScriptedGateway()
        val premise = "\u00e9".repeat(1024)
        val description = "d".repeat(512)
        form(port) { state, _ ->
            replace("original-premise", premise)
            replace("original-player-name", "Iris")
            replace("original-player-description", description)
            listOf("Mira", "Tovin", "Sel").forEachIndexed { i, name -> addCast(i, name, description) }
            compose.onNodeWithTag("original-premise").assert(hasText(premise))
            compose.onNodeWithTag("original-player-description").assert(hasText(description))
            repeat(3) { compose.onNodeWithTag("original-cast-$it-description").assert(hasText(description)) }
            compose.runOnIdle {
                val input = checkNotNull(state()).input
                assertTrue(validOriginalInput(input))
                assertTrue(localUtf8(OriginalStoryWire.input(input).toString()).size > 4096)
                assertEquals(premise, input.premise); assertEquals(description, input.playerDescription)
                assertTrue(input.cast.all { it.description == description })
            }
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsNotEnabled()
            warning(); noCalls(port)
            compose.onNodeWithTag("original-create").assertDoesNotExist()

            replace("original-premise", "A SCRIPTED artisan waits in an orchard.")
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsEnabled().performClick()
            generated(state)
            compose.runOnIdle {
                assertEquals(1, port.begins); assertEquals(1, port.generates)
                assertEquals("A SCRIPTED artisan waits in an orchard.", port.generatedInput.premise)
                assertEquals(description, port.generatedInput.playerDescription)
                assertTrue(port.generatedInput.cast.all { it.description == description })
                assertEquals(0, port.reviews); assertEquals(0, port.creates)
            }
            compose.onNodeWithTag("original-create").assertDoesNotExist()
        }
    }

    @Test fun aggregateWorldEditsBlockUiReviewThenCorrectedFactsAllowOneReviewWithoutCreate() {
        val port = ScriptedGateway()
        form(port) { state, _ ->
            replace("original-premise", "A SCRIPTED artisan visits an orchard.")
            replace("original-player-name", "Iris")
            addCast(0, "Mira", "A SCRIPTED keeper.")
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsEnabled().performClick()
            generated(state)
            replace("original-title", "SCRIPTED orchard review")
            compose.runOnIdle {
                val current = checkNotNull(state()); val world = checkNotNull(current.proposal)
                assertTrue(validOriginalDraft(current.input, world))
                assertTrue(OriginalStoryWire.valid(current.input, world))
                assertEquals(8, world.facts.size); assertEquals(6, world.beliefs.size); assertEquals(4, world.possessions.size)
                assertEquals(0, port.reviews); assertEquals(0, port.creates)
            }
            compose.onNodeWithTag("original-review").performScrollTo().assertIsEnabled()
            repeat(8) { replace("original-fact-$it", "F$it " + "f".repeat(509)) }
            repeat(6) { replace("original-belief-$it", "B$it " + "b".repeat(509)) }
            repeat(4) { replace("original-possession-$it-description", "P$it " + "p".repeat(509)) }
            compose.runOnIdle {
                val current = checkNotNull(state()); val world = checkNotNull(current.proposal)
                assertTrue(validOriginalDraft(current.input, world))
                assertTrue(localUtf8(OriginalStoryWire.proposal(world).toString()).size > 8192)
                assertEquals(0, port.reviews); assertEquals(0, port.creates)
            }
            compose.onNodeWithTag("original-review").performScrollTo().assertIsNotEnabled()
            warning()
            compose.onNodeWithTag("original-create").assertDoesNotExist()

            repeat(8) { replace("original-fact-$it", "A corrected SCRIPTED fact $it.") }
            compose.runOnIdle {
                val current = checkNotNull(state()); val world = checkNotNull(current.proposal)
                assertTrue(validOriginalDraft(current.input, world))
                assertTrue(localUtf8(OriginalStoryWire.proposal(world).toString()).size <= 8192)
                assertEquals(1, port.begins); assertEquals(1, port.generates)
                assertEquals(0, port.reviews); assertEquals(0, port.creates)
            }
            compose.onNodeWithTag("original-review").performScrollTo().assertIsEnabled().performClick()
            compose.waitUntil(5_000) { compose.runOnIdle { state()?.let { !it.busy && it.review != null } == true } }
            compose.onNodeWithTag("original-create").performScrollTo().assertIsEnabled()
            compose.runOnIdle {
                assertEquals(1, port.begins); assertEquals(1, port.generates); assertEquals(1, port.reviews)
                assertEquals("SCRIPTED orchard review", checkNotNull(port.reviewed).title)
                assertTrue(checkNotNull(port.reviewed).proposal.facts.all { it.text.startsWith("A corrected SCRIPTED fact ") })
                assertEquals(0, port.creates)
            }
        }
    }
}
