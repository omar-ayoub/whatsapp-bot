import requests
from flask import current_app
from .openai_service import get_openai_response

def process_whatsapp_message(sender, message):
    response = get_openai_response(sender, message)
    send_whatsapp_message(sender, response)
    return response

def send_whatsapp_message(recipient, message):
    url = f"https://graph.facebook.com/v13.0/{current_app.config['WHATSAPP_PHONE_NUMBER_ID']}/messages"
    headers = {
        'Authorization': f"Bearer {current_app.config['WHATSAPP_TOKEN']}",
        'Content-Type': 'application/json'
    }
    data = {
        'messaging_product': 'whatsapp',
        'to': recipient,
        'type': 'text',
        'text': {'body': message}
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()