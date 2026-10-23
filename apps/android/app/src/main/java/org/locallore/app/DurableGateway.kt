/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/** IO confinement is supplied by the transport; the controller and tests share this protocol. */
internal interface WorkspaceTransport {
    suspend fun exchange(command: JSONObject): JSONObject
    fun close()
}

/** No gameplay rules or ledger live here. Only authoritative player snapshots reach the UI. */
internal class DurableGateway(
    private val transport: WorkspaceTransport,
    autoCreateIfEmpty: Boolean = true,
) : DemoGateway {
    private var mayAutoCreate = autoCreateIfEmpty
    override val durable = true
    override val storyRecords = true
    private var session: String? = null
    private var scope: JSONObject? = null
    private var revision = 0L
    private var operation: Pending? = null
    private var serial = 0L
    private var textProvider = TextProvider.UNAVAILABLE
    // Order cancellation after a finite native submit, never after generation/prepare.
    private val submissionGate = Mutex()
    private val closed = AtomicBoolean(false)
    private data class Pending(val session: String, val scope: JSONObject, val turn: String,
        val request: JSONObject, val mode: DemoMode?, val serial: Long, var cancelled: Boolean = false)

    private suspend fun call(command: JSONObject): JSONObject {
        check(!closed.get())
        val reply = transport.exchange(command)
        check(reply.getInt("version") == 1)
        if (reply.getString("status") != "ok") throw WorkspaceFailure(reply.optString("error", "Storage"))
        return reply.getJSONObject("data")
    }
    private fun command(op: String) = JSONObject().put("op", op)
    override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
        val capturedSession = session ?: throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE)
        val capturedScope = scope ?: throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE)
        fun current() = !closed.get() && session == capturedSession && operation == null &&
            revision == query.context.revision && scope === capturedScope &&
            capturedScope.getString("story") == query.context.story.story &&
            capturedScope.getString("branch") == query.context.story.branch
        if (!current()) throw StoryRecordFailure(StoryRecordProblem.STALE)
        val data = try { call(StoryRecordWire.command(capturedSession, query)) }
        catch (failure: WorkspaceFailure) {
            throw StoryRecordFailure(if (failure.category in setOf("Stale", "Scope", "Session"))
                StoryRecordProblem.STALE else StoryRecordProblem.UNAVAILABLE)
        }
        if (!current()) throw StoryRecordFailure(StoryRecordProblem.STALE)
        return StoryRecordWire.decode(data, query)
    }
    private fun scoped(op: String, pending: Pending? = null): JSONObject = command(op)
        .put("session", pending?.session ?: checkNotNull(session))
        .put("scope", pending?.scope ?: checkNotNull(scope))
        .also { if (pending != null) it.put("turn", pending.turn) }

    override suspend fun initialize(): SavedSnapshot {
        if (session != null) return snapshot()
        return openLibrary(mayAutoCreate)
    }
    private suspend fun workspace(): JSONObject = call(command("workspace")).also {
        check(it.getBoolean("persistent") && it.getInt("schema_version") == 1)
        check(it.getInt("database_schema_version") == 3)
        it.getString("location")
        it.getJSONArray("stories")
    }
    private suspend fun openLibrary(allowCreate: Boolean): SavedSnapshot {
        val workspace = workspace()
        val saved = workspace.getJSONArray("stories")
        // Automatic bootstrap is a one-time compatibility option. Never repeat an uncertain create.
        mayAutoCreate = false
        if (saved.length() == 0 && !allowCreate) return emptySnapshot(workspace)
        attach(if (saved.length() == 0) call(command("create").put("seed", "lantern-quay-v1"))
            else call(command("resume").put("scope", saved.getJSONObject(0).getJSONObject("scope"))))
        return snapshot()
    }
    private fun emptySnapshot(workspace: JSONObject): SavedSnapshot {
        check(workspace.getJSONArray("stories").length() == 0)
        return SavedSnapshot(0, "", emptyList(), workspace.getString("location"), 1,
            emptyList(), null, databaseSchemaVersion = workspace.getInt("database_schema_version"))
    }
    override suspend fun reconcileSaved(): SavedSnapshot {
        mayAutoCreate = false
        operation?.cancelled = true
        operation = null
        closeSession()
        return openLibrary(allowCreate = false)
    }
    private fun attach(data: JSONObject) {
        session = data.getString("session")
        scope = data.getJSONObject("scope")
        revision = data.getLong("revision")
        operation = null
    }
    override suspend fun snapshot(): SavedSnapshot {
        if (session == null) return openLibrary(allowCreate = false)
        // Open refreshes revision from validated persisted canon before coherent player inspection.
        val opened = call(scoped("open"))
        check(sameScope(opened.getJSONObject("scope"), checkNotNull(scope)))
        revision = opened.getLong("revision")
        val view = call(scoped("play_snapshot").put("expected_revision", revision))
        check(sameScope(view.getJSONObject("scope"), checkNotNull(scope)))
        check(view.getLong("revision") == revision)
        val player = view.getJSONObject("player")
        check(player.getString("observer") == "player" && player.getLong("revision") == revision)
        check(sameScope(player.getJSONObject("scope"), checkNotNull(scope)))
        val receipts = view.getJSONArray("receipts")
        val messages = mutableListOf<SceneMessage>()
        for (i in 0 until receipts.length()) {
            val receipt = receipts.getJSONObject(i)
            val request = receipt.getJSONObject("request")
            // Inherited accepted receipts keep their original ancestor scope. Rust's
            // player snapshot owns lineage/fork filtering; never rewrite those requests.
            val originalScope = request.getJSONObject("scope")
            check(originalScope.getString("story") == checkNotNull(scope).getString("story"))
            check(timelineId.matches(originalScope.getString("branch")))
            val intent = request.getJSONObject("intent")
            val playerText = when (intent.getString("kind")) {
                "actions" -> intent.getJSONArray("value").toString()
                "dialogue" -> intent.getJSONObject("value").getString("text")
                "free_text" -> intent.getJSONObject("value").getString("text")
                else -> "Recorded intention"
            }
            messages += SceneMessage(i * 2L + 1, playerText, true)
            messages += SceneMessage(i * 2L + 2, receipt.getString("narration"), false)
        }
        val workspace = workspace()
        // Host-v1's workspace contract and the SQLite implementation have separate versions.
        val databaseSchema = workspace.getInt("database_schema_version")
        check(databaseSchema == 3)
        val stories = workspace.getJSONArray("stories").let { rows -> (0 until rows.length()).map {
            val row = rows.getJSONObject(it); val s = row.getJSONObject("scope")
            SavedStory(s.getString("story"), s.getString("branch"), row.getString("title"), row.getLong("revision"))
        } }
        val selectedScope = checkNotNull(scope)
        val root = checkNotNull(stories.singleOrNull { it.story == selectedScope.getString("story") })
        val timelines = decodeTimelines(call(command("branches").put("story", root.story)), root)
        val current = checkNotNull(timelines.singleOrNull { it.branch == selectedScope.getString("branch") })
        // A concurrent owner can advance between calls. Fail closed and recover a new
        // coherent snapshot rather than attaching a different head's catalog metadata.
        if (current.revision != revision) throw WorkspaceFailure("Stale")
        textProvider = readTextProvider()
        return SavedSnapshot(revision, if (view.getJSONObject("inventory").has("potion")) "You" else "Not in your inventory",
            messages.takeLast(40), workspace.getString("location"), 1, stories,
            SavedStory(current.story, current.branch, root.title, current.revision), current.uncommittedDrafts,
            view.getString("rules"), textProvider, databaseSchemaVersion = databaseSchema, timelines = timelines)
    }
    private suspend fun readTextProvider(): TextProvider {
        val capabilities = call(command("capabilities"))
        val available = capabilities.get("free_text") as? Boolean ?: error("Invalid capability")
        if (!available) return TextProvider.UNAVAILABLE
        val status = call(command("model_status"))
        val real = status.get("real_model") as? Boolean ?: error("Invalid provider")
        val provider = status.get("provider") as? String ?: error("Invalid provider")
        val configured = status.get("status") as? String ?: error("Invalid provider")
        return when {
            real && provider.isNotBlank() && configured == "configured_native_owner" &&
                status.get("loaded") === JSONObject.NULL -> TextProvider.LOCAL
            !real && provider == "android-scripted-play-v2" &&
                configured == "configured_fixture_owner" && status.get("loaded") == false -> TextProvider.SCRIPTED
            else -> TextProvider.UNAVAILABLE
        }
    }
    override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
        check(operation == null)
        val actionCommand = when (action) {
            DemoAction.GIVE_POTION -> command("give").put("item", "potion").put("to", "mira").put("quantity", 1)
            DemoAction.TRY_ABILITY -> command("use_ability").put("ability", "blink")
        }
        val request = JSONObject().put("version", 1).put("scope", checkNotNull(scope))
            .put("turn", UUID.randomUUID().toString()).put("expected_revision", revision)
            .put("intent", JSONObject().put("kind", "actions").put("value", JSONArray().put(actionCommand)))
        return prepareRequest(request, mode)
    }
    override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
        check(operation == null)
        if (textProvider == TextProvider.UNAVAILABLE) return DemoResult.Rejected("Unsupported")
        if (!validPlayInput(input)) return DemoResult.Rejected("Malformed")
        val request = JSONObject().put("version", 1).put("scope", checkNotNull(scope))
            .put("turn", UUID.randomUUID().toString()).put("expected_revision", revision)
            .put("intent", JSONObject().put("kind", "free_text").put("value",
                JSONObject().put("kind", input.kind.wire).put("text", input.text)))
        return prepareRequest(request, null)
    }
    private fun submitCommand(pending: Pending): JSONObject = command(if (pending.mode == null) "free_text" else "submit")
        .put("session", pending.session).put("request", pending.request).also {
            pending.mode?.let { mode -> it.put("mode", mode.name.lowercase(java.util.Locale.ROOT)) }
        }
    private suspend fun prepareRequest(request: JSONObject, mode: DemoMode?): DemoResult {
        val pending = Pending(checkNotNull(session), checkNotNull(scope), request.getString("turn"), request, mode, ++serial)
        operation = pending // Keep the original key even if submit acknowledgement is lost.
        try {
            val submitted = submitOriginal(pending) ?: return DemoResult.Rejected("Cancelled")
            if (pending.cancelled) return DemoResult.Rejected("Cancelled")
            val prepared = if (submitted.getString("phase") == "queued") call(scoped("prepare", pending)) else submitted
            return result(prepared, pending)
        } catch (failure: WorkspaceFailure) {
            // An explicit rejection before acceptance cannot create canon; transport uncertainty stays pending.
            if (failure.category in setOf("Full", "Busy", "Database", "Integrity", "Io", "Internal")) throw failure
            if (operation === pending) operation = null
            return DemoResult.Rejected(failure.category)
        }
    }
    private suspend fun submitOriginal(pending: Pending): JSONObject? = withContext(NonCancellable) {
        submissionGate.withLock {
            if (pending.cancelled) null else call(submitCommand(pending))
        }
    }
    private fun result(data: JSONObject, pending: Pending): DemoResult {
        check(data.getString("turn") == pending.turn && sameScope(data.getJSONObject("scope"), pending.scope))
        check(data.getLong("expected_revision") == pending.request.getLong("expected_revision"))
        val resolved = when (data.getString("phase")) {
        "ready" -> DemoResult.Prepared(0, pending.serial)
        "committed" -> {
            val receipt = data.getJSONObject("receipt")
            check(sameJson(receipt.getJSONObject("request"), pending.request))
            DemoResult.Accepted(pending.request.getLong("expected_revision") + 1, "", receipt.getString("narration"))
        }
        "cancelled", "failed", "stale" -> {
            DemoResult.Rejected(data.optString("error").takeUnless { it.isBlank() || it == "null" } ?: "Cancelled")
        }
        else -> error("Unfinished")
        }
        // Decode the entire authoritative result before releasing its recovery key.
        if (resolved !is DemoResult.Prepared && operation === pending) operation = null
        return resolved
    }
    override suspend fun commitAsync(result: DemoResult): DemoResult {
        if (result !is DemoResult.Prepared) return result
        val pending = operation ?: return DemoResult.Rejected("Cancelled")
        if (pending.cancelled || result.operation != pending.serial) return DemoResult.Rejected("Cancelled")
        val data = try { call(scoped("commit", pending)) }
            catch (failure: Exception) {
                // The original key is the only authority after a lost commit acknowledgement.
                val status = try { call(scoped("turn_status", pending)) } catch (_: Exception) { throw failure }
                if (status.optString("phase") !in setOf("committed", "cancelled", "failed", "stale")) throw failure
                // Ready/queued work is still uncertain. Even a terminal-looking malformed
                // reply cannot discard the key or hide the primary storage error.
                return try { this.result(status, pending) } catch (_: Exception) { throw failure }
            }
        return this.result(data, pending)
    }
    override suspend fun recoverSaved(): SavedSnapshot {
        if (session == null) return initialize()
        operation?.let { pending ->
            if (pending.cancelled) {
                try { submissionGate.withLock { result(call(scoped("cancel", pending)), pending) } }
                catch (failure: WorkspaceFailure) {
                    if (failure.category != "UnknownTurn") throw failure
                    if (operation === pending) operation = null
                }
                return snapshot()
            }
            var status = try { call(scoped("turn_status", pending)) }
                catch (failure: WorkspaceFailure) {
                    if (failure.category != "UnknownTurn") throw failure
                    submitOriginal(pending) ?: return snapshot()
                }
            if (status.getString("phase") == "queued") status = call(scoped("prepare", pending))
            if (status.getString("phase") == "ready") status = call(scoped("commit", pending))
            result(status, pending)
        }
        return snapshot()
    }
    override fun cancel() { operation?.cancelled = true }
    override suspend fun cancelSaved(): SavedSnapshot {
        operation?.let { pending ->
            pending.cancelled = true
            val status = try { submissionGate.withLock { call(scoped("cancel", pending)) } }
                catch (failure: WorkspaceFailure) {
                    if (failure.category != "UnknownTurn") throw failure
                    // Cancellation may beat submit on IO. The captured request remains
                    // cancelled even if its late submit later creates an uncommitted draft.
                    // Never discard a newer operation or regenerate this original key.
                    if (operation === pending) operation = null
                    return@let
                }
            if (status.getString("phase") == "committed") result(status, pending)
            else if (operation === pending) operation = null
        }
        return snapshot()
    }
    private suspend fun closeSession() {
        if (session != null) {
            try { call(scoped("close")) }
            catch (failure: WorkspaceFailure) {
                if (failure.category != "Closed") throw failure
            }
        }
        session = null; scope = null; revision = 0
    }
    private suspend fun release() {
        operation?.let { pending ->
            pending.cancelled = true
            try {
                val status = submissionGate.withLock { call(scoped("cancel", pending)) }
                if (status.getString("phase") == "committed") result(status, pending)
                else if (operation === pending) operation = null
            } catch (failure: WorkspaceFailure) {
                if (failure.category !in setOf("Closed", "UnknownTurn")) throw failure
                if (operation === pending) operation = null
            }
        }
        closeSession()
    }
    override suspend fun createSaved(): SavedSnapshot {
        release()
        attach(call(command("create").put("seed", "lantern-quay-v1")))
        return snapshot()
    }
    override suspend fun resumeSaved(story: SavedStory): SavedSnapshot {
        release()
        attach(call(command("resume").put("scope", JSONObject().put("story", story.story).put("branch", story.branch))))
        return snapshot()
    }
    override fun close() {
        if (closed.compareAndSet(false, true)) { operation?.cancelled = true; transport.close() }
    }
}
internal class WorkspaceFailure(val category: String) : Exception("Workspace operation failed")
private val timelineId = Regex("[A-Za-z0-9_-]{1,64}")

/** Metadata validation only. Replay, history eligibility and gameplay remain Rust-owned. */
private fun decodeTimelines(data: JSONObject, root: SavedStory): List<SavedTimeline> = try {
    check(data.toString().toByteArray(Charsets.UTF_8).size <= 60 * 1024)
    fun fields(value: JSONObject, expected: Set<String>) {
        check(value.keys().asSequence().toSet() == expected)
    }
    fun text(value: JSONObject, key: String): String = value.get(key) as? String ?: error("Wire")
    fun count(value: JSONObject, key: String): Long {
        val raw = value.get(key)
        check(raw is Int || raw is Long)
        return (raw as Number).toLong().also { check(it >= 0) }
    }
    fields(data, setOf("version", "story_id", "title", "root_branch", "branches"))
    check(count(data, "version") == 2L && text(data, "story_id") == root.story)
    check(text(data, "title") == root.title && text(data, "root_branch") == root.branch)
    check(timelineId.matches(root.story) && timelineId.matches(root.branch))
    val rows = data.get("branches") as? JSONArray ?: error("Wire")
    check(rows.length() in 1..256)
    val retiredBranches = mutableSetOf<String>()
    val timelines = (0 until rows.length()).map { index ->
        val row = rows.get(index) as? JSONObject ?: error("Wire")
        fields(row, setOf("scope", "parent_branch", "fork_revision", "revision", "drafts", "retired"))
        val itemScope = row.get("scope") as? JSONObject ?: error("Wire")
        fields(itemScope, setOf("story", "branch"))
        val story = text(itemScope, "story")
        val branch = text(itemScope, "branch")
        check(story == root.story && timelineId.matches(branch))
        val parent = if (row.isNull("parent_branch")) null else text(row, "parent_branch")
        check(parent == null || timelineId.matches(parent))
        val fork = if (row.isNull("fork_revision")) null else count(row, "fork_revision")
        val head = count(row, "revision")
        val drafts = count(row, "drafts")
        val retired = row.get("retired") as? Boolean ?: error("Wire")
        if (retired) {
            check(branch != root.branch && drafts == 0L)
            retiredBranches.add(branch)
        }
        check(drafts <= 4096 && (parent == null) == (fork == null))
        check((branch == root.branch) == (parent == null) && (fork == null || fork <= head))
        SavedTimeline(story, branch, parent, fork, head, drafts.toInt())
    }
    check(timelines.zipWithNext().all { (left, right) -> left.branch < right.branch })
    val byBranch = timelines.associateBy { it.branch }
    check(byBranch[root.branch]?.revision == root.revision)
    for (timeline in timelines) {
        var cursor = timeline
        val seen = mutableSetOf<String>()
        while (true) {
            check(seen.add(cursor.branch) && seen.size <= 32)
            val parent = cursor.parentBranch ?: break
            val ancestor = byBranch[parent] ?: error("Wire")
            check(checkNotNull(cursor.forkRevision) <= ancestor.revision)
            cursor = ancestor
        }
    }
    java.util.Collections.unmodifiableList(timelines.filter { it.branch !in retiredBranches })
} catch (_: Exception) {
    throw WorkspaceFailure("Malformed")
}
private fun sameScope(left: JSONObject, right: JSONObject) =
    left.getString("story") == right.getString("story") && left.getString("branch") == right.getString("branch")
private fun sameJson(left: Any?, right: Any?): Boolean = when {
    left is JSONObject && right is JSONObject -> {
        val keys = left.keys().asSequence().toSet()
        keys == right.keys().asSequence().toSet() && keys.all { sameJson(left.get(it), right.get(it)) }
    }
    left is JSONArray && right is JSONArray -> left.length() == right.length() &&
        (0 until left.length()).all { sameJson(left.get(it), right.get(it)) }
    left is Number && right is Number -> left.toString() == right.toString()
    else -> left == right
}
