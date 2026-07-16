package com.kipgpt.app.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore("kipgpt_session")

class SessionManager(private val context: Context) {
    companion object {
        private val KEY_TOKEN = stringPreferencesKey("token")
        private val KEY_BASE_URL = stringPreferencesKey("base_url")
        private val KEY_USER_EMAIL = stringPreferencesKey("user_email")
        private val KEY_MAIL_ACCOUNT = stringPreferencesKey("active_mail_account_id")
        const val DEFAULT_BASE_URL = "https://kip-asistan.onrender.com/api/v1/"
        const val EMULATOR_BASE_URL = "http://10.0.2.2:5001/api/v1/"
        const val RENDER_BASE_URL = "https://kip-asistan.onrender.com/api/v1/"
        const val LAN_IP_PLACEHOLDER = "10.252.49.1"

        fun lanBaseUrl(ip: String = LAN_IP_PLACEHOLDER): String {
            val clean = ip.trim().trimEnd('/')
            return "http://$clean:5001/api/v1/"
        }
    }

    val tokenFlow: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[KEY_TOKEN]
    }

    val baseUrlFlow: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_BASE_URL] ?: DEFAULT_BASE_URL
    }

    val userEmailFlow: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[KEY_USER_EMAIL]
    }

    val activeMailAccountFlow: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[KEY_MAIL_ACCOUNT]
    }

    suspend fun getActiveMailAccount(): String? {
        return activeMailAccountFlow.first()
    }

    suspend fun saveToken(token: String, email: String? = null) {
        context.dataStore.edit { prefs ->
            prefs[KEY_TOKEN] = token
            if (!email.isNullOrBlank()) {
                prefs[KEY_USER_EMAIL] = email
            }
        }
    }

    suspend fun clearToken() {
        context.dataStore.edit { prefs ->
            prefs.remove(KEY_TOKEN)
            prefs.remove(KEY_USER_EMAIL)
            prefs.remove(KEY_MAIL_ACCOUNT)
        }
    }

    suspend fun saveActiveMailAccount(accountId: String?) {
        context.dataStore.edit { prefs ->
            if (accountId.isNullOrBlank()) {
                prefs.remove(KEY_MAIL_ACCOUNT)
            } else {
                prefs[KEY_MAIL_ACCOUNT] = accountId
            }
        }
    }

    suspend fun saveBaseUrl(url: String) {
        val normalized = if (url.endsWith("/")) url else "$url/"
        context.dataStore.edit { prefs ->
            prefs[KEY_BASE_URL] = normalized
        }
    }
}
