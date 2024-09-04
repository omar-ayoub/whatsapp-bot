import requests
from flask import current_app
from .openai_service import get_openai_response
import logging

def process_whatsapp_message(sender, message):
    response = get_openai_response(sender, message)
    send_whatsapp_message(sender, response)
    return response

def send_whatsapp_message(recipient, message):
    logger = logging.getLogger(__name__)
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
    logger.debug(f"Sending message to {recipient}: {message}")
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logger.debug(f"Message sent successfully. WhatsApp response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message to WhatsApp: {str(e)}")
        return {"status": "error", "message": str(e)}