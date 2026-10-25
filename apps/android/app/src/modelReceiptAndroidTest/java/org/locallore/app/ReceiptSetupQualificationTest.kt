/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Process
import android.os.Bundle
import android.os.SystemClock
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ReceiptSetupFixture.Case
import org.locallore.app.ReceiptSetupFixture.Phase

/** Fixed callbacks exercise real setup/receipt access, not DocumentsUI or provider grants. */
abstract class ReceiptSetupUiHarness {
    @get:Rule val compose = createEmptyComposeRule()
    internal val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    internal val context get() = instrumentation.targetContext
    internal var scenario: ActivityScenario<out ReceiptSetupFixtureActivity>? = null
    internal lateinit var model: LocalModelSetupViewModel
    private lateinit var failureTrace: ReceiptSetupFailureTrace
    private var selectedSource: ReceiptSetupFixture.Source? = null
    private val sources = mutableListOf<ReceiptSetupFixture.Source>()
    private val gates = mutableListOf<ReceiptSetupFixture.Gate>()
    private val observers = mutableListOf<CoroutineScope>()

    internal fun source(blocked: Boolean = false) = ReceiptSetupFixture.Source(blocked).also { sources += it }
    internal fun gate(case: Case) = ReceiptSetupFixture.arm(case).also { gates += it }
    internal fun launch(type: Class<out ReceiptSetupFixtureActivity>) {
        scenario = ActivityScenario.launch(type)
        captureCurrentActivity()
    }
    internal fun captureCurrentActivity() {
        selectedSource = null
        // This is the current Activity's trace; retained-VM operation events can
        // still belong to the original Activity's dependency closure.
        requireNotNull(scenario).onActivity { model = it.setupController; failureTrace = it.failureTrace }
    }
    internal fun main(action: () -> Unit) = instrumentation.runOnMainSync { action() }
    internal fun await(phase: LocalModelSetupPhase) {
        ReceiptSetupFailureReporter.run(
            claim = { ReceiptSetupFixture.claimFailureEmission() },
            snapshot = {
                val progress = selectedSource?.progress() ?: ReceiptSetupSourceProgress()
                failureTrace.snapshot(phase, model.state.value.phase, progress)
            },
            send = { code, key, json ->
                instrumentation.sendStatus(code, Bundle().apply { putString(key, json) })
            },
            block = { compose.waitUntil(10_000) { model.state.value.phase == phase } },
        )
    }
    internal fun select(source: ReceiptSetupFixture.Source) = main {
        selectedSource = source
        check(model.beginPicker())
        model.completePicker(source::open)
    }
    internal fun ready() {
        await(LocalModelSetupPhase.READY)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        compose.onNodeWithTag("model-expected-hash").assertTextEquals("SHA-256 · ${ReceiptSetupFixture.HASH}")
    }
    internal fun missing() {
        await(LocalModelSetupPhase.MISSING)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("model-choose").performScrollTo().assertIsEnabled()
    }
    internal fun recheck() {
        selectedSource = null
        compose.onNodeWithTag("model-recheck").performScrollTo().performClick()
    }
    internal fun cancel() = compose.onNodeWithTag("model-import-cancel").performScrollTo().performClick()
    internal fun history(target: LocalModelSetupViewModel): Pair<CopyOnWriteArrayList<LocalModelSetupPhase>, Job> {
        val values = CopyOnWriteArrayList<LocalModelSetupPhase>()
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate).also { observers += it }
        var job: Job? = null
        main { job = scope.launch { target.state.collect { values += it.phase } } }
        return values to requireNotNull(job)
    }
    internal fun check(checks: MutableMap<String, Boolean>, name: String, actual: Boolean) {
        assertTrue(name, actual)
        assertNull("Duplicate proof check", checks.put(name, actual))
    }
    internal fun busy(env: ReceiptSetupFixture.Environment, case: Case): Boolean = io {
        try { env.access(case).installed(); false }
        catch (failure: LocalModelException) {
            assertEquals(LocalModelFailure.BUSY, failure.failure)
            true
        }
    }
    internal fun <T> io(action: suspend () -> T): T = runBlocking { withContext(Dispatchers.IO) { action() } }
    @After fun releaseOnlyCurrentFixtureResources() {
        gates.forEach { it.release.countDown() }
        sources.forEach { it.release.countDown() }
        scenario?.close(); scenario = null
        observers.forEach { it.cancel() }
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (sources.any { it.active.get() != 0 } && SystemClock.elapsedRealtime() < deadline) Thread.sleep(10)
        assertTrue("Current fixture sources must actually close", sources.all { it.active.get() == 0 })
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptSetupQualificationTest : ReceiptSetupUiHarness() {
    @Test fun importsAndRechecksThroughActualReceiptSetup() {
        val checks = linkedMapOf<String, Boolean>()
        val env = io { ReceiptSetupFixture.open(context).also { it.fresh(Case.ACCEPT) } }
        io {
            val candidate: CandidateModelAccess = CandidateLocalModel.store(context)
            check(checks, "candidate_access_receipt", candidate is ReceiptCandidateModelAccess)
            check(checks, "candidate_identity_fixed", CandidateLocalModel.identity.id == "gemma-4-e2b-it-litertlm-a790a852" &&
                CandidateLocalModel.identity.bytes == 2_588_147_712L && CandidateLocalModel.identity.sha256 ==
                "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c")
            val control = File(env.internal, "local-model-receipt-control-v1")
            val data = File(env.external, "local-model-receipt-data-v1")
            val files = candidate.plannedFiles()
            check(checks, "candidate_roots_context", AndroidReceiptModelAccess.CONTROL_CHILD == control.name &&
                AndroidReceiptModelAccess.DATA_CHILD == data.name && files.root == data &&
                files.model == File(data, "model.litertlm") && files.cache == File(data, "cache"))
            check(checks, "candidate_absent_noncreating", !Files.exists(control.toPath(), NOFOLLOW_LINKS) &&
                !Files.exists(data.toPath(), NOFOLLOW_LINKS) && candidate.installed() == null &&
                !Files.exists(control.toPath(), NOFOLLOW_LINKS) && !Files.exists(data.toPath(), NOFOLLOW_LINKS))
        }
        launch(ReceiptSetupAcceptActivity::class.java)
        missing()
        val selected = source()
        select(selected); ready()
        check(checks, "ui_ready_after_import", model.state.value.ready)
        io { env.assertRecords(Case.ACCEPT, accepted = true) }
        check(checks, "accepted_records_exact", true)
        recheck(); ready()
        check(checks, "ui_recheck_ready", model.state.value.ready)
        requireNotNull(scenario).recreate()
        captureCurrentActivity()
        ready()
        check(checks, "activity_recreation_ready", model.state.value.ready)
        val unopened = source()
        io { env.access(Case.ACCEPT).import(unopened::open); env.assertRecords(Case.ACCEPT, accepted = true) }
        check(checks, "reopen_source_unopened", unopened.opened.get() == 0)
        check(checks, "source_opened_once", selected.opened.get() == 1)
        check(checks, "source_closed_once", selected.closed.get() == 1 && selected.active.get() == 0)
        check(checks, "sdk_not_opened", ReceiptSetupFixture.playAttempts.get() == 0)
        io { env.proof(Phase.SETUP, checks, selected.opened.get(), selected.closed.get()) }
    }

    @Test fun cancelsBeforeAndAfterAcceptanceThroughCompose() {
        val checks = linkedMapOf<String, Boolean>()
        val env = io { ReceiptSetupFixture.open(context).also { it.fresh(Case.CANCEL_BEFORE, Case.CANCEL_AFTER) } }
        var opened = 0
        var closed = 0
        for (case in listOf(Case.CANCEL_BEFORE, Case.CANCEL_AFTER)) {
            val after = case == Case.CANCEL_AFTER
            val prefix = if (after) "after" else "before"
            val held = gate(case)
            launch(if (after) ReceiptSetupCancelAfterActivity::class.java else ReceiptSetupCancelBeforeActivity::class.java)
            missing()
            val selected = source()
            select(selected)
            assertTrue("Current receipt checkpoint must be reached", held.reached.await(10, TimeUnit.SECONDS))
            check(checks, "${prefix}_checkpoint_reached", held.reached.count == 0L && !held.terminal.get())
            await(LocalModelSetupPhase.IMPORTING)
            val (observed, observer) = history(model)
            cancel(); await(LocalModelSetupPhase.STOPPING)
            compose.onNodeWithTag("model-choose").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()
            check(checks, "${prefix}_stopping_held", model.state.value.phase == LocalModelSetupPhase.STOPPING && !held.terminal.get())
            check(checks, "${prefix}_busy_refused", busy(env, case))
            check(checks, "${prefix}_source_closed_once", selected.opened.get() == 1 && selected.closed.get() == 1 && selected.active.get() == 0)
            val before = io { env.assertRecords(case, accepted = after); env.snapshot(case) }
            held.release.countDown()
            await(LocalModelSetupPhase.UNCHECKED)
            assertTrue("Checkpoint must drain from explicit release, not its emergency timeout", held.terminal.get())
            main { observer.cancel() }
            check(checks, "${prefix}_not_ready_after_drain", !model.state.value.ready && LocalModelSetupPhase.READY !in observed)
            io { env.assertRecords(case, accepted = after) }
            check(checks, if (after) "after_accepted_preserved" else "before_unaccepted_preserved", before == io { env.snapshot(case) })
            recheck()
            if (after) ready() else missing()
            check(checks, "${prefix}_recheck_${if (after) "ready" else "missing"}", model.state.value.phase ==
                if (after) LocalModelSetupPhase.READY else LocalModelSetupPhase.MISSING)
            opened += selected.opened.get(); closed += selected.closed.get()
            requireNotNull(scenario).close(); scenario = null
        }
        io { env.proof(Phase.CANCELLATION, checks, opened, closed) }
    }

    @Test fun disposedScopeRetainsSourceUntilActualDrain() {
        val checks = linkedMapOf<String, Boolean>()
        val env = io { ReceiptSetupFixture.open(context).also { it.fresh(Case.DRAIN) } }
        launch(ReceiptSetupDrainActivity::class.java); missing()
        val selected = source(blocked = true)
        select(selected)
        assertTrue(selected.readEntered.await(10, TimeUnit.SECONDS))
        check(checks, "read_blocked", selected.active.get() == 1 && selected.closed.get() == 0)
        val original = model
        val (observed, observer) = history(original)
        cancel(); await(LocalModelSetupPhase.STOPPING)
        check(checks, "stopping_holds_source", selected.active.get() == 1 && selected.closed.get() == 0)
        check(checks, "contender_busy", busy(env, Case.DRAIN))
        requireNotNull(scenario).close(); scenario = null
        val disposed = original.state.value
        launch(ReceiptSetupDrainActivity::class.java)
        check(checks, "original_scope_disposed", model !== original && !disposed.ready)
        await(LocalModelSetupPhase.FAILED)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()
        check(checks, "fresh_scope_busy_failed", selected.active.get() == 1 && selected.closed.get() == 0 && busy(env, Case.DRAIN))
        selected.release.countDown()
        compose.waitUntil(10_000) { selected.closed.get() == 1 && selected.active.get() == 0 }
        check(checks, "source_closed_after_release", selected.readReleased.get() && selected.closed.get() == 1 && selected.active.get() == 0)
        var drained = false
        val deadline = SystemClock.elapsedRealtime() + 5_000
        while (!drained && SystemClock.elapsedRealtime() < deadline) {
            drained = io {
                try { assertNull(env.access(Case.DRAIN).installed()); true }
                catch (failure: LocalModelException) { assertEquals(LocalModelFailure.BUSY, failure.failure); false }
            }
            if (!drained) Thread.sleep(10)
        }
        check(checks, "actual_reservation_drained", drained)
        main { observer.cancel() }
        check(checks, "original_never_ready", original.state.value == disposed && LocalModelSetupPhase.READY !in observed)
        recheck(); missing()
        check(checks, "fresh_recheck_missing", model.state.value.phase == LocalModelSetupPhase.MISSING)
        io { env.assertRecords(Case.DRAIN, accepted = false, complete = false) }
        check(checks, "unaccepted_preserved", true)
        check(checks, "source_opened_once", selected.opened.get() == 1)
        io { env.proof(Phase.DRAIN, checks, selected.opened.get(), selected.closed.get()) }
    }
}

/** Select separately only after the controller observes the original target process absent. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptSetupRestartTest : ReceiptSetupUiHarness() {
    @Test fun reopensAcceptedCopyAfterActualProcessRestart() {
        val checks = linkedMapOf<String, Boolean>()
        val env = io { ReceiptSetupFixture.open(context) }
        val prior = io { env.previousSetupProof() }
        check(checks, "previous_proof_valid", true)
        check(checks, "process_identity_changed", prior.getInt("pid") != Process.myPid() ||
            prior.getLong("start") != Process.getStartElapsedRealtime())
        check(checks, "actual_adapter_receipt", io { env.access(Case.ACCEPT) } is ReceiptCandidateModelAccess)
        val unopened = source()
        launch(ReceiptSetupAcceptActivity::class.java); ready()
        check(checks, "ui_ready_after_reopen", model.state.value.ready)
        io { env.assertRecords(Case.ACCEPT, accepted = true); env.access(Case.ACCEPT).import(unopened::open) }
        check(checks, "accepted_records_exact", true)
        check(checks, "source_unopened", unopened.opened.get() == 0 && unopened.closed.get() == 0)
        check(checks, "sdk_not_opened", ReceiptSetupFixture.playAttempts.get() == 0)
        io { env.proof(Phase.REOPEN, checks, unopened.opened.get(), unopened.closed.get(), prior) }
    }
}
