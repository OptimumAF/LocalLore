/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Looper
import java.io.File
import java.io.IOException

/** Fixed synthetic namespace only; no Intent selects a root, identity or runtime. */
class ModelPickerInterruptionFixtureActivity : LocalModelSetupActivity() {
    internal override fun createSetupDependencies(): LocalModelSetupDependencies {
        val context = applicationContext
        val store by lazy { LocalModelStore(ModelPickerInterruptionFixture.root(context), ModelPickerFixture.identity) }
        return LocalModelSetupDependencies(
            identity = ModelPickerFixture.identity,
            checkInstalled = { store.installed() != null },
            install = { open -> store.import(open) },
            canStart = { true },
            openPlay = { throw IOException("Synthetic fixture cannot open inference") },
        )
    }
}

internal object ModelPickerInterruptionFixture {
    fun root(context: Context): File {
        check(Thread.currentThread() !== Looper.getMainLooper().thread)
        check(context.packageName == "org.locallore.app.modelpickerverify")
        return File(context.applicationContext.noBackupFilesDir.canonicalFile, "model-picker-interruption-v1")
    }
}
