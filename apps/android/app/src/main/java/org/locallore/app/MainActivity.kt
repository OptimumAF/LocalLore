/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.locallore.app.ui.LocalLoreScreen

class MainActivity : ComponentActivity() {
    private lateinit var model: ShellViewModel

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                require(modelClass == ShellViewModel::class.java)
                return ShellViewModel(NativeDemoGateway()) as T
            }
        }
        model = ViewModelProvider(this, factory)[ShellViewModel::class.java]
        setContent {
            val state by model.state.collectAsStateWithLifecycle()
            LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset)
        }
    }

    override fun onStop() {
        // Conservatively stop sample work when the surface leaves the foreground, including rotation.
        // Accepted in-memory state survives configuration recreation through the ViewModel.
        if (::model.isInitialized) model.cancel()
        super.onStop()
    }
}
