/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID
import java.util.concurrent.atomic.AtomicBoolean

/** IO confinement is supplied by the transport; the controller and tests share this protocol. */
internal interface WorkspaceTransport {
    suspend fun exchange(command: JSONObject): JSONObject
    fun close()
}

/** No gameplay rules or ledger live here. Only authoritative player snapshots reach the UI. */
internal class DurableGateway(private val transport: WorkspaceTransport) : DemoGateway {
    override val durable = true
    private var session: String? = null
    private var scope: JSONObject? = null
    private var revision = 0L
    private var operation: Pending? = null
    private var serial = 0L
    private val closed = AtomicBoolean(false)
    private data class Pending(val session: String, val scope: JSONObject, val turn: String,
        val request: JSONObject, val mode: DemoMode, val serial: Long, var cancelled: Boolean = false)

    private suspend fun call(command: JSONObject): JSONObject {
        check(!closed.get())
        val reply = transport.exchange(command)
        check(reply.getInt("version") == 1)
        if (reply.getString("status") != "ok") throw WorkspaceFailure(reply.optString("error", "Storage"))
        return reply.getJSONObject("data")
    }
    private fun command(op: String) = JSONObject().put("op", op)
    private fun scoped(op: String, pending: Pending? = null): JSONObject = command(op)
        .put("session", pending?.session ?: checkNotNull(session))
        .put("scope", pending?.scope ?: checkNotNull(scope))
        .also { if (pending != null) it.put("turn", pending.turn) }

    override suspend fun initialize(): SavedSnapshot {
        if (session != null) return snapshot()
        val workspace = call(command("workspace"))
        check(workspace.getBoolean("persistent"))
        val saved = workspace.getJSONArray("stories")
        attach(if (saved.length() == 0) call(command("create").put("seed", "lantern-quay-v1"))
            else call(command("resume").put("scope", saved.getJSONObject(0).getJSONObject("scope"))))
        return snapshot()
    }
    private fun attach(data: JSONObject) {
        session = data.getString("session")
        scope = data.getJSONObject("scope")
        revision = data.getLong("revision")
        operation = null
    }
    override suspend fun snapshot(): SavedSnapshot {
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
            check(sameScope(request.getJSONObject("scope"), checkNotNull(scope)))
            val intent = request.getJSONObject("intent")
            val playerText = when (intent.getString("kind")) {
                "actions" -> intent.getJSONArray("value").toString()
                "dialogue" -> intent.getJSONObject("value").getString("text")
                else -> "Recorded intention"
            }
            messages += SceneMessage(i * 2L + 1, playerText, true)
            messages += SceneMessage(i * 2L + 2, receipt.getString("narration"), false)
        }
        val workspace = call(command("workspace"))
        check(workspace.getBoolean("persistent") && workspace.getInt("schema_version") == 1)
        val stories = workspace.getJSONArray("stories").let { rows -> (0 until rows.length()).map {
            val row = rows.getJSONObject(it); val s = row.getJSONObject("scope")
            SavedStory(s.getString("story"), s.getString("branch"), row.getString("title"), row.getLong("revision"))
        } }
        val current = checkNotNull(stories.find { it.story == scope!!.getString("story") && it.branch == scope!!.getString("branch") })
        return SavedSnapshot(revision, if (view.getJSONObject("inventory").has("potion")) "You" else "Not in your inventory",
            messages.takeLast(40), workspace.getString("location"), 1, stories, current,
            workspace.getJSONArray("stories").let { rows -> (0 until rows.length()).map { rows.getJSONObject(it) }
                .first { sameScope(it.getJSONObject("scope"), checkNotNull(scope)) }.optInt("drafts", 0) },
            view.getString("rules"))
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
        val pending = Pending(checkNotNull(session), checkNotNull(scope), request.getString("turn"), request, mode, ++serial)
        operation = pending // Keep the original key even if submit acknowledgement is lost.
        try {
            val submitted = call(command("submit").put("session", pending.session).put("request", request)
                .put("mode", mode.name.lowercase(java.util.Locale.ROOT)))
            if (pending.cancelled) return DemoResult.Rejected("Cancelled")
            val prepared = if (submitted.getString("phase") == "queued") call(scoped("prepare", pending)) else submitted
            return result(prepared, pending)
        } catch (failure: WorkspaceFailure) {
            // An explicit rejection before acceptance cannot create canon; transport uncertainty stays pending.
            if (failure.category in setOf("Full", "Database", "Integrity", "Io", "Internal")) throw failure
            if (operation === pending) operation = null
            return DemoResult.Rejected(failure.category)
        }
    }
    private fun result(data: JSONObject, pending: Pending): DemoResult {
        check(data.getString("turn") == pending.turn && sameScope(data.getJSONObject("scope"), pending.scope))
        check(data.getLong("expected_revision") == pending.request.getLong("expected_revision"))
        return when (data.getString("phase")) {
        "ready" -> DemoResult.Prepared(0, pending.serial)
        "committed" -> {
            val receipt = data.getJSONObject("receipt")
            check(sameJson(receipt.getJSONObject("request"), pending.request))
            if (operation === pending) operation = null
            DemoResult.Accepted(pending.request.getLong("expected_revision") + 1, "", receipt.getString("narration"))
        }
        "cancelled", "failed", "stale" -> {
            if (operation === pending) operation = null
            DemoResult.Rejected(data.optString("error").takeUnless { it.isBlank() || it == "null" } ?: "Cancelled")
        }
        else -> error("Unfinished")
        }
    }
    override suspend fun commitAsync(result: DemoResult): DemoResult {
        if (result !is DemoResult.Prepared) return result
        val pending = checkNotNull(operation)
        if (pending.cancelled || result.operation != pending.serial) return DemoResult.Rejected("Cancelled")
        val data = try { call(scoped("commit", pending)) }
            catch (failure: Exception) {
                // The original key is the only authority after a lost commit acknowledgement.
                try { call(scoped("turn_status", pending)) } catch (_: Exception) { throw failure }
            }
        return this.result(data, pending)
    }
    override suspend fun recoverSaved(): SavedSnapshot {
        if (session == null) return initialize()
        operation?.let { pending ->
            if (pending.cancelled) {
                try { result(call(scoped("cancel", pending)), pending) }
                catch (failure: WorkspaceFailure) {
                    if (failure.category != "UnknownTurn") throw failure
                    if (operation === pending) operation = null
                }
                return snapshot()
            }
            var status = try { call(scoped("turn_status", pending)) }
                catch (failure: WorkspaceFailure) {
                    if (failure.category != "UnknownTurn") throw failure
                    call(command("submit").put("session", pending.session).put("request", pending.request)
                        .put("mode", pending.mode.name.lowercase(java.util.Locale.ROOT)))
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
            val status = call(scoped("cancel", pending))
            if (status.getString("phase") == "committed") result(status, pending)
            else if (operation === pending) operation = null
        }
        return snapshot()
    }
    private suspend fun release() {
        cancelSaved()
        call(scoped("close"))
        session = null; scope = null
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
