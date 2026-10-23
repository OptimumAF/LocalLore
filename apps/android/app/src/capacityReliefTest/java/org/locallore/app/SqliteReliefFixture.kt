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
    private val roots = AtomicInteger()
    private val ownerCreations = AtomicInteger()
    const val FAULT_PACKAGE = "org.locallore.app.capacityfaultsv3"
    fun createdRoots() = roots.get()
    fun createdOwners() = ownerCreations.get()
    data class CleanupObservation(val ownersClosed: Boolean = false, val exchangesDrained: Boolean = false,
        val dropAttempts: Int = 0, val probeDispatches: Int = 0, val deletionAttempted: Boolean = false,
        val rootRetained: Boolean = true)
    const val FULL_NOTICE = "Local storage is full. Free space, then retry recovery. Saved progress is retained."
    data class Call(val op: String, val turn: String?, val status: String, val error: String?, val phase: String?)
    class Replies(context: Context) : WorkspaceTransport {
        private val actual = NativeWorkspaceTransport(context)
        val calls = CopyOnWriteArrayList<Call>()
        val submits = CopyOnWriteArrayList<JSONObject>()
        val exchanges = AtomicInteger()
        val nativeDispatches = AtomicInteger()
        val closeCalls = AtomicInteger()
        var beforeFirstCommit: (suspend () -> Unit)? = null
        private var session: String? = null
        private var scope: JSONObject? = null
        override suspend fun exchange(command: JSONObject): JSONObject {
            check(ownershipClean.get() && PaddingOwner.ownershipKnown()) { "relief_ownership_unknown" }
            exchanges.incrementAndGet()
            try {
                val op = command.getString("op")
                val turn = if (op == "submit") command.getJSONObject("request").getString("turn")
                    else command.optString("turn").takeUnless { it.isEmpty() }
                if (op == "submit") submits += JSONObject(command.toString())
                if (op == "commit") beforeFirstCommit?.also { beforeFirstCommit = null }?.invoke()
                check(ownershipClean.get() && PaddingOwner.ownershipKnown()) { "relief_ownership_unknown" }
                nativeDispatches.incrementAndGet()
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
        override fun close() { closeCalls.incrementAndGet(); actual.close() }
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
        init {
            check(ownershipClean.get() && PaddingOwner.ownershipKnown()) { "relief_ownership_unknown" }
            ownerCreations.incrementAndGet()
        }
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
        var cleanup = CleanupObservation()
            internal set
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
            check(padding.restored && ownershipClean.get() && PaddingOwner.ownershipKnown()) { "padding_restore_required_before_reopen" }
            closeOwners()
            released(database) { cleanup = cleanup.copy(probeDispatches = cleanup.probeDispatches + 1) }
            return Owner(context).also { owners += it }
        }
        suspend fun probeForFaultTest() {
            check(ownershipClean.get() && PaddingOwner.ownershipKnown()) { "relief_ownership_unknown" }
            check(context.packageName == FAULT_PACKAGE)
            released(database) { cleanup = cleanup.copy(probeDispatches = cleanup.probeDispatches + 1) }
        }
    }
    fun requireIdentity(faultsRequired: Boolean = false): Context {
        val actual = InstrumentationRegistry.getInstrumentation().targetContext
        check(actual.packageName in setOf("org.locallore.app.capacityreliefv3", FAULT_PACKAGE))
        val faults = actual.packageName == FAULT_PACKAGE
        check(!faultsRequired || faults)
        @Suppress("DEPRECATION")
        val info = actual.packageManager.getApplicationInfo(actual.packageName, PackageManager.GET_META_DATA)
        check(info.flags and ApplicationInfo.FLAG_TEST_ONLY != 0)
        val label = if (faults) "LocalLore \u00B7 SQLite helper faults v3" else "LocalLore \u00B7 SQLite capacity relief test v3"
        check(actual.packageManager.getApplicationLabel(info).toString() == label)
        val metadata = checkNotNull(info.metaData)
        check(metadata.get("org.locallore.capacity.relief.pages") == 32)
        check(metadata.get("org.locallore.capacity.relief.format") == 2)
        check(metadata.get("org.locallore.capacity.relief.schema_version") == 3)
        check(metadata.get("org.locallore.capacity.relief.initial_pages") == PaddingFormat.INITIAL_PAGES)
        check(metadata.get("org.locallore.capacity.relief.padding_rows") == PaddingFormat.EXPECTED_ROWS)
        if (faults) check(metadata.get("org.locallore.capacity.relief.faults_format") == 1)
        else check(!metadata.containsKey("org.locallore.capacity.relief.faults_format"))
        return actual
    }
    private fun context(): Pair<Context, String> {
        val actual = requireIdentity()
        val parent = actual.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-capacity-relief-v3-${UUID.randomUUID()}")
        check(root.mkdir() && root.canonicalFile.parentFile == parent)
        roots.incrementAndGet()
        val token = UUID.randomUUID().toString().replace("-", "")
        val marker = File(root, PaddingFormat.MARKER)
        check(marker.createNewFile())
        marker.writeText(PaddingFormat.OWNER_FORMAT + "\n" + token + "\n", Charsets.US_ASCII)
        if (actual.packageName == FAULT_PACKAGE) {
            val faultMarker = File(root, PaddingFormat.FAULT_MARKER)
            check(faultMarker.createNewFile()); faultMarker.writeText(PaddingFormat.faultMarker(token), Charsets.US_ASCII)
        }
        return object : ContextWrapper(actual) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        } to token
    }
    suspend fun fixture(block: suspend (Fixture) -> Unit) {
        check(ownershipClean.get() && PaddingOwner.ownershipKnown()) { "prior_relief_ownership_unknown" }
        val (context, token) = context()
        val f = Fixture(context, token)
        val failures = mutableListOf<Throwable>()
        try { block(f) } catch (failure: Throwable) { failures += failure }
        withContext(NonCancellable) {
            // Fence callbacks and drain existing owners before attempting DROP.
            // Closing an existing handle is allowed while padded; new owners are not.
            var drained = false
            try {
                f.closeOwners(); drained = true
                f.cleanup = f.cleanup.copy(ownersClosed = f.owners.all { it.replies.closeCalls.get() > 0 }, exchangesDrained = true)
            } catch (failure: Throwable) {
                failures += failure; ownershipClean.set(false)
            }
            if (f.padding.hasUnknownOwnership || !PaddingOwner.ownershipKnown()) ownershipClean.set(false)
            var restored = false
            if (drained && ownershipClean.get()) try {
                if (f.database.exists()) { f.cleanup = f.cleanup.copy(dropAttempts = f.cleanup.dropAttempts + 1); f.padding.drop() }
                restored = f.padding.restored
                if (!restored) ownershipClean.set(false)
            } catch (failure: Throwable) { failures += failure; ownershipClean.set(false) }
            var closed = false
            if (restored && drained && ownershipClean.get()) try {
                if (f.database.exists()) released(f.database) { f.cleanup = f.cleanup.copy(probeDispatches = f.cleanup.probeDispatches + 1) }
                closed = true
            } catch (failure: Throwable) { failures += failure; ownershipClean.set(false) }
            if (closed) try {
                withContext(Dispatchers.IO) {
                    f.cleanup = f.cleanup.copy(deletionAttempted = true)
                    val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
                    check(f.root.canonicalFile == f.root.absoluteFile && f.root.parentFile == parent)
                    val marker = File(f.root, PaddingFormat.MARKER)
                    check(marker.isFile && marker.canonicalFile == marker.absoluteFile && marker.length() <= 192)
                    val original = PaddingFormat.OWNER_FORMAT + "\n" + f.token + "\n"
                    check(marker.readText(Charsets.US_ASCII) in setOf(original, original + PaddingFormat.SCHEMA + "\n"))
                    val faultMarker = if (f.context.packageName == FAULT_PACKAGE) File(f.root, PaddingFormat.FAULT_MARKER) else null
                    faultMarker?.let {
                        check(it.isFile && it.canonicalFile == it.absoluteFile && it.length() <= 128)
                        check(it.readText(Charsets.US_ASCII) == PaddingFormat.faultMarker(f.token))
                    }
                    val allowed = setOf(PaddingFormat.MARKER, "workspace-v1") + if (faultMarker == null) emptySet() else setOf(PaddingFormat.FAULT_MARKER)
                    check(f.root.list()?.toSet()?.all { it in allowed } == true)
                    val workspace = File(f.root, "workspace-v1")
                    val known = setOf("stories.sqlite3", "stories.sqlite3-journal", "stories.sqlite3-wal", "stories.sqlite3-shm")
                    val files = if (workspace.exists()) {
                        check(workspace.canonicalFile == workspace.absoluteFile && workspace.isDirectory)
                        checkNotNull(workspace.listFiles()).also { entries ->
                            check(entries.all { it.name in known && it.isFile && it.canonicalFile == it.absoluteFile })
                        }.toList()
                    } else emptyList()
                    check(files.sumOf { it.length() } < 2 * 1024 * 1024)
                    files.forEach { check(it.delete()) }
                    if (workspace.exists()) check(workspace.delete())
                    faultMarker?.let { check(it.delete()) }
                    check(marker.delete()); check(f.root.delete())
                    f.cleanup = f.cleanup.copy(rootRetained = false)
                }
            } catch (failure: Throwable) { failures += failure; ownershipClean.set(false) }
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
        assertEquals(1, saved.schemaVersion); assertEquals(3, saved.databaseSchemaVersion)
    }
    fun sameAccepted(before: SavedSnapshot, after: SavedSnapshot) {
        assertEquals(before.revision, after.revision); assertEquals(before.potionOwner, after.potionOwner)
        assertEquals(before.messages, after.messages); assertEquals(before.selected, after.selected)
        assertEquals(before.stories, after.stories); assertEquals(before.rulesProfile, after.rulesProfile)
        assertEquals(before.schemaVersion, after.schemaVersion); assertEquals(before.location, after.location)
        assertEquals(before.databaseSchemaVersion, after.databaseSchemaVersion)
        assertEquals(before.timelines.map { it.copy(uncommittedDrafts = 0) }, after.timelines.map { it.copy(uncommittedDrafts = 0) })
        assertEquals(before.textProvider, after.textProvider)
    }
    fun accepted(saved: SavedSnapshot) {
        assertEquals(1L, saved.revision); assertEquals("Not in your inventory", saved.potionOwner)
        assertEquals(2, saved.messages.size); assertEquals(0, saved.uncommittedDrafts)
        assertEquals(1, saved.schemaVersion); assertEquals(3, saved.databaseSchemaVersion)
        assertEquals("You give 1 potion to mira.", saved.messages.single { !it.isPlayer }.text)
    }
    fun phase(status: JSONObject, phase: String) {
        assertEquals(phase, status.getString("phase"))
        assertEquals(0L, status.getLong("expected_revision"))
        assertTrue(status.has("receipt"))
        assertEquals(phase == "committed", !status.isNull("receipt"))
    }
    private suspend fun released(path: File, onDispatch: () -> Unit = {}) = withContext(Dispatchers.IO) {
        check(ownershipClean.get() && PaddingOwner.ownershipKnown()) { "relief_ownership_unknown" }
        withTimeout(8_000) {
            while (true) {
                val handles = mutableListOf<Long>()
                try {
                    repeat(4) {
                        check(ownershipClean.get() && PaddingOwner.ownershipKnown()) { "relief_ownership_unknown" }
                        onDispatch()
                        NativeWorkspace.open(path.absolutePath).let { if (it != 0L) handles += it }
                    }
                    if (handles.size == 4) break
                } finally { handles.forEach { NativeWorkspace.close(it) } }
                delay(5)
            }
        }
    }
}
