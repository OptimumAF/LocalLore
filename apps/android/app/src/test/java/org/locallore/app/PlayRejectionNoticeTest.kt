/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class PlayRejectionNoticeTest {
    private val dispatcher = StandardTestDispatcher()
    private val store = ViewModelStore()
    private var models = 0

    @Before fun setUp() { Dispatchers.setMain(dispatcher) }
    @After fun tearDown() { store.clear(); Dispatchers.resetMain() }

    private fun model(gateway: DemoGateway) = ShellViewModel(gateway).also {
        store.put("rejection-${models++}", it)
    }

    private class SavedGateway(
        private val preparation: DemoResult,
        private val commitment: DemoResult = DemoResult.Rejected("UnexpectedCommit"),
    ) : DemoGateway {
        override val durable = true
        private val story = SavedStory("synthetic-rejection", "main", "The Lantern Garden", 3)
        val saved = SavedSnapshot(
            revision = story.revision,
            potionOwner = "Iris",
            messages = listOf(SceneMessage(1, "A lantern hangs over the gate.", false)),
            location = "Synthetic local save",
            schemaVersion = 1,
            stories = listOf(story),
            selected = story,
            textProvider = TextProvider.SCRIPTED,
        )
        val textRequests = mutableListOf<Pair<PlayInput, Long>>()
        val commits = mutableListOf<DemoResult>()
        var snapshotReads = 0

        override suspend fun initialize() = saved
        override suspend fun snapshot(): SavedSnapshot {
            snapshotReads++
            return saved
        }

        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult =
            error("Free text must remain a text request")

        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
            textRequests += input to revision
            return preparation
        }

        override suspend fun commitAsync(result: DemoResult): DemoResult {
            commits += result
            return commitment
        }
    }

    private fun assertSavedRejection(model: ShellViewModel, gateway: SavedGateway, notice: String) {
        val state = model.state.value
        assertEquals(notice, state.notice)
        assertEquals(gateway.saved.revision, state.revision)
        assertEquals(gateway.saved.potionOwner, state.potionOwner)
        assertEquals(gateway.saved.messages, state.messages)
        assertEquals(gateway.saved.selected, state.selectedStory)
        assertFalse(state.busy)
        assertFalse(state.recoveryRequired)
        assertEquals(1, gateway.snapshotReads)
    }

    @Test fun inventoryRejectionForMatchingFreeTextStaysGeneralAndDoesNotCommit() = runTest(dispatcher) {
        val gateway = SavedGateway(DemoResult.Rejected("Inventory"))
        val model = model(gateway)
        advanceUntilIdle()
        val input = PlayInput(PlayInputKind.ACTION, "Give my potion to Mira.")
        model.submitText(input)
        advanceUntilIdle()

        assertEquals(listOf(input to gateway.saved.revision), gateway.textRequests)
        assertEquals(emptyList<DemoResult>(), gateway.commits)
        assertSavedRejection(model, gateway, inventoryNotice)
    }

    @Test fun abilityRejectionAtCommitKeepsSavedProjectionAndDoesNotMentionBlink() = runTest(dispatcher) {
        val prepared = DemoResult.Prepared(1, 2)
        val gateway = SavedGateway(prepared, DemoResult.Rejected("Ability"))
        val model = model(gateway)
        advanceUntilIdle()
        val input = PlayInput(PlayInputKind.ACTION, "Try the unlearned blink ability.")
        model.submitText(input)
        advanceUntilIdle()

        assertEquals(listOf(input to gateway.saved.revision), gateway.textRequests)
        assertEquals(listOf(prepared), gateway.commits)
        assertSavedRejection(model, gateway, abilityNotice)
    }

    @Test fun typedShortcutKeepsSpecificNoticeOnlyForMatchingRejection() = runTest(dispatcher) {
        val cases = listOf(
            Triple(DemoAction.GIVE_POTION, "Inventory", "You no longer hold the potion. Nothing changed."),
            Triple(DemoAction.TRY_ABILITY, "Ability", "Blink is not learned. Nothing changed."),
            Triple(DemoAction.TRY_ABILITY, "Inventory", inventoryNotice),
            Triple(DemoAction.GIVE_POTION, "Ability", abilityNotice),
        )
        for ((expectedAction, category, notice) in cases) {
            val model = model { action, _, _ ->
                assertEquals(expectedAction, action)
                DemoResult.Rejected(category)
            }
            model.submit(expectedAction)
            advanceUntilIdle()

            assertEquals(notice, model.state.value.notice)
            assertEquals(0L, model.state.value.revision)
            assertEquals(emptyList<SceneMessage>(), model.state.value.messages)
        }
    }

    @Test fun clarificationIsActionableAndUnknownCategoryUsesSafeFallback() = runTest(dispatcher) {
        val cases = listOf(
            "ClarificationRequired" to "The engine needs a clearer request. Rephrase and try again.",
            "Unrecognized private category" to "This response was rejected. Nothing changed; try again.",
        )
        for ((category, notice) in cases) {
            val gateway = SavedGateway(DemoResult.Rejected(category))
            val model = model(gateway)
            advanceUntilIdle()
            model.submitText(PlayInput(PlayInputKind.DIALOGUE, "What is beyond the garden?"))
            advanceUntilIdle()

            assertSavedRejection(model, gateway, notice)
        }
    }

    private companion object {
        const val inventoryNotice = "The inventory rules blocked this action. Check your items and try again."
        const val abilityNotice = "The ability rules blocked this action. Check the abilities available to your character."
    }
}
