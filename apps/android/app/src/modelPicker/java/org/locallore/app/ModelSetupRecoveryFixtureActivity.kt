/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Looper
import java.io.File
import java.io.IOException
import java.util.concurrent.atomic.AtomicInteger
import org.json.JSONObject

/** Actual setup UI with fixed synthetic launch failures. No runtime or play Activity is created. */
class ModelSetupRecoveryFixtureActivity : LocalModelSetupActivity() {
    internal override fun createSetupDependencies(): LocalModelSetupDependencies {
        val context = applicationContext
        val store by lazy { ModelSetupRecoveryFixture.store(context) }
        return LocalModelSetupDependencies(ModelSetupRecoveryFixture.identity,
            checkInstalled = {
                ModelSetupRecoveryFixture.requireIo()
                ModelSetupRecoveryFixture.fullChecks.incrementAndGet()
                store.installed() != null
            },
            install = { open ->
                ModelSetupRecoveryFixture.requireIo()
                ModelSetupRecoveryFixture.fileImports.incrementAndGet()
                store.import(open)
            },
            canStart = { ModelSetupRecoveryFixture.available },
            openPlay = ModelSetupRecoveryFixture::attemptStart)
    }
}

/** One production admission object for the process; intentionally no reset or release operation. */
internal object ModelSetupRecoveryFixture {
    val identity = LocalModelIdentity("synthetic-setup-recovery-v1", 63,
        "648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0", 1024)
    private val admission = CandidateOwnerAdmission()
    val available: Boolean get() = admission.available
    val seedImports = AtomicInteger()
    val fileImports = AtomicInteger()
    val fullChecks = AtomicInteger()
    val startAttempts = AtomicInteger()
    val constructions = AtomicInteger()
    val ioViolations = AtomicInteger()
    val cacheSentinel: ByteArray get() = "LocalLore setup recovery cache v1\n".toByteArray(Charsets.US_ASCII)

    fun attemptStart() {
        check(Looper.myLooper() == Looper.getMainLooper())
        if (startAttempts.incrementAndGet() == 1) {
            throw IllegalStateException("PRIVATE_SETUP_LAUNCH_FAILURE", IOException("PRIVATE_SETUP_LAUNCH_CAUSE"))
        }
        admission.attach<Nothing> {
            constructions.incrementAndGet()
            throw IllegalStateException("PRIVATE_SETUP_CONSTRUCTION_FAILURE", IOException("PRIVATE_SETUP_CONSTRUCTION_CAUSE"))
        }
    }
    fun requireIo() {
        if (Looper.myLooper() == Looper.getMainLooper()) {
            ioViolations.incrementAndGet()
            throw IllegalStateException("Fixture file work requires IO")
        }
    }
    fun root(context: Context): File {
        requireIo()
        check(context.packageName == "org.locallore.app.modelpickerverify")
        return File(context.applicationContext.noBackupFilesDir.canonicalFile, "model-setup-recovery-v1")
    }
    fun store(context: Context) = LocalModelStore(root(context), identity)
    fun counts() = JSONObject().put("seed_imports", seedImports.get()).put("file_imports", fileImports.get())
        .put("full_checks", fullChecks.get()).put("start_attempts", startAttempts.get())
        .put("constructions", constructions.get()).put("io_violations", ioViolations.get())
}
