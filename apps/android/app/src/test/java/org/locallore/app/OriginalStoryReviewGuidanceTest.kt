/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class OriginalStoryReviewGuidanceTest {
    private val input = OriginalInput("An apprentice carries a lantern to a watchtower.", "Iris")
    private val world = OriginalProposal(
        locations = listOf(
            OriginalLocation("Garden", "A walled garden."),
            OriginalLocation("Tower", "A watchtower."),
        ),
        playerLocation = 0,
        characters = listOf(OriginalCharacter("Sel", "A gardener.", 1, listOf(0))),
        routes = emptyList(),
        facts = emptyList(),
        beliefs = emptyList(),
        possessions = emptyList(),
    )

    private fun rejected(
        problem: Any? = null,
        status: String = "rejected",
        category: String = "InvalidProposal",
    ) = JSONObject().put("version", 1).put("status", status).put("error", category)
        .put("review_problem", problem)

    private suspend fun failureFrom(
        expectedOperation: String,
        reply: JSONObject,
        act: suspend (DurableGateway) -> Unit,
    ): WorkspaceFailure {
        val gateway = DurableGateway(object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                assertEquals(expectedOperation, command.getString("op"))
                return reply
            }

            override fun close() = Unit
        })
        return try {
            act(gateway)
            error("The native refusal must not produce a result")
        } catch (failure: WorkspaceFailure) {
            failure
        }
    }

    @Test fun exactReviewRefusalCodesBecomeTypedGuidance() = runTest {
        for ((code, expected) in listOf(
            "RouteReachability" to OriginalReviewProblem.ROUTE_REACHABILITY,
            "CharacterSelfKnowledge" to OriginalReviewProblem.CHARACTER_SELF_KNOWLEDGE,
        )) {
            val failure = failureFrom("authoring_review", rejected(code)) {
                it.reviewOriginal("job-1", input, world, "Watchtower")
            }
            assertEquals("InvalidProposal", failure.category)
            assertEquals(expected, failure.originalReviewProblem)
        }
    }

    @Test fun absentMalformedOrOutOfScopeReviewCodesCannotBecomeGuidance() = runTest {
        val replies = listOf(
            rejected(),
            rejected(JSONObject.NULL),
            rejected(true),
            rejected(1),
            rejected(JSONArray(listOf("RouteReachability"))),
            rejected(JSONObject().put("reason", "RouteReachability")),
            rejected("routeReachability"),
            rejected("RouteReachability "),
            rejected("CharacterSelfKnowledge: private text"),
            rejected("RouteReachability", category = "Stale"),
            rejected("RouteReachability", status = "error"),
        )
        for (reply in replies) {
            val failure = failureFrom("authoring_review", reply) {
                it.reviewOriginal("job-1", input, world, "Watchtower")
            }
            assertNull(failure.originalReviewProblem)
        }
        val unrelated = failureFrom("authoring_generate", rejected("RouteReachability")) {
            it.generateOriginal("job-1")
        }
        assertNull(unrelated.originalReviewProblem)
    }

    private inner class ScriptedPort : OriginalStoryGateway {
        private lateinit var captured: OriginalInput
        var generateError: WorkspaceFailure? = null
        var review: suspend (OriginalInput, OriginalProposal, String) -> OriginalReview =
            { currentInput, currentWorld, title ->
                OriginalReview("job-1", "b".repeat(64), currentInput, currentWorld, title,
                    listOf("A synthetic reviewed starting world."))
            }
        var creates = 0

        override suspend fun originalCapabilities() = OriginalCapabilities(true, "scripted")

        override suspend fun beginOriginal(input: OriginalInput): OriginalJob {
            captured = input
            return OriginalJob("job-1", "a".repeat(64), "scripted")
        }

        override suspend fun generateOriginal(job: String): OriginalGenerated {
            generateError?.let { throw it }
            return OriginalGenerated(job, captured, world, "scripted")
        }

        override suspend fun reviewOriginal(
            job: String, input: OriginalInput, proposal: OriginalProposal, title: String,
        ) = review(input, proposal, title)

        override suspend fun cancelOriginal(job: String) = true

        override suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot {
            creates++
            error("These tests do not authorize creating a story")
        }
    }

    private inner class Form(scope: CoroutineScope) {
        val port = ScriptedPort()
        val published = mutableListOf<OriginalStoryUiState>()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = OriginalStoryController(port, scope, published::add, closed::add)
        val state: OriginalStoryUiState get() = published.last()

        init {
            controller.open(OriginalCapabilities(true, "scripted"))
            controller.edit(state, input, null, "Watchtower")
        }

        fun refuse(problem: OriginalReviewProblem) {
            port.review = { _, _, _ -> throw WorkspaceFailure("InvalidProposal", problem) }
            controller.review(state)
        }

        fun assertGuidance(problem: OriginalReviewProblem) {
            assertEquals(problem, state.reviewProblem)
            assertFalse(state.busy)
            assertNull(state.review)
            assertNull(state.notice)
            assertNotNull(state.proposal)
            assertEquals(0, port.creates)
        }
    }

    @Test fun typedCurrentRefusalPreservesDraftAndOnlyFreshReviewRestoresConsent() = runTest {
        val form = Form(this)
        val accept = form.port.review
        form.controller.generate(form.state)
        advanceUntilIdle()
        val ready = form.state

        form.refuse(OriginalReviewProblem.ROUTE_REACHABILITY)
        advanceUntilIdle()
        form.assertGuidance(OriginalReviewProblem.ROUTE_REACHABILITY)
        assertEquals(ready.input, form.state.input)
        assertEquals(ready.proposal, form.state.proposal)
        assertEquals(ready.title, form.state.title)
        assertEquals(ready.job, form.state.job)

        form.controller.edit(form.state, OriginalStoryEdit.ToggleRoute(0, 1))
        assertNull(form.state.reviewProblem)
        assertEquals(listOf(OriginalRoute(0, 1)), form.state.proposal!!.routes)
        form.refuse(OriginalReviewProblem.CHARACTER_SELF_KNOWLEDGE)
        advanceUntilIdle()
        form.assertGuidance(OriginalReviewProblem.CHARACTER_SELF_KNOWLEDGE)

        form.controller.review(form.state)
        assertNull(form.state.reviewProblem)
        assertNull(form.state.review)
        assertTrue(form.state.busy)
        advanceUntilIdle()
        form.assertGuidance(OriginalReviewProblem.CHARACTER_SELF_KNOWLEDGE)
        form.controller.edit(form.state, OriginalStoryEdit.ToggleKnown(OriginalKnown.CHARACTER, 0, 1))
        assertNull(form.state.reviewProblem)
        assertEquals(listOf(0, 1), form.state.proposal!!.characters.single().knownBy)

        form.port.review = accept
        form.controller.review(form.state)
        advanceUntilIdle()
        assertNotNull(form.state.review)
        assertEquals(0, form.port.creates)
        form.controller.dispose()
    }

    @Test fun genericAndNonReviewFailuresDoNotPublishReviewGuidance() = runTest {
        val form = Form(this)
        form.controller.generate(form.state)
        advanceUntilIdle()

        for (failure in listOf(
            WorkspaceFailure("InvalidProposal"),
            WorkspaceFailure("Io", OriginalReviewProblem.ROUTE_REACHABILITY),
        )) {
            form.port.review = { _, _, _ -> throw failure }
            form.controller.review(form.state)
            advanceUntilIdle()
            assertNull(form.state.reviewProblem)
            assertNull(form.state.review)
            assertNotNull(form.state.notice)
            assertFalse(form.state.busy)
        }

        form.refuse(OriginalReviewProblem.ROUTE_REACHABILITY)
        advanceUntilIdle()
        form.assertGuidance(OriginalReviewProblem.ROUTE_REACHABILITY)
        form.port.generateError = WorkspaceFailure("InvalidProposal", OriginalReviewProblem.ROUTE_REACHABILITY)
        form.controller.generate(form.state)
        assertNull(form.state.reviewProblem)
        advanceUntilIdle()
        assertNull(form.state.reviewProblem)
        assertNotNull(form.state.notice)
        assertFalse(form.state.busy)
        assertEquals(0, form.port.creates)
        form.controller.dispose()
    }

    @Test fun dismissalClearsGuidanceAndFencesAReviewRefusalThatReturnsLate() = runTest {
        val form = Form(this)
        form.controller.generate(form.state)
        advanceUntilIdle()
        form.refuse(OriginalReviewProblem.ROUTE_REACHABILITY)
        advanceUntilIdle()
        form.assertGuidance(OriginalReviewProblem.ROUTE_REACHABILITY)

        val release = CompletableDeferred<Unit>()
        var returnedLate = false
        form.port.review = { _, _, _ ->
            withContext(NonCancellable) {
                release.await()
                returnedLate = true
                throw WorkspaceFailure("InvalidProposal", OriginalReviewProblem.CHARACTER_SELF_KNOWLEDGE)
            }
        }
        form.controller.review(form.state)
        runCurrent()
        form.controller.dismiss()
        runCurrent()
        val closing = form.state
        assertTrue(closing.closing)
        assertNull(closing.reviewProblem)
        assertTrue(form.closed.isEmpty())

        release.complete(Unit)
        advanceUntilIdle()
        assertTrue(returnedLate)
        assertSame(closing, form.state)
        assertEquals(listOf(StoryCreationClose()), form.closed)
        assertEquals(0, form.port.creates)
        form.controller.dispose()
    }
}
