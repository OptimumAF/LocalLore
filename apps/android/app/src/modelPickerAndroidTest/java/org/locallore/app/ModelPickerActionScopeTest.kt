/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Activity
import android.app.Instrumentation
import android.content.Intent
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Drives the real setup screen and intercepts the document request before any provider opens. */
@RunWith(AndroidJUnit4::class)
@Suppress("DEPRECATION")
class ModelPickerActionScopeTest {
    @get:Rule val compose = createEmptyComposeRule()

    @Test fun retiredChooseAndCheckCannotActOnReplacementStatus() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        assertEquals("org.locallore.app.modelpickerverify", context.packageName)
        val root = runBlocking(Dispatchers.IO) {
            ModelPickerFixture.root(context).toPath().also {
                assertTrue("Synthetic picker root must be absent before launch", Files.notExists(it, NOFOLLOW_LINKS))
            }
        }

        val requests = mutableListOf<Intent>()
        val monitor = object : Instrumentation.ActivityMonitor() {
            override fun onStartActivity(intent: Intent): Instrumentation.ActivityResult? {
                if (intent.action != Intent.ACTION_OPEN_DOCUMENT) return null
                requests.add(Intent(intent))
                return Instrumentation.ActivityResult(Activity.RESULT_CANCELED, null)
            }
        }

        instrumentation.addMonitor(monitor)
        try {
            ActivityScenario.launch(ModelPickerFixtureActivity::class.java).use { scenario ->
                lateinit var model: LocalModelSetupViewModel
                scenario.onActivity { model = it.setupController }
                compose.waitUntil(10_000) { model.state.value.phase == LocalModelSetupPhase.MISSING }
                val original = model.state.value
                val choose = control("model-choose").fetchSemanticsNode()
                val check = control("model-recheck").fetchSemanticsNode()
                val retiredChoose = checkNotNull(choose.config[SemanticsActions.OnClick].action)
                val retiredCheck = checkNotNull(check.config[SemanticsActions.OnClick].action)
                compose.onNodeWithTag("model-setup-status").assertTextEquals(original.notice)

                control("model-recheck").performClick()
                compose.waitUntil(10_000) {
                    val state = model.state.value
                    state !== original && state.phase == LocalModelSetupPhase.MISSING
                }
                val replacement = model.state.value
                assertNotSame(original, replacement)
                assertEquals(original.notice, replacement.notice)
                compose.onNodeWithTag("model-setup-status").assertTextEquals(replacement.notice)
                assertNotEquals(choose.id, control("model-choose").fetchSemanticsNode().id)
                assertNotEquals(check.id, control("model-recheck").fetchSemanticsNode().id)

                compose.runOnIdle {
                    retiredCheck()
                    assertSame(replacement, model.state.value)
                    assertTrue(requests.isEmpty())
                    retiredChoose()
                    assertSame(replacement, model.state.value)
                    assertTrue(requests.isEmpty())
                }

                control("model-choose").performClick()
                compose.waitUntil(10_000) { model.state.value.phase == LocalModelSetupPhase.UNCHECKED }
                compose.onNodeWithTag("model-setup-status")
                    .assertTextEquals("No file selected. Check the local copy or choose a file.")
                compose.runOnIdle {
                    assertEquals(1, requests.size)
                    val request = requests.single()
                    assertEquals("*/*", request.type)
                    assertTrue(request.hasCategory(Intent.CATEGORY_OPENABLE))
                    assertTrue(request.getBooleanExtra(Intent.EXTRA_LOCAL_ONLY, false))
                    assertTrue(request.getStringArrayExtra(Intent.EXTRA_MIME_TYPES)?.contentEquals(arrayOf("*/*")) == true)
                }
                control("model-choose")
            }
        } finally {
            instrumentation.removeMonitor(monitor)
        }

        runBlocking(Dispatchers.IO) {
            assertTrue("Synthetic canceled result must leave the picker root absent", Files.notExists(root, NOFOLLOW_LINKS))
        }
    }

    private fun control(tag: String) = compose.onNodeWithTag(tag).performScrollTo().assertIsEnabled()
}
