/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Original display/read-fence oracles. Native corpus capture is a setup prerequisite, not a verdict stub. */
@OptIn(ExperimentalCoroutinesApi::class)
class Query2StoryRecordTest {
    private val context = StoryRecordContext(SavedStory("survey-story", "child", "Synthetic survey", 8), 8)
    private val oldFact = "The survey beacon flashes amber at the north pier."
    private val newFact = "The survey beacon flashes violet at the north pier."
    private fun query(section: StoryRecordSection, version: Int = 2) = StoryRecordQuery(context, section, version = version)
    private fun scope(story: String = context.story.story, branch: String = "ancestor") = JSONObject().put("story", story).put("branch", branch)
    private fun scoped(sequence: Any = 3L, story: String = context.story.story, branch: String = "ancestor") =
        JSONObject().put("kind", "scoped_event").put("value", JSONObject().put("original_scope", scope(story, branch)).put("sequence", sequence))
    private fun field(source: JSONObject = scoped()) = JSONObject().put("kind", "field").put("key", "energy")
        .put("origin", "canonical_field").put("actor", "player").put("field", "Energy")
        .put("value", JSONObject().put("type", "number").put("value", 3L)).put("source", source)
    private fun relationship(source: JSONObject = scoped()) = JSONObject().put("kind", "relationship").put("key", "mira-trust")
        .put("origin", "canonical_field").put("from", "player").put("to", "mira").put("dimension", "trust").put("value", 1L).put("source", source)
    private fun knowledge(source: JSONObject = scoped()) = JSONObject().put("kind", "knowledge").put("key", "known-beacon")
        .put("origin", "known_as_observed").put("id", "relic-location").put("subject", "player").put("confidence", JSONObject.NULL)
        .put("text", oldFact).put("sources", JSONArray().put(source))
    private fun message() = JSONObject().put("kind", "scoped_message").put("key", "message-ancestor")
        .put("origin", "recorded_message").put("original_scope", scope()).put("turn", "survey-turn")
        .put("message_kind", "narration").put("text", "The recorded survey continues.").put("event_ids", JSONArray().put(2L).put(5L))
    private fun marker(revision: Any = 4L) = JSONObject().put("kind", "author_correction").put("revision", revision)
    private fun event(reference: StoryRecordScopedEvent) = JSONObject().put("kind", "event").put("key", "event-${reference.sequence}")
        .put("origin", "recorded_observation").put("event", JSONObject().put("sequence", reference.sequence)
            .put("scope", scope(reference.originalScope.story, reference.originalScope.branch)).put("turn", "survey-turn").put("story_time", 90L)
            .put("participants", JSONArray().put("player")).put("witnesses", JSONArray().put("player"))
            .put("consequence", JSONObject().put("effect", "time_advanced").put("from", 89L).put("to", 90L)))
    private fun page(q: StoryRecordQuery, rows: List<JSONObject>, total: Int = rows.size, next: String? = null) = JSONObject()
        .put("version", q.version).put("scope", scope(q.context.story.story, q.context.story.branch))
        .put("head", q.context.revision).put("revision", q.context.revision).put("story_time", 100L)
        .put("observer", JSONObject().put("kind", "player")).put("privacy", "player_visible").put("status", "supported")
        .put("view", q.section.wire).put("total", total).put("rows", JSONArray(rows)).put("next_cursor", next ?: JSONObject.NULL).put("unsupported", JSONArray())
    private fun copy(value: JSONObject) = JSONObject(value.toString())
    private fun required(data: JSONObject, q: StoryRecordQuery): StoryRecordPage = try {
        StoryRecordWire.decode(data, q)
    } catch (failure: StoryRecordFailure) {
        throw AssertionError("The fixed player adapter must decode this valid Query${q.version} ${q.section.wire} page", failure)
    }
    private fun invalid(data: JSONObject, q: StoryRecordQuery) {
        try { StoryRecordWire.decode(data, q); fail("Malformed or cross-version record must refuse") }
        catch (failure: StoryRecordFailure) { assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem) }
    }
    private fun invalidCommand(q: StoryRecordQuery) {
        try { StoryRecordWire.command("same-session", q); fail("Invalid query version/cursor must refuse") }
        catch (failure: StoryRecordFailure) { assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem) }
    }
    private fun objects(array: JSONArray): List<JSONObject> = (0 until array.length()).map(array::getJSONObject)
    private val corpus: JSONObject by lazy {
        val stream = checkNotNull(javaClass.getResourceAsStream("/story-record-query2-v1.json")) {
            "SETUP: Root must capture the frozen native Query2 corpus before this cohort"
        }
        val bytes = stream.use { it.readBytes() }
        check(bytes.size <= 128 * 1024) { "SETUP: native corpus exceeds frozen cap" }
        JSONObject(bytes.toString(Charsets.UTF_8)).also { assertEquals(1, it.getInt("version")) }
    }
    private fun nativeCase(id: String) = objects(corpus.getJSONArray("cases")).single { it.getString("id") == id }
    private fun nativeQuery(case: JSONObject, raw: JSONObject): StoryRecordQuery {
        val current = case.getJSONObject("scope")
        val context = StoryRecordContext(SavedStory(current.getString("story"), current.getString("branch"), "Captured native fixture", case.getLong("head")), case.getLong("head"))
        val q = raw.getJSONObject("query")
        assertEquals(2, q.getInt("version")); assertEquals(8, q.getInt("limit")); assertEquals("player", q.getJSONObject("observer").getString("kind"))
        assertTrue(q.isNull("at_revision")); assertEquals(context.revision, q.getLong("expected_head"))
        assertEquals(context.story.story, q.getJSONObject("scope").getString("story")); assertEquals(context.story.branch, q.getJSONObject("scope").getString("branch"))
        return StoryRecordQuery(context, StoryRecordSection.entries.single { it.wire == q.getString("view") }, q.getString("search"),
            if (q.isNull("cursor")) null else q.getString("cursor"), version = 2)
    }
    private fun reference(value: JSONObject) = StoryRecordScopedEvent(
        StoryRecordScope(value.getJSONObject("original_scope").getString("story"), value.getJSONObject("original_scope").getString("branch")), value.getLong("sequence"))
    private fun rawReferences(row: JSONObject): List<StoryRecordScopedEvent> = when (row.getString("kind")) {
        "field", "relationship" -> row.getJSONObject("source").let { if (it.getString("kind") == "scoped_event") listOf(reference(it.getJSONObject("value"))) else emptyList() }
        "knowledge", "promise" -> objects(row.getJSONArray("sources")).filter { it.getString("kind") == "scoped_event" }.map { reference(it.getJSONObject("value")) }.distinct()
        "scoped_message" -> row.getJSONObject("original_scope").let { original ->
            val ids = row.getJSONArray("event_ids")
            (0 until ids.length()).map { StoryRecordScopedEvent(StoryRecordScope(original.getString("story"), original.getString("branch")), ids.getLong(it)) }
        }
        "event" -> row.getJSONObject("event").let { event ->
            val original = event.getJSONObject("scope")
            listOf(StoryRecordScopedEvent(StoryRecordScope(original.getString("story"), original.getString("branch")), event.getLong("sequence")))
        }
        else -> emptyList()
    }
    private fun observed(case: JSONObject): StoryRecordEntry {
        val found = objects(case.getJSONArray("pages")).filter { it.getJSONObject("query").getString("view") == "knowledge" }.flatMap { raw ->
            val q = nativeQuery(case, raw)
            val rows = objects(raw.getJSONObject("page").getJSONArray("rows"))
            val decoded = required(raw.getJSONObject("page"), q)
            rows.indices.filter { rows[it].getString("kind") == "knowledge" && rows[it].getString("id") == "relic-location" && rows[it].getString("origin") == "known_as_observed" }
                .map { decoded.entries[it] }
        }
        return found.single()
    }

    @Test fun allFiveDefaultsUseQuery2WhileExplicitLegacyPlayerQueriesRemainVersion1() {
        for (section in StoryRecordSection.entries) {
            val q = StoryRecordQuery(context, section)
            assertEquals("Default for ${section.wire}", 2, q.version)
            val wire = StoryRecordWire.command("bound-session", q).getJSONObject("query")
            assertEquals(2, wire.getInt("version")); assertEquals(section.wire, wire.getString("view")); assertEquals(8, wire.getInt("limit"))
            assertEquals(setOf("kind"), wire.getJSONObject("observer").keys().asSequence().toSet())
            assertEquals("player", wire.getJSONObject("observer").getString("kind")); assertEquals(8L, wire.getLong("expected_head"))
            assertEquals("child", wire.getJSONObject("scope").getString("branch")); assertTrue(wire.isNull("at_revision"))
            if (section != StoryRecordSection.PROMISES) {
                val legacy = q.copy(version = 1)
                assertEquals(1, StoryRecordWire.command("same-session", legacy).getJSONObject("query").getInt("version"))
            } else invalidCommand(q.copy(version = 1))
        }
    }

    @Test fun everyCapturedNativePageDecodesWithoutSkippingRowsFlatteningScopeOrLeakingForbiddenText() {
        val cases = objects(corpus.getJSONArray("cases"))
        assertTrue(cases.map { it.getString("id") }.containsAll(listOf("root", "corrected", "rediscovered")))
        for (case in cases) for (section in StoryRecordSection.entries) {
            val pages = objects(case.getJSONArray("pages")).filter { it.getJSONObject("query").getString("view") == section.wire }
            assertTrue("Captured view ${section.wire} is required", pages.isNotEmpty())
            var cursor: String? = null
            var count = 0
            var total: Int? = null
            val keys = mutableSetOf<String>()
            for (raw in pages) {
                val q = nativeQuery(case, raw); assertEquals(cursor, q.cursor)
                val data = raw.getJSONObject("page"); val decoded = required(data, q)
                assertEquals(case.getLong("story_time"), decoded.storyTime)
                if (total == null) total = decoded.total else assertEquals(total, decoded.total)
                val rows = objects(data.getJSONArray("rows")); assertEquals(rows.size, decoded.entries.size)
                decoded.entries.forEachIndexed { index, entry ->
                    assertTrue("No duplicate across native pages", keys.add(entry.key))
                    assertTrue(entry.eventSources.isEmpty())
                    assertEquals(rawReferences(rows[index]), entry.scopedEventSources)
                }
                val display = decoded.entries.joinToString("\n") { "${it.title}\n${it.text}\n${it.sources}" }
                val forbidden = case.getJSONArray("forbidden")
                for (i in 0 until forbidden.length()) {
                    val secret = forbidden.getString(i)
                    assertFalse(data.toString().contains(secret)); assertFalse(display.contains(secret))
                }
                count += decoded.entries.size; cursor = decoded.nextCursor
            }
            assertNull(cursor); assertEquals(total, count)
        }
    }

    @Test fun nativeUnseenCorrectionPreservesKnownObservationUntilAnActualRediscovery() {
        val root = nativeCase("root"); val corrected = nativeCase("corrected"); val rediscovered = nativeCase("rediscovered")
        assertEquals(1, root.getInt("domain_version")); assertEquals(2, corrected.getInt("domain_version")); assertEquals(2, rediscovered.getInt("domain_version"))
        val before = observed(root); val remembered = observed(corrected); val updated = observed(rediscovered)
        assertEquals(oldFact, before.text); assertEquals(oldFact, remembered.text); assertEquals(newFact, updated.text)
        for (entry in listOf(before, remembered, updated)) {
            assertEquals("known_as_observed", entry.origin.wire); assertEquals("Known as observed", entry.origin.label)
            assertTrue(entry.eventSources.isEmpty()); assertEquals(1, entry.scopedEventSources.size)
        }
        assertEquals(before.scopedEventSources, remembered.scopedEventSources)
        assertEquals(root.getJSONObject("scope").getString("branch"), remembered.scopedEventSources.single().originalScope.branch)
        assertEquals(rediscovered.getJSONObject("scope").getString("branch"), updated.scopedEventSources.single().originalScope.branch)
        assertTrue(updated.scopedEventSources.single().sequence > corrected.getLong("head"))
    }

    @Test fun exactPrivateCorrectionMarkerHasNoEventOrNavigationAuthority() = runTest {
        val q = query(StoryRecordSection.HISTORY)
        val entry = required(page(q, listOf(marker())), q).entries.single()
        assertEquals("author-correction:4", entry.key); assertEquals("History correction", entry.title)
        assertEquals("History was corrected at revision #4. This marker is not a witnessed event.", entry.text)
        assertEquals("author_correction", entry.origin.wire); assertEquals("History correction", entry.origin.label)
        assertTrue(entry.sources.isEmpty()); assertTrue(entry.eventSources.isEmpty()); assertTrue(entry.scopedEventSources.isEmpty()); assertNull(entry.event)
        for (name in listOf("key", "origin", "reason", "operation", "receipt", "source")) invalid(page(q, listOf(marker().put(name, "PRIVATE_AUTHOR_PAYLOAD"))), q)
        for (revision in listOf<Any>(0, -1, 9, true, 1.5, "4")) invalid(page(q, listOf(marker(revision))), q)
        invalid(page(q.copy(version = 1), listOf(marker())), q.copy(version = 1))
        invalid(page(query(StoryRecordSection.KNOWLEDGE), listOf(marker())), query(StoryRecordSection.KNOWLEDGE))
        val reads = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ actual ->
            reads += actual
            required(page(actual, if (actual.section == StoryRecordSection.HISTORY) listOf(marker()) else emptyList()), actual)
        }, this)
        controller.open(context); advanceUntilIdle(); controller.select(StoryRecordSection.HISTORY); advanceUntilIdle()
        assertEquals("author_correction", controller.state.value.entries.single().origin.wire)
        val prior = reads.toList(); controller.openEvent(4); controller.openScopedEvent(StoryRecordScopedEvent(StoryRecordScope(context.story.story, context.story.branch), 4)); advanceUntilIdle()
        assertEquals(prior, reads); assertNull(controller.state.value.eventDetail); controller.dispose()
    }

    @Test fun scopedMessagesRetainOriginalScopeAndOrderedIdsWhileLegacyMessagesStayExplicitV1() {
        val q = query(StoryRecordSection.HISTORY)
        for (kind in listOf("original_input", "narration")) {
            val raw = message().put("message_kind", kind)
            val entry = required(page(q, listOf(raw)), q).entries.single()
            assertEquals(if (kind == "original_input") "Recorded player input" else "Recorded narration", entry.title)
            assertEquals("recorded_message", entry.origin.wire); assertTrue(entry.eventSources.isEmpty()); assertNull(entry.event)
            assertEquals(listOf(2L, 5L).map { StoryRecordScopedEvent(StoryRecordScope("survey-story", "ancestor"), it) }, entry.scopedEventSources)
            assertEquals(listOf("Event #2 · survey-story / ancestor", "Event #5 · survey-story / ancestor"), entry.sources)
        }
        for (ids in listOf(JSONArray(), JSONArray().put(2).put(2), JSONArray().put(5).put(2), JSONArray().put(0), JSONArray().put(9), JSONArray().put(true), JSONArray().put(2.5)))
            invalid(page(q, listOf(message().put("event_ids", ids))), q)
        invalid(page(q, listOf(message().put("original_scope", scope("another-story")))), q)
        invalid(page(q, listOf(message().put("turn", "bad/turn"))), q)
        invalid(page(q, listOf(message().put("message_kind", "world_truth"))), q)
        invalid(page(q.copy(version = 1), listOf(message())), q.copy(version = 1))
        val legacy = message().put("kind", "message").also { it.remove("original_scope") }
        invalid(page(q, listOf(legacy)), q)
        val v1 = q.copy(version = 1); val old = required(page(v1, listOf(legacy)), v1).entries.single()
        assertEquals(listOf(2L, 5L), old.eventSources); assertTrue(old.scopedEventSources.isEmpty())
    }

    @Test fun progressionRelationshipsAndObservedKnowledgeAcceptOnlyVersionedTypedSourcesAndPlayerSubjects() {
        val rows = listOf(StoryRecordSection.PROGRESSION to field(), StoryRecordSection.RELATIONSHIPS to relationship(), StoryRecordSection.KNOWLEDGE to knowledge())
        for ((section, row) in rows) {
            val q = query(section); val entry = required(page(q, listOf(row)), q).entries.single()
            assertEquals(listOf(StoryRecordScopedEvent(StoryRecordScope("survey-story", "ancestor"), 3)), entry.scopedEventSources)
            assertEquals(listOf("Event #3 · survey-story / ancestor"), entry.sources); assertTrue(entry.eventSources.isEmpty())
            for (bad in listOf(
                JSONObject().put("kind", "event").put("value", 3), scoped(true), scoped(3.5), scoped(0), scoped(9),
                scoped(story = "foreign"), scoped(branch = "bad/branch"), scoped().also { it.getJSONObject("value").put("extra", true) },
            )) {
                val broken = copy(row)
                if (section == StoryRecordSection.KNOWLEDGE) broken.put("sources", JSONArray().put(bad)) else broken.put("source", bad)
                invalid(page(q, listOf(broken)), q)
            }
            for (safe in listOf(JSONObject().put("kind", "seed").put("value", "synthetic-seed"), JSONObject().put("kind", "withheld"))) {
                val safeRow = copy(row)
                if (section == StoryRecordSection.KNOWLEDGE) safeRow.put("sources", JSONArray().put(safe)) else safeRow.put("source", safe)
                assertTrue(required(page(q, listOf(safeRow)), q).entries.single().scopedEventSources.isEmpty())
            }
        }
        val q = query(StoryRecordSection.KNOWLEDGE)
        for (bad in listOf(knowledge().put("subject", JSONObject.NULL), knowledge().put("subject", "mira"), knowledge().put("confidence", "believed"),
            knowledge().put("origin", "canonical_truth").put("subject", JSONObject.NULL))) invalid(page(q, listOf(bad)), q)
        invalid(page(q.copy(version = 1), listOf(knowledge())), q.copy(version = 1))
        val belief = knowledge().put("origin", "subjective_belief").put("confidence", "suspected")
        assertEquals("subjective_belief", required(page(q, listOf(belief)), q).entries.single().origin.wire)
        invalid(page(q, listOf(copy(belief).put("confidence", JSONObject.NULL))), q)
        invalid(page(q, listOf(copy(belief).put("confidence", "established_truth"))), q)
        invalid(page(q, listOf(copy(belief).put("subject", "mira"))), q)
        val legacy = knowledge(JSONObject().put("kind", "event").put("value", 3)).put("origin", "canonical_truth").put("subject", JSONObject.NULL)
        val v1 = q.copy(version = 1); assertEquals("canonical_truth", required(page(v1, listOf(legacy)), v1).entries.single().origin.wire)
    }

    @Test fun versionedCursorAndPageFramesRefuseCrossVersionTypesAndFrozenContextDrift() {
        val q = query(StoryRecordSection.HISTORY); val raw = message()
        val next = "2:1:${"a".repeat(64)}"
        assertEquals(next, required(page(q, listOf(raw), 2, next), q).nextCursor)
        for (cursor in listOf("1:1:${"a".repeat(64)}", "2:0:${"a".repeat(64)}", "2:1:bad", "3:1:${"a".repeat(64)}")) {
            invalid(page(q, listOf(raw), 2, cursor), q); invalidCommand(q.copy(cursor = cursor))
        }
        for (mutate in listOf<(JSONObject) -> Unit>(
            { it.put("version", 1) }, { it.put("version", true) }, { it.put("head", 9L) }, { it.put("revision", 7L) },
            { it.getJSONObject("scope").put("branch", "other") }, { it.put("observer", JSONObject().put("kind", "omniscient")) },
            { it.put("privacy", "omniscient") }, { it.put("view", "knowledge") }, { it.put("story_time", -1) },
        )) invalid(page(q, listOf(raw)).also(mutate), q)
        invalidCommand(q.copy(version = 3))
    }

    @Test fun progressionSourceDrillUsesExactAncestorTupleAndCurrentLensAndRejectsWrongReturnedBranch() = runTest {
        val ref = StoryRecordScopedEvent(StoryRecordScope("survey-story", "ancestor"), 3)
        for (wrongBranch in listOf(false, true)) {
            val reads = mutableListOf<StoryRecordQuery>(); var lookup = 0
            val controller = StoryRecordController({ q ->
                reads += q
                if (q.section == StoryRecordSection.PROGRESSION) required(page(q, listOf(field())), q)
                else { lookup++; required(page(q, listOf(event(if (wrongBranch) ref.copy(originalScope = ref.originalScope.copy(branch = "other")) else ref))), q) }
            }, this)
            controller.open(context); advanceUntilIdle()
            assertNull(controller.state.value.problem); assertEquals(listOf(ref), controller.state.value.entries.single().scopedEventSources)
            val before = reads.toList(); controller.openEvent(3); controller.openScopedEvent(ref.copy(sequence = 2)); advanceUntilIdle()
            assertEquals(before, reads)
            controller.openScopedEvent(ref); advanceUntilIdle(); assertEquals(1, lookup)
            val q = reads.last(); assertEquals(context, q.context); assertEquals(StoryRecordSection.HISTORY, q.section); assertEquals(2, q.version)
            assertEquals("\"event\":{\"sequence\":3,\"scope\":{\"story\":\"survey-story\",\"branch\":\"ancestor\"}", q.search)
            val wire = StoryRecordWire.command("same-session", q).getJSONObject("query")
            assertEquals("child", wire.getJSONObject("scope").getString("branch")); assertEquals(8L, wire.getLong("expected_head"))
            val detail = checkNotNull(controller.state.value.eventDetail); assertEquals(ref, detail.scopedReference)
            if (wrongBranch) { assertEquals(StoryRecordProblem.INVALID_RESPONSE, detail.problem); assertNull(detail.entry) }
            else { assertNull(detail.problem); assertEquals(ref.originalScope, detail.entry?.event?.originalScope); assertTrue(checkNotNull(detail.entry).eventSources.isEmpty()) }
            controller.dispose()
        }
    }

    @Test fun nonCooperativeQuery2RepliesCannotReviveDismissedDisposedOrReplacedContexts() = runTest {
        for (action in listOf("dismiss", "dispose", "context", "section")) {
            val late = CompletableDeferred<Unit>(); val reads = mutableListOf<StoryRecordQuery>()
            val controller = StoryRecordController({ q ->
                reads += q
                if (q.context == context && q.section == StoryRecordSection.PROGRESSION) withContext(NonCancellable) { late.await() }
                required(page(q, if (q.section == StoryRecordSection.HISTORY) listOf(marker()) else listOf(field(scoped(story = q.context.story.story)))), q)
            }, this)
            try {
                controller.open(context); runCurrent(); assertEquals(2, reads.single().version)
                when (action) {
                    "dismiss" -> controller.dismiss()
                    "dispose" -> controller.dispose()
                    "context" -> controller.open(context.copy(story = context.story.copy(branch = "next-branch", revision = 9), revision = 9))
                    else -> controller.select(StoryRecordSection.HISTORY)
                }
                runCurrent(); val fresh = controller.state.value
                late.complete(Unit); advanceUntilIdle(); assertEquals(fresh, controller.state.value)
                if (action == "dismiss" || action == "dispose") assertEquals(StoryRecordState(), fresh)
                if (action == "dispose") {
                    val calls = reads.size; controller.open(context); controller.select(StoryRecordSection.HISTORY); controller.retry(); advanceUntilIdle(); assertEquals(calls, reads.size)
                }
            } finally { late.complete(Unit); controller.dispose(); advanceUntilIdle() }
        }
    }

    @Test fun controllerRefusesStalePageIdentityAndClearsPrivateFailuresWithoutDispatchingEvidence() = runTest {
        for (failure in listOf("query", "clock", "private")) {
            val reads = mutableListOf<StoryRecordQuery>()
            val controller = StoryRecordController({ q ->
                reads += q
                if (failure == "private") error("PRIVATE_ADAPTER_FAILURE /private/story")
                val decoded = required(page(q, listOf(field())), q)
                if (failure == "query") decoded.copy(query = q.copy(context = context.copy(revision = 9))) else decoded.copy(storyTime = -1)
            }, this)
            controller.open(context); advanceUntilIdle()
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem); assertTrue(controller.state.value.entries.isEmpty())
            assertFalse(controller.state.value.toString().contains("PRIVATE_ADAPTER_FAILURE"))
            val before = reads.toList(); controller.openScopedEvent(StoryRecordScopedEvent(StoryRecordScope("survey-story", "ancestor"), 3)); advanceUntilIdle()
            assertEquals(before, reads); assertNull(controller.state.value.eventDetail); controller.dispose()
        }
    }
}
