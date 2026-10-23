/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Before
import org.junit.FixMethodOrder
import org.junit.Test
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.junit.runners.MethodSorters
import org.locallore.app.SqliteReliefFixture.accepted
import org.locallore.app.SqliteReliefFixture.fixture
import org.locallore.app.SqliteReliefFixture.full
import org.locallore.app.SqliteReliefFixture.initial
import org.locallore.app.SqliteReliefFixture.phase
import org.locallore.app.SqliteReliefFixture.sameAccepted

/** Native-only cases allocate no Activity or Compose rule. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 28)
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
class SqliteReliefNativeTest {
    @Before fun noLiveActivityBeforeNativeCase() = noLiveActivity()
    @After fun noLiveActivityAfterNativeCase() = noLiveActivity()
    private fun noLiveActivity() = runBlocking {
        withContext(Dispatchers.Main) {
            val monitor = ActivityLifecycleMonitorRegistry.getInstance()
            for (stage in Stage.values().filter { it != Stage.DESTROYED }) {
                assertEquals("native_activity_${stage.name}_count", 0, monitor.getActivitiesInStage(stage).size)
            }
        }
    }
    @Test fun actualFullThenOwnedPaddingRemovalCommitsOnlyOriginalReadyKeyOnce() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val before = withContext(Dispatchers.Main) { f.main.replies.acceptedView(0) }
            val ready = withContext(Dispatchers.Main) {
                f.main.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            }
            assertTrue(ready is DemoResult.Prepared)
            withContext(Dispatchers.Main) { phase(f.main.replies.status(), "ready") }
            f.padding.fill() // Both child SQL and process are closed before the actual Rust commit.
            withContext(Dispatchers.Main) {
                full { f.main.gateway.commitAsync(ready) }
                full { f.main.gateway.recoverSaved() }
                f.main.replies.originalOnly(2, 2, 0)
                phase(f.main.replies.status(), "ready")
                sameAccepted(baseline, f.main.gateway.snapshot())
                assertTrue(before == f.main.replies.acceptedView(0))
            }
            f.padding.drop()
            val saved = withContext(Dispatchers.Main) { f.main.gateway.recoverSaved() }
            accepted(saved)
            val receipt = withContext(Dispatchers.Main) { f.main.replies.status().getJSONObject("receipt").toString() }
            withContext(Dispatchers.Main) {
                phase(f.main.replies.status(), "committed")
                sameAccepted(saved, f.main.gateway.recoverSaved())
                f.main.replies.originalOnly(3, 2, 1)
                assertTrue(receipt == f.main.replies.status().getJSONObject("receipt").toString())
            }
            val key = f.main.replies.key()
            val request = f.main.replies.request()
            val after = withContext(Dispatchers.Main) { f.main.replies.acceptedView(1) }
            val next = f.reopen()
            withContext(Dispatchers.Main) {
                sameAccepted(saved, next.gateway.initialize())
                phase(next.replies.status(key), "committed")
                assertTrue(receipt == next.replies.resubmit(request).getJSONObject("receipt").toString())
                assertTrue(after == next.replies.acceptedView(1))
                accepted(next.gateway.recoverSaved())
                assertEquals(0, next.replies.count("prepare")); assertEquals(0, next.replies.count("commit"))
            }
        }
    }
    @Test fun cancelledFullReadyTurnRemainsUnspentAfterPaddingRemovalAndReopen() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val before = withContext(Dispatchers.Main) { f.main.replies.acceptedView(0) }
            val ready = withContext(Dispatchers.Main) { f.main.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) }
            assertTrue(ready is DemoResult.Prepared)
            f.padding.fill()
            withContext(Dispatchers.Main) {
                full { f.main.gateway.commitAsync(ready) }
                full { f.main.gateway.recoverSaved() }
                f.main.replies.originalOnly(2, 2, 0)
                phase(f.main.replies.status(), "ready")
                sameAccepted(baseline, f.main.gateway.cancelSaved())
                phase(f.main.replies.status(), "cancelled")
                assertTrue(before == f.main.replies.acceptedView(0))
            }
            f.padding.drop()
            withContext(Dispatchers.Main) {
                phase(f.main.replies.native(f.main.replies.scoped("commit").put("turn", f.main.replies.key())), "cancelled")
                sameAccepted(baseline, f.main.gateway.recoverSaved())
                phase(f.main.replies.status(), "cancelled")
                f.main.replies.originalOnly(3, 2, 0)
            }
            val key = f.main.replies.key()
            val request = f.main.replies.request()
            val next = f.reopen()
            withContext(Dispatchers.Main) {
                val saved = next.gateway.initialize()
                sameAccepted(baseline, saved); assertEquals(0, saved.uncommittedDrafts)
                phase(next.replies.status(key), "cancelled")
                phase(next.replies.resubmit(request), "cancelled")
                initial(next.gateway.recoverSaved())
                assertTrue(before == next.replies.acceptedView(0))
                assertEquals(0, next.replies.count("prepare")); assertEquals(0, next.replies.count("commit"))
            }
        }
    }
}
