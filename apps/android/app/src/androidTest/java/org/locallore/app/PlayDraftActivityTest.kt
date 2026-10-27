/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.RuleChain
import org.junit.rules.TestRule
import org.junit.runners.model.Statement

/** Actual product factory and saved-instance recreation, with synthetic scripted inference. */
class PlayDraftActivityTest {
    private val compose = createAndroidComposeRule<MainActivity>()
    private val isolatedPackage = TestRule { base, _ ->
        object : Statement() {
            override fun evaluate() {
                // Refuse before the Activity can open a different installed app's workspace.
                assumeTrue("Requires isolated input-draft verification APK",
                    InstrumentationRegistry.getInstrumentation().targetContext.packageName in
                        setOf("org.locallore.app.draftverify", "org.locallore.app.draftprocessverify"))
                base.evaluate()
            }
        }
    }
    @get:Rule val rules: TestRule = RuleChain.outerRule(isolatedPackage).around(compose)

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }

    @Test fun actualRecreationKeepsScopedEditorAndOwnerButNeverSubmitsIt() {
        lateinit var model: ShellViewModel
        lateinit var originalTransport: NativeWorkspaceTransport
        compose.activityRule.scenario.onActivity {
            model = ViewModelProvider(it)[ShellViewModel::class.java]
            originalTransport = requireNotNull(it.constructedWorkspaceTransport)
        }
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.persistent }
        assertFalse(model.state.value.recoveryRequired)
        val priorStory = model.state.value.selectedStory?.story
        compose.runOnIdle { model.reset() }
        compose.waitUntil(15_000) {
            !model.state.value.busy && model.state.value.selectedStory != null &&
                model.state.value.selectedStory?.story != priorStory
        }
        val before = model.state.value
        assertEquals(0L, before.revision)
        assertTrue(before.messages.isEmpty())
        assertEquals(TextProvider.SCRIPTED, before.textProvider)
        tag("play-kind-dialogue").performClick()
        val words = "SYNTHETIC unsent dialogue: Mira, I remember the lanterns.\nNo turn has been sent."
        tag("play-input").performTextReplacement(words)
        tag("play-send").assertIsEnabled()

        compose.activityRule.scenario.recreate()
        compose.activityRule.scenario.onActivity {
            assertSame(model, ViewModelProvider(it)[ShellViewModel::class.java])
            // The retained ViewModel owns the original transport. Recreation allocates none.
            assertNull(it.constructedWorkspaceTransport)
        }
        compose.waitForIdle()
        tag("play-input").assert(hasText(words))
        tag("play-kind-dialogue").assertIsSelected()
        assertEquals(before.selectedStory, model.state.value.selectedStory)
        assertEquals(before.revision, model.state.value.revision)
        assertEquals(before.messages, model.state.value.messages)
        assertEquals(before.potionOwner, model.state.value.potionOwner)
        assertNotNull(originalTransport)

        // Re-read native saved state; a matching UI copy alone would not prove no commit.
        compose.runOnIdle { model.recover() }
        compose.waitUntil(15_000) { !model.state.value.busy }
        assertFalse(model.state.value.recoveryRequired)
        assertEquals(0L, model.state.value.revision)
        assertEquals(before.messages, model.state.value.messages)
        tag("play-input").assert(hasText(words))
        tag("play-send").performClick()
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.revision == 1L }
        val committed = model.state.value
        assertEquals(1, committed.messages.count { it.isPlayer && it.text == words })
        assertEquals(before.potionOwner, committed.potionOwner)

        compose.activityRule.scenario.recreate()
        compose.waitForIdle()
        tag("play-input").assert(hasText(words))
        tag("play-kind-dialogue").assertIsSelected()
        compose.runOnIdle { model.recover() }
        compose.waitUntil(15_000) { !model.state.value.busy }
        assertFalse(model.state.value.recoveryRequired)
        assertEquals(1L, model.state.value.revision)
        assertEquals(committed.messages, model.state.value.messages)
    }
}
