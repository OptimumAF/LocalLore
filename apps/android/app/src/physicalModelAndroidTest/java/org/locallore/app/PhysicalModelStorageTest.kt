/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.system.Os
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performScrollTo
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 36)
class PhysicalModelPreflightTest : PhysicalModelHarness() {
    @Test fun verifiesPrivatePhoneSourceBeforeCopy() {
        val deadline = selected(PhysicalModelPreflightTest::class.java, PhysicalModelPhase.PRECHECK)
        io(deadline) {
            val checks = linkedMapOf<String, Boolean>()
            val env = PhoneEnvironment(context)
            checked(checks, "build_identity_exact", BuildConfig.PHYSICAL_MODEL_VERIFICATION && BuildConfig.MODEL_RECEIPT_VERIFICATION &&
                !BuildConfig.MODEL_VOLUME_VERIFICATION && CandidateLocalModel.identity.bytes == PhysicalModelPolicy.MODEL_BYTES &&
                CandidateLocalModel.identity.sha256 == PhysicalModelPolicy.MODEL_SHA256)
            checked(checks, "phone_profile_exact", PhysicalModelPolicy.admit(env.before) == env.before)
            checked(checks, "context_roots_exact", listOf(env.storage.source, env.storage.control, env.storage.data, env.storage.proof)
                .all { it.parentFile == context.noBackupFilesDir.canonicalFile })
            env.source(false)
            checked(checks, "same_filesystem", Os.lstat(env.storage.source.path).st_dev == env.before.anchorDevice)
            checked(checks, "source_owner_probe_exact", true)
            checked(checks, "source_whitelist_exact", true)
            checked(checks, "source_model_absent", !Files.exists(File(env.storage.source, "model.litertlm").toPath(), NOFOLLOW_LINKS))
            checked(checks, "legacy_roots_absent", listOf("local-model-v1", "local-model-removable-v1", "local-model-receipt-control-v1", "local-model-receipt-data-v1")
                .none { Files.exists(File(env.storage.internal, it).toPath(), NOFOLLOW_LINKS) })
            val access = CandidateLocalModel.store(context)
            checked(checks, "candidate_access_receipt", access is ReceiptCandidateModelAccess && access.plannedFiles().root == env.storage.data)
            checked(checks, "candidate_roots_absent", env.candidateAbsent())
            checked(checks, "candidate_installed_null_noncreating", access.installed() == null && env.candidateAbsent())
            checked(checks, "memory_eligible", PhysicalModelPolicy.admit(env.before) == env.before)
            checked(checks, "two_copy_capacity", env.storage.preflight().availableBytes >= PhysicalModelPolicy.FRESH_BYTES)
            env.write(PhysicalModelPhase.PRECHECK, deadline, PhoneCounts(), checks)
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 36)
class PhysicalModelImportTest : PhysicalModelHarness() {
    @get:Rule val compose = createEmptyComposeRule()
    private var scenario: ActivityScenario<LocalModelSetupActivity>? = null
    private var activeCounts: PhoneCounts? = null
    private var activeDeadline: PhoneDeadline? = null

    @Test fun importsFixedPhoneCandidate() {
        val deadline = selected(PhysicalModelImportTest::class.java, PhysicalModelPhase.IMPORT)
        activeDeadline = deadline
        val counts = PhoneCounts().also { activeCounts = it }
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { PhoneEnvironment(context) }
        val prior = io(deadline) { env.prior(PhysicalModelPhase.IMPORT) }
        checked(checks, "prior_precheck_exact", prior.first.phase == PhysicalModelPhase.PRECHECK)
        checked(checks, "process_identity_changed", prior.first.identity != env.identity)
        val source = io(deadline) {
            env.source(true)
            checked(checks, "source_owner_probe_exact", true)
            checked(checks, "source_whitelist_exact", true)
            checked(checks, "source_regular_uid", phoneRegular(File(env.storage.source, "model.litertlm"), PhysicalModelPolicy.MODEL_BYTES).isRegularFile)
            checked(checks, "memory_eligible", PhysicalModelPolicy.admit(env.before) == env.before)
            env.storage.admit(PhysicalModelPolicy.MODEL_BYTES)
            checked(checks, "shared_capacity", true)
            PhoneSource(env, counts, deadline).also { checked(checks, "source_fullhash_exact", it.verify()) }
        }
        checked(checks, "source_verify_closed_once", counts.verifyOpened.get() == 1L && counts.verifyClosed.get() == 1L)
        io(deadline) {
            val access = CandidateLocalModel.store(context)
            checked(checks, "candidate_access_receipt", access is ReceiptCandidateModelAccess)
            check(env.candidateAbsent() && access.installed() == null)
            val refused = try { access.admitRuntime(); false }
                catch (failure: LocalModelException) { failure.failure == LocalModelFailure.INVALID_MODEL }
            checked(checks, "preaccept_runtime_refused", refused && CandidateLocalModel.canStart())
        }
        lateinit var controller: LocalModelSetupViewModel
        scenario = ActivityScenario.launch(LocalModelSetupActivity::class.java)
        requireNotNull(scenario).onActivity { check(it.javaClass == LocalModelSetupActivity::class.java); controller = it.setupController }
        compose.waitUntil(deadline.remaining(10_000)) { controller.state.value.phase == LocalModelSetupPhase.MISSING }
        checked(checks, "setup_missing_before", controller.state.value.phase == LocalModelSetupPhase.MISSING)
        InstrumentationRegistry.getInstrumentation().runOnMainSync {
            check(controller.beginPicker()); controller.completePicker(source::openImport)
        }
        compose.waitUntil(deadline.remaining(120_000)) { controller.state.value.phase == LocalModelSetupPhase.READY }
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        checked(checks, "setup_ready_after", controller.state.value.ready)
        checked(checks, "import_offmain_closed_once", counts.offMain.get() && counts.importOpened.get() == 1L && counts.importClosed.get() == 1L)
        checked(checks, "import_exact_bytes", counts.importBytes.get() == PhysicalModelPolicy.MODEL_BYTES)
        io(deadline) {
            val access = CandidateLocalModel.store(context)
            val accepted = requireNotNull(access.installed())
            checked(checks, "accepted_full_recheck", accepted.root == env.storage.data)
            access.admitRuntime()
            checked(checks, "receipt_owner_exact", true)
            env.write(PhysicalModelPhase.IMPORT, deadline, counts, checks, prior)
        }
    }

    @After fun closeOnlyOwnedSetup() {
        scenario?.close(); scenario = null
        val counts = activeCounts ?: return
        val deadline = activeDeadline ?: return
        while (counts.importOpened.get() != counts.importClosed.get() && deadline.elapsed() < deadline.phase.budgetMs) Thread.sleep(10)
        check(counts.importOpened.get() == counts.importClosed.get()) { "Phone import source closure remains unknown" }
    }
}
