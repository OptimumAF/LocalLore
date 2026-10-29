/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class OriginalStoryWireTest {
    private fun input()=OriginalInput("SYNTHETIC Iris explores a clockwork orchard.","SYNTHETIC Iris","A careful visitor.",
        listOf(OriginalCast("Sel","An orchard keeper.")),"narrative_v1",StoryPresentation("warm",listOf("spider")))
    private fun proposal()=OriginalProposal(listOf(OriginalLocation("Orchard","A frost-covered orchard.")),0,
        listOf(OriginalCharacter("Sel","An orchard keeper.",0,listOf(0,1))),emptyList(),listOf(OriginalFact("The gate is shut.",listOf(0),0)),
        listOf(OriginalBelief(1,"The clock is slow.","suspected")),listOf(OriginalPossession("Token","An unmarked token.",0,null)))
    private fun malformed(action: ()->Unit) { try { action(); fail("Malformed author metadata accepted") }
        catch(e: WorkspaceFailure) { assertEquals("Malformed",e.category) } }
    @Test fun strictAuthorInputAndProposalRejectForeignFieldsAndBounds() {
        val i=OriginalStoryWire.input(input()); assertEquals(input(),OriginalStoryWire.input(i))
        val p=OriginalStoryWire.proposal(proposal()); assertEquals(proposal(),OriginalStoryWire.proposal(p))
        for(key in i.keys().asSequence().toList()) {
            malformed { OriginalStoryWire.input(JSONObject(i.toString()).also { it.remove(key) }) }
            malformed { OriginalStoryWire.input(JSONObject(i.toString()).put(key,JSONObject.NULL)) }
        }
        for(key in p.keys().asSequence().toList()) malformed { OriginalStoryWire.proposal(JSONObject(p.toString()).also { it.remove(key) }) }
        malformed { OriginalStoryWire.input(JSONObject(i.toString()).put("seed",JSONObject())) }
        malformed { OriginalStoryWire.proposal(JSONObject(p.toString()).put("abilities",JSONArray())) }
        for(bad in listOf<Any>(1.0,"1",true,2)) malformed { OriginalStoryWire.input(JSONObject(i.toString()).put("version",bad)) }
        for(bad in listOf("", " outer", "line\nbreak", "\uD800","a".repeat(1025))) malformed {
            OriginalStoryWire.input(JSONObject(i.toString()).put("premise",bad)) }
        malformed { OriginalStoryWire.proposal(JSONObject(p.toString()).put("player_location",1)) }
        malformed { OriginalStoryWire.proposal(JSONObject(p.toString()).also { it.getJSONArray("characters").getJSONObject(0).put("known_by",JSONArray().put(0).put(0)) }) }
        malformed { OriginalStoryWire.proposal(JSONObject(p.toString()).also { it.getJSONArray("beliefs").getJSONObject(0).put("confidence","true") }) }
        malformed { OriginalStoryWire.proposal(JSONObject(p.toString()).also { it.getJSONArray("facts").getJSONObject(0).put("discoverable_at",false) }) }
        val decoded=OriginalStoryWire.proposal(p); p.getJSONArray("characters").getJSONObject(0).put("name","Foreign")
        assertEquals("Sel",decoded.characters.single().name)
        try { (decoded.characters.single().knownBy as MutableList<*>).clear(); fail("Mutable native metadata") } catch (_: UnsupportedOperationException) {}
        assertFalse(OriginalStoryWire.cancelled(JSONObject().put("cancelled",false)))
        malformed { OriginalStoryWire.job(JSONObject().put("job","j".repeat(33)).put("input_sha256","a".repeat(64)).put("provider","scripted")) }
        malformed { OriginalStoryWire.capabilities(JSONObject().put("available",true).put("provider","cloud").put("max_tokens",1024)) }
        malformed { OriginalStoryWire.capabilities(JSONObject().put("available",true).put("provider",JSONObject.NULL).put("max_tokens",1024)) }
    }
    private class Host(val database: File): WorkspaceTransport, AutoCloseable {
        private var handle=NativeWorkspace.open(database.absolutePath).also { check(it>0) }
        override suspend fun exchange(command: JSONObject): JSONObject {
            check(handle>0)
            val bytes=JSONObject().put("version",1).put("command",command).toString().toByteArray(Charsets.UTF_8); check(bytes.size<=24576)
            val raw=NativeWorkspace.call(handle,bytes); check(raw.size in 1..262144)
            val root=JSONObject(raw.toString(Charsets.UTF_8)); assertEquals(1,root.getInt("version"))
            return root
        }
        suspend fun data(op: String, configure: (JSONObject)->Unit={}): JSONObject {
            val command=JSONObject().put("op",op); configure(command)
            val root=exchange(command)
            assertEquals("Native $op error=${root.optString("error").take(64)}","ok",root.opt("status"))
            return root.getJSONObject("data")
        }
        override fun close() { val old=handle; handle=0; if(old>0)NativeWorkspace.close(old) }
    }
    private fun database(): File {
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("org.locallore.app.draftprocessverify",context.packageName); assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
        val root=File(context.cacheDir,"original-wire-${UUID.randomUUID()}"); check(root.mkdir())
        return File(root,"stories.sqlite3")
    }
    private suspend fun review(host: Host): OriginalReview {
        val input=input(); val job=OriginalStoryWire.job(host.data("authoring_begin") { it.put("input",OriginalStoryWire.input(input)) })
        assertEquals("scripted",job.provider)
        val generated=OriginalStoryWire.generated(host.data("authoring_generate") { it.put("job",job.job) })
        assertEquals(job.job,generated.job); assertEquals(input,generated.input); assertEquals("scripted",generated.provider)
        return OriginalStoryWire.review(host.data("authoring_review") { it.put("job",job.job).put("input",OriginalStoryWire.input(input))
            .put("proposal",OriginalStoryWire.proposal(generated.proposal)).put("title","SYNTHETIC reviewed orchard") })
    }
    @Test fun nativeAuthoringReadsNeverCreateAndCancelKeepsLibrary()=runBlocking(Dispatchers.IO) {
        Host(database()).use { host ->
            val before=host.data("workspace").toString()
            assertEquals(OriginalCapabilities(true,"scripted"),OriginalStoryWire.capabilities(host.data("authoring_capabilities")))
            val review=review(host); assertEquals(before,host.data("workspace").toString())
            val status=host.data("authoring_status") { it.put("job",review.job) }
            assertEquals(setOf("job","phase","error"),status.keys().asSequence().toSet())
            assertEquals("reviewed",status.getString("phase")); assertTrue(status.isNull("error"))
            assertTrue(OriginalStoryWire.cancelled(host.data("authoring_cancel") { it.put("job",review.job) }))
            assertEquals("cancelled",host.data("authoring_status") { it.put("job",review.job) }.getString("phase"))
            assertEquals(before,host.data("workspace").toString())
        }
    }
    @Test fun nativeReviewedCreateRetriesAfterReopenWithoutGeneration()=runBlocking(Dispatchers.IO) {
        val file=database(); val id=UUID.randomUUID().toString().replace("-",""); lateinit var review: OriginalReview
        lateinit var scope: JSONObject; lateinit var player: String
        Host(file).use { host ->
            review=review(host)
            val result=host.data("authoring_create") { it.put("job",review.job).put("review_sha256",review.reviewSha256).put("creation_id",id) }
            assertEquals(setOf("session","scope","revision","created"),result.keys().asSequence().toSet())
            assertTrue(result.getBoolean("created")); assertEquals(0L,result.getLong("revision")); scope=result.getJSONObject("scope")
            assertEquals("original-$id",scope.getString("story")); assertEquals("main",scope.getString("branch"))
            assertFalse(OriginalStoryWire.cancelled(host.data("authoring_cancel") { it.put("job",review.job) }))
            player=host.data("play_snapshot") { it.put("session",result.getString("session")).put("scope",scope).put("expected_revision",0) }.toString()
        }
        Host(file).use { host ->
            // No begin/generate/review occurs in this fresh process-local Host.
            val retry=host.data("authoring_create") { it.put("job",review.job).put("review_sha256",review.reviewSha256).put("creation_id",id) }
            assertFalse(retry.getBoolean("created")); assertEquals(scope.toString(),retry.getJSONObject("scope").toString())
            assertEquals(player,host.data("play_snapshot") { it.put("session",retry.getString("session")).put("scope",scope).put("expected_revision",0) }.toString())
            assertEquals(1,host.data("workspace").getJSONArray("stories").length())
        }
        Host(file).use { host ->
            val observer=JSONObject(player).getJSONObject("player").getString("observer")
            assertNotEquals("player",observer) // Original-world IDs are assigned by Rust, not the bundled fixture.
            var corruptObserver=false
            val port=object: WorkspaceTransport {
                override suspend fun exchange(command: JSONObject): JSONObject=host.exchange(command).also {
                    // Negative adapter test only: the unmodified JNI result above remains authoritative.
                    if(corruptObserver && command.optString("op")=="play_snapshot" && it.optString("status")=="ok")
                        it.getJSONObject("data").getJSONObject("player").put("observer","foreign-observer")
                }
                override fun close()=host.close()
            }
            val gateway=DurableGateway(port,autoCreateIfEmpty=false,initialScopeHint=PlayDraftScope("original-$id","main"))
            try {
                val saved=gateway.initialize()
                val selected=checkNotNull(saved.selected)
                assertEquals("original-$id",selected.story); assertEquals("main",selected.branch)
                assertEquals(review.title,selected.title); assertEquals(0L,saved.revision)
                assertEquals("narrative_v1",saved.rulesProfile); assertEquals(5,saved.databaseSchemaVersion)
                assertEquals(saved.selected,gateway.recoverSaved().selected)
                corruptObserver=true
                try { gateway.snapshot(); fail("An established native player binding was retargeted") }
                catch(e: WorkspaceFailure) { assertEquals("Stale",e.category) }
                assertNull(gateway.forkContext(selected,0,1)) // A refused snapshot cannot lend a coherent player view.
                corruptObserver=false
                val recovered=gateway.recoverSaved(); assertEquals(saved.selected,recovered.selected)
                // These are semantic player lenses, independent of the engine's actual actor ID.
                assertEquals("player",gateway.forkContext(recovered.selected!!,0,2)!!.observer)
                val legacy=gateway.createSaved()
                assertNotEquals(selected.story,legacy.selected!!.story)
                assertEquals("fantasy_v1",legacy.rulesProfile)
                // A fresh explicit attachment must not reuse the prior story's opaque observer binding.
                val returned=gateway.resumeSaved(selected)
                assertEquals(selected,returned.selected); assertEquals(0L,returned.revision)
                assertEquals("narrative_v1",returned.rulesProfile)
            } finally { gateway.close() }
        }
        OriginalPlayerTransportCases.verify()
    }
}
