package com.kipgpt.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.kipgpt.app.BuildConfig
import com.kipgpt.app.data.AddMailAccountRequest
import com.kipgpt.app.data.ApiClient
import com.kipgpt.app.data.MailAccount
import com.kipgpt.app.data.MailProviderInfo
import com.kipgpt.app.data.SessionManager
import kotlinx.coroutines.launch
import retrofit2.HttpException

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun SettingsScreen(
    apiClient: ApiClient,
    sessionManager: SessionManager,
    onBack: (() -> Unit)? = null,
    onLogout: (() -> Unit)? = null,
    modifier: Modifier = Modifier,
) {
    val baseUrl = remember { mutableStateOf(SessionManager.DEFAULT_BASE_URL) }
    val userEmail = remember { mutableStateOf<String?>(null) }
    val testing = remember { mutableStateOf(false) }
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    val accounts = remember { mutableStateListOf<MailAccount>() }
    val activeAccountId = remember { mutableStateOf<String?>(null) }
    val providers = remember { mutableStateOf<Map<String, MailProviderInfo>>(emptyMap()) }
    val accountsLoading = remember { mutableStateOf(false) }
    val showAddForm = remember { mutableStateOf(false) }
    val savingAccount = remember { mutableStateOf(false) }

    val accountEmail = remember { mutableStateOf("") }
    val accountLabel = remember { mutableStateOf("") }
    val accountPassword = remember { mutableStateOf("") }
    val accountProvider = remember { mutableStateOf("gmail") }
    val imapServer = remember { mutableStateOf("") }
    val smtpServer = remember { mutableStateOf("") }
    val imapPort = remember { mutableStateOf("993") }
    val smtpPort = remember { mutableStateOf("587") }

    fun apiErrorMessage(e: Exception, fallback: String): String {
        if (e is HttpException) {
            val body = e.response()?.errorBody()?.string().orEmpty()
            val parsed = body.substringAfter("\"error\":\"", "").substringBefore("\"")
            if (parsed.isNotBlank()) return parsed
        }
        return e.message ?: fallback
    }

    suspend fun loadMailAccounts() {
        if (onLogout == null) return
        accountsLoading.value = true
        try {
            val response = apiClient.api.mailAccounts()
            accounts.clear()
            accounts.addAll(response.accounts)
            activeAccountId.value = response.active_mail_account
            providers.value = response.providers
            if (accountProvider.value !in response.providers.keys && response.providers.isNotEmpty()) {
                accountProvider.value = response.providers.keys.first()
            }
        } catch (e: Exception) {
            snackbar.showSnackbar(apiErrorMessage(e, "Mail hesapları yüklenemedi"))
        } finally {
            accountsLoading.value = false
        }
    }

    LaunchedEffect(Unit) {
        sessionManager.baseUrlFlow.collect { baseUrl.value = it }
    }

    LaunchedEffect(apiClient) {
        if (onLogout != null) {
            try {
                val me = apiClient.api.me()
                userEmail.value = me.email
            } catch (_: Exception) {
            }
            loadMailAccounts()
        }
    }

    Scaffold(
        modifier = modifier,
        topBar = {
            if (onBack != null) {
                TopAppBar(
                    title = { Text("Ayarlar") },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Geri")
                        }
                    },
                )
            }
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
        ) {
            if (onLogout == null) {
                Text("Ayarlar", style = MaterialTheme.typography.headlineSmall)
                Spacer(Modifier.height(8.dp))
            }

            if (!userEmail.value.isNullOrBlank()) {
                Text("Hesap", style = MaterialTheme.typography.titleMedium)
                Text(
                    userEmail.value!!,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
                Spacer(Modifier.height(16.dp))
                HorizontalDivider()
                Spacer(Modifier.height(16.dp))
            }

            if (onLogout != null) {
                Text("Mail hesapları", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(8.dp))
                Text(
                    "Uygulamada kullanmak istediğiniz e-posta adreslerini buradan ekleyin.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(12.dp))

                if (accountsLoading.value && accounts.isEmpty()) {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontally))
                } else if (accounts.isEmpty()) {
                    Text(
                        "Henüz mail hesabı yok.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                } else {
                    accounts.forEach { account ->
                        val isActive = account.id == activeAccountId.value
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 8.dp),
                        ) {
                            Text(
                                account.label.ifBlank { account.email },
                                style = MaterialTheme.typography.bodyLarge,
                            )
                            Text(
                                buildString {
                                    append(account.email)
                                    if (account.provider.isNotBlank()) {
                                        append(" · ")
                                        append(providers.value[account.provider]?.label ?: account.provider)
                                    }
                                    if (isActive) append(" · Aktif")
                                },
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                if (!isActive) {
                                    TextButton(
                                        onClick = {
                                            scope.launch {
                                                try {
                                                    val response = apiClient.api.activateMailAccount(account.id)
                                                    accounts.clear()
                                                    accounts.addAll(response.accounts)
                                                    activeAccountId.value = response.active_mail_account
                                                    snackbar.showSnackbar("Aktif hesap: ${account.email}")
                                                } catch (e: Exception) {
                                                    snackbar.showSnackbar(
                                                        apiErrorMessage(e, "Hesap seçilemedi"),
                                                    )
                                                }
                                            }
                                        },
                                    ) {
                                        Text("Aktif yap")
                                    }
                                }
                                if (accounts.size > 1) {
                                    TextButton(
                                        onClick = {
                                            scope.launch {
                                                try {
                                                    val response = apiClient.api.deleteMailAccount(account.id)
                                                    accounts.clear()
                                                    accounts.addAll(response.accounts)
                                                    activeAccountId.value = response.active_mail_account
                                                    snackbar.showSnackbar("Hesap silindi")
                                                } catch (e: Exception) {
                                                    snackbar.showSnackbar(
                                                        apiErrorMessage(e, "Hesap silinemedi"),
                                                    )
                                                }
                                            }
                                        },
                                    ) {
                                        Text("Sil", color = MaterialTheme.colorScheme.error)
                                    }
                                }
                            }
                        }
                        HorizontalDivider()
                    }
                }

                Spacer(Modifier.height(12.dp))
                Button(
                    onClick = { showAddForm.value = !showAddForm.value },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(if (showAddForm.value) "Formu gizle" else "Mail hesabı ekle")
                }

                if (showAddForm.value) {
                    Spacer(Modifier.height(12.dp))
                    Text("Sağlayıcı", style = MaterialTheme.typography.titleSmall)
                    Spacer(Modifier.height(8.dp))
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        val providerKeys = providers.value.keys.ifEmpty {
                            listOf("gmail", "outlook", "yahoo", "custom")
                        }
                        providerKeys.forEach { key ->
                            FilterChip(
                                selected = accountProvider.value == key,
                                onClick = { accountProvider.value = key },
                                label = {
                                    Text(providers.value[key]?.label ?: key.replaceFirstChar { it.uppercase() })
                                },
                            )
                        }
                    }
                    val hint = providers.value[accountProvider.value]?.hint.orEmpty()
                    if (hint.isNotBlank()) {
                        Spacer(Modifier.height(8.dp))
                        Text(
                            hint,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }

                    Spacer(Modifier.height(12.dp))
                    OutlinedTextField(
                        value = accountEmail.value,
                        onValueChange = { accountEmail.value = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("E-posta adresi") },
                        singleLine = true,
                    )
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = accountLabel.value,
                        onValueChange = { accountLabel.value = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Etiket (isteğe bağlı)") },
                        singleLine = true,
                    )
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = accountPassword.value,
                        onValueChange = { accountPassword.value = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Şifre / uygulama şifresi") },
                        singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                    )

                    if (accountProvider.value == "custom") {
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(
                            value = imapServer.value,
                            onValueChange = { imapServer.value = it },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("IMAP sunucu") },
                            singleLine = true,
                        )
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(
                            value = smtpServer.value,
                            onValueChange = { smtpServer.value = it },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("SMTP sunucu") },
                            singleLine = true,
                        )
                        Spacer(Modifier.height(8.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedTextField(
                                value = imapPort.value,
                                onValueChange = { imapPort.value = it },
                                modifier = Modifier.weight(1f),
                                label = { Text("IMAP port") },
                                singleLine = true,
                            )
                            OutlinedTextField(
                                value = smtpPort.value,
                                onValueChange = { smtpPort.value = it },
                                modifier = Modifier.weight(1f),
                                label = { Text("SMTP port") },
                                singleLine = true,
                            )
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    Button(
                        onClick = {
                            scope.launch {
                                savingAccount.value = true
                                try {
                                    val response = apiClient.api.addMailAccount(
                                        AddMailAccountRequest(
                                            account_email = accountEmail.value.trim(),
                                            account_label = accountLabel.value.trim(),
                                            mail_provider = accountProvider.value,
                                            mail_password = accountPassword.value,
                                            imap_server = imapServer.value.trim(),
                                            smtp_server = smtpServer.value.trim(),
                                            imap_port = imapPort.value.trim().ifBlank { "993" },
                                            smtp_port = smtpPort.value.trim().ifBlank { "587" },
                                        ),
                                    )
                                    accounts.clear()
                                    accounts.addAll(response.accounts)
                                    activeAccountId.value = response.active_mail_account
                                    accountEmail.value = ""
                                    accountLabel.value = ""
                                    accountPassword.value = ""
                                    imapServer.value = ""
                                    smtpServer.value = ""
                                    showAddForm.value = false
                                    snackbar.showSnackbar(response.message ?: "Mail hesabı eklendi")
                                } catch (e: Exception) {
                                    snackbar.showSnackbar(apiErrorMessage(e, "Hesap eklenemedi"))
                                } finally {
                                    savingAccount.value = false
                                }
                            }
                        },
                        enabled = !savingAccount.value &&
                            accountEmail.value.isNotBlank() &&
                            accountPassword.value.isNotBlank(),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        if (savingAccount.value) {
                            CircularProgressIndicator(modifier = Modifier.height(20.dp))
                        } else {
                            Text("Hesabı kaydet")
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))
                HorizontalDivider()
                Spacer(Modifier.height(16.dp))
            }

            Text("Sunucu adresi", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = baseUrl.value,
                onValueChange = { baseUrl.value = it },
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("https://kip-asistan.onrender.com/api/v1/") },
                singleLine = true,
            )
            Spacer(Modifier.height(8.dp))

            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(
                    selected = baseUrl.value == SessionManager.RENDER_BASE_URL,
                    onClick = { baseUrl.value = SessionManager.RENDER_BASE_URL },
                    label = { Text("Render (Canlı)") },
                )
                FilterChip(
                    selected = baseUrl.value == SessionManager.EMULATOR_BASE_URL,
                    onClick = { baseUrl.value = SessionManager.EMULATOR_BASE_URL },
                    label = { Text("Emülatör") },
                )
            }

            Spacer(Modifier.height(8.dp))
            Text(
                "Varsayılan: Render canlı sunucu. Emülatör için 10.0.2.2, gerçek telefon için bilgisayarınızın yerel IP adresi.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "KipGPT sürümü: ${BuildConfig.VERSION_NAME}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(16.dp))

            Button(
                onClick = {
                    scope.launch {
                        sessionManager.saveBaseUrl(baseUrl.value)
                        apiClient.updateBaseUrl(
                            if (baseUrl.value.endsWith("/")) baseUrl.value else "${baseUrl.value}/",
                        )
                        snackbar.showSnackbar("Sunucu adresi kaydedildi")
                    }
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Kaydet")
            }

            Spacer(Modifier.height(8.dp))
            OutlinedButton(
                onClick = {
                    scope.launch {
                        testing.value = true
                        try {
                            val normalized = if (baseUrl.value.endsWith("/")) {
                                baseUrl.value
                            } else {
                                "${baseUrl.value}/"
                            }
                            apiClient.updateBaseUrl(normalized)
                            if (onLogout != null) {
                                val me = apiClient.api.me()
                                userEmail.value = me.email
                                loadMailAccounts()
                                snackbar.showSnackbar("Bağlantı başarılı: ${me.email}")
                            } else {
                                snackbar.showSnackbar("Adres kaydedildi. Giriş yaparak test edin.")
                            }
                        } catch (e: Exception) {
                            snackbar.showSnackbar("Bağlantı hatası: ${e.message}")
                        } finally {
                            testing.value = false
                        }
                    }
                },
                enabled = !testing.value,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (testing.value) {
                    CircularProgressIndicator()
                } else {
                    Text("Bağlantıyı Test Et")
                }
            }

            if (onLogout != null) {
                Spacer(Modifier.height(16.dp))
                HorizontalDivider()
                Spacer(Modifier.height(16.dp))
                OutlinedButton(
                    onClick = {
                        scope.launch {
                            sessionManager.clearToken()
                            apiClient.updateToken(null)
                            onLogout()
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Çıkış Yap")
                }
            }
        }
    }
}
