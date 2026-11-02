/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.nio.charset.CharacterCodingException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Real search admission and JSON/controller paths, with a synthetic read-only record port. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordSearchUnicodeTest {
    private val context = StoryRecordContext(SavedStory("unicode-search", "main", "Synthetic", 2), 2)
    private val malformed = listOf(
        "\uD800", "\uDC00", "x\uD800", "\uDC00x", "x\uD800y", "\uDC00\uD800",
        "\uD800\uD800", "\uD83D\uDE42\uD800", "a".repeat(255) + "\uD800",
    )
    private fun page(query: StoryRecordQuery, next: Boolean = false) = StoryRecordPage(
        query, 3, if (next) 2 else 1,
        listOf(StoryRecordEntry("name", "Name", "Player", StoryRecordOrigin.CANONICAL_FIELD, listOf("Seed - player"))),
        if (next) "cursor-1" else null, listOf("Synthetic page limitation"),
    )
    private fun wireText(text: String, version: Int = 2): String =
        StoryRecordWire.command(StoryRecordQuery(context, search = text, version = version), "synthetic-session")
            .getJSONObject("query").getString("search")

    @Test fun malformedSurrogatesAreRefusedWithoutSubstitutionOrAnEscapingException() {
        malformed.forEachIndexed { index, text ->
            try { localUtf8(text); fail("Fixture $index must contain malformed UTF-16") }
            catch (_: CharacterCodingException) { }
            assertFalse("Malformed UTF-16 case $index was admitted", validStoryRecordSearch(text))
        }
    }
    @Test fun malformedSearchIsBadSearchAtBothWireVersionsBeforeACommandIsReturned() {
        for (version in listOf(1, 2)) for (text in malformed) {
            try { wireText(text, version); fail("Malformed search reached a wire command") }
            catch (error: StoryRecordFailure) { assertEquals(StoryRecordProblem.BAD_SEARCH, error.problem) }
        }
    }
    @Test fun malformedSearchClearsOldPageWithoutDispatchAndAFreshValidSearchRecovers() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ query -> calls += query; page(query, next = calls.size == 1) }, this)
        controller.open(context); advanceUntilIdle()
        assertFalse(controller.state.value.entries.isEmpty()); assertNotNull(controller.state.value.nextCursor)
        assertFalse(controller.state.value.limitations.isEmpty())
        for (text in malformed) {
            controller.search(text); advanceUntilIdle()
            val rejected = controller.state.value
            assertEquals(StoryRecordProblem.BAD_SEARCH, rejected.problem)
            assertFalse(rejected.loading); assertTrue(rejected.visible); assertEquals(context, rejected.context)
            assertEquals(text, rejected.search); assertTrue(rejected.entries.isEmpty()); assertEquals(0, rejected.total)
            assertNull(rejected.cursor); assertNull(rejected.nextCursor); assertNull(rejected.storyTime)
            assertTrue(rejected.limitations.isEmpty()); assertEquals(1, calls.size)
        }
        val valid = "\u65E5\u672C\u8A9E \uD83D\uDE42 e\u0301"
        controller.search(valid); advanceUntilIdle()
        assertEquals(2, calls.size); assertEquals(valid, calls.last().search)
        assertNull(controller.state.value.problem); assertFalse(controller.state.value.entries.isEmpty())
        controller.dispose()
    }
    @Test fun exactUtf8ByteBoundariesPreserveSupplementaryAndCombiningCharacters() {
        val boundaries = listOf(
            "a".repeat(256) to "a".repeat(257),
            "\u00E9".repeat(128) to "\u00E9".repeat(129),
            "\uD83D\uDE42".repeat(64) to ("\uD83D\uDE42".repeat(64) + "a"),
            ("e\u0301".repeat(85) + "a") to ("e\u0301".repeat(85) + "ab"),
        )
        for ((accepted, rejected) in boundaries) {
            assertEquals(256, localUtf8(accepted).size); assertTrue(localUtf8(rejected).size > 256)
            assertTrue(validStoryRecordSearch(accepted)); assertEquals(accepted, wireText(accepted))
            assertFalse(validStoryRecordSearch(rejected))
            try { wireText(rejected); fail("Oversized search reached a wire command") }
            catch (error: StoryRecordFailure) { assertEquals(StoryRecordProblem.BAD_SEARCH, error.problem) }
        }
    }
    @Test fun validLiteralsStayExactWithoutTrimmingNormalizingOrInterpretingEscapeSpellings() = runTest {
        val texts = listOf("", "  MiXeD % _ ' \" \\  ", "\\uD800", "\u00E9", "e\u0301",
            "\u65E5\u672C\u8A9E", "\uD83D\uDE42", "line\u2028separator\u2029")
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ query -> calls += query; page(query) }, this)
        controller.open(context); advanceUntilIdle(); calls.clear()
        for (text in texts) {
            assertTrue(validStoryRecordSearch(text))
            for (version in listOf(1, 2)) assertEquals(text, wireText(text, version))
            controller.search(text); advanceUntilIdle()
            assertEquals(text, calls.last().search); assertEquals(text, controller.state.value.search)
            assertNull(controller.state.value.problem)
        }
        assertEquals(texts, calls.map { it.search }); controller.dispose()
    }
    @Test fun existingIsoControlAndEmptySearchRulesAreUnchanged() {
        assertTrue(validStoryRecordSearch("")); assertEquals("", wireText(""))
        for (control in listOf('\u0000', '\t', '\n', '\u001F', '\u007F', '\u0085', '\u009F')) {
            val text = "before${control}after"
            assertFalse(validStoryRecordSearch(text))
            try { wireText(text); fail("Control character reached a wire command") }
            catch (error: StoryRecordFailure) { assertEquals(StoryRecordProblem.BAD_SEARCH, error.problem) }
        }
    }
    @Test fun aLateNonCooperativeOldScopeReadCannotReplaceTheNewScopeBadSearchState() = runTest {
        val old = context.copy(story = context.story.copy(story = "old-search"))
        val gate = CompletableDeferred<Unit>(); val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ query ->
            calls += query
            if (query.context == old) withContext(NonCancellable) { gate.await() }
            page(query)
        }, this)
        lateinit var rejected: StoryRecordState
        try {
            controller.open(old); runCurrent(); assertTrue(controller.state.value.loading)
            controller.open(context); runCurrent(); assertFalse(controller.state.value.loading)
            controller.search("\uD800"); runCurrent(); rejected = controller.state.value
            assertEquals(StoryRecordProblem.BAD_SEARCH, rejected.problem); assertEquals(context, rejected.context)
            assertEquals(listOf(old, context), calls.map { it.context }); assertTrue(rejected.entries.isEmpty())
        } finally { gate.complete(Unit); runCurrent() }
        assertSame(rejected, controller.state.value)
        controller.search("fresh \uD83D\uDE42"); advanceUntilIdle()
        assertEquals(3, calls.size); assertEquals("fresh \uD83D\uDE42", calls.last().search)
        assertNull(controller.state.value.problem); controller.dispose()
    }
    @Test fun loadingAndDisposedControlsStillIgnoreEditsWithoutDispatchingThem() = runTest {
        val gate = CompletableDeferred<Unit>(); var calls = 0
        val controller = StoryRecordController({ query -> calls++; withContext(NonCancellable) { gate.await() }; page(query) }, this)
        lateinit var hidden: StoryRecordState
        try {
            controller.open(context); runCurrent(); val loading = controller.state.value
            controller.search("\uD800"); controller.search("valid"); runCurrent()
            assertSame(loading, controller.state.value); assertEquals(1, calls)
            controller.dispose(); hidden = controller.state.value
            controller.search("\uD800"); controller.search("valid"); controller.open(context)
            assertSame(hidden, controller.state.value); assertFalse(hidden.visible); assertEquals(1, calls)
        } finally { gate.complete(Unit); runCurrent() }
        assertSame(hidden, controller.state.value); assertEquals(1, calls)
    }
    @Test fun aValidUnicodeReaderFailureKeepsItsExistingGenericClassification() = runTest {
        val privateFailure = "SYNTHETIC_PRIVATE_READER_DETAIL"
        val controller = StoryRecordController({ query ->
            if (query.search.isNotEmpty()) throw IllegalStateException(privateFailure)
            page(query)
        }, this)
        controller.open(context); advanceUntilIdle()
        controller.search("\uD83D\uDE42"); advanceUntilIdle()
        assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
        assertFalse(controller.state.value.toString().contains(privateFailure))
        controller.search(""); advanceUntilIdle(); assertNull(controller.state.value.problem)
        controller.dispose()
    }
}
