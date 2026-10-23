/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.SystemClock
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Exercises the production gateway, including its IO coroutine and actual JNI registry. */
@RunWith(AndroidJUnit4::class)
class NativeLifecycleOwnershipTest {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val fields = listOf("live_sessions", "retained_sessions", "operations", "workers")
    private fun counts(): List<Int> = NativeBridge.exchange(0, NativeBridge.control("stats")).let { reply ->
        fields.map { reply.getInt(it) }
    }
    private fun await(description: String, predicate: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 3_000
        while (!predicate()) {
            check(SystemClock.elapsedRealtime() < deadline) { description }
            SystemClock.sleep(5)
        }
    }
    private fun main(action: () -> Unit) = instrumentation.runOnMainSync(action)

    @Test fun retainedResetAfterDisposalCannotAllocateAnUnownedNativeSession() {
        val baseline = counts()
        val store = ViewModelStore()
        lateinit var gateway: NativeDemoGateway
        lateinit var model: ShellViewModel
        main {
            gateway = NativeDemoGateway()
            model = ShellViewModel(gateway)
            store.put("native-owner", model)
            model.setMode(DemoMode.DELAYED)
            model.submit(DemoAction.GIVE_POTION)
        }
        try {
            await("Native worker did not start") { counts()[3] > baseline[3] }
            main { store.clear() }
            await("Disposal retained native resources") { counts() == baseline }
            val disposed = model.state.value
            // Models/callbacks can outlive the view. Disposal must remain terminal.
            main { repeat(3) { model.reset() } }
            assertEquals("Retained reset callback allocated native resources", baseline, counts())
            assertEquals(disposed, model.state.value)
        } finally {
            // Also clean up if the regression reopens a session after the store was cleared.
            main { store.clear(); gateway.close() }
            await("Test cleanup retained resources") { counts() == baseline }
        }
    }

    @Test fun replacingRunningSessionsCannotCancelFreshWorkOrLeakOldOwners() {
        val baseline = counts()
        val store = ViewModelStore()
        lateinit var model: ShellViewModel
        main {
            model = ShellViewModel(NativeDemoGateway())
            store.put("native-owner", model)
        }
        try {
            repeat(12) {
                main {
                    model.setMode(DemoMode.DELAYED)
                    model.submit(DemoAction.GIVE_POTION)
                }
                await("Native delayed worker did not start") { counts()[3] > baseline[3] }
                // Reset invalidates the captured session while the old IO worker is unwinding.
                main {
                    model.reset()
                    model.submit(DemoAction.GIVE_POTION)
                }
                await("Fresh accepted turn was lost after reset") { !model.state.value.busy }
                assertEquals(1L, model.state.value.revision)
                assertEquals("Mira", model.state.value.potionOwner)
                assertEquals(2, model.state.value.messages.size)
                await("Obsolete worker/session retained") {
                    counts() == listOf(baseline[0] + 1, baseline[1] + 1, baseline[2] + 1, baseline[3])
                }
                main { model.reset() }
                assertEquals(0L, model.state.value.revision)
            }
        } finally {
            main { store.clear() }
            await("Final disposal retained resources") { counts() == baseline }
        }
    }
}
