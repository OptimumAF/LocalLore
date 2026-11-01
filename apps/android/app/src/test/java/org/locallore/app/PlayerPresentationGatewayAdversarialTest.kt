/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Actual native captures, not fabricated successful V2 payloads. No JNI/Store runs here. */
internal class PresentationCapturedCase(val value: JSONObject) {
    val id: String get() = value.getString("id")
    val scope: JSONObject get() = value.getJSONObject("scope")
    val revision: Long get() = value.getLong("revision")
    val story: String get() = scope.getString("story")
    val branch: String get() = scope.getString("branch")
    val turns: JSONArray get() = value.getJSONArray("expected_turns")
    fun envelope(role: String) = JSONObject(value.getJSONObject(role).toString())
    fun saved(): SavedStory {
        val rows = value.getJSONObject("workspace").getJSONObject("data").getJSONArray("stories")
        val root = (0 until rows.length()).map(rows::getJSONObject)
            .single { it.getJSONObject("scope").getString("story") == story }
        return SavedStory(story, branch, root.getString("title"), revision)
    }
}

internal class PresentationCaptureCorpus {
    private val original: String = checkNotNull(javaClass.classLoader!!.getResourceAsStream("player-presentation-v2-native.json")) {
        "Genuine native presentation capture is a setup prerequisite"
    }.bufferedReader(Charsets.UTF_8).use { it.readText() }
    private val document = JSONObject(original)
    private val loadedDocument = document.toString()
    val cases = document.getJSONArray("cases").let { rows ->
        (0 until rows.length()).map { PresentationCapturedCase(rows.getJSONObject(it)) }
    }
    init {
        check(document.getInt("version") == 1)
        check(cases.map { it.id }.toSet() == setOf("main", "corrected", "rediscovered", "empty", "mixed", "slashes", "u64"))
        check(cases.size == 7)
        for (case in cases) {
            check(case.envelope("reply").getString("status") == "ok")
            check(case.envelope("reply").getJSONObject("data").getInt("version") == 2)
        }
    }
    fun case(id: String) = cases.single { it.id == id }
    fun scoped(scope: JSONObject) = cases.single {
        it.story == scope.getString("story") && it.branch == scope.getString("branch")
    }
    fun assertUnchanged() { assertEquals(loadedDocument, document.toString()) }
}

/** Mock only transport I/O; every successful envelope was captured from ordinary native Host. */
internal class PresentationCaptureTransport(val corpus: PresentationCaptureCorpus, initial: String = "main") : WorkspaceTransport {
    var selected = corpus.case(initial)
    val commands = mutableListOf<JSONObject>()
    val resumes = mutableListOf<PlayDraftScope>()
    var closes = 0
    var mutateNext: ((JSONObject) -> Unit)? = null
    var beforePresentation: (suspend () -> Unit)? = null
    var mutateNextBranches: ((JSONObject) -> Unit)? = null
    fun gateway() = DurableGateway(this, autoCreateIfEmpty = false,
        initialScopeHint = PlayDraftScope(selected.story, selected.branch))
    override suspend fun exchange(command: JSONObject): JSONObject {
        commands += JSONObject(command.toString())
        return when (command.getString("op")) {
            "workspace" -> selected.envelope("workspace")
            "branches" -> selected.envelope("branches").also { reply ->
                mutateNextBranches?.also { mutateNextBranches = null }?.invoke(reply.getJSONObject("data"))
            }
            "resume" -> {
                selected = corpus.scoped(command.getJSONObject("scope"))
                resumes += PlayDraftScope(selected.story, selected.branch)
                selected.envelope("resumed")
            }
            "open" -> selected.envelope("opened")
            "play_presentation_v2" -> {
                val captured = selected.envelope("reply")
                mutateNext?.also { mutateNext = null }?.invoke(captured.getJSONObject("data"))
                beforePresentation?.also { beforePresentation = null }?.invoke()
                captured
            }
            "play_snapshot" -> throw AssertionError("Presentation Gateway must use play_presentation_v2, not legacy play_snapshot")
            "capabilities" -> selected.envelope("capabilities")
            "model_status" -> selected.envelope("model_status")
            "close" -> JSONObject().put("version", 1).put("status", "ok").put("data", JSONObject())
            else -> throw AssertionError("Presentation browsing dispatched unexpected operation ${command.getString("op")}")
        }
    }
    override fun close() { closes++ }
    fun assertReadOnly() {
        assertTrue(commands.all { it.getString("op") in setOf("workspace", "branches", "resume", "open",
            "play_presentation_v2", "capabilities", "model_status", "close") })
    }
}

/** Object-key order is presentation-neutral; array order and all accepted values are retained. */
private fun canonicalPresentationJson(value: Any?): String = when (value) {
    null, JSONObject.NULL -> "null"
    is JSONObject -> value.keys().asSequence().toList().sorted().joinToString(",", "{", "}") {
        JSONObject.quote(it) + ":" + canonicalPresentationJson(value.get(it))
    }
    is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonicalPresentationJson(value.get(it)) }
    is String -> JSONObject.quote(value)
    else -> value.toString()
}

internal fun assertCapturedPresentation(messages: List<SceneMessage>, case: PresentationCapturedCase) {
    val expected = case.value.getJSONArray("expected_messages")
    assertEquals(expected.length(), messages.size)
    assertEquals(case.turns.length() * 2, messages.size)
    for ((index, actual) in messages.withIndex()) {
        val row = expected.getJSONObject(index)
        assertEquals(row.getLong("id"), actual.id)
        assertEquals(row.getBoolean("player"), actual.isPlayer)
        val turn = case.turns.getJSONObject(index / 2)
        if (actual.isPlayer && turn.getJSONObject("intent").getString("kind") == "actions") {
            assertEquals(canonicalPresentationJson(JSONArray(row.getString("text"))),
                canonicalPresentationJson(JSONArray(actual.text)))
        } else {
            assertEquals(row.getString("text"), actual.text)
            if (!actual.isPlayer) assertEquals(turn.getString("narration"), actual.text)
            else assertEquals(turn.getJSONObject("intent").getJSONObject("value").getString("text"), actual.text)
        }
    }
}

internal suspend fun initializeCaptured(gateway: DurableGateway): SavedSnapshot = try { gateway.initialize() }
catch (failure: WorkspaceFailure) {
    throw AssertionError("Genuine captured native presentation refused: ${failure.category}", failure)
}

@OptIn(ExperimentalCoroutinesApi::class)
class PlayerPresentationGatewayAdversarialTest {
    private suspend fun refused(categories: Set<String> = setOf("Malformed"), body: suspend () -> Unit) {
        try { body(); fail("Malformed/stale player presentation was accepted") }
        catch (failure: WorkspaceFailure) { assertTrue("Wrong refusal ${failure.category}", failure.category in categories) }
    }

    @Test fun genuineCapturedMainCorrectedRediscoveredEmptyAndMixedPublishWithoutLegacyContext() = runTest {
        val corpus = PresentationCaptureCorpus()
        for (case in corpus.cases) {
            val transport = PresentationCaptureTransport(corpus, case.id); val gateway = transport.gateway()
            try {
                val saved = initializeCaptured(gateway)
                assertEquals(case.revision, saved.revision)
                assertEquals(case.story, saved.selected!!.story); assertEquals(case.branch, saved.selected!!.branch)
                assertCapturedPresentation(saved.messages, case)
                val request = transport.commands.single { it.getString("op") == "play_presentation_v2" }
                assertEquals(case.revision, request.getLong("expected_revision"))
                assertEquals(case.story, request.getJSONObject("scope").getString("story"))
                assertEquals(case.branch, request.getJSONObject("scope").getString("branch"))
                assertEquals(case.value.getJSONObject("resumed").getJSONObject("data").getString("session"), request.getString("session"))
                transport.assertReadOnly()
            } finally { gateway.close() }
        }
        corpus.assertUnchanged()
    }

    @Test fun mixedAcceptedIntentTextAndNarrationAreLosslessAndWindowIdsDoNotRestartAtOne() = runTest {
        val corpus = PresentationCaptureCorpus(); val case = corpus.case("mixed")
        val transport = PresentationCaptureTransport(corpus, "mixed"); val gateway = transport.gateway()
        try {
            val kinds = (0 until case.turns.length()).map { case.turns.getJSONObject(it).getJSONObject("intent").getString("kind") }.toSet()
            assertEquals(setOf("actions", "dialogue", "free_text"), kinds)
            val window = case.envelope("reply").getJSONObject("data").getJSONObject("window")
            assertTrue(window.getLong("start") > 0)
            val saved = initializeCaptured(gateway)
            assertEquals(40, saved.messages.size)
            assertEquals(window.getLong("start") * 2 + 1, saved.messages.first().id)
            assertEquals(window.getLong("end") * 2, saved.messages.last().id)
            assertCapturedPresentation(saved.messages, case)
        } finally { gateway.close() }
    }

    @Test fun genuineAncestorInputsRemainScopedAndCapturedPrivateAuthorNpcValuesStayAbsent() = runTest {
        val corpus = PresentationCaptureCorpus(); val case = corpus.case("corrected")
        val data = case.envelope("reply").getJSONObject("data")
        assertTrue((0 until case.turns.length()).any { case.turns.getJSONObject(it).getJSONObject("original_scope").getString("branch") != case.branch })
        assertEquals(canonicalPresentationJson(case.turns), canonicalPresentationJson(data.getJSONArray("turns")))
        val forbidden = case.value.getJSONArray("forbidden")
        for (i in 0 until forbidden.length()) assertFalse(data.toString().contains(forbidden.getString(i)))
        val transport = PresentationCaptureTransport(corpus, "corrected"); val gateway = transport.gateway()
        try { assertCapturedPresentation(initializeCaptured(gateway).messages, case); transport.assertReadOnly() }
        finally { gateway.close() }
    }

    @Test fun privateUnknownAndMistypedFieldsCannotBecomeDisplayOrAValidSnapshot() = runTest {
        val corpus = PresentationCaptureCorpus()
        val faults: List<(JSONObject) -> Unit> = listOf(
            { it.put("author_reason", "PRIVATE_PRESENTATION_PAYLOAD") },
            { it.getJSONObject("player").put("other_actor_sheet", "PRIVATE_PRESENTATION_PAYLOAD") },
            { it.getJSONArray("turns").getJSONObject(0).put("proposal", JSONObject()) },
            { it.put("revision", true) }, { it.put("domain_version", 3) },
            { it.put("revision", it.getLong("revision") + 1) },
            { it.getJSONObject("scope").put("branch", "another-current-branch") },
            { it.getJSONObject("player").put("observer", true) },
            { it.getJSONObject("player").getJSONObject("self_state").put("private_beliefs", JSONArray()) })
        for (fault in faults) {
            val transport = PresentationCaptureTransport(corpus, "corrected"); val gateway = transport.gateway()
            transport.mutateNext = fault
            try { refused { gateway.initialize() }; transport.assertReadOnly() } finally { gateway.close() }
        }
    }

    @Test fun inconsistentWindowsAndGloballyDuplicateFutureOrReorderedEventsAreRejected() = runTest {
        val corpus = PresentationCaptureCorpus()
        val faults: List<(JSONObject) -> Unit> = listOf(
            { it.getJSONObject("window").put("start", 1) },
            { it.getJSONObject("window").put("total", 4097) },
            { it.getJSONObject("window").put("end", 1.0) },
            { it.getJSONArray("turns").getJSONObject(0).put("event_ids", JSONArray().put(0)) },
            { it.getJSONArray("turns").getJSONObject(0).put("event_ids", JSONArray().put(it.getLong("revision") + 1)) },
            { val turns = it.getJSONArray("turns"); turns.getJSONObject(1).put("event_ids", JSONArray(turns.getJSONObject(0).getJSONArray("event_ids").toString())) },
            { val turns = it.getJSONArray("turns"); val first = turns.getJSONObject(0); val second = turns.getJSONObject(1); turns.put(0, second); turns.put(1, first) })
        for (fault in faults) {
            val transport = PresentationCaptureTransport(corpus, "corrected"); val gateway = transport.gateway()
            transport.mutateNext = fault
            try { refused { gateway.initialize() } } finally { gateway.close() }
        }
    }

    @Test fun malformedOriginalIntentShapeAndForeignScopeCannotBorrowValidNarration() = runTest {
        val corpus = PresentationCaptureCorpus()
        val faults: List<(JSONObject) -> Unit> = listOf(
            { it.getJSONArray("turns").getJSONObject(0).getJSONObject("original_scope").put("story", "another-story") },
            { it.getJSONArray("turns").getJSONObject(0).getJSONObject("original_scope").put("branch", "../private") },
            { it.getJSONArray("turns").getJSONObject(0).put("intent", JSONObject().put("kind", "author_correction").put("value", "private")) },
            { it.getJSONArray("turns").getJSONObject(0).getJSONObject("intent").getJSONArray("value").getJSONObject(0).put("private_authority", true) },
            { val turns = it.getJSONArray("turns"); val dialogue = (0 until turns.length()).map(turns::getJSONObject).first { row -> row.getJSONObject("intent").getString("kind") == "dialogue" }; dialogue.getJSONObject("intent").getJSONObject("value").put("audience", "not-an-array") })
        for (fault in faults) {
            val transport = PresentationCaptureTransport(corpus, "corrected"); val gateway = transport.gateway()
            transport.mutateNext = fault
            try { refused { gateway.initialize() } } finally { gateway.close() }
        }
    }

    @Test fun aCoherentLeaseCannotRetargetItsAlreadyBoundOpaqueObserver() = runTest {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val gateway = transport.gateway()
        try {
            initializeCaptured(gateway)
            transport.mutateNext = { it.getJSONObject("player").put("observer", "another-valid-actor") }
            refused(setOf("Stale")) { gateway.snapshot() }
        } finally { gateway.close() }
    }

    @Test fun lateCapturedSnapshotCannotReattachAfterARealResumeToAnotherCapturedBranch() = runTest {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val gateway = transport.gateway()
        try {
            initializeCaptured(gateway)
            val entered = CompletableDeferred<Unit>(); val release = CompletableDeferred<Unit>()
            transport.beforePresentation = { entered.complete(Unit); withContext(NonCancellable) { release.await() } }
            val old = async { refused(setOf("Stale")) { gateway.snapshot() } }
            try {
                runCurrent(); assertTrue(entered.isCompleted)
                val next = gateway.resumeSaved(corpus.case("corrected").saved())
                release.complete(Unit); old.await()
                assertCapturedPresentation(next.messages, corpus.case("corrected"))
                assertEquals(corpus.case("corrected").branch, gateway.snapshot().selected!!.branch)
                transport.assertReadOnly()
            } finally { release.complete(Unit) }
        } finally { gateway.close() }
    }

    @Test fun closureDuringNonCooperativePresentationReadPreventsPublication() = runTest {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val gateway = transport.gateway(); initializeCaptured(gateway)
        val entered = CompletableDeferred<Unit>(); val release = CompletableDeferred<Unit>()
        transport.beforePresentation = { entered.complete(Unit); withContext(NonCancellable) { release.await() } }
        val pending = async { refused(setOf("Closed", "Stale")) { gateway.snapshot() } }
        try {
            runCurrent(); assertTrue(entered.isCompleted)
            gateway.close(); release.complete(Unit); pending.await()
            assertEquals(1, transport.closes)
            transport.assertReadOnly()
        } finally { release.complete(Unit); gateway.close() }
    }

    @Test fun equalScopeHeadAndReusedRecordedSessionDoNotAuthorizeAnOldAttachmentRead() = runTest {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val gateway = transport.gateway()
        try {
            val first = initializeCaptured(gateway)
            val entered = CompletableDeferred<Unit>(); val release = CompletableDeferred<Unit>()
            transport.beforePresentation = { entered.complete(Unit); withContext(NonCancellable) { release.await() } }
            val old = async { refused(setOf("Stale")) { gateway.snapshot() } }
            try {
                runCurrent(); assertTrue(entered.isCompleted)
                // Capture replays the exact same session string, IDs and head. Only
                // the real Gateway attachment/scope-object generation has changed.
                val refreshed = gateway.resumeSaved(corpus.case("main").saved())
                assertEquals(first.selected, refreshed.selected)
                release.complete(Unit); old.await()
                assertCapturedPresentation(gateway.snapshot().messages, corpus.case("main"))
            } finally { release.complete(Unit) }
        } finally { gateway.close() }
    }

    @Test fun catalogHeadAdvanceCannotBeCombinedWithAnOlderValidPresentation() = runTest {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val gateway = transport.gateway()
        try {
            initializeCaptured(gateway)
            transport.mutateNextBranches = { data ->
                val rows = data.getJSONArray("branches")
                val selected = (0 until rows.length()).map(rows::getJSONObject).single {
                    it.getJSONObject("scope").getString("branch") == corpus.case("main").branch
                }
                selected.put("revision", selected.getLong("revision") + 1)
            }
            refused(setOf("Stale")) { gateway.snapshot() }
        } finally { gateway.close() }
    }

    @Test fun nativeAdmittedSlashTextSurvivesAndroidJsonReserializationWithoutAnExtraProseBudget() {
        val corpus = PresentationCaptureCorpus(); val case = corpus.case("slashes")
        val reply = case.envelope("reply")
        // JNI bounds the original native envelope. API 35 JSONStringer additionally
        // escapes every slash when rendering the same decoded fields and values.
        val rawBytes = case.value.getLong("raw_reply_utf8_bytes")
        assertTrue(rawBytes in 1..65_536L)
        assertEquals(20, case.turns.length())
        val escaped = object : JSONObject(reply.getJSONObject("data").toString()) {
            override fun toString(): String {
                val source = super.toString()
                return buildString {
                    var backslashes = 0
                    for (character in source) {
                        if (character == '/' && backslashes % 2 == 0) append('\\')
                        append(character)
                        backslashes = if (character == '\\') backslashes + 1 else 0
                    }
                }
            }
        }
        assertTrue(escaped.toString().toByteArray(Charsets.UTF_8).size > 65_536)
        val decoded = PlayerPresentationWire.decode(escaped,
            PlayDraftScope(case.story, case.branch), case.revision)
        assertCapturedPresentation(decoded.messages, case)
        corpus.assertUnchanged()
    }

    @Test fun nativeAcceptedUnsignedDeadlineAndClaimKeepExactNumericDisplayWithoutMutatingThePresentationDto() {
        val corpus = PresentationCaptureCorpus(); val case = corpus.case("u64")
        val data = case.envelope("reply").getJSONObject("data")
        val untouched = data.toString()
        val maximum = "18446744073709551615"
        val intents = (0 until case.turns.length()).map { turnIndex ->
            case.turns.getJSONObject(turnIndex).getJSONObject("intent")
        }
        assertEquals(listOf("actions", "dialogue", "actions"), intents.map { it.getString("kind") })
        val commands = intents.filter { it.getString("kind") == "actions" }.flatMap { intent ->
            val actions = intent.getJSONArray("value")
            (0 until actions.length()).map(actions::getJSONObject)
        }
        assertEquals(maximum, commands.single { it.getString("op") == "promise" }.get("deadline"))
        assertEquals("2", commands.single { it.getString("op") == "believe" }.get("claim_event"))
        val expected = case.value.getJSONArray("expected_messages")
        val originalInputs = (0 until expected.length()).map(expected::getJSONObject)
            .filter { it.getBoolean("player") }.map { it.getString("text") }
        assertTrue(originalInputs.any { it.contains("\"deadline\":" + maximum) })
        assertTrue(originalInputs.any { it.contains("\"claim_event\":2") })

        val decoded = PlayerPresentationWire.decode(data, PlayDraftScope(case.story, case.branch), case.revision)
        assertCapturedPresentation(decoded.messages, case)
        val displayed = decoded.messages.filter { it.isPlayer }.map { it.text }
        assertTrue(displayed.any { it.contains("\"deadline\":" + maximum) })
        assertTrue(displayed.any { it.contains("\"claim_event\":2") })
        assertFalse(displayed.any { it.contains("1.8446744073709552E19", ignoreCase = true) })
        assertFalse(displayed.any { it.contains("\"deadline\":-1") })
        assertFalse(displayed.any { it.contains("\"deadline\":9223372036854775807") })
        assertEquals(untouched, data.toString())
        corpus.assertUnchanged()
    }
}
