/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import android.content.Context
import android.graphics.Insets
import android.view.ViewGroup
import android.view.WindowInsets
import android.view.WindowManager
import android.widget.FrameLayout
import androidx.activity.ComponentActivity
import androidx.annotation.RequiresApi
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.Density
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.view.WindowCompat
import androidx.test.filters.SdkSuppress
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.PlayInput
import org.locallore.app.SavedStory
import org.locallore.app.SceneMessage
import org.locallore.app.ShellState
import org.locallore.app.TextProvider

/** Injected Android insets and real screen layout only; no real-IME, JNI or story acceptance proof. */
@RequiresApi(30)
@SdkSuppress(minSdkVersion = 30)
class ChatImeInsetsTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()
    private lateinit var host: StickyInsetsFrame
    private lateinit var content: ComposeView
    private var pixelsPerDp = 1f
    private val statusPx = 24
    private val navigationPx = 18

    private class Calls {
        val sent = mutableListOf<Pair<PlayInput, SavedStory?>>()
        var actions = 0
        var modes = 0
        var cancels = 0
        var resets = 0
        var diagnostics = 0

        fun assertQuiet() {
            assertTrue(sent.isEmpty())
            assertEquals(0, actions)
            assertEquals(0, modes)
            assertEquals(0, cancels)
            assertEquals(0, resets)
            assertEquals(0, diagnostics)
        }
    }

    // Like the AndroidX inset-test strategy, retain the injected platform value:
    // requestApplyInsets must not replace it with an unrelated real system frame.
    // Reference: AndroidX WindowInsetsPaddingTest.kt @ ffbddbd1295b99a57b395a5dcfb86af31f451492.
    private class StickyInsetsFrame(context: Context) : FrameLayout(context) {
        var injected: WindowInsets? = null
        override fun dispatchApplyWindowInsets(insets: WindowInsets): WindowInsets =
            super.dispatchApplyWindowInsets(injected ?: insets)
    }

    private fun initial(): ShellState {
        val story = SavedStory("scripted-ime-story", "main", "SCRIPTED inset fixture", 20)
        return ShellState(revision = 20, potionOwner = "Mira", persistent = true,
            selectedStory = story, stories = listOf(story), textProvider = TextProvider.SCRIPTED,
            messages = (1..40).map { id ->
                SceneMessage(id.toLong(), "SCRIPTED accepted row $id.\n" +
                    "The survey quay stays unchanged.\n".repeat(3), id % 2 == 1)
            })
    }

    private fun show(state: MutableState<ShellState>, calls: Calls, fontScale: Float = 1f) {
        compose.runOnUiThread {
            WindowCompat.setDecorFitsSystemWindows(compose.activity.window, false)
            // The fixture does not ask Android to resize its window or show an IME.
            // Only the explicitly injected native inset frame changes its layout.
            compose.activity.window.setSoftInputMode(
                WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING or
                    WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN)
        }
        compose.setContent {
            AndroidView(factory = { context ->
                StickyInsetsFrame(context).also { frame ->
                    host = frame
                    content = ComposeView(context)
                    frame.addView(content, ViewGroup.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
                    content.setContent {
                        val density = LocalDensity.current.density
                        SideEffect { pixelsPerDp = density }
                        CompositionLocalProvider(LocalDensity provides Density(density, fontScale)) {
                            LocalLoreScreen(state.value, { calls.actions++ }, { calls.modes++ },
                                { calls.cancels++ }, { calls.resets++ },
                                onDiagnostics = { calls.diagnostics++ },
                                onText = { input, story -> calls.sent += input to story }, exposeTestTags = true)
                        }
                    }
                }
            }, modifier = Modifier.fillMaxSize())
        }
        compose.waitForIdle()
        injectIme(0)
    }

    private fun injectIme(bottom: Int) {
        compose.runOnIdle {
            val status = Insets.of(0, statusPx, 0, 0)
            val navigation = Insets.of(0, 0, 0, navigationPx)
            val insets = WindowInsets.Builder()
                .setInsets(WindowInsets.Type.statusBars(), status)
                .setInsetsIgnoringVisibility(WindowInsets.Type.statusBars(), status)
                .setVisible(WindowInsets.Type.statusBars(), true)
                .setInsets(WindowInsets.Type.navigationBars(), navigation)
                .setInsetsIgnoringVisibility(WindowInsets.Type.navigationBars(), navigation)
                .setVisible(WindowInsets.Type.navigationBars(), true)
                .setInsets(WindowInsets.Type.ime(), Insets.of(0, 0, 0, bottom))
                .setVisible(WindowInsets.Type.ime(), bottom > 0)
                .setDisplayCutout(null)
                .build()
            host.injected = insets
            host.dispatchApplyWindowInsets(insets)
        }
        compose.waitForIdle()
    }

    private fun scrollTo(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        // The composer can be taller than the viewport at doubled font scale.
        // Reveal the actual descendant, not only the top of its LazyColumn item.
        return compose.onNodeWithTag(tag).performScrollTo()
    }

    private fun rawBounds(tag: String): Rect {
        val bounds = compose.onNodeWithTag(tag).getUnclippedBoundsInRoot()
        return Rect(bounds.left.value * pixelsPerDp, bounds.top.value * pixelsPerDp,
            bounds.right.value * pixelsPerDp, bounds.bottom.value * pixelsPerDp)
    }

    private fun assertLatestBottom(ime: Int) {
        compose.onNodeWithTag("transcript-latest").assertIsDisplayed()
        val height = compose.runOnIdle { content.height.toFloat() }
        val bottom = height - maxOf(navigationPx, ime)
        compose.waitUntil(5_000) { kotlin.math.abs(rawBounds("transcript-latest").bottom - bottom) <= 1f }
        assertEquals(bottom, rawBounds("transcript-latest").bottom, 1f)
        assertEquals(statusPx.toFloat(), rawBounds("story-list").top, 1f)
    }

    @After fun releaseNestedComposition() {
        if (::content.isInitialized) compose.runOnIdle { content.disposeComposition() }
    }

    @Test fun injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        scrollTo("message-body-10").assertIsDisplayed()
        assertLatestBottom(0)
        val closed = rawBounds("transcript-latest")
        val ime = compose.runOnIdle { content.height / 3 }
        assertTrue(ime > navigationPx)

        injectIme(ime)
        assertLatestBottom(ime)
        assertTrue(rawBounds("transcript-latest").bottom < closed.bottom)
        injectIme(0)
        assertLatestBottom(0)
        assertEquals(closed.bottom, rawBounds("transcript-latest").bottom, 1f)
        compose.runOnIdle { assertSame(original, state.value); calls.assertQuiet() }
    }

    @Test fun doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls, fontScale = 2f)
        val draft = "SCRIPTED caf\u00e9 \uD83C\uDF0A dialogue remains unsent.\nStill my own words."
        scrollTo("play-kind-dialogue").performClick()
        scrollTo("play-input").performTextReplacement(draft)
        val retainedEdit = checkNotNull(compose.onNodeWithTag("play-input").fetchSemanticsNode()
            .config[SemanticsActions.SetText].action)
        val ime = compose.runOnIdle { content.height / 3 }
        injectIme(ime)
        scrollTo("play-send").assertIsDisplayed().assertIsEnabled()
        val send = rawBounds("play-send")
        val height = compose.runOnIdle { content.height.toFloat() }
        assertTrue(send.top >= statusPx - 1f)
        assertTrue(send.bottom <= height - maxOf(navigationPx, ime) + 1f)
        assertEquals(send.height, compose.onNodeWithTag("play-send").fetchSemanticsNode().boundsInRoot.height, 1f)
        scrollTo("play-input").assert(hasText(draft))
        scrollTo("play-kind-dialogue").assertIsSelected()
        injectIme(0)
        scrollTo("play-input").assert(hasText(draft))
        scrollTo("play-kind-dialogue").assertIsSelected()
        compose.runOnIdle { assertSame(original, state.value); calls.assertQuiet() }

        val branch = checkNotNull(original.selectedStory).copy(branch = "fork")
        compose.runOnIdle { state.value = original.copy(selectedStory = branch) }
        compose.waitForIdle()
        compose.runOnIdle { retainedEdit(AnnotatedString("stale old-branch edit")) }
        injectIme(ime)
        scrollTo("play-input").assert(hasText(""))
        scrollTo("play-kind-action").assertIsSelected()
        scrollTo("play-send").assertIsNotEnabled()
        injectIme(0)
        compose.runOnIdle { assertEquals(branch, state.value.selectedStory); calls.assertQuiet() }
    }
}
