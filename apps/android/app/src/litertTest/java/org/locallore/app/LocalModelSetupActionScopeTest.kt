/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import java.io.ByteArrayInputStream
import java.io.InputStream
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
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class LocalModelSetupActionScopeTest {
    private val dispatcher = StandardTestDispatcher(TestCoroutineScheduler())
    private val models = ViewModelStore()

    private fun model(
        check: suspend () -> Boolean = { false },
        install: suspend (() -> InputStream) -> Unit = {},
        canStart: () -> Boolean = { true },
    ) = LocalModelSetupViewModel(check, install, dispatcher, canStart).also {
        models.put("model-setup-action-scope", it)
    }

    @Before fun setup() { Dispatchers.setMain(dispatcher) }

    @After fun cleanup() {
        models.clear()
        Dispatchers.resetMain()
    }

    @Test fun stalePickerAndRecheckCannotUseIdenticalLookingMissingState() = runTest(dispatcher) {
        var checks = 0
        var installs = 0
        val model = model(check = { checks++; false }, install = { installs++ })
        model.onForeground()
        advanceUntilIdle()
        val first = model.state.value
        assertEquals(LocalModelSetupPhase.MISSING, first.phase)

        assertTrue(model.recheck(first))
        advanceUntilIdle()
        val current = model.state.value
        assertEquals(first.phase, current.phase)
        assertEquals(first.notice, current.notice)
        assertNotSame(first, current)

        assertFalse(model.beginPicker(first))
        assertFalse(model.recheck(first))
        advanceUntilIdle()
        assertSame(current, model.state.value)
        assertEquals(2, checks)
        assertEquals(0, installs)

        assertTrue(model.beginPicker(current))
        assertEquals(LocalModelSetupPhase.PICKING, model.state.value.phase)
        assertFalse(model.beginPicker(current))
        model.completePicker(null)
        assertEquals(LocalModelSetupPhase.UNCHECKED, model.state.value.phase)
        assertEquals(0, installs)
    }

    @Test fun staleStartCannotUseIdenticalLookingReadyStateAfterForegroundReturn() = runTest(dispatcher) {
        var checks = 0
        val model = model(check = { checks++; true })
        model.onForeground()
        advanceUntilIdle()
        val first = model.state.value
        assertEquals(LocalModelSetupPhase.READY, first.phase)

        model.onBackground()
        assertFalse(model.beginPlay(first))
        model.onForeground()
        advanceUntilIdle()
        val current = model.state.value
        assertEquals(first.phase, current.phase)
        assertEquals(first.notice, current.notice)
        assertNotSame(first, current)
        assertFalse(model.beginPlay(first))
        assertSame(current, model.state.value)
        assertEquals(2, checks)

        assertTrue(model.beginPlay(current))
        assertEquals(LocalModelSetupPhase.OPENING, model.state.value.phase)
        assertFalse(model.beginPlay(current))
    }

    @Test fun staleCancelCannotStopReplacementImportAndCurrentCancelWaitsForDrain() = runTest(dispatcher) {
        val release = CompletableDeferred<Unit>()
        var imports = 0
        var opens = 0
        val model = model(install = { open ->
            imports++
            open().close()
            if (imports == 1) throw IllegalStateException("Fixture import failure")
            withContext(NonCancellable) { release.await() }
        })
        val open = { opens++; ByteArrayInputStream(byteArrayOf(1)) }
        try {
            model.onForeground()
            val check = model.state.value
            advanceUntilIdle()
            assertTrue(model.beginPicker(model.state.value))
            model.completePicker(open)
            val first = model.state.value
            assertEquals(LocalModelSetupPhase.IMPORTING, first.phase)
            advanceUntilIdle()
            assertEquals(LocalModelSetupPhase.FAILED, model.state.value.phase)

            assertTrue(model.beginPicker(model.state.value))
            model.completePicker(open)
            runCurrent()
            val current = model.state.value
            assertEquals(first.phase, current.phase)
            assertEquals(first.notice, current.notice)
            assertNotSame(first, current)
            assertEquals(2, opens)

            model.cancel(check)
            model.cancel(first)
            runCurrent()
            assertSame(current, model.state.value)

            model.cancel(current)
            runCurrent()
            val stopping = model.state.value
            assertEquals(LocalModelSetupPhase.STOPPING, stopping.phase)
            model.cancel(stopping)
            model.cancel(current)
            assertFalse(model.recheck(stopping))
            assertSame(stopping, model.state.value)

            release.complete(Unit)
            advanceUntilIdle()
            assertEquals(LocalModelSetupPhase.UNCHECKED, model.state.value.phase)
            assertEquals(2, imports)
            assertTrue(model.recheck(model.state.value))
            advanceUntilIdle()
            assertEquals(LocalModelSetupPhase.MISSING, model.state.value.phase)
        } finally {
            release.complete(Unit)
        }
    }

    @Test fun exactFrameStillRejectsARecheckWhileTheRuntimeIsHeld() = runTest(dispatcher) {
        var allowed = false
        var checks = 0
        val model = model(check = { checks++; true }, canStart = { allowed })
        model.onForeground()
        val held = model.state.value
        assertEquals(LocalModelSetupPhase.SESSION_HELD, held.phase)

        allowed = true
        assertFalse(model.recheck(held))
        assertFalse(model.beginPicker(held))
        assertFalse(model.beginPlay(held))
        model.cancel(held)
        advanceUntilIdle()
        assertSame(held, model.state.value)
        assertEquals(0, checks)

        model.onForeground()
        advanceUntilIdle()
        assertEquals(LocalModelSetupPhase.READY, model.state.value.phase)
        assertEquals(1, checks)
    }

    @Test fun disposedControllerRejectsCancelEvenWithItsExactBusyFrame() = runTest(dispatcher) {
        var checks = 0
        val model = model(check = { checks++; false })
        model.onForeground()
        val checking = model.state.value
        assertEquals(LocalModelSetupPhase.CHECKING, checking.phase)
        model.dispose()
        model.cancel(checking)
        advanceUntilIdle()
        assertSame(checking, model.state.value)
        assertEquals(0, checks)
    }
}
