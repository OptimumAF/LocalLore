/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTagsAsResourceId
import androidx.compose.ui.unit.dp
import org.locallore.app.BranchForkInput
import org.locallore.app.BranchForkOutcome
import org.locallore.app.BranchForkUiState

/** A transient displayed review, never a native request or persisted recovery identity. */
private class ForkDialogDelivery {
    var active = true
    private var state: BranchForkUiState? = null
    private var problem: String? = null
    private var recoveryPending = false
    private var token = Any()
    fun render(value: BranchForkUiState, storageProblem: String?, pending: Boolean): Any {
        if (state !== value || problem != storageProblem || recoveryPending != pending) {
            state = value; problem = storageProblem; recoveryPending = pending; token = Any()
        }
        return token
    }
    fun accepts(rendered: Any) = active && token === rendered
}

/** Presentation only: requested numeric boundaries are validated by the shared Rust port. */
@Composable
internal fun BranchForkPanel(
    visible: Boolean,
    state: BranchForkUiState,
    storageProblem: String?,
    recoveryPending: Boolean,
    onBoundary: (BranchForkInput?, Long) -> Unit,
    onConfirm: (BranchForkInput, Boolean) -> Unit,
    onRetry: (Boolean) -> Unit,
    onLookup: () -> Unit,
    onForget: (Boolean) -> Unit,
    onCancel: () -> Unit,
    onClose: () -> Unit,
    onResume: (BranchForkOutcome) -> Unit,
    exposeTestTags: Boolean = false,
) {
    if (!visible) return
    val lifetime = remember { ForkDialogDelivery() }
    val delivery = lifetime.render(state, storageProblem, recoveryPending)
    DisposableEffect(lifetime) { onDispose { lifetime.active = false } }
    fun act(action: () -> Unit) { if (lifetime.accepts(delivery)) action() }
    val input = state.input
    var boundary by remember(delivery) { mutableStateOf((input?.atRevision ?: state.context?.head ?: 0).toString()) }
    var consent by remember(delivery) { mutableStateOf(false) }
    var forgetConsent by remember(delivery) { mutableStateOf(false) }
    val editable = !state.busy && !recoveryPending && !state.lookupOnly && !state.uncertain && state.outcome == null && storageProblem == null
    val requested = boundary.toLongOrNull()?.takeIf { it >= 0 && it <= (input?.expectedParentRevision ?: state.context?.head ?: -1) }
    AlertDialog(
        modifier = Modifier.testTag("fork-dialog").semantics { testTagsAsResourceId = exposeTestTags },
        onDismissRequest = { act { if (state.busy) onCancel() else onClose() } },
        title = { Text("New timeline / recovery", modifier = Modifier.semantics { heading() }) },
        text = {
            Column(Modifier.fillMaxWidth().heightIn(max = 520.dp).verticalScroll(rememberScrollState())
                .testTag("fork-scroll"),
                verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("A fork preserves the original timeline. Later choices are never automatically replayed.")
                Text("Author corrections are unavailable. This does not grant abilities, knowledge or edit existing facts.",
                    style = MaterialTheme.typography.bodySmall)
                storageProblem?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("fork-storage-error")) }
                input?.let {
                    Text("Requested parent: ${it.parent.story} / ${it.parent.branch}", modifier = Modifier.testTag("fork-parent"))
                    Text("Captured parent head: ${it.expectedParentRevision}")
                    Text("Fixed child ID: ${it.childBranch}", modifier = Modifier.testTag("fork-child"))
                    Text("Requested accepted-turn boundary: ${it.atRevision}. Rust validates that it is complete.")
                }
                state.context?.let { Text("Current selection: ${it.parent.story} / ${it.parent.branch} · head ${it.head}",
                    style = MaterialTheme.typography.bodySmall) }
                if (state.lookupOnly) Text("Recovered request: lookup only. Nothing is created automatically.", modifier = Modifier.testTag("fork-lookup-only"))
                if (editable && state.context != null) {
                    key(delivery) {
                        OutlinedTextField(boundary, { value -> act { if (value.length <= 16 && value.all(Char::isDigit)) boundary = value } },
                            label = { Text("Requested completed boundary") }, singleLine = true,
                            modifier = Modifier.fillMaxWidth().testTag("fork-boundary"))
                        OutlinedButton(onClick = { act { requested?.let { onBoundary(input, it) } } }, enabled = requested != null,
                            modifier = Modifier.fillMaxWidth().testTag("fork-review-boundary")) {
                            Text(if (input == null) "Prepare new request" else "Review this boundary")
                        }
                    }
                }
                if (input != null && !state.lookupOnly && state.outcome == null && storageProblem == null) {
                    Row {
                        key(delivery) {
                            Checkbox(consent, { value -> act { consent = value } }, enabled = !state.busy, modifier = Modifier.testTag("fork-consent"))
                        }
                        Text("Create exactly this new timeline, preserving the original.")
                    }
                    key(delivery) {
                        if (!state.uncertain) Button(onClick = { act { onConfirm(input, consent) } }, enabled = consent && !state.busy,
                            modifier = Modifier.fillMaxWidth().testTag("fork-confirm")) { Text("Create timeline") }
                        else OutlinedButton(onClick = { act { onRetry(consent) } }, enabled = consent && !state.busy,
                            modifier = Modifier.fillMaxWidth().testTag("fork-retry")) { Text("Retry original request") }
                    }
                }
                if (recoveryPending) key(delivery) {
                    OutlinedButton(onClick = { act(onLookup) }, enabled = !state.busy,
                        modifier = Modifier.fillMaxWidth().testTag("fork-lookup")) { Text("Look up original identity") }
                }
                state.outcome?.let { outcome ->
                    Text((if (outcome.created) "Fork confirmed" else "Existing fork found") +
                        ": ${outcome.scope.story} / ${outcome.scope.branch} · fork ${outcome.forkRevision} · current head ${outcome.headRevision}",
                        modifier = Modifier.testTag("fork-outcome"))
                    key(delivery) {
                        Button(onClick = { act { onResume(outcome) } }, enabled = !state.busy,
                            modifier = Modifier.fillMaxWidth().testTag("fork-resume")) { Text("Resume this timeline") }
                    }
                }
                if (state.busy) {
                    Text("Local timeline request is pending. A committed result wins late cancellation.", modifier = Modifier.testTag("fork-pending"))
                    key(delivery) {
                        OutlinedButton(onClick = { act(onCancel) }, modifier = Modifier.fillMaxWidth().testTag("fork-cancel")) { Text("Request cancellation") }
                    }
                }
                state.notice?.let { Text(it, modifier = Modifier.testTag("fork-notice")) }
                if (recoveryPending || storageProblem != null) {
                    Row {
                        key(delivery) {
                            Checkbox(forgetConsent, { value -> act { forgetConsent = value } }, enabled = !state.busy,
                                modifier = Modifier.testTag("fork-forget-consent"))
                        }
                        Text("Forget only the recovery hint. A timeline may already exist.")
                    }
                    key(delivery) {
                        TextButton(onClick = { act { onForget(forgetConsent) } }, enabled = forgetConsent && !state.busy,
                            modifier = Modifier.testTag("fork-forget")) { Text("Forget recovery hint") }
                    }
                }
            }
        },
        confirmButton = {
            key(delivery) {
                TextButton(onClick = { act(onClose) }, enabled = !state.busy, modifier = Modifier.testTag("fork-close")) { Text("Close") }
            }
        },
    )
}
