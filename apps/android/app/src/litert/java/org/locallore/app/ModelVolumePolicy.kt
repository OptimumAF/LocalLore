/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** Context observations only. The Android adapter proves canonical paths and filesystem facts. */
internal data class ModelVolumeFacts(
    val uuid: String?,
    val device: Long,
    val appFilesPath: String?,
    val mountRootPath: String?,
    val mounted: Boolean,
    val removable: Boolean,
    val primary: Boolean,
    val emulated: Boolean,
    val writable: Boolean,
    val availableBytes: Long,
) {
    // Facts contain private identities. Accidental diagnostic interpolation must not expose them.
    override fun toString(): String = "ModelVolumeFacts(redacted)"
}

internal enum class ModelVolumeFailure { MISSING, AMBIGUOUS, INVALID, CHANGED, NO_SPACE }
internal class ModelVolumeException(val failure: ModelVolumeFailure) :
    Exception("Model volume unavailable: ${failure.name}")

/** Immutable observation pin, not a filesystem reservation or proof against a compromised OS. */
internal class ModelVolumeLease internal constructor(
    val volume: ModelVolumeFacts,
    private val userdataDevice: Long,
    private val packageName: String,
) {
    /** Re-observe immediately before owned file work and SDK admission. Does no I/O itself. */
    fun recheck(
        candidates: List<ModelVolumeFacts>,
        userdataDevice: Long,
        userdataFree: Long,
        missingModelBytes: Long,
    ): ModelVolumeFacts {
        if (this.userdataDevice != userdataDevice) fail(ModelVolumeFailure.CHANGED)
        val current = ModelVolumePolicy.select(candidates, userdataDevice, packageName).volume
        if (volume.uuid != current.uuid || volume.device != current.device ||
            volume.appFilesPath != current.appFilesPath || volume.mountRootPath != current.mountRootPath
        ) fail(ModelVolumeFailure.CHANGED)
        val required = ModelVolumePolicy.externalRequiredBytes(missingModelBytes)
        if (userdataFree < 0) fail(ModelVolumeFailure.INVALID)
        if (userdataFree < ModelVolumePolicy.USERDATA_MIN_BYTES || current.availableBytes < required) {
            fail(ModelVolumeFailure.NO_SPACE)
        }
        return current
    }

    override fun toString(): String = "ModelVolumeLease(redacted)"
}

/** Pure candidate policy. Existing benchmark floors remain independent of model import reserve. */
internal object ModelVolumePolicy {
    const val IMPORT_RESERVE_BYTES = 268_435_456L
    const val EXTERNAL_MIN_BYTES = 2_147_483_648L
    const val USERDATA_MIN_BYTES = 1_140_850_688L

    fun select(
        candidates: List<ModelVolumeFacts>,
        userdataDevice: Long,
        packageName: String,
    ): ModelVolumeLease {
        if (userdataDevice <= 0 || candidates.size > 16 || packageName.length > 255 ||
            !packageName.matches(Regex("[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)+"))
        ) fail(ModelVolumeFailure.INVALID)
        val eligible = candidates.filter { it.mounted && it.removable && !it.primary && !it.emulated && it.writable }
        if (eligible.isEmpty()) fail(ModelVolumeFailure.MISSING)
        if (eligible.size != 1) fail(ModelVolumeFailure.AMBIGUOUS)
        val selected = eligible.single()
        val uuid = selected.uuid
        val mount = selected.mountRootPath
        if (uuid.isNullOrEmpty() || uuid.length > 128 || uuid.any { it.code !in 33..126 } ||
            selected.device <= 0 || selected.device == userdataDevice || selected.availableBytes < 0 ||
            !absoluteNormalized(mount) ||
            selected.appFilesPath != "$mount/Android/data/$packageName/files"
        ) fail(ModelVolumeFailure.INVALID)
        return ModelVolumeLease(selected.copy(), userdataDevice, packageName)
    }

    /** Missing artifact bytes are supplied by trusted store state, never picker/model metadata. */
    fun externalRequiredBytes(missingModelBytes: Long): Long {
        val retained = maxOf(EXTERNAL_MIN_BYTES, IMPORT_RESERVE_BYTES)
        if (missingModelBytes < 0 || missingModelBytes > Long.MAX_VALUE - retained) {
            fail(ModelVolumeFailure.INVALID)
        }
        // The runtime floor must remain available after copying, not be consumed by the artifact.
        return missingModelBytes + retained
    }

    private fun absoluteNormalized(path: String?): Boolean = path != null && path.length in 2..4096 &&
        path.startsWith('/') && !path.endsWith('/') && path.none { it.code < 32 || it.code == 127 || it == '\\' } &&
        path.substring(1).split('/').all { it.isNotEmpty() && it != "." && it != ".." }
}

private fun fail(failure: ModelVolumeFailure): Nothing = throw ModelVolumeException(failure)
