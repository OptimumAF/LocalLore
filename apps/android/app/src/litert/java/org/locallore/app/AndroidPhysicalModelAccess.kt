/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.ActivityManager
import android.app.Application
import android.content.Context
import android.os.Build
import android.os.Looper
import android.os.Process
import android.system.Os
import android.system.OsConstants
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import kotlinx.coroutines.CancellationException

/** Explicit internal-storage experiment; never enters the old removable-volume selector. */
internal object AndroidPhysicalModelAccess {
    fun create(context: Context): CandidateModelAccess {
        val storage = AndroidPhysicalModelStorage.open(context)
        return ReceiptCandidateModelAccess(ReceiptModelTransaction(
            storage.control, storage.data, CandidateLocalModel.identity,
            storageAdmission = storage::admit,
        ))
    }
}

/** All paths originate in the exact target Context; no Intent or source metadata selects roots. */
internal class AndroidPhysicalModelStorage private constructor(
    private val context: Context,
    val internal: File,
    private val lease: PhysicalModelLease,
) {
    val source = File(internal, SOURCE_CHILD)
    val control = File(internal, CONTROL_CHILD)
    val data = File(internal, DATA_CHILD)
    val proof = File(internal, PROOF_CHILD)
    private var refused = false
    private val childPins = mutableMapOf<String, Pair<Long, Long>>()

    /** Current shared-filesystem admission before receipt operations and every SDK boundary. */
    @Synchronized fun admit(missingBytes: Long = 0) {
        fixed {
            check(!refused)
            val current = observe(context, internal, childPins)
            lease.recheck(current, missingBytes)
        }
    }

    /** Fresh two-copy capacity is checked separately before any model bytes are staged. */
    @Synchronized fun preflight(): PhysicalModelFacts = fixed {
        check(!refused)
        val current = observe(context, internal, childPins)
        lease.recheck(current, 2 * PhysicalModelPolicy.MODEL_BYTES)
        check(!Files.exists(control.toPath(), NOFOLLOW_LINKS) && !Files.exists(data.toPath(), NOFOLLOW_LINKS))
        current
    }

    @Synchronized fun snapshot(): PhysicalModelFacts = fixed {
        check(!refused)
        observe(context, internal, childPins).also { lease.recheck(it) }
    }

    private inline fun <T> fixed(action: () -> T): T = try { action() }
    catch (cancelled: CancellationException) { refused = true; throw cancelled }
    catch (failure: PhysicalModelException) {
        refused = true
        throw LocalModelException(if (failure.failure == PhysicalModelFailure.NO_SPACE) LocalModelFailure.NO_SPACE else LocalModelFailure.STORAGE)
    } catch (_: Exception) {
        refused = true
        throw LocalModelException(LocalModelFailure.STORAGE)
    }

    companion object {
        const val SOURCE_CHILD = "physical-model-source-v1"
        const val CONTROL_CHILD = "physical-model-control-v1"
        const val DATA_CHILD = "physical-model-data-v1"
        const val PROOF_CHILD = "physical-model-proof-v1"
        private val children = listOf(SOURCE_CHILD, CONTROL_CHILD, DATA_CHILD, PROOF_CHILD)
        private val legacy = listOf("local-model-v1", "local-model-removable-v1",
            "local-model-receipt-control-v1", "local-model-receipt-data-v1")

        fun open(context: Context): AndroidPhysicalModelStorage = try {
            configuration(context)
            val app = context.applicationContext
            // Resolve Android's trusted /data/user alias once; every selected child remains strict.
            val anchor = app.noBackupFilesDir.canonicalFile
            val initial = observe(app, anchor)
            AndroidPhysicalModelStorage(app, anchor, PhysicalModelPolicy.pin(initial)).also { it.admit() }
        } catch (cancelled: CancellationException) { throw cancelled }
        catch (failure: PhysicalModelException) {
            throw LocalModelException(if (failure.failure == PhysicalModelFailure.NO_SPACE) LocalModelFailure.NO_SPACE else LocalModelFailure.STORAGE)
        } catch (failure: LocalModelException) { throw failure }
        catch (_: Exception) { throw LocalModelException(LocalModelFailure.STORAGE) }

        private fun configuration(context: Context) {
            check(Looper.myLooper() != Looper.getMainLooper())
            if (Build.VERSION.SDK_INT < 31) error("Physical profile unavailable")
            check(Build.VERSION.SDK_INT == 36 && BuildConfig.DEBUG && BuildConfig.PHYSICAL_MODEL_VERIFICATION &&
                BuildConfig.MODEL_RECEIPT_VERIFICATION && !BuildConfig.MODEL_VOLUME_VERIFICATION)
            check(context.applicationContext.packageName == PhysicalModelPolicy.PACKAGE &&
                Application.getProcessName() == PhysicalModelPolicy.PACKAGE &&
                context.applicationContext.applicationInfo.uid == Process.myUid())
            check(CandidateLocalModel.identity.bytes == PhysicalModelPolicy.MODEL_BYTES &&
                CandidateLocalModel.identity.sha256 == PhysicalModelPolicy.MODEL_SHA256)
        }

        private fun observe(context: Context, anchor: File, pins: MutableMap<String, Pair<Long, Long>>? = null): PhysicalModelFacts {
            if (Build.VERSION.SDK_INT < 31) error("Physical profile unavailable")
            configuration(context)
            check(context.noBackupFilesDir.canonicalFile == anchor)
            val uid = Process.myUid()
            val anchorStat = directory(anchor, uid)
            for (name in legacy) check(!Files.exists(File(anchor, name).toPath(), NOFOLLOW_LINKS))
            for (name in children) {
                val child = File(anchor, name)
                check(child.parentFile == anchor)
                if (Files.exists(child.toPath(), NOFOLLOW_LINKS)) {
                    val info = directory(child, uid)
                    check(info.st_dev == anchorStat.st_dev)
                    val identity = info.st_dev to info.st_ino
                    pins?.get(name)?.let { check(it == identity) }
                    pins?.set(name, identity)
                } else {
                    check(pins?.containsKey(name) != true)
                }
            }
            val memory = ActivityManager.MemoryInfo().also {
                context.getSystemService(ActivityManager::class.java).getMemoryInfo(it)
            }
            return PhysicalModelFacts(Build.MODEL, Build.VERSION.SDK_INT, Build.SOC_MODEL,
                Build.SUPPORTED_ABIS.firstOrNull() ?: "", Os.sysconf(OsConstants._SC_PAGESIZE),
                memory.totalMem, memory.availMem, memory.lowMemory, anchor.usableSpace,
                uid, anchorStat.st_uid, anchorStat.st_dev, anchorStat.st_ino)
        }

        private fun directory(file: File, uid: Int): android.system.StructStat {
            val path = file.toPath()
            check(file.isAbsolute && path.normalize() == path && file.canonicalFile == file)
            var cursor: java.nio.file.Path? = path
            while (cursor != null) {
                check(Files.isDirectory(cursor, NOFOLLOW_LINKS) && !Files.isSymbolicLink(cursor))
                cursor = cursor.parent
            }
            return Os.lstat(file.path).also {
                check(OsConstants.S_ISDIR(it.st_mode) && it.st_uid == uid && it.st_dev > 0 && it.st_ino > 0)
            }
        }
    }
}
