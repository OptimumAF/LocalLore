/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import java.io.IOException

/** Only the explicit SDK candidate has this launcher. Intent extras never select a model/profile. */
class LocalModelSetupActivity : ComponentActivity() {
    private lateinit var model: LocalModelSetupViewModel
    private val picker = registerForActivityResult(object : ActivityResultContracts.OpenDocument() {
        override fun createIntent(context: Context, input: Array<String>): Intent =
            super.createIntent(context, input).putExtra(Intent.EXTRA_LOCAL_ONLY, true)
    }) { uri ->
        if (::model.isInitialized) {
            if (uri == null) model.completePicker(null)
            else {
                val resolver = applicationContext.contentResolver
                model.completePicker {
                    resolver.openInputStream(uri) ?: throw IOException("Selected document unavailable")
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val context = applicationContext
        // Resolve private storage only inside the controller's IO operations. An unavailable
        // directory/configuration is a fixed setup failure, never a raw exception on Main.
        val store by lazy { CandidateLocalModel.store(context) }
        val factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                require(modelClass == LocalModelSetupViewModel::class.java)
                return LocalModelSetupViewModel(
                    checkInstalled = { store.installed() != null },
                    install = { open -> store.import(open) },
                    canStart = CandidateLocalModel::canStart,
                ) as T
            }
        }
        model = ViewModelProvider(this, factory)[LocalModelSetupViewModel::class.java]
        setContent {
            val state by model.state.collectAsStateWithLifecycle()
            MaterialTheme(colorScheme = lightColorScheme(
                primary = Color(0xFF18584E), onPrimary = Color.White,
                surface = Color(0xFFF8F5EC), background = Color(0xFFF8F5EC),
                onSurface = Color(0xFF202D2A), onBackground = Color(0xFF202D2A),
            )) {
                Scaffold { safePadding ->
                    Column(Modifier.fillMaxSize().padding(safePadding)
                        .verticalScroll(rememberScrollState()).padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally) {
                        Column(Modifier.widthIn(max = 560.dp).fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(16.dp)) {
                            Text("LocalLore", style = MaterialTheme.typography.headlineLarge,
                                fontFamily = FontFamily.Serif, modifier = Modifier.semantics { heading() })
                            Text("Experimental local model", style = MaterialTheme.typography.titleLarge)
                            Text("Choose an existing local file. LocalLore checks its size and SHA-256, then keeps a copy in private app storage. Stories stay on this device during play.")
                            Text("The picker requests local storage; your file provider controls where its documents come from.",
                                style = MaterialTheme.typography.bodySmall)
                            Text("Expected model · ${CandidateLocalModel.identity.id}")
                            Text("File size · ${CandidateLocalModel.identity.bytes} bytes. Additional space is required for the copy and runtime cache.",
                                style = MaterialTheme.typography.bodySmall)
                            Text("SHA-256 · ${CandidateLocalModel.identity.sha256}",
                                style = MaterialTheme.typography.bodySmall, modifier = Modifier.testTag("model-expected-hash"))
                            Text("This candidate has not qualified phone performance, narrative quality or active-model cleanup.",
                                style = MaterialTheme.typography.bodySmall)
                            Text(state.notice, modifier = Modifier.testTag("model-setup-status")
                                .semantics { liveRegion = LiveRegionMode.Polite })
                            if (state.busy) {
                                CircularProgressIndicator(Modifier.testTag("model-setup-progress"))
                                OutlinedButton(onClick = model::cancel,
                                    enabled = state.phase != LocalModelSetupPhase.STOPPING,
                                    modifier = Modifier.testTag("model-import-cancel")) { Text("Cancel file operation") }
                            }
                            Button(onClick = {
                                if (model.beginPicker()) {
                                    try { picker.launch(arrayOf("*/*")) }
                                    catch (_: Exception) { model.pickerFailed() }
                                }
                            }, enabled = state.canChoose, modifier = Modifier.fillMaxWidth().testTag("model-choose")) {
                                Text("Choose local model file")
                            }
                            OutlinedButton(onClick = { model.recheck() }, enabled = !state.busy && state.phase !in
                                setOf(LocalModelSetupPhase.PICKING, LocalModelSetupPhase.OPENING, LocalModelSetupPhase.SESSION_HELD),
                                modifier = Modifier.fillMaxWidth().testTag("model-recheck")) { Text("Check local copy") }
                            Button(onClick = {
                                if (model.beginPlay()) {
                                    try {
                                        startActivity(Intent(this@LocalModelSetupActivity, LiteRtPlayActivity::class.java))
                                        finish()
                                    } catch (_: Exception) { model.playLaunchFailed() }
                                }
                            }, enabled = state.ready, modifier = Modifier.fillMaxWidth().testTag("model-start")) {
                                Text("Start local story")
                            }
                            TextButton(onClick = { finish() }) { Text("Close") }
                        }
                    }
                }
            }
        }
    }

    override fun onStart() {
        super.onStart()
        if (::model.isInitialized) model.onForeground()
    }

    override fun onStop() {
        if (::model.isInitialized) model.onBackground()
        super.onStop()
    }
}

/** No alternate provider is selected after play starts, including after startup failure. */
class LiteRtPlayActivity : MainActivity() {
    internal override fun createWorkspaceTransport(): NativeWorkspaceTransport =
        CandidateLocalModel.createTransport(applicationContext)
}
