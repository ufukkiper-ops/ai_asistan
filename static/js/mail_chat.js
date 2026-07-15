(function () {
    function byId(id) {
        return document.getElementById(id);
    }

    document.addEventListener("DOMContentLoaded", function () {
        const toggle = byId("chat-bubble-toggle");
        const panel = byId("chat-bubble-panel");
        const closeBtn = byId("chat-bubble-close");
        const form = byId("chat-bubble-form");
        const input = byId("chat-bubble-text");
        const messages = byId("chat-bubble-messages");

        if (!toggle || !panel || !form || !input || !messages) {
            return;
        }

        function openPanel() {
            panel.hidden = false;
            toggle.classList.add("active");
            setTimeout(function () {
                input.focus();
            }, 50);
        }

        function closePanel() {
            panel.hidden = true;
            toggle.classList.remove("active");
        }

        toggle.addEventListener("click", function () {
            if (panel.hidden) {
                openPanel();
            } else {
                closePanel();
            }
        });

        if (closeBtn) {
            closeBtn.addEventListener("click", closePanel);
        }

        function appendMessage(role, text) {
            const empty = messages.querySelector(".chat-bubble-empty");
            if (empty) {
                empty.remove();
            }
            const div = document.createElement("div");
            div.className = "chat-bubble-msg " + (role === "user" ? "user" : "bot");
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            return div;
        }

        form.addEventListener("submit", async function (event) {
            event.preventDefault();

            const message = input.value.trim();
            if (!message) {
                return;
            }

            appendMessage("user", message);
            input.value = "";

            const loading = appendMessage("bot", "KipGPT düşünüyor...");
            loading.classList.add("loading");

            try {
                const formData = new FormData();
                formData.set("action", "text");
                formData.append("soru", message);

                const response = await fetch("/", {
                    method: "POST",
                    body: formData,
                });

                const contentType = response.headers.get("content-type") || "";
                if (!contentType.includes("application/json")) {
                    throw new Error("Sunucudan geçersiz yanıt alındı.");
                }

                const data = await response.json();
                loading.classList.remove("loading");

                if (data.status === "success") {
                    loading.textContent = data.answer;
                } else {
                    loading.textContent = "Hata: " + (data.error || "Bilinmeyen hata");
                }
            } catch (err) {
                loading.classList.remove("loading");
                loading.textContent = "Hata: " + (err.message || "Bağlantı hatası");
            }

            messages.scrollTop = messages.scrollHeight;
        });
    });
})();
