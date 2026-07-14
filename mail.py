import imaplib
import smtplib
import email
import os
import re

from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from openai import OpenAI


# ===========================
# AYARLAR
# ===========================

EMAIL = "ufukkiper@pamecarbon.com"
PASSWORD = "Ufuk-55-"

IMAP_SERVER = "mail.pamecarbon.com"

SMTP_SERVER = "mail.pamecarbon.com"
SMTP_PORT = 587

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ===========================
# IMAP BAĞLANTISI
# ===========================

def connect_mail(folder="INBOX"):

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)

    mail.login(EMAIL, PASSWORD)

    status, _ = mail.select(folder)

    if status != "OK":
        raise Exception(f"{folder} klasörü açılamadı.")

    return mail


# ===========================
# TÜM KLASÖRLERİ LİSTELE
# ===========================

def list_folders():

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)

    mail.login(EMAIL, PASSWORD)

    status, folders = mail.list()

    if status == "OK":

        for folder in folders:
            print(folder.decode())

    mail.logout()


# ===========================
# HEADER ÇÖZÜMLEME
# ===========================

def decode_mail_header(value):

    if value is None:
        return ""

    decoded = decode_header(value)

    result = ""

    for part, enc in decoded:

        if isinstance(part, bytes):

            result += part.decode(
                enc if enc else "utf-8",
                errors="ignore"
            )

        else:

            result += str(part)

    return result


# ===========================
# MAİL GÖVDESİ
# ===========================

def extract_body(msg):

    body = ""

    if msg.is_multipart():

        for part in msg.walk():

            if part.get_content_type() != "text/plain":
                continue

            payload = part.get_payload(decode=True)

            if payload:

                body = payload.decode(
                    part.get_content_charset() or "utf-8",
                    errors="ignore"
                )

                break

    else:

        payload = msg.get_payload(decode=True)

        if payload:

            body = payload.decode(
                msg.get_content_charset() or "utf-8",
                errors="ignore"
            )

    return body.strip()


# ===========================
# KLASÖRDEN MAİL OKU
# ===========================

def get_folder_mails(folder="INBOX", count=20):

    mail = connect_mail(folder)

    status, messages = mail.search(None, "ALL")

    if status != "OK":
        return []

    ids = messages[0].split()

    result = []

    for mail_id in reversed(ids[-count:]):

        try:

            _, msg_data = mail.fetch(mail_id, "(RFC822)")

            raw = msg_data[0][1]

            msg = email.message_from_bytes(raw)

            subject = decode_mail_header(msg.get("Subject"))

            sender_display = decode_mail_header(msg.get("From"))

            match = re.search(
                r'[\w\.-]+@[\w\.-]+',
                sender_display
            )

            sender = match.group(0) if match else sender_display

            result.append({

                "id": mail_id.decode(),

                "subject": subject,

                "sender_display": sender_display,

                "sender": sender,

                "content": extract_body(msg)

            })

        except Exception as e:

            print("MAIL HATASI:", e)

    mail.logout()

    return result
# ===========================
# KLASÖRLER
# ===========================

def get_inbox(count=20):
    return get_folder_mails("INBOX", count)


def get_sent(count=20):

    folders = [
        "Sent",
        "Sent Items",
        "INBOX.Sent",
        "INBOX.Sent Items"
    ]

    for folder in folders:

        try:
            return get_folder_mails(folder, count)
        except:
            pass

    return []


def get_spam(count=20):

    folders = [
        "Spam",
        "Junk",
        "INBOX.Spam",
        "INBOX.Junk"
    ]

    for folder in folders:

        try:
            return get_folder_mails(folder, count)
        except:
            pass

    return []


def get_trash(count=20):

    folders = [
        "Trash",
        "Deleted",
        "Deleted Items",
        "INBOX.Trash"
    ]

    for folder in folders:

        try:
            return get_folder_mails(folder, count)
        except:
            pass

    return []


def get_drafts(count=20):

    folders = [
        "Drafts",
        "INBOX.Drafts"
    ]

    for folder in folders:

        try:
            return get_folder_mails(folder, count)
        except:
            pass

    return []


def get_archive(count=20):

    folders = [
        "Archive",
        "Archives",
        "INBOX.Archive"
    ]

    for folder in folders:

        try:
            return get_folder_mails(folder, count)
        except:
            pass

    return []


# ===========================
# GPT MAİL ANALİZİ
# ===========================

def analyze_mail(text):

    prompt = f"""
Aşağıdaki e-postayı analiz et.

1. Kısa özet
2. Önem derecesi
3. Yapılması gerekenler
4. Profesyonel cevap önerisi

Mail:

{text}
"""

    response = client.chat.completions.create(

        model="gpt-5.5",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
# ===========================
# MAIL GÖNDER
# ===========================

def send_reply_mail(to_email, subject, body):

    msg = MIMEMultipart()

    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(
        MIMEText(body, "plain", "utf-8")
    )

    server = smtplib.SMTP(
        SMTP_SERVER,
        SMTP_PORT
    )

    server.starttls()

    server.login(
        EMAIL,
        PASSWORD
    )

    server.sendmail(
        EMAIL,
        to_email,
        msg.as_string()
    )

    server.quit()

    return True


# ===========================
# YENİ MAIL GÖNDER
# ===========================

def send_new_mail(
        to_email,
        subject,
        body):

    msg = MIMEMultipart()

    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(
        MIMEText(body, "plain", "utf-8")
    )

    server = smtplib.SMTP(
        SMTP_SERVER,
        SMTP_PORT
    )

    server.starttls()

    server.login(
        EMAIL,
        PASSWORD
    )

    server.sendmail(
        EMAIL,
        to_email,
        msg.as_string()
    )

    server.quit()

    return True


# ===========================
# TEST
# ===========================

if __name__ == "__main__":

    print("=== KLASÖRLER ===")

    try:
        list_folders()
    except Exception as e:
        print(e)

    print()

    print("=== GELEN KUTUSU ===")

    try:

        mails = get_inbox(5)

        print("Mail Sayısı:", len(mails))

        for mail in mails:

            print("-" * 50)

            print(mail["sender"])

            print(mail["subject"])

    except Exception as e:

        print(e)