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
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Rule
import org.locallore.app.CapacityTestFixture.samePresentation
import org.locallore.app.CapacityTestFixture.PREFIX_TURNS
import org.locallore.app.CapacityTestFixture.FULL_NOTICE
import org.locallore.app.ui.LocalLoreScreen

/** The sole capacity gameplay UI case retains its ordinary Compose rule teardown. */
@RunWith(AndroidJUnit4::class)
class SqliteCapacityInstrumentedTest {
    @get:Rule val compose = createComposeRule()

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun idle(model: ShellViewModel) {
        compose.waitUntil(10_000) { !model.state.value.busy }
        compose.waitForIdle()
    }

    @Test fun composedActualFullKeepsLastCanonBlocksCallbacksAndRepeatedRecoveryThenFencesDisposal() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val accepted = withContext(Dispatchers.Main) { f.main.replies.acceptedView(baseline.revision) }
            val model = withContext(Dispatchers.Main) { f.model() }
            compose.setContent {
                val state by model.state.collectAsState()
                LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover)
            }
            idle(model)
            tag("give-potion").performClick(); idle(model)
            repeat(3) { attempt ->
                tag("notice").assertTextEquals(FULL_NOTICE)
                tag("revision").assertTextEquals("Accepted revision \u00B7 $PREFIX_TURNS")
                tag("potion-owner").assertTextEquals("Healing potion \u00B7 You")
                tag("give-potion").assertIsNotEnabled(); tag("try-ability").assertIsNotEnabled()
                tag("mode-menu").assertIsNotEnabled(); tag("recover-save").assertIsEnabled()
                compose.runOnIdle {
                    samePresentation(baseline, model.state.value)
                    assertTrue(model.state.value.recoveryRequired)
                    model.submit(DemoAction.GIVE_POTION)
                    model.setMode(DemoMode.MALFORMED)
                    assertEquals(DemoMode.ACCEPTED, model.state.value.mode)
                }
                withContext(Dispatchers.Main) {
                    f.main.replies.assertOriginalOnly(attempt + 1)
                    readyWithoutReceipt(f.main.replies.status())
                    assertTrue(accepted == f.main.replies.acceptedView(baseline.revision))
                }
                if (attempt < 2) { tag("recover-save").performClick(); idle(model) }
            }
            val key = f.main.replies.key()
            val next = f.reopen() // Disposal closes this owner; it does not cancel its persisted draft.
            val calls = f.main.replies.calls.size
            compose.runOnIdle {
                val disposed = model.state.value
                model.submit(DemoAction.GIVE_POTION); model.recover(); model.reset(); model.resume(baseline.selected)
                assertEquals(disposed, model.state.value)
            }
            assertEquals(calls, f.main.replies.calls.size)
            withContext(Dispatchers.Main) {
                val saved = next.gateway.initialize()
                sameAccepted(baseline, saved)
                assertEquals(1, saved.uncommittedDrafts)
                readyWithoutReceipt(next.replies.status(key), "queued")
                sameAccepted(baseline, next.gateway.recoverSaved())
                assertEquals(0, next.replies.count("prepare")); assertEquals(0, next.replies.count("commit"))
                assertTrue(accepted == next.replies.acceptedView(baseline.revision))
            }
        }
    }
}
