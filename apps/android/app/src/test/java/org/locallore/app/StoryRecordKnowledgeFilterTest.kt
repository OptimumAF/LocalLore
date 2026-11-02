/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Original native pages stay untouched; synthetic ports exercise only local UI ownership. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordKnowledgeFilterTest {
    private val dispatcher = StandardTestDispatcher()
    private val owners = ViewModelStore()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { owners.clear(); Dispatchers.resetMain() }

    private val context = StoryRecordContext(SavedStory("knowledge-ui", "main", "Synthetic", 12), 12)
    private val active get() = StoryRecordKnowledgeFilter.entries.filter { it.origin != null }
    private val origins = listOf("known_as_observed", "recorded_statement", "subjective_belief", "recorded_discovery")
    private val corpus: JSONObject by lazy {
        val bytes = checkNotNull(javaClass.getResourceAsStream("/story-record-knowledge-filters-v1.json"))
            .use { it.readBytes() }
        check(bytes.size in 1..128 * 1024) { "Native knowledge corpus must be bounded and present" }
        JSONObject(localText(bytes, 128 * 1024)).also { check(it.getInt("version") == 1) }
    }
    private fun objects(a: JSONArray): List<JSONObject> = (0 until a.length()).map(a::getJSONObject)
    private fun cases() = objects(corpus.getJSONArray("cases"))
    private fun filterRows(c: JSONObject) = objects(c.getJSONArray("filters"))
    private fun filter(c: JSONObject, origin: String?) = filterRows(c).single {
        if (origin == null) it.isNull("origin") else it.optString("origin") == origin
    }
    private fun pages(c: JSONObject, origin: String?) = objects(filter(c, origin).getJSONArray("pages"))
    private fun rows(c: JSONObject, origin: String?) = pages(c, origin).flatMap {
        objects(it.getJSONObject("page").getJSONArray("rows"))
    }
    private fun ctx(c: JSONObject): StoryRecordContext {
        val scope = c.getJSONObject("scope")
        return StoryRecordContext(SavedStory(scope.getString("story"), scope.getString("branch"),
            "Original native corpus", c.getLong("head")), c.getLong("head"))
    }
    private fun query(c: JSONObject, f: JSONObject, qp: JSONObject): StoryRecordQuery {
        val raw = qp.getJSONObject("query")
        val selected = if (f.isNull("origin")) StoryRecordKnowledgeFilter.ALL
            else active.single { it.origin!!.wire == f.getString("origin") }
        return StoryRecordQuery(ctx(c), StoryRecordSection.KNOWLEDGE,
            cursor = if (raw.isNull("cursor")) null else raw.getString("cursor"), knowledgeFilter = selected)
    }
    private fun sources(row: JSONObject) = objects(row.getJSONArray("sources"))
    private fun scoped(row: JSONObject): List<StoryRecordScopedEvent> = sources(row).filter {
        it.getString("kind") == "scoped_event"
    }.map {
        val value = it.getJSONObject("value")
        val original = value.getJSONObject("original_scope")
        StoryRecordScopedEvent(StoryRecordScope(original.getString("story"), original.getString("branch")),
            value.getLong("sequence"))
    }.distinct()
    private fun decoded(c: JSONObject, f: JSONObject, qp: JSONObject) =
        StoryRecordWire.decode(qp.getJSONObject("page"), query(c, f, qp), c.getString("player"))
    private fun envelope(q: StoryRecordQuery, rows: List<JSONObject>) = JSONObject()
        .put("version", q.version)
        .put("scope", JSONObject().put("story", q.context.story.story).put("branch", q.context.story.branch))
        .put("head", q.context.revision).put("revision", q.context.revision).put("story_time", 100L)
        .put("observer", JSONObject().put("kind", "player")).put("privacy", "player_visible")
        .put("status", "supported").put("view", q.section.wire).put("total", rows.size)
        .put("rows", JSONArray(rows)).put("next_cursor", JSONObject.NULL).put("unsupported", JSONArray())
    private fun invalid(q: StoryRecordQuery, page: JSONObject, player: String = "player") {
        try { StoryRecordWire.decode(page, q, player); fail("An incompatible query/row must refuse") }
        catch (failure: StoryRecordFailure) { assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem) }
    }
    private fun invalidCommand(q: StoryRecordQuery) {
        try { StoryRecordWire.command("synthetic-session", q); fail("Contradictory facets must not dispatch") }
        catch (failure: StoryRecordFailure) { assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem) }
    }
    private fun localQuery(filter: StoryRecordKnowledgeFilter = StoryRecordKnowledgeFilter.ALL) =
        StoryRecordQuery(context, StoryRecordSection.KNOWLEDGE, knowledgeFilter = filter)

    @Test fun localFacetAuthorityIsExactlyTheFourNativePlayerOriginsAndAll() {
        assertEquals(listOf("ALL", "OBSERVED", "STATEMENTS", "BELIEFS", "DISCOVERIES"),
            StoryRecordKnowledgeFilter.entries.map { it.name })
        assertEquals(listOf("All", "Known as observed", "Statements", "Beliefs", "Discoveries"),
            StoryRecordKnowledgeFilter.entries.map { it.label })
        assertNull(StoryRecordKnowledgeFilter.ALL.origin)
        assertEquals(origins, active.map { it.origin!!.wire })
        assertFalse(StoryRecordKnowledgeFilter.entries.any { it.origin == StoryRecordOrigin.CANONICAL_TRUTH })
        assertEquals(StoryRecordKnowledgeFilter.ALL, StoryRecordQuery(context).knowledgeFilter)
        assertEquals(StoryRecordKnowledgeFilter.ALL, StoryRecordState().knowledgeFilter)
    }

    @Test fun everyOriginalNativePageMatchesTheExactClosedWireQueryAndPreservesTypedEvidence() {
        assertEquals(setOf("parent", "corrected"), cases().map { it.getString("id") }.toSet())
        assertEquals(setOf(1, 2), cases().map { it.getInt("domain_version") }.toSet())
        for (c in cases()) {
            assertEquals(listOf(null) + origins, filterRows(c).map {
                if (it.isNull("origin")) null else it.getString("origin")
            })
            for (f in filterRows(c)) {
                var previous: String? = null
                val keys = mutableSetOf<String>()
                val qps = objects(f.getJSONArray("pages"))
                var count = 0
                for ((index, qp) in qps.withIndex()) {
                    val q = query(c, f, qp)
                    val rawQuery = qp.getJSONObject("query")
                    val command = StoryRecordWire.command("retained-session", q)
                    val actualQuery = command.getJSONObject("query")
                    assertEquals("inspection_query", command.getString("op"))
                    assertEquals(setOf("version", "scope", "expected_head", "at_revision", "observer",
                        "view", "cursor", "limit", "search"), actualQuery.keys().asSequence().toSet())
                    assertTrue("Original native query must match without a new JSON field", actualQuery.similar(rawQuery))
                    assertEquals(if (f.isNull("origin")) "" else "\"origin\":\"" + f.getString("origin") + "\"",
                        actualQuery.getString("search"))
                    assertEquals(previous, q.cursor)
                    val nativePage = qp.getJSONObject("page")
                    val before = nativePage.toString()
                    val page = decoded(c, f, qp)
                    assertEquals(before, nativePage.toString())
                    assertEquals(c.getLong("story_time"), page.storyTime)
                    assertEquals(nativePage.getInt("total"), page.total)
                    val rawRows = objects(nativePage.getJSONArray("rows"))
                    assertEquals(rawRows.size, page.entries.size)
                    for ((entry, raw) in page.entries.zip(rawRows)) {
                        assertEquals(raw.getString("key"), entry.key)
                        assertTrue(keys.add(entry.key))
                        assertEquals(raw.getString("origin"), entry.origin.wire)
                        assertEquals(raw.getString("text"), entry.text)
                        assertEquals(scoped(raw), entry.scopedEventSources)
                        assertTrue(entry.eventSources.isEmpty())
                        val confidence = if (raw.isNull("confidence")) null else raw.getString("confidence")
                        val subject = if (raw.isNull("subject")) null else raw.getString("subject")
                        assertEquals(listOfNotNull(raw.getString("id"), subject, confidence).joinToString(" \u00B7 "), entry.title)
                        if (entry.origin == StoryRecordOrigin.SUBJECTIVE_BELIEF) {
                            assertEquals("uncertain", confidence)
                            assertEquals(c.getString("player"), subject)
                            assertEquals(2, entry.scopedEventSources.size)
                        }
                        for (j in 0 until c.getJSONArray("forbidden").length())
                            assertFalse(raw.toString().contains(c.getJSONArray("forbidden").getString(j)))
                        if (!f.isNull("origin")) assertEquals(f.getString("origin"), entry.origin.wire)
                    }
                    previous = page.nextCursor
                    count += page.entries.size
                    if (index < qps.lastIndex) {
                        assertNotNull(previous); assertEquals(8, page.entries.size)
                    } else assertNull(previous)
                    assertEquals(nativePage.optString("next_cursor").takeUnless { nativePage.isNull("next_cursor") },
                        page.nextCursor)
                }
                assertEquals(qps.first().getJSONObject("page").getInt("total"), count)
            }
        }
    }

    @Test fun filteredNativePagesAreExactPartitionsOfAllRatherThanKotlinFilteredRecounts() {
        for (c in cases()) {
            val all = rows(c, null)
            val expectedCounts = if (c.getString("id") == "parent") listOf(22, 2, 10, 9, 1)
                else listOf(21, 2, 9, 9, 1)
            assertEquals(expectedCounts[0], all.size)
            val partitions = mutableSetOf<String>()
            for ((index, origin) in origins.withIndex()) {
                val actual = rows(c, origin)
                val expected = all.filter { it.getString("origin") == origin }
                assertEquals(expectedCounts[index + 1], actual.size)
                assertEquals(expected.map { it.getString("key") }, actual.map { it.getString("key") })
                for ((a, b) in actual.zip(expected)) assertTrue(a.similar(b))
                assertTrue(actual.all { partitions.add(it.getString("key")) })
            }
            assertEquals(all.map { it.getString("key") }.toSet(), partitions)
            assertEquals(listOf(8, 1), pages(c, "subjective_belief").map {
                it.getJSONObject("page").getJSONArray("rows").length()
            })
        }
    }

    @Test fun quotedOriginLikeProseDoesNotSpoofFacetsAndUnseenRetconKeepsOriginalObservation() {
        val parent = cases().single { it.getString("id") == "parent" }
        val child = cases().single { it.getString("id") == "corrected" }
        val quoted = rows(parent, "recorded_statement").first { it.getString("text").contains("\"origin\":") }
        for (origin in origins) assertTrue(quoted.getString("text").contains("\"origin\":\"" + origin + "\""))
        for (origin in origins.filter { it != "recorded_statement" })
            assertFalse(rows(parent, origin).any { it.getString("key") == quoted.getString("key") })
        for (c in listOf(parent, child)) {
            val observed = rows(c, "known_as_observed").single { it.getString("id") == "relic-location" }
            assertEquals("Tideglass lies in dry-well: SECRET-TIDE-731.", observed.getString("text"))
            assertEquals(listOf(StoryRecordScopedEvent(StoryRecordScope("quay", "main"), 20)), scoped(observed))
            val discovered = rows(c, "recorded_discovery").single()
            assertEquals(observed.getString("text"), discovered.getString("text"))
            assertEquals(scoped(observed), scoped(discovered))
            assertFalse(rows(c, null).any { it.getString("origin") == "canonical_truth" })
        }
        assertTrue(rows(parent, "recorded_statement").any {
            it.getString("text").contains("B86_PARENT_ONLY_STATEMENT_AFTER_FORK")
        })
        assertFalse(rows(child, null).any { it.toString().contains("B86_PARENT_ONLY_STATEMENT_AFTER_FORK") })
    }

    @Test fun otherwiseValidWrongOriginNativeRowsPassAllButRefuseEveryDifferentActiveFacet() {
        for (c in cases()) for (sourceOrigin in origins) {
            val raw = rows(c, sourceOrigin).first()
            val all = StoryRecordQuery(ctx(c), StoryRecordSection.KNOWLEDGE)
            val original = envelope(all, listOf(raw))
            val before = raw.toString()
            val admitted = StoryRecordWire.decode(original, all, c.getString("player")).entries.single()
            assertEquals(sourceOrigin, admitted.origin.wire)
            for (selected in active.filter { it.origin!!.wire != sourceOrigin }) {
                val q = all.copy(knowledgeFilter = selected)
                invalid(q, original, c.getString("player"))
            }
            assertEquals(before, raw.toString())
        }
    }

    @Test fun legacyAllCanonicalTruthCompatibilityIsKeptButQueryTwoTruthNeverBecomesAFacet() {
        val q1 = localQuery().copy(version = 1)
        val truth = JSONObject().put("kind", "knowledge").put("key", "legacy-truth")
            .put("origin", "canonical_truth").put("id", "legacy-fact").put("subject", JSONObject.NULL)
            .put("confidence", JSONObject.NULL).put("text", "Legacy player-visible world fact")
            .put("sources", JSONArray().put(JSONObject().put("kind", "seed").put("value", "legacy-seed")))
        assertEquals(StoryRecordOrigin.CANONICAL_TRUTH,
            StoryRecordWire.decode(envelope(q1, listOf(truth)), q1).entries.single().origin)
        val q2 = q1.copy(version = 2)
        invalid(q2, envelope(q2, listOf(truth)))
        for (f in active) invalid(q2.copy(knowledgeFilter = f), envelope(q2, listOf(truth)))
    }

    @Test fun activeFacetConflictsRefuseInsteadOfSilentlyChoosingAQueryWhileAllKeepsLiteralSearch() {
        for (f in active) {
            val q = localQuery(f)
            val bad = listOf(q.copy(version = 1), q.copy(search = "literal % _ words"),
                q.copy(promiseFilter = StoryRecordPromiseFilter.OPEN),
                q.copy(promiseFilter = StoryRecordPromiseFilter.OVERDUE),
                q.copy(relationshipTarget = StoryRecordRelationshipTarget("mira"))) +
                StoryRecordSection.entries.filter { it != StoryRecordSection.KNOWLEDGE }.map { q.copy(section = it) }
            for (value in bad) {
                invalidCommand(value)
                invalid(value, envelope(value, emptyList()))
            }
        }
        val text = "  Literal \"origin\":\"subjective_belief\" % _ \u65E5\u672C\u8A9E  "
        for (version in listOf(1, 2)) {
            val q = localQuery().copy(version = version, search = text)
            assertEquals(text, StoryRecordWire.command("s", q).getJSONObject("query").getString("search"))
        }
    }

    private fun answer(q: StoryRecordQuery): StoryRecordPage {
        val ref = StoryRecordScopedEvent(StoryRecordScope(q.context.story.story, q.context.story.branch), 2)
        if (q.section == StoryRecordSection.HISTORY && q.search.startsWith("\"event\":{")) {
            val event = StoryRecordEvent(2, "synthetic-turn", 10, ref.originalScope)
            return StoryRecordPage(q, 40, 1, listOf(StoryRecordEntry("event-2", "Observed event", "Read only",
                StoryRecordOrigin.RECORDED_OBSERVATION, listOf("Event #2"), event = event,
                scopedEventSources = listOf(ref))), null)
        }
        val origin = q.knowledgeFilter.origin ?: if (q.section == StoryRecordSection.KNOWLEDGE)
            StoryRecordOrigin.KNOWN_AS_OBSERVED else StoryRecordOrigin.CANONICAL_FIELD
        val total = if (q.knowledgeFilter == StoryRecordKnowledgeFilter.BELIEFS) 9 else 1
        val offset = if (q.cursor == null) 0 else { check(q.cursor == "facet-page-1"); 8 }
        val count = minOf(8, total - offset)
        return StoryRecordPage(q, 40, total, List(count) { index ->
            StoryRecordEntry("entry-" + (offset + index), "Visible row", "Synthetic read-only knowledge",
                origin, listOf("Synthetic source"), scopedEventSources = listOf(ref))
        }, if (offset + count < total) "facet-page-1" else null)
    }

    @Test fun controllerFirstNextRetryRetainFacetAndNativeCountsAndSelectionRestartsAtFirstPage() = runTest(dispatcher) {
        val calls = mutableListOf<StoryRecordQuery>(); var failNext = false
        val controller = StoryRecordController({ q ->
            calls += q
            if (failNext) { failNext = false; throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE) }
            answer(q)
        }, this)
        try {
            controller.open(context); advanceUntilIdle()
            controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); advanceUntilIdle()
            assertEquals(9, controller.state.value.total); assertEquals(8, controller.state.value.entries.size)
            assertEquals(StoryRecordKnowledgeFilter.BELIEFS, controller.state.value.knowledgeFilter)
            failNext = true; controller.next(); advanceUntilIdle()
            assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
            assertEquals("facet-page-1", controller.state.value.cursor)
            controller.retry(); advanceUntilIdle()
            assertEquals("facet-page-1", calls.last().cursor)
            assertEquals(StoryRecordKnowledgeFilter.BELIEFS, calls.last().knowledgeFilter)
            assertEquals(9, controller.state.value.total); assertEquals(1, controller.state.value.entries.size)
            controller.first(); advanceUntilIdle()
            assertNull(calls.last().cursor); assertEquals(StoryRecordKnowledgeFilter.BELIEFS, calls.last().knowledgeFilter)
            controller.next(); advanceUntilIdle()
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED); advanceUntilIdle()
            assertNull(calls.last().cursor); assertEquals(StoryRecordKnowledgeFilter.OBSERVED, calls.last().knowledgeFilter)
            assertEquals(StoryRecordKnowledgeFilter.OBSERVED, controller.state.value.knowledgeFilter)
            assertEquals(1, controller.state.value.total)
        } finally { controller.dispose() }
    }

    @Test fun controllerSearchAllFacetAndSectionReselectionHaveExplicitResetSemantics() = runTest(dispatcher) {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; answer(q) }, this)
        try {
            controller.open(context); advanceUntilIdle()
            val initial = calls.size
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); advanceUntilIdle()
            assertEquals(initial, calls.size)
            controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
            controller.search("literal words"); advanceUntilIdle()
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); advanceUntilIdle()
            assertEquals("", calls.last().search); assertEquals(StoryRecordKnowledgeFilter.BELIEFS, calls.last().knowledgeFilter)
            controller.search("a different literal"); advanceUntilIdle()
            assertEquals("a different literal", calls.last().search)
            assertEquals(StoryRecordKnowledgeFilter.ALL, calls.last().knowledgeFilter)
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.ALL); advanceUntilIdle()
            assertEquals("", calls.last().search)
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); advanceUntilIdle()
            controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
            assertEquals(StoryRecordKnowledgeFilter.ALL, calls.last().knowledgeFilter)
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); advanceUntilIdle()
            controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
            assertEquals(StoryRecordKnowledgeFilter.ALL, calls.last().knowledgeFilter)
            controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
            assertEquals(StoryRecordKnowledgeFilter.ALL, controller.state.value.knowledgeFilter)
        } finally { controller.dispose() }
    }

    @Test fun typedReaderCannotSmuggleAnOtherwiseWellFormedWrongOriginIntoAFilteredPage() = runTest(dispatcher) {
        for (selected in active) {
            val wrong = active.first { it != selected }.origin!!
            val controller = StoryRecordController({ q ->
                val positive = answer(q)
                if (q.knowledgeFilter == StoryRecordKnowledgeFilter.ALL) positive
                else positive.copy(entries = listOf(positive.entries.first().copy(origin = wrong)), total = 1, nextCursor = null)
            }, this)
            try {
                controller.open(context); advanceUntilIdle()
                controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
                assertNull(controller.state.value.problem)
                controller.knowledgeFilter(selected); advanceUntilIdle()
                assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
                assertTrue(controller.state.value.entries.isEmpty()); assertEquals(0, controller.state.value.total)
            } finally { controller.dispose() }
        }
    }

    @Test fun loadingOldFacetCompletionAndDisposedCallsCannotRetargetANewerContext() = runTest(dispatcher) {
        val release = CompletableDeferred<Unit>(); val calls = mutableListOf<StoryRecordQuery>(); var hold = false
        val controller = StoryRecordController({ q ->
            calls += q
            if (hold) { hold = false; withContext(NonCancellable) { release.await() } }
            answer(q)
        }, this)
        lateinit var fresh: StoryRecordState
        try {
            controller.open(context); advanceUntilIdle()
            controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
            hold = true; controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); runCurrent()
            val count = calls.size; assertTrue(controller.state.value.loading)
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED); runCurrent(); assertEquals(count, calls.size)
            val newer = context.copy(story = context.story.copy(branch = "other"))
            controller.open(newer); runCurrent()
            controller.select(StoryRecordSection.KNOWLEDGE); runCurrent()
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED); runCurrent()
            fresh = controller.state.value
            assertEquals(newer, fresh.context); assertEquals(StoryRecordKnowledgeFilter.OBSERVED, fresh.knowledgeFilter)
        } finally { release.complete(Unit); runCurrent() }
        assertSame(fresh, controller.state.value)
        controller.dismiss(); val closed = controller.state.value; val count = calls.size
        controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); runCurrent()
        assertSame(closed, controller.state.value); assertEquals(count, calls.size)
        controller.open(context); runCurrent(); controller.dispose()
        val disposed = controller.state.value
        controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); controller.open(context); runCurrent()
        assertSame(disposed, controller.state.value)
    }

    @Test fun scopedEventOpeningAndBackRetainFacetWithoutFilteringOrRetargetingTheEvidence() = runTest(dispatcher) {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; answer(q) }, this)
        try {
            controller.open(context); advanceUntilIdle()
            controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS); advanceUntilIdle()
            val before = controller.state.value; val ref = before.entries.first().scopedEventSources.single()
            controller.openScopedEvent(ref); advanceUntilIdle()
            assertEquals(StoryRecordKnowledgeFilter.ALL, calls.last().knowledgeFilter)
            assertEquals(StoryRecordSection.HISTORY, calls.last().section)
            assertEquals(ref.originalScope, controller.state.value.eventDetail!!.entry!!.event!!.originalScope)
            val count = calls.size
            controller.knowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED); advanceUntilIdle()
            assertEquals(count, calls.size)
            controller.back(); advanceUntilIdle()
            assertEquals(before, controller.state.value)
            assertEquals(StoryRecordKnowledgeFilter.BELIEFS, controller.state.value.knowledgeFilter)
        } finally { controller.dispose() }
    }

    private inner class ReaderGateway : DemoGateway {
        override val durable = true
        override val storyRecords = true
        val reads = mutableListOf<StoryRecordQuery>()
        private fun saved() = SavedSnapshot(context.revision, "You", emptyList(),
            "D:/synthetic/read-only-records", 1, listOf(context.story), context.story)
        override suspend fun initialize() = saved()
        override suspend fun snapshot() = saved()
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
            reads += query
            return answer(query)
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode) = DemoResult.Rejected("Unsupported")
    }

    @Test fun viewModelFacetCallbacksRequireExactCurrentRenderedViewIncludingEqualReopenAndClose() = runTest(dispatcher) {
        val gateway = ReaderGateway()
        val model = ShellViewModel(gateway); owners.put("knowledge-owner", model)
        advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
        model.recordSection(StoryRecordSection.KNOWLEDGE, model.storyRecord.value); advanceUntilIdle()
        val old = model.storyRecord.value
        model.recordKnowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS, old); advanceUntilIdle()
        assertEquals(StoryRecordKnowledgeFilter.BELIEFS, model.storyRecord.value.knowledgeFilter)
        val current = model.storyRecord.value; val reads = gateway.reads.size
        model.recordKnowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED, old)
        model.recordKnowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED, current.copy()); runCurrent()
        assertSame(current, model.storyRecord.value); assertEquals(reads, gateway.reads.size)
        model.closeStoryRecord(current)
        model.recordKnowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED, current); runCurrent()
        assertFalse(model.storyRecord.value.visible); assertEquals(reads, gateway.reads.size)
        model.openStoryRecord(); advanceUntilIdle()
        model.recordSection(StoryRecordSection.KNOWLEDGE, model.storyRecord.value); advanceUntilIdle()
        val reopened = model.storyRecord.value
        assertEquals(old, reopened); assertNotSame(old, reopened)
        val again = gateway.reads.size
        model.recordKnowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED, old); runCurrent()
        assertSame(reopened, model.storyRecord.value); assertEquals(again, gateway.reads.size)
        model.recordKnowledgeFilter(StoryRecordKnowledgeFilter.OBSERVED, reopened); advanceUntilIdle()
        assertEquals(StoryRecordKnowledgeFilter.OBSERVED, model.storyRecord.value.knowledgeFilter)
        val last = model.storyRecord.value; val finalReads = gateway.reads.size
        owners.clear()
        model.recordKnowledgeFilter(StoryRecordKnowledgeFilter.BELIEFS, last); runCurrent()
        assertEquals(finalReads, gateway.reads.size)
    }
}

