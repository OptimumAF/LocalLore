/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*

/** Deferred synthetic transport cases called by the existing wire test; no extra SDK test selector. */
internal object OriginalPlayerTransportCases {
    private class Barrier {
        val entered=CompletableDeferred<Unit>()
        val release=CompletableDeferred<Unit>()
        suspend fun pause() { entered.complete(Unit); release.await() }
    }
    private class Port(private val observers: List<String>,private val barriers: Map<Int,Barrier>): WorkspaceTransport {
        // Deliberately return this SAME object on every attachment, with the SAME session text/head.
        val sharedScope=JSONObject().put("story","original-binding-fixture").put("branch","main")
        private val lock=Any()
        private var views=0
        private val postView=mutableMapOf<Job,Int>()
        private val attachments=mutableListOf<JSONObject>()
        fun attachedScopes(): List<JSONObject> = synchronized(lock) { attachments.toList() }
        private fun ok(data: JSONObject)=JSONObject().put("version",1).put("status","ok").put("data",data)
        private fun row()=JSONObject().put("scope",sharedScope).put("title","Synthetic binding fixture").put("revision",0).put("drafts",0)
        override suspend fun exchange(command: JSONObject): JSONObject {
            val job=checkNotNull(currentCoroutineContext()[Job])
            return when(command.getString("op")) {
                "workspace" -> {
                    val observed=synchronized(lock) { postView.remove(job) }
                    observed?.let { barriers[it]?.pause() }
                    ok(JSONObject().put("persistent",true).put("location","synthetic transport only").put("schema_version",1)
                        .put("database_schema_version",5).put("stories",JSONArray().put(row())))
                }
                "branches" -> ok(JSONObject().put("version",2).put("story_id","original-binding-fixture").put("title","Synthetic binding fixture")
                    .put("root_branch","main").put("branches",JSONArray().put(JSONObject().put("scope",sharedScope)
                        .put("parent_branch",JSONObject.NULL).put("fork_revision",JSONObject.NULL).put("revision",0).put("drafts",0).put("retired",false))))
                "resume" -> {
                    synchronized(lock) { attachments+=sharedScope }
                    ok(JSONObject().put("session","reused-session").put("scope",sharedScope).put("revision",0))
                }
                "open" -> ok(JSONObject().put("session","reused-session").put("scope",sharedScope).put("revision",0))
                "play_snapshot" -> {
                    val ordinal=synchronized(lock) { (++views).also { postView[job]=it } }
                    val observer=observers.getOrElse(ordinal-1) { observers.last() }
                    ok(JSONObject().put("scope",sharedScope).put("revision",0).put("rules","narrative_v1").put("inventory",JSONObject())
                        .put("receipts",JSONArray()).put("player",JSONObject().put("scope",sharedScope).put("revision",0).put("observer",observer)))
                }
                "capabilities" -> ok(JSONObject().put("free_text",false))
                "close" -> ok(JSONObject().put("closed",true))
                else -> throw AssertionError("Unexpected command in bounded player-binding transport case")
            }
        }
        override fun close() {}
    }
    private fun stale(result: Result<SavedSnapshot>) {
        val failure=result.exceptionOrNull()
        assertTrue("An obsolete or conflicting snapshot was published",failure is WorkspaceFailure)
        assertEquals("Stale",(failure as WorkspaceFailure).category)
    }
    suspend fun verify() {
        withTimeout(5000) { reusedAttachmentCannotPublish() }
        withTimeout(5000) { overlappingViewsCannotRetarget() }
    }
    private suspend fun reusedAttachmentCannotPublish()=coroutineScope {
        val oldBarrier=Barrier()
        val port=Port(listOf("a-old-player","a-current-player","a-current-player"),mapOf(1 to oldBarrier))
        val gateway=DurableGateway(port,autoCreateIfEmpty=false)
        try {
            val old=async { runCatching { gateway.initialize() } }
            oldBarrier.entered.await() // Old read has decoded its player view but cannot publish yet.
            val current=gateway.reconcileSaved()
            val selected=checkNotNull(current.selected)
            val live=checkNotNull(gateway.forkContext(selected,0,7))
            val scopes=port.attachedScopes(); assertEquals(2,scopes.size)
            assertSame(port.sharedScope,scopes[0]); assertSame(scopes[0],scopes[1])
            assertEquals("reused-session",live.session)
            oldBarrier.release.complete(Unit)
            stale(old.await())
            assertEquals(live,gateway.forkContext(selected,0,7))
            assertEquals(selected,gateway.snapshot().selected) // The new player's binding was not replaced by the old result.
        } finally { oldBarrier.release.complete(Unit); gateway.close() }
    }
    private suspend fun overlappingViewsCannotRetarget()=coroutineScope {
        val firstBarrier=Barrier(); val conflictingBarrier=Barrier()
        val port=Port(listOf("a-current-player","a-foreign-player","a-current-player"),mapOf(1 to firstBarrier,2 to conflictingBarrier))
        val gateway=DurableGateway(port,autoCreateIfEmpty=false)
        try {
            val first=async { runCatching { gateway.initialize() } }
            firstBarrier.entered.await()
            val conflicting=async { runCatching { gateway.snapshot() } }
            conflictingBarrier.entered.await() // Both reads observed an unbound player before their independent post-view barriers.
            firstBarrier.release.complete(Unit)
            val accepted=first.await().getOrThrow(); val selected=checkNotNull(accepted.selected)
            val live=checkNotNull(gateway.forkContext(selected,0,9))
            assertEquals(1,port.attachedScopes().size) // Same attachment, not a reset that could hide the conflict.
            conflictingBarrier.release.complete(Unit)
            stale(conflicting.await())
            assertEquals(live,gateway.forkContext(selected,0,9))
            assertEquals(selected,gateway.snapshot().selected) // Re-read of the accepted observer still succeeds.
        } finally {
            firstBarrier.release.complete(Unit); conflictingBarrier.release.complete(Unit); gateway.close()
        }
    }
}
