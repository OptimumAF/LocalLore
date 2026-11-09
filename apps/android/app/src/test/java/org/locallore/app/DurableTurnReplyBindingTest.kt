/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test

/** Native presentation captures set up reads; fault-injected turn replies exercise the Kotlin boundary. */
@OptIn(ExperimentalCoroutinesApi::class)
class DurableTurnReplyBindingTest {
    private class TurnTransport(corpus: PresentationCaptureCorpus) : WorkspaceTransport {
        private val reads = PresentationCaptureTransport(corpus)
        private val mutations = mutableListOf<JSONObject>()
        val initial = reads.selected
        val gateway = DurableGateway(this, autoCreateIfEmpty = false,
            initialScopeHint = PlayDraftScope(initial.story, initial.branch))
        var reply: suspend (String, JSONObject) -> JSONObject? = { _, _ -> null }
        val calls: List<String> get() = mutations.map { it.getString("op") }
        val submissions: List<JSONObject> get() = mutations.filter { it.getString("op") == "submit" }

        override suspend fun exchange(command: JSONObject): JSONObject {
            val operation = command.getString("op")
            if (operation !in setOf("submit", "turn_status", "prepare", "commit", "cancel"))
                return reads.exchange(command)
            mutations += copy(command)
            val request = submissions.first().getJSONObject("request")
            return reply(operation, request) ?: when (operation) {
                "submit", "turn_status" -> view(request, "queued")
                "prepare" -> view(request, "ready")
                "commit" -> view(request, "committed")
                "cancel" -> view(request, "cancelled")
                else -> error("Unexpected turn operation")
            }
        }

        override fun close() = reads.close()

        fun assertOriginalKey() {
            val submit = submissions.first()
            val request = submit.getJSONObject("request")
            val scope = request.getJSONObject("scope")
            for (command in mutations) {
                assertEquals(submit.getString("session"), command.getString("session"))
                if (command.getString("op") == "submit") {
                    assertEquals(submit.toString(), command.toString())
                } else {
                    assertEquals(scope.getString("story"), command.getJSONObject("scope").getString("story"))
                    assertEquals(scope.getString("branch"), command.getJSONObject("scope").getString("branch"))
                    assertEquals(request.getString("turn"), command.getString("turn"))
                }
            }
        }
    }

    private suspend fun initialized(corpus: PresentationCaptureCorpus): TurnTransport =
        TurnTransport(corpus).also {
            val saved = initializeCaptured(it.gateway)
            assertEquals(it.initial.saved(), saved.selected)
            assertCapturedPresentation(saved.messages, it.initial)
        }

    private suspend fun TurnTransport.submit() =
        gateway.respond(DemoAction.TRY_ABILITY, initial.revision, DemoMode.ACCEPTED)

    private suspend fun lostAcknowledgement(body: suspend () -> Unit) {
        try {
            body()
        } catch (failure: WorkspaceFailure) {
            assertEquals("Io", failure.category)
            return
        }
        fail("Lost acknowledgement was not reported")
    }

    private suspend fun refusePreparation(body: suspend () -> DemoResult) {
        val outcome = try {
            body()
        } catch (_: Exception) {
            return
        }
        assertTrue("The suspect reply prepared or accepted a turn", outcome is DemoResult.Rejected)
    }

    private suspend fun refuseRecovery(body: suspend () -> SavedSnapshot) {
        try {
            body()
        } catch (_: Exception) {
            return
        }
        fail("The suspect recovery reply appeared to succeed")
    }

    @Test fun malformedOrForeignQueuedSubmitCannotPrepareAndKeepsItsKey() = runTest {
        val corpus = PresentationCaptureCorpus()
        val faults: List<(JSONObject) -> Unit> = listOf(
            { it.put("turn", "foreign-turn") },
            { it.getJSONObject("scope").put("story", "foreign-story") },
            { it.getJSONObject("scope").put("branch", "foreign-branch") },
            { it.put("expected_revision", it.getLong("expected_revision").toString()) },
            { it.put("expected_revision", it.getLong("expected_revision") + 0.5) },
        )
        for (fault in faults) {
            val port = initialized(corpus)
            port.reply = { operation, request ->
                if (operation == "submit") view(request, "queued", fault) else null
            }
            refusePreparation { port.submit() }
            assertEquals(listOf("submit"), port.calls)

            port.reply = { operation, request ->
                if (operation == "turn_status") view(request, "cancelled") else null
            }
            port.gateway.recoverSaved()
            assertEquals(listOf("submit", "turn_status"), port.calls)
            port.assertOriginalKey()
        }
        corpus.assertUnchanged()
    }

    @Test fun foreignOrMalformedReadyRecoveryStatusCannotDispatchCommit() = runTest {
        val corpus = PresentationCaptureCorpus()
        val faults: List<(JSONObject) -> Unit> = listOf(
            { it.put("turn", "foreign-turn") },
            { it.getJSONObject("scope").put("branch", "foreign-branch") },
            { it.put("expected_revision", it.getLong("expected_revision").toString()) },
            { it.put("expected_revision", it.getLong("expected_revision") + 0.5) },
            { it.put("phase", "Ready") },
        )
        for (fault in faults) {
            val port = initialized(corpus)
            port.reply = { operation, request ->
                if (operation == "submit") throw WorkspaceFailure("Io")
                view(request, "ready", fault)
            }
            lostAcknowledgement { port.submit() }
            refuseRecovery { port.gateway.recoverSaved() }
            assertEquals(listOf("submit", "turn_status"), port.calls)

            port.reply = { operation, request ->
                if (operation == "turn_status") view(request, "cancelled") else null
            }
            port.gateway.recoverSaved()
            assertEquals(listOf("submit", "turn_status", "turn_status"), port.calls)
            port.assertOriginalKey()
        }
    }

    @Test fun foreignPrepareAfterMatchingQueuedRecoveryCannotDispatchCommit() = runTest {
        val port = initialized(PresentationCaptureCorpus())
        port.reply = { operation, request ->
            when (operation) {
                "submit" -> throw WorkspaceFailure("Io")
                "prepare" -> view(request, "ready") { it.getJSONObject("scope").put("story", "foreign-story") }
                else -> null
            }
        }
        lostAcknowledgement { port.submit() }
        refuseRecovery { port.gateway.recoverSaved() }
        assertEquals(listOf("submit", "turn_status", "prepare"), port.calls)

        port.reply = { operation, request ->
            if (operation == "turn_status") view(request, "cancelled") else null
        }
        port.gateway.recoverSaved()
        assertEquals(listOf("submit", "turn_status", "prepare", "turn_status"), port.calls)
        port.assertOriginalKey()
    }

    @Test fun lostSubmitAcknowledgementRetriesExactlyAndOnlyCommitsAfterBoundReady() = runTest {
        val port = initialized(PresentationCaptureCorpus())
        port.reply = { operation, _ ->
            when {
                operation == "submit" && port.submissions.size == 1 -> throw WorkspaceFailure("Io")
                operation == "turn_status" -> JSONObject().put("version", 1).put("status", "rejected")
                    .put("error", "UnknownTurn")
                else -> null
            }
        }
        lostAcknowledgement { port.submit() }
        port.gateway.recoverSaved()
        port.gateway.recoverSaved()
        assertEquals(listOf("submit", "turn_status", "submit", "prepare", "commit"), port.calls)
        port.assertOriginalKey()
    }

    @Test fun matchingCommittedStatusResolvesLostCommitAcknowledgementWithoutResubmission() = runTest {
        val port = initialized(PresentationCaptureCorpus())
        port.reply = { operation, request ->
            when (operation) {
                "commit" -> throw WorkspaceFailure("Io")
                "turn_status" -> view(request, "committed")
                else -> null
            }
        }
        val prepared = port.submit()
        assertTrue(prepared is DemoResult.Prepared)
        assertEquals(DemoResult.Accepted(port.initial.revision + 1, "", narration),
            port.gateway.commitAsync(prepared))
        port.gateway.recoverSaved()
        assertEquals(listOf("submit", "prepare", "commit", "turn_status"), port.calls)
        port.assertOriginalKey()
    }

    @Test fun matchingReadyCommitReplyDoesNotCompleteRecoveryOrDiscardKey() = runTest {
        val port = initialized(PresentationCaptureCorpus())
        port.reply = { operation, request ->
            when (operation) {
                "submit" -> throw WorkspaceFailure("Io")
                "prepare" -> view(request, "ready") {
                    it.put("expected_revision", request.getLong("expected_revision"))
                }
                "commit" -> view(request, "ready")
                else -> null
            }
        }
        lostAcknowledgement { port.submit() }
        refuseRecovery { port.gateway.recoverSaved() }
        assertEquals(listOf("submit", "turn_status", "prepare", "commit"), port.calls)

        port.reply = { operation, request ->
            if (operation == "turn_status") view(request, "committed") else null
        }
        port.gateway.recoverSaved()
        port.gateway.recoverSaved()
        assertEquals(listOf("submit", "turn_status", "prepare", "commit", "turn_status"), port.calls)
        port.assertOriginalKey()
    }

    @Test fun cancellationRetiresPendingTurnBeforeSuspendedReadyRecoveryReturns() = runTest {
        val port = initialized(PresentationCaptureCorpus())
        val statusEntered = CompletableDeferred<Unit>()
        val resumeStatus = CompletableDeferred<Unit>()
        port.reply = { operation, request ->
            when (operation) {
                "submit" -> throw WorkspaceFailure("Io")
                "turn_status" -> {
                    statusEntered.complete(Unit)
                    resumeStatus.await()
                    view(request, "ready")
                }
                else -> null
            }
        }
        lostAcknowledgement { port.submit() }
        val recovery = async { runCatching { port.gateway.recoverSaved() } }
        runCurrent()
        try {
            assertTrue(statusEntered.isCompleted)
            port.gateway.cancelSaved()
        } finally {
            resumeStatus.complete(Unit)
        }
        val retired = recovery.await()
        assertEquals(listOf("submit", "turn_status", "cancel"), port.calls)
        assertTrue("Retired recovery must not publish a successful snapshot", retired.isFailure)
        port.assertOriginalKey()
    }

    private companion object {
        const val narration = "The synthetic turn was accepted."
        fun copy(value: JSONObject) = JSONObject(value.toString())
        fun view(request: JSONObject, phase: String, edit: (JSONObject) -> Unit = {}): JSONObject {
            val receipt = if (phase == "committed") JSONObject()
                .put("request", copy(request))
                .put("proposal", JSONObject())
                .put("events", JSONArray())
                .put("narration", narration) else JSONObject.NULL
            val data = JSONObject().put("turn", request.getString("turn"))
                .put("scope", copy(request.getJSONObject("scope")))
                .put("expected_revision", request.get("expected_revision"))
                .put("phase", phase)
                .put("error", JSONObject.NULL)
                .put("receipt", receipt)
            edit(data)
            return JSONObject().put("version", 1).put("status", "ok").put("data", data)
        }
    }
}
