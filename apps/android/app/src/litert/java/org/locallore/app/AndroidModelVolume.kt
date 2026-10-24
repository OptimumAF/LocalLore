/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Build
import android.os.Environment
import android.os.Looper
import android.os.storage.StorageManager
import android.system.Os
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS

/**
 * Debug-only removable-media admission. Context supplies every path; no URI, Intent, model text,
 * benchmark directory or caller-supplied path can select storage. Facts are operational checks,
 * not authentication of physical media or protection against a compromised OS/concurrent removal.
 * Canonical saves remain in the ordinary internal workspace.
 */
internal class AndroidModelVolume private constructor(
    private val context: Context,
    private val lease: ModelVolumeLease,
    private val appFilesInode: Long,
    private val mountInode: Long,
) {
    val root: File = File(checkNotNull(lease.volume.appFilesPath), "local-model-removable-v1")
    private var refused = false

    /** Always re-observe before model access, publication/cleanup, and deferred SDK construction. */
    fun admit(missingModelBytes: Long = 0): Unit = synchronized(this) {
        fixedFailure {
            check(!refused)
            try {
                offMain()
                if (Build.VERSION.SDK_INT < 30) error("Volume unavailable")
                val snapshot = observe(context)
                val current = lease.recheck(snapshot.volumes, snapshot.userdataDevice,
                    snapshot.userdataFree, missingModelBytes)
                check(Os.stat(checkNotNull(current.appFilesPath)).st_ino == appFilesInode)
                check(Os.stat(checkNotNull(current.mountRootPath)).st_ino == mountInode)
            } catch (failure: Exception) {
                // No same-process recovery can attest that a removed/replaced volume is safe.
                refused = true
                throw failure
            }
        }
    }

    companion object {
        fun select(context: Context): AndroidModelVolume = fixedFailure {
            offMain()
            check(BuildConfig.MODEL_VOLUME_VERIFICATION)
            if (Build.VERSION.SDK_INT < 30) error("Volume unavailable")
            val app = context.applicationContext
            check(app.packageName == "org.locallore.app.modelvolumeverify")
            val snapshot = observe(app)
            val lease = ModelVolumePolicy.select(snapshot.volumes, snapshot.userdataDevice, app.packageName)
            lease.recheck(snapshot.volumes, snapshot.userdataDevice, snapshot.userdataFree, 0)
            AndroidModelVolume(app, lease,
                Os.stat(checkNotNull(lease.volume.appFilesPath)).st_ino,
                Os.stat(checkNotNull(lease.volume.mountRootPath)).st_ino).also { it.admit() }
        }

        private class Snapshot(val volumes: List<ModelVolumeFacts>, val userdataDevice: Long, val userdataFree: Long)

        @androidx.annotation.RequiresApi(30)
        private fun observe(context: Context): Snapshot {
            check(Build.VERSION.SDK_INT >= 30)
            val internal = realDirectory(context.noBackupFilesDir)
            val manager = context.getSystemService(StorageManager::class.java)
            // Android may create this app's system-managed directories. No model/cache is created.
            val volumes = context.getExternalFilesDirs(null).mapNotNull { anchor ->
                if (anchor == null) return@mapNotNull null
                val volume = manager.getStorageVolume(anchor) ?: error("Volume unavailable")
                if (volume.isPrimary) return@mapNotNull null
                val mount = checkNotNull(volume.directory)
                val files = realDirectory(anchor)
                val directory = realDirectory(mount)
                check(manager.getStorageVolume(files)?.uuid == volume.uuid)
                val device = Os.stat(files.path).st_dev
                check(Os.stat(directory.path).st_dev == device)
                ModelVolumeFacts(volume.uuid, device, files.path, directory.path,
                    volume.state == Environment.MEDIA_MOUNTED, volume.isRemovable, volume.isPrimary,
                    volume.isEmulated, files.canWrite(), files.usableSpace)
            }
            return Snapshot(volumes, Os.stat(internal.path).st_dev, internal.usableSpace)
        }

        private fun realDirectory(file: File): File {
            val absolute = file.absoluteFile
            val path = absolute.toPath()
            check(path.normalize() == path && absolute.canonicalFile == absolute)
            var cursor: java.nio.file.Path? = path
            while (cursor != null) {
                check(Files.isDirectory(cursor, NOFOLLOW_LINKS) && !Files.isSymbolicLink(cursor))
                cursor = cursor.parent
            }
            return absolute
        }

        private fun offMain() = check(Looper.myLooper() != Looper.getMainLooper())

        private inline fun <T> fixedFailure(action: () -> T): T = try { action() }
        catch (failure: ModelVolumeException) {
            throw LocalModelException(if (failure.failure == ModelVolumeFailure.NO_SPACE)
                LocalModelFailure.NO_SPACE else LocalModelFailure.STORAGE)
        } catch (_: Exception) { throw LocalModelException(LocalModelFailure.STORAGE) }
    }
}
