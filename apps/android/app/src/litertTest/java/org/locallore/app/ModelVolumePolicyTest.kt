/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Original observations only; no Android, filesystem, real model, SDK or device access. */
class ModelVolumePolicyTest {
    private val app = "org.locallore.app.modelvolumeverify"
    private val mount = "/storage/ABCD-1234"
    private fun facts() = ModelVolumeFacts("opaque-volume-v1", 7, "$mount/Android/data/$app/files", mount,
        mounted = true, removable = true, primary = false, emulated = false, writable = true,
        availableBytes = 8_589_934_592L)
    private fun select(rows: List<ModelVolumeFacts> = listOf(facts()), device: Long = 2, name: String = app) =
        ModelVolumePolicy.select(rows, device, name)
    private fun refusal(expected: ModelVolumeFailure, action: () -> Unit) {
        try { action(); fail("Expected fixed refusal") }
        catch (failure: ModelVolumeException) {
            assertEquals(expected, failure.failure)
            assertEquals("Model volume unavailable: ${expected.name}", failure.message)
            assertNull(failure.cause)
        }
    }
    private fun recheck(row: ModelVolumeFacts = facts(), userdata: Long = ModelVolumePolicy.USERDATA_MIN_BYTES,
        missing: Long = 0, device: Long = 2) = select().recheck(listOf(row), device, userdata, missing)

    @Test fun selectsOnlyEligibleVolumeWithoutOrderFallback() {
        val ineligible = listOf(facts().copy(mounted = false), facts().copy(removable = false),
            facts().copy(primary = true), facts().copy(emulated = true), facts().copy(writable = false))
        assertEquals(facts(), select(ineligible + facts()).volume)
        assertEquals(facts(), select(listOf(facts()) + ineligible).volume)
        ineligible.forEach { refusal(ModelVolumeFailure.MISSING) { select(listOf(it)) } }
        refusal(ModelVolumeFailure.MISSING) { select(emptyList()) }
    }

    @Test fun duplicateAndDistinctEligibleVolumesAreBothAmbiguous() {
        refusal(ModelVolumeFailure.AMBIGUOUS) { select(listOf(facts(), facts())) }
        refusal(ModelVolumeFailure.AMBIGUOUS) { select(listOf(facts(), facts().copy(uuid = "other", device = 9))) }
        refusal(ModelVolumeFailure.AMBIGUOUS) { select(listOf(facts(), facts().copy(uuid = null))) }
        refusal(ModelVolumeFailure.INVALID) { select(List(17) { facts().copy(mounted = false) }) }
    }

    @Test fun invalidIdentityAndCapacityObservationsAreRefused() {
        listOf(facts().copy(uuid = null), facts().copy(uuid = ""), facts().copy(uuid = "x".repeat(129)),
            facts().copy(uuid = "private\ncanary"), facts().copy(device = 0), facts().copy(device = -1),
            facts().copy(device = 2), facts().copy(availableBytes = -1)).forEach {
            refusal(ModelVolumeFailure.INVALID) { select(listOf(it)) }
        }
        refusal(ModelVolumeFailure.INVALID) { select(device = 0) }
        refusal(ModelVolumeFailure.INVALID) { select(device = -1) }
        refusal(ModelVolumeFailure.INVALID) { recheck(userdata = -1) }
    }

    @Test fun onlyExactOwnedAnchorIsAcceptedWithoutFilesystemAccess() {
        val wrong = listOf(null, "relative", "$mount/Android/data/other.app/files", "$mount/Android/data/$app/files/child",
            "$mount/Android/data/$app/files/", "$mount/Android/data/$app/files/../files")
        wrong.forEach { refusal(ModelVolumeFailure.INVALID) { select(listOf(facts().copy(appFilesPath = it))) } }
        listOf(null, "/", "storage/ABCD", "/storage//ABCD", "/storage/./ABCD", "/storage/../ABCD",
            "/storage/ABCD/", "/storage/a\\b", "/storage/a\n", "/" + "x".repeat(4096)).forEach {
            refusal(ModelVolumeFailure.INVALID) { select(listOf(facts().copy(mountRootPath = it))) }
        }
        listOf("", "single", "org..app", "org/app", "org.app\n", "1org.app").forEach {
            refusal(ModelVolumeFailure.INVALID) { select(name = it) }
        }
    }

    @Test fun recheckPinsUuidFilesystemBothPathsAndUserdataDevice() {
        listOf(facts().copy(uuid = "remounted"), facts().copy(device = 8),
            facts().copy(mountRootPath = "/storage/NEW", appFilesPath = "/storage/NEW/Android/data/$app/files"))
            .forEach { refusal(ModelVolumeFailure.CHANGED) { recheck(it) } }
        refusal(ModelVolumeFailure.INVALID) { recheck(facts().copy(appFilesPath = "$mount/Android/data/other.app/files")) }
        refusal(ModelVolumeFailure.CHANGED) { recheck(device = 3) }
        refusal(ModelVolumeFailure.MISSING) { recheck(facts().copy(mounted = false)) }
        refusal(ModelVolumeFailure.MISSING) { recheck(facts().copy(writable = false)) }
        refusal(ModelVolumeFailure.AMBIGUOUS) { select().recheck(listOf(facts(), facts()), 2, Long.MAX_VALUE, 0) }
    }

    @Test fun changingFreeBytesDoesNotChangePinnedIdentity() {
        val row = facts().copy(availableBytes = ModelVolumePolicy.EXTERNAL_MIN_BYTES)
        assertEquals(row, recheck(row))
        assertEquals(facts(), select().volume) // Rechecking never mutates the pin.
    }

    @Test fun runtimeExternalAndUserdataFloorsAreInclusive() {
        assertEquals(ModelVolumePolicy.EXTERNAL_MIN_BYTES, ModelVolumePolicy.externalRequiredBytes(0))
        recheck(facts().copy(availableBytes = ModelVolumePolicy.EXTERNAL_MIN_BYTES))
        refusal(ModelVolumeFailure.NO_SPACE) { recheck(facts().copy(availableBytes = ModelVolumePolicy.EXTERNAL_MIN_BYTES - 1)) }
        refusal(ModelVolumeFailure.NO_SPACE) { recheck(userdata = ModelVolumePolicy.USERDATA_MIN_BYTES - 1) }
        recheck(userdata = Long.MAX_VALUE)
    }

    @Test fun importUsesMaximumOfExistingRuntimeFloorAndArtifactPlusReserve() {
        val model = 2_588_147_712L
        val required = model + ModelVolumePolicy.IMPORT_RESERVE_BYTES
        assertEquals(2_856_583_168L, ModelVolumePolicy.externalRequiredBytes(model))
        recheck(facts().copy(availableBytes = required), missing = model)
        refusal(ModelVolumeFailure.NO_SPACE) { recheck(facts().copy(availableBytes = required - 1), missing = model) }
        assertEquals(ModelVolumePolicy.EXTERNAL_MIN_BYTES, ModelVolumePolicy.externalRequiredBytes(63))
        assertEquals(ModelVolumePolicy.EXTERNAL_MIN_BYTES,
            ModelVolumePolicy.externalRequiredBytes(ModelVolumePolicy.EXTERNAL_MIN_BYTES - ModelVolumePolicy.IMPORT_RESERVE_BYTES))
    }

    @Test fun capacityArithmeticRefusesOverflowWithoutWrapping() {
        val largest = Long.MAX_VALUE - ModelVolumePolicy.IMPORT_RESERVE_BYTES
        assertEquals(Long.MAX_VALUE, ModelVolumePolicy.externalRequiredBytes(largest))
        recheck(facts().copy(availableBytes = Long.MAX_VALUE), missing = largest)
        listOf(-1L, Long.MIN_VALUE, largest + 1, Long.MAX_VALUE).forEach {
            refusal(ModelVolumeFailure.INVALID) { ModelVolumePolicy.externalRequiredBytes(it) }
        }
    }

    @Test fun refusalBeforeCallerDispatchAndDiagnosticsContainNoPrivateFacts() {
        var opens = 0
        refusal(ModelVolumeFailure.NO_SPACE) {
            recheck(facts().copy(availableBytes = 0))
            opens++ // Represents the caller's source/model/Engine dispatch, never run on refusal.
        }
        assertEquals(0, opens)
        assertEquals("ModelVolumeFacts(redacted)", facts().toString())
        assertEquals("ModelVolumeLease(redacted)", select().toString())
    }
}
