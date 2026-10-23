/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.runners.model.MultipleFailureException
import java.io.File
import java.util.UUID
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicBoolean

/** Test-only capacity relief; Rust remains the sole authority for all accepted state. */
internal object SqliteReliefFixture {
    private val ownershipClean = AtomicBoolean(true)
    const val FULL_NOTICE = "Local storage is full. Free space, then retry recovery. Saved progress is retained."
    data class Call(val op: String, val turn: String?, val status: String, val error: String?, val phase: String?)
    class Replies(context: Context) : WorkspaceTransport {
        private val actual = NativeWorkspaceTransport(context)
        val calls = CopyOnWriteArrayList<Call>()
        val submits = CopyOnWriteArrayList<JSONObject>()
        val exchanges = AtomicInteger()
        var beforeFirstCommit: (suspend () -> Unit)? = null
        private var session: String? = null
        private var scope: JSONObject? = null
        override suspend fun exchange(command: JSONObject): JSONObject {
            exchanges.incrementAndGet()
            try {
                val op = command.getString("op")
                val turn = if (op == "submit") command.getJSONObject("request").getString("turn")
                    else command.optString("turn").takeUnless { it.isEmpty() }
                if (op == "submit") submits += JSONObject(command.toString())
                if (op == "commit") beforeFirstCommit?.also { beforeFirstCommit = null }?.invoke()
                val reply = actual.exchange(command)
                val data = if (reply.getString("status") == "ok") reply.getJSONObject("data") else null
                calls += Call(op, turn, reply.getString("status"),
                    reply.optString("error").takeUnless { it.isEmpty() }, data?.optString("phase"))
                if (data != null && op in setOf("create", "resume")) {
                    session = data.getString("session")
                    scope = JSONObject(data.getJSONObject("scope").toString())
                }
                return reply // No synthesized or modified native reply.
            } finally { exchanges.decrementAndGet() }
        }
        override fun close() = actual.close()
        fun count(op: String) = calls.count { it.op == op }
        fun key() = submits.single().getJSONObject("request").getString("turn")
        fun request() = JSONObject(submits.single().getJSONObject("request").toString())
        fun scoped(op: String) = JSONObject().put("op", op).put("session", checkNotNull(session)).put("scope", checkNotNull(scope))
        suspend fun native(command: JSONObject): JSONObject {
            val reply = exchange(command)
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        suspend fun status(key: String = key()) = native(scoped("turn_status").put("turn", key))
        suspend fun acceptedView(revision: Long) = native(scoped("play_snapshot").put("expected_revision", revision)).toString()
        suspend fun resubmit(request: JSONObject) = native(JSONObject().put("op", "submit")
            .put("session", checkNotNull(session)).put("request", request).put("mode", "accepted"))
        fun originalOnly(commits: Int, full: Int, accepted: Int) {
            assertEquals(1, submits.size)
            check(key().length == 36 && UUID.fromString(key()).toString() == key())
            assertEquals(1, count("prepare"))
            assertEquals(commits, count("commit"))
            assertEquals(full, calls.count { it.op == "commit" && it.status == "rejected" && it.error == "Full" })
            assertEquals(accepted, calls.count { it.op == "commit" && it.status == "ok" && it.phase == "committed" })
            assertTrue(calls.filter { it.turn != null }.all { it.turn == key() })
        }
    }
    class Owner(context: Context) {
        val replies = Replies(context)
        val gateway = DurableGateway(replies)
    }
    class Fixture(val context: Context, val token: String) {
        val root = context.noBackupFilesDir.canonicalFile
        val database = File(root, "workspace-v1/stories.sqlite3")
        val padding = PaddingOwner(database, token)
        val main = Owner(context)
        val owners = mutableListOf(main)
        val models = mutableListOf<ViewModelStore>()
        fun model(): ShellViewModel {
            val store = ViewModelStore().also { models += it }
            return ViewModelProvider(store, object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T = ShellViewModel(main.gateway) as T
            })[ShellViewModel::class.java]
        }
        suspend fun closeOwners() {
            withContext(Dispatchers.Main) { models.forEach { it.clear() }; owners.forEach { it.gateway.close() } }
            withTimeout(8_000) { while (owners.any { it.replies.exchanges.get() != 0 }) delay(5) }
        }
        suspend fun reopen(): Owner {
            check(padding.restored) { "padding_restore_required_before_reopen" }
            closeOwners()
            released(database)
            return Owner(context).also { owners += it }
        }
    }
    private fun context(): Pair<Context, String> {
        val actual = InstrumentationRegistry.getInstrumentation().targetContext
        check(actual.packageName == "org.locallore.app.capacityrelief")
        @Suppress("DEPRECATION")
        val info = actual.packageManager.getApplicationInfo(actual.packageName, PackageManager.GET_META_DATA)
        check(info.flags and ApplicationInfo.FLAG_TEST_ONLY != 0)
        check(actual.packageManager.getApplicationLabel(info).toString() == "LocalLore \u00B7 SQLite capacity relief test")
        val metadata = checkNotNull(info.metaData)
        check(metadata.get("org.locallore.capacity.relief.pages") == 32)
        check(metadata.get("org.locallore.capacity.relief.format") == 1)
        val parent = actual.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-capacity-relief-${UUID.randomUUID()}")
        check(root.mkdir() && root.canonicalFile.parentFile == parent)
        val token = UUID.randomUUID().toString().replace("-", "")
        val marker = File(root, PaddingFormat.MARKER)
        check(marker.createNewFile())
        marker.writeText(token + "\n", Charsets.US_ASCII)
        return object : ContextWrapper(actual) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        } to token
    }
    suspend fun fixture(block: suspend (Fixture) -> Unit) {
        check(ownershipClean.get()) { "prior_relief_ownership_unknown" }
        val (context, token) = context()
        val f = Fixture(context, token)
        val failures = mutableListOf<Throwable>()
        try { block(f) } catch (failure: Throwable) { failures += failure }
        withContext(NonCancellable) {
            // Fence callbacks and drain existing owners before attempting DROP.
            // Closing an existing handle is allowed while padded; new owners are not.
            var drained = false
            try { f.closeOwners(); drained = true } catch (failure: Throwable) {
                failures += failure; ownershipClean.set(false)
            }
            if (f.padding.hasUnknownOwnership) ownershipClean.set(false)
            var restored = false
            if (drained && ownershipClean.get()) try {
                if (f.database.exists()) f.padding.drop()
                restored = f.padding.restored
                if (!restored) ownershipClean.set(false)
            } catch (failure: Throwable) { failures += failure; ownershipClean.set(false) }
            var closed = false
            if (restored && drained && ownershipClean.get()) try {
                if (f.database.exists()) released(f.database)
                closed = true
            } catch (failure: Throwable) { failures += failure; ownershipClean.set(false) }
            if (closed) try {
                withContext(Dispatchers.IO) {
                    val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
                    check(f.root.canonicalFile.parentFile == parent)
                    check(f.root.walkTopDown().filter { it.isFile }.sumOf { it.length() } < 2 * 1024 * 1024)
                    check(f.root.deleteRecursively())
                }
            } catch (failure: Throwable) { failures += failure }
        }
        MultipleFailureException.assertEmpty(failures)
    }
    suspend fun full(block: suspend () -> Any?) {
        try { block(); fail("Expected actual Rust SQLite Full") }
        catch (failure: WorkspaceFailure) { assertEquals("Full", failure.category) }
    }
    fun initial(saved: SavedSnapshot) {
        assertEquals(0L, saved.revision); assertEquals("You", saved.potionOwner)
        assertTrue(saved.messages.isEmpty()); assertEquals(1, saved.stories.size)
    }
    fun sameAccepted(before: SavedSnapshot, after: SavedSnapshot) {
        assertEquals(before.revision, after.revision); assertEquals(before.potionOwner, after.potionOwner)
        assertEquals(before.messages, after.messages); assertEquals(before.selected, after.selected)
        assertEquals(before.stories, after.stories); assertEquals(before.rulesProfile, after.rulesProfile)
        assertEquals(before.schemaVersion, after.schemaVersion); assertEquals(before.location, after.location)
    }
    fun accepted(saved: SavedSnapshot) {
        assertEquals(1L, saved.revision); assertEquals("Not in your inventory", saved.potionOwner)
        assertEquals(2, saved.messages.size); assertEquals(0, saved.uncommittedDrafts)
        assertEquals("You give 1 potion to mira.", saved.messages.single { !it.isPlayer }.text)
    }
    fun phase(status: JSONObject, phase: String) {
        assertEquals(phase, status.getString("phase"))
        assertEquals(0L, status.getLong("expected_revision"))
        assertTrue(status.has("receipt"))
        assertEquals(phase == "committed", !status.isNull("receipt"))
    }
    private suspend fun released(path: File) = withContext(Dispatchers.IO) {
        withTimeout(8_000) {
            while (true) {
                val handles = mutableListOf<Long>()
                try {
                    repeat(4) { NativeWorkspace.open(path.absolutePath).let { if (it != 0L) handles += it } }
                    if (handles.size == 4) break
                } finally { handles.forEach { NativeWorkspace.close(it) } }
                delay(5)
            }
        }
    }
}
