/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.res.Configuration
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.LocalLoreScreen

/** Real Compose configuration changes with inert state/callbacks; no engine/model/JNI proof. */
class SystemThemeTest {
    @get:Rule val compose = createComposeRule()

    private class Calls {
        val actions = mutableListOf<DemoAction>()
        val modes = mutableListOf<DemoMode>()
        val sent = mutableListOf<Pair<PlayInput, SavedStory?>>()
        var cancels = 0; var resets = 0; var diagnostics = 0
        fun assertQuiet() {
            assertTrue(actions.isEmpty()); assertTrue(modes.isEmpty()); assertTrue(sent.isEmpty())
            assertEquals(0, cancels); assertEquals(0, resets); assertEquals(0, diagnostics)
        }
    }

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }

    private fun show(state: MutableState<ShellState>, night: MutableState<Int>, calls: Calls,
        capture: (ColorScheme) -> Unit) {
        compose.setContent {
            val configuration = Configuration(LocalConfiguration.current).apply {
                uiMode = (uiMode and Configuration.UI_MODE_NIGHT_MASK.inv()) or night.value
            }
            CompositionLocalProvider(LocalConfiguration provides configuration) {
                LocalLoreScreen(state.value, { calls.actions += it }, {
                    calls.modes += it; state.value = state.value.copy(mode = it)
                }, { calls.cancels++ }, { calls.resets++ }, onDiagnostics = { calls.diagnostics++ },
                    onText = { input, story -> calls.sent += input to story }, exposeTestTags = true,
                    overlay = { val colors = MaterialTheme.colorScheme; SideEffect { capture(colors) } })
            }
        }
        compose.waitForIdle()
    }

    private fun awaitTheme(read: () -> ColorScheme?, dark: Boolean) {
        compose.waitUntil(5_000) {
            compose.runOnIdle {
                read()?.let { if (dark) it.surface.luminance() < 0.1f else it.surface == Color(0xFFF8F5EC) } == true
            }
        }
    }

    @Test fun systemDayNightRoundTripKeepsScopedDialogueDraftStateAndUserCallbacks() {
        val story = SavedStory("scripted-theme-story", "main", "SCRIPTED theme fixture", 7)
        val initial = ShellState(revision = 7, potionOwner = "Mira", mode = DemoMode.REJECTED,
            persistent = true, stories = listOf(story), selectedStory = story, textProvider = TextProvider.SCRIPTED,
            messages = listOf(SceneMessage(1, "SCRIPTED unchanged narration", false)), notice = "SCRIPTED unchanged notice")
        val state = mutableStateOf(initial); val night = mutableStateOf(Configuration.UI_MODE_NIGHT_NO)
        val calls = Calls(); var colors: ColorScheme? = null
        show(state, night, calls) { colors = it }; awaitTheme({ colors }, false)
        val draft = "SCRIPTED dialogue retained across the system theme change."
        tag("play-kind-dialogue").performClick()
        tag("play-input").performTextReplacement(draft)
        for ((mode, dark) in listOf(Configuration.UI_MODE_NIGHT_YES to true, Configuration.UI_MODE_NIGHT_NO to false)) {
            compose.runOnIdle { night.value = mode }
            awaitTheme({ colors }, dark)
            tag("play-input").assert(hasText(draft))
            tag("play-kind-dialogue").assertIsSelected()
            tag("play-send").assertIsEnabled()
            tag("message-body-1").assertTextEquals("SCRIPTED unchanged narration")
            tag("notice").assertTextEquals("SCRIPTED unchanged notice")
            compose.runOnIdle {
                assertSame(initial, state.value); calls.assertQuiet()
                val observed = checkNotNull(colors)
                if (dark) assertTrue(observed.onSurface.luminance() > observed.surface.luminance())
                else assertEquals(Color(0xFF18584E), observed.primary)
            }
        }
        tag("mode-menu").performClick()
        compose.onNodeWithTag("mode-FAILED").performClick()
        tag("play-send").performClick()
        tag("try-ability").performClick()
        compose.runOnIdle {
            assertEquals(listOf(DemoMode.FAILED), calls.modes)
            assertEquals(listOf(PlayInput(PlayInputKind.DIALOGUE, draft) to story), calls.sent)
            assertEquals(listOf(DemoAction.TRY_ABILITY), calls.actions)
            assertEquals(initial.copy(mode = DemoMode.FAILED), state.value)
            assertEquals(0, calls.cancels); assertEquals(0, calls.resets); assertEquals(0, calls.diagnostics)
        }
    }

    @Test fun nightDayChangesDoNotSubmitOrCancelBusyDraftAndExplicitCancelStillFiresOnce() {
        val state = mutableStateOf(ShellState(textProvider = TextProvider.SCRIPTED, revision = 11))
        val night = mutableStateOf(Configuration.UI_MODE_NIGHT_NO); val calls = Calls(); var colors: ColorScheme? = null
        show(state, night, calls) { colors = it }; awaitTheme({ colors }, false)
        val draft = "SCRIPTED pending action remains inert."
        tag("play-input").performTextReplacement(draft)
        compose.runOnIdle { state.value = state.value.copy(busy = true, preparingResponse = true) }
        val before = compose.runOnIdle { state.value }
        for ((mode, dark) in listOf(Configuration.UI_MODE_NIGHT_YES to true, Configuration.UI_MODE_NIGHT_NO to false)) {
            compose.runOnIdle { night.value = mode }
            awaitTheme({ colors }, dark)
            tag("play-input").assert(hasText(draft)).assertIsNotEnabled()
            tag("play-send").assertIsNotEnabled()
            tag("give-potion").assertIsNotEnabled()
            tag("cancel-turn").assertIsEnabled()
            compose.runOnIdle { assertSame(before, state.value); calls.assertQuiet() }
        }
        tag("cancel-turn").performClick()
        compose.runOnIdle {
            assertEquals(1, calls.cancels)
            assertSame(before, state.value) // Callback plumbing only; this fixture owns no runtime resource.
            assertTrue(calls.sent.isEmpty()); assertTrue(calls.actions.isEmpty()); assertTrue(calls.modes.isEmpty())
            assertEquals(0, calls.resets); assertEquals(0, calls.diagnostics)
        }
    }
}
