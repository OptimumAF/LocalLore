/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** Public Android observations only. Board platform is an independently pinned HOST fact. */
internal data class PhysicalModelFacts(
    val model: String,
    val api: Int,
    val soc: String,
    val primaryAbi: String,
    val pageBytes: Long,
    val totalMemory: Long,
    val availableMemory: Long,
    val lowMemory: Boolean,
    val availableBytes: Long,
    val processUid: Int,
    val anchorUid: Int,
    val anchorDevice: Long,
    val anchorInode: Long,
)

internal enum class PhysicalModelFailure { IDENTITY, MEMORY, ANCHOR, CHANGED, NO_SPACE, INVALID }
internal class PhysicalModelException(val failure: PhysicalModelFailure) :
    Exception("Physical model unavailable: ${failure.name}")

/** One explicit experiment policy, not a supported-device or allocation guarantee. */
internal object PhysicalModelPolicy {
    const val PROFILE = "s918u1_api36_arm64_4k_v1"
    const val PACKAGE = "org.locallore.app.phoneverify"
    const val GIB = 1_073_741_824L
    const val MODEL_BYTES = 2_588_147_712L
    const val MODEL_SHA256 = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
    const val RESERVE_BYTES = 2 * GIB
    const val FRESH_BYTES = 2 * MODEL_BYTES + RESERVE_BYTES

    fun requiredBytes(missingBytes: Long): Long {
        if (missingBytes < 0 || missingBytes > Long.MAX_VALUE - RESERVE_BYTES) fail(PhysicalModelFailure.INVALID)
        return missingBytes + RESERVE_BYTES
    }

    fun admit(facts: PhysicalModelFacts, missingBytes: Long = 0): PhysicalModelFacts {
        val required = requiredBytes(missingBytes)
        if (facts.model != "SM-S918U1" || facts.api != 36 || facts.soc != "SM8550" ||
            facts.primaryAbi != "arm64-v8a" || facts.pageBytes != 4096L) fail(PhysicalModelFailure.IDENTITY)
        if (facts.totalMemory !in 10 * GIB..12 * GIB || facts.availableMemory !in 4 * GIB..facts.totalMemory ||
            facts.lowMemory) fail(PhysicalModelFailure.MEMORY)
        if (facts.processUid <= 0 || facts.anchorUid != facts.processUid || facts.anchorDevice <= 0 ||
            facts.anchorInode <= 0) fail(PhysicalModelFailure.ANCHOR)
        if (facts.availableBytes < 0) fail(PhysicalModelFailure.INVALID)
        if (facts.availableBytes < required) fail(PhysicalModelFailure.NO_SPACE)
        return facts
    }

    fun fresh(facts: PhysicalModelFacts): PhysicalModelFacts = admit(facts, 2 * MODEL_BYTES)

    fun pin(facts: PhysicalModelFacts): PhysicalModelLease = PhysicalModelLease(admit(facts))

    internal fun fail(reason: PhysicalModelFailure): Nothing = throw PhysicalModelException(reason)
}

/** Failed admission is terminal for this owner; a later larger snapshot cannot revive it. */
internal class PhysicalModelLease internal constructor(private val initial: PhysicalModelFacts) {
    private var refused = false

    @Synchronized fun recheck(current: PhysicalModelFacts, missingBytes: Long = 0): PhysicalModelFacts {
        if (refused) PhysicalModelPolicy.fail(PhysicalModelFailure.CHANGED)
        try {
            PhysicalModelPolicy.admit(current, missingBytes)
            if (current.processUid != initial.processUid || current.anchorUid != initial.anchorUid ||
                current.anchorDevice != initial.anchorDevice || current.anchorInode != initial.anchorInode ||
                current.totalMemory != initial.totalMemory) PhysicalModelPolicy.fail(PhysicalModelFailure.CHANGED)
            return current
        } catch (failure: PhysicalModelException) {
            refused = true
            throw failure
        }
    }
}
