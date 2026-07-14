function appendMessage(role, text){

    const messages = document.querySelector(".messages");

    const div = document.createElement("div");

    div.className =
        role==="user"
        ? "msg msg-user"
        : "msg msg-bot";

    div.innerHTML =
        `<b>${role==="user" ? "Sen" : "KipGPT"}:</b><br>${text}`;

    messages.appendChild(div);

    messages.scrollTop = messages.scrollHeight;

    return div;
}
async function sendTextMessage(event) {
    event.preventDefault();

    const input = document.getElementById("chat-input");
    const message = input.value.trim();

    const fileInput = document.getElementById("file-input");

if (!message && fileInput.files.length === 0) {
    return;
}

    const messages = document.querySelector(".messages");

    // Kullanıcının mesajını hemen ekrana yaz
    appendMessage("user", message);

    // KipGPT düşünüyor...
    const loading =
    appendMessage(
        "assistant",
        "<i>KipGPT düşünüyor...</i>"
    );

    messages.scrollTop = messages.scrollHeight;

    const formData = new FormData();
    

if (fileInput.files.length > 0) {
    formData.set("action", "image");
    formData.append("image", fileInput.files[0]);
    formData.append("image_prompt", message || "Bu resmi detaylı analiz et.");
} else {
    formData.set("action", "text");
    formData.append("soru", message);
}


    input.value = "";

    try {

    console.log("FETCH BAŞLIYOR");
    console.log(formData.get("action"));
    console.log(formData.get("soru"));

    const response = await fetch("/", {
    method: "POST",
    body: formData
});

console.log(response.status);

const data = await response.json();

    if (data.status === "success") {

        loading.innerHTML = "<b>KipGPT:</b><br>" + data.answer;

    } else {

        loading.innerHTML = "<b>Hata:</b><br>" + data.error;

    }



    } catch (e) {

        loading.innerHTML = `
            <b>Bağlantı Hatası</b>
        `;

        console.error(e);

    }

    messages.scrollTop = messages.scrollHeight;
}