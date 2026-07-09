from flask import Flask, render_template_string
import os

app = Flask(__name__)

# Basit bir HTML arayüzü
BASE_HTML = "<html><body><h1>Kip Asistan Aktif!</h1></body></html>"

@app.route("/")
def home():
    return render_template_string(BASE_HTML)

if __name__ == "__main__":
    # Render, PORT değişkenini otomatik atar
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)