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
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class LocalModelSetupViewModelTest {
    private val scheduler = TestCoroutineScheduler()
    private val dispatcher = StandardTestDispatcher(scheduler)
    private val models = ViewModelStore()
    private var count = 0
    private fun model(check: suspend () -> Boolean = { false },
        install: suspend (() -> InputStream) -> Unit = {},
        canStart: () -> Boolean = { true }): LocalModelSetupViewModel =
        LocalModelSetupViewModel(check, install, dispatcher, canStart).also { models.put("setup-${count++}", it) }
    private fun stream(): InputStream = ByteArrayInputStream(byteArrayOf(6, 3, 1))
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { models.clear(); Dispatchers.resetMain() }

    @Test fun noFileOrStoryWorkStartsBeforeForeground() = runTest(dispatcher) {
        var calls = 0
        val model = model(check = { calls++; true }, install = { calls++ })
        assertFalse(model.beginPlay())
        assertFalse(model.beginPicker())
        assertFalse(model.recheck())
        advanceUntilIdle()
        assertEquals(0, calls)
        assertFalse(model.state.value.ready)
    }

    @Test fun foregroundVerifiesBeforePlayAndDuplicateLaunchIsFenced() = runTest(dispatcher) {
        val result = CompletableDeferred<Boolean>()
        var checks = 0
        val model = model(check = { checks++; result.await() })
        model.onForeground()
        runCurrent()
        assertEquals(LocalModelSetupPhase.CHECKING, model.state.value.phase)
        assertFalse(model.beginPlay())
        assertFalse(model.recheck())
        result.complete(true)
        advanceUntilIdle()
        assertEquals(1, checks)
        assertTrue(model.beginPlay())
        assertFalse(model.beginPlay())
        assertFalse(model.beginPicker())
        assertFalse(model.recheck())
    }

    @Test fun restartChecksActualArtifactRatherThanRememberingReady() = runTest(dispatcher) {
        var present = true
        var checks = 0
        val model = model(check = { checks++; present })
        model.onForeground(); advanceUntilIdle()
        assertTrue(model.state.value.ready)
        model.onBackground()
        assertFalse(model.state.value.ready)
        present = false
        model.onForeground(); advanceUntilIdle()
        assertEquals(2, checks)
        assertEquals(LocalModelSetupPhase.MISSING, model.state.value.phase)
        assertFalse(model.beginPlay())
    }

    @Test fun explicitPickerIsRequiredAndConsumedExactlyOnce() = runTest(dispatcher) {
        var opens = 0
        var installs = 0
        val model = model(install = { open -> installs++; open().use { assertEquals(6, it.read()) } })
        val open = { opens++; stream() }
        model.completePicker(open)
        model.onForeground(); advanceUntilIdle()
        assertEquals(0, opens)
        assertTrue(model.beginPicker())
        assertFalse(model.beginPicker())
        model.completePicker(open)
        model.completePicker(open)
        assertFalse(model.beginPlay())
        advanceUntilIdle()
        assertEquals(1, opens)
        assertEquals(1, installs)
        assertTrue(model.state.value.ready)
        model.completePicker(open)
        assertEquals(1, opens)
    }

    @Test fun pickerSurvivesProviderForegroundButNullSelectionDoesNotOpenStream() = runTest(dispatcher) {
        var installs = 0
        val model = model(install = { installs++ })
        model.onForeground(); advanceUntilIdle()
        assertTrue(model.beginPicker())
        model.onBackground(); model.onForeground()
        assertEquals(LocalModelSetupPhase.PICKING, model.state.value.phase)
        model.completePicker(null)
        advanceUntilIdle()
        assertEquals(0, installs)
        assertFalse(model.state.value.ready)
        assertTrue(model.beginPicker())
    }

    @Test fun pickerFailureDoesNotExposeProviderDataAndAllowsAnotherSelection() = runTest(dispatcher) {
        val model = model()
        model.onForeground(); advanceUntilIdle()
        assertTrue(model.beginPicker())
        model.pickerFailed()
        assertEquals(LocalModelSetupPhase.FAILED, model.state.value.phase)
        assertTrue(model.beginPicker())
    }

    @Test fun providerAndCheckFailuresHaveFixedMessages() = runTest(dispatcher) {
        val privateFailure = "content://private-provider/story secret-path"
        val model = model(check = { throw IllegalStateException(privateFailure) },
            install = { open -> open().use { it.read() } })
        model.onForeground(); advanceUntilIdle()
        val first = model.state.value.notice
        assertEquals(LocalModelSetupPhase.FAILED, model.state.value.phase)
        assertFalse(first.contains(privateFailure))
        assertTrue(model.beginPicker())
        model.completePicker { throw SecurityException(privateFailure) }
        advanceUntilIdle()
        assertEquals(first, model.state.value.notice)
        assertFalse(model.beginPlay())
    }

    @Test fun cancellationHoldsSlotUntilNoncooperativeImportReallyReturns() = runTest(dispatcher) {
        val release = CompletableDeferred<Unit>()
        var installs = 0
        var published = false
        val model = model(check = { published }, install = {
            installs++
            withContext(NonCancellable) { release.await(); published = true }
        })
        model.onForeground(); advanceUntilIdle()
        assertTrue(model.beginPicker()); model.completePicker(::stream); runCurrent()
        model.cancel(); runCurrent()
        assertEquals(LocalModelSetupPhase.STOPPING, model.state.value.phase)
        assertFalse(model.recheck())
        assertFalse(model.beginPicker())
        assertFalse(model.beginPlay())
        assertEquals(1, installs)
        release.complete(Unit); advanceUntilIdle()
        assertTrue(published)
        assertEquals(LocalModelSetupPhase.UNCHECKED, model.state.value.phase)
        assertFalse(model.state.value.ready)
        assertTrue(model.state.value.notice.contains("may already have been saved"))
        assertTrue(model.recheck()); advanceUntilIdle()
        assertTrue(model.state.value.ready)
    }

    @Test fun cancellationBeforeDispatchedBodyStartsDoesNotLeakReservation() = runTest(dispatcher) {
        var checks = 0
        val model = model(check = { checks++; false })
        model.onForeground()
        model.cancel()
        advanceUntilIdle()
        assertEquals(0, checks)
        assertFalse(model.state.value.busy)
        assertTrue(model.recheck())
        advanceUntilIdle()
        assertEquals(1, checks)
    }

    @Test fun backgroundCancellationCannotPublishOldVerificationAsReady() = runTest(dispatcher) {
        val release = CompletableDeferred<Unit>()
        var checks = 0
        val model = model(check = {
            checks++
            if (checks == 1) withContext(NonCancellable) { release.await(); true } else false
        })
        model.onForeground(); runCurrent()
        model.onBackground(); model.onForeground(); runCurrent()
        assertTrue(model.state.value.busy)
        assertFalse(model.beginPlay())
        release.complete(Unit); advanceUntilIdle()
        assertEquals(2, checks)
        assertEquals(LocalModelSetupPhase.MISSING, model.state.value.phase)
    }

    @Test fun disposalFencesLateImportAndAllFurtherActions() = runTest(dispatcher) {
        val release = CompletableDeferred<Unit>()
        var returned = false
        val model = model(install = { withContext(NonCancellable) { release.await(); returned = true } })
        model.onForeground(); advanceUntilIdle()
        assertTrue(model.beginPicker()); model.completePicker(::stream); runCurrent()
        model.dispose()
        val stopped = model.state.value
        release.complete(Unit); advanceUntilIdle()
        assertTrue(returned)
        assertEquals(stopped, model.state.value)
        model.onForeground(); model.completePicker(::stream); model.pickerFailed()
        assertFalse(model.recheck()); assertFalse(model.beginPicker()); assertFalse(model.beginPlay())
        assertEquals(stopped, model.state.value)
    }

    @Test fun restoredControllerIgnoresOldPickerDelivery() = runTest(dispatcher) {
        var opened = 0
        val model = model(install = { it().close() })
        model.completePicker { opened++; stream() }
        model.onForeground(); advanceUntilIdle()
        assertEquals(0, opened)
        assertEquals(LocalModelSetupPhase.MISSING, model.state.value.phase)
    }

    @Test fun heldRuntimePreventsVerificationImportAndAnotherSession() = runTest(dispatcher) {
        var calls = 0
        val model = model(check = { calls++; true }, install = { calls++ }, canStart = { false })
        model.onForeground(); advanceUntilIdle()
        assertEquals(LocalModelSetupPhase.SESSION_HELD, model.state.value.phase)
        assertFalse(model.recheck()); assertFalse(model.beginPicker()); assertFalse(model.beginPlay())
        model.completePicker { calls++; stream() }
        assertEquals(0, calls)
        assertEquals("Close the app completely before starting another local session.", model.state.value.notice)
    }

    @Test fun runtimeAdmissionIsRecheckedWhenStartIsTapped() = runTest(dispatcher) {
        var allowed = true
        val model = model(check = { true }, canStart = { allowed })
        model.onForeground(); advanceUntilIdle()
        assertTrue(model.state.value.ready)
        allowed = false
        assertFalse(model.beginPlay())
        assertEquals(LocalModelSetupPhase.SESSION_HELD, model.state.value.phase)
    }

    @Test fun runtimeClaimDuringPickerPreventsSelectedStreamOpening() = runTest(dispatcher) {
        var allowed = true
        var opens = 0
        val model = model(install = { it().close() }, canStart = { allowed })
        model.onForeground(); advanceUntilIdle(); assertTrue(model.beginPicker())
        allowed = false
        model.completePicker { opens++; stream() }
        advanceUntilIdle()
        assertEquals(0, opens)
        assertEquals(LocalModelSetupPhase.SESSION_HELD, model.state.value.phase)
    }

    @Test fun failedScreenLaunchRequiresFreshVerification() = runTest(dispatcher) {
        var checks = 0
        val model = model(check = { checks++; true })
        model.onForeground(); advanceUntilIdle()
        assertTrue(model.beginPlay())
        model.playLaunchFailed()
        assertFalse(model.beginPlay())
        assertTrue(model.recheck()); advanceUntilIdle()
        assertEquals(2, checks)
        assertTrue(model.beginPlay())
    }
}
