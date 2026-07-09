import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from openai import OpenAI

# 🔐 EMAIL VE SUNUCU AYARLARI
EMAIL = "ufukkiper@pamecarbon.com"
PASSWORD = "Ufuk-55-"  # 16 haneli Google Uygulama Şifreniz

IMAP_SERVER = "mail.pamecarbon.com"
SMTP_SERVER = "mail.pamecarbon.com"
SMTP_PORT = 465

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def connect_mail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")
    return mail

def get_last_mails(count=5):
    mail = connect_mail()
    _, messages = mail.search(None, "ALL")
    mail_ids = messages[0].split()

    result = []

    for i in reversed(mail_ids[-count:]):
        try:
            _, msg_data = mail.fetch(i, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # 🛠️ Konu Başlığı Çözümü
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")

            # 🛠️ Gönderici (Kimden) Çözümü - Bozuk görünen yer burasıydı
            from_raw = msg.get("From")
            from_parts = decode_header(from_raw)
            from_text = ""
            for part, enc in from_parts:
                if isinstance(part, bytes):
                    from_text += part.decode(enc if enc else "utf-8", errors="ignore")
                else:
                    from_text += str(part)
            
            # E-posta adresini saf halde temizlemek için (örn: "İsim <mail@mail.com>" -> "mail@mail.com")
            import re
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', from_text)
            sender_email = email_match.group(0) if email_match else from_text

            # 🛠️ İçerik Çözümü
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                        break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")

            # Metni temizleme ve kırpma
            body = body.strip()

            result.append({
                "id": i.decode(),
                "subject": subject,
                "sender_display": from_text, # Ekranda güzel görünen isim
                "sender": sender_email,      # Arka planda mail atılacak gerçek adres
                "content": body[:1000]
            })
        except Exception as e:
            print(f"Bir mail ayrıştırılırken hata atlandı: {e}")
            continue

    return result

def analyze_mail(text):
    prompt = f"Bu maili analiz et:\n- önemli mi\n- kısa özet\n- yapılması gereken\n- cevap öner\n\nMail:\n{text}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def send_reply_mail(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        raise Exception(f"E-posta gönderilirken kritik hata: {str(e)}")