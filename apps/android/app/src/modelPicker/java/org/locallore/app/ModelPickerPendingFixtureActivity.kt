/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Application
import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.os.Build
import android.os.Looper
import android.os.Process
import androidx.lifecycle.lifecycleScope
import java.io.File
import java.io.IOException
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.WRITE
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.json.JSONObject

/** Isolated debug fixture. Actual framework callbacks remain subject to the unchanged controller. */
class ModelPickerPendingFixtureActivity : LocalModelSetupActivity() {
    @Volatile internal var restoredFromSavedState = false
        private set
    @Volatile internal var localStateSaved = false
        private set

    override fun onCreate(savedInstanceState: Bundle?) {
        restoredFromSavedState = savedInstanceState != null
        super.onCreate(savedInstanceState)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        localStateSaved = true
    }

    internal override fun createSetupDependencies(): LocalModelSetupDependencies {
        val context = applicationContext
        val store by lazy { LocalModelStore(ModelPickerPendingFixture.root(context), ModelPickerPendingFixture.identity) }
        return LocalModelSetupDependencies(ModelPickerPendingFixture.identity,
            checkInstalled = { store.installed() != null }, install = { open -> store.import(open) },
            canStart = { true }, openPlay = { throw IOException("Synthetic fixture cannot open inference") })
    }

    internal override fun onModelPickerResultObserved(selected: Boolean, before: LocalModelSetupPhase,
        after: LocalModelSetupPhase) {
        if (Build.VERSION.SDK_INT < 30) {
            ModelPickerPendingFixture.receiptError.set(true)
            return
        }
        val ordinal = ModelPickerPendingFixture.callbackCount.incrementAndGet()
        if (ordinal !in 1..2) {
            ModelPickerPendingFixture.callbackOverflow.set(true)
            launchReceiptWrite {
                ModelPickerPendingFixture.writeNew(File(ModelPickerPendingFixture.root(applicationContext),
                    "callback-overflow-v1.txt"), "overflow-v1\n".toByteArray(Charsets.US_ASCII))
            }
            return // Extra callbacks cannot replace either closed receipt or disappear as success.
        }
        val receipt = JSONObject().put("version", 1).put("ordinal", ordinal)
            .put("pid", Process.myPid()).put("start", Process.getStartElapsedRealtime())
            .put("uid", Process.myUid()).put("process", Application.getProcessName()).put("task_id", taskId)
            .put("saved_restored", restoredFromSavedState).put("selected", selected)
            .put("before", before.name).put("after", after.name)
        launchReceiptWrite {
            val root = ModelPickerPendingFixture.root(applicationContext)
            val ready = ModelPickerPendingFixture.readJson(File(root, "pending-ready-proof-v1.json"), 2048)
            val run = ready.getString("run")
            check(run.matches(Regex("[a-f0-9]{32}")))
            val stats = ModelPickerPendingFixture.stats(applicationContext, run)
            receipt.put("run", run).put("attempts", stats.getInt("attempts"))
                .put("opened", stats.getInt("opened")).put("closed", stats.getInt("closed"))
                .put("active", stats.getInt("active")).put("failures", stats.getInt("failures"))
            ModelPickerPendingFixture.writeJson(File(root, "callback-$ordinal-v1.json"), receipt, 2048)
            ModelPickerPendingFixture.writeNew(File(root, "callback-$ordinal-ready-v1.txt"),
                "callback-ready-v1\n".toByteArray(Charsets.US_ASCII))
        }
    }

    private fun launchReceiptWrite(write: () -> Unit) {
        ModelPickerPendingFixture.receiptWriters.incrementAndGet()
        val job = try {
            lifecycleScope.launch(Dispatchers.IO) {
                try { write() }
                catch (_: Exception) { ModelPickerPendingFixture.receiptError.set(true) }
            }
        } catch (_: Exception) {
            ModelPickerPendingFixture.receiptError.set(true)
            ModelPickerPendingFixture.receiptWriters.decrementAndGet()
            return
        }
        job.invokeOnCompletion { cause ->
            if (cause != null) ModelPickerPendingFixture.receiptError.set(true)
            ModelPickerPendingFixture.receiptWriters.decrementAndGet()
        }
    }
}

/** Fixed paths and bounded original fixture proofs, never selected through an Intent or URI. */
internal object ModelPickerPendingFixture {
    val identity = LocalModelIdentity("synthetic-picker-pending-v1", 63,
        "648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0", 1024)
    val callbackCount = AtomicInteger()
    val callbackOverflow = AtomicBoolean()
    val receiptError = AtomicBoolean()
    val receiptWriters = AtomicInteger()
    fun root(context: Context): File {
        check(Thread.currentThread() !== Looper.getMainLooper().thread)
        check(context.packageName == "org.locallore.app.modelpickerverify")
        return File(context.applicationContext.noBackupFilesDir.canonicalFile, "model-picker-pending-v1")
    }
    fun stats(context: Context, run: String): Bundle {
        check(Thread.currentThread() !== Looper.getMainLooper().thread)
        check(run.matches(Regex("[a-f0-9]{32}")))
        return requireNotNull(context.contentResolver.call(
            Uri.parse("content://org.locallore.app.modelpickerverify.test.modelpicker.control"), "stats", null,
            Bundle().apply { putString("run", run) }))
    }
    fun oldProofs(context: Context): JSONObject {
        check(Thread.currentThread() !== Looper.getMainLooper().thread)
        val anchor = context.applicationContext.noBackupFilesDir.canonicalFile
        val specifications = listOf(
            Triple("picker_model", "model-picker-fixture-v1/model.litertlm", 63),
            Triple("picker_receipt", "model-picker-fixture-v1/picker-process-proof-v1.json", 256),
            Triple("interruption_model", "model-picker-interruption-v1/model.litertlm", 63),
            Triple("interruption_receipt", "model-picker-interruption-v1/interruption-arm-proof-v1.json", 1024),
            Triple("interruption_sentinel", "model-picker-interruption-v1/interruption-sentinel-v1.bin", 128),
            Triple("interruption_cache", "model-picker-interruption-v1/cache/preserve-v1.bin", 128))
        return JSONObject().also { proof ->
            for ((key, child, cap) in specifications) {
                val file = File(anchor, child)
                check(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.length() in 1..cap.toLong())
                val hash = hash(file)
                if (key.endsWith("_model")) check(hash == ModelPickerFixture.identity.sha256 && file.length() == 63L)
                proof.put(key, hash)
            }
        }
    }
    fun hash(file: File): String = MessageDigest.getInstance("SHA-256").digest(file.readBytes())
        .joinToString("") { "%02x".format(it) }
    fun readJson(file: File, cap: Int): JSONObject {
        check(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.length() in 1..cap.toLong())
        return JSONObject(file.readText(Charsets.US_ASCII))
    }
    fun writeJson(file: File, value: JSONObject, cap: Int) {
        val bytes = value.toString().toByteArray(Charsets.US_ASCII)
        check(bytes.size in 1..cap)
        writeNew(file, bytes)
    }
    fun writeNew(file: File, bytes: ByteArray) {
        check(Thread.currentThread() !== Looper.getMainLooper().thread)
        FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
            val buffer = ByteBuffer.wrap(bytes)
            while (buffer.hasRemaining()) channel.write(buffer)
            channel.force(true)
        }
    }
}
