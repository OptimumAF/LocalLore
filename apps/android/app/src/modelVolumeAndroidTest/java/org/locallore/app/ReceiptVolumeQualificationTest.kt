/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.IBinder
import android.os.Parcel
import android.os.Process
import android.os.SystemClock
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.coroutines.coroutineContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test
import org.locallore.app.ReceiptAndroidFixture.Case
import org.locallore.app.ReceiptAndroidFixture.Phase

/** Real Android files and one same-UID owned child; no runtime or native publication. */
@SdkSuppress(minSdkVersion = 30)
class ReceiptVolumeQualificationTest {
    @Test fun acceptsAndReopensReceipt() = runBlocking {
        withContext(Dispatchers.IO) {
            val env = ReceiptAndroidFixture.open(context())
            env.fresh(Case.ACCEPT)
            val source = ReceiptAndroidFixture.Source()
            env.transaction(Case.ACCEPT).import(source::open)
            assertEquals(1, source.opened.get()); assertEquals(1, source.closed.get())
            env.assertRecords(Case.ACCEPT, accepted = true)
            val before = env.snapshot(Case.ACCEPT)
            val unexpected = ReceiptAndroidFixture.Source()
            assertNotNull(env.transaction(Case.ACCEPT).installed())
            env.transaction(Case.ACCEPT).import(unexpected::open)
            assertEquals(0, unexpected.opened.get())
            expect(LocalModelFailure.UNSAFE_PATH) { env.transaction(Case.ACCEPT).discardUncommitted() }
            assertEquals(before, env.snapshot(Case.ACCEPT))
            env.proof(Phase.ACCEPT, passed(Phase.ACCEPT))
        }
    }

    @Test fun cancelsAcrossAcceptanceBoundary() = runBlocking {
        withContext(Dispatchers.IO) {
            val env = ReceiptAndroidFixture.open(context())
            env.fresh(Case.CANCEL_BEFORE, Case.CANCEL_AFTER)
            val before = selfCancel(env, Case.CANCEL_BEFORE, ReceiptCheckpoint.BEFORE_COMMIT)
            assertTrue(before)
            env.assertRecords(Case.CANCEL_BEFORE, accepted = false)
            assertNull(env.transaction(Case.CANCEL_BEFORE).installed())
            val after = selfCancel(env, Case.CANCEL_AFTER, ReceiptCheckpoint.AFTER_COMMIT)
            assertTrue(after)
            env.assertRecords(Case.CANCEL_AFTER, accepted = true)
            val unexpected = ReceiptAndroidFixture.Source()
            env.transaction(Case.CANCEL_AFTER).import(unexpected::open)
            assertNotNull(env.transaction(Case.CANCEL_AFTER).installed())
            assertEquals(0, unexpected.opened.get())
            env.proof(Phase.CANCELLATION, passed(Phase.CANCELLATION))
        }
    }

    @Test fun refusesForeignAndUncommittedData() = runBlocking {
        withContext(Dispatchers.IO) {
            val env = ReceiptAndroidFixture.open(context())
            env.fresh(Case.PARTIAL, Case.FOREIGN, Case.FOREIGN_CONTROL, Case.GUARD)
            val partialBytes = ReceiptAndroidFixture.bytes.copyOf(17)
            val partial = ReceiptAndroidFixture.Source(partialBytes)
            expect(LocalModelFailure.INVALID_MODEL) { env.transaction(Case.PARTIAL).import(partial::open) }
            assertEquals(1, partial.closed.get())
            env.assertRecords(Case.PARTIAL, accepted = false, modelBytes = partialBytes)
            assertNull(env.transaction(Case.PARTIAL).installed())
            env.transaction(Case.PARTIAL).discardUncommitted()
            env.assertDiscarded(Case.PARTIAL)
            val retry = ReceiptAndroidFixture.Source()
            env.transaction(Case.PARTIAL).import(retry::open)
            assertEquals(1, retry.opened.get()); assertEquals(1, retry.closed.get())
            env.assertRecords(Case.PARTIAL, accepted = true)

            // Prepare B's receipt while the common data directory is still absent.
            val otherReached = AtomicBoolean()
            val otherSource = ReceiptAndroidFixture.Source()
            expectCheckpointCancellation {
                env.transaction(Case.FOREIGN_CONTROL, checkpoint = {
                    if (it == ReceiptCheckpoint.RECEIPT_FORCED) {
                        otherReached.set(true)
                        throw CancellationException("Receipt fixture stop")
                    }
                }).import(otherSource::open)
            }
            assertTrue(otherReached.get()); assertEquals(0, otherSource.opened.get())
            env.assertReceiptOnly(Case.FOREIGN_CONTROL)
            val ownerSource = ReceiptAndroidFixture.Source()
            expectCheckpointCancellation {
                env.transaction(Case.FOREIGN, checkpoint = {
                    if (it == ReceiptCheckpoint.DATA_FORCED) throw CancellationException("Receipt fixture stop")
                }).import(ownerSource::open)
            }
            assertEquals(1, ownerSource.closed.get())
            env.assertRecords(Case.FOREIGN, accepted = false)
            val beforeForeign = env.snapshot(Case.FOREIGN)
            val beforeOther = env.snapshot(Case.FOREIGN_CONTROL)
            val unopened = ReceiptAndroidFixture.Source()
            expect(LocalModelFailure.UNSAFE_PATH) { env.transaction(Case.FOREIGN_CONTROL).import(unopened::open) }
            assertEquals(0, unopened.opened.get())
            expect(LocalModelFailure.UNSAFE_PATH) { env.transaction(Case.FOREIGN_CONTROL).discardUncommitted() }
            assertEquals(beforeForeign, env.snapshot(Case.FOREIGN))
            assertEquals(beforeOther, env.snapshot(Case.FOREIGN_CONTROL))
            env.addUnknown(Case.FOREIGN)
            val withUnknown = env.snapshot(Case.FOREIGN)
            expect(LocalModelFailure.UNSAFE_PATH) { env.transaction(Case.FOREIGN).discardUncommitted() }
            assertEquals(withUnknown, env.snapshot(Case.FOREIGN))

            val revoked = AtomicBoolean()
            val guardSource = ReceiptAndroidFixture.Source()
            val guarded = env.transaction(Case.GUARD, revoked = revoked::get, checkpoint = {
                if (it == ReceiptCheckpoint.RECEIPT_FORCED) revoked.set(true)
            })
            expect(LocalModelFailure.STORAGE) { guarded.import(guardSource::open) }
            assertTrue(revoked.get()); assertEquals(0, guardSource.opened.get())
            env.assertReceiptOnly(Case.GUARD)
            val guardBefore = env.snapshot(Case.GUARD)
            expect(LocalModelFailure.STORAGE) { guarded.discardUncommitted() }
            assertEquals(guardBefore, env.snapshot(Case.GUARD))
            env.proof(Phase.REFUSAL, passed(Phase.REFUSAL))
        }
    }

    @Test fun recoversAfterOwnedProcessDeath() = runBlocking {
        withContext(Dispatchers.IO) {
            val context = context()
            val env = ReceiptAndroidFixture.open(context)
            env.fresh(Case.PROCESS)
            val connection = ProofConnection()
            val intent = Intent().setComponent(ComponentName(context, ReceiptProofService::class.java))
            var attempted = false
            var registered = false
            var released = false
            var linked = false
            var endpoint: IBinder? = null
            val death = CountDownLatch(1)
            val deathCount = AtomicInteger()
            val recipient = IBinder.DeathRecipient { deathCount.incrementAndGet(); death.countDown() }
            var primaryFailure: Throwable? = null
            try {
                attempted = true
                registered = context.bindService(intent, connection, Context.BIND_AUTO_CREATE)
                assertTrue(registered)
                assertTrue(connection.connected.await(10, TimeUnit.SECONDS))
                check(!connection.failed.get())
                val binder = requireNotNull(connection.endpoint.get())
                endpoint = binder
                binder.linkToDeath(recipient, 0); linked = true
                val childStarted = SystemClock.elapsedRealtime()
                ack(binder, ReceiptProofService.START)
                val child = waitHeld(binder, connection)
                assertTrue(child.pid != Process.myPid() && child.start > 0)
                assertEquals(Process.myUid(), child.uid)
                env.assertRecords(Case.PROCESS, accepted = false)
                val pending = env.snapshot(Case.PROCESS)
                val unopened = ReceiptAndroidFixture.Source()
                val transaction = env.transaction(Case.PROCESS)
                expect(LocalModelFailure.BUSY) { transaction.installed() }
                expect(LocalModelFailure.BUSY) { transaction.import(unopened::open) }
                expect(LocalModelFailure.BUSY) { transaction.discardUncommitted() }
                assertEquals(0, unopened.opened.get())
                assertEquals(pending, env.snapshot(Case.PROCESS))
                assertEquals(child, snapshot(binder).also { check(it.state == ReceiptProofService.State.DATA_FORCED) }.child)
                check(!connection.failed.get() && connection.connections.get() == 1)
                val haltStarted = SystemClock.elapsedRealtime()
                ack(binder, ReceiptProofService.HALT)
                connection.releasing.set(true)
                context.unbindService(connection); released = true
                assertTrue(death.await(5, TimeUnit.SECONDS))
                assertTrue(SystemClock.elapsedRealtime() - haltStarted < 5_000)
                // Timer precedes START; DATA_FORCED's later 30s timeout cannot have
                // returned and released the lock before this accepted hard death.
                assertTrue(SystemClock.elapsedRealtime() - childStarted < 25_000)
                assertEquals(1, deathCount.get())
                context.stopService(intent) // Fixed, idempotent cleanup after actual captured death.
                assertEquals(pending, env.snapshot(Case.PROCESS))
                val resumeSource = ReceiptAndroidFixture.Source()
                val deadline = SystemClock.elapsedRealtime() + 5_000
                while (true) {
                    try {
                        transaction.import(resumeSource::open)
                        break
                    } catch (failure: LocalModelException) {
                        if (failure.failure != LocalModelFailure.BUSY || SystemClock.elapsedRealtime() >= deadline) throw failure
                        delay(20)
                    }
                }
                assertEquals(0, resumeSource.opened.get())
                env.assertRecords(Case.PROCESS, accepted = true)
                assertNotNull(transaction.installed())
                check(!connection.failed.get() && connection.connections.get() == 1)
                env.proof(Phase.PROCESS, passed(Phase.PROCESS), child)
            } catch (failure: Throwable) {
                primaryFailure = failure
                throw failure
            } finally {
                var cleanupFailure: Throwable? = null
                fun cleanup(action: () -> Unit) {
                    try { action() } catch (failure: Throwable) {
                        if (cleanupFailure == null) cleanupFailure = failure
                        else cleanupFailure?.addSuppressed(failure)
                    }
                }
                // Context can retain connection tracking even when bind returns false.
                if (attempted && !released) cleanup {
                    connection.releasing.set(true)
                    context.unbindService(connection); released = true
                }
                if (attempted) cleanup { context.stopService(intent) }
                if (linked) cleanup {
                    check(released && death.await(5, TimeUnit.SECONDS))
                    endpoint?.unlinkToDeath(recipient, 0)
                }
                cleanupFailure?.let { failure ->
                    if (primaryFailure != null) primaryFailure?.addSuppressed(failure) else throw failure
                }
            }
        }
    }

    private suspend fun selfCancel(env: ReceiptAndroidFixture.Environment, case: Case,
        point: ReceiptCheckpoint): Boolean = coroutineScope {
        val reached = AtomicBoolean()
        val returned = AtomicBoolean()
        val source = ReceiptAndroidFixture.Source()
        val job = launch {
            val self = requireNotNull(coroutineContext[Job])
            env.transaction(case, checkpoint = {
                if (it == point) { reached.set(true); self.cancel() }
            }).import(source::open)
            returned.set(true)
        }
        job.join()
        assertTrue(reached.get() && job.isCancelled && !returned.get())
        assertEquals(1, source.opened.get()); assertEquals(1, source.closed.get())
        true
    }

    private suspend fun expect(reason: LocalModelFailure, block: suspend () -> Unit) {
        try { block(); fail("Expected fixed receipt refusal") }
        catch (failure: LocalModelException) {
            assertEquals(reason, failure.failure)
            assertEquals("Local model unavailable: ${reason.name}", failure.message)
            var cause: Throwable? = failure
            var count = 0
            while (cause != null) {
                assertTrue(++count <= 8)
                assertEquals(LocalModelException::class.java, cause.javaClass)
                assertEquals(failure.message, cause.message)
                cause = cause.cause
            }
        }
    }

    private suspend fun expectCheckpointCancellation(block: suspend () -> Unit) {
        try { block(); fail("Expected receipt checkpoint interruption") }
        catch (_: CancellationException) { /* Preserved unaccepted state is checked independently. */ }
    }

    private fun passed(phase: Phase) = phase.checks.associateWith { true }
    private fun context() = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext

    private class ProofConnection : ServiceConnection {
        val connected = CountDownLatch(1)
        val endpoint = AtomicReference<IBinder?>()
        val failed = AtomicBoolean()
        val releasing = AtomicBoolean()
        val connections = AtomicInteger()
        override fun onServiceConnected(name: ComponentName, service: IBinder) {
            if (connections.incrementAndGet() != 1 || !endpoint.compareAndSet(null, service)) failed.set(true)
            connected.countDown()
        }
        override fun onNullBinding(name: ComponentName) { failed.set(true); connected.countDown() }
        override fun onBindingDied(name: ComponentName) { failed.set(true); connected.countDown() }
        override fun onServiceDisconnected(name: ComponentName) { if (!releasing.get()) failed.set(true) }
    }

    private data class Snapshot(val state: ReceiptProofService.State, val child: ReceiptAndroidFixture.Child)
    private fun snapshot(endpoint: IBinder): Snapshot = request(endpoint, ReceiptProofService.SNAPSHOT) {
        val state = requireNotNull(ReceiptProofService.State.entries.getOrNull(it.readInt()))
        val pid = it.readInt(); val uid = it.readInt(); val start = it.readLong()
        check(pid > 0 && uid > 0 && start > 0)
        Snapshot(state, ReceiptAndroidFixture.Child(pid, start, uid))
    }
    private suspend fun waitHeld(endpoint: IBinder, connection: ProofConnection): ReceiptAndroidFixture.Child {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (true) {
            check(!connection.failed.get())
            val value = snapshot(endpoint)
            if (value.state == ReceiptProofService.State.DATA_FORCED) return value.child
            check(value.state != ReceiptProofService.State.FAILED && SystemClock.elapsedRealtime() < deadline)
            delay(20)
        }
    }
    private fun ack(endpoint: IBinder, code: Int) = request(endpoint, code) { check(it.readInt() == 1) }
    private fun <T> request(endpoint: IBinder, code: Int, read: (Parcel) -> T): T {
        val data = Parcel.obtain(); val reply = Parcel.obtain()
        try {
            data.writeInterfaceToken(ReceiptProofService.TOKEN)
            check(endpoint.transact(code, data, reply, 0))
            reply.readException()
            return read(reply).also { check(reply.dataAvail() == 0) }
        } finally { data.recycle(); reply.recycle() }
    }
}
