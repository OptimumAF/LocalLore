/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

class ProcessVerificationProbeTest {
    @Test fun missingOrInvalidConfigurationDisablesPreviousProofRouting() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assumeTrue(BuildConfig.INPUT_PROCESS_VERIFICATION && context.packageName == "org.locallore.app.draftprocessverify")
        val run = "cb92da7130f486e5"
        val directory = File(context.noBackupFilesDir, "process-verify-v1/$run")
        ProcessVerificationProbe.configure(context, run, 19, false)
        ProcessVerificationProbe.factoryCreated()
        ProcessVerificationProbe.created(PlayDraftScope("synthetic_story", "root"))
        ProcessVerificationProbe.operation("workspace")
        ProcessVerificationProbe.operation("SYNTHETIC secret unknown operation")
        ProcessVerificationProbe.saved(PlayDraftScope("synthetic_story", "root"))
        val files = listOf("created.json", "commands.json", "saved.json").map { File(directory, it) }
        val original = files.map { it.readBytes() }
        val commands = JSONObject(original[1].toString(Charsets.UTF_8))
        assertEquals(1, commands.getJSONObject("operations").getInt("other"))
        assertEquals(1, commands.getJSONObject("operations").getInt("workspace"))
        assertFalse(original[1].toString(Charsets.UTF_8).contains("secret"))
        for (invalid in listOf(null, "INVALID", "a".repeat(10_000))) {
            ProcessVerificationProbe.configure(context, invalid, 20, true)
            ProcessVerificationProbe.created(null)
            ProcessVerificationProbe.saved(null)
            ProcessVerificationProbe.operation("commit")
            files.zip(original).forEach { (file, bytes) -> assertArrayEquals(bytes, file.readBytes()) }
        }
        // Re-enabling the same run preserves process lifetime counters; rotation cannot hide an owner.
        ProcessVerificationProbe.configure(context, run, 21, true)
        ProcessVerificationProbe.created(null)
        val restored = JSONObject(files[0].readText())
        assertEquals(1, restored.getInt("factory_creations"))
        assertTrue(restored.getBoolean("restored_state"))
        assertEquals(1, restored.getJSONObject("operations").getInt("other"))
        ProcessVerificationProbe.configure(context, null, 21, true)
    }
}
