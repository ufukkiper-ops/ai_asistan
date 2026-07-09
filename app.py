from mail import get_last_mails, analyze_mail
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import os
import json
import base64
from openai import OpenAI
from pypdf import PdfReader
import docx

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "gizli123")
@@ -58,30 +55,6 @@
    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

# --- YENİ: DOKÜMAN OKUMA FONKSİYONLARI ---
def read_pdf(file_storage):
    try:
        reader = PdfReader(file_storage)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except Exception as e:
        return f"[PDF Okuma Hatası: {str(e)}]"

def read_docx(file_storage):
    try:
        doc = docx.Document(file_storage)
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return "\n".join(text).strip()
    except Exception as e:
        return f"[Word Okuma Hatası: {str(e)}]"
# -----------------------------------------

BASE_HTML = """
<!DOCTYPE html>
<html lang="tr">
@@ -92,15 +65,12 @@
    
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
    <link rel="shortcut icon" type="image/x-icon" href="/static/favicon.ico">
    
    <link rel="apple-touch-icon" sizes="192x192" href="/static/icon.png">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    
    <title>AI Asistan</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        /* CSS kodların aynen kalıyor... */
        :root {
            color-scheme: light !important;
            --background-color: #ffffff !important;
@@ -113,6 +83,46 @@
            color: #0f172a !important;
            display: flex; height: 100vh; overflow: hidden;
        }
        a { text-decoration: none; color: inherit; }
        .layout { display: flex; width: 100%; height: 100%; background-color: #ffffff !important; }
        .sidebar {
            width: 280px; background: #f8fafc !important; padding: 20px;
            border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 15px;
        }
        .sidebar h2 { margin: 0; font-size: 20px; font-weight: 600; color: #0284c7 !important; }
        .user-box { padding: 12px; background: #f1f5f9 !important; border-radius: 12px; font-size: 14px; border: 1px solid #e2e8f0; color: #334155 !important; }
        .new-chat { display: block; width: 100%; background: linear-gradient(135deg, #38bdf8, #0284c7) !important; color: white !important; text-align: center; padding: 12px; border-radius: 12px; font-weight: 600; transition: all 0.2s; }
        .new-chat:hover { opacity: 0.9; transform: translateY(-1px); }
        .chat-list { display: flex; flex-direction: column; gap: 8px; overflow-y: auto; flex: 1; }
        .chat-item { display: block; padding: 12px; border-radius: 10px; background: #f1f5f9 !important; font-size: 14px; border: 1px solid transparent; transition: all 0.2s; color: #334155 !important; }
        .chat-item:hover { background: #e2e8f0 !important; }
        .chat-item.active { background: #3b82f6 !important; border-color: #2563eb !important; color: white !important; }
        .main { flex: 1; display: flex; flex-direction: column; background-color: #ffffff !important; }
        .topbar { background: #f8fafc !important; padding: 15px 25px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; color: #334155 !important; }
        .right-buttons { display: flex; gap: 10px; }
        .btn { border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-weight: 500; transition: opacity 0.2s; }
        .btn:hover { opacity: 0.9; }
        .btn-blue { background: #38bdf8 !important; color: black !important; }
        .btn-red { background: #ef4444 !important; color: white !important; }
        .btn-green { background: #10b981 !important; color: white !important; }
        .messages { flex: 1; padding: 25px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; background-color: #ffffff !important; }
        .msg { max-width: 75%; padding: 14px 18px; border-radius: 16px; line-height: 1.6; white-space: pre-wrap; font-size: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .msg-user { background: #0284c7 !important; color: white !important; align-self: flex-end; border-bottom-right-radius: 4px; }
        .msg-user * { color: white !important; }
        .msg-bot { background-color: #f1f5f9 !important; color: #0f172a !important; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid #e2e8f0; }
        .msg-bot, .msg-bot *, .bot-text, .messages .msg-bot * { color: #0f172a !important; }
        .msg img { max-width: 100%; border-radius: 10px; margin-top: 10px; }
        .bottom { padding: 20px; background: #f8fafc !important; border-top: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 10px; }
        .input-container { display: flex; background: #ffffff !important; border-radius: 14px; padding: 6px; align-items: center; border: 1px solid #cbd5e1; }
        .input-container input[type="text"] { flex: 1; background: transparent !important; border: none; padding: 10px 15px; color: #0f172a !important; font-size: 15px; outline: none; }
        .card { max-width: 400px; margin: 100px auto; background: #ffffff !important; padding: 30px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); color: #0f172a !important; }
        .card input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #cbd5e1; background: #ffffff !important; border-radius: 10px; color: #0f172a !important; }
        .error { color: #7f1d1d !important; background: #fca5a5 !important; padding: 12px; border-radius: 10px; margin-bottom: 15px; font-size: 14px; }
        .image-bar { display: flex; gap: 10px; align-items: center; font-size: 13px; background: #f1f5f9 !important; padding: 8px 12px; border-radius: 10px; color: #334155 !important; }
        @media (max-width: 768px) { .sidebar { display: none; } }
    </style>
</head>
<body>
{{ content|safe }}
<script>
    const msgDiv = document.querySelector('.messages');
@@ -307,68 +317,32 @@
                save_data(data)
                return jsonify({"status": "success", "answer": cevap})

        elif action == "image":  # Bu alan artık genel dosya/resim yükleme alanı oldu
        elif action == "image":
            uploaded_file = request.files.get("image")
            prompt = request.form.get("image_prompt", "").strip() or "Bu dosyayı detaylı incele ve yorumla."
            prompt = request.form.get("image_prompt", "").strip() or "Bu resmi detaylı yorumla."

            if uploaded_file and uploaded_file.filename != "":
                filename = uploaded_file.filename.lower()
                
                try:
                    # --- RESİM Mİ DOKÜMAN MI KONTROLÜ ---
                    if filename.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                        # Gelen dosya resim ise vision modeline gönderiyoruz
                        image_data_url = image_file_to_data_url(uploaded_file)
                        gecmis.append({
                            "role": "user",
                            "content": f"[RESİM] {prompt}",
                            "image": image_data_url
                        })
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {"type": "image_url", "image_url": {"url": image_data_url}}
                                    ]
                                }
                            ]
                        )
                        cevap = response.choices[0].message.content
                        gecmis.append({"role": "assistant", "content": cevap})

                    elif filename.endswith('.pdf'):
                        # Gelen dosya PDF ise metni çıkarıyoruz
                        pdf_text = read_pdf(uploaded_file)
                        tam_soru = f"Kullanıcı bir PDF dokümanı yükledi. Sorusu: {prompt}\n\nDoküman İçeriği:\n{pdf_text}"
                        gecmis.append({"role": "user", "content": f"[DOKÜMAN - {uploaded_file.filename}] {prompt}"})
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": tam_soru}]
                        )
                        cevap = response.choices[0].message.content
                        gecmis.append({"role": "assistant", "content": cevap})

                    elif filename.endswith(('.docx', '.doc')):
                        # Gelen dosya Word ise metni çıkarıyoruz
                        docx_text = read_docx(uploaded_file)
                        tam_soru = f"Kullanıcı bir Word dokümanı yükledi. Sorusu: {prompt}\n\nDoküman İçeriği:\n{docx_text}"
                        gecmis.append({"role": "user", "content": f"[DOKÜMAN - {uploaded_file.filename}] {prompt}"})
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": tam_soru}]
                        )
                        cevap = response.choices[0].message.content
                        gecmis.append({"role": "assistant", "content": cevap})
                    
                    else:
                        cevap = "Desteklenmeyen dosya formatı. Lütfen Resim, PDF veya Word dosyası yükleyin."
                        gecmis.append({"role": "assistant", "content": cevap})

                    image_data_url = image_file_to_data_url(uploaded_file)
                    gecmis.append({
                        "role": "user",
                        "content": f"[RESİM] {prompt}",
                        "image": image_data_url
                    })
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": image_data_url}}
                                ]
                            }
                        ]
                    )
                    cevap = response.choices[0].message.content
                    gecmis.append({"role": "assistant", "content": cevap})
                    data[username]["chats"][active_chat] = gecmis
                    save_data(data)
                except Exception as e:
@@ -420,15 +394,15 @@
                
                <form class="image-bar" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="action" value="image">
                    <input type="file" name="image" accept="image/*,.pdf,.docx" required style="color:#0f172a; font-size:12px;">
                    <input type="text" name="image_prompt" placeholder="Dosya ile ilgili sorunuz..." style="background:#ffffff; border:1px solid #cbd5e1; padding:5px; color:#0f172a; border-radius:5px;">
                    <button class="btn btn-green" type="submit" style="padding:5px 10px; font-size:12px;">Dosyayı Yorumlat</button>
                    <input type="file" name="image" accept="image/*" required style="color:#0f172a; font-size:12px;">
                    <input type="text" name="image_prompt" placeholder="Resim sorusu..." style="background:#ffffff; border:1px solid #cbd5e1; padding:5px; color:#0f172a; border-radius:5px;">
                    <button class="btn btn-green" type="submit" style="padding:5px 10px; font-size:12px;">Resmi Yorumlat</button>
                </form>
            </div>
        </div>
    </div>
    """
    return render_page(content)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))