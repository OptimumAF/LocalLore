/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Fake-port draft/consent/ownership adversaries; Rust validates actual narration and canon. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryPresentationControllerTest {
    private val quay = StoryTemplateOption(DEFAULT_STORY_TEMPLATE, "Lantern Quay", "Original quay.", "fantasy_v1")
    private val harbor = StoryTemplateOption("bracken-harbor-v1", "Bracken Harbor", "Original harbor.", "narrative_v1")
    private fun preview(template: String, name: String?, settings: StoryPresentation?): StoryCreationPreview {
        val option = if (template == quay.template) quay else harbor
        val player = name ?: if (template == quay.template) "Rowan" else "Alex"
        return StoryCreationPreview(template, "a".repeat(64), option.defaultTitle, option.description, option.profile,
            listOf("Player: $player"), StoryPlayerSetup("a".repeat(64), "b".repeat(64), player), settings ?: StoryPresentation())
    }
    private data class Read(val template: String, val name: String?, val settings: StoryPresentation?)
    private inner class Gateway : StoryCreationGateway {
        val reads = mutableListOf<Read>()
        val creates = mutableListOf<StoryCreationRequest>()
        var legacyReads = 0
        var read: suspend (String, String?, StoryPresentation?) -> StoryCreationPreview? = { template, name, settings -> preview(template, name, settings) }
        var write: suspend (StoryCreationRequest) -> SavedSnapshot = { error("Synthetic uncertain write") }
        override suspend fun templates() = listOf(quay, harbor)
        override suspend fun preview(): StoryCreationPreview { legacyReads++; error("Unexpected legacy fallback") }
        override suspend fun setupPreview(template: String, playerName: String?): StoryCreationPreview? {
            legacyReads++; error("Unexpected setup fallback")
        }
        override suspend fun presentationPreview(template: String, playerName: String?, presentation: StoryPresentation?): StoryCreationPreview? {
            reads += Read(template, playerName, presentation)
            return read(template, playerName, presentation)
        }
        override suspend fun create(request: StoryCreationRequest): SavedSnapshot { creates += request; return write(request) }
    }

    @Test fun editsRevokeConsentUntilExactNameToneAndPhraseReview() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val original = controller.state.value.review!!
            controller.editTitle(original, "A retained title")
            controller.editTone(original, "warm")
            controller.editExcludedPhrases(original, "red fog\nstorm bell")
            controller.editPlayerName(original, "Marin")
            val dirty = controller.state.value.review!!
            assertNotSame(original, dirty)
            assertFalse(hasReviewedCreation(dirty, "Marin", "warm", "red fog\nstorm bell"))
            controller.confirm(original); controller.confirm(dirty); controller.reviewChanges(original)
            controller.reviewChanges(dirty.copy())
            controller.chooseTemplate(dirty, controller.state.value.templates[1])
            assertSame(dirty, controller.state.value.review)
            assertEquals(1, gateway.reads.size); assertTrue(gateway.creates.isEmpty())
            controller.reviewChanges(dirty)
            assertNull(controller.state.value.review); assertTrue(controller.state.value.busy)
            advanceUntilIdle()
            val reviewed = controller.state.value.review!!
            assertEquals(StoryPresentation("warm", listOf("red fog", "storm bell")), reviewed.preview.presentation)
            assertEquals("Marin", reviewed.preview.playerSetup!!.playerName)
            assertEquals(original.creationId, reviewed.creationId); assertEquals("A retained title", reviewed.title)
            assertEquals(0, gateway.legacyReads); assertTrue(gateway.creates.isEmpty())
            controller.confirm(dirty); assertTrue(gateway.creates.isEmpty())
            controller.confirm(reviewed); advanceUntilIdle()
            assertSame(reviewed, gateway.creates.single())
        } finally { controller.dispose() }
    }

    @Test fun invalidLiteralDraftsRemainVisibleAndCannotReviewCreateOrChangeStarter() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val rendered = controller.state.value.review!!
            val wave = String(Character.toChars(0x1f30a))
            for (invalid in listOf(" leading", "trailing ", "\n", "one\n", "one\n\ntwo", "nul\u0000", "x\u202e",
                "x\u2066", "\uD800", "n".repeat(65), wave.repeat(65), "echo\nECHO", "\u0130\ni\u0307",
                (1..9).joinToString("\n") { "phrase-$it" }, (1..5).joinToString("\n") { wave.repeat(63) + it })) {
                controller.editExcludedPhrases(rendered, invalid)
                val dirty = controller.state.value.review!!
                controller.reviewChanges(dirty); controller.confirm(dirty)
                controller.chooseTemplate(dirty, controller.state.value.templates[1])
                assertSame(dirty, controller.state.value.review)
                assertEquals(invalid, controller.state.value.excludedPhrasesDraft)
                assertEquals(1, gateway.reads.size); assertTrue(gateway.creates.isEmpty())
            }
            val exact = (0..3).map { wave.repeat(63) + String(Character.toChars(0x1f300 + it)) }
            assertEquals(1024, exact.sumOf { it.toByteArray(Charsets.UTF_8).size })
            assertTrue(validStoryPresentation(StoryPresentation("brisk", exact)))
            assertFalse(validStoryPresentation(StoryPresentation("brisk", exact + "z")))
            assertTrue(validStoryPresentation(StoryPresentation("plain", listOf("\u00df", "SS", "\u00e9", "e\u0301"))))
            controller.editTone(rendered, "UNKNOWN")
            assertEquals("plain", controller.state.value.toneDraft)
        } finally { controller.dispose() }
    }

    @Test fun reviewedSettingsCarryAcrossTemplatesButLegacyPortsRetainTheirOldCapability() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            controller.editTone(controller.state.value.review!!, "brisk")
            controller.editExcludedPhrases(controller.state.value.review!!, "glass rain")
            controller.reviewChanges(controller.state.value.review!!); advanceUntilIdle()
            controller.chooseTemplate(controller.state.value.review!!, controller.state.value.templates[1]); advanceUntilIdle()
            assertEquals(harbor.template, controller.state.value.review!!.preview.template)
            assertEquals("Alex", controller.state.value.playerNameDraft)
            assertEquals(StoryPresentation("brisk", listOf("glass rain")), controller.state.value.review!!.preview.presentation)
            assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
        for (withSetup in listOf(false, true)) {
            var legacyReads = 0
            val legacy = object : StoryCreationGateway {
                override suspend fun preview(): StoryCreationPreview {
                    legacyReads++
                    return this@StoryPresentationControllerTest.preview(quay.template, null, null).copy(presentation = null,
                        playerSetup = if (withSetup) StoryPlayerSetup("a".repeat(64), "b".repeat(64), "Rowan") else null)
                }
                override suspend fun setupPreview(template: String, playerName: String?): StoryCreationPreview? =
                    if (withSetup) preview() else null
                override suspend fun create(request: StoryCreationRequest): SavedSnapshot = error("No write expected")
            }
            val old = StoryCreationController(legacy, this) {}
            try {
                old.open(); advanceUntilIdle()
                assertEquals(1, legacyReads)
                assertNull(old.state.value.review!!.preview.presentation)
                assertNull(old.state.value.toneDraft); assertNull(old.state.value.excludedPhrasesDraft)
            } finally { old.dispose() }
        }
    }

    @Test fun cancelledNoncooperativePresentationReviewDrainsBeforeClosingWithoutPublishing() = runTest {
        val gateway = Gateway()
        val pending = CompletableDeferred<StoryCreationPreview>()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            controller.editTone(controller.state.value.review!!, "warm")
            val dirty = controller.state.value.review!!
            gateway.read = { _, _, _ -> withContext(NonCancellable) { pending.await() } }
            controller.reviewChanges(dirty); runCurrent()
            controller.dismiss(); controller.open(); runCurrent()
            assertTrue(controller.state.value.closing); assertTrue(closed.isEmpty())
            pending.complete(preview(quay.template, "Rowan", StoryPresentation("warm"))); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
            assertFalse(controller.state.value.visible); assertTrue(gateway.creates.isEmpty())
        } finally { pending.complete(preview(quay.template, "Rowan", StoryPresentation("warm"))); controller.dispose() }
    }

    @Test fun staleEditorsAndReviewTicketsCannotBorrowANewPreviewOrReopenedCreation() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val original = controller.state.value.review!!
            controller.editTone(original, "warm")
            val dirty = controller.state.value.review!!
            controller.reviewChanges(dirty); advanceUntilIdle()
            val current = controller.state.value.review!!
            controller.editTone(original, "brisk"); controller.editExcludedPhrases(original, "Wrong")
            controller.editPlayerName(original, "Wrong"); controller.reviewChanges(dirty); controller.confirm(original)
            assertSame(current, controller.state.value.review)
            controller.dismiss(); advanceUntilIdle(); controller.open(); advanceUntilIdle()
            val reopened = controller.state.value.review!!
            controller.editTone(current, "brisk"); controller.editExcludedPhrases(current, "Wrong"); controller.reviewChanges(current)
            assertSame(reopened, controller.state.value.review)
            assertNotEquals(current.creationId, reopened.creationId)
            assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun malformedOrMissingPresentationResultsNeverDowngradeToAnotherPort() = runTest {
        for (fault in listOf("tone", "phrases", "case", "name", "template", "missing", "lost", "error")) {
            val gateway = Gateway()
            val controller = StoryCreationController(gateway, this) {}
            try {
                controller.open(); advanceUntilIdle()
                controller.editExcludedPhrases(controller.state.value.review!!, "Red fog")
                gateway.read = { template, name, settings ->
                    val good = preview(template, name, settings)
                    when (fault) {
                        "tone" -> good.copy(presentation = settings!!.copy(tone = "warm"))
                        "phrases" -> good.copy(presentation = settings!!.copy(excludedPhrases = emptyList()))
                        "case" -> good.copy(presentation = settings!!.copy(excludedPhrases = listOf("red fog")))
                        "name" -> good.copy(playerSetup = good.playerSetup!!.copy(playerName = "Foreign"))
                        "template" -> preview(harbor.template, name, settings)
                        "missing" -> good.copy(presentation = null)
                        "lost" -> null
                        else -> error("PRIVATE_native_path")
                    }
                }
                controller.reviewChanges(controller.state.value.review!!); advanceUntilIdle()
                assertNull(fault, controller.state.value.review)
                assertEquals(0, gateway.legacyReads); assertTrue(gateway.creates.isEmpty())
                assertFalse(controller.state.value.notice!!.contains("PRIVATE"))
            } finally { controller.dispose() }
        }
    }

    @Test fun copiedPresentationListsCannotBeChangedThroughPortAliasesOrBorrowedRequests() = runTest {
        val gateway = Gateway()
        val phrases = mutableListOf("Red fog")
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            controller.editExcludedPhrases(controller.state.value.review!!, "Red fog")
            gateway.read = { template, name, settings ->
                try { (settings!!.excludedPhrases as MutableList<String>).add("Forbidden"); fail("Mutable borrowed settings") }
                catch (_: UnsupportedOperationException) {}
                preview(template, name, settings).copy(presentation = StoryPresentation("plain", phrases))
            }
            controller.reviewChanges(controller.state.value.review!!); advanceUntilIdle()
            val captured = controller.state.value.review!!.preview.presentation!!
            phrases[0] = "Changed source"
            assertEquals(listOf("Red fog"), captured.excludedPhrases)
            try { (captured.excludedPhrases as MutableList<String>).clear(); fail("Mutable captured settings") }
            catch (_: UnsupportedOperationException) {}
            assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun disposalAndDispatchedCreationFenceLatePresentationResultsAndEdits() = runTest {
        for (duringCreate in listOf(false, true)) {
            val gateway = Gateway()
            val read = CompletableDeferred<StoryCreationPreview>()
            val write = CompletableDeferred<SavedSnapshot>()
            val closed = mutableListOf<StoryCreationClose>()
            val controller = StoryCreationController(gateway, this, closed::add)
            val saved = SavedSnapshot(0, "Player", emptyList(), "synthetic", 1, emptyList(), null)
            try {
                controller.open(); advanceUntilIdle()
                controller.editTone(controller.state.value.review!!, "warm")
                if (!duringCreate) gateway.read = { _, _, _ -> withContext(NonCancellable) { read.await() } }
                controller.reviewChanges(controller.state.value.review!!); runCurrent()
                if (duringCreate) {
                    val reviewed = controller.state.value.review!!
                    gateway.write = { withContext(NonCancellable) { write.await() } }
                    controller.confirm(reviewed); controller.confirm(reviewed)
                    controller.editTone(reviewed, "brisk"); controller.editExcludedPhrases(reviewed, "Wrong")
                    runCurrent(); assertSame(reviewed, gateway.creates.single())
                }
                controller.dispose(); read.complete(preview(quay.template, "Rowan", StoryPresentation("warm")))
                write.complete(saved); advanceUntilIdle(); controller.open()
                assertFalse(controller.state.value.visible); assertTrue(closed.isEmpty())
                assertEquals(if (duringCreate) 1 else 0, gateway.creates.size)
            } finally { read.complete(preview(quay.template, "Rowan", StoryPresentation("warm"))); write.complete(saved); controller.dispose() }
        }
    }
}
