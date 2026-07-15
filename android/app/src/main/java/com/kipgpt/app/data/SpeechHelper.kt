package com.kipgpt.app.data

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import java.util.Locale

private fun Context.findActivity(): Activity? {
    var current: Context = this
    while (current is ContextWrapper) {
        if (current is Activity) {
            return current
        }
        current = current.baseContext
    }
    return null
}

class SpeechHelper(context: Context) {
    private val appContext = context.applicationContext
    private val recognizerContext: Context = context.findActivity() ?: context
    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var recognizer: SpeechRecognizer? = null
    private var listening = false
    private var onListenResult: ((String) -> Unit)? = null
    private var onListenError: ((String) -> Unit)? = null
    private var onListenEnd: (() -> Unit)? = null

    init {
        tts = TextToSpeech(appContext) { status ->
            ttsReady = status == TextToSpeech.SUCCESS
            if (ttsReady) {
                val turkish = Locale("tr", "TR")
                val language = if (tts?.isLanguageAvailable(turkish) == TextToSpeech.LANG_AVAILABLE) {
                    turkish
                } else {
                    Locale.getDefault()
                }
                tts?.language = language
            }
        }
        ensureRecognizer()
    }

    private fun ensureRecognizer(): SpeechRecognizer? {
        if (recognizer != null) {
            return recognizer
        }
        if (!SpeechRecognizer.isRecognitionAvailable(recognizerContext)) {
            return null
        }

        recognizer = SpeechRecognizer.createSpeechRecognizer(recognizerContext).apply {
            setRecognitionListener(recognitionListener)
        }
        return recognizer
    }

    private val recognitionListener = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() {}
        override fun onError(error: Int) {
            listening = false
            if (error == SpeechRecognizer.ERROR_CLIENT ||
                error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY
            ) {
                recognizer?.destroy()
                recognizer = null
            }
            onListenError?.invoke(mapSpeechError(error))
            onListenEnd?.invoke()
        }

        override fun onResults(results: Bundle?) {
            listening = false
            val text = results
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()
                ?.trim().orEmpty()
            if (text.isNotBlank()) {
                onListenResult?.invoke(text)
            } else {
                onListenError?.invoke("Ses anlaşılamadı")
            }
            onListenEnd?.invoke()
        }

        override fun onPartialResults(partialResults: Bundle?) {}
        override fun onEvent(eventType: Int, params: Bundle?) {}
    }

    fun isListenAvailable(): Boolean = ensureRecognizer() != null
    fun isSpeakAvailable(): Boolean = ttsReady
    fun isListening(): Boolean = listening
    fun isSpeaking(): Boolean = tts?.isSpeaking == true

    fun speak(text: String) {
        if (!ttsReady || text.isBlank()) return
        stopSpeaking()
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "kipgpt-tts")
    }

    fun stopSpeaking() {
        tts?.stop()
    }

    fun startListening(
        onResult: (String) -> Unit,
        onError: (String) -> Unit,
        onEnd: () -> Unit = {},
    ): Boolean {
        val speechRecognizer = ensureRecognizer() ?: run {
            onError("Ses tanıma kullanılamıyor. Google uygulamasını güncelleyin.")
            return false
        }
        if (listening) {
            stopListening()
            return false
        }

        onListenResult = onResult
        onListenError = onError
        onListenEnd = onEnd
        listening = true

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "tr-TR")
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "tr-TR")
            putExtra(RecognizerIntent.EXTRA_ONLY_RETURN_LANGUAGE_PREFERENCE, false)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Konuşmaya başlayın")
        }

        return try {
            speechRecognizer.startListening(intent)
            true
        } catch (e: Exception) {
            listening = false
            recognizer?.destroy()
            recognizer = null
            onError(e.message ?: "Mikrofon başlatılamadı")
            false
        }
    }

    fun stopListening() {
        recognizer?.stopListening()
        recognizer?.cancel()
        listening = false
    }

    fun shutdown() {
        stopListening()
        stopSpeaking()
        recognizer?.destroy()
        recognizer = null
        tts?.shutdown()
        tts = null
        ttsReady = false
    }

    private fun mapSpeechError(error: Int): String {
        return when (error) {
            SpeechRecognizer.ERROR_AUDIO -> "Ses kaydı hatası"
            SpeechRecognizer.ERROR_CLIENT -> "Ses tanıma iptal edildi"
            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Mikrofon izni gerekli"
            SpeechRecognizer.ERROR_NETWORK -> "İnternet gerekli (Google ses tanıma)"
            SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Ağ zaman aşımı"
            SpeechRecognizer.ERROR_NO_MATCH -> "Ses anlaşılamadı, tekrar deneyin"
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Ses tanıma meşgul, tekrar deneyin"
            SpeechRecognizer.ERROR_SERVER -> "Ses sunucusu hatası"
            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Konuşma algılanmadı"
            else -> "Ses tanıma hatası"
        }
    }
}
