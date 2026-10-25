/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Looper
import java.io.File
import java.security.MessageDigest

/** Debug candidate only. Neither an Intent nor imported metadata can change this identity. */
internal object CandidateLocalModel {
    private val admission = CandidateOwnerAdmission()
    @Volatile private var preparedStore: CandidateModelAccess? = null
    @Volatile private var receiptTrace: LiteRtWorkerTrace? = null
    @Volatile private var receiptSendTrace: LiteRtSendTrace? = null
    const val MODEL_SHA256 = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
    const val WORKER_SHA256 = "aa004c6b32782f1f29606942427ace0494e1c29c78fda44c1c2c431b37b8bdb4"
    val identity = LocalModelIdentity("gemma-4-e2b-it-litertlm-a790a852", 2_588_147_712L, MODEL_SHA256)

    // Exact UTF-8 profile description, hashed separately from the model and worker source.
    // Template identity denotes the bundled container, not an extracted independent template.
    internal const val MANIFEST = """{"version":1,"scope":"debug_candidate_not_phone_qualified","model_repository":"litert-community/gemma-4-E2B-it-litert-lm","model_revision":"a790a852d433991c0c0a41c1154cf9b3850300fa","model_path":"gemma-4-E2B-it.litertlm","model_bytes":2588147712,"model_sha256":"181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c","runtime_revision":"bda624851d74be34d4e1f7fac1fc4155939539c7","worker_source_sha256":"aa004c6b32782f1f29606942427ace0494e1c29c78fda44c1c2c431b37b8bdb4","template_identity":"bundled_model_container","context_tokens":4096,"director_tokens":350,"narrator_tokens":220,"deadline_ms":60000,"repair_limit":1,"threads":4}"""

    fun store(context: Context): CandidateModelAccess = preparedStore ?: synchronized(this) {
        preparedStore ?: run {
            check(Looper.myLooper() != Looper.getMainLooper())
            val app = context.applicationContext
            val store = if (BuildConfig.MODEL_RECEIPT_VERIFICATION) {
                AndroidReceiptModelAccess.create(app)
            } else if (BuildConfig.MODEL_VOLUME_VERIFICATION) {
                val volume = AndroidModelVolume.select(app)
                PublicationCandidateModelAccess(LocalModelStore(volume.root, identity, storageAdmission = volume::admit))
            } else {
                val privateAnchor = app.noBackupFilesDir.canonicalFile
                PublicationCandidateModelAccess(LocalModelStore(File(privateAnchor, "local-model-v1"), identity))
            }
            store
                .also { preparedStore = it }
        }
    }

    internal fun config(files: LocalModelFiles, storageAdmission: () -> Unit = {}): LiteRtWorkerConfig = LiteRtWorkerConfig(
        root = files.root, model = files.model, cache = files.cache,
        expectedModelBytes = identity.bytes, modelSha256 = MODEL_SHA256,
        templateSha256 = MODEL_SHA256, workerSha256 = WORKER_SHA256,
        profileManifestSha256 = MessageDigest.getInstance("SHA-256")
            .digest(MANIFEST.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) },
        storageAdmission = storageAdmission,
    )

    fun canStart(): Boolean = admission.available

    /** Bounded metadata only in the explicit receipt build; no creation, reset or callback. */
    internal fun receiptWorkerSnapshot(): LiteRtWorkerSnapshot? =
        if (BuildConfig.MODEL_RECEIPT_VERIFICATION) receiptTrace?.snapshot() else null

    /** Independent call-site observations; absence never means zero or a reusable owner. */
    internal fun receiptSendSnapshot(): LiteRtSendSnapshot? =
        if (BuildConfig.MODEL_RECEIPT_VERIFICATION) receiptSendTrace?.snapshot() else null

    fun createTransport(context: Context, trace: LiteRtWorkerTrace? = null): NativeWorkspaceTransport = admission.attach {
        // Setup establishes this on IO. ViewModel construction must not query/create directories.
        val store = preparedStore ?: throw WorkspaceConstructionUnavailable()
        val files = store.plannedFiles()
        val observedTrace = trace ?: if (BuildConfig.MODEL_RECEIPT_VERIFICATION) LiteRtWorkerTrace() else null
        val observedSend = if (BuildConfig.MODEL_RECEIPT_VERIFICATION) LiteRtSendTrace() else null
        if (BuildConfig.MODEL_RECEIPT_VERIFICATION) receiptTrace = observedTrace
        if (BuildConfig.MODEL_RECEIPT_VERIFICATION) receiptSendTrace = observedSend
        val owner = config(files) {
            // Capture-only on Main; the unchanged worker invokes this on IO before SDK boundaries.
            check(Looper.myLooper() != Looper.getMainLooper())
            store.admitRuntime()
        }.createOwner(trace = observedTrace, sendTrace = observedSend)
        try { NativeWorkspaceTransport(context, owner) }
        catch (failure: Exception) { owner.close(); throw failure }
    }
}

/** No independent SDK owner may replace a prior, possibly uncertain, process owner. */
internal class CandidateOwnerAdmission {
    private var claimed = false
    val available: Boolean get() = synchronized(this) { !claimed }
    fun <T> attach(create: () -> T): T {
        synchronized(this) {
            if (claimed) throw WorkspaceConstructionUnavailable()
            claimed = true
        }
        // Reservation survives failure, Activity finish and late callbacks. No private cause escapes.
        return try { create() } catch (_: Exception) { throw WorkspaceConstructionUnavailable() }
    }
}
