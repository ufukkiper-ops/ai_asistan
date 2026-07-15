package com.kipgpt.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.AttachFile
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material.icons.outlined.StarOutline
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
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.kipgpt.app.data.ApiClient
import com.kipgpt.app.data.AttachmentSaver
import com.kipgpt.app.data.MailAttachment
import com.kipgpt.app.data.MailFolder
import com.kipgpt.app.data.MailItem
import com.kipgpt.app.data.TranslateRequest
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MailScreen(
    apiClient: ApiClient,
    modifier: Modifier = Modifier,
) {
    val folders = remember { mutableStateListOf<MailFolder>() }
    val mails = remember { mutableStateListOf<MailItem>() }
    val selectedFolder = remember { mutableStateOf("inbox") }
    val selectedMail = remember { mutableStateOf<MailItem?>(null) }
    val search = remember { mutableStateOf("") }
    val account = remember { mutableStateOf("") }
    val loading = remember { mutableStateOf(false) }
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    fun loadMails() {
        scope.launch {
            loading.value = true
            try {
                val response = apiClient.api.mails(
                    folder = selectedFolder.value,
                    search = search.value.trim().ifBlank { null },
                )
                mails.clear()
                mails.addAll(response.mails)
                account.value = response.account
            } catch (e: Exception) {
                snackbar.showSnackbar(e.message ?: "Mailler yüklenemedi")
            } finally {
                loading.value = false
            }
        }
    }

    LaunchedEffect(Unit) {
        try {
            folders.clear()
            folders.addAll(apiClient.api.folders().folders)
        } catch (_: Exception) {
        }
    }

    LaunchedEffect(selectedFolder.value) {
        if (selectedMail.value == null) {
            loadMails()
        }
    }

    if (selectedMail.value != null) {
        MailDetailScreen(
            mail = selectedMail.value!!,
            folder = selectedFolder.value,
            apiClient = apiClient,
            onBack = { selectedMail.value = null },
            modifier = modifier,
        )
        return
    }

    Scaffold(
        modifier = modifier,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("Mailler")
                        if (account.value.isNotBlank()) {
                            Text(
                                account.value,
                                style = MaterialTheme.typography.bodySmall,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { loadMails() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Yenile")
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            LazyRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(folders, key = { it.id }) { folder ->
                    FilterChip(
                        selected = selectedFolder.value == folder.id,
                        onClick = { selectedFolder.value = folder.id },
                        label = { Text(folder.label) },
                    )
                }
            }

            OutlinedTextField(
                value = search.value,
                onValueChange = { search.value = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp),
                placeholder = { Text("Mail ara...") },
                singleLine = true,
                trailingIcon = {
                    IconButton(onClick = { loadMails() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Ara")
                    }
                },
            )

            Spacer(Modifier.height(8.dp))

            PullToRefreshBox(
                isRefreshing = loading.value,
                onRefresh = { loadMails() },
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
            ) {
                when {
                    loading.value && mails.isEmpty() -> {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            CircularProgressIndicator()
                        }
                    }
                    mails.isEmpty() -> {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            Text(
                                "Bu klasörde mail yok",
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                    else -> {
                        LazyColumn(modifier = Modifier.fillMaxSize()) {
                            items(mails, key = { it.id }) { mail ->
                                MailRow(mail) { selectedMail.value = mail }
                                HorizontalDivider()
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun MailRow(mail: MailItem, onClick: () -> Unit) {
    val senderName = formatSenderName(mail)
    val senderEmail = formatSenderEmail(mail)
    val senderInitial = senderName.firstOrNull()?.uppercaseChar()?.toString() ?: "?"

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.Top,
    ) {
        Box(
            modifier = Modifier
                .padding(top = 2.dp, end = 12.dp)
                .size(42.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.primary),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                senderInitial,
                color = Color.White,
                fontWeight = FontWeight.SemiBold,
                style = MaterialTheme.typography.titleMedium,
            )
        }

        Column(Modifier.weight(1f)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f)) {
                    Text(
                        senderName,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        style = MaterialTheme.typography.titleSmall,
                    )
                    if (senderEmail.isNotBlank() && senderEmail != senderName) {
                        Text(
                            senderEmail,
                            style = MaterialTheme.typography.bodySmall,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                if (mail.starred) {
                    Icon(
                        Icons.Default.Star,
                        contentDescription = "Yıldızlı",
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(horizontal = 6.dp),
                    )
                }
                Text(mail.date, style = MaterialTheme.typography.bodySmall)
            }

            Spacer(Modifier.height(4.dp))

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    mail.subject.ifBlank { "(Konu yok)" },
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f, fill = false),
                )
                if (mail.thread_count > 1) {
                    Text(
                        "${mail.thread_count} mesaj",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(start = 6.dp),
                    )
                }
            }

            Text(
                mail.content.replace("\n", " ").take(120),
                style = MaterialTheme.typography.bodySmall,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            if (mail.attachments.isNotEmpty()) {
                Row(
                    modifier = Modifier.padding(top = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        Icons.Default.AttachFile,
                        contentDescription = null,
                        modifier = Modifier.padding(end = 4.dp),
                        tint = MaterialTheme.colorScheme.primary,
                    )
                    Text(
                        "${mail.attachments.size} ek",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MailDetailScreen(
    mail: MailItem,
    folder: String,
    apiClient: ApiClient,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val content = remember { mutableStateOf(mail.content) }
    val translatedLang = remember { mutableStateOf<String?>(null) }
    val loading = remember { mutableStateOf(false) }
    val downloadingIndex = remember { mutableStateOf<Int?>(null) }
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    fun downloadAttachment(att: MailAttachment) {
        scope.launch {
            downloadingIndex.value = att.index
            try {
                val body = apiClient.api.downloadAttachment(
                    mailId = mail.id,
                    index = att.index,
                    folder = folder,
                )
                body.use { response ->
                    val bytes = response.bytes()
                    val savedName = AttachmentSaver.saveToDownloads(
                        context = context,
                        filename = att.filename,
                        bytes = bytes,
                        mime = att.mime,
                    )
                    snackbar.showSnackbar("İndirildi: $savedName")
                }
            } catch (e: Exception) {
                snackbar.showSnackbar(e.message ?: "Ek indirilemedi")
            } finally {
                downloadingIndex.value = null
            }
        }
    }

    fun translate(lang: String) {
        if (translatedLang.value == lang) {
            content.value = mail.content
            translatedLang.value = null
            return
        }
        scope.launch {
            loading.value = true
            try {
                val response = apiClient.api.translate(
                    TranslateRequest(mail.content, lang),
                )
                content.value = response.translated
                translatedLang.value = lang
            } catch (e: Exception) {
                snackbar.showSnackbar(e.message ?: "Çeviri hatası")
            } finally {
                loading.value = false
            }
        }
    }

    Scaffold(
        modifier = modifier,
        topBar = {
            TopAppBar(
                title = { Text(mail.subject.ifBlank { "(Konu yok)" }, maxLines = 1) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Geri")
                    }
                },
                actions = {
                    IconButton(onClick = { translate("tr") }) {
                        Icon(Icons.Default.Translate, contentDescription = "Çevir")
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
        ) {
            val senderName = formatSenderName(mail)
            val senderEmail = formatSenderEmail(mail)
            val senderInitial = senderName.firstOrNull()?.uppercaseChar()?.toString() ?: "?"

            Row(verticalAlignment = Alignment.Top) {
                Box(
                    modifier = Modifier
                        .padding(end = 12.dp)
                        .size(48.dp)
                        .clip(CircleShape)
                        .background(MaterialTheme.colorScheme.primary),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        senderInitial,
                        color = Color.White,
                        fontWeight = FontWeight.SemiBold,
                        style = MaterialTheme.typography.titleLarge,
                    )
                }
                Column(Modifier.weight(1f)) {
                    Text(
                        senderName,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                    if (senderEmail.isNotBlank()) {
                        Text(
                            senderEmail,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Text(
                        mail.date,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 2.dp),
                    )
                }
                if (mail.starred) {
                    Icon(Icons.Default.Star, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                } else {
                    Icon(Icons.Outlined.StarOutline, contentDescription = null)
                }
            }

            Spacer(Modifier.height(12.dp))
            Text(
                mail.subject.ifBlank { "(Konu yok)" },
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Medium,
            )
            Spacer(Modifier.height(8.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("tr" to "TR", "en" to "EN", "de" to "DE").forEach { (code, label) ->
                    FilterChip(
                        selected = translatedLang.value == code,
                        onClick = { translate(code) },
                        label = { Text(label) },
                    )
                }
            }

            Spacer(Modifier.height(12.dp))

            if (loading.value) {
                CircularProgressIndicator()
            } else {
                Text(content.value, style = MaterialTheme.typography.bodyLarge)
            }

            if (mail.attachments.isNotEmpty()) {
                Spacer(Modifier.height(16.dp))
                Text("Ekler (${mail.attachments.size})", fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(8.dp))
                mail.attachments.forEach { att ->
                    OutlinedButton(
                        onClick = { downloadAttachment(att) },
                        enabled = downloadingIndex.value == null,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                    ) {
                        if (downloadingIndex.value == att.index) {
                            CircularProgressIndicator(modifier = Modifier.height(18.dp))
                        } else {
                            Icon(Icons.Default.Download, contentDescription = null)
                        }
                        Spacer(Modifier.padding(horizontal = 4.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                att.filename.ifBlank { "ek" },
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                            Text(
                                formatSize(att.size),
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                    }
                }
            }
        }
    }
}

private fun formatSize(bytes: Int): String {
    if (bytes < 1024) return "$bytes B"
    if (bytes < 1024 * 1024) return "${bytes / 1024} KB"
    return "${bytes / (1024 * 1024)} MB"
}

private fun formatSenderName(mail: MailItem): String {
    val raw = mail.sender_display.ifBlank { mail.sender }.trim()
    val nameMatch = Regex("^\"?([^\"<]+)\"?\\s*<").find(raw)
    if (nameMatch != null) {
        return nameMatch.groupValues[1].trim()
    }
    if (raw.contains("@") && !raw.contains(" ")) {
        return raw.substringBefore("@")
    }
    return raw.ifBlank { "Bilinmeyen gönderen" }
}

private fun formatSenderEmail(mail: MailItem): String {
    val raw = mail.sender_display.ifBlank { mail.sender }.trim()
    val emailMatch = Regex("<([^>]+)>").find(raw)
    if (emailMatch != null) {
        return emailMatch.groupValues[1].trim()
    }
    return mail.sender.trim().takeIf { it.contains("@") } ?: raw.takeIf { it.contains("@") } ?: ""
}
