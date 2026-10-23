/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class PlayInputViewModelTest {
    private val scheduler = TestCoroutineScheduler()
    private val dispatcher = StandardTestDispatcher(scheduler)
    private val store = ViewModelStore()
    private var models = 0
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }

    private class TextGateway : DemoGateway {
        override val durable = true
        val story = SavedStory("synthetic-input", "main", "Synthetic", 0)
        var provider = TextProvider.SCRIPTED
        var saved = SavedSnapshot(0, "You", emptyList(), "app private", 1, listOf(story), story)
        val received = mutableListOf<Pair<PlayInput, Long>>()
        var prepare: suspend () -> DemoResult = { DemoResult.Prepared(1, 1) }
        var commit: suspend () -> DemoResult = { DemoResult.Rejected("Provider") }
        var commits = 0
        var cancellations = 0
        var closes = 0
        override suspend fun initialize() = snapshot()
        override suspend fun snapshot() = saved.copy(textProvider = provider)
        override suspend fun cancelSaved() = snapshot()
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult =
            error("Text input must not be translated to a typed shortcut")
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
            received += input to revision
            return prepare()
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult { commits++; return commit() }
        override fun cancel() { cancellations++ }
        override fun close() { closes++ }
    }
    private fun model(gateway: TextGateway) = ShellViewModel(gateway).also { store.put("input-${models++}", it) }

    @Test fun inputBoundsCountUtf8AndRejectMalformedUnicodeWithoutChangingOriginalText() {
        fun valid(text: String) = validPlayInput(PlayInput(PlayInputKind.ACTION, text))
        assertTrue(valid("  literal\ntext\t  "))
        assertFalse(valid(" \n\t"))
        assertTrue(valid("a".repeat(2048)))
        assertFalse(valid("a".repeat(2049)))
        assertTrue(valid("\uD83D\uDE80".repeat(512)))
        assertFalse(valid("\uD83D\uDE80".repeat(512) + "a"))
        for (text in listOf("\uD800", "\uDC00", "a\uD800b", "\uD800\uD800", "\u0000x", "x\r", "x\u007f"))
            assertFalse(valid(text))
    }

    @Test fun exactTextKindAndHeadReachTextInterfaceOnceAndPublishOnlyAcceptedSnapshot() = runTest(dispatcher) {
        val gateway = TextGateway()
        val preparation = CompletableDeferred<DemoResult>()
        val commitment = CompletableDeferred<DemoResult>()
        gateway.prepare = { preparation.await() }
        gateway.commit = { commitment.await() }
        val model = model(gateway)
        advanceUntilIdle()
        assertEquals(TextProvider.SCRIPTED, model.state.value.textProvider)
        val input = PlayInput(PlayInputKind.DIALOGUE, "  I claim the lantern is blue.\n\t  ")
        model.submitText(input); model.submitText(input); runCurrent()
        assertEquals(listOf(input to 0L), gateway.received)
        assertTrue(model.state.value.messages.isEmpty())
        preparation.complete(DemoResult.Prepared(1, 1)); runCurrent()
        assertEquals(1, gateway.commits)
        assertTrue(model.state.value.messages.isEmpty())
        gateway.saved = gateway.saved.copy(revision = 1, messages = listOf(
            SceneMessage(1, input.text, true), SceneMessage(2, "Accepted words recorded.", false)))
        commitment.complete(DemoResult.Accepted(999, "forged display", "not the saved narration"))
        advanceUntilIdle()
        assertEquals(1L, model.state.value.revision)
        assertEquals("You", model.state.value.potionOwner)
        assertEquals(gateway.saved.messages, model.state.value.messages)
        assertFalse(model.state.value.busy)
    }

    @Test fun unavailableAndInvalidInputNeverCallProvider() = runTest(dispatcher) {
        val unavailable = TextGateway().also { it.provider = TextProvider.UNAVAILABLE }
        val missing = model(unavailable); advanceUntilIdle()
        missing.submitText(PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira."))
        val gateway = TextGateway(); val ready = model(gateway); advanceUntilIdle()
        for (text in listOf("", "  ", "a".repeat(2049), "\uD800", "x\u0000"))
            ready.submitText(PlayInput(PlayInputKind.DIALOGUE, text))
        advanceUntilIdle()
        assertTrue(unavailable.received.isEmpty())
        assertTrue(gateway.received.isEmpty())
        assertTrue(ready.state.value.messages.isEmpty())
    }

    @Test fun rejectionAndUncertainTransportDoNotPublishTextOrSecondGuessCanon() = runTest(dispatcher) {
        val input = PlayInput(PlayInputKind.ACTION, "private synthetic text")
        val rejected = TextGateway().also { it.prepare = { DemoResult.Rejected("Agency") } }
        val first = model(rejected); advanceUntilIdle(); first.submitText(input); advanceUntilIdle()
        assertEquals(0, rejected.commits)
        assertTrue(first.state.value.messages.isEmpty())
        val uncertain = TextGateway().also { it.prepare = { error(input.text) } }
        val second = model(uncertain); advanceUntilIdle(); second.submitText(input); advanceUntilIdle()
        assertTrue(second.state.value.recoveryRequired)
        assertFalse(second.state.value.notice!!.contains(input.text))
        assertTrue(second.state.value.messages.isEmpty())
        second.submitText(input); advanceUntilIdle()
        assertEquals(1, uncertain.received.size)
        second.recover(); advanceUntilIdle()
        assertFalse(second.state.value.recoveryRequired)
        assertTrue(second.state.value.messages.isEmpty())
    }

    @Test fun cancelFencesAnUncooperativeLateTextPreparation() = runTest(dispatcher) {
        val gateway = TextGateway()
        val late = CompletableDeferred<DemoResult>()
        gateway.prepare = { withContext(NonCancellable) { late.await() } }
        val model = model(gateway); advanceUntilIdle()
        model.submitText(PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira.")); runCurrent()
        model.cancel(); runCurrent()
        late.complete(DemoResult.Prepared(1, 1)); advanceUntilIdle()
        assertEquals(1, gateway.cancellations)
        assertEquals(0, gateway.commits)
        assertEquals(0L, model.state.value.revision)
        assertTrue(model.state.value.messages.isEmpty())
        assertFalse(model.state.value.busy)
    }

    @Test fun disposedTextCallbacksCannotPublishOrReopenResources() = runTest(dispatcher) {
        val gateway = TextGateway()
        val late = CompletableDeferred<DemoResult>()
        gateway.prepare = { withContext(NonCancellable) { late.await() } }
        val model = model(gateway); advanceUntilIdle()
        val input = PlayInput(PlayInputKind.DIALOGUE, "Retained callback")
        model.submitText(input); runCurrent(); store.clear()
        val frozen = model.state.value
        late.complete(DemoResult.Prepared(1, 1)); advanceUntilIdle()
        repeat(2) { model.submitText(input); model.reset(); model.recover() }; advanceUntilIdle()
        assertEquals(frozen, model.state.value)
        assertEquals(1, gateway.received.size)
        assertEquals(0, gateway.commits)
        assertEquals(1, gateway.closes)
    }
}
