/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Bundle
import android.os.Process
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.runner.lifecycle.ActivityLifecycleCallback
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import java.io.File
import java.nio.file.Files
import java.util.concurrent.atomic.AtomicReference
import java.util.concurrent.atomic.AtomicBoolean
import org.json.JSONArray
import org.json.JSONObject
import org.junit.After
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

private const val giftInput = "I give my last potion to Mira."
private const val dialogueInput = "Where is the tideglass relic?"
private object OrdinaryDiagnostics { val emitted = AtomicBoolean() }
private fun sha(bytes: ByteArray) = ReceiptRealEnvironment.sha(bytes)
private fun canonicalHash(value: Any): String = sha(ReceiptRealEnvironment.canonical(value).toByteArray(Charsets.UTF_8))
private fun workerSnapshot() = requireNotNull(CandidateLocalModel.receiptWorkerSnapshot()) { "ORDINARY_TRACE_MISSING" }
private fun workerHash(value: LiteRtWorkerSnapshot) = sha(value.json().toByteArray(Charsets.US_ASCII))
private fun workerZero(value: LiteRtWorkerSnapshot) = value.counts.values.all { it == 0 } && value.creationsTotal == 0 &&
    value.lastMs.values.all { it == null } && value.saturated.isEmpty() && !value.timeSaturated && !value.creationsSaturated
private fun workerClosed(value: LiteRtWorkerSnapshot) {
    check(value.saturated.isEmpty() && !value.timeSaturated && !value.creationsSaturated)
    val roles = value.creations.map { it.role }
    check(roles == listOf(LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.NARRATOR) ||
        roles == listOf(LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.NARRATOR))
    check(value.creationsTotal == roles.size && value.creations.all {
        it.returnedMs != null && it.failedMs == null && it.failure == LiteRtTraceFailure.NONE
    })
    for (event in listOf(LiteRtWorkerEvent.CONVERSATION_CREATE_ENTERED, LiteRtWorkerEvent.CONVERSATION_CREATE_RETURNED,
        LiteRtWorkerEvent.SEND_ENTERED, LiteRtWorkerEvent.SEND_RETURNED, LiteRtWorkerEvent.DONE_ENTERED, LiteRtWorkerEvent.DONE_RETURNED,
        LiteRtWorkerEvent.DRAIN_SETTLED, LiteRtWorkerEvent.CONVERSATION_CLOSE_ENTERED, LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN))
        check(value.counts.getValue(event) == roles.size)
    for (event in listOf(LiteRtWorkerEvent.ERROR_ENTERED, LiteRtWorkerEvent.ERROR_RETURNED, LiteRtWorkerEvent.CANCEL_ENTERED,
        LiteRtWorkerEvent.CANCEL_RETURNED, LiteRtWorkerEvent.UNCERTAIN)) check(value.counts.getValue(event) == 0)
    check(value.counts.getValue(LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED) == 1 && value.counts.getValue(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN) == 1)
    check(value.counts.getValue(LiteRtWorkerEvent.MESSAGE_RETURNED) > 0)
}
private fun identity() = CancellationIdentity(Process.myPid(), Process.getStartElapsedRealtime(), Process.myUid())
private fun capacity(env: ReceiptRealEnvironment): CancellationCapacity {
    env.admit()
    val after = env.memory()
    check(after.totalMem == env.memoryBefore.totalMem)
    return CancellationCapacity(env.userdataBefore, env.internal.usableSpace, env.externalBefore, env.external.usableSpace,
        after.totalMem, env.memoryBefore.availMem, after.availMem)
}

/** Fixed metadata only. Other proof families remain untouched. */
private class OrdinaryFiles(val env: ReceiptRealEnvironment) {
    private val root = File(env.internal, "receipt-ordinary-scene-proof-v1")
    private fun names(phase: OrdinaryRoutePhase): Set<String> = buildSet {
        for (value in OrdinaryRoutePhase.entries.take(phase.ordinal + 1)) {
            add("${value.file}-v1.json"); add("${value.file}-ready-v1.txt"); add("${value.file}-worker-v2.json")
        }
        if (phase != OrdinaryRoutePhase.ORDINARY_START) add("guards-worker-v2.json")
    }
    fun fresh() { env.admit(); ReceiptRealEnvironment.absent(root) }
    private fun read(phase: OrdinaryRoutePhase): Pair<OrdinaryRouteProof, String> {
        val raw = ReceiptRealEnvironment.read(File(root, "${phase.file}-v1.json"), 4096)
        check(raw.isNotEmpty() && raw.all { it.toInt() in 32..126 })
        check(ReceiptRealEnvironment.read(File(root, "${phase.file}-ready-v1.txt"), 0).isEmpty())
        val json = JSONObject(raw.toString(Charsets.US_ASCII))
        fun number(key: String) = ReceiptRealEnvironment.number(json, key)
        fun integer(key: String) = number(key).also { check(it in 0..Int.MAX_VALUE) }.toInt()
        val flags = json.getJSONObject("checks")
        val checks = flags.keys().asSequence().associateWith { flags.get(it) as? Boolean ?: error("ORDINARY_CHECK_TYPE") }
        val proof = OrdinaryRouteProof(phase, CancellationIdentity(integer("pid"), number("start"), integer("uid")),
            integer("prior_pid"), number("prior_start"), json.getString(phase.priorKey), number("elapsed_ms"),
            CancellationCapacity(number("userdata_free_before"), number("userdata_free_after"), number("external_free_before"),
                number("external_free_after"), number("memory_total_bytes"), number("memory_available_before"), number("memory_available_after")),
            checks, json.getString("receipts_sha256"), json.getString("gift_receipt_sha256"), json.getString("worker_trace_sha256"),
            if (phase != OrdinaryRoutePhase.ORDINARY_START) json.getString("dialogue_receipt_sha256") else null,
            if (phase != OrdinaryRoutePhase.ORDINARY_REOPEN) integer("repairs") else null,
            if (phase != OrdinaryRoutePhase.ORDINARY_REOPEN) json.get("fallback") as? Boolean ?: error("ORDINARY_BOOLEAN") else null,
            if (phase == OrdinaryRoutePhase.ORDINARY_DIALOGUE) json.getString("guards_worker_trace_sha256") else null)
        check(proof.json().toByteArray(Charsets.US_ASCII).contentEquals(raw))
        fun trace(name: String, expected: String) {
            val bytes = ReceiptRealEnvironment.read(File(root, name), 4096)
            check(bytes.isNotEmpty() && bytes.all { it.toInt() in 32..126 } && sha(bytes) == expected)
        }
        trace("${phase.file}-worker-v2.json", proof.workerTraceSha256)
        proof.guardsTraceSha256?.let { trace("guards-worker-v2.json", it) }
        return proof to sha(raw)
    }
    fun prior(phase: OrdinaryRoutePhase): Pair<OrdinaryRouteProof, String> {
        env.admit(); check(phase != OrdinaryRoutePhase.ORDINARY_START)
        ReceiptRealEnvironment.strictDirectory(root)
        ReceiptRealEnvironment.entries(root, names(OrdinaryRoutePhase.entries[phase.ordinal - 1]))
        val imported = env.prior(ReceiptRealPhase.IMPORT)
        val start = read(OrdinaryRoutePhase.ORDINARY_START)
        check(start.first.priorSha256 == imported.second && start.first.priorPid == imported.first.getInt("pid") &&
            start.first.priorStart == imported.first.getLong("start"))
        if (phase == OrdinaryRoutePhase.ORDINARY_DIALOGUE) return start
        val dialogue = read(OrdinaryRoutePhase.ORDINARY_DIALOGUE)
        check(dialogue.first.priorSha256 == start.second && dialogue.first.priorPid == start.first.identity.pid &&
            dialogue.first.priorStart == start.first.identity.start && dialogue.first.giftReceiptSha256 == start.first.giftReceiptSha256)
        return dialogue
    }
    fun write(proof: OrdinaryRouteProof, traces: Map<String, LiteRtWorkerSnapshot>) {
        env.admit()
        val expected = mutableMapOf("${proof.phase.file}-worker-v2.json" to proof.workerTraceSha256)
        proof.guardsTraceSha256?.let { expected["guards-worker-v2.json"] = it }
        check(traces.keys == expected.keys)
        if (proof.phase == OrdinaryRoutePhase.ORDINARY_START) { ReceiptRealEnvironment.absent(root); Files.createDirectory(root.toPath()) }
        ReceiptRealEnvironment.strictDirectory(root)
        for ((name, trace) in traces) {
            val bytes = trace.json().toByteArray(Charsets.US_ASCII)
            check(bytes.size in 1..4096 && sha(bytes) == expected.getValue(name))
            ReceiptRealEnvironment.forcedNew(File(root, name), bytes)
        }
        ReceiptRealEnvironment.forcedNew(File(root, "${proof.phase.file}-v1.json"), proof.json().toByteArray(Charsets.US_ASCII))
        ReceiptRealEnvironment.forcedNew(File(root, "${proof.phase.file}-ready-v1.txt"), byteArrayOf())
        ReceiptRealEnvironment.entries(root, names(proof.phase))
    }
}

/** Launches ordinary setup and observes its actual Start transition, never an alternate factory. */
abstract class ReceiptOrdinaryHarness : ReceiptRealHarness() {
    @get:Rule val compose = createEmptyComposeRule()
    private var setup: ActivityScenario<LocalModelSetupActivity>? = null
    internal lateinit var play: LiteRtPlayActivity
    internal lateinit var model: ShellViewModel
    internal lateinit var actual: NativeWorkspaceTransport
    internal fun selectOrdinary(type: Class<*>, phase: OrdinaryRoutePhase): ReceiptRealDeadline {
        assumeTrue("Exact ordinary route class required", InstrumentationRegistry.getArguments().getString("class") == type.name)
        return ReceiptRealDeadline(if (phase == OrdinaryRoutePhase.ORDINARY_REOPEN) ReceiptRealPhase.REOPEN else ReceiptRealPhase.PLAY)
            .also { check(it.phase.budgetMs == phase.budgetMs) }
    }
    internal fun launch(checks: MutableMap<String, Boolean>, deadline: ReceiptRealDeadline) {
        check(CandidateLocalModel.canStart())
        val seen = AtomicReference<LiteRtPlayActivity?>()
        val duplicate = AtomicBoolean()
        val monitor = ActivityLifecycleMonitorRegistry.getInstance()
        val callback = ActivityLifecycleCallback { activity, stage ->
            if (activity.javaClass == LiteRtPlayActivity::class.java && stage == Stage.RESUMED) {
                if (seen.get() != null && seen.get() !== activity) duplicate.set(true)
                else { play = activity as LiteRtPlayActivity; seen.set(activity) }
            }
        }
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.runOnMainSync { monitor.addLifecycleCallback(callback) }
        try {
            lateinit var setupActivity: LocalModelSetupActivity
            setup = ActivityScenario.launch(LocalModelSetupActivity::class.java)
            requireNotNull(setup).onActivity { setupActivity = it; check(it.javaClass == LocalModelSetupActivity::class.java) }
            checked(checks, "setup_activity_exact", true)
            compose.waitUntil(deadline.remaining(90_000)) { setupActivity.setupController.state.value.phase == LocalModelSetupPhase.READY }
            compose.onNodeWithTag("model-setup-status").performScrollTo()
                .assertTextEquals("The local copy matches the built-in size and SHA-256. Ready for local play.")
            checked(checks, "setup_ready_visible", true)
            instrumentation.runOnMainSync { check(setupActivity.lifecycle.currentState == Lifecycle.State.RESUMED && CandidateLocalModel.canStart()) }
            compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
            checked(checks, "start_enabled", true)
            var starts = 0
            compose.onNodeWithTag("model-start").performClick(); starts++
            checked(checks, "start_clicked_once", starts == 1)
            compose.waitUntil(deadline.remaining()) { seen.get() != null && setupActivity.isDestroyed }
            check(!duplicate.get()) { "ORDINARY_MULTIPLE_PLAY" }
            play = requireNotNull(seen.get())
            instrumentation.runOnMainSync {
                check(play.javaClass == LiteRtPlayActivity::class.java)
                actual = requireNotNull(play.constructedWorkspaceTransport) { "ORDINARY_TRANSPORT_MISSING" }
                model = ViewModelProvider(play)[ShellViewModel::class.java]
            }
            checked(checks, "setup_finished", setupActivity.isDestroyed)
            checked(checks, "play_activity_exact", true)
            checked(checks, "constructed_transport_observed", true)
            checked(checks, "production_shell_viewmodel", model.javaClass == ShellViewModel::class.java)
            settled(deadline); resumed()
            checked(checks, "play_resumed", true)
            workerSnapshot() // A missing passive observation is never coerced to zero.
        } finally { instrumentation.runOnMainSync { monitor.removeLifecycleCallback(callback) } }
    }
    internal fun resumed() = InstrumentationRegistry.getInstrumentation().runOnMainSync {
        check(play.lifecycle.currentState == Lifecycle.State.RESUMED) { "ORDINARY_NOT_RESUMED" }
    }
    internal fun settled(deadline: ReceiptRealDeadline) {
        compose.waitUntil(deadline.remaining()) { !model.state.value.busy }
        check(!model.state.value.recoveryRequired && !model.state.value.preparingResponse && !model.state.value.checkingCancellation)
    }
    internal fun node(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        return compose.onNodeWithTag(tag)
    }
    internal fun visibleTranscript() {
        for (message in model.state.value.messages) {
            val tag = "message-body-${message.id}"
            val okay = try {
                compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
                val bodies = compose.onAllNodesWithTag(tag).fetchSemanticsNodes()
                bodies.size == 1 && bodies.single().config.getOrNull(SemanticsProperties.Text)?.map { it.text } == listOf(message.text) &&
                    compose.onNodeWithTag(tag).isDisplayed()
            } catch (_: Throwable) { false }
            check(okay) { "ORDINARY_TRANSCRIPT" }
        }
    }
    internal fun enter(kind: PlayInputKind, text: String) {
        resumed()
        node("play-kind-${kind.wire}").performClick().assertIsSelected()
        node("play-input").performTextReplacement(text)
        node("play-input").assertTextContains(text)
    }
    internal fun send() { resumed(); node("play-send").assertIsEnabled().performClick() }
    internal fun recordLoaded(deadline: ReceiptRealDeadline, predicate: (StoryRecordState) -> Boolean = { true }) {
        compose.waitUntil(deadline.remaining()) {
            val state = model.storyRecord.value
            state.visible && !state.loading && state.problem == null && predicate(state)
        }
        resumed()
    }
    internal fun recordNode(tag: String) = compose.onNodeWithTag(tag).performScrollTo()
    internal fun search(text: String, deadline: ReceiptRealDeadline) {
        recordNode("story-record-search").performTextReplacement(text)
        recordNode("story-record-search-submit").performClick()
        recordLoaded(deadline) { it.search == text }
    }
    internal fun section(section: StoryRecordSection, deadline: ReceiptRealDeadline) {
        search("", deadline)
        recordNode("story-record-section-${section.wire}").performClick()
        recordLoaded(deadline) { it.section == section && it.search.isEmpty() }
        compose.onNodeWithTag("story-record-section-${section.wire}").assertIsSelected()
    }
    internal fun visibleRecord(index: Int) {
        val entry = model.storyRecord.value.entries[index]
        val okay = try {
            val row = recordNode("story-record-entry-$index")
            val pending = ArrayDeque<androidx.compose.ui.semantics.SemanticsNode>()
            pending.add(row.fetchSemanticsNode())
            val texts = mutableListOf<String>()
            var visited = 0
            while (pending.isNotEmpty()) {
                check(++visited <= 256)
                val node = pending.removeFirst()
                node.config.getOrNull(SemanticsProperties.Text)?.forEach { texts.add(it.text) }
                pending.addAll(node.children)
            }
            val source = if (entry.sources.isEmpty()) "Source · none recorded" else "Sources · ${entry.sources.joinToString(" · ")}"
            row.isDisplayed() && texts.containsAll(listOf(entry.title, entry.text, entry.origin.label, source))
        } catch (_: Throwable) { false }
        check(okay) { "ORDINARY_RECORD_PRESENTATION" }
    }
    internal suspend fun view(): JSONObject {
        check(!model.state.value.busy && !model.state.value.recoveryRequired)
        val handle = actual.forkHandle()
        val selected = requireNotNull(model.state.value.selectedStory)
        val scope = JSONObject().put("story", selected.story).put("branch", selected.branch)
        val session = data(actual, JSONObject().put("op", "resume").put("scope", scope))
        return data(actual, JSONObject().put("op", "play_snapshot").put("session", session.getString("session"))
            .put("scope", scope).put("expected_revision", model.state.value.revision)).also { check(actual.forkHandle() == handle) }
    }
    internal fun giftReceipt(receipt: JSONObject) {
        val request = receipt.getJSONObject("request").getJSONObject("intent")
        check(request.getString("kind") == "free_text" && request.getJSONObject("value").getString("kind") == "action" &&
            request.getJSONObject("value").getString("text") == giftInput)
        val events = receipt.getJSONArray("events")
        check(events.length() == 1)
        val outcome = events.getJSONObject(0).getJSONObject("outcome")
        check(outcome.getString("effect") == "given" && outcome.getString("item") == "potion" && outcome.getString("from") == "player" &&
            outcome.getString("to") == "mira" && outcome.getInt("quantity") == 1)
    }
    internal fun observeFailure(block: () -> Unit) {
        try { block() } catch (original: Throwable) {
            // Use the production snapshot only, never a replacement trace or observer callback.
            if (OrdinaryDiagnostics.emitted.compareAndSet(false, true)) {
                try {
                    val latest = requireNotNull(CandidateLocalModel.receiptWorkerSnapshot())
                    InstrumentationRegistry.getInstrumentation().sendStatus(LiteRtWorkerTrace.STATUS_CODE,
                        Bundle().apply { putString(LiteRtWorkerTrace.STATUS_KEY, latest.json()) })
                } catch (_: Throwable) { }
                try {
                    val send = requireNotNull(CandidateLocalModel.receiptSendSnapshot())
                    InstrumentationRegistry.getInstrumentation().sendStatus(LiteRtSendTrace.STATUS_CODE,
                        Bundle().apply { putString(LiteRtSendTrace.STATUS_KEY, send.json()) })
                } catch (_: Throwable) { }
                try {
                    val callback = requireNotNull(CandidateLocalModel.receiptCallbackSnapshot())
                    InstrumentationRegistry.getInstrumentation().sendStatus(LiteRtCallbackTrace.STATUS_CODE,
                        Bundle().apply { putString(LiteRtCallbackTrace.STATUS_KEY, callback.json()) })
                } catch (_: Throwable) { }
                try {
                    val status = requireNotNull(CandidateLocalModel.receiptStatusSnapshot())
                    InstrumentationRegistry.getInstrumentation().sendStatus(LiteRtStatusTrace.STATUS_CODE,
                        Bundle().apply { putString(LiteRtStatusTrace.STATUS_KEY, status.json()) })
                } catch (_: Throwable) { }
            }
            throw original
        }
    }
    internal fun closePlay(deadline: ReceiptRealDeadline) {
        if (::play.isInitialized && !play.isDestroyed) {
            InstrumentationRegistry.getInstrumentation().runOnMainSync { play.finish() }
            compose.waitUntil(deadline.remaining(5_000)) { play.isDestroyed }
        }
        setup?.close(); setup = null
    }
    @After fun closeOnlyOwnedActivities() {
        if (::play.isInitialized && !play.isDestroyed) InstrumentationRegistry.getInstrumentation().runOnMainSync { play.finish() }
        setup?.close(); setup = null
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptOrdinaryStartTest : ReceiptOrdinaryHarness() {
    @Test fun startsFromSetupAndCommitsRealGift() {
        val phase = OrdinaryRoutePhase.ORDINARY_START
        val deadline = selectOrdinary(ReceiptOrdinaryStartTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { ReceiptRealEnvironment.open(context) }
        val files = OrdinaryFiles(env)
        val prior = io(deadline) {
            files.fresh(); ReceiptRealEnvironment.absent(File(env.internal, "workspace-v1")); env.prior(ReceiptRealPhase.IMPORT)
        }
        checked(checks, "prior_import_proof_exact", prior.first.getInt("pid") != Process.myPid() ||
            prior.first.getLong("start") != Process.getStartElapsedRealtime())
        checked(checks, "memory_eligible", env.memoryEligible())
        // No Candidate.store/installed call here: ordinary setup alone performs its initial full check.
        launch(checks, deadline)
        observeFailure {
            node("empty-library").assertIsDisplayed()
            var creates = 0
            node("reset-demo").assertIsEnabled().performClick(); creates++
            compose.waitUntil(deadline.remaining(5_000)) {
                compose.onAllNodes(hasTestTag("story-creation-confirm") and isEnabled()).fetchSemanticsNodes().size == 1
            }
            compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsDisplayed().assertIsEnabled().performClick()
            compose.waitUntil(deadline.remaining(5_000)) {
                compose.onAllNodesWithTag("story-creation-dialog").fetchSemanticsNodes().isEmpty()
            }
            settled(deadline); resumed()
            checked(checks, "new_story_clicked_once", creates == 1)
            checked(checks, "production_transport_local", model.state.value.textProvider == TextProvider.LOCAL)
            io(deadline) {
                val before = view()
                check(before.getLong("revision") == 0L && before.getJSONArray("receipts").length() == 0)
            }
            checked(checks, "canonical_zero_before", true)
            node("inference-provider").assertTextEquals("Local Rust engine · local inference configured")
            node("play-provider").assertTextEquals(TextProvider.LOCAL.label)
            checked(checks, "local_provider_visible", true)
            enter(PlayInputKind.ACTION, giftInput); checked(checks, "fixed_action_visible", true)
            var sends = 0; send(); sends++
            checked(checks, "send_clicked_once", sends == 1)
            compose.waitUntil(deadline.remaining()) { !model.state.value.busy }
            settled(deadline); resumed()
            node("notice").assertTextEquals("Outcome accepted and saved by the local engine.")
            node("revision").assertTextEquals("Accepted revision · 1")
            node("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
            check(model.state.value.messages.size == 2)
            visibleTranscript(); checked(checks, "gift_visible", true)
            var receiptHash = ""; var receiptsHash = ""; var repairs = -1; var fallback = false
            val handle = io(deadline) {
                workerClosed(workerSnapshot()); checked(checks, "worker_closed_known", true)
                val view = view()
                val receipts = view.getJSONArray("receipts")
                checked(checks, "canonical_revision_one", view.getLong("revision") == 1L)
                checked(checks, "single_receipt", receipts.length() == 1)
                val receipt = receipts.getJSONObject(0)
                giftReceipt(receipt); checked(checks, "gift_receipt_exact", true)
                val accepted = requireNotNull(CandidateLocalModel.store(context).installed())
                checked(checks, "full_model_postcheck", true)
                val handle = actual.forkHandle(); checked(checks, "owner_guard_postcheck", true)
                val profile = JSONObject(localText(CandidateLocalModel.config(accepted).profileBytes(), 4096))
                val play = receipt.getJSONObject("play")
                checked(checks, "local_profile_exact", ReceiptRealEnvironment.canonical(profile) == ReceiptRealEnvironment.canonical(play.getJSONObject("profile")))
                receiptHash = canonicalHash(receipt); receiptsHash = canonicalHash(receipts)
                repairs = play.getInt("repairs"); fallback = play.getBoolean("fallback")
                checked(checks, "source_unopened", ReceiptRealCounts().unopened())
                handle
            }
            closePlay(deadline)
            io(deadline) {
                checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
                checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                val trace = workerSnapshot(); workerClosed(trace)
                deadline.remaining()
                files.write(OrdinaryRouteProof(phase, identity(), prior.first.getInt("pid"), prior.first.getLong("start"), prior.second,
                    deadline.elapsed(), capacity(env), checks, receiptsHash, receiptHash, workerHash(trace), repairs = repairs, fallback = fallback),
                    mapOf("start-worker-v2.json" to trace))
                deadline.remaining()
            }
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptOrdinaryDialogueTest : ReceiptOrdinaryHarness() {
    @Test fun inspectsGiftRejectsInvalidActionsAndRecordsDialogue() {
        val phase = OrdinaryRoutePhase.ORDINARY_DIALOGUE
        val deadline = selectOrdinary(ReceiptOrdinaryDialogueTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { ReceiptRealEnvironment.open(context) }
        val files = OrdinaryFiles(env)
        val prior = io(deadline) { files.prior(phase) }
        checked(checks, "prior_start_proof_exact", true)
        checked(checks, "process_identity_changed", prior.first.identity.pid != Process.myPid() || prior.first.identity.start != Process.getStartElapsedRealtime())
        checked(checks, "memory_eligible", env.memoryEligible())
        launch(checks, deadline)
        checked(checks, "production_transport_local", model.state.value.textProvider == TextProvider.LOCAL)
        observeFailure {
            val initial = io(deadline) { view() }
            val receiptsBefore = initial.getJSONArray("receipts")
            checked(checks, "initial_gift_receipts_exact", initial.getLong("revision") == 1L && receiptsBefore.length() == 1 &&
                canonicalHash(receiptsBefore) == prior.first.receiptsSha256 && canonicalHash(receiptsBefore.getJSONObject(0)) == prior.first.giftReceiptSha256)
            node("story-record-open").assertIsEnabled().performClick(); recordLoaded(deadline)
            section(StoryRecordSection.PROGRESSION, deadline)
            check(model.storyRecord.value.entries.isNotEmpty() && model.storyRecord.value.entries.all { it.origin == StoryRecordOrigin.CANONICAL_FIELD })
            visibleRecord(0); checked(checks, "progression_visible", true)
            section(StoryRecordSection.HISTORY, deadline)
            val history = model.storyRecord.value.entries
            val inputIndex = history.indexOfFirst { it.origin == StoryRecordOrigin.RECORDED_MESSAGE && it.title == "Recorded player input" && it.text == giftInput }
            check(inputIndex >= 0 && history[inputIndex].sources == listOf("Event #1"))
            check(history.any { it.origin == StoryRecordOrigin.RECORDED_MESSAGE && it.title == "Recorded narration" && it.sources == listOf("Event #1") })
            visibleRecord(inputIndex); checked(checks, "history_provenance_visible", true)
            val sourceIndex = history[inputIndex].eventSources.indexOf(1L); check(sourceIndex >= 0)
            recordNode("story-record-source-$inputIndex-$sourceIndex").performClick()
            recordLoaded(deadline) { it.eventDetail?.let { detail -> !detail.loading && detail.problem == null && detail.entry?.event?.sequence == 1L } == true }
            compose.onNodeWithTag("story-event-detail").assertIsDisplayed()
            checked(checks, "event_source_navigation_visible", true)
            compose.onNodeWithTag("story-event-back").performClick(); recordLoaded(deadline) { it.eventDetail == null }
            section(StoryRecordSection.RELATIONSHIPS, deadline)
            check(model.storyRecord.value.entries.isNotEmpty() && model.storyRecord.value.entries.all { it.origin == StoryRecordOrigin.CANONICAL_FIELD })
            visibleRecord(0); checked(checks, "relationships_visible", true)
            section(StoryRecordSection.KNOWLEDGE, deadline)
            val truths = model.storyRecord.value.entries.filter { it.origin == StoryRecordOrigin.CANONICAL_TRUTH }
            check(model.storyRecord.value.nextCursor == null && truths.isNotEmpty())
            search("SECRET-TIDE-731", deadline)
            check(model.storyRecord.value.total == 1 && model.storyRecord.value.entries.single().origin == StoryRecordOrigin.CANONICAL_TRUTH)
            visibleRecord(0); checked(checks, "knowledge_known_truth_visible", true)
            for (hidden in listOf("The tideglass relic is in old-ruins.", "Rowan may possess the tideglass relic.")) {
                search(hidden, deadline)
                check(model.storyRecord.value.total == 0 && model.storyRecord.value.entries.isEmpty())
                recordNode("story-record-empty").assertIsDisplayed()
            }
            checked(checks, "hidden_belief_search_empty", true)
            search("An old repair mark is scratched inside the dry well.", deadline)
            check(model.storyRecord.value.total == 0 && model.storyRecord.value.entries.isEmpty())
            recordNode("story-record-empty").assertIsDisplayed(); checked(checks, "hidden_beacon_search_empty", true)
            compose.onNodeWithTag("story-record-close").performClick()
            compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
            checked(checks, "inspector_canon_unchanged", io(deadline) { canonicalHash(view()) == canonicalHash(initial) })
            enter(PlayInputKind.ACTION, "I use ability blink."); send(); settled(deadline); resumed()
            node("notice").assertTextEquals("Blink is not learned. Nothing changed.")
            checked(checks, "ability_action_rejected", io(deadline) { canonicalHash(view()) == canonicalHash(initial) })
            enter(PlayInputKind.ACTION, giftInput); send(); settled(deadline); resumed()
            node("notice").assertTextEquals("You no longer hold the potion. Nothing changed.")
            checked(checks, "duplicate_gift_rejected", io(deadline) { canonicalHash(view()) == canonicalHash(initial) })
            checked(checks, "guards_canon_unchanged", io(deadline) { canonicalHash(view()) == canonicalHash(initial) })
            val guards = workerSnapshot()
            checked(checks, "guards_worker_zero", workerZero(guards))
            enter(PlayInputKind.DIALOGUE, dialogueInput)
            checked(checks, "dialogue_kind_selected", true); checked(checks, "fixed_dialogue_visible", true)
            var sends = 0; send(); sends++
            checked(checks, "dialogue_send_clicked_once", sends == 1)
            settled(deadline); resumed()
            node("notice").assertTextEquals("Outcome accepted and saved by the local engine.")
            node("revision").assertTextEquals("Accepted revision · 2")
            check(model.state.value.messages.size == 4 && model.state.value.messages.count { it.isPlayer && it.text == dialogueInput } == 1)
            visibleTranscript(); checked(checks, "dialogue_visible", true)
            var receiptsHash = ""; var dialogueHash = ""; var repairs = -1; var fallback = false
            val handle = io(deadline) {
                workerClosed(workerSnapshot()); checked(checks, "worker_closed_known", true)
                val view = view(); val receipts = view.getJSONArray("receipts")
                checked(checks, "canonical_revision_two", view.getLong("revision") == 2L)
                checked(checks, "two_receipts", receipts.length() == 2)
                checked(checks, "gift_receipt_preserved", canonicalHash(receipts.getJSONObject(0)) == prior.first.giftReceiptSha256)
                val receipt = receipts.getJSONObject(1)
                val request = receipt.getJSONObject("request")
                val intent = request.getJSONObject("intent")
                val events = receipt.getJSONArray("events"); check(events.length() == 1)
                val event = events.getJSONObject(0)
                val outcome = event.getJSONObject("outcome")
                val audience = outcome.getJSONArray("audience")
                checked(checks, "literal_dialogue_receipt_exact", request.getLong("expected_revision") == 1L &&
                    ReceiptRealEnvironment.canonical(request.getJSONObject("scope")) == ReceiptRealEnvironment.canonical(view.getJSONObject("scope")) &&
                    event.getLong("sequence") == 2L && outcome.getLong("source") == 2L &&
                    audience.length() == 1 && audience.getString(0) == "mira" && intent.getString("kind") == "free_text" &&
                    intent.getJSONObject("value").getString("kind") == "dialogue" && intent.getJSONObject("value").getString("text") == dialogueInput &&
                    outcome.getString("effect") == "said" && outcome.getString("speaker") == "player" && outcome.getString("text") == dialogueInput)
                val accepted = requireNotNull(CandidateLocalModel.store(context).installed())
                checked(checks, "full_model_postcheck", true)
                val handle = actual.forkHandle(); checked(checks, "owner_guard_postcheck", true)
                val profile = JSONObject(localText(CandidateLocalModel.config(accepted).profileBytes(), 4096))
                val play = receipt.getJSONObject("play")
                checked(checks, "local_profile_exact", ReceiptRealEnvironment.canonical(profile) == ReceiptRealEnvironment.canonical(play.getJSONObject("profile")))
                receiptsHash = canonicalHash(receipts); dialogueHash = canonicalHash(receipt)
                repairs = play.getInt("repairs"); fallback = play.getBoolean("fallback")
                handle
            }
            node("story-record-open").performClick(); recordLoaded(deadline)
            section(StoryRecordSection.KNOWLEDGE, deadline)
            check(model.storyRecord.value.nextCursor == null)
            checked(checks, "known_truth_unchanged", model.storyRecord.value.entries.filter { it.origin == StoryRecordOrigin.CANONICAL_TRUTH } == truths)
            search(dialogueInput, deadline)
            val statements = model.storyRecord.value.entries
            checked(checks, "statement_not_truth", model.storyRecord.value.total == 1 && statements.single().origin == StoryRecordOrigin.RECORDED_STATEMENT &&
                statements.single().text == dialogueInput && statements.single().sources == listOf("Event #2"))
            visibleRecord(0)
            compose.onNodeWithTag("story-record-close").performClick()
            io(deadline) { check(canonicalHash(view().getJSONArray("receipts")) == receiptsHash); check(actual.forkHandle() == handle) }
            checked(checks, "source_unopened", ReceiptRealCounts().unopened())
            closePlay(deadline)
            io(deadline) {
                checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
                checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                val trace = workerSnapshot(); workerClosed(trace)
                requireOrdinaryTraceHistory(guards, trace)
                deadline.remaining()
                files.write(OrdinaryRouteProof(phase, identity(), prior.first.identity.pid, prior.first.identity.start, prior.second,
                    deadline.elapsed(), capacity(env), checks, receiptsHash, prior.first.giftReceiptSha256, workerHash(trace),
                    dialogueReceiptSha256 = dialogueHash, repairs = repairs, fallback = fallback, guardsTraceSha256 = workerHash(guards)),
                    mapOf("guards-worker-v2.json" to guards, "dialogue-worker-v2.json" to trace))
                deadline.remaining()
            }
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptOrdinaryReopenTest : ReceiptOrdinaryHarness() {
    @Test fun reopensTwoReceiptsThroughSetupWithoutSdk() {
        val phase = OrdinaryRoutePhase.ORDINARY_REOPEN
        val deadline = selectOrdinary(ReceiptOrdinaryReopenTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { ReceiptRealEnvironment.open(context) }
        val files = OrdinaryFiles(env)
        val prior = io(deadline) { files.prior(phase) }
        checked(checks, "prior_dialogue_proof_exact", true)
        checked(checks, "process_identity_changed", prior.first.identity.pid != Process.myPid() || prior.first.identity.start != Process.getStartElapsedRealtime())
        checked(checks, "memory_eligible", env.memoryEligible())
        launch(checks, deadline)
        checked(checks, "production_transport_local", model.state.value.textProvider == TextProvider.LOCAL)
        resumed(); node("revision").assertTextEquals("Accepted revision · 2")
        node("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
        check(model.state.value.messages.size == 4)
        visibleTranscript(); checked(checks, "retained_transcript_visible", true)
        checked(checks, "no_send_or_cancel", !model.state.value.busy && !model.state.value.preparingResponse)
        val handle = io(deadline) {
            val view = view(); val receipts = view.getJSONArray("receipts")
            checked(checks, "canonical_revision_two", view.getLong("revision") == 2L)
            checked(checks, "two_receipts_exact", receipts.length() == 2 && canonicalHash(receipts) == prior.first.receiptsSha256 &&
                canonicalHash(receipts.getJSONObject(0)) == prior.first.giftReceiptSha256 && canonicalHash(receipts.getJSONObject(1)) == prior.first.dialogueReceiptSha256)
            requireNotNull(CandidateLocalModel.store(context).installed()); checked(checks, "full_model_postcheck", true)
            val handle = actual.forkHandle(); checked(checks, "owner_guard_postcheck", true)
            checked(checks, "source_unopened", ReceiptRealCounts().unopened())
            handle
        }
        closePlay(deadline)
        io(deadline) {
            checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
            checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
            val trace = workerSnapshot(); checked(checks, "worker_zero", workerZero(trace))
            deadline.remaining()
            files.write(OrdinaryRouteProof(phase, identity(), prior.first.identity.pid, prior.first.identity.start, prior.second,
                deadline.elapsed(), capacity(env), checks, prior.first.receiptsSha256, prior.first.giftReceiptSha256, workerHash(trace),
                dialogueReceiptSha256 = prior.first.dialogueReceiptSha256), mapOf("reopen-worker-v2.json" to trace))
            deadline.remaining()
        }
    }
}
