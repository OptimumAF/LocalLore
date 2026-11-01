/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

/** Probe routing only. A device/controller process-death result is a separate gate. */
class PresentationProcessVerificationProbeTest {
    @Test fun explicitProfileCountsPresentationAttemptsWithoutReclassifyingLegacyOrUnknownOperations() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assumeTrue(BuildConfig.PRESENTATION_PROCESS_VERIFICATION && context.packageName == "org.locallore.app.presentationprocessverify")
        val run = "4f8a1360a93cb7de"
        val directory = File(context.noBackupFilesDir, "process-verify-v3/$run")
        PresentationProcessVerificationProbe.configure(context, run, 19, false)
        PresentationProcessVerificationProbe.factoryCreated()
        PresentationProcessVerificationProbe.created(PlayDraftScope("synthetic_story", "main"))
        PresentationProcessVerificationProbe.operation("play_presentation_v2") // Dispatch attempt, not a successful native reply.
        PresentationProcessVerificationProbe.operation("PRIVATE_UNKNOWN_OPERATION")
        PresentationProcessVerificationProbe.saved(PlayDraftScope("synthetic_story", "main"))
        val files = listOf("created.json", "commands.json", "saved.json").map { File(directory, it) }
        val original = files.map { it.readBytes() }
        val commands = JSONObject(original[1].toString(Charsets.UTF_8))
        assertEquals(3, commands.getInt("version")); assertEquals("locallore_presentation_process_verify_v3", commands.getString("scope"))
        assertEquals(presentationProcessOperations.toSet(), commands.getJSONObject("operations").keys().asSequence().toSet())
        assertEquals(1, commands.getJSONObject("operations").getInt("play_presentation_v2"))
        assertEquals(0, commands.getJSONObject("operations").getInt("play_snapshot"))
        assertEquals(1, commands.getJSONObject("operations").getInt("other")); assertFalse(original[1].toString(Charsets.UTF_8).contains("PRIVATE_UNKNOWN"))
        for (invalid in listOf(null, "INVALID", "a".repeat(10_000))) {
            PresentationProcessVerificationProbe.configure(context, invalid, 20, true)
            PresentationProcessVerificationProbe.created(null); PresentationProcessVerificationProbe.saved(null)
            PresentationProcessVerificationProbe.operation("commit")
            files.zip(original).forEach { (file, bytes) -> assertArrayEquals(bytes, file.readBytes()) }
        }
        PresentationProcessVerificationProbe.configure(context, run, 21, true)
        PresentationProcessVerificationProbe.created(null)
        val restored = JSONObject(files[0].readText())
        assertTrue(restored.getBoolean("restored_state")); assertEquals(1, restored.getInt("factory_creations"))
        assertEquals(1, restored.getJSONObject("operations").getInt("play_presentation_v2"))
        assertEquals(1, restored.getJSONObject("operations").getInt("other"))
        PresentationProcessVerificationProbe.configure(context, null, 21, true)
    }
}
