/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.locallore.app.CapacityTestFixture.fixture
import org.locallore.app.CapacityTestFixture.initial
import org.locallore.app.CapacityTestFixture.sameAccepted
import org.locallore.app.CapacityTestFixture.failureFull
import org.locallore.app.CapacityTestFixture.readyWithoutReceipt
import org.junit.FixMethodOrder
import org.junit.Before
import org.junit.After
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import org.junit.runners.MethodSorters

/** Real JNI/SQLite checks deliberately allocate no Compose rule or Activity. */
@RunWith(AndroidJUnit4::class)
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
class SqliteCapacityNativeTest {
    @Before fun noLiveActivityBeforeNativeCase() = requireNoLiveActivities()
    @After fun noLiveActivityAfterNativeCase() = requireNoLiveActivities()

    private fun requireNoLiveActivities() = runBlocking {
        withContext(Dispatchers.Main) {
            val monitor = ActivityLifecycleMonitorRegistry.getInstance()
            for (stage in Stage.values().filter { it != Stage.DESTROYED }) {
                // Report fixed stage/count only, never an Activity identifier.
                val count = monitor.getActivitiesInStage(stage).size
                assertEquals("native_activity_${stage.name}_count", 0, count)
            }
        }
    }

    @Test fun actualReadyFullRetriesKeepOriginalKeyAndCanonThenReopenAsUncommittedDraft() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val accepted = withContext(Dispatchers.Main) { f.main.replies.acceptedView(baseline.revision) }
            withContext(Dispatchers.Main) {
                val ready = f.main.gateway.respond(DemoAction.GIVE_POTION, baseline.revision, DemoMode.ACCEPTED)
                assertTrue(ready is DemoResult.Prepared)
                readyWithoutReceipt(f.main.replies.status())
                failureFull { f.main.gateway.commitAsync(ready) }
                repeat(2) { failureFull { f.main.gateway.recoverSaved() } }
                f.main.replies.assertOriginalOnly(3)
                readyWithoutReceipt(f.main.replies.status())
                val saved = f.main.gateway.snapshot()
                sameAccepted(baseline, saved)
                assertEquals(1, saved.uncommittedDrafts)
                assertTrue(accepted == f.main.replies.acceptedView(baseline.revision))
            }
            val key = f.main.replies.key()
            val next = f.reopen()
            withContext(Dispatchers.Main) {
                val saved = next.gateway.initialize()
                sameAccepted(baseline, saved)
                assertEquals(1, saved.uncommittedDrafts)
                readyWithoutReceipt(next.replies.status(key), "queued")
                sameAccepted(baseline, next.gateway.recoverSaved())
                assertTrue(accepted == next.replies.acceptedView(baseline.revision))
                assertEquals(0, next.replies.count("submit"))
                assertEquals(0, next.replies.count("prepare"))
                assertEquals(0, next.replies.count("commit"))
            }
        }
    }

    @Test fun cancellingActualFullTurnPersistsCancellationAndReopenCannotApplyItsOriginalRequest() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val accepted = withContext(Dispatchers.Main) { f.main.replies.acceptedView(baseline.revision) }
            withContext(Dispatchers.Main) {
                val ready = f.main.gateway.respond(DemoAction.GIVE_POTION, baseline.revision, DemoMode.ACCEPTED)
                assertTrue(ready is DemoResult.Prepared)
                failureFull { f.main.gateway.commitAsync(ready) }
                failureFull { f.main.gateway.recoverSaved() }
                f.main.replies.assertOriginalOnly(2)
                readyWithoutReceipt(f.main.replies.status())
                val cancelled = f.main.gateway.cancelSaved()
                sameAccepted(baseline, cancelled)
                assertEquals(0, cancelled.uncommittedDrafts)
                readyWithoutReceipt(f.main.replies.status(), "cancelled")
                sameAccepted(baseline, f.main.gateway.recoverSaved())
                assertTrue(accepted == f.main.replies.acceptedView(baseline.revision))
            }
            val key = f.main.replies.key()
            val request = f.main.replies.originalRequest()
            val next = f.reopen()
            withContext(Dispatchers.Main) {
                val saved = next.gateway.initialize()
                sameAccepted(baseline, saved)
                assertEquals(0, saved.uncommittedDrafts)
                readyWithoutReceipt(next.replies.status(key), "cancelled")
                readyWithoutReceipt(next.replies.resubmit(request), "cancelled")
                sameAccepted(baseline, next.gateway.recoverSaved())
                assertTrue(accepted == next.replies.acceptedView(baseline.revision))
                assertEquals(0, next.replies.count("prepare")); assertEquals(0, next.replies.count("commit"))
            }
        }
    }
}
