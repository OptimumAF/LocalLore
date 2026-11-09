/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Synthetic native replies exercise the production workspace envelope and ownership boundary. */
class LocalInferenceWorkspaceEnvelopeTest {
    private class Gate {
        private val entered = CountDownLatch(1)
        private val released = CountDownLatch(1)

        fun waitForRelease() {
            entered.countDown()
            check(released.await(8, TimeUnit.SECONDS)) { "Fake native call was not released" }
        }

        fun assertEntered() = assertTrue("Fake native call did not begin", entered.await(4, TimeUnit.SECONDS))
        fun release() = released.countDown()
    }

    private class Port(private val reply: (String) -> String) : LocalInferenceNativePort {
        val calls = ConcurrentLinkedQueue<String>()
        val closes = AtomicInteger()
        val closed = CountDownLatch(1)

        override fun call(input: ByteArray): ByteArray {
            val operation = input.toString(Charsets.UTF_8)
            calls.add(operation)
            return reply(operation).toByteArray()
        }

        override fun poll(): LocalInferencePending? = null
        override fun respond(ticket: Long, response: ByteArray): Boolean = error("No role response expected")

        override fun close() {
            closes.incrementAndGet()
            closed.countDown()
        }
    }

    private val ok = """{"version":1,"status":"ok","data":{"phase":"terminal"}}"""

    private fun owner() = LocalInferenceOwner(
        "{}".toByteArray(),
        LocalRoleWorker { error("No SDK role expected") },
        Dispatchers.IO,
        LocalInferenceLimits(turnMs = 5_000, cleanupMs = 5_000, pollMs = 2, authorMs = 5_000),
    )

    private suspend fun LocalInferenceOwner.call(port: Port, operation: String): JSONObject {
        val cancelInput = when (operation) {
            "prepare" -> "cancel"
            "authoring_generate" -> "authoring_cancel"
            else -> null
        }?.toByteArray()
        return executeWorkspace(port, operation, operation.toByteArray(), cancelInput)
    }

    private suspend fun assertQuarantined(owner: LocalInferenceOwner, port: Port, failure: Throwable?) {
        assertTrue("Expected ownership uncertainty, observed $failure", failure is LocalInferenceUncertain)
        assertTrue(owner.quarantined)
        assertTrue(owner.nativeInvalidatedKnown)
        assertEquals(1, port.closes.get())
        val before = port.calls.toList()
        assertTrue(runCatching { owner.call(port, "workspace") }.exceptionOrNull() is LocalInferenceUncertain)
        assertEquals(before, port.calls.toList())
    }

    private fun clean(owner: LocalInferenceOwner, port: Port) {
        owner.close()
        assertTrue("Fake native invalidation did not finish", port.closed.await(4, TimeUnit.SECONDS))
        assertEquals(1, port.closes.get())
    }

    @Test fun malformedOpenAndCommitEnvelopesQuarantineTheWorkspace() = runBlocking {
        val malformed = listOf(
            "open" to "[]",
            "open" to """{"version":"1","status":"ok","data":{}}""",
            "open" to """{"version":2,"status":"ok","data":{}}""",
            "open" to """{"version":1,"status":"unknown","data":{}}""",
            "commit" to """{"version":1,"status":"ok"}""",
            "commit" to """{"version":1,"status":"ok","data":[]}""",
            "commit" to """{"version":1,"status":"rejected","error":false}""",
            "commit" to (ok + "{}"),
            "commit" to (ok + '\u0000' + "{}"),
        )
        for ((operation, reply) in malformed) {
            val owner = owner()
            val port = Port { command -> if (command == operation) reply else ok }
            try {
                val failure = runCatching { owner.call(port, operation) }.exceptionOrNull()
                assertQuarantined(owner, port, failure)
                assertEquals(listOf(operation), port.calls.toList())
            } finally {
                clean(owner, port)
            }
        }
    }

    @Test fun malformedTerminalGenerationEnvelopeCannotLeaveTheWorkspaceUsable() = runBlocking {
        for (operation in listOf("prepare", "authoring_generate")) {
            val owner = owner()
            val port = Port { command ->
                if (command == operation) """{"version":1,"status":"ok","data":null}""" else ok
            }
            try {
                val failure = runCatching { owner.call(port, operation) }.exceptionOrNull()
                assertQuarantined(owner, port, failure)
                assertEquals(operation, port.calls.first())
            } finally {
                clean(owner, port)
            }
        }
    }

    @Test fun cancelledReadStillQuarantinesWhenTheTerminalEnvelopeIsMalformed() = runBlocking {
        val owner = owner()
        val gate = Gate()
        val port = Port { operation ->
            if (operation == "inspection_query") {
                gate.waitForRelease()
                """{"version":1,"status":"ok","data":false}"""
            } else ok
        }
        val outcome = CompletableDeferred<Result<JSONObject>>()
        val reader = launch(start = CoroutineStart.UNDISPATCHED) {
            outcome.complete(runCatching { owner.call(port, "inspection_query") })
        }
        try {
            gate.assertEntered()
            reader.cancel()
            assertFalse(outcome.isCompleted)
            assertFalse(owner.quarantined)
            gate.release()

            withTimeout(5_000) { reader.join() }
            assertQuarantined(owner, port, outcome.await().exceptionOrNull())
            assertEquals(listOf("inspection_query"), port.calls.toList())
        } finally {
            gate.release()
            clean(owner, port)
        }
    }

    @Test fun cancelledReadWithAValidEnvelopeDiscardsOnlyTheReply() = runBlocking {
        val owner = owner()
        val gate = Gate()
        val port = Port { operation ->
            if (operation == "play_presentation_v2") gate.waitForRelease()
            ok
        }
        val outcome = CompletableDeferred<Result<JSONObject>>()
        val reader = launch(start = CoroutineStart.UNDISPATCHED) {
            outcome.complete(runCatching { owner.call(port, "play_presentation_v2") })
        }
        try {
            gate.assertEntered()
            reader.cancel()
            assertFalse(outcome.isCompleted)
            gate.release()

            withTimeout(5_000) { reader.join() }
            assertTrue(outcome.await().exceptionOrNull() is CancellationException)
            assertFalse(owner.quarantined)
            assertEquals("terminal", owner.call(port, "workspace").getJSONObject("data").getString("phase"))
            assertEquals(listOf("play_presentation_v2", "workspace"), port.calls.toList())
            assertEquals(0, port.closes.get())
        } finally {
            gate.release()
            clean(owner, port)
        }
    }

    @Test fun malformedCleanupCancelAcknowledgementQuarantinesEvenAfterGenerationReturns() = runBlocking {
        val owner = owner()
        val gate = Gate()
        val port = Port { operation ->
            when (operation) {
                "prepare" -> {
                    gate.waitForRelease()
                    ok
                }
                "cancel" -> {
                    gate.release()
                    """{"version":1,"status":"rejected"}"""
                }
                else -> ok
            }
        }
        val outcome = CompletableDeferred<Result<JSONObject>>()
        val generation = launch(start = CoroutineStart.UNDISPATCHED) {
            outcome.complete(runCatching { owner.call(port, "prepare") })
        }
        try {
            gate.assertEntered()
            generation.cancel()

            withTimeout(5_000) { generation.join() }
            assertQuarantined(owner, port, outcome.await().exceptionOrNull())
            assertEquals(listOf("prepare", "cancel"), port.calls.toList())
        } finally {
            gate.release()
            clean(owner, port)
        }
    }

    @Test fun validRejectionMetadataAndSuccessPayloadPassThroughWithoutQuarantine() = runBlocking {
        val owner = owner()
        val port = Port { operation ->
            if (operation == "authoring_review") {
                """{"version":1,"status":"rejected","error":"InvalidProposal","review_problem":"RouteReachability"}"""
            } else ok
        }
        try {
            val rejected = owner.call(port, "authoring_review")
            assertEquals("rejected", rejected.getString("status"))
            assertEquals("InvalidProposal", rejected.getString("error"))
            assertEquals("RouteReachability", rejected.getString("review_problem"))

            val followUp = owner.call(port, "commit")
            assertEquals("ok", followUp.getString("status"))
            assertEquals("terminal", followUp.getJSONObject("data").getString("phase"))
            assertFalse(owner.quarantined)
            assertEquals(0, port.closes.get())
        } finally {
            clean(owner, port)
        }
    }
}
