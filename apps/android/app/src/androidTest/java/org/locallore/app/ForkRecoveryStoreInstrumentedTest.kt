/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.util.UUID
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual Android AtomicFile on unique synthetic roots; no power-loss or external-writer claim. */
@RunWith(AndroidJUnit4::class)
class ForkRecoveryStoreInstrumentedTest {
    private fun context(): Context {
        val app = ApplicationProvider.getApplicationContext<Context>()
        val root = File(app.noBackupFilesDir, "fork-hint-fixture-${UUID.randomUUID()}").also { check(it.mkdir()) }
        return object : ContextWrapper(app) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
    }
    private val saved = BranchForkRecovery(1, BranchForkInput(ForkScope("synthetic", "main"), "fixed-child", 4, 2))
    private fun rejected(work: () -> Unit) {
        try { work(); fail("Expected unavailable recovery hint") } catch (_: ForkRecoveryFailure) { }
    }
    @Test fun exactHintSurvivesReopenAndAStaleInstanceCannotOverwriteOrClearIt() {
        val app = context(); val first = AtomicForkRecoveryStore(app); val stale = AtomicForkRecoveryStore(app)
        assertNull(first.load()); assertNull(stale.load())
        first.save(saved)
        assertEquals(saved, AtomicForkRecoveryStore(app).load())
        rejected { stale.save(saved.copy(input = saved.input.copy(childBranch = "different-child"))) }
        rejected { stale.save(null) }
        first.save(saved) // Explicit retry retains exactly the same identity.
        rejected { first.save(saved.copy(input = saved.input.copy(atRevision = 1))) }
        assertEquals(saved, AtomicForkRecoveryStore(app).load())
        first.save(null)
        assertNull(AtomicForkRecoveryStore(app).load())
    }
    @Test fun malformedFutureDuplicateAndOversizedHintsRequireExplicitClearWithoutAdoption() {
        val app = context()
        val root = File(app.noBackupFilesDir, "fork-recovery-v1").also { check(it.mkdir()) }
        val pending = File(root, "pending.json")
        val canary = File(app.noBackupFilesDir, "unrelated.txt").also { it.writeText("unchanged synthetic canary") }
        val valid = ForkNativeWire.recovery(saved).toString(Charsets.UTF_8)
        val cases = listOf(
            valid.replace("\"version\":1", "\"version\":2").toByteArray(),
            valid.replaceFirst("{", "{\"version\":1,").toByteArray(),
            byteArrayOf(0xc3.toByte(), 0x28),
            ByteArray(4097) { 'x'.code.toByte() },
        )
        for (bytes in cases) {
            pending.writeBytes(bytes)
            val store = AtomicForkRecoveryStore(app)
            rejected { store.load() }
            rejected { store.save(saved) }
            assertArrayEquals(bytes, pending.readBytes())
            store.save(null) // Separate caller consent; never automatic on parse failure.
            assertNull(AtomicForkRecoveryStore(app).load())
            assertEquals("unchanged synthetic canary", canary.readText())
        }
    }
    @Test fun orphanNewFileIsNotSilentlyTreatedAsNoRecoveryIdentity() {
        val app = context()
        val root = File(app.noBackupFilesDir, "fork-recovery-v1").also { check(it.mkdir()) }
        val orphan = File(root, "pending.json.new").also { it.writeText("incomplete") }
        val store = AtomicForkRecoveryStore(app)
        rejected { store.load() }
        assertEquals("incomplete", orphan.readText())
        rejected { store.save(saved) }
        store.save(null)
        assertFalse(orphan.exists())
        assertNull(AtomicForkRecoveryStore(app).load())
    }
    @Test fun unavailableFixedDirectoryNeverAdoptsOrReplacesTheBlockingFile() {
        val app = context()
        val blocker = File(app.noBackupFilesDir, "fork-recovery-v1").also { it.writeText("keep original bytes") }
        val store = AtomicForkRecoveryStore(app)
        assertNull(store.load())
        rejected { store.save(saved) }
        assertEquals("keep original bytes", blocker.readText())
        assertTrue(blocker.isFile)
    }
}
