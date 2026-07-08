import imaplib
import email
from email.header import decode_header
import os
from openai import OpenAI

# EMAIL AYARLARI
EMAIL = "seninmail@gmail.com"
PASSWORD = "app_password"
IMAP_SERVER = "imap.gmail.com"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def connect_mail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")
    return mail


def get_last_mails(limit=5):
    mail = connect_mail()
    _, messages = mail.search(None, "ALL")
    mail_ids = messages[0].split()

    result = []

    for i in reversed(mail_ids[-limit:]):
        _, msg_data = mail.fetch(i, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subject, _ = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(errors="ignore")

        from_ = msg.get("From")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        result.append({
            "subject": subject,
            "from": from_,
            "body": body[:1000]
        })

    return result


def analyze_mail(text):
    prompt = f"""
Bu maili analiz et:

- önemli mi
- kısa özet
- yapılması gereken
- cevap öner

Mail:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content