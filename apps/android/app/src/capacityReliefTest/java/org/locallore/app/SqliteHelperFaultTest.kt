/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Explicit nested selectors each require a fresh instrumentation process; poison is never reset. */
class SqliteHelperFaultTest {
    @RunWith(AndroidJUnit4::class) @SdkSuppress(minSdkVersion = 28)
    class Malformed {
        @Test fun malformedTerminalIsReapedAndPoisonsEveryDependentDispatch() = runFault(PaddingFault.MALFORMED)
    }
    @RunWith(AndroidJUnit4::class) @SdkSuppress(minSdkVersion = 28)
    class Oversize {
        @Test fun oversizeTerminalIsBoundedAndPoisonsEveryDependentDispatch() = runFault(PaddingFault.OVERSIZE)
    }
    @RunWith(AndroidJUnit4::class) @SdkSuppress(minSdkVersion = 28)
    class Timeout {
        @Test fun deadlineDestroysOnlyOwnedChildAndPoisonsEveryDependentDispatch() = runFault(PaddingFault.TIMEOUT)
    }
    @RunWith(AndroidJUnit4::class) @SdkSuppress(minSdkVersion = 28)
    class AfterFill {
        @Test fun closedFullChildBadExitRetainsOwnedPaddingWithoutNativeDispatch() = runFault(PaddingFault.AFTER_FILL_EXIT)
    }
    @RunWith(AndroidJUnit4::class) @SdkSuppress(minSdkVersion = 28)
    class MarkerDrift {
        @Test fun postReadOnlyMarkerDriftIsUncertainAndPoisonsEveryDependentDispatch() = runFault(PaddingFault.MARKER_DRIFT_AFTER_RO)
    }
    @RunWith(AndroidJUnit4::class) @SdkSuppress(minSdkVersion = 28)
    class DispatchFence {
        @Test fun swallowedHelperFailureCannotDispatchAwaitingNativeCommit() = runFault(PaddingFault.MALFORMED, throughHook = true)
    }

    private companion object {
        suspend fun capture(block: suspend () -> Unit): Throwable? = try { block(); null } catch (failure: Throwable) { failure }

        fun runFault(fault: PaddingFault, throughHook: Boolean = false) = runBlocking {
            SqliteReliefFixture.requireIdentity(faultsRequired = true)
            var capturedFixture: SqliteReliefFixture.Fixture? = null
            var helperFailure: Throwable? = null
            var observed: PaddingObservation? = null
            var initialNativeDispatches = -1
            val outerFailure = capture {
                SqliteReliefFixture.fixture { f ->
                    capturedFixture = f
                    val saved = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
                    SqliteReliefFixture.initial(saved)
                    val ready = withContext(Dispatchers.Main) { f.main.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) }
                    assertTrue(ready is DemoResult.Prepared)
                    val key = f.main.replies.key()
                    withContext(Dispatchers.Main) { SqliteReliefFixture.phase(f.main.replies.status(), "ready") }
                    initialNativeDispatches = f.main.replies.nativeDispatches.get()
                    if (throughHook) {
                        f.main.replies.beforeFirstCommit = {
                            // Deliberately swallow the real helper failure to challenge the post-await fence.
                            helperFailure = capture { f.padding.fill(fault) }
                        }
                        val rejected = withContext(Dispatchers.Main) { capture { f.main.gateway.commitAsync(ready) } }
                        assertEquals("no_post_hook_native_dispatch", initialNativeDispatches, f.main.replies.nativeDispatches.get())
                        assertNotNull("awaiting_commit_must_be_fenced", rejected)
                    } else helperFailure = capture { f.padding.fill(fault) }
                    assertNotNull("actual_child_failure_required", helperFailure)
                    observed = f.padding.observation
                    val child = checkNotNull(observed)
                    assertTrue("owned_child_started", child.started)
                    assertTrue("owned_child_reaped", child.reaped)
                    assertTrue("owned_readers_stopped", child.readersStopped)
                    assertFalse("unexpected_pipe_read_failed", child.unexpectedReadFailure)
                    if (fault == PaddingFault.TIMEOUT) {
                        // destroy() may close a blocked reader; this never restores protocol/SQL certainty.
                        assertEquals("owned_shutdown_read_observation", child.readFailed, child.shutdownReadFailure)
                    } else {
                        assertFalse("pipe_read_failed", child.readFailed)
                        assertFalse("unrequested_shutdown_read_failed", child.shutdownReadFailure)
                    }
                    assertTrue("bounded_pipe_bytes", child.bytesSeen in 0..9216)
                    assertFalse("unknown_completion_is_sticky", PaddingOwner.ownershipKnown())
                    assertTrue("owner_unknown_completion", f.padding.hasUnknownOwnership)
                    when (fault) {
                        PaddingFault.OVERSIZE -> { assertTrue(child.overflow); assertTrue(child.bytesSeen > 8192) }
                        PaddingFault.TIMEOUT -> { assertTrue(child.deadlineExpired); assertTrue(child.destroyRequested) }
                        PaddingFault.AFTER_FILL_EXIT -> assertEquals(79, child.exitCode)
                        PaddingFault.MARKER_DRIFT_AFTER_RO -> assertEquals(80, child.exitCode)
                        PaddingFault.MALFORMED -> { assertEquals(0, child.exitCode); assertFalse(child.overflow) }
                        PaddingFault.NONE -> fail("Fault selection required")
                    }
                    assertFalse("padding_not_acknowledged_restored", f.padding.restored)
                    assertEquals("no_post_fault_native_dispatch", initialNativeDispatches, f.main.replies.nativeDispatches.get())

                    // These attempts must fail at their in-memory entry gates, before IO or JNI.
                    val starts = PaddingOwner.startedCount()
                    val roots = SqliteReliefFixture.createdRoots()
                    val owners = SqliteReliefFixture.createdOwners()
                    assertNotNull(capture { withContext(Dispatchers.Main) { f.main.replies.status(key) } })
                    assertNotNull(capture { f.reopen() })
                    assertNotNull(capture { SqliteReliefFixture.Owner(f.context) })
                    assertNotNull(capture { PaddingOwner(f.database, f.token).fill() })
                    assertNotNull(capture { f.padding.drop() })
                    assertNotNull(capture { f.probeForFaultTest() })
                    assertNotNull(capture { SqliteReliefFixture.fixture { fail("Poisoned fixture dispatched") } })
                    assertEquals(starts, PaddingOwner.startedCount())
                    assertEquals(roots, SqliteReliefFixture.createdRoots())
                    assertEquals(owners, SqliteReliefFixture.createdOwners())
                    assertEquals(initialNativeDispatches, f.main.replies.nativeDispatches.get())
                    assertEquals(0, f.cleanup.probeDispatches)
                    throw checkNotNull(helperFailure) // Keep the original real child failure through cleanup.
                }
            }
            // Preserve genuine assertion/cleanup failures in RED and unexpected execution paths.
            if (outerFailure !== helperFailure) throw checkNotNull(outerFailure)
            assertSame(helperFailure, outerFailure)
            val f = checkNotNull(capturedFixture)
            assertEquals(observed, f.padding.observation)
            assertTrue("existing_owner_close_allowed", f.main.replies.closeCalls.get() > 0)
            assertTrue("existing_owners_closed", f.cleanup.ownersClosed)
            assertTrue("native_exchanges_drained", f.cleanup.exchangesDrained)
            assertEquals(0, f.main.replies.exchanges.get())
            assertEquals(0, f.cleanup.dropAttempts); assertEquals(0, f.cleanup.probeDispatches)
            assertFalse("no_root_delete_attempt", f.cleanup.deletionAttempted)
            assertTrue("root_intentionally_retained_without_probe", f.cleanup.rootRetained)
            assertEquals(initialNativeDispatches, f.main.replies.nativeDispatches.get())
            assertFalse(PaddingOwner.ownershipKnown())
        }
    }
}
