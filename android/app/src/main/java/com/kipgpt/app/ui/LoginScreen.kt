package com.kipgpt.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.kipgpt.app.data.ApiClient
import com.kipgpt.app.data.LoginRequest
import com.kipgpt.app.data.RegisterRequest
import com.kipgpt.app.data.SessionManager
import kotlinx.coroutines.launch
import retrofit2.HttpException

@Composable
fun LoginScreen(
    apiClient: ApiClient,
    sessionManager: SessionManager,
    onLoggedIn: () -> Unit,
    onOpenSettings: () -> Unit,
) {
    val context = LocalContext.current
    val email = remember { mutableStateOf("") }
    val password = remember { mutableStateOf("") }
    val showPassword = remember { mutableStateOf(false) }
    val loading = remember { mutableStateOf(false) }
    val isRegister = remember { mutableStateOf(false) }
    val linkGmail = remember { mutableStateOf(false) }
    val googleConfigured = remember { mutableStateOf(false) }
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        sessionManager.baseUrlFlow.collect { url ->
            apiClient.updateBaseUrl(url)
        }
    }

    LaunchedEffect(Unit) {
        try {
            googleConfigured.value = apiClient.api.googleAuthStatus().configured
        } catch (_: Exception) {
            googleConfigured.value = false
        }
    }

    Scaffold(snackbarHost = { SnackbarHost(snackbar) }) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text("KipGPT", style = MaterialTheme.typography.headlineLarge)
            Spacer(Modifier.height(8.dp))
            Text(
                if (isRegister.value) "Yeni hesap oluşturun" else "Hesabınıza giriş yapın",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(24.dp))

            if (googleConfigured.value) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Checkbox(
                        checked = linkGmail.value,
                        onCheckedChange = { linkGmail.value = it },
                    )
                    Text(
                        if (isRegister.value) {
                            "Gmail’i de bağla (isteğe bağlı)"
                        } else {
                            "Girişte Gmail’i bağla / yenile"
                        },
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(
                    onClick = {
                        scope.launch {
                            loading.value = true
                            try {
                                val action = if (isRegister.value) "register" else "login"
                                val res = apiClient.api.googleAuthStart(
                                    action = action,
                                    withMail = if (linkGmail.value) 1 else 0,
                                )
                                val url = res.authorization_url
                                if (url.isBlank()) {
                                    snackbar.showSnackbar(res.error ?: "Google bağlantısı açılamadı")
                                } else {
                                    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                                }
                            } catch (e: HttpException) {
                                val msg = e.response()?.errorBody()?.string()?.let {
                                    it.substringAfter("\"error\":\"").substringBefore("\"")
                                } ?: "Google girişi başarısız"
                                snackbar.showSnackbar(msg)
                            } catch (e: Exception) {
                                snackbar.showSnackbar("Bağlantı hatası: ${e.message}")
                            } finally {
                                loading.value = false
                            }
                        }
                    },
                    enabled = !loading.value,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(
                        if (isRegister.value) {
                            if (linkGmail.value) "Google ile kayıt + Gmail" else "Google ile kayıt ol"
                        } else {
                            if (linkGmail.value) "Google ile giriş + Gmail" else "Google ile Giriş Yap"
                        },
                    )
                }
                Spacer(Modifier.height(16.dp))
                Text(
                    "veya e-posta ile",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(12.dp))
            }

            OutlinedTextField(
                value = email.value,
                onValueChange = { email.value = it },
                label = { Text("E-posta") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            )
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = password.value,
                onValueChange = { password.value = it },
                label = { Text("Şifre") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                visualTransformation = if (showPassword.value) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                trailingIcon = {
                    IconButton(onClick = { showPassword.value = !showPassword.value }) {
                        Icon(
                            if (showPassword.value) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                            contentDescription = "Şifreyi göster",
                        )
                    }
                },
            )

            if (isRegister.value && googleConfigured.value) {
                Spacer(Modifier.height(8.dp))
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Checkbox(
                        checked = linkGmail.value,
                        onCheckedChange = { linkGmail.value = it },
                    )
                    Text(
                        "Kayıt sonrası Gmail’i bağla",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }

            Spacer(Modifier.height(20.dp))

            Button(
                onClick = {
                    scope.launch {
                        loading.value = true
                        try {
                            val response = if (isRegister.value) {
                                apiClient.api.register(
                                    RegisterRequest(
                                        email = email.value.trim(),
                                        password = password.value,
                                        link_gmail = linkGmail.value,
                                    ),
                                )
                            } else {
                                apiClient.api.login(
                                    LoginRequest(email.value.trim(), password.value),
                                )
                            }
                            sessionManager.saveToken(response.token, response.user.email)
                            apiClient.updateToken(response.token)
                            if (isRegister.value && linkGmail.value && response.gmail_oauth_available) {
                                try {
                                    val oauth = apiClient.api.mailOAuthStart("google")
                                    if (oauth.authorization_url.isNotBlank()) {
                                        context.startActivity(
                                            Intent(Intent.ACTION_VIEW, Uri.parse(oauth.authorization_url)),
                                        )
                                        snackbar.showSnackbar("Gmail bağlamak için Google’ı onaylayın")
                                    }
                                } catch (_: Exception) {
                                    // Hesap oluştu; Gmail sonra eklenebilir
                                }
                            }
                            onLoggedIn()
                        } catch (e: HttpException) {
                            val msg = e.response()?.errorBody()?.string()?.let {
                                it.substringAfter("\"error\":\"").substringBefore("\"")
                            } ?: "Giriş başarısız"
                            snackbar.showSnackbar(msg)
                        } catch (e: Exception) {
                            snackbar.showSnackbar("Bağlantı hatası: ${e.message}")
                        } finally {
                            loading.value = false
                        }
                    }
                },
                enabled = !loading.value && email.value.isNotBlank() && password.value.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (loading.value) {
                    CircularProgressIndicator(modifier = Modifier.height(20.dp))
                } else {
                    Text(if (isRegister.value) "Kayıt Ol" else "Giriş Yap")
                }
            }

            TextButton(onClick = { isRegister.value = !isRegister.value }) {
                Text(if (isRegister.value) "Zaten hesabım var" else "Yeni hesap oluştur")
            }

            TextButton(onClick = onOpenSettings) {
                Text("Sunucu ayarları")
            }
        }
    }
}
