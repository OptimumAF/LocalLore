/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Captured native reads with fault injection only at the Kotlin session reply boundary. */
@OptIn(ExperimentalCoroutinesApi::class)
class DurableSessionReplyBindingTest {
    private class SessionTransport(corpus: PresentationCaptureCorpus, hint: PlayDraftScope? = null) :
        WorkspaceTransport {
        private val reads = PresentationCaptureTransport(corpus)
        val commands = mutableListOf<JSONObject>()
        val gateway = DurableGateway(this, autoCreateIfEmpty = false, initialScopeHint = hint)
        var resumeReply: suspend (JSONObject) -> JSONObject = { it }
        var openReply: suspend (JSONObject) -> JSONObject = { it }
        var closeReply: suspend (JSONObject) -> JSONObject = { it }

        override suspend fun exchange(command: JSONObject): JSONObject {
            commands += JSONObject(command.toString())
            val reply = reads.exchange(command)
            return when (command.getString("op")) {
                "resume" -> resumeReply(reply)
                "open" -> openReply(reply)
                "close" -> closeReply(reply)
                else -> reply
            }
        }

        override fun close() = reads.close()

        fun resumeScopes() = commands.filter { it.getString("op") == "resume" }.map {
            val scope = it.getJSONObject("scope")
            PlayDraftScope(scope.getString("story"), scope.getString("branch"))
        }

        fun readsInOrder() = commands.filter {
            it.getString("op") in setOf("open", "play_presentation_v2")
        }
    }

    private fun mainTransport(corpus: PresentationCaptureCorpus): SessionTransport =
        corpus.case("main").let { SessionTransport(corpus, PlayDraftScope(it.story, it.branch)) }

    private fun assertCategory(category: String, failure: Throwable?) {
        assertEquals("Expected $category; observed $failure", category, (failure as? WorkspaceFailure)?.category)
    }

    private fun assertReadOwner(commands: List<JSONObject>, case: PresentationCapturedCase) {
        val session = case.envelope("resumed").getJSONObject("data").getString("session")
        assertEquals(listOf("open", "play_presentation_v2"), commands.map { it.getString("op") })
        for (command in commands) {
            assertEquals(session, command.getString("session"))
            val scope = command.getJSONObject("scope")
            assertEquals(case.story, scope.getString("story"))
            assertEquals(case.branch, scope.getString("branch"))
        }
        assertEquals(case.revision, commands.last().getLong("expected_revision"))
    }

    private fun assertSavedCase(saved: SavedSnapshot, case: PresentationCapturedCase) {
        assertEquals(case.saved(), saved.selected)
        assertEquals(case.revision, saved.revision)
        assertCapturedPresentation(saved.messages, case)
    }

    @Test fun foreignStartupHintAcknowledgementCannotAttachAndHintRemainsForExactRetry() = runTest {
        val corpus = PresentationCaptureCorpus()
        val target = corpus.case("corrected")
        val hint = PlayDraftScope(target.story, target.branch)
        val port = SessionTransport(corpus, hint)
        port.resumeReply = { corpus.case("rediscovered").envelope("resumed") }

        assertCategory("Stale", runCatching { port.gateway.initialize() }.exceptionOrNull())
        assertEquals(listOf(hint), port.resumeScopes())
        assertTrue(port.readsInOrder().isEmpty())

        port.resumeReply = { it }
        assertSavedCase(port.gateway.initialize(), target)
        assertEquals(listOf(hint, hint), port.resumeScopes())
        assertReadOwner(port.readsInOrder(), target)
        corpus.assertUnchanged()
    }

    @Test fun malformedStartupResumeAcknowledgementsCannotDispatchOpenOrPresentation() = runTest {
        val corpus = PresentationCaptureCorpus()
        val faults: List<(JSONObject) -> Unit> = listOf(
            { it.remove("session") },
            { it.put("session", "") },
            { it.put("session", "a".repeat(129)) },
            { it.getJSONObject("scope").put("foreign", true) },
            { it.put("revision", it.getLong("revision").toString()) },
            { it.put("revision", it.getLong("revision") + 0.5) },
            { it.put("revision", -1) },
            { it.put("extra", true) },
        )
        for (fault in faults) {
            val port = SessionTransport(corpus)
            port.resumeReply = { it.apply { fault(getJSONObject("data")) } }

            assertCategory("Malformed", runCatching { port.gateway.initialize() }.exceptionOrNull())
            assertEquals(1, port.resumeScopes().size)
            assertTrue(port.readsInOrder().isEmpty())
        }
    }

    @Test fun explicitResumeRefusesForeignAndMalformedRepliesThenAcceptsNewerExactHead() = runTest {
        val corpus = PresentationCaptureCorpus()
        val port = mainTransport(corpus)
        assertSavedCase(port.gateway.initialize(), corpus.case("main"))
        port.commands.clear()

        val target = corpus.case("corrected")
        val requested = target.saved().copy(revision = target.revision - 2)
        port.resumeReply = { corpus.case("empty").envelope("resumed") }
        assertCategory("Stale", runCatching { port.gateway.resumeSaved(requested) }.exceptionOrNull())
        assertTrue(port.readsInOrder().isEmpty())

        port.resumeReply = { it.apply { getJSONObject("data").put("revision", target.revision - 0.5) } }
        assertCategory("Malformed", runCatching { port.gateway.resumeSaved(requested) }.exceptionOrNull())
        assertTrue(port.readsInOrder().isEmpty())

        // The user's saved row can be older than Resume, and Open can advance it again.
        port.resumeReply = { it.apply { getJSONObject("data").put("revision", target.revision - 1) } }
        assertSavedCase(port.gateway.resumeSaved(requested), target)
        val targetScope = PlayDraftScope(target.story, target.branch)
        assertEquals(listOf(targetScope, targetScope, targetScope), port.resumeScopes())
        assertReadOwner(port.readsInOrder(), target)
    }

    @Test fun foreignOrMalformedOpenCannotDispatchPresentationOrReplaceAttachment() = runTest {
        val corpus = PresentationCaptureCorpus()
        val target = corpus.case("main")
        val port = mainTransport(corpus)
        assertSavedCase(port.gateway.initialize(), target)
        val faults: List<Pair<String, (JSONObject) -> Unit>> = listOf(
            "Stale" to { it.put("session", "different-session") },
            "Stale" to { it.getJSONObject("scope").put("story", "different-story") },
            "Stale" to { it.getJSONObject("scope").put("branch", "different-branch") },
            "Malformed" to { it.remove("session") },
            "Malformed" to { it.put("session", false) },
            "Malformed" to { it.getJSONObject("scope").put("extra", true) },
            "Malformed" to { it.put("revision", it.getLong("revision").toString()) },
            "Malformed" to { it.put("revision", it.getLong("revision") + 0.5) },
            "Malformed" to { it.put("revision", -1) },
        )
        for ((category, fault) in faults) {
            port.commands.clear()
            port.openReply = { it.apply { fault(getJSONObject("data")) } }
            assertCategory(category, runCatching { port.gateway.snapshot() }.exceptionOrNull())
            assertEquals(listOf("open"), port.commands.map { it.getString("op") })
        }

        port.commands.clear()
        port.openReply = { it }
        assertSavedCase(port.gateway.snapshot(), target)
        assertReadOwner(port.readsInOrder(), target)
    }

    @Test fun lateResumeCannotReplaceAnotherAttachmentInstalledWhileItWasSuspended() = runTest {
        val corpus = PresentationCaptureCorpus()
        val port = mainTransport(corpus)
        assertSavedCase(port.gateway.initialize(), corpus.case("main"))
        port.commands.clear()

        val oldTarget = corpus.case("corrected")
        val newTarget = corpus.case("rediscovered")
        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        port.resumeReply = { reply ->
            val scope = reply.getJSONObject("data").getJSONObject("scope")
            if (scope.getString("branch") == oldTarget.branch) {
                entered.complete(Unit)
                release.await()
            }
            reply
        }

        val late = async { runCatching { port.gateway.resumeSaved(oldTarget.saved()) } }
        try {
            runCurrent()
            assertTrue(entered.isCompleted)
            val newer = async { runCatching { port.gateway.resumeSaved(newTarget.saved()) } }
            runCurrent()
            assertTrue("The newer attachment must install before the older reply returns", newer.isCompleted)
            assertSavedCase(newer.await().getOrThrow(), newTarget)
            assertReadOwner(port.readsInOrder(), newTarget)
        } finally {
            release.complete(Unit)
        }

        assertCategory("Stale", late.await().exceptionOrNull())
        assertEquals(listOf(
            PlayDraftScope(oldTarget.story, oldTarget.branch),
            PlayDraftScope(newTarget.story, newTarget.branch),
        ), port.resumeScopes())
        assertReadOwner(port.readsInOrder(), newTarget)
        port.commands.clear()
        assertSavedCase(port.gateway.snapshot(), newTarget)
        assertReadOwner(port.readsInOrder(), newTarget)
    }

    @Test fun staleCloseCompletionCannotDispatchAnOlderResume() = runTest {
        val corpus = PresentationCaptureCorpus()
        val port = mainTransport(corpus)
        assertSavedCase(port.gateway.initialize(), corpus.case("main"))
        port.commands.clear()

        val oldTarget = corpus.case("corrected")
        val newTarget = corpus.case("rediscovered")
        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        port.closeReply = { reply ->
            if (entered.complete(Unit)) release.await()
            reply
        }

        val late = async { runCatching { port.gateway.resumeSaved(oldTarget.saved()) } }
        try {
            runCurrent()
            assertTrue(entered.isCompleted)
            assertTrue(port.resumeScopes().isEmpty())
            val newer = async { runCatching { port.gateway.resumeSaved(newTarget.saved()) } }
            runCurrent()
            assertTrue("The newer resume must finish while the earlier close reply waits", newer.isCompleted)
            assertSavedCase(newer.await().getOrThrow(), newTarget)
            assertReadOwner(port.readsInOrder(), newTarget)
        } finally {
            release.complete(Unit)
        }

        assertCategory("Stale", late.await().exceptionOrNull())
        assertEquals(listOf(PlayDraftScope(newTarget.story, newTarget.branch)), port.resumeScopes())
        assertReadOwner(port.readsInOrder(), newTarget)
        port.commands.clear()
        assertSavedCase(port.gateway.snapshot(), newTarget)
        assertReadOwner(port.readsInOrder(), newTarget)
    }

    @Test fun staleReconcileCloseCannotReopenLibraryAfterNewerResume() = runTest {
        val corpus = PresentationCaptureCorpus()
        val port = mainTransport(corpus)
        assertSavedCase(port.gateway.initialize(), corpus.case("main"))
        port.commands.clear()

        val target = corpus.case("rediscovered")
        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        port.closeReply = { reply ->
            if (entered.complete(Unit)) release.await()
            reply
        }

        val late = async { runCatching { port.gateway.reconcileSaved() } }
        val beforeLateReply = try {
            runCurrent()
            assertTrue(entered.isCompleted)
            assertEquals(listOf("close"), port.commands.map { it.getString("op") })
            val newer = async { runCatching { port.gateway.resumeSaved(target.saved()) } }
            runCurrent()
            assertTrue("The newer resume must finish while reconcile waits for Close", newer.isCompleted)
            assertSavedCase(newer.await().getOrThrow(), target)
            assertReadOwner(port.readsInOrder(), target)
            port.commands.map(JSONObject::toString)
        } finally {
            release.complete(Unit)
        }

        assertCategory("Stale", late.await().exceptionOrNull())
        assertEquals(beforeLateReply, port.commands.map(JSONObject::toString))
        port.commands.clear()
        assertSavedCase(port.gateway.snapshot(), target)
        assertReadOwner(port.readsInOrder(), target)
    }

    @Test fun staleOpenCompletionCannotDispatchPresentationAfterNewerSnapshot() = runTest {
        val corpus = PresentationCaptureCorpus()
        val target = corpus.case("main")
        val port = mainTransport(corpus)
        assertSavedCase(port.gateway.initialize(), target)
        port.commands.clear()

        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        port.openReply = { reply ->
            if (entered.complete(Unit)) release.await()
            reply
        }

        val late = async { runCatching { port.gateway.snapshot() } }
        try {
            runCurrent()
            assertTrue(entered.isCompleted)
            assertEquals(listOf("open"), port.readsInOrder().map { it.getString("op") })
            val newer = async { runCatching { port.gateway.snapshot() } }
            runCurrent()
            assertTrue("The newer snapshot must finish while the earlier Open reply waits", newer.isCompleted)
            assertSavedCase(newer.await().getOrThrow(), target)
        } finally {
            release.complete(Unit)
        }

        assertCategory("Stale", late.await().exceptionOrNull())
        val reads = port.readsInOrder()
        assertEquals(listOf("open", "open", "play_presentation_v2"), reads.map { it.getString("op") })
        assertReadOwner(reads.drop(1), target)
        port.commands.clear()
        assertSavedCase(port.gateway.snapshot(), target)
        assertReadOwner(port.readsInOrder(), target)
    }
}
