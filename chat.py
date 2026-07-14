import os
import base64

from pypdf import PdfReader
from openai import OpenAI


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def image_file_to_data_url(file_storage):
    mime_type = file_storage.mimetype or "image/jpeg"

    raw = file_storage.read()

    encoded = base64.b64encode(raw).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def pdf_to_text(file_storage):

    reader = PdfReader(file_storage)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def ask_gpt(prompt):
    client = get_client()

    if client is None:
        raise Exception("OPENAI_API_KEY bulunamadı.")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
def generate_chat_response(messages):

    client = get_client()

    if client is None:
        raise Exception("OPENAI_API_KEY bulunamadı.")

    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=messages
    )

    return response.choices[0].message.content
def generate_chat_title(soru):

    client = get_client()

    if client is None:
        raise Exception("OPENAI_API_KEY bulunamadı.")

    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=[
            {
                "role": "system",
                "content": "En fazla 4 kelimelik bir sohbet başlığı oluştur. Emoji kullanabilirsin. Sadece başlığı yaz."
            },
            {
                "role": "user",
                "content": soru
            }
        ]
    )

    return response.choices[0].message.content.strip()  
def analyze_pdf(uploaded_file, prompt):

    client = get_client()

    if client is None:
        raise Exception("OPENAI_API_KEY bulunamadı.")

    pdf_text = pdf_to_text(uploaded_file)

    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nPDF İçeriği:\n\n{pdf_text}"
            }
        ]
    )

    return response.choices[0].message.content
def analyze_image(uploaded_file, prompt):

    client = get_client()

    if client is None:
        raise Exception("OPENAI_API_KEY bulunamadı.")

    image_data_url = image_file_to_data_url(uploaded_file)

    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        }
                    }
                ]
            }
        ]
    )

    return (
        response.choices[0].message.content,
        image_data_url
    )