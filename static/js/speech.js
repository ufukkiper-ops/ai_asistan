(function (global) {
    const SpeechRecognition = global.SpeechRecognition || global.webkitSpeechRecognition;
    const synth = global.speechSynthesis;

    let recognition = null;
    let listening = false;
    let activeMicButton = null;

    function isSpeechSupported() {
        return !!SpeechRecognition;
    }

    function isSpeakSupported() {
        return !!synth;
    }

    function stripForSpeech(text) {
        return String(text || "")
            .replace(/<[^>]+>/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    }

    function setMicButtonState(button, active) {
        if (!button) return;
        button.classList.toggle("is-listening", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
    }

    function speak(text, options) {
        if (!synth || !text) return false;
        stopSpeaking();
        const utter = new SpeechSynthesisUtterance(stripForSpeech(text));
        utter.lang = (options && options.lang) || "tr-TR";
        utter.rate = (options && options.rate) || 1;
        synth.speak(utter);
        return true;
    }

    function stopSpeaking() {
        if (synth) synth.cancel();
    }

    function isSpeaking() {
        return !!synth && synth.speaking;
    }

    function stopListening() {
        if (recognition) {
            try {
                recognition.stop();
            } catch (_err) {
                /* ignore */
            }
        }
        listening = false;
        setMicButtonState(activeMicButton, false);
        activeMicButton = null;
    }

    function startListening(onResult, onError, onEnd, micButton) {
        if (!SpeechRecognition) {
            if (onError) onError("Tarayıcınız sesli girişi desteklemiyor.");
            return false;
        }

        if (listening) {
            stopListening();
            return false;
        }

        recognition = new SpeechRecognition();
        recognition.lang = "tr-TR";
        recognition.interimResults = false;
        recognition.continuous = false;
        activeMicButton = micButton || null;
        setMicButtonState(activeMicButton, true);
        listening = true;

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            if (onResult) onResult(transcript);
        };

        recognition.onerror = function (event) {
            if (onError) onError(event.error || "Ses tanıma hatası");
        };

        recognition.onend = function () {
            listening = false;
            setMicButtonState(activeMicButton, false);
            activeMicButton = null;
            if (onEnd) onEnd();
        };

        try {
            recognition.start();
            return true;
        } catch (err) {
            listening = false;
            setMicButtonState(activeMicButton, false);
            activeMicButton = null;
            if (onError) onError(err.message || "Mikrofon başlatılamadı");
            return false;
        }
    }

    function bindMicToField(button, field, options) {
        if (!button || !field) return;

        button.addEventListener("click", function () {
            if (listening && activeMicButton === button) {
                stopListening();
                return;
            }

            const append = options && options.append;
            startListening(
                function (transcript) {
                    const value = (field.value || "").trim();
                    field.value = append && value ? value + " " + transcript : transcript;
                    field.dispatchEvent(new Event("input", { bubbles: true }));
                    field.focus();
                },
                function (message) {
                    if (options && options.onError) {
                        options.onError(message);
                    } else {
                        window.alert(message);
                    }
                },
                null,
                button
            );
        });
    }

    function createSpeakButton(textProvider) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "speech-speak-btn";
        button.title = "Dinle";
        button.innerHTML = '<span class="material-icons-outlined">volume_up</span>';
        button.addEventListener("click", function () {
            if (isSpeaking()) {
                stopSpeaking();
                return;
            }
            const text = typeof textProvider === "function" ? textProvider() : textProvider;
            speak(text);
        });
        return button;
    }

    global.KipSpeech = {
        speak: speak,
        stopSpeaking: stopSpeaking,
        isSpeaking: isSpeaking,
        startListening: startListening,
        stopListening: stopListening,
        isListening: function () { return listening; },
        isSpeechSupported: isSpeechSupported,
        isSpeakSupported: isSpeakSupported,
        stripForSpeech: stripForSpeech,
        bindMicToField: bindMicToField,
        createSpeakButton: createSpeakButton,
    };
})(window);
