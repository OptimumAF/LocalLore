/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.net.Uri
import android.os.Bundle
import android.os.CancellationSignal
import android.os.Handler
import android.os.HandlerThread
import android.os.Looper
import android.os.OperationCanceledException
import android.os.ParcelFileDescriptor
import java.io.File
import java.io.FileNotFoundException
import java.util.concurrent.atomic.AtomicInteger

/** Installed in the test APK only. It accepts no path, filename or data from the caller. */
class TestDiagnosticProvider : ContentProvider() {
    private val opened = AtomicInteger()
    private val closed = AtomicInteger()
    private val started = AtomicInteger()
    private val cancelled = AtomicInteger()
    private val openedOnMain = AtomicInteger()
    private val waiting = Object()
    private lateinit var callbackHandler: Handler

    override fun onCreate(): Boolean {
        callbackHandler = Handler(HandlerThread("diagnostic-test-close").also { it.start() }.looper)
        return true
    }

    override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor? = openFile(uri, mode, null)

    override fun openFile(uri: Uri, mode: String, signal: CancellationSignal?): ParcelFileDescriptor? {
        val path = case(uri)
        check(mode == "wt")
        started.incrementAndGet()
        if (Looper.myLooper() == Looper.getMainLooper()) openedOnMain.incrementAndGet()
        if (path == "failure") throw FileNotFoundException("SYNTHETIC_PROVIDER_SECRET_DO_NOT_EXPORT")
        if (path == "null") return null
        if (path == "slow") {
            signal?.setOnCancelListener {
                cancelled.incrementAndGet()
                synchronized(waiting) { waiting.notifyAll() }
            }
            val deadline = System.nanoTime() + 10_000_000_000L
            synchronized(waiting) {
                while (signal?.isCanceled != true && System.nanoTime() < deadline) waiting.wait(20)
            }
            signal?.throwIfCanceled()
            throw OperationCanceledException("Synthetic slow provider timed out")
        }
        val file = fixture(path)
        if (!file.exists()) file.writeText("SYNTHETIC_OLD_BYTES_LONGER_THAN_NEW_OUTPUT")
        val flags = if (path == "write_failure") ParcelFileDescriptor.MODE_READ_ONLY
        else ParcelFileDescriptor.MODE_READ_WRITE or ParcelFileDescriptor.MODE_CREATE or ParcelFileDescriptor.MODE_TRUNCATE
        return ParcelFileDescriptor.open(file, flags, callbackHandler) { closed.incrementAndGet() }
            .also { opened.incrementAndGet() }
    }

    override fun call(method: String, arg: String?, extras: Bundle?): Bundle = when (method) {
        "reset" -> {
            listOf("success", "write_failure").forEach { fixture(it).delete() }
            opened.set(0); closed.set(0); started.set(0); cancelled.set(0); openedOnMain.set(0)
            Bundle()
        }
        "stats" -> Bundle().apply {
            putInt("opened", opened.get()); putInt("closed", closed.get())
            putInt("started", started.get()); putInt("cancelled", cancelled.get())
            putInt("opened_on_main", openedOnMain.get())
        }
        "bytes" -> Bundle().apply { putByteArray("bytes", fixture("success").takeIf { it.exists() }?.readBytes()) }
        else -> throw IllegalArgumentException("Unsupported synthetic operation")
    }

    private fun fixture(name: String): File = File(requireNotNull(context).cacheDir, "diagnostic-test-$name.json")
    private fun case(uri: Uri): String {
        val name = uri.pathSegments.singleOrNull()
        if (uri.authority != AUTHORITY || uri.query != null || uri.fragment != null ||
            name !in setOf("success", "failure", "write_failure", "null", "slow")) {
            throw FileNotFoundException("Unsupported synthetic destination")
        }
        return requireNotNull(name)
    }

    override fun getType(uri: Uri): String { case(uri); return "application/json" }
    override fun query(uri: Uri, projection: Array<out String>?, selection: String?,
        selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null
    override fun insert(uri: Uri, values: ContentValues?): Uri? = throw UnsupportedOperationException()
    override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int =
        throw UnsupportedOperationException()
    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int =
        throw UnsupportedOperationException()

    companion object { const val AUTHORITY = "org.locallore.app.test.diagnostics" }
}
