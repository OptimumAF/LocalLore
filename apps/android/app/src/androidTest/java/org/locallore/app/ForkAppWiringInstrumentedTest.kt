/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual production adapters/JNI, isolated synthetic noBackup roots. Device execution is separate. */
@RunWith(AndroidJUnit4::class)
class ForkAppWiringInstrumentedTest {
    private fun isolatedContext(): Context {
        val app = ApplicationProvider.getApplicationContext<Context>()
        val directory = File(app.noBackupFilesDir, "fork-app-fixture-${UUID.randomUUID()}").also { check(it.mkdir()) }
        return object : ContextWrapper(app) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = directory
        }
    }
    @Test fun sharedTransportForkAndExplicitResumeLeaveOriginalAcceptedSuffixUntouched() = runBlocking {
        withContext(Dispatchers.IO) {
            val app = isolatedContext()
            val transport = NativeWorkspaceTransport(app)
            val stories = DurableGateway(transport, autoCreateIfEmpty = false)
            val forks = NativeForkGateway(transport::forkHandle)
            try {
                val empty = stories.initialize()
                assertNull(empty.selected)
                val initial = stories.createSaved()
                val original = checkNotNull(initial.selected)
                assertNotNull(stories.forkContext(original, 0, 1))
                val prepared = stories.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
                assertTrue(prepared is DemoResult.Prepared)
                assertNull(stories.forkContext(original, 0, 1))
                assertTrue(stories.commitAsync(prepared) is DemoResult.Accepted)
                val accepted = stories.snapshot()
                val parent = checkNotNull(accepted.selected)
                assertEquals(1L, accepted.revision)
                val context = checkNotNull(stories.forkContext(parent, 1, 2))
                assertNull(stories.forkContext(parent, 0, 2))
                assertNull(stories.forkContext(parent.copy(branch = "foreign"), 1, 2))
                val handle = transport.forkHandle()
                assertEquals(handle, transport.forkHandle())
                val input = BranchForkInput(context.parent, "fixed-app-child", 1, 0)
                val hint = AtomicForkRecoveryStore(app)
                assertNull(hint.load())
                hint.save(BranchForkRecovery(1, input))
                val registered = forks.register(context, input, true)
                val completed = forks.run(registered.operation)
                assertEquals(BranchForkPhase.COMPLETED, completed.phase)
                assertTrue(checkNotNull(completed.outcome).created)
                val unchanged = stories.snapshot()
                assertEquals(parent, unchanged.selected)
                assertEquals(accepted.messages, unchanged.messages)
                assertEquals(accepted.potionOwner, unchanged.potionOwner)
                val child = stories.resumeSaved(parent.copy(branch = input.childBranch, revision = 0))
                assertEquals(0L, child.revision)
                assertTrue(child.messages.isEmpty())
                assertEquals(initial.potionOwner, child.potionOwner)
                assertTrue(stories.commitAsync(stories.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)) is DemoResult.Accepted)
                val restored = stories.resumeSaved(parent)
                assertEquals(accepted.messages, restored.messages)
                assertEquals(accepted.potionOwner, restored.potionOwner)
                assertEquals(1L, restored.revision)
                assertEquals(BranchForkRecovery(1, input), AtomicForkRecoveryStore(app).load())
            } finally { forks.close(); stories.close() }
        }
    }
    @Test fun newOwnerRestoresOnlyIdentityAndLookupCannotCreateAMissingChild() = runBlocking {
        withContext(Dispatchers.IO) {
            val app = isolatedContext()
            val firstTransport = NativeWorkspaceTransport(app)
            val first = DurableGateway(firstTransport, autoCreateIfEmpty = false)
            val input: BranchForkInput
            try {
                first.initialize()
                val selected = checkNotNull(first.createSaved().selected)
                val context = checkNotNull(first.forkContext(selected, 0, 1))
                input = BranchForkInput(context.parent, "missing-fixed-child", 0, 0)
                val hint = AtomicForkRecoveryStore(app)
                assertNull(hint.load()); hint.save(BranchForkRecovery(1, input))
            } finally { first.close() }
            val transport = NativeWorkspaceTransport(app)
            val stories = DurableGateway(transport, autoCreateIfEmpty = false)
            val forks = NativeForkGateway(transport::forkHandle)
            try {
                val reopened = stories.initialize()
                assertEquals(input.parent.branch, checkNotNull(reopened.selected).branch)
                val saved = checkNotNull(AtomicForkRecoveryStore(app).load())
                assertEquals(input, saved.input)
                suspend fun catalog() = transport.exchange(JSONObject().put("op", "branches").put("story", input.parent.story)).toString()
                val before = catalog()
                assertFalse(forks.lookup(saved.input).found)
                assertEquals(before, catalog())
                assertEquals(input.parent.branch, checkNotNull(stories.snapshot().selected).branch)
            } finally { forks.close(); stories.close() }
        }
    }
}
