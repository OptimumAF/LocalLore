/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import org.junit.Assert.*
import org.junit.Test

class CandidateOwnerAdmissionTest {
    @Test fun failedConstructionStillRefusesAnotherRuntime() {
        val guard = CandidateOwnerAdmission()
        val allocations = AtomicInteger()
        try { guard.attach<Unit> { allocations.incrementAndGet(); error("synthetic constructor failure") }; fail() }
        catch (expected: WorkspaceConstructionUnavailable) {
            assertEquals("Workspace unavailable", expected.message)
            assertNull(expected.cause)
        }
        assertFalse(guard.available)
        try { guard.attach { allocations.incrementAndGet() }; fail() }
        catch (expected: WorkspaceConstructionUnavailable) { assertEquals("Workspace unavailable", expected.message) }
        assertEquals(1, allocations.get())
    }

    @Test fun simultaneousConstructionCannotCreateTwoOwners() {
        val guard = CandidateOwnerAdmission()
        val entered = CountDownLatch(1)
        val finish = CountDownLatch(1)
        val completed = CountDownLatch(1)
        val allocations = AtomicInteger()
        val thread = Thread {
            try { guard.attach { allocations.incrementAndGet(); entered.countDown(); check(finish.await(2, TimeUnit.SECONDS)) } }
            finally { completed.countDown() }
        }
        thread.start()
        try {
            assertTrue(entered.await(2, TimeUnit.SECONDS))
            try { guard.attach { allocations.incrementAndGet() }; fail() }
            catch (_: WorkspaceConstructionUnavailable) { }
            assertFalse(guard.available)
        } finally { finish.countDown(); assertTrue(completed.await(2, TimeUnit.SECONDS)); thread.join(2_000) }
        assertFalse(thread.isAlive)
        assertEquals(1, allocations.get())
        assertFalse(guard.available)
    }

    @Test fun fixedProfilePreservesArtifactAndRuntimeProvenance() {
        val files = LocalModelFiles(File("test-root"), File("test-root/model.litertlm"), File("test-root/cache"))
        val config = CandidateLocalModel.config(files)
        assertEquals(2_588_147_712L, config.expectedModelBytes)
        assertEquals("181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c", config.modelSha256)
        assertEquals(config.modelSha256, config.templateSha256)
        val profile = localText(config.profileBytes(), 4096)
        assertTrue(profile.contains("\"runtime_revision\":\"bda624851d74be34d4e1f7fac1fc4155939539c7\""))
        assertTrue(profile.contains("\"context_tokens\":4096"))
        assertEquals(files.model, config.model)
        assertEquals(files.cache, config.cache)
    }
}
