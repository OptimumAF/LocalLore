/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Original pure policy adversaries; no Android API, filesystem, model or native runtime. */
class PhysicalModelPolicyTest {
    private val gib = PhysicalModelPolicy.GIB
    private fun facts() = PhysicalModelFacts("SM-S918U1", 36, "SM8550", "arm64-v8a", 4096,
        11 * gib, 6 * gib, false, PhysicalModelPolicy.FRESH_BYTES, 10234, 10234, 71, 817)
    private fun refuses(reason: PhysicalModelFailure, action: () -> Unit) {
        try { action(); fail("Expected closed physical profile refusal") }
        catch (failure: PhysicalModelException) {
            assertEquals(reason, failure.failure)
            assertEquals("Physical model unavailable: ${reason.name}", failure.message)
            assertNull(failure.cause)
            assertFalse(failure.toString().contains("PRIVATE_PHONE_CANARY"))
        }
    }

    @Test fun profileAndArtifactIdentityAreFixedWithoutPromisingPhoneQualification() {
        assertEquals("s918u1_api36_arm64_4k_v1", PhysicalModelPolicy.PROFILE)
        assertEquals("org.locallore.app.phoneverify", PhysicalModelPolicy.PACKAGE)
        assertEquals(2_588_147_712L, PhysicalModelPolicy.MODEL_BYTES)
        assertEquals("181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c", PhysicalModelPolicy.MODEL_SHA256)
        assertEquals(facts(), PhysicalModelPolicy.fresh(facts()))
    }

    @Test fun onlyExactModelApiSocPrimaryAbiAndPageSizeAreAdmitted() {
        listOf(facts().copy(model = "SM-S918B"), facts().copy(model = "PRIVATE_PHONE_CANARY"),
            facts().copy(api = 35), facts().copy(api = 37), facts().copy(soc = "kalama"),
            facts().copy(primaryAbi = "x86_64"), facts().copy(primaryAbi = "armeabi-v7a"),
            facts().copy(pageBytes = 16384), facts().copy(pageBytes = 0)).forEach {
            refuses(PhysicalModelFailure.IDENTITY) { PhysicalModelPolicy.admit(it) }
        }
    }

    @Test fun memoryFloorsAndTierBoundsAreInclusive() {
        for (total in listOf(10 * gib, 12 * gib)) {
            PhysicalModelPolicy.admit(facts().copy(totalMemory = total, availableMemory = 4 * gib))
            PhysicalModelPolicy.admit(facts().copy(totalMemory = total, availableMemory = total))
        }
        listOf(facts().copy(totalMemory = 10 * gib - 1), facts().copy(totalMemory = 12 * gib + 1),
            facts().copy(availableMemory = 4 * gib - 1), facts().copy(availableMemory = -1),
            facts().copy(availableMemory = 12 * gib), facts().copy(lowMemory = true)).forEach {
            refuses(PhysicalModelFailure.MEMORY) { PhysicalModelPolicy.admit(it) }
        }
    }

    @Test fun sameFilesystemTwoCopiesUseOneCombinedReserve() {
        assertEquals(2 * gib, PhysicalModelPolicy.RESERVE_BYTES)
        assertEquals(7_323_779_072L, PhysicalModelPolicy.FRESH_BYTES)
        assertEquals(PhysicalModelPolicy.FRESH_BYTES,
            PhysicalModelPolicy.requiredBytes(2 * PhysicalModelPolicy.MODEL_BYTES))
        for (missing in listOf(0L, PhysicalModelPolicy.MODEL_BYTES, 2 * PhysicalModelPolicy.MODEL_BYTES)) {
            val required = PhysicalModelPolicy.requiredBytes(missing)
            assertEquals(2 * gib, required - missing)
            PhysicalModelPolicy.admit(facts().copy(availableBytes = required), missing)
            refuses(PhysicalModelFailure.NO_SPACE) {
                PhysicalModelPolicy.admit(facts().copy(availableBytes = required - 1), missing)
            }
        }
        refuses(PhysicalModelFailure.NO_SPACE) {
            PhysicalModelPolicy.fresh(facts().copy(availableBytes = PhysicalModelPolicy.requiredBytes(PhysicalModelPolicy.MODEL_BYTES)))
        }
    }

    @Test fun insufficientCapacityRefusesBeforeOpeningAnySource() {
        var opened = 0
        refuses(PhysicalModelFailure.NO_SPACE) {
            PhysicalModelPolicy.fresh(facts().copy(availableBytes = PhysicalModelPolicy.FRESH_BYTES - 1))
            opened++
        }
        assertEquals(0, opened)
    }

    @Test fun arithmeticCannotWrapAndNegativeObservationsAreRefused() {
        val maximum = Long.MAX_VALUE - PhysicalModelPolicy.RESERVE_BYTES
        assertEquals(Long.MAX_VALUE, PhysicalModelPolicy.requiredBytes(maximum))
        PhysicalModelPolicy.admit(facts().copy(availableBytes = Long.MAX_VALUE), maximum)
        for (value in listOf(-1L, Long.MIN_VALUE, maximum + 1, Long.MAX_VALUE)) {
            refuses(PhysicalModelFailure.INVALID) { PhysicalModelPolicy.requiredBytes(value) }
        }
        refuses(PhysicalModelFailure.INVALID) { PhysicalModelPolicy.admit(facts().copy(availableBytes = -1)) }
    }

    @Test fun ownedAnchorIdentityMustBeValidAndSameUid() {
        listOf(facts().copy(processUid = 0), facts().copy(anchorUid = 0), facts().copy(anchorUid = 10235),
            facts().copy(anchorDevice = 0), facts().copy(anchorDevice = -1),
            facts().copy(anchorInode = 0), facts().copy(anchorInode = -1)).forEach {
            refuses(PhysicalModelFailure.ANCHOR) { PhysicalModelPolicy.pin(it) }
        }
    }

    @Test fun ownerFilesystemInodeAndKernelMemoryCannotChangeWithinLease() {
        listOf(facts().copy(processUid = 10235, anchorUid = 10235), facts().copy(anchorDevice = 72),
            facts().copy(anchorInode = 818), facts().copy(totalMemory = 12 * gib)).forEach { changed ->
            val lease = PhysicalModelPolicy.pin(facts())
            refuses(PhysicalModelFailure.CHANGED) { lease.recheck(changed) }
            refuses(PhysicalModelFailure.CHANGED) { lease.recheck(facts()) }
        }
    }

    @Test fun memoryOrSpaceRefusalCannotBeRevivedByLaterHeadroom() {
        for (bad in listOf(facts().copy(availableMemory = -1), facts().copy(lowMemory = true), facts().copy(availableBytes = 2 * gib - 1))) {
            val lease = PhysicalModelPolicy.pin(facts())
            try { lease.recheck(bad); fail("Expected admission refusal") } catch (_: PhysicalModelException) { }
            refuses(PhysicalModelFailure.CHANGED) { lease.recheck(facts().copy(availableBytes = Long.MAX_VALUE)) }
        }
    }

    @Test fun modelAllocationDoesNotRechargeStartupMemoryOnTheExistingLease() {
        val initial = facts()
        for (available in listOf(0L, gib, 4 * gib - 1)) {
            val loaded = initial.copy(availableMemory = available)
            refuses(PhysicalModelFailure.MEMORY) { PhysicalModelPolicy.pin(loaded) }
            refuses(PhysicalModelFailure.MEMORY) { PhysicalModelPolicy.fresh(loaded) }
            val lease = PhysicalModelPolicy.pin(initial)
            assertEquals(loaded, lease.recheck(loaded))
            assertEquals(loaded, PhysicalModelPolicy.ongoing(loaded))
        }
    }

    @Test fun changingCurrentCapacityDoesNotConsumeOrReserveMemoryAndDisk() {
        val initial = facts()
        val lease = PhysicalModelPolicy.pin(initial)
        val smaller = initial.copy(availableMemory = 4 * gib, availableBytes = 2 * gib)
        assertEquals(smaller, lease.recheck(smaller))
        assertEquals(initial, lease.recheck(initial))
        assertEquals(PhysicalModelPolicy.FRESH_BYTES, initial.availableBytes)
    }
}
