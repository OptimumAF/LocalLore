/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.ParcelFileDescriptor
import android.os.SystemClock
import android.view.KeyEvent
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performScrollToNode
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.runner.lifecycle.ActivityLifecycleCallback
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import java.io.ByteArrayOutputStream
import java.util.concurrent.atomic.AtomicReference
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Actual Activity/native preview and picker cancellation; no document is selected or written. */
@RunWith(AndroidJUnit4::class)
class ArchiveActivityTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private lateinit var retained: ShellViewModel
    private var pickerRequested = false
    private val targetPackage get() = instrumentation.targetContext.packageName
    private val documentPackages = setOf("com.android.documentsui", "com.google.android.documentsui")

    @Before fun awaitExistingDurableStory(): Unit {
        compose.activityRule.scenario.onActivity { retained = ViewModelProvider(it)[ShellViewModel::class.java] }
        compose.waitUntil(10_000) {
            val state = retained.state.value
            state.persistent && state.selectedStory != null && !state.busy && !state.recoveryRequired
        }
        // Do not reset, create, resume, or submit a turn: use the Activity's existing selected story.
        archiveButton().assertIsEnabled()
    }

    @After fun cancelOnlyOwnedPickerAndCloseArchive(): Unit {
        if (pickerRequested && foregroundPackage() in documentPackages) {
            backOnlyFromDocumentsUi()
            awaitForeground(targetPackage)
        }
        if (::retained.isInitialized) {
            compose.activityRule.scenario.onActivity { retained.archiveController?.dismiss() }
            compose.waitUntil(10_000) { !retained.archive.value.visible && !retained.state.value.busy }
        }
    }

    @Test fun nativePreviewCanBeRevokedThenCloseRefreshesWithoutChangingAcceptedStory(): Unit {
        val before = retained.state.value
        archiveButton().performClick()
        compose.onNodeWithTag("archive-dialog").assertIsDisplayed()
        compose.onNodeWithTag("archive-export-prepare").performScrollTo().performClick()
        compose.waitUntil(10_000) {
            !retained.archive.value.busy && retained.archive.value.prepared != null
        }
        val prepared = requireNotNull(retained.archive.value.prepared)
        assertTrue("The Activity must capture the currently selected story", prepared.preview.storyId == before.selectedStory?.story)
        assertEquals(1, prepared.preview.version)
        assertTrue(prepared.preview.bytes > 0)
        assertEquals(before.revision, prepared.preview.branchHeads[before.selectedStory?.branch])
        assertFalse(prepared.preview.noncommittedWorkflowTransferred)
        compose.onNodeWithTag("archive-preview").assertExists()
        compose.onNodeWithTag("archive-cancel").assertIsDisplayed().performClick()
        compose.waitUntil(10_000) {
            !retained.archive.value.busy && retained.archive.value.prepared == null
        }
        compose.onNodeWithTag("archive-preview").assertDoesNotExist()
        assertTrue(retained.state.value.archiveActive)
        compose.onNodeWithTag("archive-close").performClick()
        awaitClosedAndRefreshed()
        archiveButton().assertIsEnabled()
        assertSameCanon(before, retained.state.value)
    }

    @Test fun realOpenDocumentCancellationDrainsRetainedTicketAfterActivityRecreation(): Unit {
        val before = retained.state.value
        val originalActivity = compose.activity
        archiveButton().performClick()
        pickerRequested = true
        compose.onNodeWithTag("archive-import-pick").performScrollTo().performClick()
        // A model flag alone cannot prove that the real OS picker was launched.
        awaitDocumentsUi()
        assertTrue(retained.archive.value.awaitingPicker)
        assertTrue("No document has been selected or validated", retained.archive.value.prepared == null)

        // ActivityScenario.recreate first waits for RESUMED, which an external picker
        // deliberately prevents. Recreate the actual stopped Activity and observe its
        // replacement instead of forcing it foreground or dismissing the picker early.
        val replacement = AtomicReference<MainActivity>()
        val monitor = ActivityLifecycleMonitorRegistry.getInstance()
        val callback = ActivityLifecycleCallback { activity, stage ->
            if (activity is MainActivity && activity !== originalActivity && stage == Stage.CREATED)
                replacement.set(activity)
        }
        try {
            instrumentation.runOnMainSync { monitor.addLifecycleCallback(callback); originalActivity.recreate() }
            val deadline = SystemClock.elapsedRealtime() + 10_000
            while (replacement.get() == null && SystemClock.elapsedRealtime() < deadline) Thread.sleep(10)
            assertNotNull("The stopped Activity must be recreated while the picker is open", replacement.get())
            instrumentation.runOnMainSync {
                assertSame("The pending picker belongs to the retained ViewModel", retained,
                    ViewModelProvider(requireNotNull(replacement.get()))[ShellViewModel::class.java])
            }
        } finally {
            instrumentation.runOnMainSync { monitor.removeLifecycleCallback(callback) }
        }
        awaitDocumentsUi()
        assertTrue(retained.archive.value.awaitingPicker)
        // Global Back is sent only after verifying DocumentsUI is foreground, never to an unknown app.
        backOnlyFromDocumentsUi()
        awaitForeground(targetPackage)
        pickerRequested = false
        compose.waitUntil(10_000) {
            val state = retained.archive.value
            state.visible && !state.awaitingPicker && !state.busy &&
                state.notice == "Import cancelled. No archive was imported."
        }
        compose.onNodeWithTag("archive-dialog").assertIsDisplayed()
        compose.onNodeWithTag("archive-import-pick").performScrollTo().assertIsEnabled()
        compose.onNodeWithTag("archive-export-prepare").performScrollTo().assertIsEnabled()
        compose.onNodeWithTag("archive-preview").assertDoesNotExist()
        compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
        assertTrue("Cancellation must not create an import preview", retained.archive.value.prepared == null)
        assertTrue("Cancellation must not import a story", retained.archive.value.imported == null)
        assertSameCanon(before, retained.state.value)
        compose.onNodeWithTag("archive-close").performClick()
        awaitClosedAndRefreshed()
        archiveButton().assertIsEnabled()
        assertSameCanon(before, retained.state.value)
    }

    private fun archiveButton() = compose.onNodeWithTag("story-list")
        .performScrollToNode(hasTestTag("story-archive")).let { compose.onNodeWithTag("story-archive") }

    private fun awaitClosedAndRefreshed(): Unit {
        compose.waitUntil(10_000) {
            !retained.archive.value.visible && !retained.state.value.archiveActive &&
                !retained.state.value.busy && retained.state.value.notice == "Saved-story library refreshed."
        }
        compose.onNodeWithTag("archive-dialog").assertDoesNotExist()
    }

    private fun assertSameCanon(before: ShellState, after: ShellState): Unit {
        // Boolean comparisons deliberately avoid printing saved titles, message prose, or file paths on failure.
        assertTrue("The selected story and accepted head must stay unchanged", before.selectedStory == after.selectedStory)
        assertEquals(before.revision, after.revision)
        assertTrue("Inventory must stay unchanged", before.potionOwner == after.potionOwner)
        assertTrue("Accepted messages must stay unchanged", before.messages == after.messages)
        assertTrue("Saved-story library must stay unchanged", before.stories == after.stories)
        assertEquals(before.uncommittedDrafts, after.uncommittedDrafts)
        assertFalse(after.recoveryRequired)
    }

    private fun backOnlyFromDocumentsUi(): Unit {
        assertTrue("DocumentsUI must be foreground before sending Back", foregroundPackage() in documentPackages)
        instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
    }

    private fun awaitDocumentsUi(): Unit = awaitForegroundWhere { it in documentPackages }
    private fun awaitForeground(expected: String): Unit = awaitForegroundWhere { it == expected }
    private fun awaitForegroundWhere(matches: (String?) -> Boolean): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) {
            if (matches(foregroundPackage())) return
            Thread.yield()
        }
        fail("Expected Activity did not become foreground within the bounded wait")
    }

    private fun foregroundPackage(): String? {
        // Constant read-only shell command; output is bounded and never logged or returned in failures.
        val output = ByteArrayOutputStream()
        ParcelFileDescriptor.AutoCloseInputStream(
            instrumentation.uiAutomation.executeShellCommand("dumpsys activity activities"),
        ).use { input ->
            val buffer = ByteArray(8192)
            while (output.size() < 262_144) {
                val count = input.read(buffer, 0, minOf(buffer.size, 262_144 - output.size()))
                if (count < 0) break
                if (count > 0) output.write(buffer, 0, count)
            }
        }
        val lines = output.toString(Charsets.UTF_8.name()).lineSequence().toList()
        val resumed = lines.firstOrNull { it.trimStart().startsWith("topResumedActivity=") }
            ?: lines.firstOrNull { it.contains("mResumedActivity:") || it.contains("mResumedActivity=") }
            ?: return null
        return Regex("\\b([A-Za-z0-9_.]+)/[A-Za-z0-9_.$]+").find(resumed)?.groupValues?.get(1)
    }
}
