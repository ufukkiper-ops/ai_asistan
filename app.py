from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return "Sunucu çalışıyor!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)))