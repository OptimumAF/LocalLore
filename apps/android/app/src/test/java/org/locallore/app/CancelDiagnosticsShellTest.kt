/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Controller-only faults. Actual Android JSON/gateway integration is a separate test selection. */
@OptIn(ExperimentalCoroutinesApi::class)
class CancelDiagnosticsShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val store = ViewModelStore()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }

    private val story = SavedStory("synthetic", "main", "Synthetic", 0)
    private val saved = SavedSnapshot(0, "You", emptyList(), "/synthetic/local", 1, listOf(story), story)
    private inner class Gateway : DemoGateway {
        override val durable = true
        val acknowledgement = CompletableDeferred<SavedSnapshot>()
        override suspend fun initialize() = saved
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult = awaitCancellation()
        override suspend fun cancelSaved() = acknowledgement.await()
    }
    private fun start(gateway: Gateway, log: DiagnosticLog): ShellViewModel =
        ShellViewModel(gateway, log).also { store.put("model", it) }

    @Test fun delayedAcknowledgementHasNoCompletedCancellationRecord() = runTest(dispatcher) {
        val gateway = Gateway(); val log = DiagnosticLog(); val model = start(gateway, log)
        runCurrent(); model.submit(DemoAction.GIVE_POTION); runCurrent()
        model.cancel(); runCurrent()
        val pending = log.snapshot().json
        gateway.acknowledgement.complete(saved); advanceUntilIdle()
        assertFalse("Cancellation is not confirmed while reconciliation is pending", pending.contains("\"phase\":\"CANCEL\""))
        assertTrue(log.snapshot().json.contains("\"phase\":\"CANCEL\",\"outcome\":\"COMPLETED\""))
        assertFalse(model.state.value.busy)
        assertFalse(model.state.value.recoveryRequired)
    }

    @Test fun failedAcknowledgementRecordsUncertaintyWithoutPrivateFailureText() = runTest(dispatcher) {
        val gateway = Gateway(); val log = DiagnosticLog(); val model = start(gateway, log)
        runCurrent(); model.submit(DemoAction.GIVE_POTION); runCurrent()
        model.cancel(); runCurrent()
        gateway.acknowledgement.completeExceptionally(IllegalStateException("PRIVATE synthetic transport detail"))
        advanceUntilIdle()
        val diagnostic = log.snapshot().json
        assertTrue(model.state.value.recoveryRequired)
        assertFalse(model.state.value.busy)
        assertTrue(model.state.value.messages.isEmpty())
        assertFalse(diagnostic.contains("\"phase\":\"CANCEL\",\"outcome\":\"COMPLETED\""))
        assertTrue(diagnostic.contains("\"phase\":\"CANCEL\",\"outcome\":\"UNKNOWN\""))
        assertTrue(diagnostic.contains("\"error\":\"TRANSPORT\""))
        assertFalse(diagnostic.contains("PRIVATE"))
        assertFalse(model.state.value.notice!!.contains("PRIVATE"))
    }

    @Test fun disposalWhileAcknowledgementIsPendingCannotReportCompletion() = runTest(dispatcher) {
        val gateway = Gateway(); val log = DiagnosticLog(); val model = start(gateway, log)
        runCurrent(); model.submit(DemoAction.GIVE_POTION); runCurrent()
        model.cancel(); runCurrent(); store.clear()
        gateway.acknowledgement.complete(saved); advanceUntilIdle()
        assertFalse(log.snapshot().json.contains("\"phase\":\"CANCEL\""))
        assertTrue(model.state.value.messages.isEmpty())
    }
}
