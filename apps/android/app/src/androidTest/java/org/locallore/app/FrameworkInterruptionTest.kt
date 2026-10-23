/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Activity
import android.app.Application
import android.content.Context
import android.content.ContextWrapper
import android.os.Bundle
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.RuleChain
import org.junit.rules.TestRule
import org.junit.runner.Description
import org.junit.runner.RunWith
import org.junit.runners.model.MultipleFailureException
import org.junit.runners.model.Statement
import java.io.File
import java.util.UUID
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference

/** Actual framework callbacks and Rust/SQLite; only reply delivery is gated, in this test APK. */
@SdkSuppress(minSdkVersion = 29)
@RunWith(AndroidJUnit4::class)
class FrameworkInterruptionTest {
    private data class Turn(val command: JSONObject)
    private class DeliveryGate(val actual: NativeWorkspaceTransport) : WorkspaceTransport {
        val entered = CompletableDeferred<Turn>()
        val nativeReply = CompletableDeferred<JSONObject>()
        val release = CompletableDeferred<Unit>()
        val returned = CompletableDeferred<Unit>()
        val inNative = AtomicBoolean(false)
        val activeAtFirstStop = AtomicReference<Boolean?>(null)
        val calls = CopyOnWriteArrayList<Pair<String, String?>>()
        private val firstPrepare = AtomicBoolean(true)
        override suspend fun exchange(command: JSONObject): JSONObject {
            val op = command.getString("op")
            val key = if (op == "submit") command.getJSONObject("request").getString("turn")
                else command.optString("turn").takeUnless { it.isEmpty() }
            calls += op to key
            if (op != "prepare" || !firstPrepare.compareAndSet(true, false)) return actual.exchange(command)
            var captured: JSONObject? = null
            try {
                // Capture completion on IO even if Main's caller is cancelled. Otherwise a
                // cancelled withContext return could falsely leave the in-native flag set.
                return withContext(NonCancellable + Dispatchers.IO) {
                    inNative.set(true)
                    entered.complete(Turn(JSONObject(command.toString())))
                    try {
                        val reply = actual.exchange(command)
                        captured = reply
                        inNative.set(false)
                        nativeReply.complete(reply)
                        release.await()
                        reply
                    } catch (failure: Throwable) {
                        nativeReply.completeExceptionally(failure)
                        throw failure
                    } finally { inNative.set(false) }
                }
            } catch (cancelled: CancellationException) {
                // Deliberately deliver an obsolete reply to the cancelled controller. Its
                // generation/scope fence, rather than cancellation alone, must reject it.
                if (release.isCompleted && captured != null) return checkNotNull(captured)
                throw cancelled
            } finally { returned.complete(Unit) }
        }
        override fun close() = actual.close()
    }
    private data class Owner(val context: Context, val gate: DeliveryGate, val model: ShellViewModel) {
        val database: File get() = File(context.noBackupFilesDir, "workspace-v1/stories.sqlite3")
    }
    private class Fixture : TestRule, Application.ActivityLifecycleCallbacks {
        val owners = CopyOnWriteArrayList<Owner>()
        val seen = CopyOnWriteArrayList<ShellViewModel>()
        private val application = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext as Application
        override fun onActivityPreCreated(activity: Activity, savedInstanceState: Bundle?) {
            if (activity !is MainActivity) return
            val factory = object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    check(modelClass == ShellViewModel::class.java)
                    val parent = application.noBackupFilesDir.canonicalFile
                    val root = File(parent, "synthetic-framework-${UUID.randomUUID()}")
                    check(root.mkdir()); check(root.canonicalFile.parentFile == parent)
                    val context = object : ContextWrapper(application) {
                        override fun getApplicationContext(): Context = this
                        override fun getNoBackupFilesDir(): File = root
                    }
                    val gate = DeliveryGate(NativeWorkspaceTransport(context))
                    val model = ShellViewModel(DurableGateway(gate))
                    owners += Owner(context, gate, model)
                    return model as T
                }
            }
            // The production Activity then obtains exactly this ordinary store entry.
            // A recreated Activity must find the retained model without another owner.
            seen += ViewModelProvider(activity, factory)[ShellViewModel::class.java]
        }
        override fun onActivityPreStopped(activity: Activity) {
            if (activity is MainActivity) owners.forEach {
                if (it.gate.entered.isCompleted) it.gate.activeAtFirstStop.compareAndSet(null, it.gate.inNative.get())
            }
        }
        override fun onActivityCreated(activity: Activity, state: Bundle?) = Unit
        override fun onActivityStarted(activity: Activity) = Unit
        override fun onActivityResumed(activity: Activity) = Unit
        override fun onActivityPaused(activity: Activity) = Unit
        override fun onActivityStopped(activity: Activity) = Unit
        override fun onActivitySaveInstanceState(activity: Activity, state: Bundle) = Unit
        override fun onActivityDestroyed(activity: Activity) = Unit
        override fun apply(base: Statement, description: Description) = object : Statement() {
            override fun evaluate() {
                val failures = mutableListOf<Throwable>()
                application.registerActivityLifecycleCallbacks(this@Fixture)
                try { base.evaluate() } catch (failure: Throwable) { failures += failure }
                finally {
                    application.unregisterActivityLifecycleCallbacks(this@Fixture)
                    owners.forEach { it.gate.release.complete(Unit); it.gate.close() }
                    try {
                        runBlocking {
                            owners.forEach {
                                if (it.gate.entered.isCompleted) withTimeout(5_000) { it.gate.returned.await() }
                                allSlotsReleased(it.database)
                                // The exact create-new root only, after native owners have drained.
                                check(it.context.noBackupFilesDir.deleteRecursively())
                            }
                        }
                    } catch (failure: Throwable) { failures += failure }
                }
                MultipleFailureException.assertEmpty(failures)
            }
        }
    }
    private val fixture = Fixture()
    private val compose = createAndroidComposeRule<MainActivity>()
    @get:Rule val rules: TestRule = RuleChain.outerRule(fixture).around(compose)
    private val owner: Owner get() = fixture.owners.single()
    private fun main(action: () -> Unit) = InstrumentationRegistry.getInstrumentation().runOnMainSync(action)
    private fun idle() {
        runBlocking { withTimeout(10_000) { while (owner.model.state.value.busy) delay(5) } }
        assertFalse(owner.model.state.value.recoveryRequired)
        assertTrue(owner.model.state.value.persistent)
    }
    private fun zero() {
        val state = owner.model.state.value
        assertEquals(0L, state.revision)
        assertTrue(state.messages.isEmpty())
        assertEquals("You", state.potionOwner)
    }
    private fun accepted() {
        val state = owner.model.state.value
        assertEquals(1L, state.revision)
        assertEquals(2, state.messages.size)
        assertEquals("Not in your inventory", state.potionOwner)
        assertEquals("You give 1 potion to mira.", state.messages.single { !it.isPlayer }.text)
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag("revision"))
        compose.onNodeWithTag("revision").assertTextEquals("Accepted revision · 1")
    }
    private fun beginActualRunningTurn(): Turn {
        idle(); zero()
        assertSame(owner.model, ViewModelProvider(compose.activity)[ShellViewModel::class.java])
        main { owner.model.setMode(DemoMode.DELAYED); owner.model.submit(DemoAction.GIVE_POTION) }
        return runBlocking {
            val turn = withTimeout(3_000) { owner.gate.entered.await() }
            val query = JSONObject(turn.command.toString()).put("op", "turn_status")
            withTimeout(3_000) {
                while (true) {
                    val reply = owner.gate.actual.exchange(query)
                    assertEquals("ok", reply.getString("status"))
                    val phase = reply.getJSONObject("data").getString("phase")
                    if (phase == "running") break
                    assertEquals("Actual active-work overlap was not observed", "queued", phase)
                    delay(1)
                }
            }
            turn
        }
    }
    private fun stoppedBeforeNativeReturn() {
        assertEquals("Insufficient native/framework-stop overlap; do not infer a cancellation pass",
            true, owner.gate.activeAtFirstStop.get())
        runBlocking {
            val reply = withTimeout(3_000) { owner.gate.nativeReply.await() }
            assertEquals("ok", reply.getString("status"))
            assertEquals("cancelled", reply.getJSONObject("data").getString("phase"))
        }
        idle(); zero()
        assertEquals(0, owner.gate.calls.count { it.first == "commit" })
    }
    private fun releaseLateReply() = runBlocking {
        owner.gate.release.complete(Unit)
        withTimeout(3_000) { owner.gate.returned.await() }
        withContext(Dispatchers.Main) { /* Barrier after obsolete continuation delivery. */ }
    }
    private fun reopen(expected: ShellState, original: SavedStory? = null) = runBlocking {
        val gateway = DurableGateway(NativeWorkspaceTransport(owner.context))
        try {
            val library = gateway.initialize()
            if (original != null) {
                val first = gateway.resumeSaved(library.stories.single { it.story == original.story && it.branch == original.branch })
                assertEquals(0L, first.revision); assertTrue(first.messages.isEmpty())
            }
            val selected = checkNotNull(expected.selectedStory)
            val restored = gateway.resumeSaved(gateway.snapshot().stories.single { it.story == selected.story && it.branch == selected.branch })
            assertEquals(expected.revision, restored.revision)
            assertEquals(expected.messages, restored.messages)
            assertEquals(expected.potionOwner, restored.potionOwner)
        } finally { gateway.close() }
    }

    @Test fun realFrameworkStopCancelsRunningTurnAndLateReplyCannotAttachToNewStory() {
        val old = beginActualRunningTurn()
        val original = checkNotNull(owner.model.state.value.selectedStory)
        compose.activityRule.scenario.moveToState(Lifecycle.State.CREATED)
        assertEquals(Lifecycle.State.CREATED, compose.activityRule.scenario.state)
        stoppedBeforeNativeReturn()
        compose.activityRule.scenario.moveToState(Lifecycle.State.RESUMED)
        main { owner.model.reset() }; idle(); zero()
        assertNotEquals(original.story, owner.model.state.value.selectedStory!!.story)
        main { owner.model.setMode(DemoMode.ACCEPTED); owner.model.submit(DemoAction.GIVE_POTION) }
        idle(); accepted()
        val before = owner.model.state.value
        releaseLateReply(); idle(); accepted()
        assertEquals(before, owner.model.state.value)
        assertEquals(1, owner.gate.calls.count { it.first == "commit" })
        assertFalse(owner.gate.calls.any { it.first == "commit" && it.second == old.command.getString("turn") })
        reopen(before, original)
    }

    @Test fun realFrameworkRecreationCancelsRunningTurnAndRetainsOnlyTheCurrentAcceptedReceipt() {
        val old = beginActualRunningTurn()
        val retained = owner.model
        compose.activityRule.scenario.recreate()
        assertEquals(Lifecycle.State.RESUMED, compose.activityRule.scenario.state)
        assertEquals(1, fixture.owners.size)
        assertTrue(fixture.seen.size >= 2)
        assertTrue(fixture.seen.all { it === retained })
        stoppedBeforeNativeReturn()
        main { retained.setMode(DemoMode.ACCEPTED); retained.submit(DemoAction.GIVE_POTION) }
        idle(); accepted()
        val before = retained.state.value
        releaseLateReply(); idle(); accepted()
        assertEquals(before, retained.state.value)
        assertFalse(owner.gate.calls.any { it.first == "commit" && it.second == old.command.getString("turn") })
        reopen(before)
    }

    @Test fun realFrameworkDestructionFencesLateReplyAndRetainedCallbacksWithoutDeletingSavedCanon() {
        beginActualRunningTurn()
        compose.activityRule.scenario.close()
        assertEquals(Lifecycle.State.DESTROYED, compose.activityRule.scenario.state)
        assertEquals(true, owner.gate.activeAtFirstStop.get())
        releaseLateReply()
        val disposed = owner.model.state.value
        val calls = owner.gate.calls.toList()
        main { owner.model.reset(); owner.model.submit(DemoAction.GIVE_POTION); owner.model.recover() }
        assertEquals(disposed, owner.model.state.value)
        assertEquals(calls, owner.gate.calls.toList())
        assertEquals(0, calls.count { it.first == "commit" })
        runBlocking { allSlotsReleased(owner.database) }
        reopen(disposed)
        assertTrue(owner.database.isFile)
        zero()
    }
    companion object {
        private suspend fun allSlotsReleased(path: File) = withContext(Dispatchers.IO) {
            withTimeout(5_000) {
                while (true) {
                    val handles = mutableListOf<Long>()
                    try {
                        repeat(4) { NativeWorkspace.open(path.absolutePath).let { if (it != 0L) handles += it } }
                        if (handles.size == 4) break
                    } finally { handles.forEach { NativeWorkspace.close(it) } }
                    delay(5)
                }
            }
        }
    }
}
