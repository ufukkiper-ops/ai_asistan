from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify, make_response
import os, json, base64, email, re
from email.header import decode_header
from openai import OpenAI
from mail import get_last_mails, analyze_mail, send_reply_mail, connect_mail

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "gizli123")

# --- VERİ YÖNETİMİ ---
USERS_FILE = "users.json"
DATA_FILE = "data.json"

def ensure_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f: json.dump([], f, ensure_ascii=False, indent=2)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump({}, f, ensure_ascii=False, indent=2)

def load_users():
    ensure_files()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f: json.dump(users, f, ensure_ascii=False, indent=2)

def load_data():
    ensure_files()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key) if api_key else None

# --- ROTALAR ---

@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session: return redirect(url_for("login"))
    # Ana sayfa içeriğini buraya koyabilirsin
    return render_page("<h1>KipGPT Ana Sayfa</h1><a href='/mail'>Mail Kutusu</a>")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        users = load_users()
        if any(u["username"] == username for u in users):
            error = "Bu kullanıcı adı zaten kullanılıyor."
        else:
            users.append({"username": username, "password": password})
            save_users(users)
            return redirect(url_for("login"))
    
    content = f"<h2>Kayıt Ol</h2><form method='post'><input name='username' placeholder='Kullanıcı'><input name='password' type='password'><button>Kayıt Ol</button></form>"
    return render_page(content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        session["user"] = username
        return redirect(url_for("index"))
    return render_page("<form method='post'><input name='username'><button>Giriş</button></form>")

@app.route("/mail", methods=["GET", "POST"])
def mail_route():
    if "user" not in session: return redirect(url_for("login"))
    
    # AI İşlemleri (Eski kodundaki 'olustur' ve 'revize_et' mantığını buraya taşıdık)
    ai_yaniti = ""
    if request.method == "POST":
        islem = request.form.get("islem")
        # ... buraya AI mantığını ekle ...
    
    mailler = get_last_mails(count=5)
    content = "<h2>Mail Kutusu</h2>"
    # ... mailleri listele ...
    
    response = make_response(render_page(content))
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

# BASE_HTML ve render_page fonksiyonların aynı kalsın...
def render_page(content):
    # Senin mevcut BASE_HTML değişkenini burada kullan
    return render_template_string(BASE_HTML, content=content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)