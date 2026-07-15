package com.kipgpt.app

import android.app.Application
import com.kipgpt.app.data.SessionManager

class KipGptApplication : Application() {
    lateinit var sessionManager: SessionManager
        private set

    override fun onCreate() {
        super.onCreate()
        sessionManager = SessionManager(this)
    }
}
