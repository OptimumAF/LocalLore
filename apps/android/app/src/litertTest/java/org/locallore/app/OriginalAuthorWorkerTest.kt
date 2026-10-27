/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.File
import java.security.MessageDigest
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Injected SDK-neutral resources and four synthetic bytes, never a real model or device. */
class OriginalAuthorWorkerTest {
    @get:Rule val temporary=TemporaryFolder()
    private val request=LocalInferenceRequest(1,"author","Synthetic author input",1024,4096,4,"{\"type\":\"object\"}")
    private fun config(): LiteRtWorkerConfig {
        val root=temporary.newFolder(); val model=File(root,"synthetic.litertlm").also { it.writeBytes(byteArrayOf(1,2,3,4)) }
        val cache=File(root,"cache").also { check(it.mkdir()) }
        val hash=MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
        return LiteRtWorkerConfig(root,model,cache,4,hash,"a".repeat(64),"b".repeat(64),"c".repeat(64))
    }
    private class Resource(private val output: String): LiteRtEngineResource {
        var parentCloses=0; var conversationCloses=0; lateinit var captured: LocalInferenceRequest
        override fun initialize() {}
        override fun conversation(request: LocalInferenceRequest): LiteRtConversationResource {
            captured=request
            return object: LiteRtConversationResource {
                override fun send(request: LocalInferenceRequest,callbacks: LiteRtCallbacks) {
                    callbacks.message { LiteRtChunk(text=listOf(output)) }; callbacks.done()
                }
                override fun cancel() {}
                override fun close(): Boolean { conversationCloses++; return true }
            }
        }
        override fun close(): Boolean { parentCloses++; return true }
    }
    @Test fun authorHasItsOwnBudgetAndAccurateWorkerAndCallbackLabels()=runBlocking {
        val resource=Resource("x".repeat(8192)); val trace=LiteRtWorkerTrace(); val callbacks=LiteRtCallbackTrace()
        val worker=LiteRtRoleWorker(config(),LiteRtResources { resource },trace,callbacks)
        val engine=worker.open(); val call=engine.start(request)
        assertEquals(8192,call.await().response().size); assertTrue(call.drain()); assertTrue(call.close()); assertTrue(engine.close())
        assertEquals(request,resource.captured); assertEquals(1,resource.conversationCloses); assertEquals(1,resource.parentCloses)
        assertEquals(LiteRtTraceRole.AUTHOR,trace.snapshot().creations.single().role)
        val observed=callbacks.snapshot().calls.single(); assertEquals(LiteRtCallbackRole.AUTHOR,observed.role)
        assertEquals(1024,observed.maxOutputTokens); assertEquals(8192,observed.counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES))
        assertTrue(callbacks.snapshot().json().contains("\"role\":\"AUTHOR\""))
    }
    @Test fun oversizedAuthorOutputRetainsUnknownParentInsteadOfClosingIt()=runBlocking {
        val resource=Resource("x".repeat(8193)); var uncertain=0
        val worker=LiteRtRoleWorker(config(),LiteRtResources { resource },onUncertain={uncertain++})
        val engine=worker.open(); val call=engine.start(request)
        try { call.await(); fail("Oversized author response accepted") } catch (_: LocalInferenceUncertain) {}
        assertFalse(call.drain()); assertFalse(engine.close()); assertEquals(0,resource.parentCloses); assertEquals(0,resource.conversationCloses)
        assertTrue(uncertain>0)
    }
    @Test fun authorDoesNotWidenPlayConfigOrPassiveMetadataCaps() {
        val config=config(); config.validateRequest(request)
        for(bad in listOf(request.copy(maxTokens=1025),request.copy(role="director",maxTokens=351),request.copy(role="narrator",maxTokens=221))) {
            try { config.validateRequest(bad); fail("Role budget widened") } catch (_: IllegalStateException) {}
        }
        val profile=config.profileBytes().toString(Charsets.UTF_8)
        assertTrue(profile.contains("\"director_tokens\":350")); assertTrue(profile.contains("\"narrator_tokens\":220")); assertFalse(profile.contains("author_tokens"))
        val trace=LiteRtCallbackTrace(); trace.begin(LiteRtCallbackRole.AUTHOR,4096,1024,10,2)
        try { trace.begin(LiteRtCallbackRole.NARRATOR,4096,1024,10,2); fail() } catch (_: IllegalArgumentException) {}
        assertEquals(1,trace.snapshot().requests)
    }
}
