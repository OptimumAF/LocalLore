/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Bundle
import android.os.Looper
import android.os.Process
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.Lifecycle
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Assume.assumeTrue
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

private object ComposeCancellationDiagnostics { val reporter = ReceiptWorkerFailureReporter() }
private val cancelAction = PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira.")
private fun count(snapshot: LiteRtWorkerSnapshot, event: LiteRtWorkerEvent) = snapshot.counts.getValue(event)
private fun unsaturated(snapshot: LiteRtWorkerSnapshot) = check(snapshot.saturated.isEmpty() &&
    !snapshot.timeSaturated && !snapshot.creationsSaturated)
private fun creations(snapshot: LiteRtWorkerSnapshot, roles: List<LiteRtTraceRole>) {
    unsaturated(snapshot)
    check(snapshot.creationsTotal == roles.size && snapshot.creations.map { it.role } == roles)
    check(snapshot.creations.all { it.returnedMs != null && it.failedMs == null && it.failure == LiteRtTraceFailure.NONE })
}
private fun countsEqual(snapshot: LiteRtWorkerSnapshot, value: Int, vararg events: LiteRtWorkerEvent) =
    check(events.all { count(snapshot, it) == value })
private fun sampleReady(snapshot: LiteRtWorkerSnapshot): Boolean {
    unsaturated(snapshot)
    countsEqual(snapshot, 0, LiteRtWorkerEvent.DONE_ENTERED, LiteRtWorkerEvent.ERROR_ENTERED,
        LiteRtWorkerEvent.CANCEL_ENTERED, LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED, LiteRtWorkerEvent.UNCERTAIN)
    check(snapshot.creationsTotal <= 1)
    if (count(snapshot, LiteRtWorkerEvent.SEND_RETURNED) != 1 || count(snapshot, LiteRtWorkerEvent.MESSAGE_RETURNED) < 1) return false
    creations(snapshot, listOf(LiteRtTraceRole.DIRECTOR))
    countsEqual(snapshot, 1, LiteRtWorkerEvent.SEND_ENTERED, LiteRtWorkerEvent.SEND_RETURNED)
    return true
}
private fun cancelledTrace(snapshot: LiteRtWorkerSnapshot, sample: LiteRtWorkerSnapshot) {
    requireCancellationTraceHistory(sample, snapshot)
    creations(snapshot, listOf(LiteRtTraceRole.DIRECTOR))
    countsEqual(snapshot, 1, LiteRtWorkerEvent.SEND_ENTERED, LiteRtWorkerEvent.SEND_RETURNED,
        LiteRtWorkerEvent.CANCEL_ENTERED, LiteRtWorkerEvent.CANCEL_RETURNED, LiteRtWorkerEvent.DRAIN_SETTLED,
        LiteRtWorkerEvent.CONVERSATION_CLOSE_ENTERED, LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN,
        LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED, LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)
    countsEqual(snapshot, 0, LiteRtWorkerEvent.UNCERTAIN)
    val done = count(snapshot, LiteRtWorkerEvent.DONE_ENTERED)
    val error = count(snapshot, LiteRtWorkerEvent.ERROR_ENTERED)
    check((done == 1 && error == 0 || done == 0 && error == 1) &&
        count(snapshot, LiteRtWorkerEvent.DONE_RETURNED) == done && count(snapshot, LiteRtWorkerEvent.ERROR_RETURNED) == error)
    check(count(snapshot, LiteRtWorkerEvent.MESSAGE_RETURNED) >= count(sample, LiteRtWorkerEvent.MESSAGE_RETURNED))
}
private fun recoveredTrace(snapshot: LiteRtWorkerSnapshot) {
    val roles = snapshot.creations.map { it.role }
    check(roles == listOf(LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.NARRATOR) ||
        roles == listOf(LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.NARRATOR))
    creations(snapshot, roles)
    countsEqual(snapshot, roles.size, LiteRtWorkerEvent.CONVERSATION_CREATE_ENTERED, LiteRtWorkerEvent.CONVERSATION_CREATE_RETURNED,
        LiteRtWorkerEvent.SEND_ENTERED, LiteRtWorkerEvent.SEND_RETURNED, LiteRtWorkerEvent.DONE_ENTERED,
        LiteRtWorkerEvent.DONE_RETURNED, LiteRtWorkerEvent.DRAIN_SETTLED, LiteRtWorkerEvent.CONVERSATION_CLOSE_ENTERED,
        LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN)
    countsEqual(snapshot, 0, LiteRtWorkerEvent.ERROR_ENTERED, LiteRtWorkerEvent.ERROR_RETURNED,
        LiteRtWorkerEvent.CANCEL_ENTERED, LiteRtWorkerEvent.CANCEL_RETURNED, LiteRtWorkerEvent.UNCERTAIN)
    countsEqual(snapshot, 1, LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED, LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)
    check(count(snapshot, LiteRtWorkerEvent.MESSAGE_RETURNED) > 0)
}

/** A separate fixed proof family; old source-preflight/import bytes and whitelist remain unchanged. */
private class ComposeCancellationFiles(val env: ReceiptRealEnvironment) {
    private val root = File(env.internal, "receipt-compose-cancel-proof-v1")
    private fun manifest(through: ComposeCancellationPhase): Set<String> = buildSet {
        for (phase in ComposeCancellationPhase.entries.take(through.ordinal + 1)) {
            add("${phase.file}-v1.json"); add("${phase.file}-ready-v1.txt")
        }
        add("cancel-sample-worker-v2.json"); add("cancel-worker-v2.json")
        if (through != ComposeCancellationPhase.UI_CANCEL) add("recover-worker-v2.json")
    }
    fun fresh() { env.admit(); ReceiptRealEnvironment.absent(root) }
    private fun sidecar(name: String, expected: String) {
        val raw = ReceiptRealEnvironment.read(File(root, name), 4096)
        check(raw.isNotEmpty() && raw.all { it.toInt() in 32..126 } && ReceiptRealEnvironment.sha(raw) == expected)
    }
    private fun read(phase: ComposeCancellationPhase): Pair<ComposeCancellationProof, String> {
        val raw = ReceiptRealEnvironment.read(File(root, "${phase.file}-v1.json"), 4096)
        check(raw.isNotEmpty() && raw.all { it.toInt() in 32..126 })
        check(ReceiptRealEnvironment.read(File(root, "${phase.file}-ready-v1.txt"), 0).isEmpty())
        val json = JSONObject(raw.toString(Charsets.US_ASCII))
        fun number(key: String) = ReceiptRealEnvironment.number(json, key)
        fun integer(key: String) = number(key).also { check(it in 0..Int.MAX_VALUE) }.toInt()
        fun boolean(key: String) = json.get(key) as? Boolean ?: error("Invalid proof boolean")
        val flags = json.getJSONObject("checks")
        val checks = flags.keys().asSequence().associateWith { flags.get(it) as? Boolean ?: error("Invalid proof check") }
        val proof = ComposeCancellationProof(phase, CancellationIdentity(integer("pid"), number("start"), integer("uid")),
            integer("prior_pid"), number("prior_start"), json.getString(ComposeCancellationProof.priorKey(phase)), number("elapsed_ms"),
            CancellationCapacity(number("userdata_free_before"), number("userdata_free_after"), number("external_free_before"),
                number("external_free_after"), number("memory_total_bytes"), number("memory_available_before"), number("memory_available_after")),
            checks, if (phase != ComposeCancellationPhase.UI_CANCEL) json.getString("receipt_sha256") else null,
            if (phase == ComposeCancellationPhase.UI_RECOVER) integer("repairs") else null,
            if (phase == ComposeCancellationPhase.UI_RECOVER) boolean("fallback") else null,
            if (phase != ComposeCancellationPhase.UI_REOPEN) json.getString("worker_trace_sha256") else null,
            if (phase == ComposeCancellationPhase.UI_CANCEL) json.getString("sample_worker_trace_sha256") else null)
        check(proof.json().toByteArray(Charsets.US_ASCII).contentEquals(raw)) // Closed keys/types/fixed values and no duplicate JSON keys.
        return proof to ReceiptRealEnvironment.sha(raw)
    }
    fun prior(phase: ComposeCancellationPhase): Pair<ComposeCancellationProof, String> {
        env.admit(); check(phase != ComposeCancellationPhase.UI_CANCEL)
        ReceiptRealEnvironment.strictDirectory(root)
        ReceiptRealEnvironment.entries(root, manifest(if (phase == ComposeCancellationPhase.UI_RECOVER) ComposeCancellationPhase.UI_CANCEL else ComposeCancellationPhase.UI_RECOVER))
        val imported = env.prior(ReceiptRealPhase.IMPORT)
        val cancelled = read(ComposeCancellationPhase.UI_CANCEL)
        check(cancelled.first.priorSha256 == imported.second && cancelled.first.priorPid == imported.first.getInt("pid") &&
            cancelled.first.priorStart == imported.first.getLong("start"))
        sidecar("cancel-sample-worker-v2.json", requireNotNull(cancelled.first.sampleTraceSha256))
        sidecar("cancel-worker-v2.json", requireNotNull(cancelled.first.workerTraceSha256))
        if (phase == ComposeCancellationPhase.UI_RECOVER) return cancelled
        val recovered = read(ComposeCancellationPhase.UI_RECOVER)
        check(recovered.first.priorSha256 == cancelled.second && recovered.first.priorPid == cancelled.first.identity.pid &&
            recovered.first.priorStart == cancelled.first.identity.start)
        sidecar("recover-worker-v2.json", requireNotNull(recovered.first.workerTraceSha256))
        return recovered
    }
    fun write(proof: ComposeCancellationProof, traces: Map<String, LiteRtWorkerSnapshot> = emptyMap()) {
        env.admit()
        val expected = when (proof.phase) {
            ComposeCancellationPhase.UI_CANCEL -> setOf("cancel-sample-worker-v2.json", "cancel-worker-v2.json")
            ComposeCancellationPhase.UI_RECOVER -> setOf("recover-worker-v2.json")
            ComposeCancellationPhase.UI_REOPEN -> emptySet()
        }
        check(traces.keys == expected)
        if (proof.phase == ComposeCancellationPhase.UI_CANCEL) { ReceiptRealEnvironment.absent(root); Files.createDirectory(root.toPath()) }
        ReceiptRealEnvironment.strictDirectory(root)
        for ((name, snapshot) in traces) {
            val raw = snapshot.json().toByteArray(Charsets.US_ASCII)
            check(raw.size in 1..4096)
            val expectedHash = if (name == "cancel-sample-worker-v2.json") proof.sampleTraceSha256 else proof.workerTraceSha256
            check(ReceiptRealEnvironment.sha(raw) == expectedHash)
            ReceiptRealEnvironment.forcedNew(File(root, name), raw)
        }
        ReceiptRealEnvironment.forcedNew(File(root, "${proof.phase.file}-v1.json"), proof.json().toByteArray(Charsets.US_ASCII))
        ReceiptRealEnvironment.forcedNew(File(root, "${proof.phase.file}-ready-v1.txt"), byteArrayOf())
        ReceiptRealEnvironment.entries(root, manifest(proof.phase))
    }
}

private fun identity() = CancellationIdentity(Process.myPid(), Process.getStartElapsedRealtime(), Process.myUid())
private fun traceSha(snapshot: LiteRtWorkerSnapshot) = ReceiptRealEnvironment.sha(snapshot.json().toByteArray(Charsets.US_ASCII))
private fun capacity(env: ReceiptRealEnvironment): CancellationCapacity {
    env.admit()
    val after = env.memory()
    check(after.totalMem == env.memoryBefore.totalMem)
    return CancellationCapacity(env.userdataBefore, env.internal.usableSpace, env.externalBefore, env.external.usableSpace,
        after.totalMem, env.memoryBefore.availMem, after.availMem)
}

/** No action dispatch seam: all story, Send and Cancel operations below use production semantics nodes. */
abstract class ReceiptComposeCancellationHarness : ReceiptRealHarness() {
    @get:Rule val compose = createEmptyComposeRule()
    private var scenario: ActivityScenario<ReceiptComposeCancellationActivity>? = null
    internal lateinit var activity: ReceiptComposeCancellationActivity
    internal lateinit var model: ShellViewModel
    internal val actual get() = activity.actualTransport
    internal val trace get() = activity.workerTrace
    internal fun resumed() = InstrumentationRegistry.getInstrumentation().runOnMainSync {
        check(activity.lifecycle.currentState == Lifecycle.State.RESUMED) { "Receipt UI is not resumed" }
    }

    internal fun selectCompose(type: Class<*>, phase: ComposeCancellationPhase): ReceiptRealDeadline {
        assumeTrue("Exact dedicated Compose cancellation class required",
            InstrumentationRegistry.getArguments().getString("class") == type.name)
        // Only borrow unchanged duration constants, never old class selection or proof emission.
        return ReceiptRealDeadline(if (phase == ComposeCancellationPhase.UI_REOPEN) ReceiptRealPhase.REOPEN else ReceiptRealPhase.PLAY)
            .also { check(it.phase.budgetMs == phase.budgetMs) }
    }
    internal fun launch(checks: MutableMap<String, Boolean>, deadline: ReceiptRealDeadline) {
        scenario = ActivityScenario.launch(ReceiptComposeCancellationActivity::class.java)
        requireNotNull(scenario).onActivity {
            activity = it
            model = ViewModelProvider(it)[ShellViewModel::class.java]
            check(Looper.myLooper() == Looper.getMainLooper())
        }
        checked(checks, "production_main_activity", activity is MainActivity)
        checked(checks, "production_shell_viewmodel", model.javaClass == ShellViewModel::class.java)
        settled(deadline)
        resumed()
    }
    internal fun settled(deadline: ReceiptRealDeadline) {
        // SDK/IO work is external to Compose's virtual clock; never register it as an idling resource.
        compose.waitUntil(deadline.remaining()) { !model.state.value.busy }
        check(!model.state.value.preparingResponse && !model.state.value.checkingCancellation && !model.state.value.recoveryRequired)
    }
    internal fun node(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    internal fun zeroVisible() {
        node("revision").assertTextEquals("Accepted revision · 0")
        node("potion-owner").assertTextEquals("Healing potion · You")
        check(model.state.value.revision == 0L && model.state.value.messages.isEmpty())
    }
    internal fun giftVisible() {
        node("revision").assertTextEquals("Accepted revision · 1")
        node("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
        val state = model.state.value
        check(state.revision == 1L && state.messages.size == 2)
        check(state.messages.single { it.isPlayer }.text == cancelAction.text)
        for (message in state.messages) {
            // Keep dynamically generated narration out of assertion/error messages.
            val displayed = try {
                compose.onNodeWithTag("story-list").performScrollToNode(hasText(message.text))
                compose.onNodeWithText(message.text).isDisplayed()
            } catch (_: Throwable) { false }
            check(displayed) { "Accepted transcript is not visible" }
        }
    }
    internal fun enterGift(checks: MutableMap<String, Boolean>) {
        node("inference-provider").assertTextEquals("Local Rust engine · local inference configured")
        node("play-provider").assertTextEquals(TextProvider.LOCAL.label)
        checked(checks, "local_provider_visible", true)
        node("play-kind-action").assertIsSelected()
        node("play-input").performTextReplacement(cancelAction.text)
        node("play-input").assertTextContains(cancelAction.text)
        checked(checks, "fixed_input_visible", true)
    }
    internal suspend fun nativeView(): JSONObject {
        val state = model.state.value
        check(!state.busy && !state.recoveryRequired)
        val chosen = requireNotNull(state.selectedStory)
        val scope = JSONObject().put("story", chosen.story).put("branch", chosen.branch)
        val session = data(actual, JSONObject().put("op", "resume").put("scope", scope))
        return data(actual, JSONObject().put("op", "play_snapshot").put("session", session.getString("session"))
            .put("scope", scope).put("expected_revision", state.revision))
    }
    internal fun zero(view: JSONObject) {
        check(view.getLong("revision") == 0L && view.getJSONArray("receipts").length() == 0)
        val potion = view.getJSONObject("inventory").getJSONObject("potion")
        check(potion.getString("owner") == "player" && ReceiptRealEnvironment.number(potion, "quantity") == 1L)
    }
    internal fun observing(block: () -> Unit) = runBlocking {
        ComposeCancellationDiagnostics.reporter.run(trace, send = { code, key, json ->
            InstrumentationRegistry.getInstrumentation().sendStatus(code, Bundle().apply { putString(key, json) })
        }) { block() }
    }
    internal fun closeSurface() { scenario?.close(); scenario = null }
    @After fun closeOnlyOwnedSurface() { closeSurface() }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptComposeCancelTest : ReceiptComposeCancellationHarness() {
    @Test fun cancelsRealTurnThroughComposeControls() {
        val phase = ComposeCancellationPhase.UI_CANCEL
        val deadline = selectCompose(ReceiptComposeCancelTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { ReceiptRealEnvironment.open(context) }
        val files = ComposeCancellationFiles(env)
        val prior = io(deadline) { files.fresh(); env.prior(ReceiptRealPhase.IMPORT) }
        checked(checks, "prior_import_proof_exact", true)
        checked(checks, "memory_eligible", env.memoryEligible())
        val access = io(deadline) {
            CandidateLocalModel.store(context).also {
                checked(checks, "candidate_access_receipt", it is ReceiptCandidateModelAccess)
                checked(checks, "accepted_full_recheck", withTimeout(deadline.remaining(60_000)) { it.installed() != null })
                it.admitRuntime(); checked(checks, "runtime_guard_passed", true)
            }
        }
        io(deadline) { ReceiptRealEnvironment.absent(File(env.internal, "workspace-v1")) }
        launch(checks, deadline)
        observing {
            node("empty-library").assertIsDisplayed()
            checked(checks, "empty_library_visible", model.state.value.selectedStory == null)
            var newStoryClicks = 0
            node("reset-demo").assertIsEnabled().performClick(); newStoryClicks++
            checked(checks, "new_story_clicked_once", newStoryClicks == 1)
            settled(deadline)
            checked(checks, "production_transport_local", model.state.value.textProvider == TextProvider.LOCAL)
            zeroVisible(); checked(checks, "initial_zero_visible", true)
            io(deadline) { zero(nativeView()) }; checked(checks, "canonical_zero_before", true)
            val handle = io(deadline) { actual.forkHandle() }
            enterGift(checks)
            var sends = 0
            resumed()
            node("play-send").assertIsEnabled().performClick(); sends++
            checked(checks, "send_clicked_once", sends == 1)
            compose.waitUntil(deadline.remaining(65_000)) { model.state.value.busy && model.state.value.preparingResponse }
            node("busy-status").assertTextEquals("Preparing local response…")
            resumed()
            checked(checks, "preparing_visible", true)
            node("cancel-turn").assertIsDisplayed().assertIsEnabled()
            checked(checks, "cancel_control_displayed", true)
            var sample = trace.snapshot()
            compose.waitUntil(deadline.remaining(65_000)) {
                check(model.state.value.busy && model.state.value.preparingResponse) { "Compose cancellation window missed" }
                sample = trace.snapshot()
                sampleReady(sample)
            }
            check(model.state.value.busy && model.state.value.preparingResponse && sampleReady(sample))
            resumed()
            checked(checks, "sampled_public_inflight", true)
            // The production button invokes ShellViewModel.cancel(), including its actual caller cancellation.
            var cancels = 0
            compose.onNodeWithTag("cancel-turn").performClick(); cancels++
            checked(checks, "cancel_clicked_once", cancels == 1)
            settled(deadline)
            resumed()
            node("notice").assertTextEquals("Cancellation checked. Showing the accepted saved history.")
            zeroVisible(); checked(checks, "cancellation_settled_visible", true)
            io(deadline) {
                cancelledTrace(trace.snapshot(), sample)
                check(actual.forkHandle() == handle)
                checked(checks, "worker_drain_closed_known", true)
                zero(nativeView()); checked(checks, "canonical_zero_after", true)
                requireNotNull(access.installed())
                checked(checks, "accepted_post_sdk_full_recheck", true)
                check(actual.forkHandle() == handle) // Reject late fencing during the full hash.
                checked(checks, "source_unopened", ReceiptRealCounts().unopened())
            }
            closeSurface() // After settled success only; Activity.onStop cannot earn cancellation.
            io(deadline) {
                checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
                checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                val final = trace.snapshot()
                cancelledTrace(final, sample)
                deadline.remaining()
                files.write(ComposeCancellationProof(phase, identity(), prior.first.getInt("pid"), prior.first.getLong("start"),
                    prior.second, deadline.elapsed(), capacity(env), checks,
                    workerTraceSha256 = traceSha(final), sampleTraceSha256 = traceSha(sample)),
                    mapOf("cancel-sample-worker-v2.json" to sample, "cancel-worker-v2.json" to final))
                deadline.remaining()
            }
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptComposeRecoverTest : ReceiptComposeCancellationHarness() {
    @Test fun sendsRecoveryGiftThroughCompose() {
        val phase = ComposeCancellationPhase.UI_RECOVER
        val deadline = selectCompose(ReceiptComposeRecoverTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { ReceiptRealEnvironment.open(context) }
        val files = ComposeCancellationFiles(env)
        val prior = io(deadline) { files.prior(phase) }
        checked(checks, "prior_cancel_proof_exact", true)
        checked(checks, "process_identity_changed", prior.first.identity.pid != Process.myPid() || prior.first.identity.start != Process.getStartElapsedRealtime())
        checked(checks, "memory_eligible", env.memoryEligible())
        val access = io(deadline) {
            CandidateLocalModel.store(context).also {
                checked(checks, "candidate_access_receipt", it is ReceiptCandidateModelAccess)
                checked(checks, "accepted_full_recheck", withTimeout(deadline.remaining(60_000)) { it.installed() != null })
                it.admitRuntime(); checked(checks, "runtime_guard_passed", true)
            }
        }
        launch(checks, deadline)
        checked(checks, "production_transport_local", model.state.value.textProvider == TextProvider.LOCAL)
        observing {
            zeroVisible(); checked(checks, "initial_zero_visible", true)
            io(deadline) { zero(nativeView()) }; checked(checks, "initial_canonical_zero", true)
            val handle = io(deadline) { actual.forkHandle() }
            enterGift(checks)
            var sends = 0
            resumed()
            node("play-send").assertIsEnabled().performClick(); sends++
            checked(checks, "send_clicked_once", sends == 1)
            compose.waitUntil(deadline.remaining()) { !model.state.value.busy && model.state.value.revision == 1L || model.state.value.recoveryRequired }
            settled(deadline)
            resumed()
            node("notice").assertTextEquals("Outcome accepted and saved by the local engine.")
            giftVisible(); checked(checks, "accepted_gift_visible", true)
            var receiptHash = ""
            var repairs = -1
            var fallback = false
            io(deadline) {
                recoveredTrace(trace.snapshot())
                check(actual.forkHandle() == handle)
                checked(checks, "worker_drain_closed_known", true)
                val view = nativeView()
                val receipt = gift(view)
                checked(checks, "canonical_revision_one", view.getLong("revision") == 1L)
                checked(checks, "canonical_given_to_mira", true)
                checked(checks, "canonical_single_receipt", view.getJSONArray("receipts").length() == 1)
                val accepted = requireNotNull(access.installed())
                checked(checks, "accepted_post_sdk_full_recheck", true)
                check(actual.forkHandle() == handle)
                val play = receipt.getJSONObject("play")
                val expected = JSONObject(localText(CandidateLocalModel.config(accepted).profileBytes(), 4096))
                checked(checks, "local_profile_exact", ReceiptRealEnvironment.canonical(play.getJSONObject("profile")) == ReceiptRealEnvironment.canonical(expected))
                receiptHash = ReceiptRealEnvironment.sha(ReceiptRealEnvironment.canonical(receipt).toByteArray(Charsets.UTF_8))
                repairs = play.getInt("repairs"); fallback = play.getBoolean("fallback")
                checked(checks, "source_unopened", ReceiptRealCounts().unopened())
            }
            closeSurface()
            io(deadline) {
                checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
                checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                val final = trace.snapshot()
                recoveredTrace(final)
                deadline.remaining()
                files.write(ComposeCancellationProof(phase, identity(), prior.first.identity.pid, prior.first.identity.start,
                    prior.second, deadline.elapsed(), capacity(env), checks, receiptSha256 = receiptHash,
                    repairs = repairs, fallback = fallback, workerTraceSha256 = traceSha(final)), mapOf("recover-worker-v2.json" to final))
                deadline.remaining()
            }
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptComposeReopenTest : ReceiptComposeCancellationHarness() {
    @Test fun showsRecoveredGiftWithoutSdk() {
        val phase = ComposeCancellationPhase.UI_REOPEN
        val deadline = selectCompose(ReceiptComposeReopenTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { ReceiptRealEnvironment.open(context) }
        val files = ComposeCancellationFiles(env)
        val prior = io(deadline) { files.prior(phase) }
        checked(checks, "prior_recover_proof_exact", true)
        checked(checks, "process_identity_changed", prior.first.identity.pid != Process.myPid() || prior.first.identity.start != Process.getStartElapsedRealtime())
        checked(checks, "memory_eligible", env.memoryEligible())
        io(deadline) {
            val access = CandidateLocalModel.store(context)
            checked(checks, "candidate_access_receipt", access is ReceiptCandidateModelAccess)
            checked(checks, "accepted_full_recheck", access.installed() != null)
            access.admitRuntime(); checked(checks, "runtime_guard_passed", true)
        }
        launch(checks, deadline)
        resumed()
        checked(checks, "production_transport_local", model.state.value.textProvider == TextProvider.LOCAL)
        giftVisible(); checked(checks, "retained_gift_visible", true)
        checked(checks, "no_send_or_cancel", !model.state.value.busy && !model.state.value.preparingResponse)
        var receiptHash = ""
        val handle = io(deadline) {
            val view = nativeView()
            val receipt = gift(view)
            checked(checks, "canonical_revision_one", view.getLong("revision") == 1L)
            receiptHash = ReceiptRealEnvironment.sha(ReceiptRealEnvironment.canonical(receipt).toByteArray(Charsets.UTF_8))
            checked(checks, "canonical_gift_receipt_unchanged", receiptHash == prior.first.receiptSha256)
            checked(checks, "source_unopened", ReceiptRealCounts().unopened())
            actual.forkHandle()
        }
        closeSurface()
        io(deadline) {
            checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
            checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
            val final = trace.snapshot()
            checked(checks, "no_worker_events", final.counts.values.all { it == 0 } && final.creationsTotal == 0 &&
                final.saturated.isEmpty() && !final.creationsSaturated && !final.timeSaturated)
            deadline.remaining()
            files.write(ComposeCancellationProof(phase, identity(), prior.first.identity.pid, prior.first.identity.start,
                prior.second, deadline.elapsed(), capacity(env), checks, receiptSha256 = receiptHash))
            deadline.remaining()
        }
    }
}
