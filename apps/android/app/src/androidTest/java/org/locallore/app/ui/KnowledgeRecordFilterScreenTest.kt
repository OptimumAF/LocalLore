/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.referentialEqualityPolicy
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.*

/**
 * Actual dialog controls over inert supplied player-record states. Callback
 * counts establish UI delivery only, never native eligibility, totals, truth,
 * inference, a committed query, or accessibility-service/device acceptance.
 */
class KnowledgeRecordFilterScreenTest {
    @get:Rule val compose = createComposeRule()

    private class Calls {
        val filters = mutableListOf<StoryRecordKnowledgeFilter>()
        var closes = 0
        var other = 0
        fun snapshot() = Triple(filters.toList(), closes, other)
    }

    private fun show(
        state: MutableState<StoryRecordState>,
        calls: Calls,
        shown: MutableState<Boolean> = mutableStateOf(true),
        fontScale: Float = 1f,
    ) {
        compose.setContent {
            val deviceDensity = LocalDensity.current
            CompositionLocalProvider(LocalDensity provides Density(deviceDensity.density, fontScale)) {
                MaterialTheme {
                    val rendered = state.value
                    // Deliberately no controller/VM guard in these callbacks:
                    // stale-action refusal must come from the real dialog.
                    if (shown.value) StoryRecordDialog(
                        rendered,
                        onDismiss = { calls.closes++; shown.value = false },
                        onSection = { calls.other++ },
                        onSearch = { calls.other++ },
                        onNext = { calls.other++ },
                        onFirst = { calls.other++ },
                        onRetry = { calls.other++ },
                        onEvent = { calls.other++ },
                        onEventBack = { calls.other++ },
                        onEventRetry = { calls.other++ },
                        onScopedEvent = { calls.other++ },
                        onPromiseFilter = { calls.other++ },
                        onFocusRelationship = { calls.other++ },
                        onAllRelationships = { calls.other++ },
                        onKnowledgeFilter = { calls.filters += it },
                    )
                }
            }
        }
        compose.waitForIdle()
        compose.onNodeWithTag("story-record-dialog").assertIsDisplayed()
    }

    private fun facetTag(filter: StoryRecordKnowledgeFilter) =
        "story-record-knowledge-${filter.name.lowercase()}"

    private fun scroll(tag: String) = compose.onNodeWithTag(tag).performScrollTo()
    private fun facet(filter: StoryRecordKnowledgeFilter) = scroll(facetTag(filter))
    private fun close() = compose.onNodeWithTag("story-record-close")

    private fun retained(tag: String, scroll: Boolean = true): () -> Boolean {
        val node = if (scroll) this.scroll(tag) else compose.onNodeWithTag(tag)
        return checkNotNull(node.assertIsEnabled().fetchSemanticsNode().config[SemanticsActions.OnClick].action)
    }

    private fun replace(state: MutableState<StoryRecordState>, value: StoryRecordState) {
        compose.runOnIdle { state.value = value }
        compose.waitForIdle()
    }

    private fun quiet(
        state: MutableState<StoryRecordState>, expected: StoryRecordState, calls: Calls,
        vararg retained: () -> Boolean,
    ) {
        val before = compose.runOnIdle { calls.snapshot() }
        compose.runOnIdle { retained.forEach { it() } }
        compose.waitForIdle()
        compose.runOnIdle {
            assertSame(expected, state.value)
            assertEquals("A retained dialog action reached an unguarded callback", before, calls.snapshot())
        }
        compose.onNodeWithTag("story-record-dialog").assertIsDisplayed()
    }

    private fun assertNoTruthFacet() {
        compose.onNodeWithTag("story-record-knowledge-canonical_truth").assertDoesNotExist()
        compose.onNodeWithTag("story-record-knowledge-canonicaltruth").assertDoesNotExist()
        compose.onAllNodes(hasText("CanonicalTruth", substring = false)).assertCountEquals(0)
        compose.onAllNodes(hasText("Known world fact", substring = false)).assertCountEquals(0)
    }

    private fun assertInsideDialog(tag: String) {
        // Both bounds belong to the separate Dialog's actual window/root.
        // An activity Box or an assumed handset rectangle cannot bound Dialog.
        val dialog = compose.onNodeWithTag("story-record-dialog").fetchSemanticsNode().boundsInRoot
        val child = compose.onNodeWithTag(tag).assertIsDisplayed().fetchSemanticsNode().boundsInRoot
        assertTrue("$tag escaped the Dialog Surface horizontally", child.left >= dialog.left - 1f && child.right <= dialog.right + 1f)
        assertTrue("$tag escaped the Dialog Surface vertically", child.top >= dialog.top - 1f && child.bottom <= dialog.bottom + 1f)
    }

    private fun fullTextUnder(tag: String, text: String) {
        val matcher = hasAnyAncestor(hasTestTag(tag)) and hasText(text, substring = false)
        val node = compose.onNode(matcher, useUnmergedTree = true).assertIsDisplayed()
        node.performSemanticsAction(SemanticsActions.GetTextLayoutResult) { action ->
            val layouts = mutableListOf<TextLayoutResult>()
            assertTrue("Text supplied no layout result", action(layouts))
            assertTrue(layouts.isNotEmpty())
            layouts.forEach { result ->
                assertTrue(result.lineCount > 0)
                for (line in 0 until result.lineCount) assertFalse("Record text was ellipsized", result.isLineEllipsized(line))
                assertFalse("Record text overflowed its layout", result.hasVisualOverflow)
            }
        }
    }

    @Test fun exactlyFiveKnowledgeFacetsExposeLiteralLabelsSelectionAndFortyEightDpTargetsOnlyInKnowledge() {
        val original = knowledge(entries = emptyList())
        val state = mutableStateOf(original, referentialEqualityPolicy())
        val calls = Calls()
        show(state, calls)
        assertEquals(Labels.map { it.first }, StoryRecordKnowledgeFilter.entries.toList())
        val tags = SemanticsMatcher("Knowledge facet tags") { node ->
            node.config.contains(SemanticsProperties.TestTag) &&
                node.config[SemanticsProperties.TestTag].startsWith("story-record-knowledge-")
        }
        compose.onAllNodes(tags).assertCountEquals(5)
        for ((filter, label) in Labels) {
            val chip = facet(filter).assertIsEnabled().assert(hasText(label, substring = false)).assertHeightIsAtLeast(48.dp)
            if (filter == StoryRecordKnowledgeFilter.ALL) chip.assertIsSelected() else chip.assertIsNotSelected()
            assertInsideDialog(facetTag(filter))
        }
        assertNoTruthFacet()
        val beliefs = original.copy(knowledgeFilter = StoryRecordKnowledgeFilter.BELIEFS)
        replace(state, beliefs)
        facet(StoryRecordKnowledgeFilter.BELIEFS).assertIsSelected()
        facet(StoryRecordKnowledgeFilter.ALL).assertIsNotSelected()
        for (section in StoryRecordSection.entries.filter { it != StoryRecordSection.KNOWLEDGE }) {
            replace(state, original.copy(section = section))
            compose.onAllNodes(tags).assertCountEquals(0)
            compose.onNodeWithText("Knowledge record type").assertDoesNotExist()
        }
        compose.runOnIdle { assertEquals(Triple(emptyList<StoryRecordKnowledgeFilter>(), 0, 0), calls.snapshot()) }
    }

    @Test fun retainedRealFacetAndCloseActionsCannotRetargetDifferentOrEqualDistinctSuppliedViews() {
        val original = knowledge()
        val state = mutableStateOf(original, referentialEqualityPolicy())
        val calls = Calls()
        show(state, calls)
        val oldFacet = retained(facetTag(StoryRecordKnowledgeFilter.BELIEFS))
        val oldClose = retained("story-record-close", scroll = false)
        val other = original.copy(context = StoryRecordContext(B, 7), knowledgeFilter = StoryRecordKnowledgeFilter.OBSERVED)
        replace(state, other)
        quiet(state, other, calls, oldFacet, oldClose)
        val replacedFacet = retained(facetTag(StoryRecordKnowledgeFilter.STATEMENTS))
        val replacedClose = retained("story-record-close", scroll = false)
        val equal = other.copy()
        assertEquals(other, equal); assertNotSame(other, equal)
        replace(state, equal)
        quiet(state, equal, calls, oldFacet, oldClose, replacedFacet, replacedClose)
        facet(StoryRecordKnowledgeFilter.DISCOVERIES).assertIsEnabled().performClick()
        compose.runOnIdle {
            assertEquals(listOf(StoryRecordKnowledgeFilter.DISCOVERIES), calls.filters)
            assertSame("UI delivery must not invent a replacement record state", equal, state.value)
            assertEquals(0, calls.closes); assertEquals(0, calls.other)
        }
        // This is a coordinator-supplied projection, not a local row filter/reducer.
        replace(state, equal.copy(knowledgeFilter = StoryRecordKnowledgeFilter.DISCOVERIES))
        facet(StoryRecordKnowledgeFilter.DISCOVERIES).assertIsSelected()
        close().assertIsDisplayed().performClick()
        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(1, calls.closes) }
    }

    @Test fun removedAndRemountedSameStateCannotReviveOldFacetOrCloseButFreshActionsStillWork() {
        val original = knowledge()
        val state = mutableStateOf(original, referentialEqualityPolicy())
        val shown = mutableStateOf(true)
        val calls = Calls()
        show(state, calls, shown)
        val oldFacet = retained(facetTag(StoryRecordKnowledgeFilter.OBSERVED))
        val oldClose = retained("story-record-close", scroll = false)
        compose.runOnIdle { shown.value = false }
        compose.waitForIdle()
        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
        compose.runOnIdle { shown.value = true }
        compose.waitForIdle()
        compose.runOnIdle { assertSame(original, state.value) }
        quiet(state, original, calls, oldFacet, oldClose)
        compose.runOnIdle { assertTrue(shown.value) }
        facet(StoryRecordKnowledgeFilter.OBSERVED).assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(listOf(StoryRecordKnowledgeFilter.OBSERVED), calls.filters); assertEquals(0, calls.other) }
        close().assertIsDisplayed().performClick()
        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(1, calls.closes); assertFalse(shown.value) }
    }

    @Test fun doubledFontKeepsEveryFacetAndUnchangedOriginSourceAndCloseReachableInTheActualDialog() {
        val rows = (0 until 8).map { index ->
            val source = StoryRecordScopedEvent(StoryRecordScope(A.story, "main"), 7L + index)
            StoryRecordEntry("supplied-$index", "Supplied record $index · café 漢字 🌿",
                "Earlier player-visible account $index: the green gate appeared shut then. " +
                    "This retained account does not establish current world truth.",
                Origins[index % Origins.size], sources = listOf("Event #${source.sequence} · ${A.story} / main"),
                scopedEventSources = listOf(source))
        }
        val original = knowledge(entries = rows).copy(
            context = StoryRecordContext(A.copy(revision = 20), 20), storyTime = 20)
        val state = mutableStateOf(original, referentialEqualityPolicy())
        val calls = Calls()
        show(state, calls, fontScale = 2f)
        for ((filter, label) in Labels) {
            facet(filter).assertIsEnabled().assertHeightIsAtLeast(48.dp)
            assertInsideDialog(facetTag(filter)); fullTextUnder(facetTag(filter), label)
        }
        assertNoTruthFacet()
        for ((index, entry) in rows.withIndex()) {
            val tag = "story-record-entry-$index"
            scroll(tag)
            // Long rows may exceed the viewport: scroll each actual Text, not
            // a fabricated container rectangle, before checking its layout.
            val inside = hasAnyAncestor(hasTestTag(tag))
            for (text in listOf(entry.title, entry.origin.label, entry.text, "Sources · ${entry.sources.single()}")) {
                compose.onNode(inside and hasText(text, substring = false), useUnmergedTree = true).performScrollTo()
                fullTextUnder(tag, text)
            }
        }
        scroll("story-record-scoped-source-7-0").assertIsEnabled().assertHeightIsAtLeast(48.dp)
            .assert(hasText("Open event #14 · ${A.story} / main", substring = false)).performClick()
        close().assertIsDisplayed().assertHeightIsAtLeast(48.dp)
        assertInsideDialog("story-record-close")
        compose.runOnIdle { assertSame(original, state.value); assertTrue(calls.filters.isEmpty()); assertEquals(1, calls.other) }
        close().performClick()
        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(1, calls.closes) }
    }

    private companion object {
        val A = SavedStory("knowledge-ui-a", "main", "SCRIPTED supplied knowledge A", 7)
        val B = SavedStory("knowledge-ui-b", "fork", "SCRIPTED supplied knowledge B", 7)
        val Labels = listOf(
            StoryRecordKnowledgeFilter.ALL to "All",
            StoryRecordKnowledgeFilter.OBSERVED to "Known as observed",
            StoryRecordKnowledgeFilter.STATEMENTS to "Statements",
            StoryRecordKnowledgeFilter.BELIEFS to "Beliefs",
            StoryRecordKnowledgeFilter.DISCOVERIES to "Discoveries",
        )
        val Origins = listOf(StoryRecordOrigin.KNOWN_AS_OBSERVED, StoryRecordOrigin.RECORDED_STATEMENT,
            StoryRecordOrigin.SUBJECTIVE_BELIEF, StoryRecordOrigin.RECORDED_DISCOVERY)
        fun knowledge(entries: List<StoryRecordEntry> = emptyList()) = StoryRecordState(
            visible = true, context = StoryRecordContext(A, 7), section = StoryRecordSection.KNOWLEDGE,
            storyTime = 10, total = entries.size, entries = entries,
            knowledgeFilter = StoryRecordKnowledgeFilter.ALL,
        )
    }
}
