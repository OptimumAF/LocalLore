/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Service
import android.content.ComponentName
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import android.os.Parcel
import android.os.Process
import android.os.SystemClock
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/** Same-UID, nonexported, volume-debug-only child; it never accepts a path or model payload. */
class ReceiptProofService : Service() {
    private val state = AtomicReference(State.IDLE)
    private val haltArmed = AtomicBoolean()
    private val heldAt = AtomicLong()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val endpoint = object : Binder() {
        override fun onTransact(code: Int, data: Parcel, reply: Parcel?, flags: Int): Boolean {
            if (code !in START..HALT) return super.onTransact(code, data, reply, flags)
            ReceiptAndroidFixture.requireIdentity(this@ReceiptProofService, child = true)
            check(Binder.getCallingUid() == Process.myUid()) { "Receipt caller refused" }
            // Binder may add framework bookkeeping flags to a caller's flags=0.
            // Require synchronous semantics, not a zero transport-flags integer.
            check((flags and IBinder.FLAG_ONEWAY) == 0) { "Receipt synchronous call required" }
            data.enforceInterface(TOKEN)
            check(data.dataAvail() == 0) { "Receipt payload refused" }
            val result = checkNotNull(reply) { "Receipt reply required" }
            when (code) {
                START -> {
                    check(state.compareAndSet(State.IDLE, State.RUNNING)) { "Receipt start state refused" }
                    scope.launch {
                        try {
                            val env = ReceiptAndroidFixture.open(applicationContext, child = true)
                            env.fresh(ReceiptAndroidFixture.Case.PROCESS)
                            val neverReleased = CountDownLatch(1)
                            env.transaction(ReceiptAndroidFixture.Case.PROCESS, checkpoint = {
                                if (it == ReceiptCheckpoint.DATA_FORCED) {
                                    heldAt.set(SystemClock.elapsedRealtime())
                                    check(state.compareAndSet(State.RUNNING, State.DATA_FORCED))
                                    // No cancellation/close/latch release can commit this worker.
                                    // Timeout is a preserved failure, never successful drainage.
                                    check(neverReleased.await(30, TimeUnit.SECONDS))
                                    error("Receipt fixture cannot resume child")
                                }
                            }).import { ReceiptAndroidFixture.bytes.inputStream() }
                            state.set(State.FAILED)
                        } catch (_: Exception) { state.set(State.FAILED) }
                    }
                    result.writeNoException(); result.writeInt(1)
                }
                SNAPSHOT -> {
                    result.writeNoException()
                    result.writeInt(state.get().ordinal)
                    result.writeInt(Process.myPid())
                    result.writeInt(Process.myUid())
                    result.writeLong(Process.getStartElapsedRealtime())
                }
                HALT -> {
                    check(state.get() == State.DATA_FORCED) { "Receipt halt state refused" }
                    check(SystemClock.elapsedRealtime() - heldAt.get() < 20_000) { "Receipt halt deadline refused" }
                    check(haltArmed.compareAndSet(false, true)) { "Receipt halt already armed" }
                    // Return the acknowledgement before the parent removes AUTO_CREATE.
                    // onUnbind then kills this process while the file lock remains held.
                    result.writeNoException(); result.writeInt(1)
                }
            }
            return true
        }
    }

    override fun onBind(intent: Intent): IBinder {
        ReceiptAndroidFixture.requireIdentity(this, child = true)
        check(intent.component == ComponentName(this, ReceiptProofService::class.java))
        check(intent.action == null && intent.data == null && intent.extras == null)
        return endpoint
    }

    override fun onUnbind(intent: Intent): Boolean {
        // Includes failure cleanup: never cancel/join the worker or release its lock first.
        killOwnedChild()
        return false
    }

    override fun onDestroy() {
        killOwnedChild()
        super.onDestroy()
    }

    private fun killOwnedChild() {
        ReceiptAndroidFixture.requireIdentity(this, child = true)
        Process.killProcess(Process.myPid())
    }

    internal enum class State { IDLE, RUNNING, DATA_FORCED, FAILED }
    internal companion object {
        const val TOKEN = "org.locallore.app.receiptproof.v1"
        const val START = 1
        const val SNAPSHOT = 2
        const val HALT = 3
    }
}
