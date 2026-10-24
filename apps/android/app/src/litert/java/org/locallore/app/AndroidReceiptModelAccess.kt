/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Looper
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import kotlinx.coroutines.CancellationException

/** Context and build flags supply authority; imported files never select a model root. */
internal object AndroidReceiptModelAccess {
    const val CONTROL_CHILD = "local-model-receipt-control-v1"
    const val DATA_CHILD = "local-model-receipt-data-v1"

    fun create(context: Context): CandidateModelAccess {
        check(Looper.myLooper() != Looper.getMainLooper())
        check(BuildConfig.MODEL_RECEIPT_VERIFICATION && BuildConfig.MODEL_VOLUME_VERIFICATION)
        val app = context.applicationContext
        val volume = AndroidModelVolume.select(app)
        val internal = app.noBackupFilesDir.canonicalFile
        val external = checkNotNull(volume.root.parentFile)
        val guard = CandidateReceiptAdmission(volume.root, volume::admit)
        return ReceiptCandidateModelAccess(ReceiptModelTransaction(
            File(internal, CONTROL_CHILD), File(external, DATA_CHILD), CandidateLocalModel.identity,
            storageAdmission = guard::admit,
        ))
    }
}

/** A rejected legacy root or media observation cannot later redirect this access instance. */
internal class CandidateReceiptAdmission(
    private val legacyRoot: File,
    private val volumeAdmission: (Long) -> Unit,
) {
    private var refused = false

    fun admit(missingModelBytes: Long = 0): Unit = synchronized(this) {
        if (refused) throw LocalModelException(LocalModelFailure.STORAGE)
        try {
            volumeAdmission(missingModelBytes)
            if (Files.exists(legacyRoot.toPath(), NOFOLLOW_LINKS)) {
                throw LocalModelException(LocalModelFailure.STORAGE)
            }
        } catch (cancelled: CancellationException) {
            refused = true
            throw cancelled
        } catch (failure: LocalModelException) {
            refused = true
            throw failure
        } catch (_: Exception) {
            refused = true
            throw LocalModelException(LocalModelFailure.STORAGE)
        }
    }
}
