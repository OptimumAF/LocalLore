/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Bundle
import android.os.Looper
import android.os.Process
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.async
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

private object CancellationDiagnostics { val reporter = ReceiptWorkerFailureReporter() }
private val cancelAction = PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira.")
private fun mainThread() = check(Looper.myLooper() == Looper.getMainLooper())
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

/** Gateway calls stay on Main. This observer never reroutes, delays or replaces production work. */
private class CancellationObserved(private val actual: NativeWorkspaceTransport) : WorkspaceTransport {
    var mainConfined = true
    var freeText = 0
    var commits = 0
    var fixedIntent = false
    override suspend fun exchange(command: JSONObject): JSONObject {
        mainConfined = mainConfined && Looper.myLooper() == Looper.getMainLooper()
        mainThread()
        when (command.getString("op")) {
            "free_text" -> {
                freeText++
                val intent = command.getJSONObject("request").getJSONObject("intent")
                fixedIntent = intent.getString("kind") == "free_text" && intent.getJSONObject("value").getString("kind") == "action" &&
                    intent.getJSONObject("value").getString("text") == cancelAction.text
            }
            "commit" -> commits++
        }
        // The actual transport's own worker() guard enforces its IO handoff; no test IO wrapper masks it.
        return actual.exchange(command)
    }
    override fun close() { mainThread(); actual.close() }
}

/** A separate fixed proof family; old source-preflight/import bytes and whitelist remain unchanged. */
private class CancellationFiles(val env: ReceiptRealEnvironment) {
    private val root = File(env.internal, "receipt-cancel-proof-v1")
    private fun manifest(through: CancellationPhase): Set<String> = buildSet {
        for (phase in CancellationPhase.entries.take(through.ordinal + 1)) {
            add("${phase.file}-v1.json"); add("${phase.file}-ready-v1.txt")
        }
        add("cancel-sample-worker-v2.json"); add("cancel-worker-v2.json")
        if (through != CancellationPhase.CANCEL) add("recover-worker-v2.json")
    }
    fun fresh() { env.admit(); ReceiptRealEnvironment.absent(root) }
    private fun sidecar(name: String, expected: String) {
        val raw = ReceiptRealEnvironment.read(File(root, name), 4096)
        check(raw.isNotEmpty() && raw.all { it.toInt() in 32..126 } && ReceiptRealEnvironment.sha(raw) == expected)
    }
    private fun read(phase: CancellationPhase): Pair<CancellationProof, String> {
        val raw = ReceiptRealEnvironment.read(File(root, "${phase.file}-v1.json"), 4096)
        check(raw.isNotEmpty() && raw.all { it.toInt() in 32..126 })
        check(ReceiptRealEnvironment.read(File(root, "${phase.file}-ready-v1.txt"), 0).isEmpty())
        val json = JSONObject(raw.toString(Charsets.US_ASCII))
        fun number(key: String) = ReceiptRealEnvironment.number(json, key)
        fun integer(key: String) = number(key).also { check(it in 0..Int.MAX_VALUE) }.toInt()
        fun boolean(key: String) = json.get(key) as? Boolean ?: error("Invalid proof boolean")
        val flags = json.getJSONObject("checks")
        val checks = flags.keys().asSequence().associateWith { flags.get(it) as? Boolean ?: error("Invalid proof check") }
        val proof = CancellationProof(phase, CancellationIdentity(integer("pid"), number("start"), integer("uid")),
            integer("prior_pid"), number("prior_start"), json.getString(CancellationProof.priorKey(phase)), number("elapsed_ms"),
            CancellationCapacity(number("userdata_free_before"), number("userdata_free_after"), number("external_free_before"),
                number("external_free_after"), number("memory_total_bytes"), number("memory_available_before"), number("memory_available_after")),
            checks, if (phase != CancellationPhase.CANCEL) json.getString("receipt_sha256") else null,
            if (phase == CancellationPhase.RECOVER) integer("repairs") else null,
            if (phase == CancellationPhase.RECOVER) boolean("fallback") else null,
            if (phase != CancellationPhase.REOPEN) json.getString("worker_trace_sha256") else null,
            if (phase == CancellationPhase.CANCEL) json.getString("sample_worker_trace_sha256") else null)
        check(proof.json().toByteArray(Charsets.US_ASCII).contentEquals(raw)) // Closed keys/types/fixed values and no duplicate JSON keys.
        return proof to ReceiptRealEnvironment.sha(raw)
    }
    fun prior(phase: CancellationPhase): Pair<CancellationProof, String> {
        env.admit(); check(phase != CancellationPhase.CANCEL)
        ReceiptRealEnvironment.strictDirectory(root)
        ReceiptRealEnvironment.entries(root, manifest(if (phase == CancellationPhase.RECOVER) CancellationPhase.CANCEL else CancellationPhase.RECOVER))
        val imported = env.prior(ReceiptRealPhase.IMPORT)
        val cancelled = read(CancellationPhase.CANCEL)
        check(cancelled.first.priorSha256 == imported.second && cancelled.first.priorPid == imported.first.getInt("pid") &&
            cancelled.first.priorStart == imported.first.getLong("start"))
        sidecar("cancel-sample-worker-v2.json", requireNotNull(cancelled.first.sampleTraceSha256))
        sidecar("cancel-worker-v2.json", requireNotNull(cancelled.first.workerTraceSha256))
        if (phase == CancellationPhase.RECOVER) return cancelled
        val recovered = read(CancellationPhase.RECOVER)
        check(recovered.first.priorSha256 == cancelled.second && recovered.first.priorPid == cancelled.first.identity.pid &&
            recovered.first.priorStart == cancelled.first.identity.start)
        sidecar("recover-worker-v2.json", requireNotNull(recovered.first.workerTraceSha256))
        return recovered
    }
    fun write(proof: CancellationProof, traces: Map<String, LiteRtWorkerSnapshot> = emptyMap()) {
        env.admit()
        val expected = when (proof.phase) {
            CancellationPhase.CANCEL -> setOf("cancel-sample-worker-v2.json", "cancel-worker-v2.json")
            CancellationPhase.RECOVER -> setOf("recover-worker-v2.json")
            CancellationPhase.REOPEN -> emptySet()
        }
        check(traces.keys == expected)
        if (proof.phase == CancellationPhase.CANCEL) { ReceiptRealEnvironment.absent(root); Files.createDirectory(root.toPath()) }
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

private fun selected(type: Class<*>, phase: CancellationPhase): ReceiptRealDeadline {
    assumeTrue("Exact dedicated cancellation class selection is required",
        InstrumentationRegistry.getArguments().getString("class") == type.name)
    // Deadline-only reuse of the unchanged 170/120-second caps, never old proof/selection/emission.
    val deadline = ReceiptRealDeadline(if (phase == CancellationPhase.REOPEN) ReceiptRealPhase.REOPEN else ReceiptRealPhase.PLAY)
    check(deadline.phase.budgetMs == phase.budgetMs)
    return deadline
}
private fun traceSha(snapshot: LiteRtWorkerSnapshot) = ReceiptRealEnvironment.sha(snapshot.json().toByteArray(Charsets.US_ASCII))
private fun identity() = CancellationIdentity(Process.myPid(), Process.getStartElapsedRealtime(), Process.myUid())
private fun capacity(env: ReceiptRealEnvironment): CancellationCapacity {
    env.admit()
    val after = env.memory()
    check(after.totalMem == env.memoryBefore.totalMem)
    return CancellationCapacity(env.userdataBefore, env.internal.usableSpace, env.externalBefore, env.external.usableSpace,
        after.totalMem, env.memoryBefore.availMem, after.availMem)
}
private fun zero(view: JSONObject) {
    check(view.getLong("revision") == 0L && view.getJSONArray("receipts").length() == 0)
    val potion = view.getJSONObject("inventory").getJSONObject("potion")
    check(potion.getString("owner") == "player" && ReceiptRealEnvironment.number(potion, "quantity") == 1L)
}
private suspend fun observeFailure(trace: LiteRtWorkerTrace, block: suspend () -> Unit) =
    CancellationDiagnostics.reporter.run(trace, send = { code, key, json ->
        InstrumentationRegistry.getInstrumentation().sendStatus(code, Bundle().apply { putString(key, json) })
    }, block = block)

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptRealCancelTest : ReceiptRealHarness() {
    @Test fun cancelsSampledPublicInferenceWithoutCommit() {
        val phase = CancellationPhase.CANCEL
        val deadline = selected(ReceiptRealCancelTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        io(deadline) {
            val env = ReceiptRealEnvironment.open(context)
            val files = CancellationFiles(env).also { it.fresh() }
            val prior = env.prior(ReceiptRealPhase.IMPORT)
            checked(checks, "prior_import_proof_exact", true)
            checked(checks, "memory_eligible", env.memoryEligible())
            val access = CandidateLocalModel.store(context)
            checked(checks, "candidate_access_receipt", access is ReceiptCandidateModelAccess)
            checked(checks, "accepted_full_recheck", withTimeout(deadline.remaining(60_000)) { access.installed() != null })
            access.admitRuntime(); checked(checks, "runtime_guard_passed", true)
            ReceiptRealEnvironment.absent(File(env.internal, "workspace-v1"))
            val trace = LiteRtWorkerTrace()
            val actual = withContext(Dispatchers.Main.immediate) { CandidateLocalModel.createTransport(context, trace) }
            val observed = CancellationObserved(actual)
            val gateway = DurableGateway(observed)
            val originalScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            var original: Deferred<DemoResult>? = null
            try {
                observeFailure(trace) {
                    val initial = withContext(Dispatchers.Main.immediate) { gateway.initialize() }
                    checked(checks, "production_transport_local", initial.textProvider == TextProvider.LOCAL)
                    zero(snapshot(actual, initial)); checked(checks, "canonical_zero_before", true)
                    val handle = actual.forkHandle() // Capture before the active SDK request.
                    val preparing = originalScope.async { mainThread(); gateway.respondText(cancelAction, 0) }.also { original = it }
                    val sampled = withContext(Dispatchers.Main.immediate) {
                        withTimeout(deadline.remaining(65_000)) {
                            var sample = trace.snapshot()
                            while (true) {
                                check(preparing.isActive) { "Cancellation window missed" }
                                if (sampleReady(sample)) break
                                delay(5) // Passive bounded observation only; no SDK callback or work is delayed.
                                sample = trace.snapshot()
                            }
                            check(preparing.isActive)
                            sample
                        }
                    }
                    checked(checks, "sampled_public_inflight", true)
                    var foregroundCancels = 0
                    withContext(Dispatchers.Main.immediate) { mainThread(); foregroundCancels++; gateway.cancelSaved() }
                    checked(checks, "cancel_saved_called_once", foregroundCancels == 1)
                    val result = withTimeout(deadline.remaining(70_000)) { preparing.await() }
                    checked(checks, "original_response_joined", true)
                    checked(checks, "response_rejected_cancelled", result is DemoResult.Rejected && result.category == "Cancelled")
                    checked(checks, "no_prepared_or_commit", result !is DemoResult.Prepared && observed.commits == 0)
                    val finalTrace = trace.snapshot()
                    cancelledTrace(finalTrace, sampled)
                    checked(checks, "sdk_cancel_entered_returned", true)
                    // This post-join production guard also refuses active/poisoned owners without an SDK probe.
                    check(actual.forkHandle() == handle)
                    checked(checks, "worker_drain_closed_known", true)
                    val saved = withContext(Dispatchers.Main.immediate) { gateway.snapshot() }
                    zero(snapshot(actual, saved)); checked(checks, "canonical_zero_after", true)
                    checked(checks, "fixed_free_text_submitted_once", observed.freeText == 1 && observed.fixedIntent)
                    checked(checks, "gateway_main_confined", observed.mainConfined)
                    withTimeout(deadline.remaining()) { requireNotNull(access.installed()) }
                    checked(checks, "accepted_post_sdk_full_recheck", true)
                    checked(checks, "source_unopened", ReceiptRealCounts().unopened()) // No source object is resolved in this class.
                    withContext(Dispatchers.Main.immediate) { gateway.close() }
                    checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
                    checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                    deadline.remaining()
                    val proof = CancellationProof(phase, identity(), prior.first.getInt("pid"), prior.first.getLong("start"),
                        prior.second, deadline.elapsed(), capacity(env), checks,
                        workerTraceSha256 = traceSha(finalTrace), sampleTraceSha256 = traceSha(sampled))
                    files.write(proof, mapOf("cancel-sample-worker-v2.json" to sampled, "cancel-worker-v2.json" to finalTrace))
                }
            } finally {
                withContext(NonCancellable + Dispatchers.Main.immediate) { gateway.close() }
                // Observe this original task; never cancel it to manufacture successful SDK drain.
                withContext(NonCancellable) {
                    try { withTimeout(deadline.remaining(5_000)) { original?.await() } } catch (_: Throwable) { }
                    if (original == null || original?.isCompleted == true) originalScope.cancel()
                    // An unreturned task retains its scope/owner; the method fails and emits no positive proof.
                }
            }
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptRealRecoverTest : ReceiptRealHarness() {
    @Test fun recoversCancelledWorkspaceAndCommitsOneRealGift() {
        val phase = CancellationPhase.RECOVER
        val deadline = selected(ReceiptRealRecoverTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        io(deadline) {
            val env = ReceiptRealEnvironment.open(context)
            val files = CancellationFiles(env)
            val prior = files.prior(phase)
            checked(checks, "prior_cancel_proof_exact", true)
            checked(checks, "process_identity_changed", prior.first.identity.pid != Process.myPid() || prior.first.identity.start != Process.getStartElapsedRealtime())
            checked(checks, "memory_eligible", env.memoryEligible())
            val access = CandidateLocalModel.store(context)
            checked(checks, "accepted_full_recheck", withTimeout(deadline.remaining(60_000)) { access.installed() != null })
            access.admitRuntime(); checked(checks, "runtime_guard_passed", true)
            val trace = LiteRtWorkerTrace()
            val actual = withContext(Dispatchers.Main.immediate) { CandidateLocalModel.createTransport(context, trace) }
            val observed = CancellationObserved(actual)
            val gateway = DurableGateway(observed, autoCreateIfEmpty = false)
            try {
                observeFailure(trace) {
                    val initial = withContext(Dispatchers.Main.immediate) { gateway.initialize() }
                    checked(checks, "production_transport_local", initial.textProvider == TextProvider.LOCAL)
                    zero(snapshot(actual, initial)); checked(checks, "initial_canonical_zero", true)
                    val prepared = withContext(Dispatchers.Main.immediate) { gateway.respondText(cancelAction, 0) }
                    check(prepared is DemoResult.Prepared) { "One real recovery turn must prepare; no retry" }
                    val finalTrace = trace.snapshot()
                    recoveredTrace(finalTrace)
                    checked(checks, "prepared_after_known_worker_close", true)
                    // Actual production transport/worker guards enforced off-Main native work; this is not a wrapper thread measurement.
                    checked(checks, "native_worker_off_main", true)
                    val acceptedFiles = withTimeout(deadline.remaining()) { requireNotNull(access.installed()) }
                    checked(checks, "accepted_post_sdk_full_recheck", true)
                    access.admitRuntime()
                    checked(checks, "fixed_free_text_submitted_once", observed.freeText == 1 && observed.fixedIntent)
                    check(withContext(Dispatchers.Main.immediate) { gateway.commitAsync(prepared) } is DemoResult.Accepted)
                    val saved = withContext(Dispatchers.Main.immediate) { gateway.snapshot() }
                    val view = snapshot(actual, saved)
                    val receipt = gift(view)
                    checked(checks, "canonical_revision_one", saved.revision == 1L)
                    checked(checks, "canonical_given_to_mira", true)
                    checked(checks, "canonical_single_receipt", view.getJSONArray("receipts").length() == 1)
                    val play = receipt.getJSONObject("play")
                    val expected = JSONObject(localText(CandidateLocalModel.config(acceptedFiles).profileBytes(), 4096))
                    checked(checks, "local_profile_exact", ReceiptRealEnvironment.canonical(play.getJSONObject("profile")) == ReceiptRealEnvironment.canonical(expected))
                    checked(checks, "source_unopened", ReceiptRealCounts().unopened())
                    checked(checks, "gateway_main_confined", observed.mainConfined)
                    val handle = actual.forkHandle()
                    withContext(Dispatchers.Main.immediate) { gateway.close() }
                    checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
                    checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                    deadline.remaining()
                    files.write(CancellationProof(phase, identity(), prior.first.identity.pid, prior.first.identity.start,
                        prior.second, deadline.elapsed(), capacity(env), checks,
                        receiptSha256 = ReceiptRealEnvironment.sha(ReceiptRealEnvironment.canonical(receipt).toByteArray(Charsets.UTF_8)),
                        repairs = play.getInt("repairs"), fallback = play.getBoolean("fallback"), workerTraceSha256 = traceSha(finalTrace)),
                        mapOf("recover-worker-v2.json" to finalTrace))
                }
            } finally { withContext(NonCancellable + Dispatchers.Main.immediate) { gateway.close() } }
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptRealCancelReopenTest : ReceiptRealUiHarness() {
    @Test fun reopensRecoveredReceiptWithoutSdk() {
        val phase = CancellationPhase.REOPEN
        val deadline = selected(ReceiptRealCancelReopenTest::class.java, phase)
        val checks = linkedMapOf<String, Boolean>()
        val counts = ReceiptRealCounts()
        val files = io(deadline) { CancellationFiles(ReceiptRealEnvironment.open(context)) }
        val env = files.env
        val prior = io(deadline) { files.prior(phase) }
        checked(checks, "prior_recover_proof_exact", true)
        checked(checks, "process_identity_changed", prior.first.identity.pid != Process.myPid() || prior.first.identity.start != Process.getStartElapsedRealtime())
        checked(checks, "memory_eligible", env.memoryEligible())
        launch(deadline, counts)
        await(deadline, LocalModelSetupPhase.READY, 90_000)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        checked(checks, "setup_ready_after_reopen", model.state.value.ready)
        io(deadline) {
            val access = CandidateLocalModel.store(context)
            checked(checks, "candidate_access_receipt", access is ReceiptCandidateModelAccess)
            checked(checks, "accepted_full_recheck", access.installed() != null)
            access.admitRuntime(); checked(checks, "runtime_guard_passed", true)
            val actual = withContext(Dispatchers.Main.immediate) { CandidateLocalModel.createTransport(context) }
            val observed = CancellationObserved(actual)
            val gateway = DurableGateway(observed, autoCreateIfEmpty = false)
            try {
                val saved = withContext(Dispatchers.Main.immediate) { gateway.initialize() }
                checked(checks, "production_transport_local", saved.textProvider == TextProvider.LOCAL)
                val receipt = gift(snapshot(actual, saved))
                checked(checks, "canonical_revision_one", saved.revision == 1L)
                val hash = ReceiptRealEnvironment.sha(ReceiptRealEnvironment.canonical(receipt).toByteArray(Charsets.UTF_8))
                checked(checks, "canonical_gift_receipt_unchanged", hash == prior.first.receiptSha256)
                checked(checks, "no_free_text_call", observed.freeText == 0 && observed.commits == 0)
                checked(checks, "source_unopened", counts.unopened())
                checked(checks, "gateway_main_confined", observed.mainConfined)
                val handle = actual.forkHandle()
                withContext(Dispatchers.Main.immediate) { gateway.close() }
                checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                deadline.remaining()
                files.write(CancellationProof(phase, identity(), prior.first.identity.pid, prior.first.identity.start,
                    prior.second, deadline.elapsed(), capacity(env), checks, receiptSha256 = hash))
            } finally { withContext(NonCancellable + Dispatchers.Main.immediate) { gateway.close() } }
        }
    }
}
