/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Test

/** Ownership/copying controls only; no SDK, native domain validation or model-quality claim. */
class OriginalAuthorOwnerTest {
    private val request=LocalInferenceRequest(1,"author","Synthetic initial world input",1024,4096,4,"{}")
    private class Port(request: LocalInferenceRequest): LocalInferenceNativePort {
        val pending=AtomicReference<LocalInferencePending?>(LocalInferencePending(1,request))
        val terminal=CountDownLatch(1); val deliveries=AtomicInteger(); val cancellations=AtomicInteger()
        var repeat=false; var accepted: ByteArray?=null
        override fun call(input: ByteArray): ByteArray=when(input.toString(Charsets.UTF_8)) {
            "generate" -> { check(terminal.await(3,TimeUnit.SECONDS)); "draft".toByteArray() }
            "cancel-job" -> { cancellations.incrementAndGet(); pending.set(null); terminal.countDown(); "cancelled".toByteArray() }
            else -> "read".toByteArray()
        }
        override fun poll()=pending.get()
        override fun respond(ticket: Long,response: ByteArray): Boolean {
            check(ticket==1L); deliveries.incrementAndGet(); accepted=response.copyOf()
            if(!repeat) { pending.set(null); terminal.countDown() }; return true
        }
        override fun close() { pending.set(null); terminal.countDown() }
    }
    private class Call: LocalRoleCall {
        val entered=CompletableDeferred<Unit>(); val response=CompletableDeferred<LocalRoleResult>()
        val drains=AtomicInteger(); val closes=AtomicInteger()
        override suspend fun await(): LocalRoleResult { entered.complete(Unit); return response.await() }
        override fun cancel() { response.complete(LocalRoleResult(true,byteArrayOf())) }
        override suspend fun drain(): Boolean { drains.incrementAndGet(); return true }
        override suspend fun close(): Boolean { closes.incrementAndGet(); return true }
    }
    private class Engine(val call: Call): LocalRoleEngine {
        val closeGate=CompletableDeferred<Boolean>().also { it.complete(true) }
        val closed=AtomicInteger()
        override suspend fun start(request: LocalInferenceRequest)=call
        override suspend fun close(): Boolean { closed.incrementAndGet(); return closeGate.await() }
    }
    private fun owner(engine: LocalRoleEngine)=LocalInferenceOwner("{}".toByteArray(),LocalRoleWorker { engine },Dispatchers.Default,
        LocalInferenceLimits(turnMs=1000,cleanupMs=1000,pollMs=2,authorMs=2000))
    private suspend fun generate(owner: LocalInferenceOwner,port: Port)=owner.execute(port,"authoring_generate","generate".toByteArray(),"cancel-job".toByteArray())
    @Test fun authorCapIsSeparateAndPlayRolesKeepTheirOldLimits() {
        request.validate(); request.copy(maxTokens=1).validate()
        for(bad in listOf(request.copy(maxTokens=1025),request.copy(role="director",maxTokens=351),request.copy(role="narrator",maxTokens=351),request.copy(role="other"))) {
            try { bad.validate(); fail("Role budget widened") } catch (_: IllegalStateException) {}
        }
        try { LocalInferenceLimits(turnMs=60001); fail() } catch (_: IllegalArgumentException) {}
        try { LocalInferenceLimits(authorMs=120001); fail() } catch (_: IllegalArgumentException) {}
        assertEquals(120000L,LocalInferenceLimits().authorMs)
    }
    @Test fun oneAuthorDeliveryAcceptsExactBoundAndReleasesRoleBeforeReturning()=runBlocking {
        val call=Call(); val engine=Engine(call); val port=Port(request); val owner=owner(engine)
        val bytes="x".repeat(8192).toByteArray(); val result=LocalRoleResult(true,bytes); bytes.fill(0)
        call.response.complete(result)
        assertEquals("draft",generate(owner,port).toString(Charsets.UTF_8))
        assertEquals(8192,port.accepted!!.size); assertEquals('x'.code.toByte(),port.accepted!![0])
        assertEquals(1,port.deliveries.get()); assertEquals(1,call.drains.get()); assertEquals(1,call.closes.get()); assertEquals(1,engine.closed.get())
        assertFalse(owner.quarantined); owner.close()
    }
    @Test fun authorOverflowAndForeignPlayRequestQuarantineWithoutDelivery()=runBlocking {
        for(pair in listOf(request to 8193,request.copy(role="director",maxTokens=350) to 2)) {
            val call=Call(); call.response.complete(LocalRoleResult(true,"x".repeat(pair.second).toByteArray()))
            val port=Port(pair.first); val owner=owner(Engine(call))
            try { generate(owner,port); fail("Invalid author response/request admitted") } catch (_: LocalInferenceUncertain) {}
            assertTrue(owner.quarantined); assertEquals(0,port.deliveries.get()); owner.close()
        }
    }
    @Test fun authorHasNoSecondDeliveryOrRepair()=runBlocking {
        val call=Call(); call.response.complete(LocalRoleResult(true,"{}".toByteArray()))
        val port=Port(request).also { it.repeat=true }; val owner=owner(Engine(call))
        try { generate(owner,port); fail("Author repeated") } catch (_: LocalInferenceUncertain) {}
        assertEquals(1,port.deliveries.get()); assertTrue(owner.quarantined); assertTrue(port.cancellations.get()>0); owner.close()
    }
    @Test fun authorCancellationWaitsForOwnedEngineClose()=runBlocking {
        val call=Call(); val gate=CompletableDeferred<Boolean>()
        val engine=object: LocalRoleEngine {
            override suspend fun start(request: LocalInferenceRequest)=call
            override suspend fun close(): Boolean=gate.await()
        }
        val port=Port(request); val owner=owner(engine)
        val generation=async { generate(owner,port) }; call.entered.await()
        val cancel=async { owner.execute(port,"authoring_cancel","cancel-job".toByteArray()) }
        withTimeout(2000) { while(call.closes.get()==0)delay(2) }
        assertFalse(cancel.isCompleted); assertFalse(generation.isCompleted); assertEquals(0,port.deliveries.get())
        gate.complete(true); generation.await(); cancel.await(); assertFalse(owner.quarantined); owner.close()
    }
}
