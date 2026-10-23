/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.SqliteReliefFixture.FULL_NOTICE
import org.locallore.app.SqliteReliefFixture.accepted
import org.locallore.app.SqliteReliefFixture.fixture
import org.locallore.app.SqliteReliefFixture.initial
import org.locallore.app.SqliteReliefFixture.phase
import org.locallore.app.SqliteReliefFixture.sameAccepted
import org.locallore.app.ui.LocalLoreScreen

/** The sole relief UI case keeps normal Compose Activity/rule teardown. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 28)
class SqliteReliefInstrumentedTest {
    @get:Rule val compose = createComposeRule()
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun idle(model: ShellViewModel) {
        compose.waitUntil(10_000) { !model.state.value.busy }
        compose.waitForIdle()
    }
    @Test fun collectedFullRecoveryAfterOwnedPaddingRemovalPublishesOnlyOriginalAcceptedReceipt() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val before = withContext(Dispatchers.Main) { f.main.replies.acceptedView(0) }
            val model = withContext(Dispatchers.Main) { f.model() }
            compose.setContent {
                val state by model.state.collectAsState()
                LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover)
            }
            idle(model)
            compose.runOnIdle {
                f.main.replies.beforeFirstCommit = { f.padding.fill() }
            }
            tag("give-potion").performClick(); idle(model)
            repeat(2) { attempt ->
                tag("notice").assertTextEquals(FULL_NOTICE)
                tag("revision").assertTextEquals("Accepted revision \u00B7 0")
                tag("potion-owner").assertTextEquals("Healing potion \u00B7 You")
                tag("give-potion").assertIsNotEnabled(); tag("try-ability").assertIsNotEnabled()
                tag("mode-menu").assertIsNotEnabled(); tag("recover-save").assertIsEnabled()
                compose.runOnIdle {
                    assertTrue(model.state.value.recoveryRequired)
                    assertEquals(baseline.messages, model.state.value.messages)
                    assertEquals(baseline.selected, model.state.value.selectedStory)
                    model.submit(DemoAction.GIVE_POTION); model.setMode(DemoMode.MALFORMED)
                    assertEquals(DemoMode.ACCEPTED, model.state.value.mode)
                }
                withContext(Dispatchers.Main) {
                    f.main.replies.originalOnly(attempt + 1, attempt + 1, 0)
                    phase(f.main.replies.status(), "ready")
                    sameAccepted(baseline, f.main.gateway.snapshot())
                    assertTrue(before == f.main.replies.acceptedView(0))
                }
                if (attempt == 0) { tag("recover-save").performClick(); idle(model) }
            }
            f.padding.drop()
            tag("recover-save").performClick(); idle(model)
            tag("revision").assertTextEquals("Accepted revision \u00B7 1")
            tag("potion-owner").assertTextEquals("Healing potion \u00B7 Not in your inventory")
            compose.runOnIdle {
                assertFalse(model.state.value.recoveryRequired)
                assertEquals(2, model.state.value.messages.size)
                assertEquals("You give 1 potion to mira.", model.state.value.messages.single { !it.isPlayer }.text)
            }
            val saved = withContext(Dispatchers.Main) { f.main.gateway.recoverSaved() }
            accepted(saved)
            withContext(Dispatchers.Main) {
                f.main.replies.originalOnly(3, 2, 1)
                phase(f.main.replies.status(), "committed")
                sameAccepted(saved, f.main.gateway.recoverSaved())
                f.main.replies.originalOnly(3, 2, 1)
            }
            val key = f.main.replies.key()
            val receipt = withContext(Dispatchers.Main) { f.main.replies.status().getJSONObject("receipt").toString() }
            val next = f.reopen()
            val oldCalls = f.main.replies.calls.size
            compose.runOnIdle {
                val disposed = model.state.value
                model.submit(DemoAction.GIVE_POTION); model.recover(); model.reset(); model.resume(baseline.selected)
                assertEquals(disposed, model.state.value)
            }
            assertEquals(oldCalls, f.main.replies.calls.size)
            withContext(Dispatchers.Main) {
                sameAccepted(saved, next.gateway.initialize())
                phase(next.replies.status(key), "committed")
                assertTrue(receipt == next.replies.status(key).getJSONObject("receipt").toString())
                accepted(next.gateway.recoverSaved())
                assertEquals(0, next.replies.count("prepare")); assertEquals(0, next.replies.count("commit"))
            }
        }
    }
}
