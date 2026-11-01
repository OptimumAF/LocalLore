/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class OriginalStoryInputValidationTest {
    private val input = OriginalInput("A clockmaker crosses a frozen orchard.", "Iris")
    private val world = OriginalProposal(
        listOf(OriginalLocation("Orchard", "Frost covers the trees.")), 0,
        listOf(OriginalCharacter("Tovin", "A patient gardener.", 0, listOf(0, 1))),
        emptyList(), emptyList(), emptyList(), emptyList())

    private class Gateway(private val world: OriginalProposal) : OriginalStoryGateway {
        var begins = 0
        var generations = 0
        var reviews = 0
        private lateinit var input: OriginalInput
        override suspend fun originalCapabilities() = OriginalCapabilities(true, "scripted")
        override suspend fun beginOriginal(input: OriginalInput): OriginalJob {
            begins++; this.input = input
            return OriginalJob("job-1", "a".repeat(64), "scripted")
        }
        override suspend fun generateOriginal(job: String): OriginalGenerated {
            generations++
            return OriginalGenerated(job, input, world, "scripted")
        }
        override suspend fun reviewOriginal(job: String, input: OriginalInput,
            proposal: OriginalProposal, title: String): OriginalReview {
            reviews++
            return OriginalReview(job, "b".repeat(64), input, proposal, title, listOf("Review the world."))
        }
        override suspend fun cancelOriginal(job: String) = true
        override suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot =
            error("These input tests never authorize creation")
    }

    @Test fun generatePredicateRejectsPlayerCastCollisionIgnoringCase() {
        assertFalse(OriginalStoryWire.valid(input.copy(cast = listOf(OriginalCast("iris", "A gardener.")))))
    }

    @Test fun generatePredicateRejectsCastCastCollisionIgnoringCase() {
        assertFalse(OriginalStoryWire.valid(input.copy(cast = listOf(
            OriginalCast("Tovin", "A gardener."), OriginalCast("tOvIn", "A clockmaker.")))))
    }

    @Test fun collidingNamesNeverReachTheGenerationGateway() = runTest {
        val gateway = Gateway(world)
        lateinit var state: OriginalStoryUiState
        val controller = OriginalStoryController(gateway, this, { state = it }, {})
        controller.open(OriginalCapabilities(true, "scripted"))
        for (cast in listOf(listOf(OriginalCast("IRIS", "A gardener.")),
            listOf(OriginalCast("Tovin", "A gardener."), OriginalCast("tovin", "A clockmaker.")))) {
            controller.edit(state, input.copy(cast = cast), null, "Orchard")
            controller.generate(state); advanceUntilIdle()
            assertEquals(0, gateway.begins); assertEquals(0, gateway.generations); assertEquals(0, gateway.reviews)
            assertNull(state.job); assertFalse(state.busy)
        }
        controller.dispose()
    }

    @Test fun correctingTheNameEnablesExactlyOneGeneration() = runTest {
        val gateway = Gateway(world)
        lateinit var state: OriginalStoryUiState
        val controller = OriginalStoryController(gateway, this, { state = it }, {})
        controller.open(OriginalCapabilities(true, "scripted"))
        controller.edit(state, input.copy(cast = listOf(OriginalCast("iris", "A gardener."))), null, "Orchard")
        controller.generate(state); advanceUntilIdle()
        assertEquals(0, gateway.begins)
        controller.edit(state, OriginalStoryEdit.Text(OriginalTextField.CAST_NAME, "Tovin", 0))
        assertTrue(OriginalStoryWire.valid(state.input))
        controller.generate(state); advanceUntilIdle()
        assertEquals(1, gateway.begins); assertEquals(1, gateway.generations); assertEquals(0, gateway.reviews)
        assertEquals(world, state.proposal); assertFalse(state.busy)
        controller.dispose()
    }

    private fun oversizedInput() = input.copy(premise = "é".repeat(1024),
        playerDescription = "p".repeat(512), cast = listOf(
            OriginalCast("Tovin", "a".repeat(512)), OriginalCast("Sera", "b".repeat(512)),
            OriginalCast("Rowan", "c".repeat(512))))

    @Test fun aggregateInputLimitPreventsGenerationBeforeBegin() = runTest {
        val oversized = oversizedInput()
        assertTrue(validOriginalInput(oversized)) // Every individual field is within its own limit.
        assertTrue(localUtf8(OriginalStoryWire.input(oversized).toString()).size > 4096)
        assertFalse(OriginalStoryWire.valid(oversized))
        val gateway = Gateway(world)
        lateinit var state: OriginalStoryUiState
        val controller = OriginalStoryController(gateway, this, { state = it }, {})
        controller.open(OriginalCapabilities(true, "scripted"))
        controller.edit(state, oversized, null, "Orchard")
        controller.generate(state); advanceUntilIdle()
        assertEquals(0, gateway.begins); assertEquals(0, gateway.generations); assertEquals(0, gateway.reviews)
        assertNull(state.job); assertFalse(state.busy)
        controller.dispose()
    }

    @Test fun reviewRejectsPlayerCastCollisionAfterGeneration() = runTest {
        val gateway = Gateway(world)
        lateinit var state: OriginalStoryUiState
        val controller = OriginalStoryController(gateway, this, { state = it }, {})
        controller.open(OriginalCapabilities(true, "scripted"))
        controller.edit(state, input, null, "Orchard"); controller.generate(state); advanceUntilIdle()
        controller.edit(state, state.input.copy(playerName = "tOvIn"), state.proposal, state.title)
        controller.review(state); advanceUntilIdle()
        assertEquals(1, gateway.begins); assertEquals(1, gateway.generations); assertEquals(0, gateway.reviews)
        assertNull(state.review); assertFalse(state.busy)
        controller.dispose()
    }

    @Test fun reviewRetainsDraftDomainValidation() = runTest {
        val gateway = Gateway(world)
        lateinit var state: OriginalStoryUiState
        val controller = OriginalStoryController(gateway, this, { state = it }, {})
        controller.open(OriginalCapabilities(true, "scripted"))
        controller.edit(state, input, null, "Orchard"); controller.generate(state); advanceUntilIdle()
        controller.edit(state, state.input, world.copy(playerLocation = 1), state.title)
        controller.review(state); advanceUntilIdle()
        assertEquals(0, gateway.reviews); assertNull(state.review)
        controller.dispose()
    }

    @Test fun reviewRejectsAggregateProposalLimit() = runTest {
        val oversized = world.copy(facts = List(8) { OriginalFact("f".repeat(512), listOf(0), null) },
            beliefs = List(6) { OriginalBelief(1, "b".repeat(512), "suspected") },
            possessions = List(4) { OriginalPossession("Token$it", "p".repeat(512), 0, null) })
        assertTrue(validOriginalDraft(input, oversized))
        assertTrue(localUtf8(OriginalStoryWire.proposal(oversized).toString()).size > 8192)
        assertFalse(OriginalStoryWire.valid(input, oversized))
        val gateway = Gateway(oversized)
        lateinit var state: OriginalStoryUiState
        val controller = OriginalStoryController(gateway, this, { state = it }, {})
        controller.open(OriginalCapabilities(true, "scripted"))
        controller.edit(state, input, null, "Orchard"); controller.generate(state); advanceUntilIdle()
        controller.review(state); advanceUntilIdle()
        assertEquals(1, gateway.begins); assertEquals(1, gateway.generations); assertEquals(0, gateway.reviews)
        assertNull(state.review); assertFalse(state.busy)
        controller.dispose()
    }
}
