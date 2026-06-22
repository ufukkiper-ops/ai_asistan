from flask import Flask, request, render_template_string, redirect, url_for, session
import os
import json
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "gizli123")

# -------------------------------
# DOSYA YARDIMCILARI
# -------------------------------
USERS_FILE = "users.json"
DATA_FILE = "data.json"


def ensure_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def load_users():
    ensure_files()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_data():
    ensure_files()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -------------------------------
# OPENAI CLIENT
# -------------------------------
def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


# -------------------------------
# HTML ŞABLONU
# -------------------------------
BASE_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Asistan</title>
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        .layout {
            display: flex;
            min-height: 100vh;
        }

        .sidebar {
            width: 260px;
            background: #020617;
            padding: 14px;
            border-right: 1px solid #1e293b;
        }

        .sidebar h2 {
            margin-top: 0;
            font-size: 18px;
        }

        .sidebar .user-box {
            margin-bottom: 14px;
            padding: 10px;
            background: #111827;
            border-radius: 10px;
        }

        .sidebar .new-chat {
            display: block;
            width: 100%;
            background: #38bdf8;
            color: black;
            text-align: center;
            padding: 10px;
            border-radius: 10px;
            font-weight: bold;
            margin-bottom: 12px;
        }

        .chat-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .chat-item {
            padding: 10px;
            border-radius: 10px;
            background: #111827;
            font-size: 14px;
            cursor: pointer;
        }

        .chat-item.active {
            background: #2563eb;
        }

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .topbar {
            background: #020617;
            padding: 14px 18px;
            border-bottom: 1px solid #1e293b;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .topbar .right-buttons {
            display: flex;
            gap: 8px;
        }

        .btn {
            border: none;
            border-radius: 10px;
            padding: 10px 14px;
            cursor: pointer;
            font-weight: bold;
        }

        .btn-blue {
            background: #38bdf8;
            color: black;
        }

        .btn-red {
            background: #ef4444;
            color: white;
        }

        .messages {
            flex: 1;
            padding: 18px;
            overflow-y: auto;
            background: #0f172a;
        }

        .msg {
            max-width: 80%;
            margin-bottom: 12px;
            padding: 12px;
            border-radius: 12px;
            line-height: 1.4;
            white-space: pre-wrap;
        }

        .msg-user {
            background: #0ea5e9;
            color: black;
            margin-left: auto;
            text-align: right;
        }

        .msg-bot {
            background: #22c55e;
            color: black;
            margin-right: auto;
            text-align: left;
        }

        .bottom {
            padding: 12px;
            background: #020617;
            border-top: 1px solid #1e293b;
        }

        .send-form {
            display: flex;
            gap: 8px;
        }

        .send-form input {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
        }

        .card {
            max-width: 420px;
            margin: 60px auto;
            background: #1e293b;
            padding: 22px;
            border-radius: 14px;
        }

        .card input {
            width: 100%;
            padding: 12px;
            margin-bottom: 10px;
            border: none;
            border-radius: 10px;
        }

        .error {
            color: #fca5a5;
            margin-bottom: 10px;
            min-height: 20px;
        }

        .helper-link {
            color: #38bdf8;
            font-weight: bold;
        }

        @media (max-width: 800px) {
            .layout {
                flex-direction: column;
            }

            .sidebar {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid #1e293b;
            }

            .messages {
                min-height: 50vh;
            }
        }
    </style>
</head>
<body>
    %CONTENT%
</body>
</html>
"""


# -------------------------------
# REGISTER
# -------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == "" or password == "":
            error = "Kullanıcı adı ve şifre boş olamaz."
        else:
            users = load_users()

            for user in users:
                if user["username"] == username:
                    error = "Bu kullanıcı adı zaten kullanılıyor."
                    break

            if error == "":
                users.append({
                    "username": username,
                    "password": password
                })
                save_users(users)
                return redirect(url_for("login"))

    content = f"""
    <div class="card">
        <h2>Kayıt Ol</h2>
        <div class="error">{error}</div>
        <form method="post">
            <input name="username" placeholder="Kullanıcı adı">
            <input name="password" type="password" placeholder="Şifre">
            <button class="btn btn-blue" type="submit">Kayıt Ol</button>
        </form>
        <p>Zaten hesabın var mı? <a class="helper-link" href="/login">Giriş Yap</a></p>
    </div>
    """
    return BASE_HTML.replace("%CONTENT%", content)


# -------------------------------
# LOGIN
# -------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        users = load_users()
        found = False

        for user in users:
            if user["username"] == username and user["password"] == password:
                session["user"] = username
                found = True
                break

        if found:
            return redirect(url_for("index"))
        else:
            error = "Kullanıcı adı veya şifre hatalı."

    content = f"""
    <div class="card">
        <h2>Giriş Yap</h2>
        <div class="error">{error}</div>
        <form method="post">
            <input name="username" placeholder="Kullanıcı adı">
            <input name="password" type="password" placeholder="Şifre">
            <button class="btn btn-blue" type="submit">Giriş Yap</button>
        </form>
        <p>Hesabın yok mu? <a class="helper-link" href="/register">Kayıt Ol</a></p>
    </div>
    """
    return BASE_HTML.replace("%CONTENT%", content)


# -------------------------------
# LOGOUT
# -------------------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# -------------------------------
# YENİ SOHBET
# -------------------------------
@app.route("/new_chat")
def new_chat():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    data = load_data()

    if username not in data or not isinstance(data[username], dict):
        data[username] = {
            "active_chat": "chat1",
            "chats": {
                "chat1": []
            }
        }

    chats = data[username]["chats"]
    new_id = f"chat{len(chats) + 1}"
    chats[new_id] = []
    data[username]["active_chat"] = new_id

    save_data(data)
    return redirect(url_for("index"))


# -------------------------------
# SOHBET DEĞİŞTİR
# -------------------------------
@app.route("/switch/<chat_id>")
def switch_chat(chat_id):
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    data = load_data()

    if username in data and "chats" in data[username] and chat_id in data[username]["chats"]:
        data[username]["active_chat"] = chat_id
        save_data(data)

    return redirect(url_for("index"))


# -------------------------------
# SOHBET TEMİZLE
# -------------------------------
@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    data = load_data()

    if username in data:
        active_chat = data[username].get("active_chat", "chat1")
        if active_chat in data[username]["chats"]:
            data[username]["chats"][active_chat] = []
            save_data(data)

    return redirect(url_for("index"))


# -------------------------------
# ANA SAYFA / CHAT
# -------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    data = load_data()

    # Kullanıcı için veri yoksa hazırla
    if username not in data or not isinstance(data[username], dict):
        data[username] = {
            "active_chat": "chat1",
            "chats": {
                "chat1": []
            }
        }

    if "active_chat" not in data[username]:
        data[username]["active_chat"] = "chat1"

    if "chats" not in data[username]:
        data[username]["chats"] = {"chat1": []}

    active_chat = data[username]["active_chat"]
    chats = data[username]["chats"]

    if active_chat not in chats:
        chats[active_chat] = []

    gecmis = chats[active_chat]

    if request.method == "POST":
        soru = request.form.get("soru", "").strip()

        if soru != "":
            gecmis.append({"role": "user", "content": soru})

            client = get_client()
            if client is None:
                cevap = "Sunucuda OPENAI_API_KEY ayarlı değil."
            else:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=gecmis
                    )
                    cevap = response.choices[0].message.content
                except Exception as e:
                    cevap = f"AI hatası: {str(e)}"

            gecmis.append({"role": "assistant", "content": cevap})

            data[username]["chats"][active_chat] = gecmis
            save_data(data)

            return redirect(url_for("index"))

    # Sol menü sohbet listesi
    chat_list_html = ""
    for cid in chats.keys():
        cls = "chat-item active" if cid == active_chat else "chat-item"
        chat_list_html += f'<a class="{cls}" href="/switch/{cid}">{cid}</a>'

    # Mesaj alanı
    messages_html = ""
    for mesaj in gecmis:
        if mesaj["role"] == "user":
            messages_html += f'<div class="msg msg-user"><b>Sen:</b><br>{mesaj["content"]}</div>'
        else:
            messages_html += f'<div class="msg msg-bot"><b>AI:</b><br>{mesaj["content"]}</div>'

    content = f"""
    <div class="layout">
        <div class="sidebar">
            <h2>AI Asistan</h2>

            <div class="user-box">
                <div><b>Kullanıcı:</b> {username}</div>
            </div>

            <a href="/new_chat" class="new-chat">+ Yeni Sohbet</a>

            <div class="chat-list">
                {chat_list_html}
            </div>
        </div>

        <div class="main">
            <div class="topbar">
                <div><b>Aktif Sohbet:</b> {active_chat}</div>
                <div class="right-buttons">
                    <form method="post" action="/clear_chat" style="display:inline;">
                        <button class="btn btn-red" type="submit">Temizle</button>
                    </form>
                    <a href="/logout"><button class="btn btn-blue" type="button">Çıkış</button></a>
                </div>
            </div>

            <div class="messages">
                {messages_html}
            </div>

            <div class="bottom">
                <form class="send-form" method="post">
                    <input name="soru" placeholder="Mesaj yaz..." autofocus>
                    <button class="btn btn-blue" type="submit">Gönder</button>
                </form>
            </div>
        </div>
    </div>
    """

    return BASE_HTML.replace("%CONTENT%", content)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)