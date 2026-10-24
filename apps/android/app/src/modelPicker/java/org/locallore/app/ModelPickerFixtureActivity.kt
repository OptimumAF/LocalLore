/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Looper
import java.io.File
import java.io.IOException

/** Compiled only in the explicit synthetic picker profile. No Intent selects trusted configuration. */
class ModelPickerFixtureActivity : LocalModelSetupActivity() {
    internal override fun createSetupDependencies(): LocalModelSetupDependencies {
        val context = applicationContext
        val store by lazy { LocalModelStore(ModelPickerFixture.root(context), ModelPickerFixture.identity) }
        return LocalModelSetupDependencies(
            identity = ModelPickerFixture.identity,
            checkInstalled = { store.installed() != null },
            install = { open -> store.import(open) },
            canStart = { true },
            openPlay = { throw IOException("Synthetic fixture cannot open inference") },
        )
    }
}

internal object ModelPickerFixture {
    private const val PAYLOAD = "LocalLore original model picker fixture v1. No model or story.\n"
    val identity = LocalModelIdentity("synthetic-picker-v1", 63,
        "648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0", 1024)
    fun bytes(): ByteArray = PAYLOAD.toByteArray(Charsets.US_ASCII)
    fun root(context: Context): File {
        check(Thread.currentThread() !== Looper.getMainLooper().thread)
        check(context.packageName == "org.locallore.app.modelpickerverify")
        return File(context.applicationContext.noBackupFilesDir.canonicalFile, "model-picker-fixture-v1")
    }
}
