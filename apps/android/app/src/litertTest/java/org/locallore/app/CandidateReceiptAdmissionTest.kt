/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.File
import java.io.IOException
import java.nio.file.Files
import kotlinx.coroutines.CancellationException
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class CandidateReceiptAdmissionTest {
    @get:Rule val temp = TemporaryFolder()

    @Test fun absentLegacyRootIsNotCreatedAndCapacityIsForwarded() {
        val legacy = File(temp.root, "legacy")
        val observed = mutableListOf<Long>()
        val admission = CandidateReceiptAdmission(legacy, observed::add)
        admission.admit(2588147712L)
        admission.admit()
        assertEquals(listOf(2588147712L, 0L), observed)
        assertFalse(legacy.exists())
        assertTrue(temp.root.listFiles()!!.isEmpty())
    }

    @Test fun existingLegacyContentIsPreservedAndRefusalIsSticky() {
        val legacy = temp.newFolder("legacy")
        val sentinel = File(legacy, "original").apply { writeText("preserve") }
        var volumeCalls = 0
        val admission = CandidateReceiptAdmission(legacy) { volumeCalls++ }
        assertFailure(LocalModelFailure.STORAGE) { admission.admit() }
        assertEquals("preserve", sentinel.readText())
        // Removing our synthetic sentinel cannot rehabilitate an already refused owner.
        assertTrue(sentinel.delete())
        assertTrue(legacy.delete())
        assertFailure(LocalModelFailure.STORAGE) { admission.admit() }
        assertEquals(1, volumeCalls)
    }

    @Test fun danglingLegacyLinkIsAlsoAnExistingForeignRoot() {
        val legacy = File(temp.root, "legacy")
        Files.createSymbolicLink(legacy.toPath(), File(temp.root, "absent").toPath())
        assertFailure(LocalModelFailure.STORAGE) { CandidateReceiptAdmission(legacy) {}.admit() }
        assertTrue(Files.isSymbolicLink(legacy.toPath()))
    }

    @Test fun lowCapacityRetainsTypedErrorAndStopsLaterVolumeCalls() {
        var calls = 0
        val admission = CandidateReceiptAdmission(File(temp.root, "legacy")) {
            calls++
            throw LocalModelException(LocalModelFailure.NO_SPACE)
        }
        assertFailure(LocalModelFailure.NO_SPACE) { admission.admit(63) }
        assertFailure(LocalModelFailure.STORAGE) { admission.admit() }
        assertEquals(1, calls)
        assertTrue(temp.root.listFiles()!!.isEmpty())
    }

    @Test fun arbitraryVolumeErrorsAreRedactedAndCancellationRemainsCancellation() {
        val legacy = File(temp.root, "legacy")
        assertFailure(LocalModelFailure.STORAGE) {
            CandidateReceiptAdmission(legacy) { throw IOException("private path") }.admit()
        }
        val cancelled = CancellationException("cancel")
        val admission = CandidateReceiptAdmission(legacy) { throw cancelled }
        try {
            admission.admit()
            fail("Expected cancellation")
        } catch (actual: CancellationException) { assertSame(cancelled, actual) }
        assertFailure(LocalModelFailure.STORAGE) { admission.admit() }
        assertFalse(legacy.exists())
    }

    private fun assertFailure(expected: LocalModelFailure, action: () -> Unit) {
        try { action(); fail("Expected fixed failure") }
        catch (failure: LocalModelException) { assertEquals(expected, failure.failure) }
    }
}
