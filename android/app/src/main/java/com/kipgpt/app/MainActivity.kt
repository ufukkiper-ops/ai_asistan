package com.kipgpt.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.kipgpt.app.data.ApiClient
import com.kipgpt.app.data.SessionManager
import com.kipgpt.app.ui.LoginScreen
import com.kipgpt.app.ui.MainScreen
import com.kipgpt.app.ui.SettingsScreen
import com.kipgpt.app.ui.theme.KipGptTheme
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val app = application as KipGptApplication

        setContent {
            KipGptTheme {
                KipGptApp(app.sessionManager)
            }
        }
    }
}

@Composable
private fun KipGptApp(sessionManager: SessionManager) {
    val viewModel: MainViewModel = viewModel(
        factory = MainViewModel.Factory(sessionManager),
    )
    val authState by viewModel.authState.collectAsState()
    val baseUrl by viewModel.baseUrl.collectAsState()
    val scope = rememberCoroutineScope()

    val token = (authState as? AuthState.LoggedIn)?.token
    val apiClient = remember(token, baseUrl) {
        ApiClient(token, baseUrl)
    }

    when {
        authState is AuthState.Loading -> {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        }
        viewModel.showGuestSettings -> {
            SettingsScreen(
                apiClient = apiClient,
                sessionManager = sessionManager,
                onBack = { viewModel.closeGuestSettings() },
                onLogout = null,
            )
        }
        authState is AuthState.LoggedOut -> {
            LoginScreen(
                apiClient = apiClient,
                sessionManager = sessionManager,
                onLoggedIn = { },
                onOpenSettings = { viewModel.openGuestSettings() },
            )
        }
        authState is AuthState.LoggedIn -> {
            MainScreen(
                apiClient = apiClient,
                sessionManager = sessionManager,
                onLogout = {
                    scope.launch {
                        viewModel.logout()
                    }
                },
            )
        }
    }
}
