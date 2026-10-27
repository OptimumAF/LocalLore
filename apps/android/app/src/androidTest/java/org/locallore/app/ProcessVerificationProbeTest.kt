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
        ProcessVerificationProbe.operation("story_template")
        ProcessVerificationProbe.operation("create_named")
        ProcessVerificationProbe.operation("SYNTHETIC secret unknown operation")
        ProcessVerificationProbe.saved(PlayDraftScope("synthetic_story", "root"))
        val files = listOf("created.json", "commands.json", "saved.json").map { File(directory, it) }
        val original = files.map { it.readBytes() }
        val commands = JSONObject(original[1].toString(Charsets.UTF_8))
        assertEquals(2, commands.getInt("version"))
        assertEquals("locallore_process_verify_v2", commands.getString("scope"))
        assertEquals(setOf("workspace", "branches", "resume", "create", "open", "play_snapshot", "free_text",
            "submit", "prepare", "commit", "cancel", "other", "story_template", "create_named"),
            commands.getJSONObject("operations").keys().asSequence().toSet())
        assertEquals(1, commands.getJSONObject("operations").getInt("story_template"))
        assertEquals(1, commands.getJSONObject("operations").getInt("create_named"))
        assertEquals(0, commands.getJSONObject("operations").getInt("create"))
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
        assertEquals(1, restored.getJSONObject("operations").getInt("story_template"))
        assertEquals(1, restored.getJSONObject("operations").getInt("create_named"))
        ProcessVerificationProbe.configure(context, null, 21, true)
    }
}
